---
name: reply
description: The shape of every reply to the user: what it opens with, how it handles a draft, its closing block, its links. Named by the gate on each typed prompt until read; nothing imports it. The words the user types are skills/shortcuts.md and the register is skills/short-form.md.
---

# The shape of a reply

A reply that finished a piece of work, whole:

```text
Done: the review draft, seven findings, one Warning.

Left: the Nit at line 88, which needs your call on the band.

`/post`: send the draft to acme/app#42 as REQUEST_CHANGES

[#42](https://github.com/acme/app/pull/42) `fix-cache`, [comment](https://github.com/acme/workspace/blob/main/projects/app/reviews/42-cache/comment.md)

TL;DR: seven findings, one Warning; waits on `/post`.

All good
```

## What it opens with

- Lead with the answer or the recommendation, and never offer an option just argued against.
- A reply ending a request's work opens on `Done:` and what landed, or on `Not done:` and what stopped it.
- Say what the code does now, not what it took to get there.
- Run the action and leave the user only the word: they never open a terminal, so a command in a reply is a dead end.
- Before acting on a message about another target than the one the session works on, name both in one line and wait for the user to confirm.

## A draft

- Show every draft whole between two `---` rules, before anything goes out and again in each turn that edits it: a body, a comment, a commit message, a label.
- A question about a draft is answered in the reply and leaves the draft alone, unless answering finds a defect, which is fixed and reported.
- Text the user will paste elsewhere goes in a fenced block.

## The closing block

- `Left:` names what is not done or not checked, one line; `Decided:` above it names each default the agent took.
- Anything held back, a finding left out or a step skipped, is explained unasked: what it is, why it is held, and whether a rule or the agent chose that.
- A choice only the user can make is explained, each option with its cost, then asked once; a publish is never asked through the question tool, since its word is typed.
- Before a reply in a summarized session says nothing waits, list every topic the session opened, from the summary and from `git log --since=<session start> --format=%s`.
- Every word offered is its own line, word first, then an imperative naming every destination: `` `/p`: push `fix-cache` to acme/app, updating #42 ``.
- Above a word that pushes, one `Confidence:` line: how sure this session is, out of 10, that what goes out is right, and each part going out that no command this session checked.
- Handing over a reviewer's comments gives each `problem n/10, fix n/10`: that the problem is real, and that the fix applied for it is right.
- A table the user asks for gives each row what it takes to understand it without opening anything else. A table of their pull requests lists every draft, one row each, with every link needed to open it, ordered by severity, then by the shorter review.
- When the user ends the session, with `pause`, a goodbye or `retro`, a `Retro:` block names what slowed the session, what worked, and the one change for next time.
- The last line is `All good`, or `Not all good` and what failed, went unchecked or was left open.

## Links

- A turn that wrote something, an edit, a commit, a push or a post, ends on links to what it wrote, each a `[label](<url>)`, never a bare path. A pull request is always a link, with its head branch in backticks beside it.

## Agents

- While agents the request started still run, end the turn on one forecast line: what went out, when to expect it back, and that `/down` kills it. Every question waits for the reply after they return.
- Before dispatching agents, project the spend from the last comparable run, `./scripts/session-tokens.py <session>`, and past $50 ask first; past $50 spent mid-request, stop and report the total.
- Report a count with its cost, at the rates *Capabilities* in `workspace.md` names.

## Repairs

- Correcting published text edits it to say the right thing and nothing else: no "an earlier version claimed".
