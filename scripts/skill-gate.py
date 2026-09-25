#!/usr/bin/env python3
"""The read gate.

NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.

A mapped artifact's skill is in context before the artifact is written: the
hooks put it there, and `./scripts/skill <name>` prints and records any other.
A write, commit or push that comes first gets the missing skill put in context
with a warning. Nothing here blocks: a rough draft lands, a later pass fixes it.

  ./scripts/skill-gate.py read <name>       print skills/<name>.md, projects/<name>/AGENTS.md or <name>.md, record it;
                                            a shape under a skill reads as pr-body/docs, a project's context as meet/context
  ./scripts/skill-gate.py check <path>...   name each missing read on stderr; `git` stands for a commit or push,
                                            which needs skills/git.md and workspace.md
  ./scripts/skill-gate.py pre-commit        check the paths staged in the repo at cwd, plus `git`
  ./scripts/skill-gate.py pre-push          check every path the pushed commits touch, plus `git`; git's
                                            pre-push lines on stdin
  ./scripts/skill-gate.py hook-claude       Claude Code PreToolUse adapter, hook JSON on stdin: the missing
                                            skills named by path, to Read whole first; the write goes ahead
  ./scripts/skill-gate.py hook-read         Claude Code PreToolUse adapter on the Read tool: a whole read of a
                                            skill, a shape, a delta or a root file is recorded; a partial one is not
  ./scripts/skill-gate.py session-start     Claude Code SessionStart adapter, hook JSON on stdin: runs
                                            scripts/sync.sh on a new session and records the CLAUDE.md
                                            imports, shortcuts and short-form, as read; after a compaction
                                            or a resume, forgets the session's reads and names them by path
  ./scripts/skill-gate.py prompt            Claude Code UserPromptSubmit adapter: the skills the prompt's
                                            words and the repositories it names call for, named by path
                                            until read

Another harness wires its before-write hook to `check` with the path, or to
`hook-claude` when its payload carries tool_name and tool_input the same way,
and exports its session id as CLAUDE_CODE_SESSION_ID. The commit and push hooks
hold without any harness.

Lives in the skills repository as scripts/skill-gate.py; a workspace mounting it at skills/
wires its hooks to skills/scripts/skill-gate.py, or keeps a shim at scripts/skill-gate.py.
The record is <root>/.skill-gate.json: per session and name, the file's hash.
A read holds while the hash still matches the file and the session is the same.
"""

import difflib
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import shutil
import shlex
import subprocess
import sys
import time
from pathlib import Path

RECORD = '.skill-gate.json'
COPIES = '.skill-gate'  # <root>/.skill-gate/<session>/<name>.md, the text as read
KEEP_DAYS = 7
COMMIT_READS = ['git', 'workspace']

# Processes that stand between a command and the harness that ran it.
PASS_THROUGH = {'bash', 'sh', 'zsh', 'fish', 'dash', 'git', 'env', 'sudo', 'xargs', 'nice',
                'timeout', 'nohup', 'setsid'}

# Written path, as a regex over the root-relative path, to the reads it needs.
# Artifacts live under projects/<repo>/; a skill file of the same name is a rule file.
MAP = [
    (r'^projects/[^/]+/reviews/.*/review_[^/]*\.md$', ['review', 'writing-style']),
    (r'^projects/[^/]+/.*/overview\.md$', ['review', 'writing-style']),
    (r'^projects/[^/]+/reviews/.*/comment_[^/]*\.md$', ['review-comment', 'writing-style']),
    (r'^projects/[^/]+/.*/issue\.md$', ['issue', 'writing-style']),
    (r'^projects/[^/]+/.*/pr-body\.md$', ['pr-body', 'writing-style']),
    (r'^projects/[^/]+/changes/[^/]+/(plan|spec|README)\.md$', ['change', 'writing-style']),
    (r'^(projects/[^/]+/)?(AGENTS|CLAUDE)\.md$', ['authoring']),
    (r'^projects/[^/]+/(CONTEXT|context-log)\.md$', ['authoring']),
    (r'^skills/(?!README\.md$)[^/]+\.md$', ['authoring']),
    (r'^skills/pr-body/[^/]+\.md$', ['authoring']),
]

GIT_HISTORY = {'commit', 'push', 'merge', 'rebase', 'cherry-pick', 'am', 'revert', 'pull'}
WRAPPERS = {'command', 'exec', 'sudo', 'env', 'nice', 'timeout', 'nohup', 'xargs', 'setsid'}
SUDO_ARG_OPTS = {'-u', '-g', '-h', '-p', '-C', '-D', '-R', '-T', '-U'}
SHELLS = {'bash', 'sh', 'zsh', 'dash'}
WRITERS = {'tee', 'sed', 'perl', 'cp', 'mv', 'install', 'touch', 'ln', 'rsync', 'truncate', 'dd'}
LAST_ARG_WRITERS = {'cp', 'mv', 'install', 'ln', 'rsync'}
SCRIPT_RUNNERS = {'python', 'python3', 'perl', 'node', 'ruby'}
INLINE_FLAGS = {'-', '-c', '-e'}
ASSIGNMENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*=')
HEREDOC = re.compile(r'(?<!<)<<(?!<)-?\s*([\'"]?)(\w+)\1')
REDIRECT = re.compile(r'(?:^|\s)&?\d?>[>|]?\s*("[^"]*"|\'[^\']*\'|\S+)')
INPUT = re.compile(r'(?<![<>])<(?![<])\s*("[^"]*"|\'[^\']*\'|\S+)')
QUOTED = re.compile(r'(?<=[\'"])([^\'"\n]+)(?=[\'"])')
SED_INPLACE = re.compile(r'^-[A-Za-z]*i')
PERL_INPLACE = re.compile(r'^-[a-zA-Z]*?i(\.\w*)?$')
# A call that writes a file, on the same line as the quoted path: a fixture string, a prefix or an assertion names nothing.
WRITE_CALL = re.compile(r'\bopen\(|\.write_(?:text|bytes)\(|\.write\(|writeFileSync\(|\bcopy(?:file)?\(|\bmove\(|\.rename\(|\.touch\(')


def root():
    """The workspace: SKILL_GATE_ROOT, else the nearest ancestor holding an AGENTS.md and the skills/ this file lives in."""
    env = os.environ.get('SKILL_GATE_ROOT')
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for d in here.parents:
        if (d / 'AGENTS.md').is_file() and (d / 'skills').is_dir():
            return d
    return here.parent.parent


