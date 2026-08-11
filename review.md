---
name: review
description: Adversarial review of a pull request, a branch, or a repository-level failure in any project. Writes a severity-grouped review file plus a comment_<model>.md GitHub draft, posted only after user approval. Supports multi-target parallel dispatch and a deep multi-angle mode.
argument-hint: <repo>#<pr-number> | <url> | <repo> <subject>
---

# Review

**Input:** `$ARGUMENTS`: a PR number or URL, a repo name plus a subject, or several of these. Process each target independently.

Write all visible prose per `skills/writing-style.md`; its scannability rule covers every artifact here. In every artifact, verdict first, then narrative, then findings; the review file alone opens with its Overview, then the verdict. Make every reference clickable, every file readable without the chat, and bold the one number or word that carries the decision.

## Workflow

Run in order for a single target; multi-target runs wrap this via *Parallel dispatch*. Run from the workspace root.

1. *Fetch & understand*: sync the checkout, gather target data, read prior reviews.
2. Run the *Re-review rounds* gate when a prior round exists.
3. *Reproduce the failure*, or run the tests for a PR.
4. *Review the diff*, or the failing surface.
5. *Write tests* for test-shaped findings.
6. Write the review file per *Output*.
7. Draft `comment_<model>.md` per *GitHub review draft*, then run its *Final check* and QA agents. Draft whether or not anything will be posted. Skip only for a PR the reviewer authored; see *Own PR*.
8. Run the `skills/writing-style.md` Pass over every line of the review file and `comment_<model>.md`. Never skip it. Re-run it after any later edit to that prose, including an edit made in answer to a question about it. State which passes ran when handing over.
9. One commit and one push covering everything. This push is pre-authorized; see *Rules*.
10. Hand over. Link the `comment_<model>.md` draft, not only the review file. Add a "Decisions needed" list, one line each: a borderline verdict, Open questions worth promoting. Omit when empty. Never list an APPROVE as needing confirmation. Post only on the literal word `post`.

## Subjects

The subject is a PR by default. Two others recur; they change only *Fetch & understand* and the anchors, the `file:line` a finding attaches to:

- **Branch or working diff**: no PR yet. Anchor findings to `file:line` at the branch head.
- **Repository-level failure**: red CI on the default branch, a failing gate, a broken release. The "diff" is the failing surface. Enumerate every failing condition from its authoritative source, attribute each to the code or config causing it, and separate what a PR can fix from what only a maintainer with project permissions can. `<slug>` names the failure, not a commit.

Both live in `projects/<repo>/reviews/<slug>/`.

## Modes

### Parallel dispatch (multi-target)

Use when `$ARGUMENTS` contains more than one target.

1. The parent prepares each checkout first, per *Fetch & understand*. Subagents never create worktrees or check out branches.
2. Dispatch one Agent per target, all in one message, `subagent_type: general-purpose`:

> Run the review workflow at `skills/review.md` on `<target>`, URL `<url>`. Read `skills/writing-style.md` before drafting any prose; every line of the review file and `comment_<model>.md` conforms to it. The checkout already exists at `<path>` with the target checked out: never create a worktree or switch branches. Follow every other step in that file. Do not commit, push, or post; the parent does that at the end. Report back the review file path and a one-paragraph summary of the verdict and headline findings.

3. Agents run concurrently, never sequenced.
4. The parent runs the *Final check* and both QA agents over every returned draft, before the commit. A subagent's own pass never stands in for them.
5. After all return, the parent makes a single commit and push covering all reviews.
6. Reconcile before handing over. When agents on coupled targets disagree, re-derive the answer from the source, name the constraint both sides must satisfy, and write the same conclusion into every affected review file. Never ship contradicting drafts, and never settle it by taking one agent's summary.

A batch target set, "review all": every open non-draft target absent from the review directory, minus bot-authored, WIP-titled, reviewer-authored, and already-reviewed ones. Check the forge itself per target, not only the review directory, and drop on any hit. Confirm the final list with the user before reviewing more than one target, naming what was dropped and why.

- A listing that returns exactly its `--limit` was clipped, not exhausted. Re-run higher before treating the set as complete.
- Sync the workspace before reading the review directory, and state the synced head when confirming the set. When it cannot be synced, derive the set read-only from the remote tree, `git ls-tree -r --name-only <remote>/<branch> -- <reviews-path>`, never from the working tree.
- Write the scope down before dispatch, in a status file beside the reviews: the confirmed set as a table, one row per target with its head sha and review directory, the dropped targets grouped by reason, and the steps to resume. Update it as results come back and commit it with the batch.

### Deep mode (multi-angle, single target)

Trigger: the user asks for a **parallel**, **red-team / blue-team**, or **deeper** review of one target, or "review and loop until perfect". Deep mode runs many lenses on one target; everything else follows the normal flow: output format, comment.md, push rules.

1. **Set up.** Run *Fetch & understand* and *Reproduce the failure* once; hand the same paths to every agent.
2. **Dispatch lens agents**, one message, concurrent, `subagent_type: general-purpose`. Default three lenses; add more for large targets: perf, docs, API surface, ops impact. Each prompt is self-contained: checkout path, target, diff path, prior-review paths, one narrow lens. Each agent returns findings in this skill's severity model with `file:line` citations.
   - **Red team**: bugs, broken invariants, security holes, edge cases, missing validation, downstream footguns.
   - **Blue team**: missing tests, undocumented invariants, hardening gaps, misuse-inviting ergonomics, migration and rollback risk.
   - **Correctness**: does the code match the description and linked issue? Scope drift, silent behavior changes, contract mismatches.
