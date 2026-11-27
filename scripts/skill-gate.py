#!/usr/bin/env python3
"""The publish gate.

NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.

A command that would push, post, merge, close, delete, mark ready or force-push is
refused unless the user typed its slash command in the turn, per skills/shortcuts.md;
so is a commit whose identity is set by hand. A pre-commit hook refuses a gitlink no
remote holds and a workflow script that does not parse. Reading a skill before writing
its artifact is a rule, not something this gate checks.

  ./scripts/skill-gate.py hook-claude   Claude Code PreToolUse adapter on Bash, hook JSON on stdin:
                                        exit 2 with the reason on a refused command
  ./scripts/skill-gate.py pre-commit    the refusals on the commit staged in the repo at cwd

Another harness wires its before-command hook to `hook-claude` when its payload carries
tool_name and tool_input the same way. The commit hook holds without any harness.

Lives in the skills repository as scripts/skill-gate.py; a workspace mounting it at skills/
wires its hooks to skills/scripts/skill-gate.py, or keeps a shim at scripts/skill-gate.py.
"""

import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import urllib.parse
from pathlib import Path

WRAPPERS = {'command', 'exec', 'sudo', 'env', 'nice', 'timeout', 'nohup', 'xargs', 'setsid'}
SHELLS = {'bash', 'sh', 'zsh', 'dash'}
HEREDOC = re.compile(r'(?<!<)<<(?!<)-?\s*([\'"]?)(\w+)\1')


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


def _git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def cmd_pre_commit(cwd):
    top = Path(_git(cwd, 'rev-parse', '--show-toplevel').strip())
    staged = [line for line in _git(cwd, 'diff', '--cached', '--name-only', '--diff-filter=ACMR').splitlines() if line]
    refused = runner_parse_errors(top, staged) + unpushed_gitlinks(top, cwd)
    for line in refused:
        print(f'refused: {line}', file=sys.stderr)
    return 1 if refused else 0


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


def _own_repo_env():
    """The environment minus every variable that ties git to the repository at hand, as `git rev-parse --local-env-vars`
    lists them: a hook in a linked worktree gets an absolute GIT_DIR, and a `git -C <submodule>` under it reads the
    parent's object store."""
    local = set(subprocess.run(['git', 'rev-parse', '--local-env-vars'], capture_output=True, text=True).stdout.split())
    local = local or {'GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY'}
    return {k: v for k, v in os.environ.items() if k not in local}


def unpushed_gitlinks(top, cwd):
    """A staged submodule pointer at a commit no remote branch of that submodule holds: a clone cannot resolve it and
    every later push of this repository is refused over it, so the submodule is pushed first."""
    out = []
    env = _own_repo_env()
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
        def held():
            r = subprocess.run(['git', '-C', str(sub), 'branch', '-r', '--contains', sha], capture_output=True, text=True,
                               env=env)
            return r.returncode == 0 and r.stdout.strip()
        if held():
            continue
        # A fresh worktree's submodule carries the remote-tracking refs of its clone, stale until fetched.
        # Bounded and non-interactive: the hook runs on every commit, network or not.
        quiet = {**env, 'GIT_TERMINAL_PROMPT': '0', 'GIT_SSH_COMMAND': 'ssh -o BatchMode=yes -o ConnectTimeout=10'}
        try:
            subprocess.run(['git', '-C', str(sub), 'fetch', '-q', 'origin'], capture_output=True, env=quiet,
                           stdin=subprocess.DEVNULL, timeout=20)
        except subprocess.TimeoutExpired:
            pass
        if not held():
            out.append(f'{path} points at {sha[:9]}, which no remote branch of that submodule holds: push the submodule '
                       'first, or fetch it where the push already landed')
    return out


# What the user typed this turn: the prompt that opened it and every message queued into it
# while it ran. A publish, a push outside the standing list and a forced push each wait for
# their word there, per Invariants 1, 2, 3 and 8 of the workspace AGENTS.md.
#
# This is a net for an honest agent's slip, read from the command's text, and never a sandbox: a
# shell can send a push in more forms than a reading can follow, a script generated at run time
# for one. Where the reading cannot place a push it asks for the word; the words themselves, in
# AGENTS.md, stay the control.
NOT_TYPED = ('<task-notification', '<command-', '<local-command-', '<system-reminder', '[SYSTEM NOTIFICATION',
             'Another Claude session sent a message:', '<cross-session-message', '<side-sessions-event',
             '<ci-monitor-event', 'Background (from the session that started this one)')
LEADING_REMINDERS = re.compile(r'\s*(?:<system-reminder>.*?</system-reminder>\s*)+', re.S)
COMMAND = '\x1f'  # opens the line turn_text writes for a typed slash command, a character no keyboard types
COMMAND_NAME = re.compile(r'<command-name>(/[\w:-]+)</command-name>')
COMMAND_ARGS = re.compile(r'<command-args>(.*?)</command-args>', re.S)
COMMAND_TAGS = re.compile(r'(?:\s*<command-(message|name|args)>.*?</command-\1>)+\s*', re.S)


def turn_text(transcript):
    """The user's typed text this turn, or None when the transcript cannot be read."""
    try:
        lines = open(transcript, encoding='utf-8', errors='replace').read().split('\n')
    except (OSError, TypeError):
        return None
    rows, raws = [], []
    for line in lines:
        line = line.strip().strip('\x00')
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
            raws.append(line)
    starts = []
    for i, e in enumerate(rows):
        if e.get('type') == 'user' and not e.get('isMeta') and not e.get('isCompactSummary'):
            typed = _said(e)
            if typed is not None:
                starts.append((i, typed))
    if not starts:
        return ''
    # A turn the API killed never finished: a retry typed after it resumes that turn, so the
    # words given there still hold, however many retries it took. A question asked while the
    # request's work still runs ends no word either, per Consent in the workspace AGENTS.md.
    k = len(starts) - 1
    while k > 0 and (RETRY.match(starts[k][1]) and _died(rows[starts[k - 1][0]:starts[k][0]])
                     or _status_question(starts[k][1]) and _still_running(rows, raws, starts[k][0])):
        k -= 1
    parts = []
    for n, (start, first) in enumerate(starts[k:], k):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(rows)
        parts.append(first)
        for e in rows[start + 1:end]:
            a = e.get('attachment') or {}
            if e.get('type') == 'attachment' and a.get('type') == 'queued_command' \
                    and (a.get('origin') or {}).get('kind') == 'human':
                queued = str(a.get('prompt', '')).replace(COMMAND, '')
                parts.append(COMMAND + ' '.join(queued.split()) if queued.startswith('/') else queued)
    return '\n'.join(parts)


