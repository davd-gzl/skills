#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
# Checks rule files against the contract in authoring.md.
#
#   ./skills/lint.py AGENTS.md skills/*.md
#   ./skills/lint.py --quiet <files>     errors only, no health table
#
# Errors block a commit. Warnings are the health table: they measure drift the
# corpus recovers from over several turns, and a warning answered by raising its
# threshold is the pollution this file exists to catch.

import re
import sys
from collections import defaultdict

# Words. Raising a cap is a decision to hold more rules in every context window,
# never the fix for a file that outgrew it: fold two rules or evict one instead.
CAPS = {
    'AGENTS.md': 3200,                  # workspace root, loaded on every turn
    'skills/review.md': 5000,           # the longest workflow, and the one to keep cutting
    'skills/review-comment.md': 3000,
    'skills/writing-style.md': 3200,
}
CAP_BY_CLASS = {'skill': 1600, 'project': 2600, 'default': 2000}

# A rule that tells the reader to stop measuring. The defect is the clause, not
# the fact: a fact goes stale silently and the clause is what stops the check.
FROZEN = re.compile(
    r'\b(stop re-deriving|stops? re-?deriving|never re-?derive|no need to (check|verify|re-?run)'
    r'|do not (re-?check|re-?measure|re-?verify)|already measured, so|settled, so stop)\b', re.I)

# An environment capability asserted as settled. Wants the command beside it.
ENV_NOUN = re.compile(
    r'\b(docker|dockerd|podman|sudo|unshare|namespace|CapEff|CapBnd|/dev/(fuse|kvm)'
    r'|docker\.sock|rootless|chroot|bwrap|this (container|box|machine|shell)|the box)\b', re.I)
ENV_ABSOLUTE = re.compile(
    r'\b(cannot|can never|is dead|never (start|run|work)|no \w+ binary|absent|not permitted'
    r'|will never|impossible|refused)\b', re.I)
ENV_ESCAPE = re.compile(r'env-check|measure it|run it|check it|`[^`]*`')

DATED = re.compile(r'\b(stated|measured|verified|as of|since)\s+(on\s+)?'
                   r'(\d{4}-\d{2}-\d{2}|\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4})\b', re.I)
ISO_DATE = re.compile(r'\b20\d{2}-[01]\d-[0-3]\d\b')
CLOCK = re.compile(r'\b[0-2]?\d:[0-5]\d\s?(am|pm|UTC|utc)?\b')

# A clause was stripped and the sentence was not repaired. The signal is the
# pair: a provenance word ending one line and punctuation opening the next. The
# tail alone fires on every 80-column wrap.
DANGLE_TAIL = re.compile(r'\b(measured|stated|verified|reported)\s*$', re.I)
DANGLE_HEAD = re.compile(r'^\s*[.,;:]($|\s)')

SHA = re.compile(r'(?<![\w/#])[0-9a-f]{7,40}(?![\w])')
EMDASH = '—'
NEGATION = re.compile(r'\b(never|neither|nor|no|not|cannot|none|nothing|nobody)\b', re.I)

FENCE = re.compile(r'^\s*```')
INLINE_CODE = re.compile(r'`[^`]*`')
LINK_TARGET = re.compile(r'\]\([^)]*\)')
HTML_TAG = re.compile(r'<[^>]{1,60}>')
PLACEHOLDER = re.compile(r'<[a-z][a-z0-9 _/-]*>', re.I)


def classify(path):
    if path.endswith('AGENTS.md') and '/' in path.rstrip('AGENTS.md').strip('/'):
        return 'project'
    if '/skills/' in path or path.startswith('skills/'):
        return 'skill'
    return 'default'


def cap_for(path):
    for key, cap in CAPS.items():
        # A bare filename matches only at the root. Without this every
        # projects/<repo>/AGENTS.md inherits the root file's larger cap.
        if path == key or ('/' in key and path.endswith('/' + key)):
            return cap
    return CAP_BY_CLASS[classify(path)]


