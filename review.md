---
name: review
description: Adversarial review of a pull request, a branch, or a repository-level failure in any project. Writes a severity-grouped review file plus a comment_<model>.md GitHub draft, posted only after user approval. Supports multi-target parallel dispatch and a deep multi-angle mode.
argument-hint: <repo>#<pr-number> | <url> | <repo> <subject>
---

# Review

**Input:** `$ARGUMENTS` — a PR number or URL, a repo name plus a subject ("meet, the CI is red"), or several of these. Process each target independently.

Write all visible prose per `skills/writing-style.md`, no exceptions; its scannability rule covers every artifact here. In every artifact: verdict first, then narrative, then findings. Make every reference clickable, every file readable without the chat, and bold the one number or word that carries the decision.

## Workflow

Run in order for a single target; multi-target runs wrap this via *Parallel dispatch*. Run from the workspace root.

1. *Fetch & understand* — sync the checkout, gather target data, read prior reviews.
2. Run the *Re-review rounds* gate when a prior round exists.
3. *Reproduce the failure* — or run the tests, for a PR.
4. *Review the diff*, or the failing surface.
5. *Write tests* for test-shaped findings.
6. Write the review file (*Output*).
7. Draft `comment_<model>.md` (*GitHub review draft*), then run its *Final check* and QA agents. Skip for a PR the reviewer authored; see *Own PR*.
8. The `skills/writing-style.md` Pass over every line of the review file and `comment_<model>.md`. First priority, never skipped, whatever the findings are worth. Re-run it after any later edit to that prose, including one made in response to a question about it. State which passes ran when handing over.
9. One commit and one push covering everything. This push is pre-authorized; see *Rules*.
10. Hand over. Link the `comment_<model>.md` draft, not only the review file. Add a "Decisions needed" list — borderline verdict, APPROVE confirmation, Open questions worth promoting — one line each; omit when empty. Post only on the literal word `post`.

## Subjects

The subject is a PR by default. Two others recur; they change only *Fetch & understand* and the anchors (the `file:line` a finding attaches to):

- **Branch or working diff** — no PR yet. Anchor findings to `file:line` at the branch head.
- **Repository-level failure** — red CI on the default branch, a failing gate, a broken release. The "diff" is the failing surface. Enumerate every failing condition from its authoritative source, attribute each to the code or config causing it, and separate what a PR can fix from what only a maintainer with project permissions can. `<slug>` names the failure (`ci-red-main`), not a commit.

Both live in `projects/<repo>/reviews/<slug>/`.

## Modes

### Parallel dispatch (multi-target)

Use when `$ARGUMENTS` contains more than one target.

1. The parent prepares each checkout first (per *Fetch & understand*). Subagents never create worktrees or check out branches.
2. Dispatch one Agent per target, all in one message (`subagent_type: general-purpose`):

> Run the review workflow at `skills/review.md` on `<target>` (URL: `<url>`). Read `skills/writing-style.md` before drafting any prose; every line of the review file and `comment_<model>.md` conforms to it. The checkout already exists at `<path>` with the target checked out — never create a worktree or switch branches. Follow every other step in that file. Do not commit, push, or post; the parent does that at the end. Report back the review file path and a one-paragraph summary of the verdict and headline findings.

3. Agents run concurrently, never sequenced.
4. The parent runs the *Final check* and both QA agents over every returned draft, before the commit. A subagent's own pass never stands in for them.
5. After all return, the parent makes a single commit and push covering all reviews.
6. Reconcile before handing over. Two agents reviewing coupled targets can reach opposite conclusions. Re-derive the answer from the source, name the constraint both sides must satisfy, and write the same conclusion into every affected review file. Never ship contradicting drafts, and never settle it by taking one agent's summary.

Building a batch target set ("review all"): every open, non-draft target absent from the review directory, minus bot-authored, `WIP`-titled, reviewer-authored, and already-reviewed ones. The review directory is not the only record: check the forge itself per target and drop on any hit. Confirm the final list with the user before reviewing more than one target, naming what was dropped and why.

