#!/usr/bin/env python3
"""The register check.

NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.

A reply to the user takes the Short form of skills/short-form.md, and a long
session drifts back to prose without noticing. This measures a reply a person hands it.
No hook calls it: a count put in front of the next draft is written toward.

  ./skills/scripts/reply-check.py                   hook JSON on stdin: the turn's final reply, its numbers on
                                                    stderr and exit 2 when it has drifted. Wired to nothing.
  ./skills/scripts/reply-check.py <file>            the numbers for a text file; exit 1 when it drifts
  ./skills/scripts/reply-check.py --last <jsonl>    the last reply's numbers when it drifted, one line, for a
                                                    person reading back over a session; else nothing
  ./skills/scripts/reply-check.py --scan <jsonl>... one row per transcript: final replies measured, drifted,
                                                    and the median articles per hundred words;
                                                    --since <date> keeps replies from that day on

Measured over the prose alone. Fenced blocks, inline code, blockquotes, table
rows, link targets and lines between two `---` rules are dropped, since a draft
quoted in a reply stays as written. Under MIN_WORDS nothing is measured, and a
prompt opening or closing on `+` exempts its reply, as does one asking for an
explanation, EXPLAIN naming the triggers; --last says which one lifted it. Every
line carries the thinking tokens the turn spent, from the transcript's usage
block, so a rule on the thinking has a number. A reply carrying a closing
block, the artifact lines, carries the `Did:` account above it, as plain lines:
an account inside a code fence is named, as is one with no `---` rule above it.
The account, quotes, tables and code
do not count toward WORDS. A coined letter, per skills/shortcuts.md, is defined
on the TL;DR line that names it and never takes a letter the table gives.
"""

import json
import pathlib
import re
import statistics
import sys

MIN_WORDS = 30

ART = re.compile(r"\b(a|an|the)\b", re.I)
HEDGE = re.compile(r"\b(might|maybe|perhaps|probably|likely|i think|i believe|it seems|could be|possibly)\b", re.I)
PLEAS = re.compile(r"\b(sure|certainly|of course|happy to|glad to|great question|absolutely|no problem)\b", re.I)
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
CLOSING = re.compile(r'^\s*[📋▶]')
DID = re.compile(r'^\s*\**Did:')

REGISTER = ('Rewrite in Short form, per skills/short-form.md: no filler, no pleasantries, '
            'no hedging, lead with the answer, one idea per paragraph, stop when it lands. Drop an '
            'article only where the sentence still reads in one pass; stacked article-free fragments '
            'are the failure this register prevents, never its target. Sample: "Gitlink moved, push '
            'refused. Rebase onto `origin/main`, retry." A quoted draft stays as written; a `+` reply '
            'is exempt.')


def prose(text):
    """The lines a reader takes as the reply's own voice."""
    out, fence, rule, account = [], False, False, False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('```'):
            fence = not fence
            continue
        if s == '---':
            rule = not rule
            continue
        if DID.match(line):
            account = True
        if account and not s:
            account = False
        if fence or rule or account or s.startswith('>') or s.startswith('|'):
            continue
        line = re.sub(r'`[^`]*`', ' ', line)
        line = re.sub(r'\]\([^)]*\)', ']', line)
        line = re.sub(r'https?://\S+', ' ', line)
        out.append(line)
    return '\n'.join(out)


# A repository path named in the reply: a known prefix, or a slashed path ending in an extension.
PATHS = re.compile(r'(?<![\w/])(?:(?:projects|skills|scripts|tests)/[\w./-]*\w|[\w-]+/[\w./-]*\.\w+)')


def unlinked(text):
    """Paths the reply names with no markdown link carrying them: the links rule, measured."""
    bare = re.sub(r'```.*?```', ' ', text, flags=re.S)
    bare = re.sub(r'\]\([^)]*\)|https?://\S+', ' ', bare)
    named = sorted(set(PATHS.findall(bare)))
    return [q for q in named if not re.search(r'\]\([^)]*' + re.escape(q.rsplit('/', 1)[-1]) + r'[^)]*\)', text)]


