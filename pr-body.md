---
name: pr-body
description: Write the title and body of a pull request. Use whenever a change is being proposed, before opening the PR. Produces pr-body.md in the change directory, and loops on it until it passes the checks below.
---

# PR body

Prose follows `skills/writing-style.md`; the rules below are the PR-body deltas.

Pick one of four shapes, by what the pull request carries, and read that shape's file whole through `./scripts/skill pr-body/<shape>` before drafting: it holds the headers in order, what goes under each, the length, how it opens and closes, and a skeleton of the body. Never mix them. A body closes on the `Read the code in this order` block below only where `round risk` ranks more than one file of the diff hot or warm, whatever the shape's own file lists; a change whose risk sits in one file drops the block. The real body each skeleton was drawn from sits in `skills/pr-body/examples/<shape>.md`, for whoever edits the shape.

| The pull request carries | Shape |
| --- | --- |
| Documentation pages, however many | `skills/pr-body/docs.md` |
| One concern, which is every bug fix, whatever the number of decisions behind it | `skills/pr-body/one-concern.md` |
| Several independent changes; parallel content long enough to want a table means this shape | `skills/pr-body/several-changes.md` |
| One change with a surface someone sees, a front-end feature or a change to what a page renders, where the decisions are what the reader gets rather than what the code does | `skills/pr-body/surface.md` |

Before picking a shape, ask whether every hunk explains itself: an escape call added, a variable unexported, an input validated. Such a change, however many files and fixes it spans, takes the one-concern shape at its shortest: a severity line and any `Fixes` line, the `In short:` part with the fix in a sentence, then one paragraph naming each kind of defect, each shown in code per *Shape*, with no `###` section per file. The tell is a body longer than the diff it describes.

## File

Put `pr-body.md` in the change directory, `projects/<repo>/changes/<slug>/`. It opens with a header block: `Target:` holding the opened PR URL, or else the `compare/...?expand=1` URL, `Head:` and `Base:` with shas, `Status:` when there is something to say, and the `Reader passes:` line step 6 of *Loop* records. Then `## Title` and `## Body`, and nothing after them: `./scripts/post-fix.sh` opens the PR from this file and pastes every line following the `## Body` heading into it, so a section added below goes out with the body. Media provenance and the inline comments posted beside the body belong in `plan.md`. Before a body already on GitHub is rewritten, `./scripts/pr-body-apply --pull <pr-body.md>` brings the live body into the file, since an edit made in the interface is invisible here.

A body carries, right under its `In short:` part, a collapsed `<details>` block titled `Topics you should know`: each topic a reader needs to follow the change, explained in a few sentences, drawn from `overview.md`. The text above uses those words and never re-explains them.

Being efficient to read is the first rule of a body: anyone who has never opened the code gets the problem and the fix in one read, with nothing else open, and a line that makes the next one understandable is worth its place. Every other line is worth the reviewer's read, or it goes. A body states each fact once, where the reader first needs it. Every later part a rule in this file or a shape's file asks for carries only what is new, and is cut whole where it adds nothing: a section, the fix's clause, a symptom, a code comment, a reading-order stop, a design bullet's first sentence. A body carries every fact the merge decision needs, and nothing a reviewer would skip: the diff restated, mechanism a reviewer can read in the code, the branch's history, a line that would read the same on any pull request, rejected alternatives a reviewer would not have raised. Those go to the decision record or `plan.md`. Step 6 of *Loop* checks it.

The design choices a reviewer could reasonably flip go in a collapsed `<details>` block titled `Design alternatives`, always in one place: under the body's last `##` section, so after `## Fix`, `## What a user notices` and `## Not fixed` wherever those exist, and above every other collapsed block that closes the body. One bullet per choice about the fix itself, the one a reviewer is likeliest to change first. Each bullet is the choice's name in bold, then two sentences: what the change does, where the body has not said it, then the other way and the condition that picks it, `- **Spaces in the name**: the value is checked as written, so a name with a leading space is refused. Trim it first if forms with stray spaces should keep rendering.` No sentence argues for either side: an option the reviewer may take, never a choice defended. A score, a label, a test-running method, how the change is split into pull requests, an alternative that cannot work, or anything about how the branch was made is not a design choice and stays out: each bullet is a question worth putting to the reviewer. A body with no such choice drops the block.

