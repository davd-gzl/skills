---
name: pr-body
description: Write the title and body of a pull request. Use whenever a change is being proposed, before opening the PR. Produces pr-body.md in the change directory, and loops on it until it passes the checks below.
---

# PR body

Write for a reader with no context who must decide whether to merge. Prose follows `skills/writing-style.md`; the rules below are the PR-body deltas.

Pick one of four shapes, by what the pull request carries, and read that shape's file whole through `./scripts/skill pr-body/<shape>` before drafting: it holds the headers in order, what goes under each, the length, how it opens and closes, and a worked example. Never mix them.

| The pull request carries | Shape |
| --- | --- |
| Documentation pages, however many | `skills/pr-body/docs.md` |
| One concern, which is every bug fix, whatever the number of decisions behind it | `skills/pr-body/one-concern.md` |
| Several independent changes; parallel content long enough to want a table means this shape | `skills/pr-body/several-changes.md` |
| One change with a surface someone sees, a front-end feature or a change to what a page renders, where the decisions are what the reader gets rather than what the code does | `skills/pr-body/surface.md` |

## File

Put `pr-body.md` in the change directory, `projects/<repo>/changes/<slug>/`. It opens with a header block: `Target:` holding the opened PR URL, or else the `compare/...?expand=1` URL, `Head:` and `Base:` with shas, and `Status:` when there is something to say. Then `## Title` and `## Body`, and nothing after them: `./scripts/post-fix.sh` opens the PR from this file and pastes every line following the `## Body` heading into it, so a section added below goes out with the body. Media provenance and the inline comments posted beside the body belong in `plan.md`. A body already on GitHub is read back before it is rewritten, per *Posting* in `skills/review-comment.md`: an edit made in the interface is invisible here.

Write nothing about how the file was written: no shape label, no model PR, no round count; that record belongs in `plan.md`. Every line is something the user pastes or acts on; delete the rest.

## Shape

Write prose, broken small.

- Paragraphs of two to four sentences, one idea each. Five or more: split.
- One-line paragraph for each turn in the argument; a skimmer reads only these.
- No process headers such as Purpose or Testing. The shape's file names the headers it takes; nothing else gets one.
- No tables, no bullet lists, no bold, no emoji.
- A diagram wherever a shape is clearer drawn than written; see *Diagrams*.
- A body using role words the reader may not share, an operator against a room owner for one, closes on a collapsed `<details>` block titled Glossary under the last paragraph: one entry per word, a blank line between them so each renders on its own, and the body stays a straight read for whoever already has the words.
- No code block unless real observed output or a diagram, trimmed to the signal-bearing lines.
- Symbols in backticks. Delta from `skills/writing-style.md`: an in-repo symbol needs no link, a link anchors on a symbol or a file name and never on a clause, and a body carries only the links a reader needs to check a claim the diff does not show. A paragraph that reads as one hyperlink has failed.

Order the paragraphs, in every shape:

0. Where an issue is being closed, `Fixes #1076` alone on the first line, above everything: GitHub closes the issue on merge from it, and a triaging maintainer sees the ask before the symptom. Name the issue there and nowhere else in the body.
1. The symptom, first sentence, in the reader's terms: what breaks, under what condition. Then the mechanism, named by symbol. Never open with what the change does.
2. The fix, in a clause, stated as a property of the new code, not a narration of the edit.
3. Anything riding along, each item with its own why.
4. What was verified, in the framing paragraphs, never at the end: the one runtime check the jobs cannot show, stated as a claim; the proof belongs in `plan.md`. Never "all tests pass" and never a trailing verification section, since the check list above the body carries every job's status. A redness seen only locally is confirmed on CI before it reaches the body, and an explanation the checks withhold is a comment on the pull request.

The reader has the diff: give only the defect, the consequence, and the context the code cannot supply.

**A body carries the calls, never the coverage.** Which endpoints got the check, which case the guard catches, what each test asserts: the reader opens the diff for all of it. What survives is the decision a reviewer could have made differently: what the default keeps working, what fails loudly rather than quietly, what is deliberately left alone.

