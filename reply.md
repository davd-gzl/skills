---
name: reply
description: The shape of every reply to the user: what it opens with, how it handles a draft, the `Did:` block it ends on, its closing block, its links. Read by path at the turn that finishes work, since nothing imports it. The words the user types are skills/shortcuts.md and the register is skills/short-form.md.
---

# The shape of a reply

A reply that finished a piece of work, whole. Every section below is one part
of it:

```text
Standard preset, not quick. The reflector is what buys recall, and it costs $7.

Did:
1. Round 2 launched, 7 finders, ~12k in context
2. Draft and claims.md written, links checked, 40 lines rewritten
Left: the Nit at line 88, which needs your call on the band

📋 `post`: the draft goes to acme/app#42 as REQUEST_CHANGES; its commit and the workspace backup are already up.

| Target | Round |
| --- | --- |
| [#42](https://github.com/acme/app/pull/42) | [comment](https://github.com/acme/workspace/blob/main/projects/app/reviews/42-cache/1-0123456/comment_<model>.md) |

TL;DR: seven findings, one Warning; waits on `post`.
```

## What it opens with

- **Lead with the recommendation, and never offer an option you have just argued
  against.** The reader picks the thing you meant to rule out.
- Run the action; the user only says the word. They never open a terminal, so a
  command in a reply is a dead end.
- Say what the code does, not what it took to get there. What was tried and
  dropped belongs in the change's `plan.md`.

## A draft

Every draft shown, pasted between two rules, never linked:

```text
The body now reads:

---

This job runs on a schedule only, and GitHub disables those after 60 days.

---
```

- Show the text before creating anything, and again every time it is asked for,
  a question about where it lives included. A body, a reply, an inline comment,
  a commit message, a label, a rename. Show the whole artifact, never only the
  part that goes out.
- Answer a question about a draft in the reply, and leave the draft alone. Edit
  it when they say what to change, or when answering turns up a defect, which is
  applied and reported rather than offered.
- Text the user will paste elsewhere goes in a fenced block, which is what
  carries a copy button.

## What the turn did

- **A reply finishing a piece of work ends on a `Did:` block listing everything
  it did**, above the closing block, as plain lines, never fenced or quoted:
  one numbered line per step in order, a clause and never a sentence, carrying
  the step, what it produced, and what it put in context, so the heavy step
  shows. Then `Left:`, dropped when nothing is left.
- The prose above never retells a listed step: it carries the decisions to make
  and the word to give.
- A commit, a push or a sha is not a step. Name what changed and leave the shas
  to the prose and the closing block.
- A reply covering more than one topic rules them off with `---`, one before
  each topic after the first, and one above the `Did:` block.
- **A list of lines landed or asked is one line per item: the file in backticks,
  a colon, then the fewest words that say what changes**, the question last:
  `` `skills/tools/src/lint.rs`: copied rules by opening clause. Build? ``

## The closing block

- One bare verb, `post` never `post the issue`, and beside it what saying it
  does: what opens, in which repository, against which base, and whether it
  opens as a draft or ready. The sentence names every destination it covers.
- Where a publish and something already authorised are both pending, do the
  latter and offer the publish alone.
- Then the artifacts, one line each, in the order *Layout* in `workspace.md`
  gives them. A closed or merged target keeps its link and loses its verb. Each
  is a `[label](<url>)` into the workspace repo's `blob/main`, never a local
  path or a command. Emoji: 📋 ▶ only.
- Under it, the `TL;DR:` line every reply ends on, per `skills/short-form.md`.

## Links

- Every reply ends on the links, pushed or not. A file whose push has not landed
  keeps its link and says so beside it, since that URL 404s until the sha is
  reported.
- **Group them one table column per target**, or per category where the work had
  no target, the links running inline inside each cell. A row per file turns four
  artifacts into a screen the reader scrolls past.
- The target is a link every time it is written, a table header included. A
  bare `#42` autolinks against whichever repository renders the reply, which
  is the workspace and not the target, so it resolves to an issue nobody opened.
- **A reply reporting a publish opens with one line per commit that went out**,
  before any of it: `[acme/app/3f680fa](<url>)`, then about five words saying
  what the commit holds.

## Numbers

`12 agents, 329k output, 15.2M cache read, $21.80` beats `about twenty dollars`.

- **Report a count with its cost, at rates read in the same turn.** Where those
  rates are read is *Capabilities* in `workspace.md`. Name the tool each figure
  came from: a raw transcript sum double-counts a streamed message.
- **A saving takes the same count as a spend.** Count the turns the other shape
  removes before naming the figure.

## Agents

```text
▶ Four rounds running, 19 finders. The last round of this shape took 11 minutes
and 329k output. `stop` kills them.
```

- An agent's return is not a turn. Reply when the step it fed is finished, never
  per agent.
- Re-dispatch every agent that died, before anything else, on `continue` and on
  any turn that resumes the work.
- Dispatching agents ends the reply with one forecast line: what went out and
  how many, the minutes and tokens the last measured round of that shape took,
  when to expect them back, and that `stop` kills them. Their return gets the
  same line with what was spent.
- **Report long work on its own stage boundaries, a background command of your
  own included, and set the fallback timer at a quarter of the forecast, never
  under twenty minutes.** A wake-up re-reads the whole conversation, so frequent
  polling costs more than the work it reports on. Each wake says which stage and
  what it wrote, never a percentage:
  `./scripts/review-progress.sh <workflow-dir> <plan-minutes> <round-dir>`.

## Repairs

- Correcting published text means editing it to say the right thing and nothing
  else: no "an earlier version claimed", no strikethrough.
- Retry a permission refusal from the harness once: a classifier is not
  deterministic. A 403 `Resource not accessible by personal access token` is a
  missing scope, handled per `skills/review-comment.md`.
