---
name: pr-body/surface
description: The pull request body for one change with a surface someone sees, a front-end feature or a change to what a page renders. Read through ./scripts/skill pr-body/surface once skills/pr-body.md has picked this shape.
---

# One change with a surface someone sees

The decisions are what the reader gets rather than what the code does, so the headings carry the skim and no count binds the length. A change with no such surface takes `skills/pr-body/one-concern.md`, whatever the number of decisions behind it.

- `Fixes #n` alone on the first line where an issue closes, then one line crediting a handover where there is one.
- `## Problem`, two or three short paragraphs: what the reader sees today, then why it is a defect. The shot sits here, under a blockquote caption naming what it shows and what produced it, per *Visual evidence* in `skills/pr-body.md`.
- The design page where one exists, linked on its own line above the first `###`.
- `## Design`, one `###` per decision a reviewer could have made differently: what the reader sees, the interface, who it answers, what it costs, what is left out. A `###` carrying one sentence is not a decision: fold it into its neighbour.
- The parts a reviewer should open go as inline comments on the diff, one per part, per `skills/review-comment.md`, never as a section of the body.
- Where the body uses role words, it closes on the Glossary block per *Shape* in `skills/pr-body.md`.

Why: a reviewer of a surface decides on what a person will see, and a heading per decision lets them stop at the one they would have made differently.

## Example

```markdown
## Problem

A govDAO vote runs code, and the page a member votes from does not link that code. This is a security change and not a redesign.

The realm holding it is on the page: `Executor created in: gno.land/r/gov/dao/v3/impl`, the last line of the proposal's prose. It is not a link, so reading the code means copying the path out and finding its source view by hand.

Nothing separates that line from the description above it, and the description is markdown the proposer wrote. It can carry a line of the same shape, or a link, pointing at any realm it likes. A member reading one block of prose cannot tell the page's statement from the proposer's, and the one that is worth trusting is the one that is not a link.

> gnoweb rendering the same member proposal, master on the left and this branch on the right.

![on master the three lines follow each other with no heading between them and the realm in plain text; on this branch the page carries a Description section, a rule, then an Execution section whose first line names the realm as a link](https://raw.githubusercontent.com/davd-gzl/agent-artifact/main/gno/govdao-executor-section/proposal-page-before-after.png)

## Design

### Two sections, not a page rework

The proposer's prose goes under `### Description`, the executor's realm and its description under `### Execution`, with a rule between them. Both sections come from [#5051](https://github.com/gnolang/gno/pull/5051), which reworked the whole page and named the second one Execution Details. Nothing else is taken from it. `StringifyProposal` prints the same section, so the page and the text form cannot drift apart.

### Which values become a link

[`CreationRealm()`](https://github.com/gnolang/gno/blob/24ce73d6f/examples/gno.land/r/gov/dao/v3/impl/render.gno#L195-L214) comes back through the public `dao.Executor` interface, so an executor returns any string it likes. It [becomes a link](https://github.com/gnolang/gno/blob/24ce73d6f/examples/gno.land/r/gov/dao/v3/impl/render.gno#L220-L239) only as a package path this chain serves: the chain domain whole, a letter directory of `r` or `p`, then segments matching the grammar the VM enforces on deployed paths. Every other value keeps today's escaped code span, a realm on another chain and an `/e/` run realm included.

### What the link claims

Where the code is, and nothing more. Only `SimpleExecutor` has its realm captured by the VM, so the link is not evidence that this realm is the one whose code runs. The escaping is what holds against a hostile value, and it is unchanged: clamp, escape, then link only over a value the grammar accepted.

A description can still write a line of the same shape, since it is markdown by design. What it cannot do is be the section: the page emits `### Execution` itself, after the description, and the link in it is the one the page built.
```

Provenance: the shape is [meet#1619](https://github.com/suitenumerique/meet/pull/1619), which carries the `Fixes` line, the handover credit and the Glossary; the body above is [gno#6149](https://github.com/gnolang/gno/pull/6149), with the image's alt text shortened.