RETRY = re.compile(r'(?i)^\s*(try again|retry)\W*$')


def _died(rows):
    """The turn these rows hold ended on an API error rather than a reply."""
    last = next((e for e in reversed(rows) if e.get('type') == 'assistant'), None)
    return bool(last and last.get('isApiErrorMessage'))


# A question about the work in flight: one line, ending on `?` or opening on a word that asks.
ASKS = re.compile(r'(?i)(?:why|what|how|did|does|is|are|where|when|wyd|hello|status|all good|ag|still)\b')
NOTIFIED = re.compile(r'<task-id>([\w-]+)</task-id>|<agent-message from="([\w-]+)"')


def _status_question(text):
    t = text.strip()
    return bool(t) and '\n' not in t and (t.endswith('?') or bool(ASKS.match(t)))


def _still_running(rows, raws, at):
    """Work launched before row `at` reports after it: a notification names a task an earlier row holds."""
    for e in rows[at + 1:]:
        for task in _notified(e):
            if any(task in r for r in raws[:at]):
                return True
    return False


def _notified(e):
    """The tasks a harness notification names; a typed message and a tool result name none."""
    a = e.get('attachment') or {}
    if e.get('type') == 'attachment' and a.get('type') == 'queued_command':
        if (a.get('origin') or {}).get('kind') == 'human':
            return []
        text = str(a.get('prompt', ''))
    elif e.get('type') == 'user':
        if _said(e) is not None:
            return []
        text = _typed(e) or ''
    else:
        return []
    return [x or y for x, y in NOTIFIED.findall(text)]


def _said(e):
    """What the user typed in a user entry, past the reminders the app puts in front of it; None where nobody typed."""
    text = _typed(e)
    if text is None:
        return None
    lead = LEADING_REMINDERS.match(text)
    if lead:
        # A session's message or an event follows a reminder too, and only the human origin tells them apart.
        if (e.get('origin') or {}).get('kind') != 'human' or lead.end() == len(text):
            return None
        text = text[lead.end():]
    # A slash command the user typed reaches the transcript as tags, which turn_text keeps as one COMMAND line; tags
    # it cannot read still open a turn, which then gives nothing, and another session's never count.
    if text.lstrip().startswith('<command-'):
        name = COMMAND_NAME.search(text) if COMMAND_TAGS.fullmatch(text) else None
        if not name or (e.get('origin') or {}).get('kind') not in (None, 'human'):
            return ''
        args = COMMAND_ARGS.search(text)
        return COMMAND + name.group(1) + ' ' + ' '.join((args.group(1) if args else '').split())
    return None if text.lstrip().startswith(NOT_TYPED) else text.replace(COMMAND, '')


def _typed(e):
    """A user entry's typed text: a string, or the text blocks of a list holding no tool result."""
    c = (e.get('message') or {}).get('content')
    if isinstance(c, str):
        return c
    if isinstance(c, list) and c and not any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in c):
        return '\n'.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text')
    return None


# The slash commands that give the gate's words, per skills/shortcuts.md, each under the NAMESPACE that
# commands/<namespace>/ gives it; typed prose gives none. An argument that is itself one of them gives its word too,
# so `/davd:push delete` pushes and deletes. `/davd:push` sends everything the closing block named.
NAMESPACE = 'davd:'
COMMANDS = {
    'push': {'push'}, 'push-review': {'push'}, 'review-loop-push': {'push'}, 'push-force': {'push', 'force'},
    'post': {'post'}, 'review-as-ai': {'post'}, 'fix-as-ai': {'push', 'post'},
    'upload': {'upload'}, 'merge': {'merge'}, 'close': {'close'}, 'delete': {'delete'}, 'ready': {'ready'},
}
PUSH_COVERS = {'push', 'post', 'upload', 'ready'}


def _command(word):
    """A command's name without its slash and namespace; a name outside the namespace is no command."""
    word = word[1:] if word.startswith('/') else word
    return word[len(NAMESPACE):] if word.startswith(NAMESPACE) else ''


def command_words(text):
    """The gate's words the turn's slash commands give, read from the lines turn_text marks with COMMAND."""
    given = set()
    for line in text.splitlines():
        if line.startswith(COMMAND):
            name, *args = line[len(COMMAND):].lower().split() or ['']
            name = _command(name)
            args = [_command(a) or a for a in args]
            words = [name] + args if name in COMMANDS and all(a in COMMANDS for a in args) else [name]
            for word in words:
                given |= COMMANDS.get(word, set())
    return given


def gives_force(text):
    """The turn approves a forced push: `/davd:push-force`."""
    return 'force' in command_words(text)


def gives(text, word):
    """The turn gives the word: a slash command gives it, or `/davd:push`, which carries every word it covers."""
    words = command_words(text)
    if 'push' in words:
        words |= PUSH_COVERS
    return word in words


# A Co-authored-by trailer is refused only where it names a model or a bot: a human reviewer whose
# fix a commit applies is credited with one, per *Commit identity* in skills/git.md.
MARKER = re.compile(r'(?i)co-authored-by:[^\n"]*(?:claude|anthropic|copilot|openai|chatgpt|gemini|\bai\b|\[bot\])'
                    r'|generated with \[?claude|assisted by ai|\U0001F916')
