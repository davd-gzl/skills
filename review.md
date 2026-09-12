---
name: review
description: Adversarial review of a pull request, a branch, or a repository-level failure in any project. One workflow, finders, one verifier per candidate, a critic, a writer, a text pass, producing overview.md, the GitHub draft per skills/review-comment.md and claims.md. Multi-target dispatch and a reviewer-authored target are in skills/review-modes.md.
argument-hint: <repo>#<pr-number> | <url> | <repo> <subject>
---

# Review

**Input:** `$ARGUMENTS`: a PR number or URL, a repo name plus a subject, or several of these. Process each target independently.

Write all visible prose per `skills/writing-style.md`; its scannability rule covers every artifact here. In every artifact, verdict first, then narrative, then findings. Make every reference clickable, every file readable without the chat, and bold the one number or word that carries the decision.

## Workflow

One shape for every target, whatever its size: the parent prepares, a workflow
finds, verifies, criticises and writes, the parent checks and ships. Run from
the workspace root; multi-target runs wrap this via *Parallel dispatch* in
`skills/review-modes.md`.

1. *Fetch & understand*: sync the checkout; the head and merge-base worktrees; a copy of head with comment lines blanked, `./scripts/blank-comments.py <head worktree> <scratch>/head-nocomments`, line numbers kept; the toolchain line every shell opens with; the round directory; the catalog; prior rounds; and each stage's model and effort from the workspace's `scripts/workflows/review-pipeline.json`.
2. Run the *Re-review rounds* gate when a prior round exists.
3. *Reproduce the failure*: the check runs at the head, each suite once per tree state, and the project's tool built once from the head worktree onto the toolchain line, named in `args.prebuilt`, so no verifier builds it.
4. Print the plan first, `./scripts/review-plan.py`, with `--preset` when the word was `quick review` or `deep review`, and paste its table and projection in the reply that launches the run, so what is about to run and cost is on screen before it does. Then run the workflow, the workspace's `scripts/workflows/review-pipeline.js` by `scriptPath`, with those as `args`, the preset as `args.preset`; a preset moves knobs, and `quick` drops the critic and the text pass, so its round ends on the writer and step 5 is its only pass over the text. Each stage is an agent reading only the rule sections its artifact needs:
   - **Finders**, one angle each, read only: line by line; removed and rewritten behaviour with the sweep by shape; the claims the diff writes about itself; the tests the diff adds with the mutation that must redden each; reachability and extremes; the refactor pass with the depth question; the catalog walk. Each reads the code before the description, since a description calling something safe lowers what a reader finds, and five of them read the blanked copy; the claims angle reads the description and the comments first, its subject, and the refactor angle reads head. Each returns candidates with the check that would prove it false, half-believed ones included, capped per the config and merged per line. An angle the diff holds no material for is skipped, `./scripts/review-plan.py --diff <head worktree> <base> <head>` printing which and writing the measurement the workflow reads: tests needs a test file, claims a comment, a doc or a decision record, removed a deleted line, refactor an added block; lines, reach and the catalog always run.
   - **One verifier per line**, from scratch, in a scratch worktree it creates and removes itself, `git -C <head worktree> worktree add --detach <scratch>/verify-<n> <sha>`, so parallel mutations never share a tree. It runs the check, on the merge base too when the claim is causal, and returns CONFIRMED, PLAUSIBLE or REFUTED with its artifact under `tests/`. That is the big candidate: a Warning, a mutation, a causal comparison. A small one, a grep-shaped check, a refactor's test run, a Nit or a Suggestion, shares one agent and one worktree with the other small ones on its file, up to the config's count, at the cheaper tier it names, the tree restored between claims; one that turns out to need a mutation comes back PLAUSIBLE with the check named, never a guess. Every verifier carries a tool-call budget and returns PLAUSIBLE with the check still to run when it runs out, since the slowest verifier holds every stage behind it, and a built binary sits on its PATH so none builds one.
   - **One critic**, reading every candidate beside the first verify wave: what is missing, an angle that came back thin, a shape nobody ran, a changed test not re-added, a cap hit silently. Its candidates verify in that wave, so no second wave waits on the slowest verifier.
   - **The writer**: `overview.md` per *Overview* when the directory has none, `comment_<model>.md` per `skills/review-comment.md` with every finding as a section, posted or `SKIP`, and `claims.md` per *Output*, its candidate rows written by the workflow from the verdicts, the writer adding the verdict line and the completeness answers. A PLAUSIBLE finding is a question.
   - **The text pass**, last, per the QA rule in `skills/review-comment.md`.
   The verify stage is the claim gate; no second gate runs. A harness with no workflow runner runs the same stages serially in one agent, same prompts, and the round note says so.
