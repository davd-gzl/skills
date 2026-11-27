#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
"""The words the user types, read from the table of skills/words.md.

A row loads for each word opening a line of the message, the run stopping at the first token that
is no word, so `/rai <url>` opens on `rai`; a line ending in a question mark opens
on nothing. A row loaded wrongly costs a few lines of context and grants nothing: when a word gives
a push or a post is skills/shortcuts.md, and the gate reads it.

    ./skills/scripts/words.py hook    UserPromptSubmit adapter: the table row of each word a line
                                      of the typed message opens with, as context
"""
import json
import re
import sys
from pathlib import Path

TABLE = Path(__file__).resolve().parent.parent / 'words.md'
ANY = '*'  # a `<placeholder>` inside a word matches any one token
# The last row of the table: what these give is nothing, so they end a run rather than extend it.
VAGUE = {('go',), ('ok',), ('yes',), ('sure',)}


def vocabulary():
    """Each word as a tuple of lowercase tokens, with its table row."""
    try:
        rows = [r for r in TABLE.read_text(encoding='utf-8').splitlines() if r.startswith('| `')]
    except OSError:
        rows = []
    words = {}
    for row in rows:
        for quoted in re.findall(r'`([^`]+)`', row.split('|')[1]):
            spaced = re.sub(r'<[^>]*>|\[[^\]]*\]', f' {ANY} ', quoted.lower().lstrip('/'))
            tokens = tuple(spaced.split())
            while tokens and tokens[-1] == ANY:  # a trailing argument is the target, not part of the word
                tokens = tokens[:-1]
            if tokens and tokens not in VAGUE:
                words.setdefault(tokens, row)
    return words


def lead(message, words):
    """The words a message opens with, in order, each the longest that matches at its place."""
    if message.rstrip().endswith('?'):
        return []
    tokens = [t.strip(',') for t in message.lower().lstrip('/').split()]
    tokens = [t for t in tokens if t]
    longest = sorted(words, key=len, reverse=True)
    found, i = [], 0
    while i < len(tokens):
        w = next((w for w in longest if len(w) <= len(tokens) - i
                  and all(a in (ANY, b) for a, b in zip(w, tokens[i:]))), None)
        if not w:
            break
        found.append(w)
        i += len(w)
    return found


def hook(stdin, stdout):
    prompt = (json.load(stdin) or {}).get('prompt') or ''
    words = vocabulary()
    rows = []
    for w in (w for line in prompt.splitlines() for w in lead(line, words)):
        if words[w] not in rows:
            rows.append(words[w])
    if rows:
        text = ('The words this message\'s lines open with, per `skills/words.md`:\n\n'
                '| Word | What it starts | Rule |\n| --- | --- | --- |\n' + '\n'.join(rows))
        json.dump({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': text}}, stdout)
    return 0


if __name__ == '__main__':
    if sys.argv[1:] != ['hook']:
        sys.exit(__doc__)
    sys.exit(hook(sys.stdin, sys.stdout))