def session_key():
    """The harness session id, else the nearest ancestor that is not a shell."""
    sid = os.environ.get('CLAUDE_CODE_SESSION_ID')
    if sid:
        return sid
    pid = os.getppid()
    while pid > 1:
        try:
            comm = Path(f'/proc/{pid}/comm').read_text().strip()
            fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        except OSError:
            break
        if comm not in PASS_THROUGH:
            return f'{pid}-{fields[19]}'
        pid = int(fields[1])
    return str(os.getppid())


def always_whole():
    """The skills every turn runs on, which are never cut however they are declared: the register and the words the
    root CLAUDE.md imports, so the harness already carries them whole and the gate must record the same bytes."""
    names = set(IMPORTED)
    try:
        text = (root() / 'CLAUDE.md').read_text()
    except OSError:
        return names
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('@'):
            names.add(re.sub(r'^skills/|\.md$', '', line[1:].strip()))
    return names


SETS = '.skill-gate/sets'  # <root>/.skill-gate/sets/<name>.md, a skill cut to the sections its reader needs
FRONT_SECTIONS = re.compile(r'^prompt-sections:\s*\[(.*?)\]\s*$', re.M)


import importlib.util as _ilu
_spec = _ilu.spec_from_file_location('sections', Path(__file__).resolve().parent / 'sections.py')
_sections = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_sections)
section = _sections.section


def cut_to_sections(name, path):
    """A skill declaring `prompt-sections: [...]` in its frontmatter is read as that cut, written under
    <root>/.skill-gate/sets and refreshed whenever the source changes, so the reader loads the sections its
    moment needs and never the stage sections it does not. No declaration returns the file itself."""
    try:
        text = path.read_text()
    except OSError:
        return path
    if name in always_whole():
        return path       # already in context whole; a cut here would desync the record from what was loaded
    m = FRONT_SECTIONS.search(text.split('---', 2)[1]) if text.startswith('---') else None
    if not m:
        return path
    wanted = [w.strip() for w in m.group(1).split(',') if w.strip()]
    if not wanted:
        return path
    out = root() / SETS / f'{name}.md'
    stamp = f'<!-- {name}: {len(wanted)} sections of {path.relative_to(root()).as_posix()} at {digest(path)[:12]}.'
    if out.is_file():
        try:
            if out.read_text().startswith(stamp):
                return out
        except OSError:
            pass
    parts, missing = [], []
    for w in wanted:
        body = section(text, w)
        parts.append(body) if body else missing.append(w)
    if missing:                       # a renamed heading falls back to the whole file rather than cutting it away
        return path
    head = (stamp + ' Read the whole file for anything else. -->\n\n'
            + text.split('---', 2)[2].split('\n##', 1)[0].strip() + '\n\n')
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(head + '\n'.join(parts))
    except OSError:
        return path
    return out


def resolve(name):
    """A skill, a project delta or a root file by name; a slashed name is a shape under a skill, or a project's context as <repo>/context."""
    paths = [root() / 'skills' / f'{name}.md']
    if '/' not in name:
        paths += [root() / 'projects' / name / 'AGENTS.md', root() / f'{name}.md']
    elif name.endswith('/context'):
        paths.append(root() / 'projects' / name[:-len('/context')] / 'CONTEXT.md')
    for path in paths:
        if path.is_file():
            return cut_to_sections(name, path) if path.parent.name == 'skills' else path
    return None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    try:
        return json.loads((root() / RECORD).read_text())
    except (OSError, ValueError):
        return {}


def save(record):
    cutoff = time.time() - KEEP_DAYS * 86400
    record = {k: v for k, v in record.items() if v.get('at', 0) > cutoff}
    (root() / RECORD).write_text(json.dumps(record, indent=1, sort_keys=True) + '\n')


def copy_path(name):
    return root() / COPIES / session_key().replace('/', '_') / f'{name}.md'


def record_read(name):
    path = resolve(name)
    if path is None:
        return False
    record = load()
    record[f'{session_key()}:{name}'] = {'sha256': digest(path), 'at': time.time()}
    save(record)
    copy = copy_path(name)
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_bytes(path.read_bytes())
    cutoff = time.time() - KEEP_DAYS * 86400
    for d in (root() / COPIES).iterdir():
        if d.is_dir() and d.stat().st_mtime < cutoff:
            shutil.rmtree(d, ignore_errors=True)
    return True


def is_read(name):
    path = resolve(name)
    if path is None:
        return False
    entry = load().get(f'{session_key()}:{name}')
    return bool(entry) and entry.get('sha256') == digest(path)


