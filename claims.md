---
name: claims
description: What every claim an agent makes rests on, imported through CLAUDE.md so every agent and subagent carries it, whatever the model.
---

# Claims

These bind every model and every agent. How the thinking is written is
`skills/thinking.md`, left out for a model its `effort-set` lists.

- **Before sending a reply, match each sentence saying what a file, a script, a number or a fix does to the command this session ran that returned it.** A sentence with no match is run now or goes out named as the inference it is. The tell is a claim read off something that names the thing without running it: a command a doc lists, a config's keys, a default projection priced for no target, a remedy whose premise was never run. The gap that costs most is between what a command returned and what the sentence asserts from it.
- Before proposing anything the user is asked to act on, a set, a grouping, a plan or a price, run every check that settles one of its parts this turn, then read the whole proposal again and run what that read raises, looping until a full pass changes nothing; only then send it. An estimate or an inference goes out only where no command could settle it this turn, named with the command that would. The tell is a follow-up question that turns up a correction: the check that found it belonged before the proposal.
- An unknown fact gets its command before anything builds on it, and the command returns the smallest output that settles it: a count, a `head`, a `--stat`, a grep, since every tool result stays in context for every later turn and the reply does not.
- Follow a written recipe where it fits the task, and name a departure from it.