5. Run the *Final check* of `skills/review-comment.md`, then the `skills/writing-style.md` Pass over `overview.md` and the draft, `./scripts/prose-check.py <file>` first. Re-run it after any later edit to that prose, including an edit made in answer to a question about it. State which passes ran when handing over.
6. One commit and one push covering everything. This push is pre-authorized; see *Rules*.
7. Retro, before the handover: run `./scripts/review-retro.py <workflow-dir>` and write `## Retro` at the end of `claims.md`, three parts from that table and the run's notifications, never from memory: what failed, an agent that died, a cap hit, an escalation, an angle whose candidates were mostly refuted, minutes over the plan; what worked, an angle whose candidates held, a batch that verified clean; one upgrade to the workflow with its estimate per *A change to the run's shape* in `skills/authoring.md`, written the same turn as a line of the workspace's `TODO.md`, where `upgrade skills` picks it up. The handover repeats the retro in three lines.
8. Hand over. Name the cost first, agents, minutes and tokens per stage from the task notifications. Link the draft and the overview. Add a "Decisions needed" list, one line each: a borderline verdict, a PLAUSIBLE worth a decision. Omit when empty. Never list an APPROVE as needing confirmation. Post only on the literal word `post`. Acting on the findings is `skills/change.md`; they stay here.

## Subjects

The subject is a PR by default. Two others recur; they change only *Fetch & understand* and the anchors, the `file:line` a finding attaches to:

- **Branch or working diff**: no PR yet. Anchor findings to `file:line` at the branch head.
- **Repository-level failure**: red CI on the default branch, a failing gate, a broken release. The "diff" is the failing surface. Enumerate every failing condition from its authoritative source, attribute each to the code or config causing it, and separate what a PR can fix from what only a maintainer with project permissions can. `<slug>` names the failure, not a commit.

Both live in `projects/<repo>/reviews/<slug>/`.

## Modes

Two cases change part of this workflow: multi-target parallel dispatch, and a
target the reviewer authored. Both are in `skills/review-modes.md`, read when
the trigger fires.

## For each target

### Fetch & understand