def relatives(path, base=None):
    """Root-relative posix forms of a path: the lexical one, so a symlink at a
    mapped path stays mapped whatever it points at, and the one through the
    parent's real location, so a symlinked ancestor cannot hide a mapped path."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(base) / p if base else root() / p
    p = Path(os.path.normpath(p))
    roots = [Path(os.path.normpath(r)) for r in (root(), root().resolve())]
    candidates = [p]
    try:
        candidates.append(p.parent.resolve() / p.name)
    except OSError:
        pass
    out = []
    for c in candidates:
        for r in roots:
            try:
                rel = c.relative_to(r).as_posix()
                if rel not in out:
                    out.append(rel)
                break
            except ValueError:
                pass
    return out


def relative(path, base=None):
    forms = relatives(path, base)
    return forms[0] if forms else None


def required_reads(path, base=None):
    names = set()
    for rel in relatives(path, base):
        for pattern, reads in MAP:
            if re.search(pattern, rel):
                names.update(reads)
        m = re.match(r'projects/([^/]+)/', rel)
        if m and (root() / 'projects' / m.group(1) / 'AGENTS.md').is_file():
            names.add(m.group(1))
        if m and (root() / 'projects' / m.group(1) / 'CONTEXT.md').is_file():
            names.add(f'{m.group(1)}/context')
    return names


def missing_reads(path, base=None):
    return sorted(n for n in required_reads(path, base) if not is_read(n))


def _split_heredocs(command):
    """Yield (line, heredoc_body) per command line, bodies taken out of the stream."""
    lines = command.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        body = []
        m = HEREDOC.search(line)
        if m:
            end = m.group(2)
            i += 1
            while i < len(lines) and lines[i].strip() != end:
                body.append(lines[i])
                i += 1
        yield line, '\n'.join(body)
        i += 1


def _split_segments(line):
    """Split on &&, ||, ; and | outside quotes, keeping >| together."""
    segments, cur, quote, i = [], [], None, 0
    while i < len(line):
        ch = line[i]
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            cur.append(ch)
        elif line.startswith(('&&', '||'), i) or ch == ';':
            segments.append(''.join(cur)); cur = []
            i += 2 if ch in '&|' else 1
            continue
        elif ch == '|' and not (cur and cur[-1] == '>'):
            segments.append(''.join(cur)); cur = []
        else:
            cur.append(ch)
        i += 1
    segments.append(''.join(cur))
    return [s.strip().strip('()').strip() for s in segments if s.strip()]


def _tokens(text):
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


def _strip_prefixes(tokens):
    """Drop NAME=value assignments and wrappers with their options."""
    while tokens:
        t = tokens[0]
        if ASSIGNMENT.match(t):
            tokens = tokens[1:]
        elif os.path.basename(t) in WRAPPERS:
            name, tokens = os.path.basename(t), tokens[1:]
            while tokens and (tokens[0].startswith('-') or ASSIGNMENT.match(tokens[0])):
                skip = 2 if name == 'sudo' and tokens[0] in SUDO_ARG_OPTS else 1
                tokens = tokens[skip:]
        else:
            break
    return tokens


def _git_subcommand(tokens):
    i = 1
    while i < len(tokens):
        t = tokens[i]
        if t in ('-C', '-c', '--git-dir', '--work-tree'):
            i += 2
        elif t.startswith('-'):
            i += 1
        else:
            return t, tokens[i + 1:]
    return None, []


def bash_targets(command, base=''):
    """Paths a shell command writes, plus `git` for anything that makes or moves history."""
    targets = set()

    def add(t):
        t = t.strip('\'"')
        if not t or t.startswith('&') or t.startswith('-') or t == os.devnull:
            return
        targets.add(t if t.startswith('/') or not base else posixpath.normpath(posixpath.join(base, t)))

    for line, body in _split_heredocs(command):
        for segment in _split_segments(line):
            plain = INPUT.sub(' ', segment)
            tokens, raw = _strip_prefixes(_tokens(plain)), _strip_prefixes(_tokens(segment))
            if not tokens:
                continue
            cmd = os.path.basename(tokens[0])
            if cmd == 'cd':
                d = tokens[1] if len(tokens) > 1 else ''
                base = '' if '$' in d or not d else (d if d.startswith('/') or not base else posixpath.join(base, d))
                continue
            script = next((t for t in (tokens[1:] if cmd in SHELLS else tokens[:1]) if not t.startswith('-')), '')
            if script.endswith('sync-push.sh') and not (cmd in SHELLS and '-n' in tokens):
                targets.add('git')
            for m in REDIRECT.finditer(plain):
                add(m.group(1))
            if cmd in SHELLS:
                inner = body
                if '-c' in raw[1:]:
                    inner = raw[raw.index('-c') + 1] if raw.index('-c') + 1 < len(raw) else ''
                if inner:
                    targets.update(bash_targets(inner, base))
                continue
            if cmd == 'git':
                sub, rest = _git_subcommand(tokens)
                if sub in GIT_HISTORY:
                    targets.add('git')
                elif sub == 'mv' and rest:
                    add(rest[-1])
                elif sub == 'checkout':
                    if '--' in rest:
                        for t in rest[rest.index('--') + 1:]:
                            add(t)
                elif sub == 'restore':
                    if '--staged' in rest and '--worktree' not in rest:
                        continue
                    for t in rest:
                        if t != '--' and not t.startswith('-'):
                            add(t)
                continue
            inplace = cmd == 'perl' and any(PERL_INPLACE.match(t) for t in tokens[1:])
            if cmd in SCRIPT_RUNNERS and not inplace:
                inline = body or (len(tokens) > 1 and tokens[1] in INLINE_FLAGS)
                if inline:
                    for text_line in (segment + '\n' + body).split('\n'):
                        if not WRITE_CALL.search(text_line):
                            continue
                        for q in QUOTED.findall(text_line):
                            if '/' in q or q.endswith('.md'):
                                add(q)
                continue
            if cmd not in WRITERS:
                continue
            args = [t for t in tokens[1:] if not t.startswith('-') and not re.match(r'^\d*>|^&', t)]
            if cmd == 'sed' and not any(SED_INPLACE.match(t) or t.startswith('--in-place') for t in tokens[1:]):
                continue
            if cmd == 'perl' and not inplace:
                continue
            if cmd in ('sed', 'perl'):
                args = args[1:]  # the first free argument is the script
            if cmd == 'dd':
                args = [t[3:] for t in tokens[1:] if t.startswith('of=')]
            if cmd in LAST_ARG_WRITERS:
                args = args[-1:]
            for t in args:
                add(t)
    return targets


def check(paths, base=None):
    messages = []
    for p in paths:
        if p == 'git':
            for name in COMMIT_READS:
                if not is_read(name):
                    messages.append(f'Run ./scripts/skill {name} before a commit or push')
            continue
        for name in missing_reads(p, base):
            messages.append(f'Run ./scripts/skill {name} before writing {p}')
    return messages


def report(messages):
    """Warn on stderr and let the action through."""
    for line in messages:
        print(line, file=sys.stderr)
    return 0


def cmd_read(name, stdout):
    if name.endswith('.md') or name.startswith(('.', '/')) or '..' in name or name.count('/') > 1:
        print(f'{name} is a path; give the skill or project name, pr-body/docs for a shape', file=sys.stderr)
        return 1
    path = resolve(name)
    if path is None:
        print(f'no skill or project named {name}: expected skills/{name}.md, '
              f'projects/{name}/AGENTS.md or {name}.md', file=sys.stderr)
        return 1
    try:
        if os.fstat(stdout.fileno()).st_rdev == os.stat(os.devnull).st_rdev:
            print(f'{name} was sent to /dev/null; the read is recorded only when it prints', file=sys.stderr)
            return 1
    except (OSError, ValueError, AttributeError):
        pass
    if is_read(name):
        stdout.write(f'{name}: unchanged since this session read it, {path}\n')
        return 0
    if path.stat().st_size > BASH_BOUND:
        stdout.write(f'{name}: {path.stat().st_size} bytes, over the Bash result bound; Read {path} whole with the Read tool, which records the read.\n')
        return 0
    copy = copy_path(name)
    if copy.is_file():
        old, new = copy.read_text().splitlines(keepends=True), path.read_text().splitlines(keepends=True)
        diff = ''.join(difflib.unified_diff(old, new, f'{name} as read', f'{name} now', n=2))
        stdout.write(f'{name}: changed since this session read it; the diff, then the record is refreshed\n{diff}')
    else:
        stdout.write(path.read_text())
    record_read(name)
    return 0


def _git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def cmd_pre_commit(cwd):
    top = Path(_git(cwd, 'rev-parse', '--show-toplevel').strip())
    staged = [line for line in _git(cwd, 'diff', '--cached', '--name-only', '--diff-filter=ACMR').splitlines() if line]
    paths = [relative(top / p) or str(top / p) for p in staged]
    refused = runner_parse_errors(top, staged) + unpushed_gitlinks(top, cwd)
    for line in refused:
        print(f'refused: {line}', file=sys.stderr)
    rc = report(check(['git', *paths]))
    return 1 if refused else rc


def runner_parse_errors(top, staged):
    """A staged workflow script that does not parse, wrapped as the async function body the harness runs it as: a bare
    backtick in a prompt string once shipped and every launch died before an agent ran, and `node --check` on the raw
    file fails on the top-level return a healthy script carries. Nothing is checked when node is absent."""
    scripts = [p for p in staged if p.startswith('scripts/workflows/') and p.endswith('.js')]
    if not scripts or shutil.which('node') is None:
        return []
    out = []
    for p in scripts:
        src = (top / p).read_text()
        wrapped = '(async()=>{' + re.sub(r'^export const meta', 'const meta', src, count=1, flags=re.M) + '})'
        run = subprocess.run(['node', '-e', 'new (require("vm").Script)(require("fs").readFileSync(0, "utf8"))'],
                             input=wrapped, capture_output=True, text=True)
        if run.returncode != 0:
            first = next((l for l in run.stderr.splitlines() if l.strip()), 'syntax error')
            out.append(f'{p} does not parse as a workflow script: {first.strip()}')
    return out


def unpushed_gitlinks(top, cwd):
    """A staged submodule pointer at a commit no remote branch of that submodule holds: a clone cannot resolve it and
    every later push of this repository is refused over it, so the submodule is pushed first."""
    out = []
    for line in _git(cwd, 'diff', '--cached', '--raw').splitlines():
        parts = line.split('\t')
        if len(parts) != 2 or not parts[0].startswith(':'):
            continue
        meta, path = parts[0].split(), parts[1]
        if len(meta) < 4 or meta[1] != '160000':
            continue
        sha = meta[3]
        sub = top / path
        if not (sub / '.git').exists():
            continue
        held = subprocess.run(['git', '-C', str(sub), 'branch', '-r', '--contains', sha], capture_output=True, text=True)
        if held.returncode != 0 or not held.stdout.strip():
            out.append(f'{path} points at {sha[:9]}, which no remote branch of that submodule holds: push the submodule first')
    return out


def cmd_pre_push(stdin, cwd):
    """Every path the pushed commits touch; commits no remote holds when the remote sha is unknown."""
    top = Path(_git(cwd, 'rev-parse', '--show-toplevel').strip())
    paths = set()
    for line in stdin.read().splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        _, local_sha, _, remote_sha = parts
        if set(local_sha) == {'0'}:
            continue
        known = set(remote_sha) != {'0'} and subprocess.run(
            ['git', 'cat-file', '-e', f'{remote_sha}^{{commit}}'], cwd=cwd, capture_output=True).returncode == 0
        if known:
            out = _git(cwd, 'diff', '--name-only', '--diff-filter=ACMR', f'{remote_sha}..{local_sha}')
        else:
            out = _git(cwd, 'log', '--format=', '--name-only', '--diff-filter=ACMR', local_sha, '--not', '--remotes')
        paths.update(p for p in out.splitlines() if p)
    return report(check(['git', *sorted(relative(top / p) or str(top / p) for p in paths)]))


# In context through CLAUDE.md's own `@` imports in every session, so recorded as read when it
# opens. `reply.md` is not among them: nothing imports it, it is the parent's own reply shape,
# and the gate names it for a Read. A hook cannot stand in for an import here, since a hook's
# context reaches the model as a stub naming a file from 10 KB and these three are past it on
# their own.
IMPORTED = ['shortcuts', 'short-form', 'thinking']
# A Bash result of 29.4 KB or more reaches the model as a stub naming a file, and a
# hook's context does so from 10 KB, measured over every transcript of this
# workspace. Only the Read tool carries a whole file, so this script names paths
# and the Read hook records the read.
BASH_BOUND = 28000

# Prompt words to the skills they call for, read where the shortcut puts them: a word
# fires inside the prompt's first PROMPT_HEAD words, the shortcut's own shape, and a URL
# form fires anywhere. A prompt ending in a question mark carries no shortcut word: it
# wants an answer, and the write hook names the rules when an artifact gets written.
# Measured over every typed prompt on this machine, the words sat mid-sentence in most of
# the prompts they matched, "what did you change?" for one, and each false trigger cost
# the reads the shortcut needs, about 30k of context. A review word names review.md
# alone: the drafting rules are the writer stage's, per its step 4, and the write hook
# names them when the draft is written.
PROMPT_HEAD = 6
PROMPT_SKILLS = [
    (r'\breview|\blgtm\b', ['review']),
    # (?<!-) on fixes alone: a repository name ending in -fixes is not a request to fix.
    (r'\bfix(ed|ing)?\b|(?<!-)\bfixes\b|\bimplement|\bsimplif|\bfeature\b', ['change', 'pr-body', 'issue']),
    (r'\bissue', ['issue']),
    (r'\breport\b|\bweekly\b', ['report']),
    # try, run, boot and launch are ordinary verbs. Each names try.md only in the shortcut's own shape: try takes a
    # number, a URL, an owner/repo or a name followed by "on <name>"; run and launch the same minus the bare number,
    # which is a count in prose; boot takes any name. Through the head window over one machine's typed prompts, 37
    # carried one of the verbs; the bare verbs named try.md on all 37, an exclusion list on 20, this shape on the 2 meant.
    (r'\b(?i:try)\b(?:\s+(?i:the|a|an|pr|this|that|it))?\s+(?!(?:review|agent|workflow|round)s?\b)(?:#?\d{2,}\b|https?://\S+|[\w.-]+/[\w.-]+\b|[\w.-]+\s+(?i:on)\s+[\w.-]+\b)'
     r'|\b(?i:run|launch)\b(?:\s+(?i:the|a|an|pr|this|that|it))?\s+(?!(?:review|agent|workflow|round)s?\b)(?:https?://\S+|[\w.-]+/[\w.-]+\b|[\w.-]+\s+(?i:on)\s+[\w.-]+\b)'
     r'|\b(?i:boot)\b\s+(?!it\b|up\b|the\b)[\w.-]+|\bscreenshot\b|\bvideo\b|\bgif\b', ['try']),
    (r'\bskill|\brules?\b|AGENTS\.md|writing.style|\bcaveman\b|\bcvm\b', ['authoring']),
]
PROMPT_URLS = [
    (r'/pull/\d+', ['review']),
    (r'/issues/\d+', ['change', 'pr-body', 'issue']),
]


def _payload(stdin):
    """The hook's JSON, and its session id into the environment when the Bash tool has not set one."""
    try:
        payload = json.load(stdin)
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    if payload.get('session_id') and not os.environ.get('CLAUDE_CODE_SESSION_ID'):
        os.environ['CLAUDE_CODE_SESSION_ID'] = str(payload['session_id'])
    return payload