SHELL_LEAD = {'do', 'then', 'else', 'elif', 'if', 'while', 'until', '{', '(', '!', 'and', 'or', 'not'}
RUNNERS = {'bash', 'sh', 'zsh', 'fish', 'python', 'python3'}
# A wrapper and the options it takes a value for; its first bare word after them may be its own argument.
WRAPPERS = {'timeout': ({'-s', '--signal', '-k', '--kill-after'}, 1), 'nice': ({'-n', '--adjustment'}, 0),
            'sudo': ({'-u', '-g', '-C', '-h', '-p', '-U'}, 0), 'env': ({'-u', '--unset', '-C', '--chdir'}, 0),
            'xargs': ({'-I', '-L', '-n', '-P', '-d', '-E', '-s', '-a'}, 0), 'time': ({'-f', '-o'}, 0),
            'stdbuf': ({'-i', '-o', '-e'}, 0), 'nohup': (set(), 0), 'exec': ({'-a'}, 0), 'command': (set(), 0)}


SHELLS = {'bash', 'sh', 'zsh', 'fish', 'dash'}
POST_SCRIPTS = {'post', 'post-review.sh', 'post-replies', 'post-fix.sh', 'post-pr-review.py', 'pr-body-apply'}


def _names(cmd):
    """The shell variables a line assigns, NAME=value, for filling a path or a repository."""
    return dict(re.findall(r'(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=["\']?([^\s;&|()"\']+)', cmd))


def _fill(v, names):
    for _ in range(4):
        v = re.sub(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', lambda m: names.get(m.group(1), os.environ.get(m.group(1), m.group(0))), v)
    return os.path.expanduser(v.strip('"\''))


def _shell_script(cmd, path, cwd=None):
    """What a shell runs from a file or from stdin: the file, the heredoc this line writes into it,
    or the heredoc fed straight to the shell. The workspace's own scripts/ are its tooling, governed
    by their own words, and are not read."""
    names = _names(cmd)
    if path:
        full = os.path.realpath(os.path.join(cwd or os.getcwd(), _fill(path, names)))
        tooling = [str(root() / 'scripts'), str(root() / 'skills' / 'scripts')]
        if any(full.startswith(d + os.sep) for d in tooling):
            return None
        try:
            if os.path.isfile(full):
                return _to_exit(open(full, encoding='utf-8', errors='replace').read())
        except (OSError, ValueError):
            pass
        for m in re.finditer(r'>\s*(\S+)\s*<<-?\s*([\'"]?)(\w+)\2.*?\n(.*?)\n\s*\3\b', cmd, re.S):
            if os.path.realpath(os.path.join(cwd or os.getcwd(), _fill(m.group(1), names))) == full:
                return _to_exit(m.group(4))
        return None
    bodies = [m.group(4) for m in re.finditer(r'\b(bash|sh|zsh|dash)\b[^\n]*?<<-?\s*([\'"]?)(\w+)\2.*?\n(.*?)\n\s*\3\b', cmd, re.S)]
    return '\n'.join(bodies) or None


def _to_exit(script):
    """A script up to its first top-level exit: what follows it never runs as shell."""
    m = re.search(r'^exit\b.*$', script, re.M)
    return script[:m.start()] if m else script


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


def _split(cmd, ops=False):
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=';&|\n()<>')
    lex.whitespace = ' \t\r'
    lex.whitespace_split = True
    seg = []
    try:
        for tok in lex:
            if tok and set(tok) <= set(';&|\n()'):
                if seg:
                    yield seg
                seg = []
                if ops:
                    for ch in tok:
                        if ch in '()':
                            yield ['\x00' + ch]
            else:
                seg.append(tok)
    except ValueError:
        for line in cmd.split('\n'):
            for part in re.split(r'&&|\|\||;|\||\(|\)', line):
                if part.split():
                    yield part.split()
        return
    if seg:
        yield seg


def _shell_files(t):
    """A shell's operands past its options: -o, -O, +o and +O take a value, and so does a cluster ending in o or O."""
    out, i = [], 1
    while i < len(t):
        x = t[i]
        if x in ('-o', '+o', '-O', '+O') or re.match(r'^[-+][A-Za-z]*[oO]$', x):
            i += 2
            continue
        if not x.startswith(('-', '+')):
            out.append(x)
        i += 1
    return out


def _segments(cmd, depth=0, ops=False, cwd=None, collect=None):
    """The simple commands of a shell line: heredoc bodies dropped, split outside quotes, a leading
    keyword, environment assignment or $( stripped, and a `bash -c` string read as its own line."""
    here = cwd
    for t in _split(_strip_heredocs(cmd), ops):
        if t and t[0].startswith('\x00'):
            yield t
            continue
        if len(t) >= 2 and t[0] in ('cd', 'pushd') and here:
            here = os.path.join(here, _fill(t[1], _names(cmd)))
        t = [x.rstrip('$').lstrip('`') for x in t]
        t = [x for x in t if x]
        while t:
            head = os.path.basename(t[0])
            if t[0] in SHELL_LEAD or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t[0]):
                t = t[1:]
            elif head in WRAPPERS:
                takes, bare = WRAPPERS[head]
                i = 1
                while i < len(t) and (t[i].startswith('-') or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t[i])):
                    i += 2 if t[i] in takes else 1
                t = t[i + bare:]
            else:
                break
        kept, drop = [], False
        for x in t:
            if drop:
                drop = False
            elif x and set(x) <= set('<>&-') and ('<' in x or '>' in x):
                # A redirection: the operator, its target and a file-descriptor number before it.
                if kept and kept[-1].isdigit():
                    kept.pop()
                drop = True
            else:
                kept.append(x)
        t = kept
        if not t:
            continue
        files = _shell_files(t) if os.path.basename(t[0]) in SHELLS else [x for x in t[1:] if not x.startswith('-')]
        if os.path.basename(t[0]) in SHELLS and any(re.match(r'^-[A-Za-z]*n[A-Za-z]*$', x) for x in t[1:]):
            continue  # -n reads a script for syntax and runs nothing
        if os.path.basename(t[0]) in SHELLS and files and os.path.basename(files[0]) in POST_SCRIPTS:
            t = t[t.index(files[0]):]
        elif os.path.basename(t[0]) in SHELLS and depth < 3 and not any(re.match(r'^-[A-Za-z]*c[A-Za-z]*$', x) for x in t[1:]):
            if any(re.match(r'^-[A-Za-z]*n[A-Za-z]*$', x) for x in t[1:]):
                continue  # -n reads the script for syntax and runs nothing
            script = _shell_script(cmd, files[0] if files else None, here)
            if script:
                if collect is not None:
                    collect.append(script)
                # A script runs in a shell of its own: its cd ends with it.
                if ops:
                    yield ['\x00(']
                yield from _segments(script, depth + 1, ops, here, collect)
                if ops:
                    yield ['\x00)']
            continue
        if t[0] == 'eval' and depth < 3:
            yield from _segments(' '.join(t[1:]), depth + 1)
            continue
        if os.path.basename(t[0]) in RUNNERS and depth < 3:
            i, script = 1, None
            while i < len(t) and t[i].startswith(('-', '+')):
                if t[i] in ('-o', '+o', '-O', '+O') or re.match(r'^[-+][A-Za-z]*[oO]$', t[i]):
                    i += 2
                    continue
                if re.match(r'^-[A-Za-z]*c[A-Za-z]*$', t[i]) and i + 1 < len(t):
                    script = t[i + 1]
                    break
                i += 1
            if script is not None:
                yield from _segments(script, depth + 1, ops)
                continue
        if os.path.basename(t[0]) in RUNNERS and len(t) > 1 and not t[1].startswith('-'):
            t = t[1:]
        t[0] = os.path.basename(t[0]) if t[0].endswith(('/gh', '/git')) else t[0]
        yield t