- Sync the checkout per *Sync a checkout* in `skills/git.md`: `git remote -v`, fetch every remote, compare `git rev-list --left-right --count HEAD...<remote>/<branch>`. The canonical remote is often `upstream`.
- Never review from a dirty tree without saying so. Never write into the reviewed checkout outside a dedicated fix branch.
- **Review from a worktree, never from the checkout itself.** A checkout tracked as a submodule sits on whatever detached HEAD the last update left, so a grep, a lint run or a test suite there answers about code nobody is reviewing. `git worktree add <scratch>/<repo>-review-<target> <canonical-remote>/<default-branch>`, check the target out inside it, and run every command of the review there.
- **A branch from outside the project gets a static danger pass before it is fetched into a local checkout**, nothing executed. Read the raw diff for: changes to the build and dependency surface, the CI workflows, the lockfile, the manifest, container files and any shell script; calls that execute, reach the network, read credentials or the environment, or write the filesystem; encoded or generated code; and Trojan Source, meaning non-ASCII added lines, bidirectional overrides, zero-width characters and homoglyphs. Say in the review what the pass covered and what it found, and carry anything not malicious but risky into the findings. `author_association` of `NONE` or `FIRST_TIME_CONTRIBUTOR` is the trigger, from `gh api repos/<repo>/pulls/<n> --jq '.author_association'`; `gh pr list --json` has no such field.
- **A worktree that already exists is reused, never cleaned.** `worktree add` fails on an existing path: re-run only the checkout. It may carry uncommitted edits from another session, so never stash, clean or revert; report them and work around them.
- For a PR: `gh pr view <number> -R <repo> --json title,body,author,baseRefName,headRefName,files,additions,deletions,commits` and `gh pr diff <number> -R <repo>`.
- **A finding the description already names is one sentence at most, and often none.** The author wrote it down on purpose, so restating it back at them spends the review's attention on the one thing they cannot learn from it. What is left worth saying is the consequence they may not have pictured, and a clip says that better than a paragraph.
- Read the description, linked issues, all comments via `gh api repos/<repo>/issues/<number>/comments`, and all review comments via `gh api repos/<repo>/pulls/<number>/comments`. Note unresolved threads. Paginate every list call with `gh api --paginate`: truncation at 30 items is silent.
- Read past reviews in `projects/<repo>/reviews/` first; focus on what changed since the last reviewed commit.
- Read `projects/<repo>/CONTEXT.md` before the target and take the round's pace from it, which outranks the plan's projection: a launch weeks away means a lower finder cap and more targets, a quiet stretch the full cap and a second round. An author's stated wants shape the draft, and a finding class they asked not to receive ships `SKIP`.
- A target nobody has reviewed on the forge yet is unsafe until a round has read it: it gets the static danger pass whatever its author's association.
- Read every changed file in full, and map callers, dependents, and siblings.
- **A project with no invariant catalog gets one proposed before its first round starts**, built from the repository's own bug history, its past reviews and the classes its domain is known for, one class per entry with the check that settles it; the round waits for the user's word on the draft, since a finder walking no catalog walks nothing.
- A CONFIRMED finding whose class the catalog lacks adds that class to the catalog in the same round, with the check that found it, so the next round's finders walk it.

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
- **Differ**: full re-review round, focused on what changed since `<old-sha>`. A file the head adds gets first-round depth, whatever round it lands in.
- **New head is a merge of the base branch**: never base-only. Run `git show <new-sha> --cc`; any hunk it prints is conflict-resolution content, reviewed like any diff. Base commits may add tests the branch now fails: run the affected suite on the new head.
- **`<old-sha>` unreachable**: skip the gate, run a full round against the merge-base, note the fallback.

Open every full re-review round with a `Round:` line in the draft's header: `Round <n>.`, how the head moved, what changed, which prior findings and `SKIP` sections were resolved or carried.

### Reproduce the failure

- `gh pr checks <number> -R <repo>` first, plus the check-runs API. Note every failure.
- Run the project's own test and lint commands, taken from its CI workflow file, never guessed. Match the invocation exactly, pinned versions included.
- Record pass or fail per affected package or job.
- **Run each suite and each linter once per tree state, into a file under `<scratch>`, and read that file for every later count, grep or exit code of the same state.** Re-running that state costs the run again and shows nothing new. *Repro rules* still paste that run's output, which the file holds.
- **Where the harness cannot select one fixture, run a probe in a copy of the package pruned to that fixture, never in the worktree**, with the copy recipe in the project's delta.
- Before attributing any failure to the diff, run the same check on the merge-base. A failure that also occurs there is pre-existing.
- **Run the project's own tool from the branch's source, never an installed binary.** An installed binary exercises the code it was built from, not the branch's, so a change to the tool tests itself out of the run.
- A repository-level failure gets the same discipline: reproduce each condition on the default branch and identify the introducing commit where history allows.
- When a target changes runtime behavior of a server or tool, boot it and exercise it live; record what was verified live as rows in `claims.md`.

### Review the diff

Read every line. Look for correctness defects: logic errors, missing nil checks, unchecked type assertions, off-by-one. Untested paths. Breaking changes without migration. Style inconsistencies. Reuse and simplification: duplicated helpers, foldable code, unclear naming, missing doc comments, undocumented invariants, filed as Suggestions or Nits, never blockers. Docs impact.

**Refactor pass, over every added block.** Ask whether fewer lines carry the same behaviour: a value computed twice, a guard the caller already applied, memoization that stabilises nothing, an abstraction with one call site. Where they do, post the replacement as a `Refactor:` suggestion the author applies in one click, never prose describing the change, and record both line counts in `claims.md`.

**Ask whether each fix sits at the right depth.** A special case added to shared code for one caller, a new root or flag where the cause could be removed, a guard at the call site while the callee stays unsafe for its next caller: each is a Suggestion naming the deeper form and what the shallow one costs to maintain.

**Inline a local read once that exists only to fit the line width**, and let the
formatter wrap the expression instead. A name is a claim that something is worth
naming, so one repeating the expression beside it promises several uses where
there is one, and the reader looks for the others.

