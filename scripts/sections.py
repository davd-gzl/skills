#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
"""The one cut of a `path#Heading` out of a rule file, for the review plan and its runner.

    sections.py check <pipeline config json>
        every path#Heading the config names: a name matching two headings, or none, is a row and the exit is 1

A `#` line inside a fenced block is content, never a heading. A name matches a heading whose text
starts with it, so `Re-review rounds` names `### Re-review rounds (head advanced)`; two headings
sharing the prefix is the ambiguity `check` exists for.
"""
import json
import re
import sys
from pathlib import Path


def headings(text):
    """(line index, depth, title) for every heading outside a fence."""
    out, fenced = [], False
    for i, line in enumerate(text.splitlines()):
        if re.match(r'^\s*(```|~~~)', line):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def matches(text, name):
    key = name.strip().lower()
    return [h for h in headings(text) if h[2].lower().startswith(key)]


def section(text, name):
    """One heading and everything under it, to the next heading of equal or shallower depth; None when no
    heading starts with the name. The first match is taken; `check` names the ambiguous ones."""
    hs = headings(text)
    hit = matches(text, name)
    if not hit:
        return None
    start, depth, _ = hit[0]
    lines = text.splitlines()
    end = len(lines)
    for i, d, _ in hs:
        if i > start and d <= depth:
            end = i
            break
    return '\n'.join(lines[start:end]).rstrip() + '\n'


def names_in_config(cfg):
    for stage, val in cfg.items():
        if isinstance(val, dict):
            for s in val.get('skills', []) or []:
                if '#' in s:
                    yield stage, s
            yield from names_in_config({k: v for k, v in val.items() if isinstance(v, dict)})


def check(config, root):
    rows = 0
    seen = set()
    for stage, ref in names_in_config(json.load(open(config))):
        path, name = ref.split('#', 1)
        if (path, name) in seen:
            continue
        seen.add((path, name))
        try:
            text = (root / path).read_text()
        except OSError:
            print(f'{stage}: {ref}: file missing'); rows += 1; continue
        hit = matches(text, name)
        if len(hit) != 1:
            print(f'{stage}: {ref}: {len(hit)} headings match' + (': ' + ', '.join(h[2] for h in hit) if hit else '')); rows += 1
    print(f'{rows} section name(s) to fix' if rows else 'every section name selects one heading')
    return 1 if rows else 0


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'check':
        sys.exit(check(sys.argv[2], Path.cwd()))
    print(__doc__, file=sys.stderr); sys.exit(2)
