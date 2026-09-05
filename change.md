---
name: change
description: Use when taking an issue or a review finding to a pull request. Covers the change directory, spec.md and plan.md with their numbered open calls, the worktree, the fix, the CI run and the self-review, and the pull request on the fork.
argument-hint: <issue-number|url|description>
---

# Change

**Input:** `$ARGUMENTS`: an issue number, a URL, or a free-text description. A
finding exploitable against merged or deployed code is read from its disclosure
repository, and is not a change until the gate in the workspace `AGENTS.md`
Invariants has run.

Read the project's own `AGENTS.md` and `projects/<repo>/AGENTS.md` before the
first command: the build and test commands and what the project demands of a
contribution live there, measured.
Where a convention is missing, `./scripts/measure-repo.sh <checkout>
<remote>/<branch> <owner>/<repo>` prints the merge style, the commit body width
and length, the commit granularity and the changelog placement; write each
answer into that file with the command, per `skills/authoring.md`.

Prose follows `skills/writing-style.md`. The title and body are
`skills/pr-body.md`. An issue for a problem no upstream issue covers is
`skills/issue.md`.

## The change directory

`projects/<repo>/changes/<slug>/` holds the work; the findings it acts on stay
in `projects/<repo>/reviews/<slug>/<n>-<sha>/`. Link each tree to the other and
never repeat what the other states. A change with no review behind it carries
the same files minus the review links, and the kind of change goes in its
`README.md`, never in the path. The two trees link each other.

- `README.md`: the single entry point, linking every other artifact. What is
  broken, what the fix does, status, the create-PR link, what is in the
  directory, the link to the review.
- `spec.md` and `plan.md`, below.
- `pr-body.md`, per `skills/pr-body.md`.
- `overview.md`, where the subject needs explaining before the diff, per
  *Overview* in `skills/review.md`.
- `issue.md`, only where no upstream issue covers the problem, stays in the
  review directory per `skills/issue.md` and is linked from `README.md`.
- `checkout/`: a submodule pinned to the branch,
  `git submodule add -b <branch> <fork-url> projects/<repo>/changes/<slug>/checkout`,
  required whenever the fix is presented. The worktree stays scratch, out of
  version control. Only the fix branch ever enters the reviewed checkout, and
  never in place: the checkout is restored to its default branch.

## Spec and plan

