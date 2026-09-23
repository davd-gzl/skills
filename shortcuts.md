---
name: shortcuts
description: The words the user types and what each one starts, in any workspace. Imported through CLAUDE.md. The shape of a reply is skills/reply.md and the register is skills/short-form.md.
---

# Shortcuts

Imported through `CLAUDE.md`. The register is `skills/short-form.md`
and the shape of a reply is `skills/reply.md`.

## The words

What the user types, and what each word starts. A word a skill defines is read
as the skill defines it; ask when the reading changes what gets built.

| Word | What it starts | Rule |
| --- | --- | --- |
| `review <target>` | one review round: the overview, the comment draft, the claim table and its tests, committed, nothing pushed or posted | `skills/review.md` |
| `quick review <target>`, `deep review <target>` | the same round on a preset: `quick` for the overview of what a change is worth, one finder per bundle on the Warning-finding angles, each running its own Warning checks, judges in short parallel batches, no reflector, the text pass past its word floor; `deep` where the code is complex or unknown, finders at 60 calls over hot bundles split by code file, judges by three, the ceiling. Each word names an output ceiling that binds only with `+<n>` on the word, which sets it, and `+<angle>` runs that angle whatever the word, `+claims` for one. |
| `plan review <target>` | the round's steps 1 to 3, then three to five questions about the target in one reply, each answer a topic and one finder, the run launching on `go` | *Modes*, `skills/review.md` |
| `review all` | every open target not yet reviewed, the scope written down first | `skills/review-modes.md` |
| `plan` | what the next review round will run and cost, the stage table and the projection | `./scripts/review-plan.py` |
| `upgrade skills` | every skill or script line of the workspace's `TODO.md` read as its critic, a project's line moved into its project's tree, then taken to its rule or script, one commit each with its estimate, the line struck as it lands; a line that fails the read is asked, never struck; every line that stays gets a verdict with its reason; nothing pushed | *Upgrading from the TODO*, `skills/authoring.md` |
| `config <stage> <key> <value>` | that knob of the review workflow changed, the plan reprinted, the estimate given | `./scripts/review-plan.py --set`, *A change to the run's shape* in `skills/authoring.md` |
| `fix <issue or finding>` | a change on the fork: spec, plan, worktree, fix, CI, simplify last; nothing pushed | `skills/change.md` |
| `try <pr> on <repo>` | the project booted locally, ready to click through | `skills/try.md` |
| `video` | the clip, only once the finding's text is frozen | `skills/try.md` |
| `stop` | the stack and the worktree torn down | `skills/try.md` |
| `report [date]` | the period's status report | `skills/report.md` |
| `post` | the shown draft goes to its target; `post as an AI` adds the marker; `upload` sends media | `skills/review-comment.md`, `skills/issue.md`, `skills/change.md` |
| `push` | the whole git flow, every commit and push the work needs, once | *Consent*, workspace `AGENTS.md` |
| `merge`, `close`, `delete` | that one action on the named target | Invariant 2 |
| `make this review public` | the round to the public artifact repo, links repointed | *Consent* |
| `path` | the worktree the work sits in, its path alone | here |
| "a comment" | the `comment_<model>.md` draft and the text for the target, never an explanation | `skills/review-comment.md` |
| `TLDR` | the answer in one line, and the word it waits on | here |
| `continue` | the local work resumed, dead agents re-dispatched first; nothing published | here |
| `go`, `ok`, `yes`, `sure`, anything else | local work only, never a publish | Invariant 2 |
