---
name: shortcuts
description: Use in every reply, in any workspace: the words the user types and what each starts, and the shape of a reply, what it opens with, its links, its closing block.
---

# Shortcuts

Every reply, in any workspace. In context from the session start hook. The
register is the *Short form* of `skills/writing-style.md`.

## The words

What the user types, and what each word starts. A word a skill defines is read
as the skill defines it; ask when the reading changes what gets built.

| Word | What it starts | Rule |
| --- | --- | --- |
| `review <target>` | one review round: the file, the overview, the comment draft, pushed, nothing posted | `skills/review.md` |
| `deep review <target>` | the same round with lens agents on one target | *Deep mode*, `skills/review-modes.md` |
| `review all` | every open target not yet reviewed, the scope written down first | `skills/review-modes.md` |
| `fix <issue or finding>` | a change on the fork: spec, plan, worktree, fix, CI; nothing pushed | `skills/change.md` |
| `try <pr> on <repo>` | the project booted locally, ready to click through | `skills/try.md` |
| `video` | the clip, only once the finding's text is frozen | `skills/try.md` |
| `stop` | the stack and the worktree torn down | `skills/try.md` |
| `report [date]` | the period's status report | `skills/report.md` |
| `post` | the shown draft goes to its target; `post as an AI` adds the marker; `upload` sends media | `skills/review-comment.md`, `skills/issue.md`, `skills/change.md` |
| `push` | the whole git flow, every commit and push the work needs, once | *Consent*, workspace `AGENTS.md` |
| `merge`, `close`, `delete` | that one action on the named target | Invariant 2 |
| `make this review public` | the round to the public artifact repo, links repointed | *Consent* |
| `path` | the worktree the work sits in, its path alone | here |
| "a comment" | the `comment_<model>.md` draft and the text for the target, never an explanation | `skills/review-comment.md` |
| `TLDR` | the answer in one line, and the word it waits on | here |
| `continue` | the local work resumed, dead agents re-dispatched first; nothing published | here |
| `go`, `ok`, `yes`, `sure`, anything else | local work only, never a publish | Invariant 2 |

## The shape of a reply

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

- An agent's return is not a turn. Reply when the step it fed is finished,
  never per agent.
- Re-dispatch every agent that died, before anything else, on `continue` and on
  any turn that resumes the work.
- Dispatching an agent names `skills/shortcuts.md` in the prompt, beside the
  skill it delegates to.
- Correcting published text means editing it to say the right thing and nothing
  else: no "an earlier version claimed", no strikethrough.
