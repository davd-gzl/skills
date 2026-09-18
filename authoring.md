---
name: authoring
description: Use when adding, editing, or removing a rule in any AGENTS.md, harness dotfile, or skill file. Defines where a rule lives, the shape it takes, and what it displaces.
---

# Authoring a rule

Every rule costs attention on every turn that loads it, and the corpus is read
by a model with a finite budget for it. What decays is the set loaded at once:
past a few dozen rules in one context the reader samples, omission first, and a
file that holds every rule ever written enforces none of them. So a rule earns
its place against the rules already loaded beside it, and adding one is a trade.

Every skill has one goal beside its task: the same decision in fewer turns. A
turn re-sends the whole context, so the turn count times the context is the
cost, and output tokens are the minor term. A rule that cuts words and adds a turn has
raised the cost; one that batches reads, hands a value the agent would have
fetched, or settles a step in one call has cut it. The decision stays equal or
the rule is not an upgrade: the outcome table, the finding set and the reply's
own numbers say whether it did, never the rule's wording. State the turns a
rule removes beside its estimate, per *A change to the run's shape*.

Run `./scripts/rules lint <files>` before committing any edit here. It warns and
never blocks: a rough rule lands, and a later pass fixes it.

## Where it goes

| The rule is about | It lives in |
| --- | --- |
| An action that cannot be taken back: a publish, a push, a delete, a rewrite | The Invariants section of the workspace `AGENTS.md` |
| What waits for a word, and which repo a push may reach | The workspace `AGENTS.md` |
| One task, whatever the repository: reviewing, drafting a body, filing an issue | The matching `skills/<task>.md` |
| Visible prose of any kind | `skills/writing-style.md`, which every other skill defers to |
| What the user's words start, and the shape of a reply | `skills/shortcuts.md` |
| One repository: its merge style, its CI, its glossary, its boot recipe | `projects/<repo>/AGENTS.md` |
| What this machine can do | No file. It is a command, see *Capabilities* |
| A rule a harness offers to keep in its own memory store | No file it owns. The corpus holds every rule, so it goes to the row above it |
| A measured fact, a decision, the state of the work, the user's priorities | A knowledge file, the change's `plan.md`, the `TODO.md`, a config doc: files the checkout carries to any device. The harness memory directory stays empty, since a run that leans on it works on one machine |

One home each. A rule worth stating in two files is one rule stated in the
broader file and linked from the narrower, and the lint reports the copy. A
prompt delegating a task to an agent names the skill file and never restates
its steps.

A rule about a repository never goes in the core skill, and a rule about every
repository never goes in one project's delta. Both mistakes read as correct
until someone works in the other house.

## The shape

Name the action, not only its absence. `Push the submodule in the command that
commits it` beats `never leave a submodule commit unpushed`: the first says what
to type, and a reader takes a prohibition for the action it names often enough
that the negative form stays only where no action replaces it, a publish that
must not happen having none. The corpus health table counts how far that has
drifted.

Put what matters first and last. A reader weighs the opening and the close of a
file and loses the middle, so the rule whose violation costs most opens its
section, the one read at the close ends it, and the middle holds what a reader
can miss once.

Open with the trigger. The first clause says when the rule fires, so a reader
whose task does not match skips the rest in one glance. `Before pushing a parent
that moved a gitlink, confirm the commit resolves on the submodule's remote.` A
rule whose trigger is every turn belongs in Invariants or nowhere.

One rule, one bullet. A bullet carrying two rules is followed for whichever half
the reader sampled. Split it.

State it, then stop. The reason belongs in the rule only where the reader would
otherwise apply it wrongly. What does not belong: the session that produced it,
the sha it was found on, the date, what was tried first, the knowledge file or
the paper behind it. That record is the artifact's, a `plan.md`, a `claims.md`,
a commit message, and the lint rejects a date or a bare sha in a rule line.

Cut the draft before committing it. A rule arrives carrying the round that
produced it. Read it back and delete every sentence that is not the trigger, the
action or the tell; what it cost and what was tried first go in the commit
message. A rule is cut once, here, at the length it keeps.

Read a new rule against the mistake that earned it, and keep it only if it
forbids what you did. A rule drafted in the turn it was earned comes out shaped
to excuse that turn: `may`, `where justified`, `unless the context differs`
license the next reader instead of constraining them. Write the one that would
have stopped it.

