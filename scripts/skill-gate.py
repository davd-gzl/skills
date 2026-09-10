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
                                            until read; and the last reply's numbers when reply-check.py
                                            says it drifted

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
    (r'^projects/[^/]+/reviews/.*/review_[^/]*\.md$', ['review', 'review-output', 'writing-style']),
    (r'^projects/[^/]+/.*/overview\.md$', ['review', 'review-output', 'writing-style']),
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


def resolve(name):
    """A skill, a project delta or a root file by name; a slashed name is a shape under a skill, or a project's context as <repo>/context."""
    paths = [root() / 'skills' / f'{name}.md']
    if '/' not in name:
        paths += [root() / 'projects' / name / 'AGENTS.md', root() / f'{name}.md']
    elif name.endswith('/context'):
        paths.append(root() / 'projects' / name[:-len('/context')] / 'CONTEXT.md')
    for path in paths:
        if path.is_file():
            return path
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
                    for q in QUOTED.findall(segment + '\n' + body):
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
    return report(check(['git', *paths]))


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


# In context through CLAUDE.md in every session, so recorded as read when it opens.
IMPORTED = ['shortcuts', 'short-form']
# A Bash result of 29.4 KB or more reaches the model as a stub naming a file, and a
# hook's context does so from 10 KB, measured over every transcript of this
# workspace. Only the Read tool carries a whole file, so this script names paths
# and the Read hook records the read.
BASH_BOUND = 28000

# Prompt words to the skills they call for. Over-matching is the design: a read
# costs context once per session, a missed rule costs the user a turn.
PROMPT_SKILLS = [
    (r'\breview|\blgtm\b|/pull/\d+', ['review', 'review-output', 'review-comment']),
    # (?<!-) on fixes alone: a repository name ending in -fixes is not a request to fix.
    (r'\bfix(ed|ing)?\b|(?<!-)\bfixes\b|\bimplement|\bsimplif|\bchange\b|\bfeature\b|/issues/\d+', ['change', 'pr-body', 'issue']),
    (r'\bissue', ['issue']),
    (r'\breport\b|\bweekly\b', ['report']),
    (r'\btry\b|\brun\b|\bboot\b|\blaunch\b|\bscreenshot\b|\bvideo\b|\bgif\b', ['try']),
    (r'\bskill|\brules?\b|AGENTS\.md|writing.style|\bcaveman\b|\bcvm\b', ['authoring']),
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


def prompt_reads(prompt):
    """The skills and project deltas a prompt calls for, in the order they matched."""
    names = []
    for pattern, reads in PROMPT_SKILLS:
        if re.search(pattern, prompt, re.I):
            names.extend(n for n in reads if n not in names)
    repos = submodule_repos()
    projects = root() / 'projects'
    for d in sorted(projects.iterdir()) if projects.is_dir() else []:
        if not (d / 'AGENTS.md').is_file():
            continue
        name = d.name
        family = name.split('-')[0]  # the word before the first dash opens every project sharing it, and any word it starts
        hit = re.search(r'(?<![\w-])' + re.escape(family), prompt, re.I)
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


def forget_session():
    """Drop every read this session recorded; a compaction took them out of context."""
    prefix = f'{session_key()}:'
    save({k: v for k, v in load().items() if not k.startswith(prefix)})


INTRO = ('Principles, Invariants, the words and the register are in context through CLAUDE.md. '
         'Any other rule is read whole with the Read tool before its first command, and that read is '
         'what the gate records; ./scripts/skill <name> names its path.')


def cmd_session_start(stdin, stdout):
    """Sync on startup and clear, and record the CLAUDE.md imports as read; after a compaction or a resume, forget the session's reads and name them for re-reading."""
    source = _payload(stdin).get('source', 'startup')
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
    point(names, 'Read again, since the compaction dropped them from context:', 'SessionStart', stdout, extra)
    return 0


def cmd_prompt(stdin, stdout):
    """What this prompt's words and repositories call for, minus what the session already read."""
    payload = _payload(stdin)
    prompt = str(payload.get('prompt', ''))
    names = [n for n in prompt_reads(prompt) if not is_read(n)]
    extra = []
    transcript = payload.get('transcript_path')
    if transcript:
        # The register check never blocks a reply; its numbers reach the model here, one turn late.
        try:
            r = subprocess.run([str(Path(__file__).resolve().parent / 'reply-check.py'), '--last', str(transcript)],
                               capture_output=True, text=True, timeout=10)
            if r.stdout.strip():
                extra.append('The last reply drifted from the register: ' + r.stdout.strip()
                             + ' This one stays inside the caps, per Short form in skills/short-form.md: '
                             'lead with the answer, one part per thing asked, the account as plain lines, TL;DR last.')
        except (OSError, subprocess.TimeoutExpired):
            pass
    point(names, 'Rules this prompt calls for, unread this session. Read each whole with the Read tool '
                 'before the first command; the read is recorded then.', 'UserPromptSubmit', stdout, extra)
    return 0


def cmd_hook_claude(stdin, stdout):
    """The skills a write still lacks are named by path, and the write proceeds."""
    payload = json.load(stdin)
    tool = payload.get('tool_name', '')
    inp = payload.get('tool_input', {}) or {}
    base = payload.get('cwd')
    if tool in ('Write', 'Edit', 'MultiEdit') and inp.get('file_path'):
        paths = [inp['file_path']]
    elif tool == 'Bash':
        paths = sorted(bash_targets(inp.get('command', '')))
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
