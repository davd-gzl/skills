#!/usr/bin/env python3
"""The register check.

NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.

A reply to the user takes the Short form of skills/short-form.md, and a long
session drifts back to prose without noticing. This measures the reply instead of
trusting it, and hands the numbers back for a rewrite.

  ./skills/scripts/reply-check.py                   Claude Code Stop adapter, hook JSON on stdin: the turn's
                                                    final reply, its numbers on stderr and exit 2 when it has
                                                    drifted, once per turn
  ./skills/scripts/reply-check.py <file>            the numbers for a text file; exit 1 when it drifts
  ./skills/scripts/reply-check.py --last <jsonl>    the last reply's numbers when it drifted, one line, for the
                                                    prompt hook to put in the next turn's context; else nothing
  ./skills/scripts/reply-check.py --scan <jsonl>... one row per transcript: final replies measured, drifted,
                                                    and the median articles per hundred words;
                                                    --since <date> keeps replies from that day on

Measured over the prose alone. Fenced blocks, inline code, blockquotes, table
rows, link targets and lines between two `---` rules are dropped, since a draft
quoted in a reply stays as written. Under MIN_WORDS nothing is measured, and a
prompt opening or closing on `+` exempts its reply. A reply carrying a closing
block, the artifact lines, carries the `Did:` account above it, as plain lines:
an account inside a code fence is named, as is one with no `---` rule above it.
The account, quotes, tables and code
do not count toward WORDS.
"""

import json
import re
import statistics
import sys

ARTICLES = 5.0      # per hundred words; the measured register runs under one
SENTENCE = 12.0     # words per sentence
MIN_WORDS = 30
WORDS = 200         # prose words in one reply; past this the reader skims

ART = re.compile(r"\b(a|an|the)\b", re.I)
HEDGE = re.compile(r"\b(might|maybe|perhaps|probably|likely|i think|i believe|it seems|could be|possibly)\b", re.I)
PLEAS = re.compile(r"\b(sure|certainly|of course|happy to|glad to|great question|absolutely|no problem)\b", re.I)
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
CLOSING = re.compile(r'^\s*[📋▶]')
DID = re.compile(r'^\s*\**Did:')

REGISTER = ('Rewrite in cvm, the Short form of skills/short-form.md: no filler, no pleasantries, '
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
    if n >= MIN_WORDS:
        if n > WORDS:
            reasons.append(f'{n} prose words, cap {WORDS}')
        if m['articles'] > ARTICLES:
            reasons.append(f"{m['articles']} articles per 100 words, cap {ARTICLES:g}")
        if m['per_sentence'] > SENTENCE:
            reasons.append(f"{m['per_sentence']} words per sentence, cap {SENTENCE:g}")
        if m['hedges']:
            reasons.append('hedge: ' + ', '.join(f'"{h}"' for h in m['hedges'][:3]))
        if m['pleasantries']:
            reasons.append('pleasantry: ' + ', '.join(f'"{h}"' for h in m['pleasantries'][:3]))
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


def exempt(prompt):
    return prompt.startswith('+') or prompt.endswith('+')


def replies(path):
    """Every final reply in a transcript: the assistant text that a prompt or the end of the file follows,
    with the prompt it answered and the time it was written."""
    out, text, prompt, when = [], [], '', ''
    for e in entries(path):
        t = e.get('type')
        if t == 'assistant':
            texts = [b.get('text') or '' for b in blocks(e) if b.get('type') == 'text']
            if any(b.get('type') == 'tool_use' for b in blocks(e)):
                text = []          # narration before a tool call is not the turn's reply
            elif texts:
                text += texts
                when = e.get('timestamp', '')
        elif t == 'user':
            if text:
                out.append(('\n\n'.join(text), prompt, when))
                text = []
            if is_prompt(e):
                prompt = prompt_text(e)
    if text:
        out.append(('\n\n'.join(text), prompt, when))
    return out


def final_reply(path, after_prompt=False):
    """The last reply and the prompt it answers, read from the tail of the transcript: the assistant
    text below the last user entry, tool result or prompt, then the prompt above it. At prompt time
    the prompt just typed may already sit at the tail; after_prompt steps over it."""
    text, prompt, collecting = [], '', True
    for e in reversed(list(entries(path, tail=1 << 19))):
        t = e.get('type')
        if t == 'assistant' and collecting:
            if not text and any(b.get('type') == 'tool_use' for b in blocks(e)):
                return '', ''      # the turn ended on a tool call, nothing to measure
            text[:0] = [b.get('text') or '' for b in blocks(e) if b.get('type') == 'text']
        elif t == 'user':
            if after_prompt and not text and is_prompt(e):
                after_prompt = False
                continue
            collecting = False
            if is_prompt(e):
                prompt = prompt_text(e)
                break
    return '\n\n'.join(text), prompt


def report(m):
    return (f"reply-check: {m['words']} words, {m['articles']} articles per 100, "
            f"{m['per_sentence']} words per sentence")


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
        text, prompt = final_reply(path)
    except OSError:
        return 0
    if not text or exempt(prompt):
        return 0
    m = measure(text)
    if not m['reasons']:
        return 0
    print(report(m) + '; ' + '; '.join(m['reasons']) + '.\n' + REGISTER, file=stderr)
    return 2


def cmd_last(path, stdout):
    """One line on the last reply when it drifted, for the next turn's context; nothing when it held."""
    try:
        text, prompt = final_reply(path, after_prompt=True)
    except OSError:
        return 0
    if not text or exempt(prompt):
        return 0
    m = measure(text)
    if m['reasons']:
        print(report(m) + '; ' + '; '.join(m['reasons']) + '.', file=stdout)
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
        rs = [(t, p) for t, p, when in replies(path) if when >= since and not exempt(p)]
        ms = [measure(t) for t, _ in rs]
        ms = [m for m in ms if m['words'] >= MIN_WORDS]
        if not ms:
            continue
        drifted = sum(1 for m in ms if m['reasons'])
        rows.append((drifted, len(ms), statistics.median(m['articles'] for m in ms), title(path), path))
    rows.sort(key=lambda r: (-r[0], -r[1]))
    print('| drifted | measured | median articles/100 | session |', file=stdout)
    print('| --- | --- | --- | --- |', file=stdout)
    for d, n, med, t, _ in rows:
        print(f'| {d} | {n} | {med:.1f} | {t} |', file=stdout)
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