Write what a measurement means, and the command, never the reading. A count, a
duration or a version frozen into a rule is right on the day it is taken and
wrong afterwards, while the reader trusts it because it is specific. Keep the
conclusion it supports and name the command that prints it fresh.

Key a rule on the property a count stands for, never on the count as a limit. A
ceiling on lines, files, agents, minutes or shell commands admits a change on
one reading of the count and refuses it on another, and says nothing about what
the change reaches. Name the property, a consumer outside the package, a
surviving Warning, a command that changes what a later session reads, and the
command that prints it. The three counts of `skills/writing-style.md` measure a
sentence, not the work, and stay.

Bold is a rank, not a voice. It marks the rules whose violation cannot be
undone, and nothing else in a skill file; when most bullets are bold the file
has stopped ranking and the reader is back to sampling. The health table prints
the share.

Write the reader's words, per `skills/writing-style.md`. Every rule here is read
by someone who has not seen the incident behind it.

A rule that names a new home for visible prose names the writing-style section
it defers to. Its reader stops at the new rule and takes it as the whole spec
for that place, so what `skills/writing-style.md` already requires there, the
link on every named thing for one, is lost unless the rule points at it.

## A skill file

The reader is a model that samples what it reads, so the file is shaped for
one pass.

- Frontmatter first, `name` and `description`, the description naming what
  the file produces and every situation that reaches it. The harness picks a
  file from that line alone and leans toward not picking, so a situation the
  description leaves out never reaches the file; the body never restates when
  to use it.
- One example before the rule, wherever a worked line, a command or a shape
  lands it in one read, and never a list of them: a second example is read as
  the rule's whole range, and past a few they cost more than they teach.
  `skills/pr-body/one-concern.md` opens on the shape and closes on the body it
  came from.
- A table of contents at the head of a file a reader opens for one section,
  `skills/review.md` for one: one line per section naming the moment it is read.
- A word the user types is defined in `skills/shortcuts.md` and nowhere
  else. Another file names the word and points at that table; a second table
  drifts from the first, which the lint reports as a copy.
- A file whose sections fire at different moments declares its reader's set in
  its frontmatter, `prompt-sections: [<heading>, ...]`, and the gate hands that
  cut, rebuilt whenever the file changes, so the reader loads its own moment and
  no other's. A heading the list names and the file has since renamed falls back
  to the whole file. Split into a second file only where the sections are
  separate documents to whoever edits them. `./scripts/skill <name>` prints the
  path the gate hands over.
- A skill the root `CLAUDE.md` imports is never cut, whatever its frontmatter
  says: the harness loads it whole as the session opens, and every turn runs on
  it. The gate hands the file and a `prompt-sections` line there changes nothing.

## Capabilities

What the machine can do is measured, never written down: `./scripts/env-check.sh`,
per *Capabilities* in `workspace.md`, which carries why a recorded capability goes
stale. A rule needing one of those facts names the command and lets the reader
read the answer. The lint blocks the clause that records one instead, `stop
re-deriving` and its neighbours, and warns wherever a capability is named with no
command beside it.

What does get written down is what a command cannot show: which recipe worked,
what a failure looked like, the fixture a manual test needs. Those go in
`projects/<repo>/AGENTS.md` with their symptom, per *A project's file* below.

## A project's file

`projects/<repo>/AGENTS.md` holds what was measured about one repository. Read it
before the first task there, and write to it in the same turn a fact is measured,
unasked. Never offer the recording as a next step.

- Conventions, each with the command that produced it: merge style, commit
  granularity, subject and body shape, changelog placement and selection, issue
  title style, which CI signals lie, every trap that cost a round. A convention
  read off the repository's documentation, or inferred from its commit format, is
  not measured.
- A glossary, filled while first reading the code: the term the codebase
  uses, the words a reader outside the project has for the same thing, and the
  few where the project's own name is unavoidable. Fill it during that first
  read, never while editing a draft, because a term stops looking like jargon to
  whoever just read the file defining it. Every posted string then takes its
  words from the right-hand column, per *Write the reader's words* in
  `skills/writing-style.md`.
- What a session cost to find: how the project runs locally, the fixture or
  seed data a manual test needs, the version and system package a build required,
  the error a wrong one prints. Each entry carries its symptom, so the next
  session recognises the failure before diagnosing it again.