def submodule_repos():
    """Project name to owner/repo, from .gitmodules."""
    out, path = {}, None
    try:
        lines = (root() / '.gitmodules').read_text().splitlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if line.startswith('path ='):
            path = line.split('=', 1)[1].strip()
        elif line.startswith('url =') and path:
            m = re.match(r'projects/([^/]+)/', path)
            repo = re.sub(r'^(https://github\.com/|git@github\.com:)', '', line.split('=', 1)[1].strip())
            if m:
                out[m.group(1)] = repo[:-4] if repo.endswith('.git') else repo
            path = None
    return out


def prompt_head(prompt):
    """The prompt's first PROMPT_HEAD words, where a shortcut word sits."""
    return ' '.join(re.sub(r'^\W+', '', prompt).split()[:PROMPT_HEAD])


def private_names():
    try:
        return set(json.loads((root() / 'workspace.json').read_text()).get('private_names', []))
    except (OSError, ValueError):
        return set()


def prompt_reads(prompt):
    """The skills and project deltas a prompt calls for, in the order they matched."""
    names = []
    head = '' if prompt.rstrip().endswith('?') else prompt_head(prompt)
    for pattern, reads in PROMPT_SKILLS:
        if re.search(pattern, head, re.I):
            names.extend(n for n in reads if n not in names)
    for pattern, reads in PROMPT_URLS:
        if re.search(pattern, prompt, re.I):
            names.extend(n for n in reads if n not in names)
    repos = submodule_repos()
    # An owner names nobody's project: gnolang/tx-indexer opens tx-indexer and not the gno family, so
    # the owner half of every URL, and of every slug under an owner .gitmodules names, leaves the text
    # the family match reads. The slug match below still reads the whole prompt.
    owners = sorted({r.split('/')[0] for r in repos.values() if '/' in r}, key=len, reverse=True)
    words = re.sub(r'github\.com/[\w.-]+/', '', prompt, flags=re.I)
    if owners:
        words = re.sub(r'(?<![\w./-])(?:' + '|'.join(map(re.escape, owners)) + r')/', '', words, flags=re.I)
    projects = root() / 'projects'
    for d in sorted(projects.iterdir()) if projects.is_dir() else []:
        if not (d / 'AGENTS.md').is_file():
            continue
        name = d.name
        family = name.split('-')[0]  # the word before the first dash opens every project sharing it, and any word it starts
        hit = re.search(r'(?<![\w-])' + re.escape(family), words, re.I)
        # A private project, one whose name or repository the consumer's workspace.json lists as private,
        # opens on its own name alone: a family word in a pull request review of the public sibling
        # pulled a security archive's conventions into every such session.
        if hit and (name in private_names() or repos.get(name, '') in private_names()) and family != name:
            hit = re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', words, re.I)
        hit = hit or (repos.get(name) and re.search(re.escape(repos[name]) + r'(?![\w-])', prompt, re.I))
        if hit and name not in names:
            names.append(name)
        if hit and (d / 'CONTEXT.md').is_file() and f'{name}/context' not in names:
            names.append(f'{name}/context')
    return names


