---
name: reply
description: The shape of every reply to the user: what it opens with, how it handles a draft, its closing block, its links. Named by the gate on each typed prompt until read; nothing imports it. The words the user types are skills/shortcuts.md and the register is skills/short-form.md.
---

# The shape of a reply

A reply that finished a piece of work, whole. Every section below is one part
of it:

```text
Done: the review draft, on the standard preset, not quick. The reflector, the agent rereading every candidate, buys recall for $7.

Left: the Nit at line 88, which needs your call on the band.

`post`: send the draft to acme/app#42 as REQUEST_CHANGES; its commit and the workspace backup are already up.

[#42](https://github.com/acme/app/pull/42), [comment](https://github.com/acme/workspace/blob/main/projects/app/reviews/42-cache/1-0123456/comment_<model>.md)

TL;DR: seven findings, one Warning; waits on `post`.

All good
```

## What it opens with

- **Lead with the recommendation, after the `Done:` line where one opens the
  reply, and never offer an option you have just argued against.** The reader
  picks the thing you meant to rule out.
- Asked whether something is finished, answer for the work, what is unfinished
  first: an idle session is not finished work. The tell is `yes` followed by
  what is still open.
- **A reply ending a request's work opens on `Done:` and what landed, or on
  `Not done:` and what stopped it**, then each item held back per *What the turn
  did*. The user learns the request ended from that word, never by asking.
- Run the action; the user only says the word. They never open a terminal, so a
  command in a reply is a dead end.
- Say what the code does, not what it took to get there. What was tried and
  dropped belongs in the change's `plan.md`.
- **A message about another target than the one the session works on gets one
  line naming both, before any command that acts on it, and waits for the user
  to confirm.**
  A message meant for another chat reads the same as a new task, and work
  started on it is spent before the user sees the mix-up:
  `This session is on acme/app#42; this asks about acme/lib#7. Switch?`
  A pasted passage naming no target counts: before acting on a pasted passage
  the session did not write, grep a distinctive phrase of several words from it
  on one line, `grep -rlF --include='*.md' --exclude-dir=checkout '<phrase>'
  projects/*/changes projects/*/reviews`, and where the file it prints sits
  under another change than the session's, that line names both; where it
  prints nothing, the passage is read as about the session's own target.

## A draft

Every draft shown, pasted between two rules, never linked:

```text
The body now reads:

---

This job runs on a schedule only, and GitHub disables those after 60 days.

---
```

- Show the text before creating anything, again in the reply of every turn that
  edits it, or in the reply after the last agent returns where one still runs,
  and every time it is asked for, a question about where it lives included. A
  body, a reply, an inline comment, a commit message, a label, a rename. Show
  the whole artifact, never only the part that goes out and never only the line
  the edit changed: a draft shown again is what the user approves, never a
  recap.
- Answer a question about a draft in the reply, and leave the draft alone. Edit
  it when they say what to change, or when answering turns up a defect, which is
  applied and reported rather than offered.
- Text the user will paste elsewhere goes in a fenced block, which is what
  carries a copy button.

## What the turn did

- Where work remains, a reply finishing a piece of work names it on one `Left:`
  line above the closing block. Steps the turn ran stay out unless one changes
  what the user decides.
- Where the agent settled a decision per *Consent* in the workspace `AGENTS.md`,
  one `Decided:` line above `Left:` names each default it took.
- When a reply holds something back, a finding left out, a `SKIP` section or a
  step skipped, or leaves the user a choice between options, explain each one
  in that reply, unasked, before asking about it, with no `+` needed per
  `skills/short-form.md`: what it is, why it is held or open, whether a rule or
  the agent chose that, and each other option with its cost. A count, `left
  out` in a word line or a question that assumes the choice has told the reader
  nothing.
- A reply covering more than one topic rules them off with `---`, one before
  each topic after the first.
- **A list of lines landed or asked is one line per item: the file in backticks,
  a colon, then the fewest words that say what changes**, the question last:
  `` `skills/tools/src/lint.rs`: copied rules by opening clause. Build? ``

## The closing block

- When the work needs a decision only the user can make, per *Consent* in the
  workspace `AGENTS.md`, ask it through the harness's question tool where it has
  one, a choice about code excepted: every such decision of the turn in one
  call, the recommended option first and marked, after the explanation above.
  The reply carries no word for them.