**A silent fallback where a human has to decide is a finding.** Code that cannot
satisfy a rule and quietly returns the old value leaves nobody told: the state
that needs a person belongs in the return, a flag beside it or an error, and the
surface that person reads has to carry it. The same pass covers a lookup into a
fixed list, `list.index(value)` and friends, which raises on a value the list
lost and takes every read of that record down with it.

**Check every claim the diff writes about itself before clearing the code it
decorates.** A godoc, a comment, a test header, the description and a decision
record name symbols, counts, tests and shapes they call safe: grep each symbol,
count each number, run each test the prose says catches something, and run each
shape the prose calls bounded or harmless. A claim that fails anchors a finding
on the code or the comment, per *Calibration*.

**Make every test the diff adds go red before crediting it.** Revert the fix,
swap the configuration the test claims to pin, and plant a sentinel panic in a
body a comment says runs. A test still green after that pins nothing: it is a
Warning on the test, and the claim it decorated stays unverified.

**Sweep again, by shape, any class the diff removes or rewrites one member
of.** Grep the package for the return type, the signature, the sentence or the
pattern that member had, never its name: the sibling that was missed carries a different name and
the same shape, and it is in scope per *Calibration*.

**Feed a path the diff makes reachable for the first time its extremes.** When a
setter, a decoder or a write path starts working, send the type's maximum, zero,
empty and a foreign unit through it and follow each to the reader that consumes
it; what the validators leave unnamed is what arrives.

**Verification discipline.** Every finding passes all of these before it enters the review:

- Verify against the actual file, never from memory or a summary.
- **A finding or Open question carried from an earlier round is re-verified before it ships**, to the same standard as a new one. It arrived with a conclusion and no run attached, and the round that wrote it may have stopped one call short of the code that settles it. Follow the path to its end: the handler that queues the work, the store that debounces it, the default the framework already applies.
- **Browser behaviour needs a browser, and headless is not one.** Anything the browser itself does rather than the page, exiting fullscreen on Escape, a shortcut, a permission prompt, is absent from a headless run and a null result there proves nothing. Run it headful on a virtual display, `xvfb-run -a`, before writing that it cannot be measured.
- Back every behavioral claim with an actual run, at every severity. Never assert stdlib or runtime behavior from memory.
- **Enumerate the case space before writing the finding.** Two sets that must agree give four cells: both, first only, second only, neither. The neither cell is usually the live one.
- **Report what the user loses, never the artifact that causes it.** A conflict, a deleted file, a moved import and a missing guard are mechanical facts; name the action that stops working, for whom, and where. Test it by reading the line cold as a maintainer, deciding in one pass whether to care.
- **When the base has moved, build the merged state and run it.** Apply the base's version of the disputed hunk into the running branch, exercise the path, then revert.
- **A synthetic event is not a run, for anything a user drives with a mouse or keyboard.** A dispatched event skips the focus moves, default actions and library handlers a real input goes through, so it passes where the real input fails. Drive the real app with real input; a synthetic event is only a probe for which listener fired.
- For any claim that the diff *causes* a behavior, run the repro on the merge-base too. Reproduces there: pre-existing, causation false; attribute only the delta and state both numbers.
- When a baseline run or a test kills a finding, drop the finding. Never keep the conclusion and attach a new rationale.
- Treat every "bound" or "leak" claim as quantitative: name the quantity, vary what claims to bound it, confirm they track.
- **Two files carrying the same line are not the same file.** A claim that deployed or released code shares a defect names the revision it was read at, or says the line matched and the revision was not compared. "Identical" over a grep hit is the failure, because the surrounding code that decides reachability was never looked at.
- A reachability claim is proved by construction, never by survey. Build the smallest artifact that would fail if the claim were false and run it, from outside the boundary the claim is about: never a test that builds its own victim, never a grep for existing instances.
- Vary the conditions before naming them. A finding that holds under one shape and not another states which, having tried both.
- When a second condition, tried once, changes no verdict, stop varying it: run the remaining cases under the first alone, and give the artifact one line naming what the try ruled out, never the doubled table.
- Run greps and lint in the reviewed checkout at the reviewed commit.
- **Sweep for callers or consumers over the whole tree, never the diff's own directory.** The consumer a change breaks sits where the diff was not looking, an integration fixture beside a package's own tests for one.
- Confirm a symbol exists with the project's own linter or compiler, sanity-checked first with a bogus symbol.