def session_reads():
    """Every name this session has recorded, whether or not its file still matches."""
    prefix = f'{session_key()}:'
    return [k[len(prefix):] for k in load() if k.startswith(prefix)]


def name_of(path, base=None):
    """The skill, shape, delta or root-file name a path resolves to, else None."""
    for rel in relatives(path, base):
        m = re.match(re.escape(SETS) + r'/([^/]+)\.md$', rel)
        if m:
            return m.group(1)
        m = re.match(r'skills/([^/]+(?:/[^/]+)?)\.md$', rel)
        if m:
            return m.group(1)
        m = re.match(r'projects/([^/]+)/AGENTS\.md$', rel)
        if m:
            return m.group(1)
        m = re.match(r'projects/([^/]+)/CONTEXT\.md$', rel)
        if m:
            return f'{m.group(1)}/context'
        m = re.match(r'([^/]+)\.md$', rel)
        if m and m.group(1) not in ('AGENTS', 'CLAUDE'):
            return m.group(1)
    return None


def point(names, header, event, stdout, extra=()):
    """Name each file to read whole with the Read tool. Nothing is recorded here: the Read hook records."""
    parts = list(extra)
    lines = []
    for name in names:
        path = resolve(name)
        if path is None:
            continue
        lines.append(f'- {name}: Read `{path.relative_to(root()).as_posix()}` whole, with the Read tool.')
    if lines:
        parts.append(header + '\n' + '\n'.join(lines))
    if parts:
        json.dump({'hookSpecificOutput': {'hookEventName': event,
                                          'additionalContext': '\n\n'.join(parts)}}, stdout)
    return [name for name in names if resolve(name) is not None]


FRONT_EFFORT = re.compile(r'^effort-set:\s*\[(.*?)\]\s*$', re.M)
TRANSCRIPT_TAIL = 262144


def effort_set():
    """The model patterns `effort-set` lists in skills/thinking.md's frontmatter: models whose thinking depth effort sets."""
    try:
        text = (root() / 'skills' / 'thinking.md').read_text()
    except OSError:
        return []
    m = FRONT_EFFORT.search(text.split('---', 2)[1]) if text.startswith('---') else None
    return [p.strip().strip('\'"') for p in m.group(1).split(',') if p.strip()] if m else []


