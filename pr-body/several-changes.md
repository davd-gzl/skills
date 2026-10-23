---
name: pr-body/several-changes
description: The pull request body for several independent changes sharing one pull request. Read through ./scripts/skill pr-body/several-changes once skills/pr-body.md has picked this shape.
---

# Several independent changes

One `### <symbol>: <one-line diagnosis>` section per change, separated by `---`, each readable alone.

- Two or three framing paragraphs first: what the changes share and what none of them is, in the reader's terms. Then a one-line bridge counting what follows.
- Each section carries its own symptom, mechanism and fix as a property of the new code, and a diagram where the reader would otherwise assemble the shape in their head, per *Diagrams* in `skills/pr-body.md`.
- What was proved goes in the section it belongs to. Where several sections share one method, one closing section names the method once and gives one row per section.
- A section naming another change, in this pull request or another, says what the two have in common in one sentence and stops.

Why: a reviewer reads the section for the file they own and skips the rest, so a section that depends on its neighbour is read without it.

## Skeleton

```markdown
<What the changes share and what none of them is, in the reader's terms: two or three paragraphs.>

<One line counting the sections that follow.>

---

### <symbol>: <one-line diagnosis>

<Symptom, mechanism, then the fix as a property of the new code.>

<A diagram, where the reader would otherwise assemble the shape.>

---

### <symbol>: <one-line diagnosis>

<The same parts, readable without the section above.>

---

### How each was proved

<The method the sections share, once, then one row per section.>

<details><summary>Read the code in this order</summary>

<The stops, hot then warm then cold, per skills/pr-body.md.>

</details>
```