SHORTCUTS = pathlib.Path(__file__).resolve().parent.parent / 'shortcuts.md'
# A letter defined in place, per skills/shortcuts.md: `r`: run the round, or `r` (run the round).
DEFINED = re.compile(r'`([a-z])`\s*(?::|\(|=|—)\s*([A-Za-z]*)')


def table_letters():
    """Each letter the shortcuts table gives, with the words it stands for: the other words of its row's
    first cell, `p`, `push`, or where the cell holds letters alone, the second cell up to its first colon."""
    try:
        rows = SHORTCUTS.read_text(encoding='utf-8').splitlines()
    except OSError:
        return {}
    out = {}
    for row in rows:
        cells = row.split('|')
        if not row.startswith('| `') or len(cells) < 3:
            continue
        named = re.sub(r'`[a-z]`', ' ', cells[1])
        words = set(re.findall(r'[a-z]+', (named if re.search(r'[a-z]', named) else cells[2].split(':')[0]).lower()))
        for c in re.findall(r'`([a-z])`', cells[1]):
            out[c] = words
    return out


def table_words():
    """Every word the shortcuts table quotes, a `<placeholder>` matching any run of text."""
    try:
        rows = [r for r in SHORTCUTS.read_text(encoding='utf-8').splitlines() if r.startswith('| `')]
    except OSError:
        return []
    return [re.compile(re.sub(r'<[^>]*>', '.+', re.escape(w)) + r'\Z')
            for r in rows for w in re.findall(r'`([^`]+)`', r)]


# A word offered to type: `say ...` or `type ...` before it, or `word`: at the head of a line.
OFFERED = re.compile(r'\b(?:say|type)\s+\**`([^`]+)`|^\s*\**`([^`]+)`\**\s*:', re.I | re.M)


def phrases(text):
    """A phrase offered to type where the shortcuts table gives a letter, per its opening rule."""
    allowed = table_words()
    known = {t for p in allowed for t in re.findall(r'[a-z]+', p.pattern)}
    out = []
    for said, head in OFFERED.findall(text):
        w = (said or head).strip()
        if ' ' not in w or all(len(t) == 1 for t in w.split()) or any(p.match(w) for p in allowed):
            continue
        if said or w.split()[0].lower() in known:
            out.append(f'offers `{w}` to type, a phrase the shortcuts table does not give')
    return out


def letters(text):
    """A coined letter the TL;DR line names with no definition beside it, and a letter coined over the table's."""
    table, reasons = table_letters(), phrases(text)
    for line in text.splitlines():
        for c, word in DEFINED.findall(line):
            if c in table and word.lower() not in table[c]:
                reasons.append(f'coins `{c}`, a letter the shortcuts table already gives')
        if line.lstrip('*').startswith('TL;DR'):
            defined = {c for c, _ in DEFINED.findall(line)}
            for c in sorted(set(re.findall(r'`([a-z])`', line)) - set(table) - defined):
                reasons.append(f'the TL;DR names the coined letter `{c}` with no definition beside it')
    return list(dict.fromkeys(reasons))


def measure(text):
    """The numbers, and the reasons it drifts, empty when it does not."""
    p = prose(text)
    words = WORD.findall(p)
    n = len(words)
    sentences = [s for s in re.split(r'(?<=[.!?:])\s+|\n+', p) if WORD.search(s)]
    m = {
        'words': n,
        'articles': round(100 * len(ART.findall(p)) / max(n, 1), 1),
        'per_sentence': round(n / max(len(sentences), 1), 1),
        'hedges': [h.group(0) for h in HEDGE.finditer(p)],
        'pleasantries': [h.group(0) for h in PLEAS.finditer(p)],
    }
    reasons = []
    lines = text.splitlines()
    if any(CLOSING.match(l) for l in lines) and not any(DID.match(l) for l in lines):
        reasons.append('a closing block with no Did: account above it')
    if re.search(r'```[^\n]*\n\s*\**Did:', text):
        reasons.append('the Did: account sits in a code fence, write it as plain lines')
    did_i = next((i for i, l in enumerate(lines) if DID.match(l)), None)
    if did_i is not None:
        j = did_i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j < 0 or lines[j].strip() != '---':
            reasons.append('the Did: account with no --- rule above it')
    # The counts stay in the metrics a reader may look at and are never a reason:
    # a cap on words, articles or sentence length is a number to write toward, and
    # the register is a reply that reads once, which no count settles.
    if n >= MIN_WORDS:
        if m['hedges']:
            reasons.append('hedge: ' + ', '.join(f'"{h}"' for h in m['hedges'][:3]))
        if m['pleasantries']:
            reasons.append('pleasantry: ' + ', '.join(f'"{h}"' for h in m['pleasantries'][:3]))
    reasons += letters(text)
    m['unlinked'] = unlinked(text)
    if m['unlinked']:
        reasons.append('named with no link: ' + ', '.join(m['unlinked'][:3]))
    m['reasons'] = reasons
    return m


