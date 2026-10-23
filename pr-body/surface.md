---
name: pr-body/surface
description: The pull request body for one change with a surface someone sees, a front-end feature or a change to what a page renders. Read through ./scripts/skill pr-body/surface once skills/pr-body.md has picked this shape.
---

# One change with a surface someone sees

The decisions are what the reader gets rather than what the code does, so the bold lead-ins carry the skim and no count binds the length. A change with no such surface takes `skills/pr-body/one-concern.md`, whatever the number of decisions behind it.

- `Fixes #n` alone on the first line where an issue closes, then one line crediting a handover where there is one.
- `## Problem`, two or three short paragraphs: what the reader sees today, then why it is a defect. The shot sits here, under a blockquote caption naming what it shows and what produced it, per *Visual evidence* in `skills/pr-body.md`.
- The design page where one exists, linked on its own line under `## Design`.
- `## Design`, one paragraph per decision a reviewer could have made differently, opening on the decision in bold inside its own sentence, never as a heading above it: what the reader sees, the interface, who it answers, what it costs, what is left out. A decision carrying one sentence is not a decision: fold it into its neighbour.
- The parts a reviewer should open go as inline comments on the diff, one per part, per `skills/review-comment.md`, never as a section of the body.
- Where the body uses role words, it closes on the Glossary block per *Shape* in `skills/pr-body.md`.

Why: a reviewer of a surface decides on what a person will see, and a bold lead-in per decision lets them stop at the one they would have made differently.

## Skeleton

```markdown
Fixes #<issue>

<The handover credit, where there is one.>

## Problem

<What the reader sees today.>

<Why that is a defect.>

> <What the shot shows and what produced it.>

![<the before and after, described>](<image URL>)

## Design

<The design page, where one exists.>

**<The decision, in bold inside its own sentence>**: <what the reader sees, who it answers, what it costs, what is left out.>

**<The next decision>**: <the same parts.>
```
