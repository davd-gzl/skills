---
name: thinking
description: How the thinking before a reply is written, for every model whose thinking depth no harness setting controls. Imported beside short-form.md, so every model and every subagent carries it; the gate lifts it for a model it has identified as effort-set.
effort-set: [claude-opus-5*, claude-fable-5*, claude-mythos-5*, claude-sonnet-5*]
---

# Thinking

Every model reads this file, and it binds every model but one kind. Where the
session's context says the running model's thinking depth is set by effort,
none of it applies and effort is the control. The gate prints that line only
when the harness told it the model and the model matches `effort-set` above; a
model it cannot name keeps these rules.

The thinking before a reply has one reader, the model, and the user never opens
it, so the readability rules of `skills/short-form.md` stop at its edge. Length
follows the step's difficulty, never a count: each task carries a minimum under
which the answer fails outright, and no instruction estimates it in advance.
What is dropped decides the outcome, so a step is shortened by removing what it
repeats and never by removing the words that say how it is known.

One step, as a draft: `Inv1 → post waits. ran git status: 3 files. ran private-names: 0 hits. infer: safe to write`

- Each step, the shortest draft that carries it; a hard step takes the length it needs.
- **Open each step with how it is known**, `ran <command>:`, `read <file>:`, or `infer:` for anything neither returned. A step with no such opener is an inference in a measurement's words, and it reaches the reply in the same clothes.
- A problem with layers gets its outline first, one draft per layer under it.
- Prompt, rules and file text already in context are named, not quoted.
- Only the option taken is written; a path the reply will not take is dropped before it is reasoned through.
- One pass; a re-check fires only on a tool result that contradicts a step.
- A fact, a status line or a path is answered with no draft.

What a claim rests on and how an unknown fact is settled are *Claims* in
`skills/short-form.md`, which binds every model.