def entries(path, tail=None):
    """Every entry of a transcript, or with `tail` the ones in its last `tail` bytes."""
    with open(path, 'rb') as f:
        if tail:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(size - tail, 0))
            data = f.read()
            if size > tail:
                data = data.split(b'\n', 1)[-1]    # drop the line the cut landed in
        else:
            data = f.read()
        for line in data.decode('utf-8', 'replace').splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and not e.get('isSidechain'):
                yield e


def blocks(e):
    c = (e.get('message') or {}).get('content')
    if isinstance(c, str):
        return [{'type': 'text', 'text': c}]
    return c if isinstance(c, list) else []


def is_prompt(e):
    """A user entry the person typed, never a tool result."""
    return e.get('type') == 'user' and any(b.get('type') == 'text' for b in blocks(e))


def prompt_text(e):
    return '\n'.join(b.get('text') or '' for b in blocks(e) if b.get('type') == 'text').strip()


# The prompts that ask for an explanation; a bare `why` stays out, since a question wanting a fact is not one.
EXPLAIN = re.compile(r"\b(explain|elaborate|walk me through|in detail|tell me more|what do you mean|wdym)\b", re.I)


def exempt(prompt):
    """The trigger that lifts the reply to explanation, else ''. `+` is the mark; a prompt asking for an
    explanation is its equal, per Short form."""
    if prompt.startswith('+') or prompt.endswith('+'):
        return '+'
    m = EXPLAIN.search(prompt)
    return m.group(0) if m else ''


def thinking_tokens(e):
    """The thinking tokens one assistant message spent, from its usage block; 0 where the record has none."""
    u = (e.get('message') or {}).get('usage') or {}
    return int(((u.get('output_tokens_details') or {}).get('thinking_tokens')) or 0)


def replies(path):
    """Every final reply in a transcript: the assistant text that a prompt or the end of the file follows,
    with the prompt it answered, the time it was written and the thinking tokens its turn spent."""
    out, text, prompt, when, think = [], [], '', '', 0
    for e in entries(path):
        t = e.get('type')
        if t == 'assistant':
            think += thinking_tokens(e)
            texts = [b.get('text') or '' for b in blocks(e) if b.get('type') == 'text']
            if any(b.get('type') == 'tool_use' for b in blocks(e)):
                text = []          # narration before a tool call is not the turn's reply
            elif texts:
                text += texts
                when = e.get('timestamp', '')
        elif t == 'user':
            if text:
                out.append(('\n\n'.join(text), prompt, when, think))
                text = []
            if is_prompt(e):
                prompt = prompt_text(e)
                think = 0
    if text:
        out.append(('\n\n'.join(text), prompt, when, think))
    return out


def final_reply(path, after_prompt=False):
    """The last reply and the prompt it answers, read from the tail of the transcript: the assistant
    text below the last user entry, tool result or prompt, then the prompt above it. At prompt time
    the prompt just typed may already sit at the tail; after_prompt steps over it."""
    text, prompt, collecting, think = [], '', True, 0
    for e in reversed(list(entries(path, tail=1 << 19))):
        t = e.get('type')
        if t == 'assistant':
            think += thinking_tokens(e)
            if collecting:
                if not text and any(b.get('type') == 'tool_use' for b in blocks(e)):
                    return '', '', 0      # the turn ended on a tool call, nothing to measure
                text[:0] = [b.get('text') or '' for b in blocks(e) if b.get('type') == 'text']
        elif t == 'user':
            if after_prompt and not text and is_prompt(e):
                after_prompt = False
                continue
            collecting = False
            if is_prompt(e):
                prompt = prompt_text(e)
                break
    return '\n\n'.join(text), prompt, think