Written before any fix code, split by audience per
[spec-kit](https://github.com/github/spec-kit):

- `spec.md` is what and why: the problem, the scenarios, the numbered
  requirements, the acceptance criteria, what is out of scope. No technology is
  named in it. Write one where no review has settled the behaviour.
- `plan.md` is how: root cause, approach, the files, how it is tested, the
  commit split, the threat model and the module inventory where the change is
  large enough to need them, and an Iterations section naming every round and
  what caught it, failures included.

Test the split: a reader judging the behaviour never needs the plan, and a
reader implementing never guesses the behaviour.

`plan.md` also carries what admits a change into scope: a table of what is in,
one row per finding with its effect on the failing signal; what is out, with
the decision each excluded item needs; and a verification table, one row per
CI job with its real command and result, plus the checks that ran beyond the
jobs.

Size the first pull request to the smallest diff that closes the ask, and send
every further capability to the out row with the decision it needs.

### Numbered open calls

An open call is a decision the document made that a human could reasonably
make differently. A document listing none is hiding the choices a human should
argue with, so list every one. The human meets each call three times:

1. `spec.md` and `plan.md` open with `## Decisions for a human`, right after
   the summary: a table, one row per call, with the identifier, the call, what
   the document chose, the defensible alternative, what turns on it, and whether
   it needs review or is simply unanswered. Number `S1` upward in the spec and
   `P1` upward in the plan, so "S3 alternative" is a complete instruction.
2. Where the call takes effect, a one-line blockquote names it and links back
   to the table.
3. The change `README.md` gathers every call from both documents under
   `## Waiting on a human`, naming the one or two to weigh first.

In the handover reply, repeat the first call in full and link the rest: chat is
gone next session.

## Setup

`git -C <checkout> remote -v`, read in full and never truncated. The push
target is the user's fork; every other remote is another contributor's and is
never pushed to. Create the fork when it is missing:

```bash
gh repo fork <owner>/<repo> --remote-only --remote-name fork
```

## Fix

1. **Understand.** `gh issue view <n> -R <repo>`, then read the code it names
   and run the repro it carries. Before editing, `git grep` the callers of the
   function the issue names: one guard where they all route through covers the
   siblings.
2. **Plan**, per *Spec and plan* above.
3. **Worktree**, never the checkout, which is a submodule whose gitlink moves
   the moment a branch lands in it:
   ```bash
   git -C <checkout> fetch <canonical-remote> <default-branch>
   git -C <checkout> worktree add .worktrees/<repo>-fix-<id> <canonical-remote>/<default-branch>
   git -C .worktrees/<repo>-fix-<id> checkout -b <branch>
   ```
   `<id>` is the issue number where one exists, a short slug otherwise.
4. **Weigh each finding before building it.** Name what implementing one costs in files and what
   it buys in cases a user actually hits: a suggestion covering a transition
   nobody has been through yet goes to the pull request body's leaves-out
   sentence, where the maintainer can ask for it, never to a second issue,
   which puts a tracker item in front of maintainers who did not ask for one. A
   finding whose absence makes the feature not work is never in this class.
5. **Implement** inside the worktree. Never commit, push, or open a pull
   request without the word. Run the formatter and the auto-fixer the CI lint
   job runs, over the changed packages, before any push: that job fails on
   their diff independently of the linter's own findings. Comments follow
   `skills/writing-style.md`, two lines carrying what the code cannot say; a
   reachability chain and the story of how the bug was found belong in the pull
   request body.
6. **Loop.** Fix every finding, then loop until nothing is left: apply each,
   re-run the checks, review again, and stop when a full pass adds nothing. That
   empty pass runs unasked and is what the handover waits for. Never hand a
   finding back as a suggestion, and never park one as an open question to keep
   the report tidy. What survives unapplied needs a decision only the user can
   make, and each is named as a decision rather than a leftover.
   `comment_<model>.md` stays the postable artifact, per
   `skills/review-comment.md`.
7. **Run the CI locally.** Reproduce every job the diff touches, loop until
   green before pushing. Take the command from the workflow file, never the
   Makefile or README, read what each script runs, and match it exactly: a
   `check` target may be formatting only. Report a job that cannot run locally as not run, never as passing,
   naming the missing dependency and the closest real substitute. When a change
   makes a linter cover new files, prove it walks them: introduce a violation,
   see it reported, remove it. When a suppression comment moves, prove it still
   suppresses: delete it, see the error, restore it. For a behaviour-preserving refactor of a pure function, ship an
   equivalence proof over a large input set.
8. **Self-review.** Before pushing, read the final diff as a reviewer who did
   not write it, with the *Verification discipline* and severity model of
   `skills/review.md`. Fix what it finds and record it in the plan's Iterations
   section, never silently amend it away.
9. **Report** the changed files and what each change does.
10. **Keep the worktree.** It carries review feedback, rebases and follow-up
    work until the pull request merges.

## Presenting the change

A fix is presented once every item in its own `plan.md` is done and verified.
An item that stayed undone is named, with the decision it needs. The reply
proposing a pull request carries
`https://github.com/<upstream>/compare/<base>...<fork-owner>:<repo>:<branch>`
as a hyperlink, with the file and line counts in the sentence.

Every change opens on the fork first, so the user reads the diff, the title,
the body and the checks where they will appear. The fork pull request is what
`post` is given against; the upstream one opens only after they say so, in a
later turn. On a repo the user does not own it opens as a
draft, which `./scripts/post-fix.sh` passes, and the user marks it ready after
revising it; on their own repos it opens ready. The fork pull request closes
when the upstream one opens, unasked and with no comment on it.

On the word `post`, run `./scripts/post-fix.sh <review-dir> <change-dir>`: it
reads `issue.md` and `pr-body.md`, creates what is missing, links the pull
request to the issue, and writes both URLs into the drafts' `Target:` lines. A
`Target:` holding a real URL counts as open, so a re-run finishes a partial
failure. Use `--dry-run` when anything about the drafts is uncertain, and
commit the updated drafts after. The word carries the change's own notes with
it: the lines drafted in `self-review.md`, per `skills/review-comment.md`, go
up in the same action, and a note whose line the branch no longer carries is
deleted rather than rewritten, with `self-review.md` recording what went.