3. **Synthesize.** Dedupe, re-rank by the severity ladder, verify each finding per *Verification discipline*. Never keep a finding on an agent's summary alone.
4. **Critic pass, exactly one round, parallel.** 2-3 critics in one message over the synthesized draft plus the diff and checkout, each with a distinct lens: verdict-check, missing-blocking, severity-calibration. Each returns ONLY findings that flip the verdict, raise a severity band, or add a missing Critical or Warning; otherwise exactly `NO_MATERIAL_FINDINGS`. Never send an open-ended "what's wrong" prompt. After: dedupe, re-read each cited `file:line`, drop what does not hold, revise. Never loop critics.
5. **Claim-verification gate, parallel.** Before drafting comment.md, one agent extracts every falsifiable claim, behavioral, structural or numeric, and runs a check designed to prove each false. It returns only claims that fail or cannot be verified; re-read those against the code, drop or fix each. Facts only; severity and verdict belong to the critic pass.
6. **Output.** Normal flow. Metadata line: `Model: <model> (<intensity>, deep)`; ask when the intensity is unknown. Deep mode over an already-reviewed commit opens a new `<n+1>-<same-sha>` directory whose round note names the mode and which prior verdict it confirms or overturns.

### Own PR (the reviewer authored it)

Check with `gh pr view <number> --json author`. Findings land as commits on the branch, never as a review to post.

- No `comment_<model>.md`, no `pr-body.md`, post nothing. The review file is still written.
- Apply every mechanical fix in the checkout the review uses: comments, docs, tests, naming, dead code. Then *Run the CI locally* until green.
- Never apply without asking: observable behavior changes, fixes to defects predating the branch, anything a maintainer would treat as a design decision. Present each as a named decision.
- One commit per finding class, conventional subject. Push to the PR's head repository, never upstream.
- Hand over the branch and shas, then what was left unapplied and the decision each needs.

### Bot mode (automatic review)

Trigger: the user names a target or set to go out as an automated bot review; never infer the set.

- `Event: COMMENT` regardless of verdict; the review file keeps its verdict.
- Body opens with `[AI bot - Automatic review]`, then one paragraph scoping the pass to technical checks, disclaiming design judgement and any merge verdict.
- Findings, anchors, severities, repros unchanged. Verify every finding with a real run before posting.

## For each target

### Fetch & understand

- Sync the checkout per the *Sync first* rule in `AGENTS.md`: `git remote -v`, fetch every remote, compare `git rev-list --left-right --count HEAD...<remote>/<branch>`. The canonical remote is often `upstream`.
- Never review from a dirty tree without saying so. Never write into the reviewed checkout outside a dedicated fix branch.
- **A branch from outside the project gets a static danger pass before it is fetched into a local checkout**, nothing executed. Read the raw diff for: changes to the build and dependency surface, the CI workflows, the lockfile, the manifest, container files and any shell script; calls that execute, reach the network, read credentials or the environment, or write the filesystem; encoded or generated code; and Trojan Source, meaning non-ASCII added lines, bidirectional overrides, zero-width characters and homoglyphs. Say in the review what the pass covered and what it found, and carry anything not malicious but risky into the findings. `author_association` of `NONE` or `FIRST_TIME_CONTRIBUTOR` is the trigger, from `gh api repos/<repo>/pulls/<n> --jq '.author_association'`; `gh pr list --json` has no such field.
- **A worktree that already exists is reused, never cleaned.** `worktree add` fails on an existing path: re-run only the checkout. It may carry uncommitted edits from another session, so never stash, clean or revert; report them and work around them.
- For a PR: `gh pr view <number> -R <repo> --json title,body,author,baseRefName,headRefName,files,additions,deletions,commits` and `gh pr diff <number> -R <repo>`.
- Read the description, linked issues, all comments via `gh api repos/<repo>/issues/<number>/comments`, and all review comments via `gh api repos/<repo>/pulls/<number>/comments`. Note unresolved threads. Paginate every list call with `gh api --paginate`: truncation at 30 items is silent.
- Read past reviews in `projects/<repo>/reviews/` first; focus on what changed since the last reviewed commit.
- Read every changed file in full, and map callers, dependents, and siblings.

Treat CI as a first-class source. `gh run list` shows only GitHub Actions; external checks from apps are check runs. Read the authoritative list for the exact commit:

```bash
sha=$(gh api repos/<repo>/commits/<branch> --jq '.sha')
gh api --paginate repos/<repo>/commits/$sha/check-runs --jq '.check_runs[] | "\(.conclusion)\t\(.name)"'
gh api repos/<repo>/commits/$sha/status --jq '.state'
```

Query each failing check's own API for detail, not its GitHub summary blurb; quote the gate's own numbers. When that API refuses, fall back to the check run's `output` fields and label every number as read from the summary, never as gate-verified.

### Re-review rounds (head advanced)

When a prior round exists and the head moved from `<old-sha>` to `<new-sha>`, compare patch-ids, stable hashes of each diff's content:

```bash
git fetch <remote> <base-branch>
git diff $(git merge-base <remote>/<base-branch> <old-sha>) <old-sha> | git patch-id --stable
git diff $(git merge-base <remote>/<base-branch> <new-sha>) <new-sha> | git patch-id --stable
```

