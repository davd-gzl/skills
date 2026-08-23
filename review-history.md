---
name: review-history
description: Query the local corpus of past reviews. Whether a target was reviewed, per-round verdicts, what was posted, findings by author, file, or term, and cross-review counts. Read-only.
argument-hint: "[pr-number] | [search term] | author <login> | stats | posted | unposted | recent [n]"
---

# Review history

Answer questions about work already reviewed, from the review directories on
disk. Never re-review to answer a history question. `gh` is allowed only for
what the corpus cannot hold, the target's current state and whether the head
moved since the review; never to re-derive what is already written down.

**Input:** `$ARGUMENTS`: a target number, a free-text term, or a mode word below.
Empty means `recent 10`.

## Corpus layout

- `projects/<repo>/reviews/<slug>/<n>-<short-sha>/` per round, `overview.md` at
  the slug root, `tests/` inside the round directory.
- Round directories are a convention, not a guarantee: an older review may keep
  its files directly under the slug. Run `ls -d projects/*/reviews/*/` before
  writing any path glob, and widen it to every directory it misses, or those
  reviews drop out of the answer with no error.
- Current naming is `review_<model>_<reviewer>.md` plus `comment_<model>.md`.
  Older rounds hold the same content under other names, and one round may hold
  several reviewer files from parallel lenses, not all of which carry a verdict.
- Round numbers count up, and duplicates with different shas exist. Order those
  by mtime. A deep re-review of an already-reviewed sha takes `<n+1>-<same-sha>`.
- A generated index lags every review written since it last ran. Read its own
  last-updated line and let the disk win on any disagreement.
- Audit-harness output is explicitly unconfirmed. Label a hit from there
  unverified, never as a review finding.
- A batch status file is transient and may belong to a session running now.
  Treat it as a claim, verify on disk, and expect new rounds to land mid-query.

## File formats

The verdict appears three ways: `**Verdict: X** — ...`, a plain
`Verdict: X — ...`, and a `## Verdict` heading carrying it on the next non-blank
line, possibly bold and in mixed case. Some lines carry a `> ` prefix or a dash
for the colon. The vocabulary is APPROVE, REQUEST CHANGES, NEEDS DISCUSSION and
CLOSE, plus whatever legacy words the corpus holds. A reanchored round may state
its verdict only inside the `Round <n>.` note. When extraction yields nothing or
nonsense, open the file.

Posted state comes from `comment*.md`, per round: a `^Posted: <url>` line means
posted, a comment file without one is an unposted draft, and no comment file
means no draft. Absence is never guessed from context. `[posted](...)` marks
which inline comments went out; a `## SKIP` section was withheld on purpose, and
its first body line names the duplicate it defers to.

The metadata header is plain in old files and bold-wrapped in new ones. Its
staleness figure was computed when the review was written, not today.

## Modes

**Target lookup**, when `$ARGUMENTS` is a number.

```bash
find projects/*/reviews -maxdepth 2 -type d -name '<number>-*'
```

No hit means not reviewed. A hit whose directory holds no review file is
reported as present but reviewless, never as reviewed. The same number in two
repositories is disambiguated before answering. Report, in order: the slug
directory, one line per round in mtime order with its verdict and posted state,
then the latest round's TL;DR and its headline findings by severity. When rounds
disagree, the latest stands and the overturned one is named.

**Search**, free text including paths and subsystems. Findings cite `file:line`
anchors and drafts head their sections `## <path>:<line>`, so a path fragment is
a good term.

```bash
grep -rli '<term>' projects/*/reviews --include='*.md'
```

Collapse to one line per target, newest round first: the number, the latest
verdict, the matching section's severity, a one-line quote, the file link.
Comment drafts duplicate the review file's findings, so count the target once.

**author `<login>`**, from the metadata header:

```bash
grep -rlE --include='*.md' '^\*{0,2}Author:?\*{0,2} <login> \|' projects/*/reviews
```

One line per target: number, title, latest verdict, posted state.

**stats**. Verdict distribution, posted against draft against no-draft, and the
multi-round targets. Compute from the listing loop, one row per target: counting
every round double-counts the re-reviews.

**posted**. Every review actually sent, any round, with its URL:

```bash
grep -r --include='comment*.md' -m1 -H '^Posted:' projects/*/reviews | sed 's/:Posted: /\t/'
```

**unposted**. Findings raised and never sent, three sources reported apart:
latest-round drafts with no `Posted:` line, `^## SKIP` sections inside drafts,
and `## Open questions` sections in review files.

**recent [n]**, default 10. Latest rounds by mtime, each with verdict and posted
state:

```bash
find projects/*/reviews -mindepth 2 -maxdepth 3 -type d -name '[0-9]*-*' \
  -printf '%T@ %p\n' | sort -rn | head -<n> | cut -d' ' -f2-
```

## Listing loop

The canonical one row per target:
`<target> TAB <verdict> TAB <POSTED|draft|no-draft> TAB <latest-round-dir>`. It
handles every naming generation, the prefix-less files, the layouts with no round
directory and the `tests/` directories, under both bash and zsh.

```bash
for d in projects/*/reviews/*/; do
  n=$(basename "$d"); n=${n%%-*}
  last=$(find "$d" -maxdepth 1 -type d -name '[0-9]*-*' | sort -V | tail -1)
  [ -z "$last" ] && last="${d%/}"
  rf=$(find "$last" -maxdepth 1 -name '*.md' ! -name 'comment*' ! -name 'overview*' \
       -exec grep -il 'verdict' {} + 2>/dev/null | sort | head -1)
  if [ -z "$rf" ]; then printf '%s\tNO-REVIEW-FILE\t-\t%s\n' "$n" "$(basename "$last")"; continue; fi
  v=$(awk '/^#+ *Verdict/{h=1;next} h&&NF{print;exit} /^(> )?\*{0,2}Verdict[:* —-]/{print;exit}' "$rf" |
      grep -oiE 'request changes|needs discussion|approve|close' | head -1 |
      tr 'a-z' 'A-Z')
  c=$(find "$last" -maxdepth 1 -name 'comment*.md' | sort | head -1)
  if [ -z "$c" ]; then post=no-draft
  elif grep -q '^Posted:' "$c"; then post=POSTED
  else post=draft; fi
  printf '%s\t%s\t%s\t%s\n' "$n" "${v:-?}" "$post" "$(basename "$last")"
done
```

A `?` verdict means the file states it somewhere nonstandard, a round note or
prose. Open that file rather than reporting the verdict unknown.

## Rules

- Read-only. This skill never writes a review, edits a draft, posts, pushes, or
  regenerates an index.
- Cite every `reviews/...` path as a clickable link, so the user opens the source.
- A finding's severity is the section it sits under. Report the section, never
  re-rank it.
- Verdicts are per round, and the reviewer files inside one round can disagree
  when they came from parallel lenses. Report the spread, never an average.
- The corpus reflects the reviewed sha, not the target's current head. Before
  presenting a finding as live, check that the head moved, or say plainly that it
  was not checked.
- Before calling a draft unposted, read the target's live review state alongside
  the round shas: `gh pr view <n> --json reviewDecision,latestReviews`. A review
  stands until it is dismissed, so an approval given at an older sha still holds,
  and a draft repeating that verdict adds nothing. Report the draft only where
  its verdict differs from what stands.
- Never infer "unreviewed" from a miss under one glob. Match the leading number
  across every review directory first: slugs drift and repositories differ.
- Prefer `find` to a bare glob in an ad-hoc command. The interactive shell is
  zsh, where an unmatched glob aborts the whole command line.