### Deep mode (multi-angle, single target)

Trigger: the user asks for a **parallel**, **red-team / blue-team**, or **deeper** review of one target, or "review and loop until perfect". Deep mode runs many lenses on one target; everything else — output format, comment.md, push rules — is the normal flow.

1. **Set up.** Run *Fetch & understand* and *Reproduce the failure* once; hand the same paths to every agent.
2. **Dispatch lens agents**, one message, concurrent (`subagent_type: general-purpose`). Default three lenses; add more for large targets (perf, docs, API surface, ops impact). Each prompt is self-contained: checkout path, target, diff path, prior-review paths, one narrow lens. Each agent returns findings in this skill's severity model with `file:line` citations.
   - **Red team** — bugs, broken invariants, security holes, edge cases, missing validation, downstream footguns.
   - **Blue team** — missing tests, undocumented invariants, hardening gaps, misuse-inviting ergonomics, migration and rollback risk.
   - **Correctness** — does the code match the description and linked issue? Scope drift, silent behavior changes, contract mismatches.
3. **Synthesize.** Dedupe, re-rank by the severity ladder, verify each finding per *Verification discipline*. Never keep a finding on an agent's summary alone.
4. **Critic pass, exactly one round, parallel.** 2-3 critics in one message, each with a distinct lens — verdict-check, missing-blocking, severity-calibration — over the synthesized draft plus the diff and checkout. Each returns ONLY findings that flip the verdict, raise a severity band, or add a missing Critical or Warning; otherwise exactly `NO_MATERIAL_FINDINGS`. Never send an open-ended "what's wrong" prompt. After: dedupe, re-read each cited `file:line`, drop what does not hold, revise. Never loop critics.
5. **Claim-verification gate, parallel.** Before drafting comment.md, one agent extracts every falsifiable claim — behavioral, structural, numeric — and runs a check designed to prove each false. It returns only claims that fail or cannot be verified; re-read those against the code, drop or fix each. Facts only; severity and verdict belong to the critic pass.
6. **Output.** Normal flow. Metadata line: `Model: <model> (<intensity>, deep)`; ask when the intensity is unknown. Deep mode over an already-reviewed commit opens a new `<n+1>-<same-sha>` directory whose round note names the mode and which prior verdict it confirms or overturns.

### Own PR (the reviewer authored it)

Check with `gh pr view <number> --json author`. Findings land as commits on the branch, never as a review to post.

- No `comment_<model>.md`, no `pr-body.md`, post nothing. The review file is still written: it is the record.
- Apply every mechanical fix — comments, docs, tests, naming, dead code — in the checkout the review uses, then *Run the CI locally* until green.
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
- For a PR: `gh pr view <number> -R <repo> --json title,body,author,baseRefName,headRefName,files,additions,deletions,commits` and `gh pr diff <number> -R <repo>`.
- Read the description, all comments (`gh api repos/<repo>/issues/<number>/comments`), all review comments (`gh api repos/<repo>/pulls/<number>/comments`), and linked issues. Note unresolved threads. Paginate every list call with `gh api --paginate`: truncation at 30 items is silent.
- Read past reviews in `projects/<repo>/reviews/` first; focus on what changed since the last reviewed commit.
- Read every changed file in full, and map callers, dependents, and siblings.

Treat CI as a first-class source. `gh run list` shows only GitHub Actions; external checks (SonarCloud, Codecov, deploy bots) are app check runs. Read the authoritative list for the exact commit:

```bash
sha=$(gh api repos/<repo>/commits/<branch> --jq '.sha')
gh api --paginate repos/<repo>/commits/$sha/check-runs --jq '.check_runs[] | "\(.conclusion)\t\(.name)"'
gh api repos/<repo>/commits/$sha/status --jq '.state'
```

Query each failing check's own API for detail, not its GitHub summary blurb; quote the gate's own numbers. When that API refuses (auth, 403): fall back to the check run's `output` fields and label every number as read from the summary, never as gate-verified.