def report(m, think=None):
    return (f"reply-check: {m['words']} words, {m['articles']} articles per 100, "
            f"{m['per_sentence']} words per sentence" + (f', {think} thinking tokens this turn' if think is not None else ''))


def cmd_hook(stdin, stderr):
    try:
        payload = json.load(stdin)
    except ValueError:
        return 0
    if payload.get('stop_hook_active'):
        return 0
    path = payload.get('transcript_path')
    if not path:
        return 0
    try:
        text, prompt, think = final_reply(path)
    except OSError:
        return 0
    if not text or exempt(prompt):
        return 0
    m = measure(text)
    if not m['reasons']:
        return 0
    print(report(m, think) + '; ' + '; '.join(m['reasons']) + '.\n' + REGISTER, file=stderr)
    return 2


def cmd_last(path, stdout):
    """One line on the last reply when it drifted, for the next turn's context; nothing when it held."""
    try:
        text, prompt, think = final_reply(path, after_prompt=True)
    except OSError:
        return 0
    if not text:
        return 0
    lift = exempt(prompt)
    if lift:
        if lift != '+':
            print(f'reply-check: the last reply was exempt, the prompt asked to explain, matched "{lift}"; {think} thinking tokens that turn.', file=stdout)
        return 0
    m = measure(text)
    if m['reasons']:
        print(report(m, think) + '; ' + '; '.join(m['reasons']) + '.', file=stdout)
    return 0


def cmd_file(path, stdout):
    m = measure(open(path, encoding='utf-8').read())
    print(report(m) + ('; ' + '; '.join(m['reasons']) if m['reasons'] else ', in register'), file=stdout)
    return 1 if m['reasons'] else 0


def title(path):
    for e in entries(path):
        if e.get('type') == 'custom-title' and e.get('customTitle'):
            return e['customTitle']
    for e in entries(path):
        if is_prompt(e):
            return prompt_text(e).splitlines()[0][:60]
    return path


def cmd_scan(paths, since, stdout):
    rows = []
    for path in paths:
        rs = [(t, p, k) for t, p, when, k in replies(path) if when >= since and not exempt(p)]
        ms = [(measure(t), k) for t, _, k in rs]
        ms = [(m, k) for m, k in ms if m['words'] >= MIN_WORDS]
        if not ms:
            continue
        drifted = sum(1 for m, _ in ms if m['reasons'])
        rows.append((drifted, len(ms), statistics.median(m['articles'] for m, _ in ms),
                     statistics.median(k for _, k in ms), title(path), path))
    rows.sort(key=lambda r: (-r[0], -r[1]))
    print('| drifted | measured | median articles/100 | median thinking tokens/turn | session |', file=stdout)
    print('| --- | --- | --- | --- | --- |', file=stdout)
    for d, n, med, think, t, _ in rows:
        print(f'| {d} | {n} | {med:.1f} | {think:.0f} | {t} |', file=stdout)
    return 0


def main(argv, stdin=None, stdout=None, stderr=None):
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        if not argv:
            return cmd_hook(stdin, stderr)
        if argv[0] == '--scan':
            since = ''
            paths = argv[1:]
            if '--since' in paths:
                i = paths.index('--since')
                since, paths = paths[i + 1], paths[:i] + paths[i + 2:]
            return cmd_scan(paths, since, stdout)
        if argv[0] == '--last' and len(argv) == 2:
            return cmd_last(argv[1], stdout)
        if len(argv) == 1:
            return cmd_file(argv[0], stdout)
    except Exception as e:  # a hook that cannot decide says so and never blocks
        print(f'reply-check: {e}', file=stderr)
        return 0
    print(__doc__, file=stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
