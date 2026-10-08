---
name: shortcuts
description: The words the user types and what each one starts, in any workspace. In context as the session opens. The shape of a reply is skills/reply.md and the register is skills/short-form.md.
---

# Shortcuts

A reply that waits names one letter, the first cell of its row below, never two
words: the user types that letter to act, on a line of letters alone, so `p d`
or `pd` gives both words and `d` inside a sentence gives none. A reply may also coin a letter
for a next step it proposes that publishes nothing and the request did not already ask for, defined beside it, `s`: run
the simplify pass; it holds for the next message only, and never takes a letter
this table already gives.

In context as the session opens, through a SessionStart hook. The register is `skills/short-form.md`
and the shape of a reply is `skills/reply.md`.

## The words

What the user types, and what each word starts. A word a skill defines is read
as the skill defines it; ask when the reading changes what gets built.

| Word | What it starts | Rule |
| --- | --- | --- |
| `review <target>` | one review round: the overview, the comment draft, the claim table and its tests, committed, nothing pushed or posted | `skills/review.md` |
| `quick review <target>`, `deep review <target>` | the same round on a preset: `quick` for the overview of what a change is worth, one finder per bundle on the Warning-finding angles, each running its own Warning checks, judges in short parallel batches, no reflector, the text pass past its word floor; `deep` where the code is complex or unknown, finders at 60 calls with the tests angle and claims on every bundle, judges by three at the standard effort, the ceiling. Each word names an output ceiling that binds only with `+<n>` on the word, which sets it, and `+<angle>` runs that angle whatever the word, `+claims` for one. |
| `plan review <target>` | the round's steps 1 to 3, then three to five questions about the target in one reply, each answer a topic and one finder, the run launching on `go` | *Modes*, `skills/review.md` |
| `review all` | every open target not yet reviewed, the scope written down first | `skills/review-modes.md` |
| `plan` | what the next review round will run and cost, the stage table and the projection | `./scripts/review-plan.py` |
| `config <stage> <key> <value>` | that knob of the review workflow changed, the plan reprinted, the estimate given | `./scripts/review-plan.py --set <stage>.<key>=<value> --write`, *A change to the run's shape* in `skills/authoring.md` |
| `fix <issue or finding>` | a change on the fork: spec, plan, worktree, fix, CI, simplify last; nothing pushed | `skills/change.md` |
| `try <pr> on <repo>` | the project booted locally, ready to click through | `skills/try.md` |
| `video` | the clip, only once the finding's text is frozen | `skills/try.md` |
| `stop` | the stack and the worktree torn down | `skills/try.md` |
| `report [date]` | the period's status report | `skills/report.md` |
| `p`, `push` | everything the closing block names, once: every commit and push the work needs, then the post, upload, title or body it links | *Consent*, workspace `AGENTS.md` |
| `pr`, `p r`, `push review` | the round over the change's branch, step 10 of *Fix*, its fixes applied, then everything `p` sends; a bare `p` runs no round | `skills/change.md` |
| `r` | the same round over the change's branch, its fixes applied, nothing committed or pushed | `skills/change.md` |
| `pf`, `p f`, `push force` | everything `p` sends, the branch it names replaced on its remote with `--force-with-lease`: Invariant 8's approval, for that push alone | Invariant 8 |
| `post` | the shown draft goes to its target where nothing waits to be pushed, and `p` sends it the same; `post as an AI` adds the marker; `upload` sends media | `skills/review-comment.md`, `skills/issue.md`, `skills/change.md` |
| `m`, `x`, `d` | merge, close or delete: that one action on the named target | Invariant 2 |
| `o`, `ready` | the named draft pull request marked ready for review | Invariant 2 |
| `make this review public` | the round to the public artifact repo, links repointed | *Consent* |
| `path` | the worktree the work sits in, its path alone | here |
| "a comment" | the `comment_<model>.md` draft and the text for the target, never an explanation | `skills/review-comment.md` |
| `TLDR` | the answer in one line, and the word it waits on | here |
| `continue` | the local work resumed, dead agents re-dispatched first; nothing published | here |
| `go`, `ok`, `yes`, `sure`, anything else | local work only, never a publish | Invariant 2 |