### Re-review rounds (head advanced)

When a prior round exists and the head moved from `<old-sha>` to `<new-sha>`, compare patch-ids (`git patch-id --stable`, a stable hash of a diff's content):

```bash
git fetch <remote> <base-branch>
git diff $(git merge-base <remote>/<base-branch> <old-sha>) <old-sha> | git patch-id --stable
git diff $(git merge-base <remote>/<base-branch> <new-sha>) <new-sha> | git patch-id --stable
```

- **Equal** — base-only move. Do NOT re-author: copy the latest round's `.md` files into `<n+1>-<new-sha>/`, rewrite shas, remap anchors (fixing any that no longer map by reading the checkout), add a one-line round note (head advanced, content unchanged, anchors re-cut, verdict unchanged), commit. Skip the rest of the workflow.
- **Differ** — full re-review round, focused on what changed since `<old-sha>`.
- **New head is a merge of the base branch** — never base-only. Run `git show <new-sha> --cc`; any hunk it prints is conflict-resolution content, reviewed like any diff. Base commits may add tests the branch now fails, so run the affected suite on the new head.
- **`<old-sha>` unreachable** — skip the gate, run a full round against the merge-base, note the fallback.

Open every full re-review round with a round-note paragraph between the metadata block and the TL;DR: `Round <n>.` — how the head moved, what changed, which prior findings were resolved or carried.

### Reproduce the failure

- `gh pr checks <number> -R <repo>` first, plus the check-runs API. Note every failure.
- Run the project's own test and lint commands, taken from its CI workflow file, never guessed. Match the invocation exactly, pinned versions included.
- Record pass or fail per affected package or job.
- Before attributing any failure to the diff, run the same check on the merge-base. A failure that also occurs there is pre-existing.
- A repository-level failure gets the same discipline: reproduce each condition on the default branch and identify the introducing commit where history allows.
- When a target changes runtime behavior of a server or tool, boot it and exercise it live; record what was verified live in the Verified section.

### Review the diff

Read every line. Look for: correctness (logic errors, nil checks, type assertions, off-by-one); untested paths; breaking changes without migration; style inconsistencies; reuse and simplification (duplicated helpers, foldable code, unclear naming, missing doc comments, undocumented invariants) — filed as Suggestions or Nits, never blockers; docs impact.

**Verification discipline.** Every finding passes all of these before it enters the review:

- Verify against the actual file, never from memory or a summary.
- Back every behavioral claim with an actual run, at every severity. Never assert stdlib or runtime behavior from memory.
- For any claim that the diff *causes* a behavior, run the repro on the merge-base too. Reproduces there: pre-existing, causation false; attribute only the delta and state both numbers. A passing repro proves the behavior exists, never that the diff created it.
- When a baseline run or a test kills a finding, drop the finding. Never keep the conclusion and attach a new rationale.
- Treat every "bound" or "leak" claim as quantitative: name the quantity, vary what claims to bound it, confirm they track.
- Run greps and lint in the reviewed checkout at the reviewed commit.
- Confirm a symbol exists with the project's own linter or compiler, sanity-checked first with a bogus symbol.

**Static-analysis findings** are leads, not findings. Before one enters the review: read the flagged lines and state the concrete failure in the project's own terms, never a rule ID plus stock message; separate real defects from unadopted policies (only the defect may be a Warning or above); say what the fix costs — a behavior-change fix is a maintainer decision, say so; never report a count as a finding — group by rule, name one representative, give the full list once.

### Write tests for test-shaped findings

When findings suggest fragile or under-tested code, write edge-case tests, run them, report the failures. Save to `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/tests/`.

When a finding's fix is a test the author should add, ship the test itself: write it under `tests/`, assert the post-fix state (never the bug's current output), run it, and when it also proves a bug show it failing before the fix and passing after. Embed it in the comment.md finding so the author can paste it in.