def prose_lines(text):
    """Every line outside a fenced block, with code spans and link targets blanked.

    A rule and its example live in one file, so a check that reads the example
    reports the file's own illustrations as violations and gets switched off.
    """
    out, in_fence = [], False
    for n, raw in enumerate(text.splitlines(), 1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = INLINE_CODE.sub('``', raw)
        line = LINK_TARGET.sub(']', line)
        line = HTML_TAG.sub('', line)
        out.append((n, raw, line))
    return out


def sentences(line):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', line) if len(s.split()) >= 8]


def normalize(sentence):
    s = PLACEHOLDER.sub('', sentence.lower())
    return re.sub(r'[^a-z0-9 ]', '', s).strip()


def check_file(path):
    try:
        text = open(path, encoding='utf-8').read()
    except OSError as exc:
        return [('error', 0, 'unreadable', str(exc))], {}, {}

    findings, lines = [], prose_lines(text)
    # Every word costs context, a fenced command as much as a sentence, so the
    # budget counts the file. Only the prose checks below skip the fences.
    words = len(text.split())
    bullets = [(n, clean) for n, _, clean in lines if clean.lstrip().startswith('- ')]
    bold = sum(1 for _, c in bullets if c.lstrip().startswith('- **'))
    negations = sum(len(NEGATION.findall(clean)) for _, _, clean in lines)

    # A project delta is a measurement log, not a rule set: a date says when to
    # re-check the fact and a sha says which tree it was read from. In the core
    # both are the staleness this file exists to catch, so they downgrade to
    # warnings here and nowhere else.
    log = classify(path) == 'project'

    for i, (n, raw, clean) in enumerate(lines):
        heading = clean.lstrip().startswith('#')
        nxt = lines[i + 1][2] if i + 1 < len(lines) else ''
        # A dash separating a term from its definition, in a heading or at the
        # head of a list item, is structure. Mid-sentence it is prose.
        sep = clean.find(EMDASH)
        structural = heading or (clean.lstrip().startswith(('- ', '* ')) and 0 <= sep < 60)
        if FROZEN.search(clean):
            findings.append(('error', n, 'frozen',
                             'tells the reader to stop measuring; state the command instead'))
        # A heading may date a block of measurements, which is how a reader
        # tells a fact that could have gone stale from one that cannot. A rule
        # carries no date: it applies whenever its trigger fires.
        if not heading and (DATED.search(clean) or ISO_DATE.search(clean) or CLOCK.search(clean)):
            findings.append(('warn' if log else 'error', n, 'dated',
                             'a rule carries no date; the incident belongs in the artifact'))
        if EMDASH in clean and not structural:
            findings.append(('error', n, 'emdash', 'em-dash in prose'))
        if DANGLE_TAIL.search(clean.rstrip()) and DANGLE_HEAD.match(nxt):
            findings.append(('error', n, 'dangling',
                             'sentence ends on a provenance word and the next line opens on '
                             'punctuation; a clause was cut and not repaired'))
        if clean.lstrip().startswith('- ') and SHA.search(clean):
            findings.append(('warn' if log else 'error', n, 'sha',
                             'a rule pins no commit; cite the behaviour, not the incident'))
        if ENV_NOUN.search(clean) and ENV_ABSOLUTE.search(clean) and not ENV_ESCAPE.search(raw):
            findings.append(('warn', n, 'env-claim',
                             'environment capability asserted without the command that reads it'))
        stripped = re.sub(r'\(\d\)|\(s\)', '', clean)
        if '(' in stripped and not heading and not clean.lstrip().startswith('|'):
            findings.append(('warn', n, 'paren', 'parenthetical; rework into the sentence'))

    cap = cap_for(path)
    if words > cap:
        level = 'error' if words > cap * 1.15 else 'warn'
        findings.append((level, 0, 'budget', f'{words} words over the {cap} cap'))

    health = {
        'words': words, 'cap': cap,
        'negation': round(negations * 100 / max(words, 1), 1),
        # Under eight bullets the share says nothing, so it is not reported.
        'bold': round(bold * 100 / len(bullets)) if len(bullets) >= 8 else '-',
        'bullets': len(bullets),
    }
    seen = defaultdict(list)
    for n, _, clean in lines:
        for sentence in sentences(clean):
            key = normalize(sentence)
            if len(key.split()) >= 8:
                seen[key].append(n)
    return findings, health, seen


def main(argv):
    quiet = '--quiet' in argv
    paths = [a for a in argv if not a.startswith('--')]
    if not paths:
        print(__doc__ or 'usage: lint.py <files>')
        return 2

    errors = 0
    health_rows, corpus = [], defaultdict(list)
    for path in paths:
        findings, health, seen = check_file(path)
        for key, nums in seen.items():
            corpus[key].append((path, nums[0]))
        for level, line, code, message in sorted(findings, key=lambda f: (f[1], f[2])):
            mark = 'ERROR' if level == 'error' else 'warn '
            errors += level == 'error'
            print(f'{mark} {path}:{line} [{code}] {message}')
        if health:
            health_rows.append((path, health))

    dupes = {k: v for k, v in corpus.items() if len({p for p, _ in v}) > 1}
    for key, places in sorted(dupes.items(), key=lambda kv: -len(kv[1]))[:10]:
        where = ', '.join(f'{p}:{n}' for p, n in places)
        print(f'warn  [dupe] one rule in {len(places)} files: {where}\n      "{key[:90]}"')

    if not quiet and health_rows:
        print(f'\n{"file":<34}{"words":>7}{"cap":>7}{"neg/100w":>10}{"bold%":>7}')
        for path, h in health_rows:
            flag = '  <-- over' if h['words'] > h['cap'] else ''
            print(f'{path:<34}{h["words"]:>7}{h["cap"]:>7}{h["negation"]:>10}{str(h["bold"]):>7}{flag}')
        total = sum(h['words'] for _, h in health_rows)
        print(f'{"total":<34}{total:>7}')
        print('\nneg/100w over 4.0 and bold% over 40 both mean the file has stopped '
              'ranking its own rules.')

    print(f'\n{errors} error(s)' if errors else '\nno errors')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