A delta file for a skill sits beside these, short, opening by naming the core
file it overrides. Work under `projects/<repo>/` reads the delta plus the core,
and the delta wins where they disagree.

## A project's context

`projects/<repo>/CONTEXT.md` holds what the user knows about one repository and
no command measures: where the project stands, what it is for, how each person
on it works, and the pace a review takes from that. It is loose on purpose, a
line per fact in the reader's words, so it fits every project and every person
rather than one. Create it on the first task in a project, unasked, from what
the user has said, and write to it in the turn a fact arrives: the user states
it, or a round observes it, an author asking twice for the same thing for one.
A fact with a command behind it goes to `AGENTS.md` beside it instead.

- Where the project stands: the phase, a launch weeks away or a quiet
  stretch, and what it is trying to become, in two or three lines.
- The people: one line per login, how they work and what they want from a
  review, a test in every finding, no nits, the decision in the first line.
- The review pace: what the phase sets, in the terms *Fetch & understand*
  in `skills/review.md` reads: how many rounds, how fast, on which path.

The file is private, per Invariant 5 in the workspace `AGENTS.md`. Every change
to it gets a dated entry at the top of `context-log.md` beside it, one or two
lines, what changed and where it came from, so the next session sees what the
project looked like before.

## What a new rule displaces

Adding is the easy half. The corpus grows on its own and shrinks only on
purpose, so every edit that adds a rule answers one question in its commit
message: what came out, or why nothing did.

A rule leaves when any of these holds:

- A script or a linter now enforces it. The rule becomes a line in that script.
- Two rules say the same thing in different words. Keep the one whose trigger is
  clearer and delete the other, rather than cross-referencing them.
- It is a narrow case of a broader rule already present. Widen the broader one
  if it does not quite cover it, then delete the narrow one.
- It names a file, flag, script, or service that no longer exists. Check before
  believing it: `git grep` the name.
- It restates what the tool already refuses to do.

A file splits on its trigger, never on its size. A section that fires at a
different moment from the rest of its file, a reply beside repository rules,
booting beside reviewing, is its own file, read when that moment comes and
named in the index. A rule leaves only for the reasons above, never for the
count, since a cut for length cannot tell the fact from the filler.

`./scripts/rules lint` prints every file's word count and its median words per rule,
and neither is a cap. Past 75 words a rule is carrying the session that found it
rather than the fact: cut that clause, never the measurement.

## Contradictions

Two rules that cannot both be followed cost a decision on every turn, and the
model resolves them silently, differently each time. Resolve them in the file.

Precedence, when a conflict survives a rewrite:

1. The user's instruction in the current turn.
2. The workspace `AGENTS.md` Invariants.
3. `projects/<repo>/AGENTS.md`, the delta for the repository being worked in.
4. The task skill in `skills/`.
5. `skills/writing-style.md` for prose, which the task skill defers to.

A skill that means to override the layer above says so in the rule itself,
naming what it overrides and where. An override nobody wrote down is a
contradiction wearing a hat.

## Measuring a rule

A wording whose effect is in doubt is measured before it lands, the whole run
designed before the first call: isolation flags first, `--tools ""
--strict-mcp-config --disable-slash-commands --setting-sources ""`, since a
plugin hook or a skill injection contaminates every answer and `--bare` drops
OAuth; every variant in one run at effort `medium`; one blind judge pass, labels
hidden and order shuffled, on single-pass readability and substance kept.
`skills/archive/chat-register/` is the harness that measured *Short form*, kept
as the record of that run.

A published result is one measurement on its own models, benchmarks and date:
the knowledge line carries those conditions beside its number, and a rule drawn
from it is measured here before it is trusted.

## Editing this corpus

- `skills/` is the canonical repository, `davd-gzl/skills`, mounted as a
  submodule in every workspace. Edit here, never in a copy.
- **`skills/` is public and generic: no secret, no private name and no local
  path in any file or commit message here.** A token, a hostname, a private
  repository, a person, a round number or an absolute path is disclosed the
  moment it is pushed. A fact naming one consumer lives in that consumer's tree,
  `workspace.md`, `workspace.json` or `projects/<repo>/AGENTS.md`, and a skill
  names that file, never the value. `skills/scripts/scrub.sh` runs from the
  pre-push hook over every line a push adds and refuses the push on a hit;
  `--tree` reads the whole tree the same way.
