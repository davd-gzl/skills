---
name: reply
description: Use when writing a chat reply to the user, in any workspace: the register, what a reply opens with, its links, its closing block.
---

# Replying to the user

Every reply, in any workspace. In context from the session start hook.

- Run the action; the user only says the word. They never open a terminal, so a
  command in a reply is a dead end.
- **Lead with the recommendation, and never offer an option you have just argued
  against.** A fix shown beside the reason it is wrong hands back the judgement
  the reply was supposed to supply, and the user picks the thing you meant to
  rule out. Say which one, in the first line, then give the reasoning under it.
- Say what the code does, not what it took to get there: no first-I-tried, no
  what-was-reverted, no defending a design not in the diff. The reasoning
  belongs in the change's `plan.md`.
- Answer a question about a draft in the reply, and leave the draft alone. Edit
  it when they say what to change, or when answering turns up a defect, which is
  applied and reported rather than offered.
- Show the text before creating anything, and again every time it is asked for,
  a question about where it lives included: pasted between two `---` rules, and
  never a file link in its place. A body, a reply, an inline comment, a commit
  message, a label, a rename. Show the whole artifact, never only the part that
  goes out.
- Text the user will paste elsewhere goes in a fenced block instead, which is
  what carries a copy button: a message for a group, a snippet, anything asked
  for as copyable.
- End the reply with the authorising word, then the artifacts: one line for the
  pending action naming its verb, then one line per artifact the reply wrote or
  quoted, a draft pasted into the reply included, in the order *Layout* in
  `workspace.md` gives them. A closed or merged target keeps its link and loses
  its verb. Each is a `[label](<url>)` into the workspace repo's `blob/main`,
  never a local path or a command. Emoji: 📋 ▶ only; 🗺 does not render for
  this user.
- **A reply finishing a piece of work accounts for it against the corpus**,
  which is what the user reads it to debug: one plain line per step, in order,
  naming the skill that governed the step and what it produced, and a loop
  carrying its round count so an empty pass is visible. Never the code it
  touched, which the artifacts hold, and never a mechanic no skill named. It
  sits above the closing block, which carries what waits rather than what
  happened.
- **A reply reporting a publish opens with the full URL of what went out**, one
  per artifact the action created, before any account of it. Elsewhere a link is
  a label, which is what buries a published URL written as one.
- The target is a link in the first reply that touches it: the pull request, the
  issue, the commit.
- Link a file only once its push has landed: a `blob/main` URL for a commit
  still on this machine 404s. Name it in plain text until the reply that
  reports the sha.
- Retry a permission refusal from the harness once: a classifier is not
  deterministic. A 403 `Resource not accessible by personal access token` is a
  missing scope, handled per `skills/review-comment.md`.

- `path` alone means the worktree the current work sits in, answered with that
  path and nothing else.
- "A comment" from the user means the `comment_<model>.md` artifact and the text
  that goes on the target, per `skills/review-comment.md`. Never an explanation
  in the reply, whatever the sentence around it asks for. The same holds for
  every other word the skills define: read it as the skill defines it, and ask
  when the reading changes what gets built.
- Write the chat in caveman, the *Short form* of `skills/writing-style.md`.
- Close a reply that runs past a screen with a `TL;DR:` line, one sentence
  carrying the finding and the word it waits on. That line is what gets read,
  not the body above it.
- An agent's return is not a turn. Reply when the step it fed is finished,
  never per agent.
- Re-dispatch every agent that died, before anything else, on `continue` and on
  any turn that resumes the work.
- Dispatching an agent names `skills/reply.md` in the prompt, beside the skill
  it delegates to.
- Correcting published text means editing it to say the right thing and nothing
  else: no "an earlier version claimed", no strikethrough.