`What a user notices` and `Not fixed` are design, so they are `##` sections of the body after `## Fix`, one bullet per effect. The reading order block goes last, in a collapsed `<details>` titled `Read the code in this order`, its temperature line and stops inside. Stops run hot, then warm, then cold, in reading order within a tier, and a test or a test fixture is cold whatever the ranking says. In a body each stop is a numbered list item at text size, never a heading, on three lines, the title and its linked file on the first, and carries no code excerpt, since the diff link opens the lines:

```markdown
🔴 hot is the riskiest code, 🟠 warm other code, 🔵 cold a test. The tier ranks the file's risk, not how much of it changed.

1. 🔴 hot · The exec check in `FormParser.Open`, [`gno.land/pkg/gnoweb/markdown/ext_forms.go`](<diff link>)
   Refuses an `exec` that is not an exported identifier.
   **If wrong:** a realm puts shell text in the copied command.
```

## In short

Every body that changes code, in every shape but `skills/pr-body/docs.md`, opens on an `In short:` part, under the severity line and the `Fixes` line, or the lines a project's delta puts there, and above the problem. It is for a reader who has never opened the subsystem: what breaks and when, the one term they need, and how the fix works as a before and after, in whatever form lands it in one read: a few plain sentences, a sketch per *Diagrams*, a few lines of code on each side, the before side dropped where a defect block below shows it. What follows gives only the detail it leaves out. As a delta from `skills/writing-style.md`, a before and after of the fix is not cut for restating the diff; a false or unproved line in this part is fixed like any other.

## Shape

Write prose, broken small.

- Paragraphs of two to four sentences, one idea each. Five or more: split.
- One-line paragraph for each turn in the argument; a skimmer reads only these.
- No tables, no emoji but the reading order's tier markers, and no bold but the decision lead-ins of `skills/pr-body/surface.md` and the labelled lead-ins a project's delta asks for. A bullet list only where its items run parallel, the paths a fix covers or the effects a user notices, never for an argument.
- Each sentence opens on the plain-words version of what it says, then names the symbol. A term the reader lacks is defined in the sentence that first uses it, never taught: how the mechanism behind it works goes in `Topics you should know`.
- Before writing a body that fixes code, whatever its shape, show each kind of defect as code right after the sentence stating it: one block per kind, the fewest lines a caller writes to trigger it, taken from the branch's own test where one exists, with a comment on the call that goes wrong, so the reader sees the failure before the account of it. A crash and a silently wrong value are two kinds. Every package the block uses beyond its own gets its import line in the block. That block shows the defect, never the diff restated, and no cut for length takes it. Every other code block is real observed output, a diagram or a before and after of the fix, trimmed to the signal-bearing lines. A change that writes a file a person opens, an export or a report, shows a few real lines of it.
- When writing the comment on a defect block's failing call, say what the call does on the base branch and, where a reference the project means to match answers the same call, what that reference gives: `prints 99; Go prints 1`.
- Symbols in backticks. Delta from `skills/writing-style.md`: an in-repo symbol needs no link, a link anchors on a symbol, a file name or the name of the documentation section it opens, and never on a clause, and a body carries only the links a reader needs to check a claim the diff does not show. A paragraph that reads as one hyperlink has failed.

Order the paragraphs, in every shape:

0. Where an issue is being closed, `Fixes #1076` alone on its own line above every heading, under the severity line where the shape carries one: GitHub closes the issue on merge from it, and a triaging maintainer sees the ask before the symptom. Name the issue there and nowhere else in the body.
1. The symptom's detail the `In short:` part leaves out, in the reader's terms. Then the mechanism, named by symbol. Never open with what the change does.
2. The fix, in a clause, stated as a property of the new code, not a narration of the edit.
3. Anything riding along, each item with its own why.
4. What was verified, in the framing paragraphs, never at the end: the one runtime check the jobs cannot show, stated as a claim; the proof belongs in `plan.md`. Never "all tests pass" and never a trailing verification section, since the check list above the body carries every job's status; the one closing section `skills/pr-body/several-changes.md` keeps names a method several sections share, one row per section. A redness seen only locally is confirmed on CI before it reaches the body, and an explanation the checks withhold is a comment on the pull request.

Before writing a pull request's state, back to draft, a commit its author has not reviewed, what it waits on, draft it as a comment on the pull request, never a line in the body: the body describes the change, and a state written there outlives the state.

**A body carries the calls, never the coverage.** Which endpoints got the check, which case the guard catches, what each test asserts: the reader opens the diff for all of it. What survives is the decision a reviewer could have made differently: what the default keeps working, what fails loudly rather than quietly, what is deliberately left alone.

- Banned openers: "Today", "Currently", "At the moment", "This PR". The first sentence names what breaks, in plain present tense.
- When the defect has a severe consequence and a mild one, lead with whichever is unambiguous. A severe example that looks like obvious garbage reads as correct rejection and hides the defect; the plainly wrong case that gets accepted lands.
- Example values must be plausible. A version one step past the build shows the defect with nothing granted, where a version far past it invites "that should fail anyway". Quote the real string, and paste the actual error rather than describing it.
- When the defect is a disagreement between two builds, two nodes or two versions, and no reference the project means to match decides between them, say the disagreement is the defect and neither answer is.
- When the project means to match a reference outside it, the language it implements or a spec it follows, and its code gives another answer, state in one sentence after the defect's code blocks what that reference requires, linked on the name of its section, leaving the diverging code to the mechanism and the answer to the block's comment: `Each case clause is its own block in Go, per the spec's [Blocks](https://go.dev/ref/spec#Blocks).`
- Before a body goes up, put everything the fix leaves standing, a sibling with the same defect, a limit of the fix, a cost it does not remove, under `## Not fixed`, in every shape: one bullet each naming it, never a paragraph explaining it, and never a sentence under `## Fix` instead. Before writing each bullet, fix its item on the branch where step 5 of *Fix* in `skills/change.md` allows it, and write the bullet only for what that leaves.
- When an input next to the defect already behaves correctly though a reader would take it for the same defect, name it beside the fix with why it is already right: `a type switch's variable cannot be redeclared in a case, since Go declares it in that clause's own block, per [Type switches](https://go.dev/ref/spec#Type_switches)`.
- Name a rider commit in one line and never offer to split it. The maintainer asks when they want that.

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

Do not ship the first draft. Re-read against checks 1 to 5, revise, repeat until a full pass changes nothing, then run step 6. Record the rounds in `plan.md`.

