---
name: pr-body/docs
description: The pull request body for a change to documentation pages, however many. Read through ./scripts/skill pr-body/docs once skills/pr-body.md has picked this shape.
---

# A docs change

The pages are what the reader reads, so the body never restates what they now say. No headers, no section per correction, no count to hit; one change spanning a dozen files still takes this shape.

- Open on the fact the pages had wrong, stated as the fact and never as the correction, in the reader's terms: what the flag is, what the chain does.
- Then what the error cost the reader, in numbers: what the pages asked for against what holds.
- One paragraph per class of correction, each naming what was wrong and what it cost, and never what the page now says.
- Close on the riders in one paragraph, each with its own why.

These four parts are the whole body between the overview and the `Fixes` line above and the reading order block that closes every body. The general order of `skills/pr-body.md` does not reach past them: no paragraph on the approach chosen, on an overlapping pull request, on what the change leaves out or on what was verified. Each of those goes in `plan.md`, or to the user in the handover.

Why: a reader of a docs diff sees the corrected pages themselves, so a body that paraphrases them is read twice and the defect that made the change worth merging is read once.

## Skeleton

```markdown
<The fact the pages had wrong, stated as the fact.> <What that cost the reader, in numbers: what the pages asked for against what holds.>

<One paragraph per class of correction: what was wrong and what it cost.>

<The riders, in one paragraph, each with its own why.>

<details><summary>Read the code in this order</summary>

<The stops, hot then warm then cold, per skills/pr-body.md.>

</details>
```
