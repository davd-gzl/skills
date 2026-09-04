---
name: review-modes
description: Use when a review covers more than one target, or when the user asks for a deep, parallel, or red-team pass, or when the reviewer authored the target. Extends skills/review.md; everything not named here follows that file.
---

# Review modes

Each mode changes part of the workflow in `skills/review.md` and nothing else:
the output format, `comment_<model>.md`, the verification discipline and the push
rules are unchanged. Read that file first.

### Parallel dispatch (multi-target)

Use when `$ARGUMENTS` contains more than one target.

1. The parent prepares each checkout first, per *Fetch & understand* in `skills/review.md`. Subagents never create worktrees or check out branches.
2. Dispatch one agent per target, all at once, each with this prompt:

> Run the review workflow at `skills/review.md` on `<target>`, URL `<url>`. Read `skills/writing-style.md` before drafting any prose; every line of the review file and `comment_<model>.md` conforms to it. The checkout already exists at `<path>` with the target checked out: never create a worktree or switch branches. Follow every other step in that file. Do not commit, push, or post; the parent does that at the end. Report back the review file path and a one-paragraph summary of the verdict and headline findings.

3. Agents run concurrently, never sequenced.
4. The parent runs the *Final check* in `skills/review-comment.md` and both QA agents over every returned draft, before the commit. A subagent's own pass never stands in for them.
5. After all return, the parent makes a single commit and push covering all reviews, its subject naming every target.
6. Reconcile before handing over. When agents on coupled targets disagree, re-derive the answer from the source, name the constraint both sides must satisfy, and write the same conclusion into every affected review file. Never ship contradicting drafts, and never settle it by taking one agent's summary.

A batch target set, "review all": every open non-draft target absent from the review directory, minus bot-authored, WIP-titled, reviewer-authored, and already-reviewed ones. Check the forge itself per target, not only the review directory, and drop on any hit. Confirm the final list with the user before reviewing more than one target, naming what was dropped and why.

- A listing that returns exactly its `--limit` was clipped, not exhausted. Re-run higher before treating the set as complete.
- **Read every target's state again while the batch runs, and stop the round on one that merged.** The set is a snapshot and a batch outlives it: a target merges, a head advances, and the agent keeps measuring a tree nobody will read. Re-check before each handover at least, kill the rounds whose target closed, and re-point the ones whose head moved at the new sha and a new round directory. What a stopped round already wrote is kept as a record with a `Status:` line saying the target merged, never offered as a draft. A finding that survives on the default branch is then an issue, not a review.
- Sync the workspace before reading the review directory, and state the synced head when confirming the set. When it cannot be synced, derive the set read-only from the remote tree, `git ls-tree -r --name-only <remote>/<branch> -- <reviews-path>`, never from the working tree.
- Write the scope down before dispatch, in a status file beside the reviews: the confirmed set as a table, one row per target with its head sha and review directory, the dropped targets grouped by reason, and the steps to resume. Update it as results come back and commit it with the batch.
- A reviewer-authored target is named as available on request. A self-review runs only when the user asks for that one target by number, never as batch scope.
- When the run also covers already-reviewed targets whose head advanced, keep only the heads whose content changed: compare patch-ids per *Re-review rounds* in `skills/review.md`, drop every base-only move, and drop every target the reviewer already approved on the forge.

### Deep mode (multi-angle, single target)

Trigger: the user asks for a **parallel**, **red-team / blue-team**, or **deeper** review of one target, or "review and loop until perfect". Deep mode runs many lenses on one target; everything else follows the normal flow: output format, comment.md, push rules.

1. **Set up.** Run *Fetch & understand* and *Reproduce the failure* in `skills/review.md` once; hand the same paths to every agent.
2. **Dispatch lens agents**, concurrent. Default three lenses; add more for large targets: perf, docs, API surface, ops impact. Each prompt is self-contained: checkout path, target, diff path, prior-review paths, one narrow lens. Each agent returns findings in this skill's severity model with `file:line` citations.
   - **Red team**: bugs, broken invariants, security holes, edge cases, missing validation, downstream footguns.
   - **Blue team**: missing tests, undocumented invariants, hardening gaps, misuse-inviting ergonomics, migration and rollback risk.
   - **Correctness**: does the code match the description and linked issue? Scope drift, silent behavior changes, contract mismatches.
   - When the workspace carries a catalog of the project's recurring bug classes, name it in every lens prompt and have each lens walk the classes its angle covers. At synthesis, confirm every class was covered by at least one lens and walk the uncovered ones against the diff before finalizing.
3. **Synthesize.** Dedupe, re-rank by the severity ladder, verify each finding per *Verification discipline* in `skills/review.md`. Never keep a finding on an agent's summary alone.
4. **Critic pass, exactly one round, parallel.** 2-3 critics in one message over the synthesized draft plus the diff and checkout, each with a distinct lens: verdict-check, missing-blocking, severity-calibration. Each returns ONLY findings that flip the verdict, raise a severity band, or add a missing Critical or Warning; otherwise exactly `NO_MATERIAL_FINDINGS`. Never send an open-ended "what's wrong" prompt. After: dedupe, re-read each cited `file:line`, drop what does not hold, revise. Never loop critics.
5. **Claim-verification gate, parallel.** Before drafting comment.md, one agent extracts every falsifiable claim, behavioral, structural or numeric, and runs a check designed to prove each false. It returns only claims that fail or cannot be verified; re-read those against the code, drop or fix each. Facts only; severity and verdict belong to the critic pass.
6. **Output.** Normal flow. Metadata line: `Model: <model> (<intensity>, deep)`; ask when the intensity is unknown. Deep mode over an already-reviewed commit opens a new `<n+1>-<same-sha>` directory whose round note names the mode and which prior verdict it confirms or overturns.

### Own PR (the reviewer authored it)

Check with `gh pr view <number> --json author`. Findings land as commits on the branch, never as a review to post.

- No `comment_<model>.md`, no `pr-body.md`, post nothing. The review file is still written.
- Apply every mechanical fix in the checkout the review uses: comments, docs, tests, naming, dead code. Then *Fix* step 7 in `skills/change.md`, the local CI run, until green.
- Never apply without asking: observable behavior changes, fixes to defects predating the branch, anything a maintainer would treat as a design decision. Present each as a named decision.
- One commit per finding class, conventional subject. Push to the PR's head repository, never upstream.
- Hand over the branch and shas, then what was left unapplied and the decision each needs.