def _dry(tokens):
    return any(x in ('--dry-run', '--help', '-h', '--list') for x in tokens)


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


def every_change_repos():
    try:
        return {norm_repo(r) for r in json.loads((root() / 'workspace.json').read_text()).get('word_for_every_change', [])}
    except (OSError, ValueError):
        return set()


def norm_repo(x):
    x = re.sub(r'^(https?://)?(www\.)?github\.com[:/]', '', x.strip().strip('"\'')).rstrip('/')
    x = re.sub(r'\.git$', '', x)
    return '/'.join(x.split('/')[:2]).lower()


def _gh_repos(t, cwd, line=''):
    out = {norm_repo(v) for v in re.findall(r'\bGH_REPO=(\S+)', line)}
    for i, x in enumerate(t):
        if x in ('-R', '--repo') and i + 1 < len(t):
            out.add(norm_repo(t[i + 1]))
        elif x.startswith('--repo='):
            out.add(norm_repo(x.split('=', 1)[1]))
        elif x.startswith('-R') and len(x) > 2:
            out.add(norm_repo(x[2:]))
        m = re.match(r'https://github\.com/([^/\s]+/[^/\s]+)/pull/\d+', x)
        if m:
            out.add(norm_repo(m.group(1)))
    if not out and cwd:
        out |= _remote_repos(cwd)
    return out


def _remote_repos(cwd):
    remotes = subprocess.run(['git', '-C', cwd, 'remote', '-v'], capture_output=True, text=True).stdout
    return {norm_repo(f'{a}/{b}') for a, b in re.findall(r'github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?\s', remotes)}


def own_login():
    try:
        return json.loads((root() / 'workspace.json').read_text())['identities']['public']['name'].lower()
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _closes_own_quietly(t, cwd, line=''):
    """Whether a gh pr close targets only the user's own repositories and says nothing and deletes nothing."""
    login, repos = own_login(), _gh_repos(t, cwd, line)
    loud = any(x.split('=')[0] in ('-c', '--comment', '-d', '--delete-branch') for x in t)
    return bool(login and repos) and not loud and all(r.split('/')[0] == login for r in repos)


def standing_publish_draft():
    """The repositories where the user's own draft pull request, its text and its comments go up unasked."""
    try:
        return {norm_repo(r) for r in json.loads((root() / 'workspace.json').read_text()).get('standing_publish_draft', [])}
    except (OSError, ValueError):
        return set()


def standing_publish_review():
    """The repositories where a finished review round's draft goes up unasked, behind the AI marker."""
    try:
        return {norm_repo(r) for r in json.loads((root() / 'workspace.json').read_text()).get('standing_publish_review', [])}
    except (OSError, ValueError):
        return set()


def standing_issue_edit():
    """The issues, each `owner/repo#number`, whose body goes up unasked."""
    try:
        return {x.lower() for x in json.loads((root() / 'workspace.json').read_text()).get('standing_issue_edit', [])}
    except (OSError, ValueError):
        return set()


def _own_draft(repo, number):
    """Whether a pull request is an open draft the user authored; a failed read keeps the word."""
    out = _gh_api(f'repos/{repo}/pulls/{number}', '[.state, .draft, .user.login] | map(tostring | ascii_downcase) | @tsv')
    return bool(out) and out.split() == ['open', 'true', own_login()]


def _gh_target(t):
    """The pull request or issue number a gh verb names: its URL, or its first argument that no flag takes."""
    for x in t:
        m = re.match(r'https://github\.com/[^/\s]+/[^/\s]+/(?:pull|issues)/(\d+)', x)
        if m:
            return m.group(1)
    r = _gh_verb(t)
    return next((x for i, x in enumerate(r) if i > 1 and x.isdigit() and not r[i - 1].startswith('-')), None)


def _drafts_only(t, cwd, line=''):
    """Whether a gh verb posts only on the user's own draft, on a repository whose standing word covers one."""
    repos, number = _gh_repos(t, cwd, line), _gh_target(t)
    return bool(number and repos) and repos <= standing_publish_draft() and all(_own_draft(r, number) for r in repos)


