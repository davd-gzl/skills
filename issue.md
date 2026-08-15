---
name: issue
description: Draft a GitHub issue for a problem found by a review. Use when a fix is being prepared and no upstream issue covers the problem. Produces issue.md, posted only after user approval.
---

# Issue

An issue states a problem; a pull request states a change. The issue never describes the fix, the pull request never re-argues the problem, and neither restates the other. When both exist, the pull request references the issue.

Prose follows `skills/writing-style.md`; the rules below are the issue deltas.

## When to draft one

Only when both hold:

1. No upstream issue already covers the problem.
2. The problem outlives the pull request that addresses it.

Search before drafting, both ways, because titles rarely contain the words you expect:

```bash
gh issue list -R <repo> --state all --limit 100 --json number,title --jq '.[]|"\(.number)\t\(.title)"'
gh api "search/issues?q=repo:<repo>+is:issue+<term>+OR+<term>" --jq '.total_count'
```

Search every title, open and closed, then full text on the words a maintainer would have used, including the repo's own working language, across pull requests as well as issues. A reframing of the ask is a new search: the words that would find the duplicate moved with it, so a resize proposal is not covered by the sweep that cleared a move proposal.

Record what the search covered in the draft's `Status:` line and name the nearest miss in the reply, because a reader cannot tell an absence that was checked from one that was assumed.

Read the timeline of any issue already covering the problem for cross-references from pull requests in the same repository, and record each with its state. An open one means the issue is taken; a closed one usually means the obvious fix was tried and rejected. An issue ranked easy with that column empty has not been checked.

## File

Put `issue.md` in the review directory, `projects/<repo>/reviews/<slug>/<n>-<sha>/`, beside the review file: an issue can exist when no fix does. It opens with a header block, `Target:` holding the opened issue URL, or else `https://github.com/<repo>/issues/new` and `Status:`, then `## Title` and `## Body`.

## Two kinds

A defect issue reports what the code does; a feature request asks for what it does not do. Everything below is the defect shape unless it says otherwise.

Read the repo's `.github/ISSUE_TEMPLATE/` before drafting either. Keep its `##` headings, `## Feature Request` for one, and delete everything else it ships: the bold prompts, the italic hints, the HTML comments. A prompt left in the body is the form showing through the answer.

```bash
gh api repos/<repo>/contents/.github/ISSUE_TEMPLATE --jq '.[].name'
```

A feature request:

- Titles what the reader could then do, never what is missing: "Let the chat be resized by dragging its border".
- States what the code settles today, with the line that settles it, then proposes the change in one sentence. A feature request carrying no proposal is a complaint.
- Puts one checkbox per piece only where the pieces could ship separately. A single ask gets no list.
- Runs as long as the ask and no longer: one ask is two sentences, five separable pieces are five checkboxes.
- Answers only the template questions carrying a fact this ask needs. The considered-alternatives and migration prompts usually carry none, and the author's own issues drop them.
- Leaves the template's question about building it to the user. Never volunteer their time and never decline for them: carry the offer on the last line only when they have said they will build it, and otherwise say nothing.

## Title

Measure the repo's own issue titles first; they rarely follow its commit convention, and applying that convention to an issue title is the common mistake.

```bash
gh issue list -R <repo> --state all --limit 25 --json title --jq '.[].title'
```

Name the observable problem, not the diagnosis: "SonarCloud quality gate has been failing on `main`", not "projectVersion is unset".

## Body

State the problem and where it comes from. Nothing else.

- Write for the maintainer. Cut anything that is a record of how you found the problem: a tool that misled you, a step you had to repeat.
- Lead with the fact that changes how everything after it reads: a count inflated by configuration, a failure that is old rather than new. A reader who meets it last has already misjudged everything above.
- Give counts meaning, never size alone: "89 findings, one code defect and 88 deployment configuration", not an inventory the reader must interpret alone.
- Open with what a maintainer sees, and where. Count the consecutive failures and name the last pass instead of "for months". Link the failing thing itself: the check run's `html_url`, the workflow run, and for an external check its `details_url`.
- Give the shape before the detail; use a diagram when several parts fail differently, per the Diagrams section of `skills/pr-body.md`.
- Break the problem into parts, each with its count and source: which files, which rule, which subsystem.
- State the root cause last, when it is checkable, with evidence a reader can open unauthenticated. A cause is a source, not a fix.
- Do not explain the maintainers' own tooling to them. State what you observed and let them supply the reason.
- Never write the remedy for a defect. Naming a fix is designing it, and a defect issue is the wrong place; a feature request is the opposite and states its proposal. If a part is already fixed, say so in one clause and link the pull request.
- Say nothing about severity, priority, or effort.
- Length follows the repo's own issues.

A discussion-opener issue is shorter: open with "Opening this to start a discussion.", then three sections at most, and end on the last fact. No closing ask, no offer to send pull requests, no hedge that the problem may already be known.

## Loop

This loop is mandatory. It is not the last polish on a body already finished: revise against the checks below, repeat until a full pass changes nothing, then run the Pass in `skills/writing-style.md` over the result. A first draft is never the posted one.

The goal is the text a maintainer reads once and understands, and that is the only goal. Shorter is usually how it is reached, never what it is for. A round that cuts a word and costs the reader a second pass has gone backwards, and a body that grows because a reader needed the sentence has gone forwards.

1. Every word the reader meets is one they can see, verbs included. Quote a setting as the label on screen and a value as the string in the menu, and take the verb from the button rather than from the API: a camera is disabled, never muted. The code's own enum names appear nowhere in a body.
2. Read the project's glossary while drafting, not after a reader stumbles. A term stops looking like jargon to whoever just read the file defining it, so the check cannot be your own ear.
3. The cause sits last and nothing follows it. Put a fact that only makes sense after the cause in that same paragraph, never above it.
4. Cut or link every assertion the body does not prove. "The largest", "the heaviest", "the only": give the line that shows it, or give the contrast that makes the claim unnecessary.
5. Read the finished body cold, as a maintainer who has never seen the code. Anywhere the eye goes back, split the sentence. That reading, not the word count, is what says the loop is done.

Report the outcome: what the last round changed, or that a full pass changed nothing.

## Posting

Never post without the literal word `post` in the current turn. On `post`, run `./scripts/post-fix.sh <review-dir> <change-dir>` yourself; it opens the issue and the pull request from the drafts and writes the URLs back into their `Target:` lines. To post standalone: `gh issue create -R <repo> --title "<title>" --body-file <path>`, body only, then write the URL into `Target:` yourself.

Check whether the repo actually uses labels before setting any.

After posting, add `Fixes #<n>` or `Refs #<n>` to `pr-body.md` where it applies, and commit the updated drafts.