Start each test file with a comment block carrying exact repro commands runnable from a plain clone — no workspace paths, no `$HOME`. Pin `git checkout <hash>` in test-file headers only; review and comment.md repro blocks never pin. The header stands alone: the run block, then at most 2-3 lines covering mechanism, observed result at the pinned hash, and what changes when fixed. Name code paths by their actual symbol. One-line in-test comments per non-obvious step.

## Preparing a fix

Findings stay in `projects/<repo>/reviews/<slug>/<n>-<sha>/`; the work on them lives in `projects/<repo>/changes/<slug>/`. Link each tree to the other and never repeat what the other states. A change with no review behind it carries the same files minus the review links. The change directory carries:

- **`README.md`** — the single entry point: what is broken, what the fix does, status, the create-PR link, what is in the directory, the link to the review. It links every other artifact.
- **`plan.md`** — written first, before any fix code, terse per `skills/writing-style.md`. Contains: the scope rule admitting a change; a table of what is in, one row per finding, with its effect on the failing signal; what is out, with the decision each excluded item needs; the verification table, one row per CI job, real command and result; checks beyond the jobs; an Iterations section naming every round and what caught it, failures included.
- **`pr-body.md`** — per `skills/pr-body.md`.
- **`issue.md`** — only when no upstream issue covers the problem, per `skills/issue.md`.
- **`checkout/`** — a submodule pinned to the branch: `git submodule add -b <branch> <fork-url> projects/<repo>/changes/<slug>/checkout`. Required whenever the fix is presented. Keep a worktree at `.worktrees/<repo>-<slug>/` as scratch, out of version control. Never write a fix into the reviewed checkout in place: a feature branch there dirties the parent's gitlink. Restore it to its default branch.

Present a change only when every `plan.md` item is done and verified. `./scripts/post-fix.sh` opens the issue and PR from the drafts, gated on the literal word `post`.

`comment_<model>.md` stays the postable artifact: every finding's `## <path>:<line>` section stays in it, fixed-on-branch and deliberately-left-out alike, each section closing with a line saying which. Never replace sections with a pointer to the review file.

### Run the CI locally

Reproduce every job the diff touches, loop until green before pushing.

- Take the command from the workflow file, never the Makefile or README, and match it exactly. Read what each script actually runs: a `check` target may be formatting only.
- Report a job that cannot run locally as not run, never as passing. Name the missing dependency and the closest real substitute.
- When a change makes a linter cover new files, prove it walks them: introduce a violation, see it reported, remove it. When a suppression comment moves, prove it still suppresses: delete it, see the error, restore it.
- For a behavior-preserving refactor of a pure function, ship an equivalence proof over a large input set.

### Self-review

Before pushing, read the final diff as a reviewer who did not write it, with the same *Verification discipline* and severity model. Fix what it finds and record it in the plan's Iterations section. Never silently amend it away.

## Links & citations

Shared by the review file and comment.md.

- Every `file:line` reference is a link to the reviewed repo's blob at the reviewed sha: `` [`file:line`](https://github.com/<repo>/blob/<short-sha>/<path>#L<line>) ``, ranges `#L<a>-L<b>`, `<short-sha>` from the round directory name. Applies to every reference, including files and tests cited by name. Never a bare backticked `file:line`.
- Link every behavioral claim to the line that proves it, not only claims naming a symbol.
- A blob link into a rendered file (`.md`) needs `?plain=1` before the `#L` anchor.
- Anchor a supporting link on words already in the prose; a named doc subsection links to its header line.
- A link must prove the exact clause it anchors. Read the cited lines and confirm the number, symbol, or behavior appears in the range. One claim per anchor: two numbers, two links. For a pinned tag, fetch the file at that tag.
- Attribute a behavior to what guarantees it: a toolchain detail cites the toolchain, never a spec that does not require it. When the spec guarantees less than observed, say so before a maintainer does.

## Repro rules

Shared by `**Repro:**` blocks in the review file and comment.md. A repro is the runnable sequence demonstrating a claimed behavior.

