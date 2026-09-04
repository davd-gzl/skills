---
name: pr-body
description: Write the title and body of a pull request. Use whenever a change is being proposed, before opening the PR. Produces pr-body.md in the change directory, and loops on it until it passes the checks below.
---

# PR body

Write for a reader with no context who must decide whether to merge. Prose follows `skills/writing-style.md`; the rules below are the PR-body deltas.

Pick one of four shapes, by what the pull request carries. Read the matching model PR before drafting. Never mix them.

- **A docs change.** No headers, no section per correction, no word count to hit. The reader reads the pages themselves, so the body never restates what they now say: name what was wrong, name what it costs, and stop. One spanning a dozen files still takes this shape.
- **One concern**, models: [gno#5999](https://github.com/gnolang/gno/pull/5999), [#5996](https://github.com/gnolang/gno/pull/5996). Four short paragraphs, about 200 words, no headers: a target, not a minimum.
- **Several independent changes**, model: [gno#6006](https://github.com/gnolang/gno/pull/6006). One `### <symbol>: <one-line diagnosis>` section per change, separated by `---`, each readable alone. Framing paragraphs first, then a one-line bridge counting what follows. About 150 words per section.
- **One change carrying several decisions**, model: [meet#1619](https://github.com/suitenumerique/meet/pull/1619). `## Problem` in two or three short paragraphs, then `## Design` with one `###` per decision a reviewer could have made differently: what the reader sees, the interface, who it answers, what it costs, what is left out. The headings carry the skim, so this shape runs longer and the budget below does not bind it. It closes on `## What to review closely`, one single-line bullet per part a reviewer should open: the part, why it matters and what it leads to, anchored on the line it sends them to. It opens on the design page where one exists, linked on its own line above the first `###`. A `###` carrying one sentence is not a decision: fold it into its neighbour.

## File

Put `pr-body.md` in the change directory, `projects/<repo>/changes/<slug>/`. It opens with a header block: `Target:` holding the opened PR URL, or else the `compare/...?expand=1` URL, `Head:` and `Base:` with shas, and `Status:` when there is something to say. Then `## Title`, `## Body`, and `## Visual evidence` only when there is something to attach. Only Title and Body get pasted into GitHub; `./scripts/post-fix.sh` opens the PR from this file.

Write nothing about how the file was written: no shape label, no model PR, no round count; that record belongs in `plan.md`. Every line is something the user pastes or acts on; delete the rest.

## Shape

Write prose, broken small.

- Paragraphs of two to four sentences, one idea each. Five or more: split.
- One-line paragraph for each turn in the argument; a skimmer reads only these.
- No process headers such as Purpose or Testing: the only headers are the multi-change shape's `###` sections and the decisions shape's `## Problem` and `## Design`.
- No tables, no bullet lists, no bold, no emoji. Parallel content long enough to want a table means the multi-change shape.
- A diagram wherever a shape is clearer drawn than written; see *Diagrams*.
- A body using role words the reader may not share, an operator against a room owner for one, closes on a collapsed `<details>` block titled Glossary under the last paragraph: one entry per word, a blank line between them so each renders on its own, and the body stays a straight read for whoever already has the words.
- No code block unless real observed output or a diagram, trimmed to the signal-bearing lines.
- Symbols in backticks. Delta from `skills/writing-style.md`: an in-repo symbol needs no link.

Order the paragraphs, in both shapes:

0. Where an issue is being closed, `Fixes #1076` alone on the first line, above everything: GitHub closes the issue on merge from it, and a triaging maintainer sees the ask before the symptom. Name the issue there and nowhere else in the body.
1. The symptom, first sentence, in the reader's terms: what breaks, under what condition. Then the mechanism, named by symbol. Never open with what the change does.
2. The fix, in a clause, stated as a property of the new code, not a narration of the edit.
3. Anything riding along, each item with its own why.
4. What was verified, in the framing paragraphs, never at the end: the one runtime check the jobs cannot show, stated as a claim, never the methodology; the proof belongs in `plan.md`. Never "all tests pass", never a trailing verification section: the check list above the body already carries every job's status. Where a failure needs an explanation the checks withhold, that explanation is a comment on the pull request; the body stays about the change.

The reader has the diff: give only the defect, the consequence, and the context the code cannot supply.

**A body carries the calls, never the coverage.** Which endpoints got the check, which case the guard catches, what each test asserts: the reader opens the diff for all of it. What survives is the decision a reviewer could have made differently: what the default keeps working, what fails loudly rather than quietly, what is deliberately left alone.

- Banned openers: "Today", "Currently", "At the moment", "This PR". The first sentence names what breaks, in plain present tense.
- When the defect has a severe consequence and a mild one, lead with whichever is unambiguous. A severe example that looks like obvious garbage reads as correct rejection and hides the defect; the plainly wrong case that gets accepted lands.
- Example values must be plausible. A version one step past the build shows the defect with nothing granted, where a version far past it invites "that should fail anyway". Quote the real string, and paste the actual error rather than describing it.
- Explain why the existing guard failed only after the reader has watched it fail. When the defect is a disagreement between two builds, two nodes or two versions, say the disagreement is the defect and neither answer is.
- State what is there, never how it got there: neither the problem's history, why the mechanism was built, when it landed, which change left it behind, nor the branch's, what an earlier round carried or what this one drops. Both histories go in `plan.md`.
- Name a rider commit in one line and never offer to split it. The maintainer asks when they want that.
- No caveat about a failure seen only locally: CI runs a different toolchain, so confirm the redness there first.

Hyperlink everything per `skills/writing-style.md`, to the blob at the branch under review or upstream documentation.

State what the change does not achieve, up front: "This does not turn the check green. It clears one condition of three." Say what was deliberately not fixed, and why, whenever a reader would wonder.

## Title

Lowercase after the scope, no trailing period. Name the outcome, not the edit: "stop the block gas price from climbing forever" beats "fix gas price bug". Match the target repo's convention: check its recent merged titles and its `.gitlint`.

## Diagrams

Draw one whenever the reader would assemble a shape in their head from sentences: which of N checks fails, a trust boundary, a before and after, an ordering change.

ASCII in a fenced block by default; Mermaid only past six nodes or crossing edges.

- Label nodes with real symbols and numbers, never placeholders.
- Mark the thing the PR changes with an arrow and three words.
- One diagram per idea; two small beat one big.
- Delete the sentences the diagram makes redundant.
- Under about twelve lines; over that, split or cut nodes.

```
commit 8cbcad76 on main
├── meet Workflow ........ 12/12 green   ← all `gh run list` shows
├── CodeQL ............... green
└── SonarCloud ........... FAIL
    ├── reliability    D → needs A    1 issue     ← this PR
    └── security       C → needs A    89 issues   84 are policy
```

## Loop

Do not ship the first draft. Re-read against the checks below, revise, repeat until a full pass changes nothing. Record the rounds in `plan.md`.

1. Would someone with no context understand the first sentence? If it needs a symbol they have not met, rewrite in observable terms.
2. Cut every sentence that does not change the merge decision: diff restating, process narration, "this PR" openers.
3. Skim it in ten seconds, first lines and diagrams only. If that does not give the merge decision, lift the argument's turns into one-line paragraphs.
4. Check against the diff one last time. A body describing a change not in the diff is worse than none.

Past the shape's budget: cut, never restructure. Overflow detail belongs in the review file and the plan. The count is never the target: the body is done when a cold read lands on the first pass.

## Visual evidence

A screenshot for any user-visible surface; a short video or GIF for any interaction or motion.

- Before and after, side by side, same viewport, same data. Crop to the surface.
- Attach by dragging into the PR body on GitHub. Keep the files under `projects/<repo>/changes/<slug>/media/`; mark each attachment point with the `media/` path. Never fabricate a `user-images` URL.
- None for backend-only, tooling, or lint changes.

Capture per *Video* in `skills/try.md`, which owns the recording rules. When no capture can be made, say the screenshot is missing and why, never what it would have shown.
