---
name: pr-body/several-changes
description: The pull request body for several independent changes sharing one pull request. Read whole once skills/pr-body.md has picked this shape.
---

# Several independent changes

One `### <symbol>: <one-line diagnosis>` section per change, separated by `---`.

- Two or three framing paragraphs after the `In short:` part of `skills/pr-body.md`, where present: what the changes share and what none of them is, in the reader's terms. Then a one-line bridge counting what follows.
- Each section carries its own symptom, mechanism and fix as a property of the new code, and a diagram where the reader would otherwise assemble the shape in their head, per *Diagrams* in `skills/pr-body.md`.
- What was proved goes in the section it belongs to. Where several sections share one method, one closing section names the method once and gives one row per section.
- A section naming another change, in this pull request or another, says what the two have in common in one sentence and stops.

## Skeleton

```markdown
In short: <What breaks and when, the one term a newcomer needs, how each fix works as a before and after, per *In short* in skills/pr-body.md.>

<details><summary>Topics you should know</summary>

<Each topic the reader needs, a few sentences each, per skills/pr-body.md.>

</details>

<What the changes share and what none of them is, in the reader's terms: two or three paragraphs.>

<One line counting the sections that follow.>

---

### <symbol>: <one-line diagnosis>

<Symptom, mechanism, then the fix as a property of the new code.>

<A diagram, where the reader would otherwise assemble the shape.>

---

### <symbol>: <one-line diagnosis>

<The same parts.>

---

### How each was proved

<The method the sections share, once, then one row per section.>

<details><summary>Read the code in this order</summary>

<The stops, hot then warm then cold, per skills/pr-body.md.>

</details>
```