- Every empirical claim ships a copy-pasteable repro: fenced `bash`, self-contained, one clear pass/fail signal, restoring modified files at the end. Pin env vars only when depended on.
- Start with `# from a local clone of <repo>:`, then the checkout command. Zero local paths, no trailing `git checkout <hash>` pin. Inline needed files with heredocs; never `curl`, never reference into the reviews tree. Clean up at the end.
- Follow the block with the observed output in a second fenced block, trimmed to the signal-bearing 5–20 lines, `# …` marking omissions.
- A repro demonstrates behavior. Source inspection and greps are not repros. Drop any repro whose only output is a passing run.
- Heredoc behavioral tests (asserting the post-fix state: fail now, pass fixed) for Critical and Warning only. Nits and Suggestions cite the anchor; a one-line "confirmed behaviorally: X" note is enough.

## Output

One block per target, this exact format:

```markdown
# <repo> [#<number>](https://github.com/<repo>/pull/<number>): <title>

URL: https://github.com/<repo>/pull/<number>
Author: <author> | Base: <base> | Files: <count> | +<add> -<del>
Reviewed by: <GitHub username> | Model: <model used> | Commit: <short-sha> (<status>)
Local checkout: `<the command that reproduces this state>`

<Round note — re-review and same-commit deep rounds only.>

**TL;DR:** <1-2 plain-language sentences for a reader with zero context. No jargon, no findings, no decision. Always include.>

**Verdict: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION / CLOSE** — <one terse sentence: decision plus open concerns by name> (<finding counts, nonzero bands only>). `CLOSE` only when the change should not land at all; cite the load-bearing reason in the same sentence.

## Verify first
<Always include. One to three lines, highest stake first: the places a human must check before merging. Each line a linked `file:line`, then one clause naming the property and the concrete way to confirm it. Load-bearing code, not findings. "run X and check Y", never "review carefully".>

## Summary
<2-4 dense sentences: the bug/feature, why it matters (anchor numbers), one-sentence shape of the fix.>

## Diagram
<When the change is shape-y: a call chain crossing files, a state machine, an ordering change, a trust boundary. Mark the edge the diff changes; drawing rules per the Diagrams section of `skills/pr-body.md`. Skip when one sentence carries the shape.>

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
<Optional. Thoughts the reviewer should see but that are not posted: deferred-scope follow-ups, extensions, design musings. One terse line each, ending with why it wasn't posted.>
```

### Format rules

- `<status>` is `latest` when `<short-sha>` matches the current head, or `stale — +N commits since`.
- A subject with no PR drops the PR-only metadata (URL, Author, Base) and titles the H1 by the subject; anchors per *Subjects*.
- `Verify first`, `Diagram`, and `Not fixable by a pull request` never reach comment.md.
- Every finding line gets a plain-English priority tag in every severity section; only a trivial nit drops it.
- Prose in `<details>` by default; labeled sub-bullets only for tangible repros.
- No Test Results section: a review-worthy failure becomes a Critical or Warning; other results get no mention.
- Never cite an absolute value for a constant the base branch recalibrates; quote the merge base or say the author must re-derive it.
- Cite `file:line` for every claim, linked per *Links & citations*. A finding living outside the tree — a service setting, a dashboard — names the place precisely instead; never borrow a nearby file as a stand-in anchor.
- No bare `#<number>` in any text GitHub renders inside the workspace repo (review H1, commit subject): it autolinks to the workspace repo, the wrong one. Link it (`[#<number>](pr-url)`) or drop the `#`.
- No GitHub checkboxes unless the author must tick items.
- Over 10 files: end the Summary with a dependency-first reading order.

### Calibration