- Banned openers: "Today", "Currently", "At the moment", "This PR". The first sentence names what breaks, in plain present tense.
- When the defect has a severe consequence and a mild one, lead with whichever is unambiguous. A severe example that looks like obvious garbage reads as correct rejection and hides the defect; the plainly wrong case that gets accepted lands.
- Example values must be plausible. A version one step past the build shows the defect with nothing granted, where a version far past it invites "that should fail anyway". Quote the real string, and paste the actual error rather than describing it.
- Explain why the existing guard failed only after the reader has watched it fail. When the defect is a disagreement between two builds, two nodes or two versions, say the disagreement is the defect and neither answer is.
- State what is there, never how it got there: neither the problem's history, why the mechanism was built, when it landed, which change left it behind, nor the branch's, what an earlier round carried or what this one drops. Both histories go in `plan.md`, and no line points at the decision record the change ships.
- Name a rider commit in one line and never offer to split it. The maintainer asks when they want that.

Hyperlink everything per `skills/writing-style.md`, to the blob at the reviewed sha or upstream documentation.

State what the change does not achieve, up front: "This does not turn the check green. It clears one condition of three." Say what was deliberately not fixed, and why, whenever a reader would wonder.

## Title

Lowercase after the scope, no trailing period. Name the outcome, not the edit: "stop the block gas price from climbing forever" beats "fix gas price bug". Match the target repo's convention: check its recent merged titles and its `.gitlint`.

## Diagrams

Draw one whenever the reader would assemble a shape in their head from sentences: which of N checks fails, a trust boundary, a before and after, an ordering change.

ASCII in a fenced block by default; Mermaid only where edges cross.

- Label nodes with real symbols and numbers, never placeholders.
- Mark the thing the PR changes with an arrow and three words.
- One diagram per idea; two small beat one big, and a diagram carrying a second idea splits.
- Delete the sentences the diagram makes redundant.

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

1. Read it as the maintainer who wrote the code it describes, before the user ever sees it. Open the file behind every sentence about what the code does today. A claim of absence is the one that breaks: where the thing exists in a weaker form, name the form and what it fails to do, never call it missing.
2. Would someone with no context understand the first sentence? If it needs a symbol they have not met, rewrite in observable terms.
3. Cut every sentence that does not change the merge decision: diff restating, process narration, "this PR" openers.
4. Skim it in ten seconds, first lines and diagrams only. If that does not give the merge decision, lift the argument's turns into one-line paragraphs.
5. Check against the diff one last time. A body describing a change not in the diff is worse than none.

Past the shape's budget: cut, never restructure. Overflow detail belongs in the review file and the plan. The count is never the target: the body is done when a cold read lands on the first pass.

## Visual evidence

A screenshot for any user-visible surface; a short video or GIF for any interaction or motion.

- Before and after, side by side, same viewport, same data. Crop to the surface.
- It sits in the problem, so a reader sees the defect before reading the account of it, and what follows explains what they already looked at.
- Retake it whenever the surface moves, in the turn the code changes, unasked. A body carrying a shot of an earlier commit shows a page that no longer exists, and the reader has no way to tell.
- **A retake gets a new filename, never the path the body already points at.** GitHub proxies an embedded image through a cache of its own, which keeps serving the bytes it fetched first, so replacing the file leaves the stale picture in the body with nothing to show it is stale.
- Host it and embed it per the picture rule in `skills/writing-style.md`, so the body goes up whole and nothing is dragged by hand, keeping a copy under `projects/<repo>/changes/<slug>/media/`. Drag into the box only where the target cannot reach the artifact repository the workspace `AGENTS.md` names, and never fabricate a `user-images` URL.
- None for backend-only, tooling, or lint changes.

Capture per *Video* in `skills/try.md`, which owns the recording rules. When no capture can be made, say the screenshot is missing and why, never what it would have shown.