- When a reply leaves the user a choice about code in a worktree or a
  checkout, ask it in the reply and offer `e` naming each tree it opens, so the
  user reads the code before answering; the TL;DR still waits on the answer.
- A first question about something new to build opens by restating it in one
  sentence that keeps the user's own nouns, in that same question and never in a
  turn of its own. The tell is a question already using a different noun for it:
  the user says their apps, and the question asks about documents.
- A decision label, `P4` or `S2` per `skills/change.md`, carries its heading
  beside it the first time a reply names it: `P4, keep the escrow as funded`. The
  user reads the reply, never the plan, and a bare label costs a turn asking
  what it is. After that the label alone reads faster.
- A publish never goes through the question tool: its word is typed, per
  Invariant 2 in the workspace `AGENTS.md`.
- Every word a reply offers, anywhere in it, is its own line with the word
  first: `` `m`: merge the site branch into main, then deploy ``. Never
  `Type m.`, never a word inside a sentence, never an emoji ahead of it, since
  the reader scans the left edge for what to type. One line per word offered,
  each from `skills/words.md` or coined per its rule, `p` for a push and
  every publish it hosts, never two words to type in turn. The clause after
  the colon is imperative and names every destination it covers: what opens,
  in which repository, against which base, and whether it opens as a draft or
  ready.
- Before offering a word that pushes, `p`, `pr`, `pf` or `rlp`, write one
  `Confidence:` line directly above the first such word line: how sure this session
  is, out of 10, that what goes out is right, as three scores, `total`, `fix`,
  that the code does what it claims, and `design`, that its shape is the one
  to keep. `fix` and `design` each read `-` where the push carries no code.
  `total` is judged on its own, never their average. Then `no need to reverify`, or
  `reverify` and each diff, test run, CI job or capture going out that this
  session never opened itself, whoever ran it, or opened and could not
  confirm. Any such part holds the score
  at 7 or below, closes the reply on `Not all good` and goes on no `Left:`
  line, the cap falling on `total`. `Confidence: total 9/10, fix 9/10, design
  8/10, no need to reverify`; `Confidence: total 6/10, fix 8/10, design 7/10,
  reverify the lint job, whose output this session never opened`.
- When a reply leaves a design choice about code whose wrong pick costs more
  than redoing the work, per *Consent* in the workspace `AGENTS.md`, open it
  on a line of its own reading `**Your call:**`, then the choice, the current
  pick and the other way with its cost, in place of the `Left:` line for that
  choice and where `Left:` would sit, so it stands out from the defaults
  `Decided:` names; the closing status reads it as a decision waited on.
- When a reply hands over a reviewer's comments, give each two confidences in
  the same form, `problem 9/10, fix 8/10`: that the problem it names is real
  and worth the change, and that the fix applied for it is right, or for one
  left unapplied that the reason holds, each with the run that shows it or the
  check still missing.
- When a reply ends on a status or links table, put the word lines directly
  above it, one for every action that table leaves pending: `p` while anything
  in it is unpushed, and the coined word of every next step the reply proposed.
  The user reads the table for where things stand and the lines beside it for
  what to type, so a word left in the prose costs a turn asking for it.
- Before a reply in a summarized session says nothing waits, or answers what is
  left, list every topic the session opened, from the summary and from the
  commits the session made, `git log --since=<session start> --format=%s`,
  never the current task alone.
- Then the artifacts, in the order *Layout* in `workspace.md` gives them. A
  closed or merged target keeps its link and loses its verb. Each is a
  `[label](<url>)` into the workspace repo's `blob/main`, or a `[label](<path>)`
  relative to the working directory where the harness opens such a link in its
  own pane; never a bare path or a command. Emoji: 📋 ▶ only.
- Each fact is stated once. The opening line, `Left:`, `Decided:`, the word
  lines and the TL;DR each say something the others do not, and a later line
  repeating an earlier one is cut, the TL;DR and the closing status excepted.
- When the user ends the session, with `pause`, a goodbye or `retro`, the reply
  carries a `Retro:` block above the links, on the session's way of working
  and never its results: what slowed or failed it and why, what worked, and
  the one change for next time or `none`, a line each, read from the session's
  commits and the transcript's tool results. It names the change and makes
  none in that reply. A session that was one review round alone takes that
  round's `## Retro` instead. This block is the one part *The reply* in
  `skills/short-form.md` lets a reply carry unasked. A reply ending a
  request's work, once nothing it started still runs, offers `retro` on the
  last word line.