- No target finding count. Stop when the diff is read in full and the blast radius — callers, dependents, siblings — is mapped.
- State only what CI does not show (see `skills/writing-style.md`); never "tests pass", "lint clean", "build green".
- Severity is binary. Warning = a maintainer could plausibly block: correctness, security, decay, missing invariant. Nit = style, polish, optional. In doubt: Nit.
- Severity measures whether the defect is real, not how big. A small genuine correctness bug is a Warning; magnitude goes in the details. Suggestion is for non-bugs: latent-only risks, design tradeoffs.
- A cosmetic nit no enabled linter enforces stays in the review file with the config link and "not posted, no change needed". Check the linter config before flagging a style convention.
- A pre-existing defect is in scope in exactly two cases: the diff is a sweep of that defect's class and missed it, or the change makes the code permanent. Name the sweep or the freeze, and say it predates the diff.
- Map the full call graph before claiming anything dead, redundant, or unused.
- Never flag contribution-policy compliance as a code finding; mention it in the narrative only when it is why CI is red.
- Post a deferred-scope or extension question only when there is a concrete risk or a decision the author must make now; otherwise Open questions.

### Rules

- One file per review: `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/review_<model>_<reviewer>.md`. `<slug>`: for a PR, `<number>-<3-4 words from the title>`, lowercase, hyphenated; otherwise a name for the subject. `<n>`: the round number, from the existing directories. `<model>`: lowercase, hyphenated. `<reviewer>`: `gh api user --jq '.login'`. Hash = reviewed head. Same commit, same mode share a directory; a deep round over a reviewed commit gets `<n+1>-<same-sha>`.
- On the first review for a repo, create `projects/<repo>/reviews/README.md` with the repo's GitHub link and one line.
- Every finding: a standalone one-line TL;DR with priority tag, plus `<details>`. The TL;DR plus the details' final "Fix:" sentence is the canonical finding text; comment.md copies it verbatim, so write it to work as a PR inline comment as-is.
- Minimal bold. The file must render in GitHub-flavored markdown: blank line after `<summary>`, continuation indented 2 spaces under list items, `<details>` nested at most one level.
- Delete empty sections' headings. Never write "None". Never fabricate findings.
- Priority order: correctness > security > determinism > state safety > tests > docs > style.
- Over 20 files: summarize by area first, then deep-dive the critical paths.
- Draft `comment_<model>.md` before committing; one final push covers both, to this repo only. Push is pre-authorized for this skill and overrides any global ask-before-push rule, scoped to this skill.
- Fold late findings into both files, verify each with a real run, commit and push in the same turn without asking. Posting still waits for `post`.
- Never push to a reviewed repo's canonical remote; a fix branch goes to the fork.
- Reviews may be published, with one exception: a finding exploitable against already-merged or deployed code is a security disclosure. Check the repo's `SECURITY.md`, keep it out of any public tree, and raise the disclosure decision with the user before writing anything. A finding on an open PR's own diff is fine at any severity.

## GitHub review draft (`comment_<model>.md`)

Draft in the same directory, same `<model>`. The user prunes by hand: `SKIP ` prefixed to a header (`## SKIP <path>:<line>`) drops the comment. Never delete a dropped comment; the marker survives regeneration.

A target with no PR — a branch, a repository-level failure — gets a GitHub issue draft in the same filename: `Target:` and `Event: ISSUE` in place of the PR header, then `## Title`, `## Body`, and the anchored `## <path>:<line>` sections posting as plain headers inside the body. Each section still runs 1-3 sentences and closes with fixed-on-branch or left-out and why. Post with `gh issue create -R <repo> --title ... --body-file ...` under the same `post` gate.

Before writing a `Full review:` link into anything posted, check this repo's visibility (`gh repo view <this-repo> --json visibility`). Private: carry no link, inline the substance instead.

Auto-SKIP duplicates: when another reviewer already raised a finding, prefix its header with `SKIP` while drafting, attribute the reviewer in the review file, and make `Already raised: <comment-url>` the section's first body line. When a section bundles an already-raised finding with a novel one, split it so the novel part posts.

Format:

```markdown
# Review: [#<number>](https://github.com/<repo>/pull/<number>)
Event: APPROVE | REQUEST_CHANGES | COMMENT

## Body
<One-line assessment folding in the verification pin ("verified on <short-sha>"), then one-sentence bullets for unanchored findings and questions only. When clean: "Looks good. Verified on <short-sha>: <CI-invisible check>." and nothing else.>

Full review: <link to the review file in this repo>

## <path>:<line>
<1-3 sentences: the problem and why it matters>

<details><summary>repro</summary>

<fenced bash repro block + fenced observed-output block>
</details>
```

### Body rules

- The Body has exactly three jobs: cross-cutting synthesis the per-line comments cannot carry; unanchored findings and questions, one sentence each, gap then fix; and the verification pin ("verified on <short-sha>"). Cut everything else.
- Never mention an anchored finding in the Body, in any form: no bullets, no recap, no "(inline)" pointer, no count.
- Do not re-describe the change, list what passed, narrate the review process, or restate thread state.
- Stateless, like every inline comment: never name a round, never frame current code as a fix relative to a prior draft. State the code's current property, not its history.
- A CI-invisible check must pass the verification rule in `skills/writing-style.md`; one that fails never appears. Nothing runtime-only checked: no verification line at all.
- At most three checks, the strongest. State each as an action and its result ("reverting the fix reproduces the bug"), never as a characterization ("a real correctness gain"). When naming a revert, describe the concrete edit, tie cause to effect in one chain.
- When a Body check asserts a property a committed test could assert, write the test instead.
- End with "Repros run at <short-sha>."; when that sha still matches the head, fold the pin into the opening line.

### General rules

- `Event:` from verdict: APPROVE → APPROVE, REQUEST CHANGES → REQUEST_CHANGES, NEEDS DISCUSSION and CLOSE → COMMENT. The `Event:` line carries the verdict; the Body never restates it.
- An own-PR target is not posted at all. If the user insists, `Event: COMMENT` whatever the verdict: GitHub rejects APPROVE and REQUEST_CHANGES on one's own PR.
- Order inline sections: Critical, Warning, Missing test, Nit, Suggestion; file order within a band.
- Post only comments that change what the author does: fix, decide, or answer. "No change needed" findings stay in the review file. Severity never gates this: a Nit asking for a concrete modification gets its own section.
- Never explain routine fixes (merge the base, regenerate assets, re-run a flaky job). A red check with a routine cause gets one short Body line.

### Building each inline comment

1. **Anchor.** One `## <path>:<line>` section per finding, every severity; ranges `## <path>:<start>-<end>`. Line numbers reference the head commit (side RIGHT). Read those exact lines first; the anchor covers exactly the lines the sentence talks about.
2. **Opener.** `Critical:` / `Nit:` / `Suggestion:` prefix matching the review file's band, then the TL;DR. A Warning gets NO prefix. A missing-test finding opens `Missing test:` plus the uncovered scenario. No bracketed priority tags in comment.md.
3. **Sentences.** Hard cap 1-3 visible sentences; code blocks and `<details>` do not count; no headers, no bold. Order: gap and stake, evidence, fix sentence last. Over 3: cut evidence, never the gap.
4. **Fix sentence.** Default none, per `skills/writing-style.md`. Add only when the remedy is non-obvious and changes what the author would do; name the outcome, never the implementation path.
5. **Links.** Every named file or test, every behavioral claim, per *Links & citations*.
6. **Repro.** Critical and Warning get a collapsed repro block when the claim is behavioral.

### Visible-text style

- Essentials only: the problem and why it matters. No stacked clauses, no symbol-chain walkthroughs, no scenario-painting.
- Do not re-prove the claim in visible text; mechanism and secondary evidence go in the repro block or the full review.
- Lead with the specific gap. Never open by explaining the author's own code or restating what the change claims.
- A latent-risk finding states the current safety in one clause and stops.
- Lowercase a source's emphasis caps in prose; caps survive only in code spans.
- Findings as facts ("X hangs forever"), not questions. A genuine question is one terse line, posted only when the answer changes the verdict or the author's next action.
- A design or layering question caps at two sentences: the alternative in one clause, then whether the choice was deliberate.
- Link the full review inside an inline comment only when the details block is not enough.