def model_id(raw):
    """A harness's model string as a bare API id: `us.anthropic.claude-opus-5-5-v1:0[1m]` reads `claude-opus-5-5`,
    a provider path or prefix, a version and a context suffix dropped."""
    m = str(raw).strip().lower().split('/')[-1]
    m = re.sub(r'\[[^\]]*\]$', '', m)
    m = re.sub(r'^(?:[a-z]{2,4}\.)?anthropic\.', '', m)
    m = re.sub(r'-v\d+(?::\d+)?$', '', m)
    return m.split('@')[0]


def session_model(payload):
    """The running model as the harness reports it: the SessionStart payload's `model`, which Claude Code does not always
    send, else the model of the transcript's last assistant entry; None when neither names one."""
    m = payload.get('model')
    if isinstance(m, dict):
        m = m.get('id')
    if isinstance(m, str) and m.strip():
        return model_id(m)
    path = payload.get('transcript_path')
    if not path:
        return None
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - TRANSCRIPT_TAIL))
            lines = f.read().decode('utf-8', 'replace').splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get('type') != 'assistant' or entry.get('isSidechain'):
            continue
        m = (entry.get('message') or {}).get('model')
        if isinstance(m, str) and m and not m.startswith('<'):
            return model_id(m)
    return None


def is_effort_set(model):
    return any(fnmatch.fnmatchcase(model, p) for p in effort_set())


def model_note(payload):
    """The line lifting skills/thinking.md, printed once per session and model, when the harness names an effort-set
    model, and its reversal when the session moves off one. A model the gate cannot name gets no line: the rules hold."""
    model = session_model(payload)
    if not model:
        return None
    key = f'{session_key()}:model'
    record = load()
    prev = (record.get(key) or {}).get('model')
    if prev == model:
        return None
    record[key] = {'model': model, 'at': time.time()}
    save(record)
    if is_effort_set(model):
        return (f'This session runs on `{model}`, whose thinking depth effort sets: `skills/thinking.md` does not apply '
                'to it.')
    if prev and is_effort_set(prev):
        return f'This session now runs on `{model}`: `skills/thinking.md` applies again.'
    return None


def forget_session():
    """Drop every read this session recorded; a compaction took them out of context."""
    prefix = f'{session_key()}:'
    save({k: v for k, v in load().items() if not k.startswith(prefix)})


INTRO = ('Principles, Invariants, the words the user types and the register are in context through '
         '`CLAUDE.md`, which imports the workspace `AGENTS.md`, `skills/shortcuts.md`, '
         '`skills/short-form.md` and `skills/thinking.md`. Every other rule, `skills/reply.md` included, is read whole with the '
         'Read tool before its first command, and that read is what the gate records; '
         './scripts/skill <name> names its path.')


def cmd_session_start(stdin, stdout):
    """Sync on startup and clear, and record the CLAUDE.md imports as read; after a compaction or a resume, forget the session's reads and name them for re-reading."""
    payload = _payload(stdin)
    source = payload.get('source', 'startup')
    extra = []
    names = []
    if source in ('startup', 'clear'):
        try:
            r = subprocess.run([str(root() / 'scripts' / 'sync.sh')], capture_output=True, text=True, timeout=90)
            extra.append(('Sync ran: ' if r.returncode == 0 else 'Sync failed: ') + (r.stdout + r.stderr).strip())
        except (OSError, subprocess.TimeoutExpired) as e:
            extra.append(f'Sync failed: {e}')
    else:
        names = [n for n in session_reads() if n not in IMPORTED]
        forget_session()
    for name in IMPORTED:
        record_read(name)
    extra.append(INTRO)
    note = model_note(payload)
    if note:
        extra.append(note)
    point(names, 'Read again, since the compaction dropped them from context:', 'SessionStart', stdout, extra)
    return 0


def cmd_prompt(stdin, stdout):
    """What this prompt's words and repositories call for, minus what the session already read."""
    payload = _payload(stdin)
    prompt = str(payload.get('prompt', ''))
    names = [n for n in prompt_reads(prompt) if not is_read(n)]
    note = model_note(payload)
    extra = [note] if note else []
    point(names, 'Rules this prompt calls for, unread this session. Read each whole with the Read tool '
                 'before the first command; the read is recorded then.', 'UserPromptSubmit', stdout, extra)
    return 0


# What the user typed this turn: the prompt that opened it and every message queued into it
# while it ran. A publish, a push outside the standing list and a forced push each wait for
# their word there, per Invariants 1, 2, 3 and 8 of the workspace AGENTS.md.
NOT_TYPED = ('<task-notification', '<command-', '<local-command-', '<system-reminder', '[SYSTEM NOTIFICATION')


def turn_text(transcript):
    """The user's typed text this turn, or None when the transcript cannot be read."""
    try:
        lines = open(transcript, encoding='utf-8', errors='replace').read().split('\n')
    except (OSError, TypeError):
        return None
    rows = []
    for line in lines:
        line = line.strip().strip('\x00')
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    start = None
    for i, e in enumerate(rows):
        m = e.get('message') or {}
        c = m.get('content')
        if e.get('type') == 'user' and not e.get('isMeta') and not e.get('isCompactSummary') \
                and isinstance(c, str) and not c.lstrip().startswith(NOT_TYPED):
            start = i
    if start is None:
        return ''
    parts = [rows[start]['message']['content']]
    for e in rows[start + 1:]:
        a = e.get('attachment') or {}
        if e.get('type') == 'attachment' and a.get('type') == 'queued_command' \
                and (a.get('origin') or {}).get('kind') == 'human':
            parts.append(str(a.get('prompt', '')))
    return '\n'.join(parts)


NEGATION = re.compile(r"(?i)\b(don'?t|do not|never|no|not|without)\W+(\w+\W+){0,2}$")


def has_word(text, word):
    """The word typed as a word, a hyphenated compound or a negation aside: `merge-base` is not merge."""
    for m in re.finditer(rf'(?i)(?<![\w-]){word}(?![\w-])', text):
        if not NEGATION.search(text[max(0, m.start() - 40):m.start()]):
            return True
    return False


MARKER = re.compile(r'(?i)co-authored-by:|generated with \[?claude|assisted by ai|\U0001F916')
SHELL_LEAD = {'do', 'then', 'else', 'elif', 'if', 'while', 'until', '{', '(', '!', 'time', 'command', 'env', 'exec',
              'nohup', 'sudo', 'xargs'}
RUNNERS = {'bash', 'sh', 'zsh', 'python', 'python3'}


