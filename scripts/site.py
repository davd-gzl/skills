#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
"""Build the GitHub Pages site under docs/ from README.md and knowledge/blog/*.md.

    ./scripts/site.py [--check]

Every page is a copy with Jekyll front matter, its relative links rewritten to the
repository's blob URLs so a link that works on GitHub works on the site. --check
exits 1 when docs/ differs from what the sources would build, for the gate.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOB = 'https://github.com/davd-gzl/skills/blob/main/'
LINK = re.compile(r'\]\((?!https?://|#|mailto:)([^)\s]+)\)')


def rewrite(text, base):
    """Relative links to the repository, resolved from the source file's directory."""
    def one(m):
        target = m.group(1)
        path = os.path.normpath(os.path.join(base, target)).replace(os.sep, '/')
        return '](' + BLOB + path + ')'
    return LINK.sub(one, text)


def page(src, title, permalink):
    body = open(os.path.join(ROOT, src)).read()
    body = rewrite(body, os.path.dirname(src))
    body = re.sub(r'^# .*\n', '', body, count=1)
    front = f'---\ntitle: "{title}"\npermalink: {permalink}\n---\n\n'
    return front + body


def title_of(src):
    for line in open(os.path.join(ROOT, src)):
        if line.startswith('# '):
            return line[2:].strip().replace('"', '')
    return os.path.basename(src)


def build():
    out = {}
    out['docs/index.md'] = page('README.md', title_of('README.md'), '/')
    posts = sorted(f for f in os.listdir(os.path.join(ROOT, 'knowledge/blog')) if f.endswith('.md'))
    index = ['---\ntitle: "Blog"\npermalink: /blog/\n---\n', 'One post per day the workflow was measured, newest first.\n']
    for f in reversed(posts):
        slug = f[:-3]
        out[f'docs/blog/{slug}.md'] = page(f'knowledge/blog/{f}', title_of(f'knowledge/blog/{f}'), f'/blog/{slug}/')
        index.append(f'- [{title_of(f"knowledge/blog/{f}")}](/blog/{slug}/), {slug[:10]}')
    out['docs/blog/index.md'] = '\n'.join(index) + '\n'
    return out


def main():
    want = build()
    check = '--check' in sys.argv
    stale = []
    for rel, text in want.items():
        path = os.path.join(ROOT, rel)
        have = open(path).read() if os.path.exists(path) else None
        if have != text:
            stale.append(rel)
            if not check:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, 'w').write(text)
    if check:
        print('docs/ is current' if not stale else 'stale: ' + ', '.join(stale))
        return 1 if stale else 0
    print(f'{len(want)} pages, {len(stale)} written')
    return 0


if __name__ == '__main__':
    sys.exit(main())