- Read the whole file before changing a rule in it. A range read against the two
  sections a task seems to need is how a section gets missed.
- Re-read after `git -C skills log -1` shows a commit that was not there before.
  Another session moves the pin mid-turn.
- A rule that proved unclear, missing or wrong during use is corrected in its
  file in the same turn, before the work that exposed it continues.
- A knob, a stage or a word that a change renames is grepped across `skills/`,
  `scripts/workflows/` and the README before the commit, since the old shape
  stays stated wherever the grep is not run.
- Run `./scripts/rules lint` over every file the edit touched, plus the workspace
  root `AGENTS.md`, and fix what it reports rather than narrowing what it reads.

## A deterministic step is a tool

A step whose answer a program can compute is a tool under `tools/`, named by
the skill and never asked of a model: resolving a link at a sha, re-anchoring a
line through a diff, ranking files, cutting a diff into bundles, writing a table
from verdicts, checking that a cited line exists, counting, sorting,
deduplicating by key. A model does such a step slowly, at a price, sometimes
wrongly, and a wrong table nobody can reopen is worse than none; the tool does
it in a second, the same way every time, and its test pins the way. The rule
holds where the step is small: a check the writer runs costs one call, a check
the model is trusted to have done costs the reader.

- When a skill's step reads as "list", "resolve", "rank", "cut", "join", "count" or "check that", ask what the input and the output are; if both are files, it is a tool.
- The tool exits non-zero on what it finds and the skill says what the agent does with the exit, so a miss is never a line in prose the next stage may skip.
- The skill names the command with its arguments and reads nothing the tool already settled; the crate's README carries the contract and the tests carry the examples.

A write gets a verb; a read stays free. Changing a tracked artifact goes
through a named script under `scripts/`, never a shell line composed in the
turn: committing, pushing, posting, editing the `TODO.md`, tagging a draft,
sweeping a round. A shell line is written once, from memory, under no test, and
its next reader cannot tell a deliberate choice from a typo. Reading stays
unrestricted, `grep`, `git log`, a count, a probe: the Principles ask for a
measurement taken this session, and a verb nobody wrote yet is no reason to
answer from memory. Where a write has no verb, write the verb.

## A change to the run's shape

A rule that moves a stage, a tier, a cap, a batch, a read order or an agent
count is handed over with its estimate: turns per agent, output tokens, cache
read, cache write and minutes per round against the last measured round, as
`./scripts/review-plan.py` projects them, and the direction of the finding
rate, each a number and each marked estimate until the outcome table measures
it. An estimate in output tokens alone measures the minor term,
`./scripts/review-retro.py` printing the split per stage. A change with no
estimate is a change nobody can judge.

## Upgrading from the TODO

`upgrade skills` runs on the strongest model available and takes the
workspace's `TODO.md` line by line, newest first. Nothing is pushed but the
marker commit.

- Before any line's work, the lines the session takes get `Taken: <the
  session's start sha>` at their end, in one commit pushed first, since another
  session reads the list only from the remote; a line another session marked is
  skipped, and a marker whose line did not land leaves in the closing commit.
- A line about a project, a defect, an issue to file, a target's behaviour, a
  recipe or a catalog, moves as it stands into that project's tree, per
  *Writing it down* in the workspace `AGENTS.md`, and is named in the closing
  list.
- Each line is read as its critic before any work: does the check it names
  still hold, does the rule it proposes fit the corpus, does what it costs pay.
- A line that passes becomes a rule, per *Where it goes* and *The shape*, with
  what it displaces named, or a script where a command can enforce it; one
  commit per line, its message the line's substance and its estimate per *A
  change to the run's shape*, the line struck in that commit.
- A line that fails the read, whose check fails when run, or that a rule
  already covers goes to the user as one question, the line and the objection,
  and waits for the word; the session's own judgement never strikes it.
- A line whose work is a run or a capability not yet there stays, with `Waits:`
  and what it waits on.
- The session ends on what landed, what was asked and what was struck, then a
  verdict on every line that stays, `Waits:` and project lines included: keep,
  strike, move or fold, each with its reason in one clause; the user's word
  strikes, never the verdict.