def _post_fix_opens_draft(t, cwd):
    """Whether post-fix.sh opens a pull request alone, on a repository whose standing word covers a draft."""
    dirs = [Path(cwd or os.getcwd(), x) for x in t[1:] if not x.startswith('-')]
    if not dirs or ('--pr-only' not in t and any((d / 'issue.md').is_file() for d in dirs)):
        return False
    try:
        bodies = [d / 'pr-body.md' for d in dirs if (d / 'pr-body.md').is_file()]
        heads = [re.search(r'^Target:\s*https://github\.com/([^/\s]+/[^/\s]+)/compare/', b.read_text(), re.M) for b in bodies]
    except OSError:
        return False
    return bool(heads) and all(m and norm_repo(m.group(1)) in standing_publish_draft() for m in heads)


def _sends_finished_round(t, cwd):
    """Whether post-review.sh sends one draft with `--as-ai` its one flag, to a repository whose standing word covers a round."""
    args = [x for x in t[1:] if not re.fullmatch(r'\d*>\S*', x)]
    drafts = [x for x in args if x != '--as-ai']
    if len(args) != 2 or len(drafts) != 1 or drafts[0].startswith('-'):
        return False
    try:
        title = Path(cwd or os.getcwd(), drafts[0]).read_text().split('\n', 1)[0]
    except OSError:
        return False
    m = re.search(r'\(https://github\.com/([^/\s]+/[^/\s]+)/pull/\d+\)', title)
    return bool(m) and norm_repo(m.group(1)) in standing_publish_review()


def _edits_beyond_body(t):
    """Whether a gh pr edit sets anything but the body: a flag's value, `-` for stdin among them, is skipped."""
    free, i = ('--body', '-b', '--body-file', '-F', '-R', '--repo'), 3
    while i < len(t):
        x = t[i]
        if x.split('=')[0] in free:
            i += 1 if '=' in x else 2
            continue
        if x.startswith('-') and x != '-':
            return True
        i += 1
    return False