- **Equal**: base-only move. Do NOT re-author: copy the latest round's `.md` files into `<n+1>-<new-sha>/`, rewrite shas, remap anchors, reading the checkout to fix any that no longer map, add a one-line round note saying the head advanced with content unchanged, anchors re-cut, verdict unchanged, then commit. Skip the rest of the workflow.
- **Differ**: full re-review round, focused on what changed since `<old-sha>`.
- **New head is a merge of the base branch**: never base-only. Run `git show <new-sha> --cc`; any hunk it prints is conflict-resolution content, reviewed like any diff. Base commits may add tests the branch now fails: run the affected suite on the new head.
- **`<old-sha>` unreachable**: skip the gate, run a full round against the merge-base, note the fallback.

Open every full re-review round with a round-note paragraph between the metadata block and the Overview: `Round <n>.`, how the head moved, what changed, which prior findings were resolved or carried.

### Reproduce the failure

- `gh pr checks <number> -R <repo>` first, plus the check-runs API. Note every failure.
- Run the project's own test and lint commands, taken from its CI workflow file, never guessed. Match the invocation exactly, pinned versions included.
- Record pass or fail per affected package or job.
- Before attributing any failure to the diff, run the same check on the merge-base. A failure that also occurs there is pre-existing.
- A repository-level failure gets the same discipline: reproduce each condition on the default branch and identify the introducing commit where history allows.
- When a target changes runtime behavior of a server or tool, boot it and exercise it live; record what was verified live in the Verified section.

### Review the diff

Read every line. Look for correctness defects: logic errors, missing nil checks, unchecked type assertions, off-by-one. Untested paths. Breaking changes without migration. Style inconsistencies. Reuse and simplification: duplicated helpers, foldable code, unclear naming, missing doc comments, undocumented invariants, filed as Suggestions or Nits, never blockers. Docs impact.

**Refactor pass, over every added block.** Ask whether fewer lines carry the same behaviour: a value computed twice, a guard the caller already applied, memoization that stabilises nothing, an abstraction with one call site. Where they do, post the replacement as a `Refactor:` suggestion the author applies in one click, never prose describing the change, and record both line counts in the review file.

**Verification discipline.** Every finding passes all of these before it enters the review:

- Verify against the actual file, never from memory or a summary.
- Back every behavioral claim with an actual run, at every severity. Never assert stdlib or runtime behavior from memory.
- **Report what the user loses, never the artifact that causes it.** A conflict, a deleted file, a moved import and a missing guard are mechanical facts; name the action that stops working, for whom, and where. Test it by reading the line cold as a maintainer, deciding in one pass whether to care.
- **When the base has moved, build the merged state and run it.** Apply the base's version of the disputed hunk into the running branch, exercise the path, then revert.
- **A synthetic event is not a run, for anything a user drives with a mouse or keyboard.** A dispatched event skips the focus moves, default actions and library handlers a real input goes through, so it passes where the real input fails. Drive the real app with real input; a synthetic event is only a probe for which listener fired.
- For any claim that the diff *causes* a behavior, run the repro on the merge-base too. Reproduces there: pre-existing, causation false; attribute only the delta and state both numbers.
- When a baseline run or a test kills a finding, drop the finding. Never keep the conclusion and attach a new rationale.
- Treat every "bound" or "leak" claim as quantitative: name the quantity, vary what claims to bound it, confirm they track.
- A reachability claim is proved by construction, never by survey. Build the smallest artifact that would fail if the claim were false and run it, from outside the boundary the claim is about: never a test that builds its own victim, never a grep for existing instances.
- Vary the conditions before naming them. A finding that holds under one shape and not another states which, having tried both.
- Run greps and lint in the reviewed checkout at the reviewed commit.
- Confirm a symbol exists with the project's own linter or compiler, sanity-checked first with a bogus symbol.

**Static-analysis findings** are leads, not findings. Before one enters the review: read the flagged lines and state the concrete failure in the project's own terms, never a rule ID plus stock message. Separate real defects from unadopted policies; only the defect may be a Warning or above. Say what the fix costs; a behavior-change fix is a maintainer decision, say so. Never report a count as a finding: group by rule, name one representative, give the full list once.

### Write tests for test-shaped findings

When findings suggest fragile or under-tested code, write edge-case tests, run them, report the failures. Save to `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/tests/`.

When a finding's fix is a test the author should add, ship the test: write it under `tests/`, assert the post-fix state, never the bug's current output, run it, and when it also proves a bug show it failing before the fix and passing after. Embed it in the comment.md finding so the author can paste it in.

Pair the defect with the baseline it breaks in one assertion, and ship both expectations side by side, the current one active and the fixed one commented, each labelled. The pair shows in one screen what the code does and what it should do, and the commented line is what the author uncomments once the fix lands.

Start each test file with a comment block carrying exact repro commands runnable from a plain clone: no workspace paths, no `$HOME`. Pin `git checkout <hash>` in test-file headers only; review and comment.md repro blocks never pin. The header stands alone: the run block, then at most 2-3 lines covering mechanism, observed result at the pinned hash, and what changes when fixed. Name code paths by their actual symbol. One-line in-test comments per non-obvious step.

## Overview (`overview.md`)

Write one when the subject is complex: the change spans subsystems, hinges on concepts the reader must learn first, or lands faster as a diagram or a table than as prose. Skip it for a docs-only change, a mechanical refactor or a small localized fix. An explicit ask from the user wins in both directions.

