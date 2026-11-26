#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
"""Refuse a commit that adds words to the rule files, unless the user said it may grow.

    rule-growth.py commit-msg <message file> [<pathspec>...]   from the commit-msg hook
    rule-growth.py pre-push [<pathspec>...]                     from the pre-push hook, ref lines on stdin

*What a new rule displaces* in authoring.md: the corpus stays flat, so a commit
adding words to the rule files removes as many in the same commit, across
files. One that cannot carries a line the user's answer in the turn puts there:

    Grows: <why nothing could go>

The template, however wrapped, bare words like `none` or `yes ok`, or a line
with no word of three letters is no answer. A Grows: line covers its whole
commit, so an amend keeping it covers what the amend adds. Words are
whitespace-separated, so a reworded sentence that adds one word grows the rules
too.

The rule files default to the Markdown files at the repository root and
directly under `pr-body/`, any README.md and TODO.md aside: this repository's
layout, and a consumer's root files where its hooksPath points here. A hook
passes its own pathspecs for another layout. A git hook runs whatever harness or model made
the commit.

A commit is measured against HEAD, an amend included: it is refused for adding
words to the commit it replaces even where that commit shrank, and passes when
it only drops the Grows: line; pre-push measures it against its real parent. A
merge is not measured: what each side added is measured in that side's own
commits, and a resolution that adds words of its own passes. pre-push measures
every commit a push carries, a branch's or a tag's, that neither the remote's
old tip nor a remote-tracking ref holds, so a commit made with `--no-verify`,
by a cherry-pick, a revert or a rebase is measured there; a revert restoring
cut words grows the rules like any other commit. Exit 1 on a refusal, 2 when
git cannot answer.
"""
import os
import re
import subprocess
import sys

DEFAULT = [':(glob)*.md', ':(glob)pr-body/*.md', ':(exclude,glob)**/README.md', ':(exclude,glob)**/TODO.md']
LINE = re.compile(r'^\s*grows:(.*)$', re.I)
TEMPLATE = 'whynothingcouldgo'   # the reason the refusal prints, letters only; authoring.md prints its start
BARE = {'no', 'none', 'nothing', 'yes', 'ok', 'todo', 'tbd'}
SCISSORS = '------------------------ >8 ------------------------'   # `commit -v` puts the diff below it
ASK = ('Cut as many words from the rule files in the same commit, whole rules per *What a new rule '
       'displaces* in authoring.md. Where nothing can go, ask the user whether the rules may grow, '
       'one line per changed rule above the question: its file, then what it now says; '
       'only their answer in the turn adds a `Grows: <why nothing could go>` line to the message.')


def die(msg):
    print(f'rule-growth: {msg}', file=sys.stderr)
    sys.exit(2)


# A caller's --literal-pathspecs, --icase-pathspecs and the like would change what the pathspecs match.
ENV = {k: v for k, v in os.environ.items() if not (k.startswith('GIT_') and k.endswith('_PATHSPECS'))}


def git(*args, ok=(0,), data=None):
    out = subprocess.run(['git', *args], capture_output=True, input=data, env=ENV)
    if out.returncode not in ok:
        die(f"git {' '.join(args)}: {out.stderr.decode(errors='replace').strip()}")
    return out


def commit(rev):
    out = git('rev-parse', '-q', '--verify', f'{rev}^{{commit}}', ok=(0, 1))
    return out.stdout.decode().strip() if out.returncode == 0 else None


def words(tree, path):
    """Words in <path> at <tree>, a commit, or '' for the index; 0 where it holds none."""
    out = git('cat-file', 'blob', f'{tree or ":0"}:{path}', ok=(0, 128))   # `:0:`, as `:1:x.md` names a stage
    return len(out.stdout.decode('utf-8', errors='replace').split()) if out.returncode == 0 else 0


def growth(new, parent, specs):
    """Net words <new>, a commit or '' for the index, adds over <parent>, a commit or None for the
    empty tree, across the rule files, with the per-file deltas behind it."""
    args = ['diff', '--cached', parent or EMPTY] if new == '' else ['diff-tree', '-r', parent or EMPTY, new]
    out = git(*args, '--name-only', '-z', '--no-renames', '--', *specs)
    deltas = []
    for p in sorted({p for p in out.stdout.decode(errors='surrogateescape').split('\0') if p}):
        d = words(new, p) - (words(parent, p) if parent else 0)
        if d:
            deltas.append((p, d))
    return sum(d for _, d in deltas), deltas