def _strip_heredocs(cmd):
    out, lines, i = [], cmd.split('\n'), 0
    while i < len(lines):
        out.append(lines[i])
        m = HEREDOC.search(lines[i])
        i += 1
        if m:
            while i < len(lines) and lines[i].strip() != m.group(2):
                i += 1
            i += 1
    return '\n'.join(out)


def _split(cmd):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=';&|\n')
    lex.whitespace = ' \t\r'
    lex.whitespace_split = True
    seg = []
    try:
        for tok in lex:
            if tok and set(tok) <= set(';&|\n'):
                if seg:
                    yield seg
                seg = []
            else:
                seg.append(tok)
    except ValueError:
        for line in cmd.split('\n'):
            for part in re.split(r'&&|\|\||;|\|', line):
                if part.split():
                    yield part.split()
        return
    if seg:
        yield seg


def _segments(cmd, depth=0):
    """The simple commands of a shell line: heredoc bodies dropped, split outside quotes, a leading
    keyword, environment assignment or $( stripped, and a `bash -c` string read as its own line."""
    for t in _split(_strip_heredocs(cmd)):
        t = [x[2:] if x.startswith('$(') else x.lstrip('`') for x in t]
        while t and (t[0] in SHELL_LEAD or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t[0])):
            if '$(' in t[0]:
                t[0] = t[0].split('$(', 1)[1]
                break
            t = t[1:]
        if not t:
            continue
        if t[0] in RUNNERS and len(t) > 2 and t[1] == '-c' and depth < 2:
            yield from _segments(t[2], depth + 1)
            continue
        if os.path.basename(t[0]) in RUNNERS and len(t) > 1 and not t[1].startswith('-'):
            t = t[1:]
        t[0] = os.path.basename(t[0]) if t[0].endswith(('/gh', '/git')) else t[0]
        yield t


def _dry(tokens):
    return '--dry-run' in tokens


def _git_sub(t):
    """git's subcommand, past -C <dir>, -c <k=v> and other global options."""
    i = 1
    while i < len(t) and t[i].startswith('-'):
        i += 2 if t[i] in ('-C', '-c', '--git-dir', '--work-tree', '--namespace') else 1
    return (t[i], i) if i < len(t) else (None, i)


def _gh_verb(t):
    """gh's two-word verb past -R <repo> and other global flags."""
    rest, i = [], 1
    while i < len(t):
        if t[i] in ('-R', '--repo', '--hostname'):
            i += 2
            continue
        rest.append(t[i])
        i += 1
    return rest


def _field_values(t):
    out = []
    for i, x in enumerate(t):
        if x in ('-f', '-F', '--field', '--raw-field') and i + 1 < len(t):
            out.append(t[i + 1])
        elif x.startswith(('-f', '-F')) and len(x) > 2 and not x.startswith('--'):
            out.append(x[2:])
        elif x.startswith(('--field=', '--raw-field=')):
            out.append(x.split('=', 1)[1])
    return out


def _read_at(value):
    if value.startswith('@'):
        try:
            return open(os.path.expanduser(value[1:]), encoding='utf-8', errors='replace').read()
        except OSError:
            return value
    return value


def publish_words(cmd):
    """Each set is one publish on the line, satisfied by any of its words; every set needs its own."""
    needs = []
    for t in _segments(cmd):
        name = os.path.basename(t[0])
        if name in ('post-review.sh', 'post-fix.sh', 'post-pr-review.py') and not _dry(t):
            needs.append({'post', 'upload'})
        if t[0] != 'gh':
            continue
        r = _gh_verb(t)
        if len(r) < 2:
            continue
        verb = (r[0], r[1])
        if verb in {('pr', 'create'), ('pr', 'comment'), ('pr', 'review'), ('pr', 'reopen'), ('issue', 'create'),
                    ('issue', 'comment'), ('issue', 'reopen'), ('release', 'create')}:
            needs.append({'post'})
        elif verb == ('pr', 'ready'):
            needs.append({'post', 'ready'})
        elif verb == ('pr', 'merge'):
            needs.append({'merge'})
        elif verb in {('pr', 'close'), ('issue', 'close')}:
            needs.append({'close'})
        elif r[1] == 'delete':
            needs.append({'delete'})
        elif r[0] == 'api':
            method = None
            for i, x in enumerate(t):
                if x in ('-X', '--method') and i + 1 < len(t):
                    method = t[i + 1].upper()
                elif x.startswith('--method='):
                    method = x.split('=', 1)[1].upper()
                elif x.startswith('-X') and len(x) > 2:
                    method = x[2:].upper()
            fields = _field_values(t)
            has_input = '--input' in t
            path = next((x for x in r[1:] if not x.startswith('-') and ('/' in x or x == 'graphql')), '')
            if path == 'graphql':
                query = ' '.join(_read_at(v.split('=', 1)[1]) for v in fields if v.startswith('query='))
                if has_input:
                    query += _read_at('@' + t[t.index('--input') + 1]) if t.index('--input') + 1 < len(t) else ''
                if re.search(r'\bmutation\b', query):
                    needs.append({'post'})
                continue
            method = method or ('POST' if fields or has_input else 'GET')
            if method == 'GET':
                continue
            # An open pull request's own body or title edit goes up unasked, per Consent in AGENTS.md.
            keys = {v.split('=', 1)[0] for v in fields}
            if method == 'PATCH' and re.search(r'/pulls/\d+/?$', path) and keys and keys <= {'body', 'title'}:
                continue
            needs.append({'delete'} if method == 'DELETE' else {'post'})
    return needs


def commit_messages(cmd):
    out = []
    for t in _segments(cmd):
        is_git_commit = t[0] == 'git' and _git_sub(t)[0] == 'commit'
        is_gh_write = t[0] == 'gh' and len(_gh_verb(t)) > 1 and _gh_verb(t)[1] in ('create', 'comment', 'review', 'edit')
        if not (t[0].endswith('scripts/commit') or is_git_commit or is_gh_write):
            continue
        for i, x in enumerate(t):
            if x in ('-m', '--message', '--body', '-b', '--title', '-t', '--trailer', '-am') and i + 1 < len(t):
                out.append(t[i + 1])
            elif x.startswith(('--message=', '--body=', '--title=', '--trailer=')):
                out.append(x.split('=', 1)[1])
            elif x.startswith('-m') and len(x) > 2 and not x.startswith('--'):
                out.append(x[2:])
            elif x in ('--body-file', '-F') and i + 1 < len(t) and t[0] == 'gh':
                out.append(_read_at('@' + t[i + 1]))
    return out