**Static-analysis findings** are leads, not findings. Before one enters the review: read the flagged lines and state the concrete failure in the project's own terms, never a rule ID plus stock message. Separate real defects from unadopted policies; only the defect may be a Warning or above. Say what the fix costs; a behavior-change fix is a maintainer decision, say so. Never report a count as a finding: group by rule, name one representative, give the full list once.

### Write tests for test-shaped findings

When findings suggest fragile or under-tested code, write edge-case tests, run them, report the failures. Save to `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/tests/`.

When a finding's fix is a test the author should add, ship the test: write it under `tests/`, assert the post-fix state, never the bug's current output, run it, and when it also proves a bug show it failing before the fix and passing after. Embed it in the comment.md finding so the author can paste it in.

Pair the defect with the baseline it breaks in one assertion, and ship both expectations side by side, the current one active and the fixed one commented, each labelled. The pair shows in one screen what the code does and what it should do, and the commented line is what the author uncomments once the fix lands.

Start each test file with a comment block carrying exact repro commands runnable from a plain clone: no workspace paths, no `$HOME`. Pin `git checkout <hash>` in test-file headers only; a draft's repro blocks never pin. The header stands alone, shaped per *Repro rules*. Name code paths by their actual symbol. One-line in-test comments per non-obvious step.

## Overview (`overview.md`)

Write one for every target, the writer's first artifact. The findings are written for a reader who already knows the subject; the overview is the only artifact that assumes nothing, and it is what the user opens first, the draft second. A judgement call about complexity was the rule before this one, and it answered "skip" for subjects a reader could not follow.

- Write it as `overview.md`, never `overview.html`: GitHub serves an `.html` blob as source, so the reader downloads the file to read it.
- **Every code block, diagram and table says whether it is the before or the after.** A reader who cannot tell which side they are looking at reads the defect as the fix. Put it in the prose introducing the block or in the block's own caption, never leave it to be inferred from the surrounding argument.
- It goes at the review directory root, `projects/<repo>/reviews/<slug>/overview.md`, never inside a round directory: it explains the subject, not one commit.
- Explainer only, carrying no review state: no verdict, no findings, no reviewed sha, no round. Name the generating model once, under the title.
- Use anything GitHub renders: a `mermaid` diagram, a `$$` formula, a decision table, before and after values, a `> [!NOTE]`, a `<details>` fold, a committed image, a Concepts section. No emoji, and nothing needing a script or a click, which the blob page strips.
- Where a page would have used a simulator, compute the interesting inputs and put the results in a table. The reader gets the answer without moving a slider, and every number is checkable from the file.
- Run the mirrored logic before publishing its numbers, against the project's own tests where they exist and against the mirrored source where they do not, and say which of the two it was.
- Update it only when new commits change the subject's own files. A base-only head bump, a new finding, a verdict change and a new round never touch it. Link it from the draft's `Overview:` line.

## Links & citations

Shared by the draft, `claims.md` and `overview.md`.