- Markdown, never HTML. It goes at the review directory root, `projects/<repo>/reviews/<slug>/overview.md`, never inside a round directory: it explains the subject, not one commit. It renders where the reader already is, diffs line by line, and needs nothing opened.
- Explainer only, carrying no review state: no verdict, no findings, no reviewed sha, no round. Name the generating model once, under the title.
- Pick what fits: a plain-language explanation, a dataflow or state diagram as a `mermaid` block, a decision table, before and after values, a Concepts section when the subject needs one. No emoji, no inline HTML, no script.
- Where a page would have used a simulator, compute the interesting inputs and put the results in a table. The reader gets the answer without moving a slider, and every number is checkable from the file.
- Run the mirrored logic before publishing its numbers, against the project's own tests where they exist and against the mirrored source where they do not, and say which of the two it was.
- Update it only when new commits change the subject's own files. A base-only head bump, a new finding, a verdict change and a new round never touch it. Link it from the review file's metadata block.

## Preparing a fix

Findings stay in `projects/<repo>/reviews/<slug>/<n>-<sha>/`; the work on them lives in `projects/<repo>/changes/<slug>/`. Link each tree to the other and never repeat what the other states. A change with no review behind it carries the same files minus the review links. The change directory carries:

- **`README.md`**: the single entry point, linking every other artifact: what is broken, what the fix does, status, the create-PR link, what is in the directory, the link to the review.
- **`plan.md`**: written first, before any fix code, terse per `skills/writing-style.md`. Contains: the scope rule admitting a change; a table of what is in, one row per finding with its effect on the failing signal; what is out, with the decision each excluded item needs; the verification table, one row per CI job with real command and result; checks beyond the jobs; an Iterations section naming every round and what caught it, failures included.
- **`pr-body.md`**: per `skills/pr-body.md`.
- **`issue.md`**: only when no upstream issue covers the problem, per `skills/issue.md`.
- **`checkout/`**: a submodule pinned to the branch: `git submodule add -b <branch> <fork-url> projects/<repo>/changes/<slug>/checkout`. Required whenever the fix is presented. Keep a worktree at `.worktrees/<repo>-<slug>/` as scratch, out of version control. Never write a fix into the reviewed checkout in place; restore it to its default branch.

Present a change only when every `plan.md` item is done and verified. `./scripts/post-fix.sh` opens the issue and PR from the drafts, gated on the literal word `post`.

`comment_<model>.md` stays the postable artifact: every finding's `## <path>:<line>` section stays in it, fixed-on-branch and deliberately-left-out alike, each closing with a line saying which. Never replace sections with a pointer to the review file.

### Run the CI locally

Reproduce every job the diff touches, loop until green before pushing.

- Take the command from the workflow file, never the Makefile or README, and match it exactly. Read what each script runs: a `check` target may be formatting only.
- Report a job that cannot run locally as not run, never as passing. Name the missing dependency and the closest real substitute.
- When a change makes a linter cover new files, prove it walks them: introduce a violation, see it reported, remove it. When a suppression comment moves, prove it still suppresses: delete it, see the error, restore it.
- For a behavior-preserving refactor of a pure function, ship an equivalence proof over a large input set.

### Self-review

Before pushing, read the final diff as a reviewer who did not write it, with the same *Verification discipline* and severity model. Fix what it finds and record it in the plan's Iterations section. Never silently amend it away.

## Links & citations

Shared by the review file and comment.md.