- Under the links, the `TL;DR:` line, where `skills/short-form.md` asks for one. A turn
  waiting on the user ends that line on `` waits on `<word>` ``, and only such a
  turn does, since the desktop notification for a waiting turn shows that
  line.
- A reply ending a request's work closes on its status: `All good` when
  nothing failed, went unchecked or was left open, else `Not all good` and
  which. CI not yet finished on a push, queued, running or awaiting approval,
  leaves it `All good`, named on `Left:`. A word or a decision waited on is no
  fault: the word stays on the `` waits on `<word>` `` tail, the decision on
  `Left:` or `**Your call:**`, while other work on `Left:` makes it `Not all good`. The status is
  the reply's last line, alone, under the links and the `TL;DR:` line where
  the reply carries one, so the user never has to ask whether everything is
  fine.

## Links

- A reply from a turn that wrote something, an edit, a commit, a push or a post,
  ends on the links, pushed or not. A file whose push has not landed
  keeps its link and says so beside it, since that URL 404s until the sha is
  reported.
- **One target's links run on one line. Several take a table, one column per
  target**, or per category where the work had no target, the links inline in each
  cell.
- The target is a link every time it is written, a table header included. A
  bare `#42` autolinks against whichever repository renders the reply, which
  is the workspace and not the target, so it resolves to an issue nobody opened.
- Write a pull request's head branch in backticks beside it every time a reply
  names the pull request, a table row and a table header included, read from
  `gh pr view <n> --json headRefName`: the user reaches the work through the
  branch, in the editor or a checkout, and a number alone costs them a lookup.
- A commit is reported as its link in the closing links,
  `[acme/app/3f680fa](<url>)`, never as a list of its own above them.

## A status table

- Read every table a reply carries back as its critic before sending it, asked
  for or not: whether the plan its rows lay out is still the one you would pick
  with every row in view, which cell rests on a title, a name or a keyword match
  rather than on reading the thing it sorts, which number no command run this
  turn printed, which command that built it errored or was patched, and which
  rows overlap. What the read finds changes the table, estimates marked as such,
  and one line under it names what the read changed, or that it changed nothing.
- **When the user asks for a table, give each row what it takes to understand
  it without opening anything else**: the target as a link, one plain line on
  what it fixes or does, its overview linked where one exists, what changed
  since the last report, what the user decides or does next, and what it leaves
  open. A row that sends the reader to three files to learn what it
  means has not saved them the reading.
- **When the user asks for a table of their pull requests, list every draft,
  one row each, with every link they need to open it**: the pull request, its
  overview, its plan and design record where they exist, its findings, and what
  is still to fix, linked to what shows it. A cell with nothing reads `—` and
  the column stays, so the table reads the same every time. Still to fix is a
  finding no commit closed, a finding held for a decision, or a limit of the
  fix, never what the bug does while the fix waits.
- **Order those rows by impact for the review time**: severity band first,
  critical down to none, then the shorter review first within a band, both
  shown in their own column, so the first row is the most security the reader
  buys per hour.

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

- While an agent or a background command the request started still runs, end
  the turn on the forecast line alone: no question, no word offered, no
  decision. Every question and every word goes in the one reply after the last
  of them returns, so one `p` covers the whole request. The tell is a closing
  block reading `still running` above a word to type.
- A linked session's note gets no relay: the user reads that session. Reply to
  one only where its result unblocks a step of this session's own work.
- Detach every side session this one starts, with `detach_session` once it
  runs, unless its result unblocks a step of this session's own work; a refused
  or unavailable detach leaves it linked, under the line above. A detached
  session is no agent this section waits on: it holds no turn open and gets no
  forecast line.
- Re-dispatch every agent that died, before anything else, on `continue` and on
  any turn that resumes the work.
- Before dispatching agents, project the request's spend in dollars from the
  last comparable run, `./scripts/session-tokens.py <session>` reading it, and
  past $50 ask before launching: the projection, what a cheaper shape drops,
  and the question. Past $50 spent mid-request, stop and report the total.
- Dispatching agents ends the reply with one forecast line: what went out and
  how many, the minutes and tokens the last measured round of that shape took,
  when to expect them back, and that `stop` kills them. Their return gets the
  same line with what was spent.
- **Report long work on its own stage boundaries, a background command of your
  own and a long foreground turn included, on the harness's task list where it has one, else one line at each task boundary, and set the fallback timer at a quarter of the forecast, never
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