def push_targets(cmd, cwd):
    """(repository, forced) for each git push on the line; repository is owner/name or None."""
    out = []
    here = cwd or os.getcwd()
    for t in _segments(cmd):
        if len(t) >= 2 and t[0] == 'cd':
            here = os.path.join(here, os.path.expanduser(t[1]))
            continue
        if t[0] != 'git':
            continue
        sub, at = _git_sub(t)
        if sub != 'push':
            continue
        where = here
        for i, x in enumerate(t[:at]):
            if x == '-C' and i + 1 < len(t):
                where = os.path.join(here, os.path.expanduser(t[i + 1]))
        rest = t[at + 1:]
        if '--dry-run' in rest or '-n' in rest:
            continue
        forced = any(x in ('--force', '--mirror') or x.startswith(('--force-with-lease', '--force-if-includes'))
                     or (x.startswith('-') and not x.startswith('--') and 'f' in x[1:]) for x in rest) \
            or any(x.startswith('+') for x in rest if not x.startswith('-'))
        args = [x for x in rest if not x.startswith('-')]
        remote = args[0] if args else 'origin'
        url = subprocess.run(['git', '-C', where, 'remote', 'get-url', remote], capture_output=True, text=True).stdout.strip()
        if not url and ('/' in remote or ':' in remote):
            url = remote
        m = re.search(r'github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$', url)
        out.append((f'{m.group(1)}/{m.group(2)}' if m else None, forced))
    return out


def standing_push():
    try:
        return set(json.loads((root() / 'workspace.json').read_text()).get('standing_push', []))
    except (OSError, ValueError):
        return set()


def refusal(cmd, payload):
    """Why this command waits for a word the turn does not carry, or None."""
    for msg in commit_messages(cmd):
        if MARKER.search(msg):
            return ('an AI-authorship marker in a commit or post message: no Co-Authored-By, no "Generated with", '
                    'no "Assisted by AI", per Invariant 7 of the workspace AGENTS.md.')
    needs = publish_words(cmd)
    standing = standing_push()
    pushes = [(r, f) for r, f in push_targets(cmd, payload.get('cwd')) if f or r not in standing]
    if not needs and not pushes:
        return None
    text = turn_text(payload.get('transcript_path') or '')
    if text is None:
        return 'the transcript is unreadable, so the word this command waits for cannot be confirmed.'
    for need in needs:
        if not any(has_word(text, w) for w in need):
            return (f'a publish waiting for its word, {" or ".join(sorted(need))}, which this turn does not carry, '
                    'per Invariants 1 and 2 of the workspace AGENTS.md. Show the draft and name the word.')
    for repo, forced in pushes:
        if forced and not has_word(text, 'force'):
            return 'a forced push, which waits for approval in the turn, per Invariant 8 of the workspace AGENTS.md.'
        if repo not in standing and not has_word(text, 'push'):
            return (f'a push to {repo or "a repository it cannot resolve"}, which no standing word covers and this '
                    'turn does not name with push, per Consent in the workspace AGENTS.md.')
    return None


def cmd_hook_claude(stdin, stdout):
    """The skills a write still lacks are named by path, and the write proceeds."""
    payload = json.load(stdin)
    tool = payload.get('tool_name', '')
    inp = payload.get('tool_input', {}) or {}
    base = payload.get('cwd')
    if tool in ('Write', 'Edit', 'MultiEdit') and inp.get('file_path'):
        paths = [inp['file_path']]
    elif tool == 'Bash':
        cmd = inp.get('command', '')
        # The invocation itself, never a message quoting the words: `git -c user.name=... commit` or
        # `git commit ... --author=`, on one command line.
        if (re.search(r'\bgit\b[^\n|;&]*?\s-c\s*user\.(name|email)=[^\n|;&]*\bcommit\b', cmd)
                or re.search(r'\bgit\b[^\n|;&]*\bcommit\b[^\n|;&]*\s--author[= ]', cmd)):
            print('Refused: a git commit that sets user.name, user.email or --author by hand. The identity is the '
                  'checkout\'s pin and the verb: ./scripts/commit -m <message> <path>..., per Commit identity in skills/git.md.', file=sys.stderr)
            return 2
        why = refusal(cmd, payload)
        if why:
            print(f'Refused: {why}', file=sys.stderr)
            return 2
        paths = sorted(bash_targets(cmd))
    else:
        return 0
    names = []
    for p in paths:
        wanted = [n for n in COMMIT_READS if not is_read(n)] if p == 'git' else missing_reads(p, base)
        names += [n for n in wanted if n not in names]
    point(names, 'Rules this write calls for, unread this session. Read each whole with the Read tool '
                 'and then write; the write goes ahead.', 'PreToolUse', stdout)
    return 0


def cmd_hook_read(stdin):
    """A Read tool call on a skill, a shape, a delta or a root file records the read; a partial read records nothing."""
    payload = _payload(stdin)
    if payload.get('tool_name') != 'Read':
        return 0
    inp = payload.get('tool_input', {}) or {}
    if inp.get('offset') or inp.get('limit') or not inp.get('file_path'):
        return 0
    name = name_of(inp['file_path'], payload.get('cwd'))
    if name and resolve(name) is not None:
        record_read(name)
    return 0


def main(argv, stdin=None, stdout=None, cwd=None):
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    op, args = argv[0], argv[1:]
    try:
        if op == 'read' and len(args) == 1:
            return cmd_read(args[0], stdout or sys.stdout)
        if op == 'check':
            return report(check(args))
        if op == 'pre-commit':
            return cmd_pre_commit(cwd or os.getcwd())
        if op == 'pre-push':
            return cmd_pre_push(stdin or sys.stdin, cwd or os.getcwd())
        if op == 'hook-claude':
            return cmd_hook_claude(stdin or sys.stdin, stdout or sys.stdout)
        if op == 'hook-read':
            return cmd_hook_read(stdin or sys.stdin)
        if op == 'session-start':
            return cmd_session_start(stdin or sys.stdin, stdout or sys.stdout)
        if op == 'prompt':
            return cmd_prompt(stdin or sys.stdin, stdout or sys.stdout)
    except Exception as e:  # a hook that cannot decide says so and never blocks
        print(f'skill-gate: {e}', file=sys.stderr)
        return 0
    print(f'unknown command: {" ".join(argv)}', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
