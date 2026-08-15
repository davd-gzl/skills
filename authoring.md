---
name: authoring
description: Use when adding, editing, or removing a rule in any AGENTS.md, CLAUDE.md, or skill file. Defines where a rule lives, the shape it takes, and what it displaces.
---

# Authoring a rule

Every rule costs attention on every turn that loads it, and the corpus is read
by a model with a finite budget for it. A file that holds every rule ever
written enforces none of them reliably: the reader samples. So a rule earns its
place against the rules already there, and adding one is a trade.

Run `./skills/lint.py <files>` before committing any edit here. Errors block.

## Where it goes

| The rule is about | It lives in |
| --- | --- |
| An action that cannot be taken back: a publish, a push, a delete, a rewrite | The Invariants section of the workspace `AGENTS.md` |
| How the agent talks to the user, and what waits for a word | The workspace `AGENTS.md` |
| One task, whatever the repository: reviewing, drafting a body, filing an issue | The matching `skills/<task>.md` |
| Visible prose of any kind | `skills/writing-style.md`, which every other skill defers to |
| One repository: its merge style, its CI, its glossary, its boot recipe | `projects/<repo>/AGENTS.md` |
| What this machine can do | No file. It is a command, see *Capabilities* |

One home each. A rule worth stating in two files is one rule stated in the
broader file and linked from the narrower, and the lint reports the copy.

A rule about a repository never goes in the core skill, and a rule about every
repository never goes in one project's delta. Both mistakes read as correct
until someone works in the other house.

## The shape

**Name the action, not only its absence.** `Push the submodule in the command
that commits it` beats `never leave a submodule commit unpushed`: the first says
what to type. Keep the negative form only where no action replaces it, a publish
that must not happen having none, and the corpus health table counts how far
that has drifted.

**Open with the trigger.** The first clause says when the rule fires, so a
reader whose task does not match skips the rest in one glance. `Before pushing a
parent that moved a gitlink, confirm the commit resolves on the submodule's
remote.` A rule whose trigger is every turn belongs in Invariants or nowhere.

**One rule, one bullet.** A bullet carrying two rules is followed for whichever
half the reader sampled. Split it.

**State it, then stop.** The reason belongs in the rule only where the reader
would otherwise apply it wrongly. What does not belong: the session that
produced it, the sha it was found on, the date, what was tried first. That
record is the artifact's, a `plan.md`, a review file, a commit message, and the
lint rejects a date or a bare sha in a rule line.

**Write what a measurement means, and the command, never the reading.** A count,
a duration or a version frozen into a rule is right on the day it is taken and
wrong afterwards, while the reader trusts it because it is specific. Keep the
conclusion it supports and name the command that prints it fresh.

**Bold is a rank, not a voice.** It marks the rules whose violation cannot be
undone. When most bullets in a file are bold, the file has stopped ranking and
the reader is back to sampling. The health table prints the share.

**Write the reader's words**, per `skills/writing-style.md`. Every rule here is
read by someone who has not seen the incident behind it.

## Capabilities

What the machine can do is measured, never written down. `./scripts/env-check.sh`
prints it: privileges, containers, capture, the shell, the authenticated
account. A rule needing one of those facts names the command and lets the reader
read the answer.

A capability recorded as absent stays recorded after the box gains it, and the
next session answers from the file instead of the machine. That is worse than
having no rule: the reader stops checking and states the stale answer with
confidence. The lint blocks the clause that causes it, `stop re-deriving` and its
neighbours, and warns wherever a capability is named with no command beside it.

What does get written down is what a command cannot show: which recipe worked,
what a failure looked like, the fixture a manual test needs. Those go in
`projects/<repo>/AGENTS.md` with their symptom, per *A project's file* below.

## A project's file

`projects/<repo>/AGENTS.md` holds what was measured about one repository. Read it
before the first task there, and write to it in the same turn a fact is measured,
unasked. Never offer the recording as a next step.

- **Conventions, each with the command that produced it**: merge style, commit
  granularity, subject and body shape, changelog placement and selection, issue
  title style, which CI signals lie, every trap that cost a round. A convention
  read off the repository's documentation, or inferred from its commit format, is
  not measured.
- **A glossary, filled while first reading the code**: the term the codebase
  uses, the words a reader outside the project has for the same thing, and the
  few where the project's own name is unavoidable. Fill it during that first
  read, never while editing a draft, because a term stops looking like jargon to
  whoever just read the file defining it. Every posted string then takes its
  words from the right-hand column, per *Write the reader's words* in
  `skills/writing-style.md`.
- **What a session cost to find**: how the project runs locally, the fixture or
  seed data a manual test needs, the version and system package a build required,
  the error a wrong one prints. Each entry carries its symptom, so the next
  session recognises the failure before diagnosing it again.

A delta file for a skill sits beside these, short, opening by naming the core
file it overrides. Work under `projects/<repo>/` reads the delta plus the core,
and the delta wins where they disagree.

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

Where a file is over its cap, the fix is folding and eviction, never a higher
cap. Raising a cap in `skills/lint.py` is a deliberate decision to carry more
rules in every context window, and it is made in its own commit, alone, with the
reason in the message.

Two metrics, because a rule file and a measurement log fail differently. A rule
file is capped on words: every rule in it loads on every turn its task runs, so
growth is the cost. A `projects/` file is a log that earns its size by holding
more measured rules, so it is capped on the size of each rule instead. Measured
across this corpus, a skill and a small delta both run 23 to 38 words per rule;
past 75 the rule is carrying the session that found it rather than the fact. Cut
that clause, never the measurement.

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

## Editing this corpus

- `skills/` is the canonical repository, `davd-gzl/skills`, mounted as a
  submodule in every workspace. Edit here, never in a copy.
- Read the whole file before changing a rule in it. A range read against the two
  sections a task seems to need is how a section gets missed, and the draft
  comes out well-formed against the rules that were read.
- Re-read after `git -C skills log -1` shows a commit that was not there before.
  Another session moves the pin mid-turn.
- Run `./skills/lint.py` over every file the edit touched, plus the workspace
  root `AGENTS.md`, and fix what it reports rather than narrowing what it reads.