1. Read it as the maintainer who wrote the code it describes, before the user ever sees it. Open the file behind every sentence about what the code does today. A claim of absence is the one that breaks: where the thing exists in a weaker form, name the form and what it fails to do, never call it missing.
2. Cut every sentence that does not change the merge decision and that no later line needs to be understood: diff restating, a fact already stated, process narration, "this PR" openers.
3. Skim it in ten seconds, first lines and diagrams only. If that does not give the merge decision, lift the argument's turns into one-line paragraphs.
4. Check against the diff one last time. A body describing a change not in the diff is worse than none.
5. Cut every heading the chosen shape does not list, `## What to review closely` above all, whose parts go as inline comments per `skills/pr-body/surface.md`; a body revised on the forge is re-derived from the shape, never edited section by section from the copy there.
6. Once before the body first goes up, and again only after a revision outside this step rewrites a paragraph, run a reader loop, whose aim is the simplest body each reader understands in one read, leaving them no question to ask the author once they have read it and the diff. Each round hands the body, the diff and the parts the project's delta requires, never the plan, to one fresh agent per reader, in parallel: the reviewer who knows the code and the maintainer deciding the merge. Beside them, in every round, `./scripts/cold-read` reads the body alone as the reader who has never opened the code, per step 11 of the Pass in `skills/writing-style.md`: it names stops only, each fixed as a `wording` stop, and the line verdicts and the `nothing` cut below come from the agents. Where it exits 2 or cannot run, a fresh agent given the body alone plays that reader and returns stops only, as `./scripts/cold-read` does, and the reply names why. The reviewer who knows the code reads in the first round only, and opens the line behind every claim the body makes about the code, a code block's lines and comments included, and names each one the code contradicts: that check is done once, and a claim a later fix rewrites is opened against the code by whoever applies the fix. Each reader first names every place it had to stop: a term used before it is explained, a step the argument skips, a sentence it read twice, a question it would still ask the author. A question the code should answer, a name or a missing comment, is fixed in the code where the diff already changes that line, and offered in the handover elsewhere. Then, for every paragraph, bullet, table row and reading-order item, it names what its reader would lose if that line went, or `nothing`, or the line that already says it, and how the line could say the same more simply. Fix every `wording` and `substance` stop and take every simpler wording that keeps the fact, before any cut: a term the reader lacks gets its definition where it is first used, and a skipped step or a hard sentence is rewritten where it stands. Then cut each line every reader marked `nothing` and each later copy of a fact, never a line the next one needs. Each reader marks each stop `wording` or `substance`, a claim the code contradicts and a stop it is unsure of being `substance`, any reader's `substance` mark deciding it, a code question offered in the handover being `wording`, and a question whose answer would teach the subsystem rather than the change `overview`, answered in `Topics you should know`. The next round goes to a fresh maintainer reading the whole body, with this round's changes marked and the line after each cut, and to a fresh `./scripts/cold-read` run over the whole body. The loop ends on the first round with no `substance` stop and no cut, its wording stops fixed with no further round: a loop waiting for an empty round samples new nits rather than converging. A second round's stops and cuts are applied, and then it ends whatever it found, the reply naming each `substance` stop still open. Every round's verdicts go in `plan.md`, where a line kept against one names the fact it carries. Then run `./scripts/post-fix.sh <change dir> --record-read`, which writes the body's hash on a `Reader passes:` header line: post-fix opens no body that line does not match, so an edit made before the pull request opens is recorded again, after the loop reruns where it rewrote a paragraph. Overflow detail belongs in the review file and the plan.

## Visual evidence

A screenshot for any user-visible surface; a short video or GIF for any interaction or motion.

- Before and after, side by side, same viewport, same data. Crop to the surface.
- It sits in the problem, so a reader sees the defect before reading the account of it, and what follows explains what they already looked at.
- Retake it whenever the surface moves, in the turn the code changes, unasked. A body carrying a shot of an earlier commit shows a page that no longer exists, and the reader has no way to tell.
- **A retake gets a new filename, never the path the body already points at.** GitHub proxies an embedded image through a cache of its own, which keeps serving the bytes it fetched first, so replacing the file leaves the stale picture in the body with nothing to show it is stale.
- Host it and embed it per the picture rule in `skills/writing-style.md`, so the body goes up whole and nothing is dragged by hand, keeping a copy under `projects/<repo>/changes/<slug>/media/`. Drag into the box only where the target cannot reach the artifact repository the workspace `AGENTS.md` names, and never fabricate a `user-images` URL.
- None for backend-only, tooling, or lint changes.

Capture per *Video* in `skills/try.md`, which owns the recording rules. When no capture can be made, say the screenshot is missing and why, never what it would have shown.
