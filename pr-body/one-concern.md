---
name: pr-body/one-concern
description: The pull request body for one concern, which is every bug fix, whatever the number of decisions behind it. Read through ./scripts/skill pr-body/one-concern once skills/pr-body.md has picked this shape.
---

# One concern

Short paragraphs under `## Problem` and `## Fix`, one per part of the fix, each saying what that part does and why it is built that way.

- The first line is the severity, `6/10, medium`, per `skills/writing-style.md`, above `Fixes #n` and every heading.
- `## Problem`, one or two paragraphs: the symptom first, in the reader's terms, under the condition that triggers it, then the mechanism named by symbol with a link into the code on the branch, then the change that introduced it.
- `## Fix`: the new code's property in a clause, never a narration of the edit. Then the riders in one paragraph, each with its own why. Then what the fix leaves standing, one sentence. Then the one runtime check no job shows, stated as a claim, and nothing after it but the closing blocks of `skills/pr-body.md`: no line naming the ADR or wherever else the decisions are recorded, which the reviewer finds in the diff.
- No `## Design`, whatever the number of decisions behind the fix: a decision a reviewer could have made differently is a clause of the fix paragraph, with what it costs.

Why: a reviewer of a fix wants the defect and the property that removes it, and opens the diff for everything else.

## Skeleton

```markdown
6/10, medium

Fixes #<issue>

## Problem

<What breaks, in the reader's terms, under the condition that triggers it.> <The mechanism, named by symbol and linked into the branch.> <The change that introduced it.>

## Fix

<The new code's property, in one clause.>

<The riders, each with its own why.> <What the fix leaves standing, in one sentence.>

<The one runtime check no job shows, stated as a claim.>

<details><summary>Read the code in this order</summary>

<The stops, hot then warm then cold, per skills/pr-body.md.>

</details>
```
