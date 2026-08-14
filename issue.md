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

Record what the search covered in the draft's `Status:` line, so a later reader sees the absence was checked, not assumed.

## File

Put `issue.md` in the review directory, `projects/<repo>/reviews/<slug>/<n>-<sha>/`, beside the review file: an issue can exist when no fix does. It opens with a header block, `Target:` holding the opened issue URL, or else `https://github.com/<repo>/issues/new` and `Status:`, then `## Title` and `## Body`.

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
- Never write the remedy. Naming a fix is designing it, and the issue is the wrong place. If a part is already fixed, say so in one clause and link the pull request.
- Say nothing about severity, priority, or effort.
- Length follows the repo's own issues.

A discussion-opener issue is shorter: open with "Opening this to start a discussion.", then three sections at most, and end on the last fact. No closing ask, no offer to send pull requests, no hedge that the problem may already be known.

## Loop

This loop is mandatory. It is not the last polish on a body already finished: revise against the checks below, repeat until a full pass changes nothing, then run the Pass in `skills/writing-style.md` over the result. A first draft is never the posted one.

The goal is the text a maintainer reads once and understands, and that is the only goal. Shorter is usually how it is reached, never what it is for. A round that cuts a word and costs the reader a second pass has gone backwards, and a body that grows because a reader needed the sentence has gone forwards.

1. Every noun the reader meets is one they can see. Quote a setting as the label on screen and a value as the string in the menu; the code's own enum names appear nowhere in a body.
2. The cause sits last and nothing follows it. Put a fact that only makes sense after the cause in that same paragraph, never above it.
3. Cut or link every assertion the body does not prove. "The largest", "the heaviest", "the only": give the line that shows it, or give the contrast that makes the claim unnecessary.
4. No sentence runs more than five words before its main verb. This fails on a subject carrying a relative clause, and the second person usually fixes it.
5. Every picture is introduced by a sentence saying what it shows and where it came from, the browser or the instance included. An image dropped in bare leaves the reader deciding whether it is a mockup.
6. Read the finished body cold, as a maintainer who has never seen the code. Anywhere the eye goes back, split the sentence. That reading, not the word count, is what says the loop is done.

Report the outcome: what the last round changed, or that a full pass changed nothing.

## Posting

Never post without the literal word `post` in the current turn. On `post`, run `./scripts/post-fix.sh <review-dir> <change-dir>` yourself; it opens the issue and the pull request from the drafts and writes the URLs back into their `Target:` lines. To post standalone: `gh issue create -R <repo> --title "<title>" --body-file <path>`, body only, then write the URL into `Target:` yourself.

Check whether the repo actually uses labels before setting any.

After posting, add `Fixes #<n>` or `Refs #<n>` to `pr-body.md` where it applies, and commit the updated drafts.