def publish_words(cmd, cwd=None):
    """Each set is one publish on the line, satisfied by any of its words; every set needs its own."""
    needs = []
    strict = every_change_repos()
    own = standing_publish() - strict
    read = []
    list(_segments(cmd, cwd=cwd, collect=read))
    names = _names('\n'.join([cmd] + read))
    for t in _segments(cmd, cwd=cwd):
        t = [_fill(x, names) if '$' in x and not x.startswith('$(') else x for x in t]
        if len(t) >= 2 and t[0] in ('cd', 'pushd'):
            cwd = os.path.join(cwd or os.getcwd(), os.path.expanduser(t[1].strip('"\'')))
            continue
        name = os.path.basename(t[0])
        # A draft on a repository listed in standing_publish_draft waits for no word, per Consent in AGENTS.md.
        pos = [x for x in t[1:] if not x.startswith('-')]
        if name == 'post-fix.sh' and _post_fix_opens_draft(t, cwd):
            continue
        # --record-read writes the body's hash into the local draft and exits before any call to GitHub.
        if name == 'post-fix.sh' and '--record-read' in t:
            continue
        if name == 'post-replies' and len(pos) >= 2 and norm_repo(pos[0]) in standing_publish_draft() \
                and _own_draft(norm_repo(pos[0]), pos[1]):
            continue
        if name == 'post-review.sh' and _sends_finished_round(t, cwd):
            continue
        if name in POST_SCRIPTS - {'pr-body-apply'} and not _dry(t):
            needs.append({'post', 'upload'})
        # pr-body-apply needs no word: it refuses a pull request the signed-in account
        # did not author, and a revised body on the user's own one is a standing word.
        if t[0] != 'gh':
            continue
        r = _gh_verb(t)
        if len(r) < 2:
            continue
        verb = (r[0], r[1])
        # Opening, editing, commenting on or readying a pull request on the user's own repository
        # waits for no word; a merge, a close and a delete still do.
        if own and verb in {('pr', 'create'), ('pr', 'comment'), ('pr', 'review'), ('pr', 'edit'), ('pr', 'ready'),
                            ('issue', 'comment')}:
            repos = _gh_repos(t, cwd, cmd)
            if repos and repos <= own:
                continue
        if verb == ('pr', 'create') and {'--draft', '-d'} & set(t):
            repos = _gh_repos(t, cwd, cmd)
            if repos and repos <= standing_publish_draft():
                continue
        if verb in {('pr', 'comment'), ('pr', 'edit'), ('issue', 'comment')} and _drafts_only(t, cwd, cmd):
            continue
        if verb == ('issue', 'edit') and not _edits_beyond_body(t):
            repos, number = _gh_repos(t, cwd, cmd), _gh_target(t)
            if number and repos and all(f'{r}#{number}' in standing_issue_edit() for r in repos):
                continue
        if verb in {('pr', 'create'), ('pr', 'comment'), ('pr', 'review'), ('pr', 'reopen'), ('issue', 'create'),
                    ('issue', 'comment'), ('issue', 'reopen'), ('issue', 'edit'), ('issue', 'lock'), ('issue', 'transfer'),
                    ('release', 'create'), ('release', 'upload'), ('gist', 'create'), ('repo', 'create'), ('repo', 'edit')}:
            needs.append({'post'})
        elif verb == ('pr', 'ready'):
            needs.append({'post', 'ready'})
        elif verb == ('pr', 'merge'):
            needs.append({'merge'})
        elif verb == ('pr', 'close') and _closes_own_quietly(t, cwd, cmd):
            # The fork's pull request closes unasked once the upstream one opens, per *Presenting the
            # change* in skills/change.md: a close with no comment on the user's own repository.
            continue
        elif verb in {('pr', 'close'), ('issue', 'close')}:
            needs.append({'close'})
        elif r[1] == 'delete':
            needs.append({'delete'})
        elif verb == ('repo', 'sync'):
            # A sync writes a branch of the user's repository: a push, and with --force a reset,
            # which Invariant 8 never allows.
            needs.append({'\x00never'} if '--force' in t else {'push'})
        elif verb == ('pr', 'edit') and (_gh_repos(t, cwd, cmd) & strict or _edits_beyond_body(t)):
            # Consent lets an open pull request's body go up unasked; a title, a label, a reviewer or a
            # base on it, and any change where every change takes the word, wait for post.
            needs.append({'post'})
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
            path = next((x for x in r[1:] if not x.startswith('-') and ('/' in x or x in ('graphql', 'markdown'))), '')
            if path.lstrip('/').split('/')[0] == 'markdown':
                continue
            if path == 'graphql':
                base = cwd or os.getcwd()
                sources = [v.split('=', 1)[1] for v in fields if v.startswith('query=')]
                if has_input and t.index('--input') + 1 < len(t):
                    sources.append('@' + t[t.index('--input') + 1])
                query, unreadable = '', False
                for src in sources:
                    # A GraphQL variable, `($org: String!)` or `login: $org`, follows `(`, `,`, `:` or `[`;
                    # a `$` anywhere else is the shell's, and what it expands to is unread.
                    if '$' in re.sub(r'([(,:\[]\s*)\$[A-Za-z_]\w*', r'\1', src) or '`' in src:
                        unreadable = True
                    elif src.startswith('@'):
                        path_ = os.path.join(base, os.path.expanduser(src[1:]))
                        if os.path.isfile(path_):
                            query += _read_at('@' + path_)
                        else:
                            unreadable = True
                    else:
                        query += src
                bodies = ' '.join(m.group(3) for m in re.finditer(r'<<-?\s*([\'"]?)(\w+)\1.*?\n(.*?)\n\s*\2\b', cmd, re.S))
                if unreadable or re.search(r'\bmutation\b', query) or re.search(r'\bmutation\b', bodies):
                    needs.append({'post'})
                continue
            method = method or ('POST' if fields or has_input else 'GET')
            if method == 'GET':
                continue
            # An open pull request's own body or title edit goes up unasked, per Consent in AGENTS.md.
            keys = {v.split('=', 1)[0] for v in fields}
            repo = norm_repo('/'.join(path.lstrip('/').split('/')[1:3])) if path.lstrip('/').startswith('repos/') else ''
            if '{owner}' in path or '{repo}' in path:
                here_repos = _remote_repos(cwd) if cwd else set()
                repo = next(iter(here_repos & strict), next(iter(here_repos), ''))
            if method == 'PATCH' and re.search(r'/pulls/(\d+|\$\{?\w+\}?)/?$', path) and keys and keys <= {'body'} \
                    and repo not in strict:
                continue
            if method == 'PUT' and '/contents/' in path:
                # A file written to a repository's branch is a push: free on a standing repository.
                if repo in {norm_repo(x) for x in standing_push()}:
                    continue
                needs.append({'upload', 'push'})
                continue
            # Taking a label, an assignee or a reviewer off an issue or a pull request edits it:
            # post, as adding one does. Any other DELETE removes the thing itself.
            edit = re.search(r'/issues/[^/]+/(labels|assignees)(/|$)|/pulls/[^/]+/requested_reviewers/?$', path)
            if method == 'DELETE' and not edit:
                needs.append({'delete'})
            # A merge, a close and a new issue keep their own words on the user's repositories too.
            elif re.search(r'/pulls/[^/]+/merge/?$', path):
                needs.append({'merge'})
            elif 'state=closed' in fields or re.search(r'"state"\s*:\s*"closed"', body := (
                    _read_at('@' + t[t.index('--input') + 1]) if has_input and t.index('--input') + 1 < len(t) else '')):
                needs.append({'close'})
            elif body.startswith('@'):
                # an --input file the gate cannot read could carry anything
                needs.append({'post'})
            elif method == 'POST' and re.search(r'/issues/?$', path):
                needs.append({'post'})
            elif repo in own and re.search(r'/(pulls|issues)(/|$)', path):
                continue
            elif repo in standing_publish_draft() and not keys & {'state', 'draft', 'base'} \
                    and (m := re.search(r'/(?:pulls|issues)/(\d+)(?:/(?:comments(?:/\d+/replies)?|labels(?:/[^/]+)?))?/?$', path)) \
                    and _own_draft(repo, m.group(1)):
                continue
            else:
                needs.append({'post'})
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
            elif x in ('--body-file', '-F', '--file') and i + 1 < len(t) and t[i + 1] != '-':
                out.append(_read_at('@' + t[i + 1]))
            elif x.startswith(('--file=', '--body-file=')):
                out.append(_read_at('@' + x.split('=', 1)[1]))
    for t in _segments(cmd):
        commits = t and (t[0].endswith('scripts/commit') or (t[0] == 'git' and _git_sub(t)[0] == 'commit'))
        from_heredoc = any('<<' in x or x == 'cat' for x in t) or any(
            x in ('-F', '--file') and i + 1 < len(t) and t[i + 1] == '-' for i, x in enumerate(t))
        if commits and from_heredoc:
            # A message written through $(cat <<EOF ...) or -F - <<EOF lives in the heredoc body the
            # segmenter drops, so the bodies on this line are read for the marker.
            out.extend(m.group(0) for m in re.finditer(r'<<-?\s*([\'"]?)(\w+)\1.*?\n(.*?)\n\s*\2\b', cmd, re.S))
    return out


