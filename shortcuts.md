---
name: shortcuts
description: Use in every reply, in any workspace: the words the user types and what each starts, and the shape of a reply, what it opens with, its links, its closing block.
---

# Shortcuts

Every reply, in any workspace. In context from the session start hook. The
register is *Short form*, `skills/short-form.md`.

## The words

What the user types, and what each word starts. A word a skill defines is read
as the skill defines it; ask when the reading changes what gets built.

| Word | What it starts | Rule |
| --- | --- | --- |
| `review <target>` | one review round: the overview, the comment draft, the claim table and its tests, pushed, nothing posted | `skills/review.md` |
| `quick review <target>`, `deep review <target>` | the same round on the `quick` or `deep` budget preset, cheaper models and caps, or more finders with the security angles run twice, the shape unchanged | `./scripts/review-plan.py --compare` |
| `review all` | every open target not yet reviewed, the scope written down first | `skills/review-modes.md` |
| `plan` | what the next review round will run and cost, the stage table and the projection | `./scripts/review-plan.py` |
| `upgrade skills` | every line of the workspace's `TODO.md` taken to its rule or script, one commit each with its estimate, the line struck as it lands; nothing pushed | *Upgrading from the TODO*, `skills/authoring.md` |
| `config <stage> <key> <value>` | that knob of the review workflow changed, the plan reprinted, the estimate given | `./scripts/review-plan.py --set`, *A change to the run's shape* in `skills/authoring.md` |
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
- The closing block carries one bare verb, `post` never `post the issue`, and
  says beside it what saying it does: what opens, in which repository, against
  which base, and whether it opens as a draft or ready. The sentence around it
  names every destination it covers: the publish, the commits and pins behind
  it, the workspace backup. Where a publish and something already authorised or
  automatic are both pending, do the latter and offer the publish alone.
- The closing block is the authorising word, then the artifacts: one line for
  the pending action naming its verb, then one line per artifact the reply wrote
  or quoted, a draft pasted into the reply included, in the order *Layout* in
  `workspace.md` gives them. A closed or merged target keeps its link and loses
  its verb. Each is a `[label](<url>)` into the workspace repo's `blob/main`,
  never a local path or a command. Emoji: 📋 ▶ only; 🗺 does not render for
  this user.
- Under the closing block, the `TL;DR:` line every reply ends on, per *Short
  form* in `skills/writing-style.md`.
- **A reply finishing a piece of work ends on the account of everything it
  did**, above the closing block, as plain lines, never in a code fence or a
  quote: `Did:` alone on a line, then one numbered line per step in order, what
  was done and what it produced, a loop with its round count, a clean step in
  three words, then `Left:` naming what stayed undone and the decision it
  needs, dropped when nothing is left. The prose above never retells a listed
  step: it carries the decisions to make and the word to give. What was tried
  and dropped stays in `plan.md`. The register check names a closing block
  without the account, and an account inside a fence.
- **A reply reporting a publish opens with the full URL of what went out**, one
  per artifact the action created, before any account of it. Elsewhere a link is
  a label, which is what buries a published URL written as one.
- The target is a link in the first reply that touches it: the pull request, the
  issue, the commit.
- Every reply ends on the links, pushed or not: the target, then each
  artifact as its `blob/main` URL. A file whose push has not landed keeps its
  link and says so beside it, since that URL 404s until the sha is reported.
- Retry a permission refusal from the harness once: a classifier is not
  deterministic. A 403 `Resource not accessible by personal access token` is a
  missing scope, handled per `skills/review-comment.md`.

- An agent's return is not a turn. Reply when the step it fed is finished,
  never per agent.
- Re-dispatch every agent that died, before anything else, on `continue` and on
  any turn that resumes the work.
- Dispatching an agent names `skills/shortcuts.md` in the prompt, beside the
  skill it delegates to.
- Dispatching agents ends the reply with one forecast line: what went out and
  how many, the minutes and tokens the last measured round of that shape took,
  when to expect them back, and that `stop` kills them. Their return gets the
  same line with what was spent.
- **Any work past ten minutes reports every ten minutes**, agents, a workflow,
  a suite, a build, a batch of targets: one line, what is done of what, minutes
  elapsed, minutes left against the forecast. A background timer, `sleep 600`
  then the count, wakes the reply and is restarted until the work ends; the
  user never asks. A workflow's count is
  `./scripts/review-progress.sh <workflow-dir> <plan-minutes>`.
- Correcting published text means editing it to say the right thing and nothing
  else: no "an earlier version claimed", no strikethrough.
