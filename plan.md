---
name: plan
description: Use before writing any fix code, to produce the spec and plan for a change and to surface the calls a human has to make. Covers spec.md, plan.md, and the numbered open calls both carry.
---

# Spec and plan

Two files in `projects/<repo>/changes/<slug>/`, written before any fix code.
Prose follows `skills/writing-style.md`.

Split them by audience, per [spec-kit](https://github.com/github/spec-kit):

- `spec.md` is what and why: the problem, the scenarios, the numbered
  requirements, the acceptance criteria, what is out of scope. No technology is
  named anywhere in it. Write one where no review has settled the behaviour.
- `plan.md` is how: the technologies, the architecture, the pipelines, the threat
  model, the module inventory, the commit split, and an Iterations section
  recording each round and what caused it, failures included.

Test the split. A reader judging the product behaviour never needs the plan, and
a reader implementing never guesses the behaviour. The change `README.md` stays
the short entry point over both.

`plan.md` also carries what admits a change into scope: a table of what is in,
one row per finding with its effect on the failing signal; what is out, with the
decision each excluded item needs; a verification table, one row per CI job with
its real command and result; the checks that ran beyond the jobs; and an
Iterations section naming every round and what caught it, failures included.

Size the first pull request to the smallest diff that closes the ask, and send
every further capability to the out row with the decision it needs. A maintainer
declining a large first branch sends back the whole branch, not the surplus.

## The change directory

`projects/<repo>/changes/<slug>/`, holding the work on findings that stay in
`projects/<repo>/reviews/<slug>/<n>-<sha>/`. Link each tree to the other and
never repeat what the other states. A change with no review behind it carries the
same files minus the review links.

- `README.md`: the single entry point, linking every other artifact. What is
  broken, what the fix does, status, the create-PR link, what is in the
  directory, the link to the review.
- `plan.md` and `spec.md`, above.
- `pr-body.md`, per `skills/pr-body.md`.
- `overview.md`, where the subject needs explaining before the diff, per
  *Overview* in `skills/review.md`.
- `issue.md`, only where no upstream issue covers the problem, per
  `skills/issue.md`.
- `checkout/`: a submodule pinned to the branch,
  `git submodule add -b <branch> <fork-url> projects/<repo>/changes/<slug>/checkout`,
  required whenever the fix is presented. A worktree at `.worktrees/<repo>-<slug>/`
  stays scratch, out of version control. A fix is never written into the reviewed
  checkout in place, which is restored to its default branch.

## Numbered open calls

An open call is a decision the document made that a human could reasonably make
differently. A document listing none is hiding the choices a human should argue
with, so list every one.

The human meets each call three times:

1. `spec.md` and `plan.md` open with `## Decisions for a human`, right after the
   summary and before the detail. Make it a table, one row per call: the
   identifier, the call, what the document chose, the defensible alternative,
   what turns on it, and whether it needs review or is simply unanswered.
   Number `S1` upward in the spec and `P1` upward in the plan, so "S3
   alternative" is a complete instruction.
2. Where the call takes effect, a one-line blockquote names it and links back to
   the table.
3. The change `README.md` gathers every call from both documents under
   `## Waiting on a human`, naming the one or two to weigh first.

Link every symbol, setting, file, issue and section named in any of it, to the
blob at the base sha or to the section carrying the detail.

In the handover reply, repeat the first call in full and link the rest. Chat is
gone next session.

## Presenting the change

A fix is presented once every item in its own `plan.md` is done and verified. An
item that stayed undone is named, with the decision it needs.