def push_targets(cmd, cwd):
    """(repository, forced, deleted, branches) for each git push on the line; repository is owner/name or None, and
    branches the remote branch each refspec writes, or None where one cannot be named."""
    out = []
    here = cwd or os.getcwd()
    here_raw = ''
    read = []
    list(_segments(cmd, cwd=here, collect=read))
    cmd_all = '\n'.join([cmd] + read)
    names = dict(re.findall(r'(?:^|[\s;&|(])([A-Za-z_][A-Za-z0-9_]*)=["\']?([^\s;&|()"\']+)', cmd_all))

    def fill(v):
        for _ in range(4):  # a name defined through another name, R=...; C=$R/x
            v = re.sub(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', lambda m: names.get(m.group(1), os.environ.get(m.group(1), m.group(0))), v)
        return os.path.expanduser(v.strip('"\''))
    stack = []
    temp_names = set(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)=["\']?\$\(mktemp\b', cmd))
    made = set()
    for t in _segments(cmd):
        if t[0] == 'git' and _git_sub(t)[0] in ('init', 'clone'):
            dests = [x for x in t[_git_sub(t)[1] + 1:] if not x.startswith('-')]
            if dests:
                made.add(dests[-1].rstrip('/'))

    # A line that points a remote, a git dir or a repository somewhere, runs a function or pops a
    # directory can send a push anywhere: every push on it waits for the word.
    # Read outside quotes and heredoc bodies, so an email address or a sentence never counts.
    bare = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", ' ', _strip_heredocs(cmd))
    unsure = bool(re.search(r'\bremote\s+(add|set-url)\b|--git-dir|\bGIT_DIR=|'
                            r'\bGIT_WORK_TREE=|\bpopd\b|\(\)\s*\{|(^|[;&|\n])\s*function\s+\w', bare))
    for t in _segments(cmd):
        if t[0] == 'git' and _git_sub(t)[0] == 'config':
            rest_c = t[_git_sub(t)[1] + 1:]
            if not any(x in ('--get', '--get-all', '--get-regexp', '--list', '-l', '--show-origin', '--show-scope')
                       for x in rest_c) and len([x for x in rest_c if not x.startswith('-')]) >= 2:
                unsure = True
        if t[0] == 'git' and _git_sub(t)[0] == 'clone':
            src = [x for x in t[_git_sub(t)[1] + 1:] if not x.startswith('-')]
            if src and re.match(r'^(https?://|ssh://|git@|[\w.-]+@[\w.-]+:)', src[0]):
                unsure = True

    def scratch(raw):
        raw = raw.strip('"\'').rstrip('/')
        if unsure or '..' in raw.split('/'):
            return False
        head = re.match(r'^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', raw)
        return bool(head and head.group(1) in temp_names) or any(raw == d or raw.startswith(d + '/') for d in made)
    for t in _segments(cmd, ops=True, cwd=cwd or os.getcwd()):
        if t == ['\x00(']:
            stack.append((here, here_raw))
            continue
        if t == ['\x00)']:
            here, here_raw = stack.pop() if stack else (here, here_raw)
            continue
        if len(t) >= 2 and t[0] in ('cd', 'pushd'):
            here, here_raw = os.path.join(here, fill(t[1])), t[1]
            continue
        if t[0] != 'git':
            continue
        sub, at = _git_sub(t)
        if sub != 'push':
            continue
        where, raw = here, here_raw
        for i, x in enumerate(t[:at]):
            if x == '-C' and i + 1 < len(t):
                where, raw = os.path.join(here, fill(t[i + 1])), t[i + 1]
            elif x.startswith('-C') and len(x) > 2:
                where, raw = os.path.join(here, fill(x[2:])), x[2:]
        rest, drop = [], False
        for x in t[at + 1:]:
            if drop:
                drop = False
            elif x in ('>', '>>', '<', '2>', '1>', '&>', '2>>'):
                drop = True
            elif not re.match(r'^\d*[<>]', x):
                rest.append(x)
        if '--dry-run' in rest or '-n' in rest:
            continue
        if any(x.startswith('--recurse-submodules') and not x.endswith(('=no', '=check')) for x in rest):
            out.append((None, False, False, None))
        forced = any(x in ('--force', '--mirror') or x.startswith(('--force-with-lease', '--force-if-includes'))
                     or (x.startswith('-') and not x.startswith('--') and 'f' in x[1:]) for x in rest) \
            or any(x.startswith('+') for x in rest if not x.startswith('-'))
        args, skip, repo_flag = [], None, None
        for x in rest:
            if skip:
                if skip == '--repo':
                    repo_flag = x
                skip = None
            elif x in ('-o', '--push-option', '--repo', '--receive-pack', '--exec'):
                skip = x
            elif x.startswith('--repo='):
                repo_flag = x.split('=', 1)[1]
            elif not x.startswith('-'):
                args.append(x)
        remote = fill(repo_flag or (args[0] if args else 'origin'))
        url = subprocess.run(['git', '-C', where, 'remote', 'get-url', remote], capture_output=True, text=True).stdout.strip()
        if not url and ('/' in remote or ':' in remote):
            url = remote
        # A push to a path on this machine publishes nothing, and neither does one to a repository
        # this same line creates with no GitHub URL on it.
        if url.startswith(('file://', '/', './', '../')) or (url and os.path.isdir(os.path.join(where, url))) \
                or (not url and scratch(raw)):
            continue
        deleted = '--delete' in rest or '-d' in rest or any(x.startswith(':') for x in args[1:])
        m = re.search(r'github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$', url)
        out.append((None if unsure or not m else norm_repo(f'{m.group(1)}/{m.group(2)}'), forced, deleted,
                    pushed_branches([fill(x) for x in (args if repo_flag else args[1:])], where)))
    for t in _segments(cmd):
        # git subtree push, and a git alias defined on the line, push where the gate cannot read.
        if t[0] == 'git' and _git_sub(t)[0] in ('subtree', 'submodule') and 'push' in t:
            out.append((None, False, False, None))
    return out


def pushed_branches(refspecs, where):
    """The remote branch each refspec writes, the checked-out one for a bare push or HEAD; None when any writes no
    branch the gate can name: a tag, a wildcard, a shell value, a detached HEAD."""
    out = []
    for x in refspecs or ['HEAD']:
        dst = x.lstrip('+').split(':', 1)[-1]
        if dst == 'HEAD':
            dst = subprocess.run(['git', '-C', where, 'symbolic-ref', '-q', '--short', 'HEAD'],
                                 capture_output=True, text=True).stdout.strip()
        dst = dst[len('refs/heads/'):] if dst.startswith('refs/heads/') else dst
        if not dst or dst.startswith('refs/') or re.search(r'[*$`\s]', dst):
            return None
        out.append(dst)
    return out


def standing_push():
    try:
        return set(json.loads((root() / 'workspace.json').read_text()).get('standing_push', []))
    except (OSError, ValueError):
        return set()


def standing_push_draft():
    """The standing repositories whose word covers a draft pull request's branch alone: a ready one's waits for push."""
    try:
        return {norm_repo(r) for r in json.loads((root() / 'workspace.json').read_text()).get('standing_push_draft', [])}
    except (OSError, ValueError):
        return set()


PR_LOOKUP_TIMEOUT = 5


def _gh_api(path, jq):
    """gh api's output, or None when the call fails, times out or gh is absent."""
    try:
        run = subprocess.run(['gh', 'api', path, '--jq', jq], capture_output=True, text=True, timeout=PR_LOOKUP_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return run.stdout if run.returncode == 0 else None


def head_pr_state(repo, branches):
    """`draft` when every pushed branch heads an open draft pull request, on the repository or its parent; `ready` when
    any heads a ready one; None when one heads none, or GitHub cannot be asked, and the standing list decides."""
    parent = _gh_api(f'repos/{repo}', '.parent.full_name // empty')
    if parent is None:
        return None
    states = set()
    for branch in branches:
        drafts = []
        for base in dict.fromkeys([repo] + parent.split()):
            q = urllib.parse.quote(f'{repo.split("/")[0]}:{branch}', safe='')
            out = _gh_api(f'repos/{base}/pulls?state=open&per_page=100&head={q}',
                          f'.[] | select(.head.repo.full_name | ascii_downcase == "{repo}") | .draft')
            if out is None:
                return None
            drafts += out.split()
        states.add('ready' if 'false' in drafts else 'draft' if drafts else None)
    return 'ready' if 'ready' in states else 'draft' if states == {'draft'} else None


def standing_publish():
    """The user's own repositories where a pull request, its text and its comments go up unasked."""
    try:
        return {norm_repo(r) for r in json.loads((root() / 'workspace.json').read_text()).get('standing_publish', [])}
    except (OSError, ValueError):
        return set()


def refusal(cmd, payload):
    """Why this command waits for a word the turn does not carry, or None."""
    for msg in commit_messages(cmd):
        if MARKER.search(msg):
            return ('an AI-authorship marker in a commit or post message: no Co-Authored-By naming a model, no "Generated with", '
                    'no "Assisted by AI", per Invariant 7 of the workspace AGENTS.md.')
    needs = publish_words(cmd, payload.get('cwd'))
    if {'\x00never'} in needs:
        return 'a forced sync resets a remote branch, which Invariant 8 of the workspace AGENTS.md never allows.'
    standing = {norm_repo(x) for x in standing_push()}
    draft_only, login = standing_push_draft(), own_login()
    pushes = []
    for r, f, d, branches in push_targets(cmd, payload.get('cwd')):
        # A draft pull request's branch goes up unasked on a repository the user owns, and a ready one's waits for
        # push where the standing word covers drafts alone, per Consent; no pull request keeps the standing list's answer.
        state = None
        if not (f or d) and r and branches and (r in draft_only or (r not in standing and r.split('/')[0] == login)):
            state = head_pr_state(r, branches)
        if f or d or state == 'ready' or (r not in standing and state != 'draft'):
            pushes.append((r, f, d, state == 'ready' and r in standing))
    if not needs and not pushes:
        return None
    text = turn_text(payload.get('transcript_path') or '')
    if text is None:
        return 'the transcript is unreadable, so the word this command waits for cannot be confirmed.'
    for need in needs:
        if not any(gives(text, w) for w in need):
            return (f'a publish waiting for its word, {" or ".join(sorted(need))}, which this turn does not carry, '
                    'per Invariants 1 and 2 of the workspace AGENTS.md. Show the draft and name the word.')
    for repo, forced, deleted, ready in pushes:
        if deleted and not gives(text, 'delete'):
            return 'a branch delete, which waits for its word, delete, per Invariant 1 of the workspace AGENTS.md.'
        if forced and not gives_force(text):
            return 'a forced push, which waits for approval in the turn, per Invariant 8 of the workspace AGENTS.md.'
        if ready and not gives(text, 'push'):
            return (f'a push to {repo}, the head branch of a ready pull request, which waits for push: the standing word '
                    'covers a draft pull request\'s branch alone, per Consent in the workspace AGENTS.md.')
        if repo not in standing and not gives(text, 'push'):
            return (f'a push to {repo or "a repository it cannot resolve"}, which no standing word covers and this '
                    'turn does not name with push, per Consent in the workspace AGENTS.md.')
    return None


def cmd_hook_claude(stdin, stdout):
    """A Bash command that would publish, push or force without the user's command in the turn is refused."""
    payload = json.load(stdin)
    tool = payload.get('tool_name', '')
    inp = payload.get('tool_input', {}) or {}
    if tool == 'Bash':
        cmd = inp.get('command', '')
        # The invocation itself, never a message quoting the words: `git -c user.name=... commit` or
        # `git commit ... --author=`, on one command line.
        if (re.search(r'\bgit\b[^\n|;&]*?\s-c\s*user\.(name|email)=[^\n|;&]*\bcommit\b', cmd)
                or re.search(r'\bgit\b[^\n|;&]*\bcommit\b[^\n|;&]*\s--author[= ]', cmd)):
            print('Refused: a git commit that sets user.name, user.email or --author by hand. The identity is the '
                  'checkout\'s pin and the verb: ./scripts/commit -m <message> <path>..., per Commit identity in skills/git.md.', file=sys.stderr)
            return 2
        try:
            why = refusal(cmd, payload)
        except Exception as e:  # a parse the gate cannot finish: refuse what may publish, pass the rest
            why = (f'the gate could not read this command ({type(e).__name__}); it may publish or push, so name the word.'
                   if re.search(r'\b(push|gh|post|merge|curl)\b', cmd) else None)
        if why:
            print(f'Refused: {why}', file=sys.stderr)
            return 2
    return 0


def main(argv, stdin=None, stdout=None, cwd=None):
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    op, args = argv[0], argv[1:]
    try:
        if op == 'pre-commit':
            return cmd_pre_commit(cwd or os.getcwd())
        if op == 'hook-claude':
            return cmd_hook_claude(stdin or sys.stdin, stdout or sys.stdout)
    except Exception as e:  # a hook that cannot decide says so and never blocks
        print(f'skill-gate: {e}', file=sys.stderr)
        return 0
    print(f'unknown command: {" ".join(argv)}', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