### Repros (comment.md deltas)

- Attempt a repro for every Critical and Warning before drafting. No run proof: word it as an observation, never "I ran X". Source-visible facts: cite the anchor, drop the block.
- A repro lives in exactly one file: comment.md owns it for findings anchored there; the review file states the result and links it. Line-specific repros stay with their comment; suite-wide ones go in a Body `<details>` block, pointed to.
- A missing-test finding carries ready-to-add cases in a collapsed `<details><summary>test cases</summary>` block, in the file's own test style, paste-ready.

### Rounds & regeneration

- Update comment.md whenever the review changes; it never lags.
- Port carried findings verbatim; change only shas, repro URLs, and stale anchors. No round-relative phrasing.
- A SKIPped finding stays SKIPped when ported, with a one-line note, until the user un-SKIPs it. Before regenerating, read the existing file and preserve every surviving `SKIP` marker.
- When the head advanced past the reviewed commit: diff `<reviewed-sha>..<head>`, drop findings that diff fixed, re-run remaining repros on the new head, re-verify every anchor.

### Posting

- Never without the literal word `post` (or `upload`) in the current turn; `push` covers git push only. The same gate covers mutating already-posted content: update the draft, show the exact new text, touch GitHub only after approval.
- A `gh` write refused 403 `Resource not accessible by personal access token` is a missing scope: never retry or work around. Record the refused command in the artifact's `Status:` line and end the reply with `post <github url of the artifact>` alone on its own line.
- APPROVE is a human decision: state the verdict and wait for confirmation. A generic "post it" covers REQUEST_CHANGES and COMMENT only.
- Post every verdict as a PR review, never a plain issue comment: `gh api repos/<repo>/pulls/<number>/reviews -f event=<EVENT> -f body='...'`, inline comments as `comments[]` entries with `path`, `line`, `side=RIGHT`, `body`. Validate every anchor against the PR diff first: one rejected anchor takes the whole review with it; move those findings into the Body.
- Thumbs-up acknowledged duplicates in the same `post`, from each SKIPped section's `Already raised:` URL. Inline thread: `gh api -X POST repos/<repo>/pulls/comments/<id>/reactions -f content=+1`; top-level: `.../issues/comments/<id>/reactions`. Skip targets already reacted to.
- After a successful post, write the URLs back (`Posted: <review-url>` under the title, `[posted](<comment-url>)` on each anchor), commit and push.

### Final check

Verify each line before handing over:

1. The Full review line points at this repo and resolves.
2. The Body names at most three checks, each runtime-only, none CI-visible, none recapping anchored findings.
3. No repro block has a passing run as its only output.
4. Every non-Warning inline comment opens with its band; Warnings open with the TL;DR. Every comment is at most 3 sentences, asks for a fix, a decision, or an answer, and carries no fix sentence its problem statement already implies.
5. No verdict restating the `Event:` line, no bold, no imported emphasis caps, every `skills/writing-style.md` rule holds.
6. Open every link and read the lines it lands on: each must contain the number, symbol, or behavior claimed, and every external link must resolve at the pinned ref.

Then two QA agents, re-run on every regeneration of comment.md:

- **Concision recheck** — one `Agent` (`subagent_type: general-purpose`) with the comment.md path, the checkout path, and the *Visible-text style* rules. Only question: can any line be shorter or clearer without dropping fact, stake, or fix? Apply the rewrites that hold against the cited lines.
- **Citation audit** — one `Agent` (`subagent_type: general-purpose`) with both file paths and the checkout. For every link, it fetches the target and returns only anchors whose lines do not contain the claim, plus unresolvable external links. It skips the `Full review:` self-link, which 404s until pushed. Fix each returned finding.

## Authoring this file

- Only directives, imperative, plus the definitions a reader needs to apply them. No justifications, no war-stories.
- A prompt delegating to this skill points at it, never restates the steps.
- When a rule proves unclear, missing, or wrong during use, update it in the same turn. Cross-target conventions belong here; one-off specifics do not.