- A private reviewed repo does not strip links from `comment_<model>.md`; the no-blob-link rule covers artifacts living outside the reviewed repo. Strip links from `claims.md` and `overview.md` when a delta file says so, never from the draft.
- Every `file:line` reference is a link to a blob at the reviewed sha: `` [`file:line`](https://github.com/<head-owner>/<repo>/blob/<sha>/<path>#L<line>) ``, ranges `#L<a>-L<b>`. Take the owner from `gh pr view <n> --json headRepositoryOwner`: a fork's commits live in the fork, so the upstream form can 404 on a cross-fork pull request. This covers every reference, including files and tests cited by name. Never a bare backticked `file:line`.
- Pin the reviewed sha, never the branch: the link shows the code the finding was written against whatever the branch does next, and a new round cuts its anchors at its own sha.
- A blob link into a rendered file such as `.md` needs `?plain=1` before the `#L` anchor.
- A link must prove the exact clause it anchors. Read the cited lines and confirm the number, symbol, or behavior appears in the range. One claim per anchor: two numbers, two links. For a pinned tag, fetch the file at that tag.
- Attribute a behavior to what guarantees it: a toolchain detail cites the toolchain, never a spec that does not require it. When the spec guarantees less than observed, say so.
- A bare sha autolinks only in the repository holding that commit. Prose in `comment_<model>.md` writes the reviewed repo's shas bare, for the hovercard; `claims.md` keeps its own shas as they are, since the reviewed repo's sha resolves to nothing in the workspace repo.

## Repro rules

Shared by the repro blocks of the draft and `claims.md`. A repro is the runnable sequence demonstrating a claimed behavior.

Settle where the repro goes before writing one. A finding on a surface the reader reaches in a browser ships no harness in the comment, whatever the rules below say: the author opens the page instead of cloning, installing a test runner and writing a config by heredoc. Post the clip, or the steps in the sentence, and keep the harness in `claims.md`, the claim that is a number included, which goes in the sentence with what it was counted over.

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
- **Film every finding whose symptom shows on screen, in the round that finds it, unasked.** Ship the clip beside the finding in both artifacts, captured per the picture rule in `skills/writing-style.md`. Where the browser cannot reach the screen, name what stood in for it.

## Output

A round directory, `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/`,
holds three things, and the overview sits beside it at the slug root:

- `comment_<model>.md`, the draft, per `skills/review-comment.md`: every finding as a section, posted or `SKIP`, with its repro; its header carries the model and effort, the reviewed sha, the overview link and the round note.
- `claims.md`, the record. A `Verdict:` line first, APPROVE, REQUEST CHANGES, NEEDS DISCUSSION or CLOSE with one terse sentence naming the open concerns. Then one row per candidate the verifiers ran: state, band, `file:line`, the check, the observed output, the artifact under `tests/`. A refuted candidate keeps its row with the proving line, so a later round reads what was cleared and why. Then the text pass's link table, and the completeness answers.
- `tests/`, every artifact a verifier ran, per *Write tests*.

When a posted round's target merges or closes, `./scripts/review-outcomes.py <draft> --write` adds an Outcomes table to `claims.md`: per posted finding, fixed, resolved or open, and whether the author replied. That table is what a change to a tier, a cap or a batch is measured against.

### Calibration

- No target finding count. Stop when the diff is read in full and the blast radius is mapped: callers, dependents, siblings.
- State only what CI does not show, per `skills/writing-style.md`; never "tests pass", "lint clean", "build green".
- A defect a CI job catches is never a comment, at any severity. Name the job that fails on it and drop the finding, because the author reads the red job before they read the review. What survives names the reason no job reaches it.
- Severity is binary. Warning = a maintainer could plausibly block: correctness, security, decay, missing invariant. Nit = style, polish, optional. In doubt: Nit.
- The verdict answers to the severities, and a surviving Warning rules out APPROVE. Reconcile before shipping: either the finding is a Nit and the band was wrong, or the verdict is COMMENT. COMMENT when the change improves strictly on its base and the Warning is a defect it did not introduce; REQUEST CHANGES when the branch causes the Warning or ships it to users. Either way the verdict line names the Warning and says why it does or does not block.
- Severity measures whether the defect is real, not how big. A small genuine correctness bug is a Warning; magnitude goes in the details. Suggestion is for non-bugs: latent-only risks, design tradeoffs.
- **Weigh the recovery before the band, and read the finding's own limits paragraph as the reader will.** A reproduction proves the defect is reachable and says nothing about what it costs. Where the write-up already says the state is recoverable, the attack unrepeatable, or the loss one more ordinary transaction, that paragraph has set the band and it is low: a defect whose worst case is doing the same thing again is a Nit, however cleanly it reproduces. The tell is a finding arguing its own severity down in its second half while its first half claims the opposite.
- **A published vector decodes itself, and the score line is what opens it.** The severity line goes in the `<summary>`, so it reads as it always did and expands to one row per metric: the code beside the metric's name, its rating, then what that metric means for this finding, never boilerplate. The score is then stated once, not in a metadata row as well. No link: a reader cannot get this from `AV:N`, and an advisory that needs a third party to be readable has taken a dependency for nothing.
- **Score the vector from what the attack requires, and never move a base metric once a band has been named.** Editing `UI`, `PR` or `AV` in the turn someone asks for a different severity is scoring backwards, whatever reason the edit carries. Deployment context has its own metrics: raise `IR`, `CR` or `AR`, publish the environmental score beside the base one, and the higher band is computed rather than asserted.
- **A finding about an ADR's own text is a Nit, whatever it concerns.** An ADR records a decision and ships no behaviour, so an omission in one costs a paragraph and never a defect: the permanence it fails to state, the alternative it skips, the filename it keeps. Its claims about the code are run like a comment's, per *Review the diff*, and one that fails is a finding on the code with the ADR as the evidence.
- A cosmetic nit no enabled linter enforces carries the config link and ships `SKIP`, per `skills/review-comment.md`. Check the linter config before flagging a style convention.
- A finding about a code comment's own wording ships `SKIP`, whatever band it lands in: it changes no behaviour, so it does not earn an inline slot by default. Keep the measurement that shows the comment wrong in `claims.md`.
- A pre-existing defect is in scope in three cases: the diff sweeps that defect's class and missed it, the change makes the code permanent, or the change makes the defect reachable for the first time. Name the sweep, the freeze or the new path, and say it predates the diff. Read the diff, never recall: promoting something to a security boundary, or adding a test asserting the behaviour, is the first case, and the verdict moves with it.
- A pre-existing defect found while reviewing, in scope or not, goes the same turn to an issue draft per `skills/issue.md`, or to the project's audit tracking where its delta names one, under the disclosure invariant when the code is deployed. A row in `claims.md` is where such a finding dies.
- Map the full call graph before claiming anything dead, redundant, or unused.
- Code that cannot run is a finding, never a reason to drop one: an impossible guard, an unreachable branch, a default the type forbids. **Ask for its removal, and name every site the removal touches**, the symbol it declares included. A rename, a reworded message or a tidied comment keeps the code and ships as polish on protection that is not there, so a wording finding inside proven-dead code is that same finding, one band down.
- Clearing something needs the same evidence as flagging it. To clear "X is safe because guard G covers it": find G's construction site, list its callers, and confirm X is one. Never infer that a guard reaches a member from a grouping made by the diff, its docs, or its author. A cleared item whose mechanism was not traced is unverified; say so.
- A suspected defect leaves the review only through a run showing it guarded, with the proving line quoted. Without that run it is a Warning, never an Open question.
- When the finding is a missed member of a class, measure the whole class in one harness and publish the table.
- Never flag contribution-policy compliance as a code finding; mention it in the narrative only when it is why CI is red.
- Never critique the project's own governing document, meaning its wording, the symbols it names or the claims it makes, and never reference it to editorialize. Where the code is wrong the finding is about the code, and where a code or test comment repeats a claim the document has outrun, the finding anchors on that comment.
- Post a deferred-scope or extension question only when there is a concrete risk or a decision the author must make now; otherwise a `SKIP` section in the draft closing with the question.

### Rules

- One directory per round, per *Output*. `<slug>`: for a PR, `<number>-<3-4 words from the title>`, lowercase, hyphenated; otherwise a name for the subject. `<n>`: the round number, from the existing directories. `<model>` in the draft's name: lowercase, hyphenated. Hash = reviewed head. A second round over a reviewed commit gets `<n+1>-<same-sha>`.
- On the first review for a repo, create `projects/<repo>/reviews/README.md` with the repo's GitHub link and one line.
- Minimal bold. Every file renders in GitHub-flavored markdown: blank line after `<summary>`, continuation indented 2 spaces under list items, `<details>` nested at most one level.
- Delete empty sections' headings. Never write "None". Never fabricate findings.
- Priority order: correctness > security > determinism > state safety > tests > docs > style.
- A diff spanning several packages or directories is summarized by area first, then its critical paths in depth.
- One final push covers the round, to this repo only. The push is pre-authorized for this skill and overrides any global ask-before-push rule.
- Fold a late finding into the draft and `claims.md`, verify it with a real run, commit and push in the same turn without asking. Posting still waits for `post`.
- Never push to a reviewed repo's canonical remote; a fix branch goes to the fork.
- Reviews may be published. A finding exploitable against already-merged or deployed code is not: it takes the disclosure gate in the workspace `AGENTS.md` Invariants before anything is written. A finding on an open PR's own diff is fine at any severity.

## GitHub review draft (`comment_<model>.md`)

The writer's artifact, step 4 of the workflow. The draft, its body rules, the shape of each inline
comment, the final check and the posting gate are in `skills/review-comment.md`.
Draft it whether or not anything will be posted.
