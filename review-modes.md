---
name: review-modes
description: Use when a review covers more than one target, or when the reviewer authored the target. Extends skills/review.md; everything not named here follows that file.
---

# Review modes

Each case changes part of the workflow in `skills/review.md` and nothing else:
the output, the verification and the push rules are unchanged. Read that file
first.

### Parallel dispatch (multi-target)

Use when `$ARGUMENTS` contains more than one target.

1. The parent prepares each target first, per *Fetch & understand* in `skills/review.md`: its worktrees, its round directory, its `args`.
2. Launch one workflow per target, all at once, each with its own `args`. Where the harness has no workflow runner, one agent per target instead, running the stages serially with this prompt:

> Run the review workflow at `skills/review.md` on `<target>`, URL `<url>`, stages serial. Read `skills/writing-style.md` before drafting any prose; every line of `overview.md` and `comment_<model>.md` conforms to it. The worktrees already exist at `<paths>`: never create one at the shared path or switch branches. Do not commit, push, or post; the parent does that at the end. Report back the draft path and a one-paragraph summary of the verdict and headline findings.

3. Runs proceed concurrently, never sequenced.
   Corrections to a dispatched agent go in one message, sent once every QA result is in: a resumed agent replays its whole transcript, so each message costs the round again. Prose edits are the parent's own; an agent is resumed only for a run.
4. The parent runs the *Final check* in `skills/review-comment.md` over every returned draft, before the commit. A subagent's own pass never stands in for it.
5. After all return, the parent makes a single commit and push covering all reviews, its subject naming every target.
6. Reconcile before handing over. When agents on coupled targets disagree, re-derive the answer from the source, name the constraint both sides must satisfy, and write the same conclusion into every affected draft. Never ship contradicting drafts, and never settle it by taking one agent's summary.

A batch target set, "review all": every open non-draft target absent from the review directory, minus bot-authored, WIP-titled, reviewer-authored, and already-reviewed ones. Check the forge itself per target, not only the review directory, and drop on any hit. Confirm the final list with the user before reviewing more than one target, naming what was dropped and why.

- A listing that returns exactly its `--limit` was clipped, not exhausted. Re-run higher before treating the set as complete.
- A security fix in the set leaves the batch and runs alone, first: a batch spends one budget per target, and a fix earns its own.
- **Read every target's state again while the batch runs, and stop the round on one that merged.** The set is a snapshot and a batch outlives it: a target merges, a head advances, and the agent keeps measuring a tree nobody will read. Re-check before each handover at least, kill the rounds whose target closed, and re-point the ones whose head moved at the new sha and a new round directory. What a stopped round already wrote is kept as a record with a `Status:` line saying the target merged, never offered as a draft. A finding that survives on the default branch is then an issue, not a review.
- Sync the workspace before reading the review directory, and state the synced head when confirming the set. When it cannot be synced, derive the set read-only from the remote tree, `git ls-tree -r --name-only <remote>/<branch> -- <reviews-path>`, never from the working tree.
- Write the scope down before dispatch, in a status file beside the reviews: the confirmed set as a table, one row per target with its head sha and review directory, the dropped targets grouped by reason, and the steps to resume. Update it as results come back and commit it with the batch.
- A reviewer-authored target is named as available on request. A self-review runs only when the user asks for that one target by number, never as batch scope.
- An external contributor's target leaves the set. It is reviewed only when the user names it.
- When the run also covers already-reviewed targets whose head advanced, keep only the heads whose content changed: compare patch-ids per *Re-review rounds* in `skills/review.md`, drop every base-only move, and drop every target the reviewer already approved on the forge.

### Blind round

Use when the round measures the reviewer against findings already known: an
earlier round's, another reviewer's, or fixes already merged. Nothing the round
reads may carry them, so the agents get a repository holding the two commits and
nothing else, real shas kept, so every worktree command and every blob link
still resolves.

1. Build it from the synced checkout, full shas, then hang every worktree the
   round uses off it, the verifiers' included; `git log` there stops at the two
   commits.
   ```bash
   git init -q <scratch>/blind-<target>
   git -C <scratch>/blind-<target> fetch -q --depth=1 <checkout> <full head sha>
   git -C <scratch>/blind-<target> fetch -q --depth=1 <checkout> <full merge-base sha>
   git -C <scratch>/blind-<target> worktree add --detach <scratch>/blind-<target>-head <head sha>
   git -C <scratch>/blind-<target> worktree add --detach <scratch>/blind-<target>-base <merge-base sha>
   ```
2. No PR dump under `.worktrees/` for the round, and no prior-round read by the
   parent: the workflow gets `args.blind: true`, whose sentence forbids the
   threads, the round directories, the dump and history.
3. The round note and the draft's `Round:` line say `Blind round`.

Cost against an ordinary round: two shallow fetches, about a minute, tokens
unchanged; an estimate until a blind round measures it.

### Own PR (the reviewer authored it)

Check with `gh pr view <number> --json author`. Findings land as commits on the branch, never as a review to post.

- No `comment_<model>.md`, no `pr-body.md`, post nothing. `claims.md` and `overview.md` are still written.
- Apply every mechanical fix in the checkout the review uses: comments, docs, tests, naming, dead code. Then *Fix* step 7 in `skills/change.md`, the local CI run, until green.
- Never apply without asking: observable behavior changes, fixes to defects predating the branch, anything a maintainer would treat as a design decision. Present each as a named decision.
- One commit per finding class, conventional subject. Push to the PR's head repository, never upstream.
- Hand over the branch and shas, then what was left unapplied and the decision each needs.
