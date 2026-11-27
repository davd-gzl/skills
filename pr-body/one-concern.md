---
name: pr-body/one-concern
description: The pull request body for one concern, which is every bug fix, whatever the number of decisions behind it. Read whole once skills/pr-body.md has picked this shape.
---

# One concern

Short paragraphs: under `## Problem` one per kind of defect, the sentence on the reference where `skills/pr-body.md` asks for one, and one per mechanism; under `## Fix` one per part of the fix, saying what that part does and why it is built that way.

- The first line is the severity, `6/10, medium`, per `skills/writing-style.md`, above `Fixes #n` and every heading.
- `## Problem`: for each kind of defect, the symptom in detail, in the reader's terms, under the condition that triggers it, then the code block that triggers it, per `skills/pr-body.md`. Then the sentence on the reference, where the same file asks for one. Then, for each mechanism, the mechanism named by symbol with a link into the code on the branch, one sentence carrying it with `so` to the internal step that goes wrong, `the key holds the path alone, so the second request reads the entry the first one wrote`, never the symptom again, and the change that introduced it.
- `## Fix`: the new code's property in a clause, never a narration of the edit. Then the part paragraphs. Then any neighbouring input that already behaves correctly though a reader would take it for the same defect, per `skills/pr-body.md`. Then the riders in one paragraph, each with its own why. Then the one runtime check no job shows, stated as a claim, and nothing after it but the closing blocks of `skills/pr-body.md`: no line naming the ADR or wherever else the decisions are recorded, which the reviewer finds in the diff.
- Where a part of the fix changes code that other inputs also reach and leaves their results unchanged, and a reviewer would ask whether they move, the part's paragraph names the invariant that keeps them: `a name is declared twice in one scope only when a case body shadows it, so resolving each name to its last declaration changes nothing in any other scope`.
- `## Not fixed`, after `## Fix`, per `skills/pr-body.md`.
- No `## Design`, whatever the number of decisions behind the fix: a decision a reviewer could have made differently is a clause of the part paragraph it shapes, with what it costs.

## Skeleton

````markdown
6/10, medium

Fixes #<issue>

In short: <What breaks and when, the one term a newcomer needs, how the fix works as a before and after, per *In short* in skills/pr-body.md.>

<details><summary>Topics you should know</summary>

<Each topic the reader needs, a few sentences each, per skills/pr-body.md.>

</details>

## Problem

<For each kind of defect: what breaks, in the reader's terms, under the condition that triggers it, then its block.>

```<language>
<The fewest lines a caller writes to trigger it, from the branch's own test where one exists, a comment on the call that goes wrong saying what it does on the base branch and, where a reference the project means to match answers the same call, what that reference gives; an import line for every package it uses beyond its own.>
```

<What the reference the project means to match requires, in one sentence linked on its section's name, where skills/pr-body.md asks for one.>

<For each mechanism: the mechanism, named by symbol and linked into the branch, one sentence carrying it with `so` to the internal step that goes wrong, never the symptom again, and the change that introduced it.>

## Fix

<The new code's property, in one clause.>

<One short paragraph per part: what it does, why it is built that way, and, where a reviewer would ask whether other inputs' results move, the invariant that keeps them unchanged.>

<A neighbouring input a reader would take for the same defect, and why it is already right, if there is one.>

<The riders, each with its own why.>

<The one runtime check no job shows, stated as a claim.>

## Not fixed

- <Each thing the fix leaves standing, named in one line.>

<details><summary>Read the code in this order</summary>

<The stops, hot then warm then cold, per skills/pr-body.md.>

</details>
````
