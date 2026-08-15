---
name: review
description: Adversarial review of a pull request, a branch, or a repository-level failure in any project. Writes a severity-grouped review file, then the GitHub draft per skills/review-comment.md. Modes for multi-target and deep passes are in skills/review-modes.md.
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
7. Draft `comment_<model>.md` per `skills/review-comment.md`, then run its *Final check*. Draft whether or not anything will be posted. Skip only for a PR the reviewer authored; see *Own PR* in `skills/review-modes.md`.
8. Run the `skills/writing-style.md` Pass over every line of the review file and `comment_<model>.md`, starting with `./scripts/prose-check.py <file>`. Never skip it. Re-run it after any later edit to that prose, including an edit made in answer to a question about it. State which passes ran when handing over.
9. One commit and one push covering everything. This push is pre-authorized; see *Rules*.
10. Hand over. Link the `comment_<model>.md` draft, not only the review file. Add a "Decisions needed" list, one line each: a borderline verdict, Open questions worth promoting. Omit when empty. Never list an APPROVE as needing confirmation. Post only on the literal word `post`.

## Subjects

The subject is a PR by default. Two others recur; they change only *Fetch & understand* and the anchors, the `file:line` a finding attaches to:

- **Branch or working diff**: no PR yet. Anchor findings to `file:line` at the branch head.
- **Repository-level failure**: red CI on the default branch, a failing gate, a broken release. The "diff" is the failing surface. Enumerate every failing condition from its authoritative source, attribute each to the code or config causing it, and separate what a PR can fix from what only a maintainer with project permissions can. `<slug>` names the failure, not a commit.

Both live in `projects/<repo>/reviews/<slug>/`.

## Modes

Four modes change part of this workflow: multi-target parallel dispatch, deep
multi-angle, bot review, and a target the reviewer authored. Each is in
`skills/review-modes.md`, read when its trigger fires.

## For each target

### Fetch & understand

- Sync the checkout per the *Sync first* rule in `AGENTS.md`: `git remote -v`, fetch every remote, compare `git rev-list --left-right --count HEAD...<remote>/<branch>`. The canonical remote is often `upstream`.
- Never review from a dirty tree without saying so. Never write into the reviewed checkout outside a dedicated fix branch.
- **Review from a worktree, never from the checkout itself.** A checkout tracked as a submodule sits on whatever detached HEAD the last update left, so a grep, a lint run or a test suite there answers about code nobody is reviewing. `git worktree add <scratchpad>/<repo>-review-<target> <canonical-remote>/<default-branch>`, check the target out inside it, and run every command of the review there.
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
- **Run the project's own tool from the branch's source, never an installed binary.** An installed binary exercises the code it was built from, not the branch's, so a change to the tool tests itself out of the run.
- A repository-level failure gets the same discipline: reproduce each condition on the default branch and identify the introducing commit where history allows.
- When a target changes runtime behavior of a server or tool, boot it and exercise it live; record what was verified live in the Verified section.

### Review the diff

Read every line. Look for correctness defects: logic errors, missing nil checks, unchecked type assertions, off-by-one. Untested paths. Breaking changes without migration. Style inconsistencies. Reuse and simplification: duplicated helpers, foldable code, unclear naming, missing doc comments, undocumented invariants, filed as Suggestions or Nits, never blockers. Docs impact.

**Refactor pass, over every added block.** Ask whether fewer lines carry the same behaviour: a value computed twice, a guard the caller already applied, memoization that stabilises nothing, an abstraction with one call site. Where they do, post the replacement as a `Refactor:` suggestion the author applies in one click, never prose describing the change, and record both line counts in the review file.

**Verification discipline.** Every finding passes all of these before it enters the review:

- Verify against the actual file, never from memory or a summary.
- **A finding carried from an earlier round is re-verified before it ships**, to the same standard as a new one. It arrived with a conclusion and no run attached, and the round that wrote it may have stopped one call short of the code that settles it. Follow the path to its end: the handler that queues the work, the store that debounces it, the default the framework already applies.
- **Browser behaviour needs a browser, and headless is not one.** Anything the browser itself does rather than the page, exiting fullscreen on Escape, a shortcut, a permission prompt, is absent from a headless run and a null result there proves nothing. Run it headful on a virtual display, `xvfb-run -a`, before writing that it cannot be measured.
- Back every behavioral claim with an actual run, at every severity. Never assert stdlib or runtime behavior from memory.
- **Enumerate the case space before writing the finding.** Two sets that must agree give four cells: both, first only, second only, neither. The neither cell is usually the live one.
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

Findings stay in `projects/<repo>/reviews/<slug>/<n>-<sha>/`; the work on them lives in `projects/<repo>/changes/<slug>/`, whose files and the shape of each are in `skills/plan.md`. Write the plan before any fix code, and present a change only when every `plan.md` item is done and verified. `./scripts/post-fix.sh` opens the issue and PR from the drafts, gated on the literal word `post`.

A "review loop" means fixing every finding, then looping until nothing is left: apply each, re-run the checks, review again, and stop when a full pass adds nothing. Never hand a finding back as a suggestion, and never park one as an open question to keep the report tidy. What survives unapplied needs a decision only the user can make, and each is named as a decision rather than a leftover.

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
- A blob link into a rendered file such as `.md` needs `?plain=1` before the `#L` anchor.
- A link must prove the exact clause it anchors. Read the cited lines and confirm the number, symbol, or behavior appears in the range. One claim per anchor: two numbers, two links. For a pinned tag, fetch the file at that tag.
- Attribute a behavior to what guarantees it: a toolchain detail cites the toolchain, never a spec that does not require it. When the spec guarantees less than observed, say so.
- A bare sha autolinks only in the repository holding that commit. Prose in `comment_<model>.md` writes the reviewed repo's shas bare, for the hovercard; the review file keeps its own shas as they are, since the reviewed repo's sha resolves to nothing in the workspace repo.

## Repro rules

Shared by `**Repro:**` blocks in the review file and comment.md. A repro is the runnable sequence demonstrating a claimed behavior.

Settle where the repro goes before writing one. A finding on a surface the reader reaches in a browser ships no harness in the comment, whatever the rules below say: the author opens the page instead of cloning, installing a test runner and writing a config by heredoc. Post the clip, or the steps in the sentence, and keep the harness in the review file, the claim that is a number included, which goes in the sentence with what it was counted over.

- Every empirical claim ships a copy-pasteable repro: fenced `bash`, self-contained, one clear pass/fail signal, restoring modified files at the end. Pin env vars only when depended on.
- **No repro for a merge conflict.** State what the resolution costs and stop; the conflict itself is not the finding.
- Start with `# from a local clone of <repo>:`, then the checkout command. Zero local paths, no trailing `git checkout <hash>` pin. Inline needed files with heredocs; never `curl`, never reference into the reviews tree. Clean up at the end.
- Follow the block with the observed output in a second fenced block, trimmed to the signal-bearing 5-20 lines, `# …` marking omissions.
- A repro whose output is a failure says so in one line directly above that output, naming what failed and why the failure is the finding.
- A repro demonstrates behavior. Source inspection and greps are not repros.
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
- Never critique the project's own governing document, meaning its wording, the symbols it names or the claims it makes, and never reference it to editorialize. Where the code is wrong the finding is about the code, and where a code or test comment repeats a claim the document has outrun, the finding anchors on that comment.
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
- Reviews may be published. A finding exploitable against already-merged or deployed code is not: it takes the disclosure gate in `skills/security-advisory.md` before anything is written. A finding on an open PR's own diff is fine at any severity.

## GitHub review draft (`comment_<model>.md`)

Step 7 of the workflow. The draft, its body rules, the shape of each inline
comment, the final check and the posting gate are in `skills/review-comment.md`.
Draft it whether or not anything will be posted.

## Authoring this file

- Only directives, imperative, plus the definitions a reader needs to apply them. No justifications, no war-stories.
- A prompt delegating to this skill points at it, never restates the steps.
- When a rule proves unclear, missing, or wrong during use, update it in the same turn. Cross-target conventions belong here; one-off specifics do not.