def message_text(raw):
    """A message file up to its first line ending in the scissors mark, whatever comment string leads it.
    A message quoting that line before its Grows: line is refused here, though git would store it whole."""
    lines = []
    for line in raw.split('\n'):    # git breaks lines on newlines alone
        if line.rstrip().endswith(SCISSORS):
            break
        lines.append(line)
    return '\n'.join(lines)


def answered(message):
    """True where a message, as git stores it, carries a Grows: line giving a reason, not the template."""
    for line in message.split('\n'):
        m = LINE.match(line)
        if not m:
            continue
        reason = m.group(1).strip().rstrip('.')
        if (not TEMPLATE.startswith(re.sub(r'[^a-z]', '', reason.lower())) and re.search(r'[^\W\d_]{3,}', reason)
                and not set(re.findall(r'\w+', reason.lower())) <= BARE):
            return True
    return False


def parents_of(sha):
    return git('rev-list', '--parents', '-n', '1', sha).stdout.decode().split()[1:]


def show(deltas):
    shown = (p.encode(errors='surrogateescape').decode(errors='backslashreplace').encode('unicode_escape').decode()
             for p, _ in deltas)
    return ', '.join(f'{p} {d:+d}' for p, (_, d) in zip(shown, deltas))


def commit_msg(msgfile, specs):
    if commit('MERGE_HEAD'):
        return 0
    net, deltas = growth('', commit('HEAD'), specs)
    if net <= 0:
        return 0
    try:
        raw = open(msgfile, encoding='utf-8', errors='replace', newline='').read()   # a lone \r stays, as git keeps it
    except OSError as e:
        die(f'cannot read {msgfile}: {e}')
    if answered(message_text(raw)):
        return 0
    print(f'rule-growth: this commit adds {net} words to the rule files ({show(deltas)}).\n{ASK}', file=sys.stderr)
    return 1


def pre_push(specs, lines):
    refused, seen = [], set()
    graft = git('rev-parse', '--git-path', 'shallow').stdout.decode().strip()
    boundary = set(open(graft).read().split()) if os.path.exists(graft) else set()
    for line in lines:
        parts = line.rsplit(b' ', 3)    # the source may be typed with spaces; the last three fields never hold one
        if len(parts) != 4:
            continue
        local, remote = parts[1].decode(errors='replace'), parts[3].decode(errors='replace')
        if not local.strip('0'):
            continue    # a delete pushes no commit
        have = [remote] if remote.strip('0') and commit(remote) else []
        span = git('rev-list', '--reverse', '--no-merges', local, '--not', *have, '--remotes')
        for sha in span.stdout.decode().split():
            if sha in boundary or sha in seen:
                continue    # a shallow clone's edge, or a commit an earlier ref of this push measured
            seen.add(sha)
            parents = parents_of(sha)
            net, deltas = growth(sha, parents[0] if parents else None, specs)
            if net > 0 and not answered(git('log', '-1', '--format=%B', sha).stdout.decode(errors='replace')):
                subject = git('log', '-1', '--format=%s', sha).stdout.decode(errors='replace').strip()
                refused.append(f'  {sha[:10]} {subject}: +{net} words ({show(deltas)})')
    if not refused:
        return 0
    print('rule-growth: these commits add words to the rule files:', file=sys.stderr)
    print('\n'.join(refused), file=sys.stderr)
    print(f'Rework each one before the push. {ASK}', file=sys.stderr)
    return 1


def main():
    global EMPTY
    args = sys.argv[1:]
    if not (args[:1] == ['commit-msg'] and len(args) >= 2 or args[:1] == ['pre-push']):
        die('usage: rule-growth.py commit-msg <message file> [<pathspec>...] | pre-push [<pathspec>...]')
    EMPTY = git('hash-object', '-t', 'tree', '--stdin', data=b'').stdout.decode().strip()
    if args[0] == 'commit-msg':
        sys.exit(commit_msg(args[1], args[2:] or DEFAULT))
    sys.exit(pre_push(args[1:] or DEFAULT, sys.stdin.buffer.read().split(b'\n')))


if __name__ == '__main__':
    main()
