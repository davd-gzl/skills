---
name: review-output
description: The exact shape of the review file: its metadata block, every section in order, and the rules for filling each. Read when writing the review file, per skills/review.md.
---

# Review output

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


## Format rules

- `<status>` is `latest` when `<short-sha>` matches the current head, or `stale — +N commits since`.
- A subject with no PR drops the PR-only metadata lines, URL, Author and Base, and titles the H1 by the subject; anchors per *Subjects* in `skills/review.md`.
- `Overview`, `Verify first`, and `Not fixable by a pull request` never reach comment.md.
- Every finding line gets a plain-English priority tag in every severity section; only a trivial nit drops it.
- Prose in `<details>` by default; labeled sub-bullets only for tangible repros.
- No Test Results section: a review-worthy failure becomes a Critical or Warning; other results get no mention.
- Never cite an absolute value for a constant the base branch recalibrates; quote the merge base or say the author must re-derive it.
- Cite `file:line` for every claim, linked per *Links & citations* in `skills/review.md`. A finding living outside the tree, a service setting or a dashboard, names the place precisely; never borrow a nearby file as a stand-in anchor.
- No bare `#<number>` in any text GitHub renders inside the workspace repo: the review H1, a commit subject. It autolinks to the workspace repo. Link it, `[#<number>](<pr-url>)`, or drop the `#`.
- No GitHub checkboxes unless the author must tick items.
- Over 10 files: end the Summary with a dependency-first reading order.