- A private reviewed repo does not strip links from `comment_<model>.md`; the no-blob-link rule covers artifacts living outside the reviewed repo. Strip links from the review file when a delta file says so, never from the comment.
- Every `file:line` reference is a link to a blob on the branch under review: `` [`file:line`](https://github.com/<head-owner>/<repo>/blob/<head-branch>/<path>#L<line>) ``, ranges `#L<a>-L<b>`. Take both from `gh pr view <n> --json headRefName,headRepositoryOwner`: a fork's branch is not a ref in the upstream repo, so the upstream form 404s on every cross-fork pull request. This covers every reference, including files and tests cited by name. Never a bare backticked `file:line`.
- Link the branch, not the sha. Re-verify anchors each round: lines move under a branch link. Pin a sha in exactly two cases: the branch is merged and deleted, or the claim is about code that has since changed and the point is what it said then.
- Link every behavioral claim to the line that proves it, not only claims naming a symbol.
- A blob link into a rendered file such as `.md` needs `?plain=1` before the `#L` anchor.
- Anchor a supporting link on words already in the prose; a named doc subsection links to its header line.
- A link must prove the exact clause it anchors. Read the cited lines and confirm the number, symbol, or behavior appears in the range. One claim per anchor: two numbers, two links. For a pinned tag, fetch the file at that tag.
- Attribute a behavior to what guarantees it: a toolchain detail cites the toolchain, never a spec that does not require it. When the spec guarantees less than observed, say so.

## Repro rules

Shared by `**Repro:**` blocks in the review file and comment.md. A repro is the runnable sequence demonstrating a claimed behavior.

- Every empirical claim ships a copy-pasteable repro: fenced `bash`, self-contained, one clear pass/fail signal, restoring modified files at the end. Pin env vars only when depended on.
- **No repro for a merge conflict.** State what the resolution costs and stop; the conflict itself is not the finding.
- **No repro for a finding the reader confirms by looking at the app.** Drive the app yourself to confirm the claim, keep the script in the review file as the record, and let the finding sentence carry the steps.
- **A clip replaces the written steps, and only the user can attach it.** When a clip exists, the sentence drops the steps and states the rule the clip demonstrates. An image hosted in a private workspace will not render on someone else's pull request: hand the file to the user to drop into the comment box, and never post a link that renders as a broken image.
- Start with `# from a local clone of <repo>:`, then the checkout command. Zero local paths, no trailing `git checkout <hash>` pin. Inline needed files with heredocs; never `curl`, never reference into the reviews tree. Clean up at the end.
- Follow the block with the observed output in a second fenced block, trimmed to the signal-bearing 5-20 lines, `# …` marking omissions.
- A repro whose output is a failure says so in one line directly above that output, naming what failed and why the failure is the finding.
- A repro demonstrates behavior. Source inspection and greps are not repros. Drop any repro whose only output is a passing run.
- A fixture's header comment is three or four lines: what it asserts, the measurement, and that it fails at the reviewed head. The mechanism belongs in the finding. Keep a measured table; cut the prose around it.
- Write the repro in the harness the repo already uses for that surface, found by reading the test the diff itself adds. A defect on a surface the project covers with an integration fixture belongs in that fixture format, not a unit test poking an internal function. Copy the neighbouring fixture's structure, naming and assertions.
- Size the fixture against the threshold it asserts. A repro claiming a bound is exceeded must exceed it: check the input against the real constant.
- A measured number is committed with the artifact that produced it, in the round directory, before the number is written down anywhere. A number whose repro is gone: delete it or re-measure it, never carry it forward.
- Run the repro from the draft, verbatim: extract the block from the file and execute it. Every number in the prose comes from that run's output, pasted, never from an earlier run, a rounder figure, or memory.
- Heredoc behavioral tests, asserting the post-fix state, fail now and pass fixed, for Critical and Warning only. Nits and Suggestions cite the anchor; a one-line "confirmed behaviorally: X" note is enough.

## Output

One block per target, this exact format:

```markdown
# <repo> [#<number>](https://github.com/<repo>/pull/<number>): <title>

URL: https://github.com/<repo>/pull/<number>
Author: <author> | Base: <base> | Files: <count> | +<add> -<del>
Reviewed by: <GitHub username> | Model: <model used> | Commit: <short-sha> (<status>)
Local checkout: `<the command that reproduces this state>`
Overview: [overview](../overview.md) <— only when the review directory has one>

<Round note. Re-review and same-commit deep rounds only.>

## Overview
<Always include. For a reader who knows the project but nothing of this work: what the change does, the problem it solves, how the pieces fit. 3-6 plain-language sentences, no jargon, no findings, no decision. Add an ASCII diagram only when the work cannot be understood without one, such as a call chain crossing files, a state machine, or a trust boundary, with the changed edge marked; drawing rules per the Diagrams section of `skills/pr-body.md`. Default is no diagram.>

**Verdict: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION / CLOSE** — <one terse sentence: decision plus open concerns by name> (<finding counts, nonzero bands only>). `CLOSE` only when the change should not land at all; cite the load-bearing reason in the same sentence.

## Verify first
<Always include. One to three lines, highest stake first: the places a human must check before merging. Each line a linked `file:line`, then one clause naming the property and the concrete way to confirm it. Load-bearing code, not findings. "run X and check Y", never "review carefully".>

## Summary
<2-4 dense sentences: the bug/feature, why it matters with anchor numbers, one-sentence shape of the fix.>

## Examples
<Optional. Input-to-outcome rows making a semantics change tangible. No findings, no `file:line`, no decision. Skip for refactors, plumbing, bugfixes with no user-visible surface.>

## Fix
<2-4 sentences prose: before-state, after-state, the load-bearing constraint. No code blocks. Link `file:Lstart-Lend` inline. Skip if purely additive or trivial.>

## Benchmarks / Numbers
<Table for N values / before-after / percentages. No prose explaining the table. Anchor naked numbers to a known budget.>

## Critical (must fix)
- **[<priority tag, plain-English>]** `file:line` — <one-line TL;DR>
  <details><summary>details</summary>

  <2-4 sentences prose, then a final sentence starting "Fix:". Labeled sub-bullets only for a concrete repro; plain prose otherwise.>
  </details>

## Warnings (should fix)
<Same shape. If another reviewer already raised a finding, attribute in the TL;DR before the tag.>

## Nits
- **[<priority tag, plain-English>]** `file:line` — <one-line TL;DR>
  <Omit the tag and `<details>` for a trivial nit with no distinct risk.>

## Missing Tests
- **[<priority tag>]** `file:line` — <one-line TL;DR of the missing scenario>
  <details><summary>details</summary>

  <Why the gap matters, the edge case, then the ready-to-add test that closes it; write and link the `tests/` artifact.>
  </details>

## Suggestions
<Same shape, rationale in the details.>

## Verified
<Optional; standard in deep mode and live-boot targets. One bullet per runtime check CI does not show: the claim, then the evidence, linked. Never "tests pass". A final bullet may list the tests run green at the reviewed sha.>

## Not fixable by a pull request
<Repository-level reviews only. One line per condition no diff can clear: what it is, the permission or action it needs, who holds it.>

## Existing threads
<Only when the target carries unresolved reviewer threads. One line each: reviewer, gist, state, overlap with own findings, link.>

## Open questions
<Optional. Thoughts the reviewer should see but not posted: deferred-scope follow-ups, extensions, design musings. One terse line each, ending with why it wasn't posted.>
```

### Format rules

- `<status>` is `latest` when `<short-sha>` matches the current head, or `stale — +N commits since`.
- A subject with no PR drops the PR-only metadata lines, URL, Author and Base, and titles the H1 by the subject; anchors per *Subjects*.
- `Overview`, `Verify first`, and `Not fixable by a pull request` never reach comment.md.
- Every finding line gets a plain-English priority tag in every severity section; only a trivial nit drops it.
- Prose in `<details>` by default; labeled sub-bullets only for tangible repros.
- No Test Results section: a review-worthy failure becomes a Critical or Warning; other results get no mention.
- Never cite an absolute value for a constant the base branch recalibrates; quote the merge base or say the author must re-derive it.
- Cite `file:line` for every claim, linked per *Links & citations*. A finding living outside the tree, a service setting or a dashboard, names the place precisely; never borrow a nearby file as a stand-in anchor.
- No bare `#<number>` in any text GitHub renders inside the workspace repo: the review H1, a commit subject. It autolinks to the workspace repo. Link it, `[#<number>](<pr-url>)`, or drop the `#`.
- No GitHub checkboxes unless the author must tick items.
- Over 10 files: end the Summary with a dependency-first reading order.

### Calibration

- No target finding count. Stop when the diff is read in full and the blast radius is mapped: callers, dependents, siblings.
- State only what CI does not show, per `skills/writing-style.md`; never "tests pass", "lint clean", "build green".
- A defect a CI job catches is never a comment, at any severity. Name the job that fails on it and drop the finding, because the author reads the red job before they read the review. What survives names the reason no job reaches it.
- Severity is binary. Warning = a maintainer could plausibly block: correctness, security, decay, missing invariant. Nit = style, polish, optional. In doubt: Nit.
- The verdict answers to the severities, and a surviving Warning rules out APPROVE. Reconcile before shipping: either the finding is a Nit and the band was wrong, or the verdict is COMMENT. COMMENT when the change improves strictly on its base and the Warning is a defect it did not introduce; REQUEST CHANGES when the branch causes the Warning or ships it to users. Either way the verdict line names the Warning and says why it does or does not block.
- Severity measures whether the defect is real, not how big. A small genuine correctness bug is a Warning; magnitude goes in the details. Suggestion is for non-bugs: latent-only risks, design tradeoffs.
- A cosmetic nit no enabled linter enforces stays in the review file with the config link and "not posted, no change needed". Check the linter config before flagging a style convention.
- A pre-existing defect is in scope in exactly two cases: the diff sweeps that defect's class and missed it, or the change makes the code permanent. Name the sweep or the freeze, and say it predates the diff. Check both by reading the diff, never from recall: a diff that promotes something to a security boundary, or adds a test asserting the behaviour, is the first case and the verdict moves with it.
- Map the full call graph before claiming anything dead, redundant, or unused.
- Clearing something needs the same evidence as flagging it. To clear "X is safe because guard G covers it": find G's construction site, list its callers, and confirm X is one. Never infer that a guard reaches a member from a grouping made by the diff, its docs, or its author. A cleared item whose mechanism was not traced is unverified; say so.
- When the finding is a missed member of a class, measure the whole class in one harness and publish the table.
- Never flag contribution-policy compliance as a code finding; mention it in the narrative only when it is why CI is red.
- Post a deferred-scope or extension question only when there is a concrete risk or a decision the author must make now; otherwise Open questions.

### Rules

- One file per review: `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/review_<model>_<reviewer>.md`. `<slug>`: for a PR, `<number>-<3-4 words from the title>`, lowercase, hyphenated; otherwise a name for the subject. `<n>`: the round number, from the existing directories. `<model>`: lowercase, hyphenated. `<reviewer>`: `gh api user --jq '.login'`. Hash = reviewed head. Same commit and mode share a directory; a deep round over a reviewed commit gets `<n+1>-<same-sha>`.
- On the first review for a repo, create `projects/<repo>/reviews/README.md` with the repo's GitHub link and one line.
- Every finding: a standalone one-line TL;DR with priority tag, plus `<details>`. The TL;DR plus the details' final "Fix:" sentence is the canonical finding text; comment.md copies it verbatim, so write it to work as a PR inline comment as-is.
- Minimal bold. The file must render in GitHub-flavored markdown: blank line after `<summary>`, continuation indented 2 spaces under list items, `<details>` nested at most one level.
- Delete empty sections' headings. Never write "None". Never fabricate findings.
- Priority order: correctness > security > determinism > state safety > tests > docs > style.
- Over 20 files: summarize by area first, then deep-dive the critical paths.
- Draft `comment_<model>.md` before committing; one final push covers both, to this repo only. The push is pre-authorized for this skill and overrides any global ask-before-push rule.
- Fold late findings into both files, verify each with a real run, commit and push in the same turn without asking. Posting still waits for `post`.
- Never push to a reviewed repo's canonical remote; a fix branch goes to the fork.
- Reviews may be published, with one exception: a finding exploitable against already-merged or deployed code is a security disclosure. Check the repo's `SECURITY.md`, keep it out of any public tree, and raise the disclosure decision with the user before writing anything. A finding on an open PR's own diff is fine at any severity.

## GitHub review draft (`comment_<model>.md`)

Draft in the same directory, same `<model>`. The user prunes by hand: `SKIP` prefixed to a header, `## SKIP <path>:<line>`, drops the comment. Never delete a dropped comment; the marker survives regeneration.

A target with no PR, a branch or a repository-level failure, gets a GitHub issue draft in the same filename: `Target:` and `Event: ISSUE` in place of the PR header, then `## Title`, `## Body`, and the anchored `## <path>:<line>` sections posting as plain headers inside the body. Each section still runs 1-3 sentences and closes with fixed-on-branch or left-out and why. Post with `gh issue create -R <repo> --title ... --body-file ...` under the same `post` gate.

Before writing a `Full review:` link into anything posted, check this repo's visibility with `gh repo view <this-repo> --json visibility`. Private: carry no link, inline the substance instead.

Auto-SKIP duplicates: when another reviewer already raised a finding, prefix its header with `SKIP` while drafting, attribute the reviewer in the review file, and make `Already raised: <comment-url>` the section's first body line. When a section bundles an already-raised finding with a novel one, split it so the novel part posts. Where the raised finding is one case of a broader one being posted, name that case in the broader sentence and link it to the original instead of splitting.

Format:

```markdown
# Review: [#<number>](https://github.com/<repo>/pull/<number>)
Event: APPROVE | REQUEST_CHANGES | COMMENT

## Body
<One-line assessment, then one-sentence bullets for unanchored findings only. When clean: "Looks good." plus one CI-invisible check, and nothing else.>

Full review: <link to the review file in this repo>

## <path>:<line>
<1-3 sentences: the problem and why it matters>

<details><summary>repro</summary>

<fenced bash repro block + fenced observed-output block>
</details>
```

### Body rules

- A finding with more than one case is a claim and a list, never a paragraph. One line for the claim and its mechanism, then one nested bullet per case naming its condition and outcome. Put the cases where it does not bite beside the ones where it does.
- The Body has exactly two jobs: cross-cutting synthesis the per-line comments cannot carry, and unanchored findings, one sentence each, gap then fix. Cut everything else. One line is the size; a paragraph there is a finding that should have been anchored.
- **Never write a Body line whose only job is to fill the field**: no line that counts the inline comments or points at them. Anchor what is about code; the Body carries what is about the branch and survives the two rules below, which take a stale base, a rebase and a conflict out of it.
- **An empty Body is refused at submit and accepted on edit.** The submit call rejects an empty string for REQUEST_CHANGES and COMMENT; a later edit of the same review sets it to empty and holds. A review whose every finding is anchored ships with its shortest true sentence and is cleared afterwards.
- **Draft the smallest postable set first, then add on request.** Open with the one finding that changes what the author does next, and hold every other finding in the review file.
- **Name the event beside the draft, never after it.** The review file's verdict is the reviewer's judgement and does not move. What gets posted, APPROVE, COMMENT or REQUEST_CHANGES, is the user's call: show it with the text and let one word settle both.
- Never mention an anchored finding in the Body, in any form: no bullets, no recap, no pointer to it, no count.
- Do not re-describe the change, list what passed, narrate the review process, or restate thread state.
- Stateless, like every inline comment: never name a round, never frame current code as a fix relative to a prior draft. State the code's current property, not its history.
- A CI-invisible check must pass the verification rule in `skills/writing-style.md`; one that fails never appears. Nothing runtime-only checked: no verification line at all.
- At most three checks, the strongest. State each as an action and its result, never as a characterization. When naming a revert, describe the concrete edit and tie cause to effect in one chain.
- When a Body check asserts a property a committed test could assert, write the test instead.
- **No sha pin in anything posted.** The reviewed sha belongs in the review file's metadata.

### General rules

- `Event:` defaults from the verdict: APPROVE → APPROVE, REQUEST CHANGES → REQUEST_CHANGES, NEEDS DISCUSSION and CLOSE → COMMENT. It is a default, not a lock: the user may post a lighter event than the verdict, and then the review file keeps the verdict while the draft records what went out. The `Event:` line carries it; the Body never restates it.
- An own-PR target is not posted at all. If the user insists, `Event: COMMENT` whatever the verdict: GitHub rejects APPROVE and REQUEST_CHANGES on one's own PR.
- Order inline sections: Critical, Warning, Missing test, Nit, Suggestion; file order within a band.
- Post only comments that change what the author does: fix, decide, or answer. "No change needed" findings stay in the review file. Severity never gates this: a Nit asking for a concrete modification gets its own section.
- Never explain routine fixes: merge the base, regenerate assets, re-run a flaky job. A red check with a routine cause gets one short Body line, naming what is no longer readable rather than the fix.
- **Never tell the author to rebase.** They meet the conflict the moment they try to merge, and a reviewer spending the body on it says nothing the branch does not already say. What a rebase costs, a behaviour it drops or a build it breaks, is a finding anchored on the line that carries it. Nothing else about the base branch reaches the comment. One exception: when the stale base is why the review is not an APPROVE, the Body says so in one line, because a withheld approval whose reason is unstated is the same defect in the other direction.

### Building each inline comment

1. **Anchor.** One `## <path>:<line>` section per finding, every severity; ranges `## <path>:<start>-<end>`. Line numbers reference the head commit, side RIGHT. Read those exact lines first; the anchor covers exactly the lines the sentence talks about. Validate every anchor against the diff hunks now, not at posting time: a line outside the diff is rejected and takes the whole review with it, so that finding belongs in the Body and the draft must say so.
2. **Opener.** `Critical:` / `Nit:` / `Suggestion:` prefix matching the review file's band, then the TL;DR. A Warning gets NO prefix. A missing-test finding opens `Missing test:` plus the uncovered scenario. No bracketed priority tags in comment.md.
3. **Sentences.** One visible sentence, two only when the second carries an action the first does not; code blocks and `<details>` do not count; no headers, no bold. Order: gap and stake, evidence, fix sentence last. Over one: cut evidence, never the gap. What ships is the defect, the anchor and the repro: the reasoning, the prototyping cost and the verification pins stay in the review file.
4. **Fix sentence.** Default none, per `skills/writing-style.md`. Add only when the remedy is non-obvious and changes what the author would do; name the outcome, never the implementation path.
5. **Links.** Every named file or test, every behavioral claim, per *Links & citations*.
6. **Repro.** Critical and Warning get a collapsed repro block when the claim is behavioral.

### Visible-text style

Governed by the *Posted comments* section of `skills/writing-style.md`: state the fix or the defect in the fewest words, cut every clause the fix already implies, no process words. The rules below are the review-specific additions.

- Essentials only: the problem and why it matters. No stacked clauses, no symbol-chain walkthroughs, no scenario-painting.
- Do not re-prove the claim in visible text; mechanism and secondary evidence go in the repro block or the full review.
- Lead with the specific gap. Never open by explaining the author's own code or restating what the change claims.
- A latent-risk finding states the current safety in one clause and stops.
- Lowercase a source's emphasis caps in prose; caps survive only in code spans.
- **Never post a question.** State the position as the reviewer's own, in one line. This covers design and layering calls.
- Link the full review inside an inline comment only when the details block is not enough.

### Repros (comment.md deltas)

- Attempt a repro for every Critical and Warning before drafting. No run proof: word it as an observation, never "I ran X". Source-visible facts: cite the anchor, drop the block.
- A repro lives in exactly one file: comment.md owns it for findings anchored there; the review file states the result and links it. Line-specific repros stay with their comment; suite-wide ones go in a Body `<details>` block, pointed to. A finding the reader confirms in the app, and a merge conflict, ship none: the run that confirmed them stays in the review file.
- A missing-test finding carries ready-to-add cases in a collapsed `<details><summary>test cases</summary>` block, in the file's own test style, paste-ready.

### Rounds & regeneration

- Update comment.md whenever the review changes; it never lags.
- Port carried findings verbatim; change only shas, repro URLs, and stale anchors. No round-relative phrasing.
- A SKIPped finding stays SKIPped when ported, with a one-line note, until the user un-SKIPs it. Before regenerating, read the existing file and preserve every surviving `SKIP` marker.
- When the head advanced past the reviewed commit: diff `<reviewed-sha>..<head>`, drop findings that diff fixed, re-run remaining repros on the new head, re-verify every anchor.

### Posting

- Never without the literal word `post` or `upload` in the current turn; `push` covers git push only. The same gate covers mutating already-posted content: update the draft, show the exact new text, touch GitHub only after approval.
- A `gh` write refused 403 `Resource not accessible by personal access token` is a missing scope: never retry or work around. Record the refused command in the artifact's `Status:` line and end the reply with `post <github url of the artifact>` alone on its own line.
- The word `post` covers every verdict, APPROVE included: post an approving review on the same word as any other, with no extra confirmation. A post still always needs the word; never auto-post.
- Post every verdict as a PR review, never a plain issue comment: `gh api repos/<repo>/pulls/<number>/reviews -f event=<EVENT> -f body='...'`, inline comments as `comments[]` entries with `path`, `line`, `side=RIGHT`, `body`. Validate every anchor against the PR diff first: one rejected anchor takes the whole review with it; move those findings into the Body.
- An unsubmitted review the author already has on the target swallows a new one: the comments land in that pending review instead of posting. Check for one before posting and fold the draft into it, or submit it first.
- Thumbs-up acknowledged duplicates in the same `post`, from each SKIPped section's `Already raised:` URL. Inline thread: `gh api -X POST repos/<repo>/pulls/comments/<id>/reactions -f content=+1`; top-level: `.../issues/comments/<id>/reactions`. Skip targets already reacted to.
- After a successful post, write the URLs back: `Posted: <review-url>` under the title, `[posted](<comment-url>)` on each anchor. Commit and push in the same turn as the post, never later: the `Posted:` line is what makes a re-post rewrite the existing review instead of adding a second one. Before any post, check whether the target already carries a review from this author and reconcile the draft first.

### Final check

Verify each line before handing over:

1. The Full review line points at this repo and resolves.
2. The Body names at most three checks, each runtime-only, none CI-visible, none recapping anchored findings.
3. No repro block has a passing run as its only output.
4. Every non-Warning inline comment opens with its band; Warnings open with the TL;DR. Every comment asks for a fix, a decision, or an answer, and carries no fix sentence its problem statement already implies.
5. Count, do not judge: one visible sentence per section, one line or nothing in the Body, one section per distinct action. Count the `<details>` blocks too, and delete the one attached to a merge conflict or to anything the author confirms by opening the app.
6. No verdict restating the `Event:` line, no bold, no imported emphasis caps, every `skills/writing-style.md` rule holds.
7. Open every link and read the lines it lands on: each must contain the number, symbol, or behavior claimed, and every external link must resolve at the pinned ref.

Then two QA agents, re-run on every regeneration of comment.md:

- **Concision recheck**: one `Agent`, `subagent_type: general-purpose`, given the comment.md path, the checkout path, and the *Visible-text style* rules. Only question: can any line be shorter or clearer without dropping fact, stake, or fix? Apply the rewrites that hold against the cited lines.
- **Citation audit**: one `Agent`, `subagent_type: general-purpose`, given both file paths and the checkout. For every link it fetches the target and returns only anchors whose lines do not contain the claim, plus unresolvable external links. It skips the `Full review:` self-link, which 404s until pushed. Fix each returned finding.

## Authoring this file

- Only directives, imperative, plus the definitions a reader needs to apply them. No justifications, no war-stories.
- A prompt delegating to this skill points at it, never restates the steps.
- When a rule proves unclear, missing, or wrong during use, update it in the same turn. Cross-target conventions belong here; one-off specifics do not.
