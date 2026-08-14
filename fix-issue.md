---
name: fix-issue
description: Fix an issue in a project: plan, implement in a worktree, open the pull request on a fork. Also verifies CI on the opened pull request and removes the worktrees of merged ones.
argument-hint: "fix <issue-number|url|description> | ci <pr-or-id> | cleanup [id]"
---

# Fix issue

**Input:** `$ARGUMENTS`, one of three modes.

- **`fix <issue>`**: a number, a URL, or a free-text description. A finding held
  privately is read from the disclosure repository first, per
  `skills/security-advisory.md`.
- **`ci <pr-or-id>`**: the opened pull request's number, or the worktree id.
- **`cleanup [id]`**: remove the worktrees whose pull request merged.

Read the project's own `AGENTS.md` and `projects/<repo>/AGENTS.md` before the
first command. Build commands, test commands and what the project demands of a
contribution live there, measured.

## Setup

`git -C <checkout> remote -v`, read in full and never truncated. The push target
is the user's fork; every other remote is another contributor's and is never
pushed to. Create the fork when it is missing:

```bash
gh repo fork <owner>/<repo> --remote-only --remote-name fork
```

## `fix`

1. **Understand.** `gh issue view <n> -R <repo>`, then read the code it names and
   run the repro it carries.
2. **Plan.** Write `plan.md` in `projects/<repo>/changes/<slug>/` before any fix
   code, per *Preparing a fix* in `skills/review.md`: root cause, approach, the
   files, how it is tested, and whatever design record the project requires of a
   change this size.
3. **Worktree**, never the checkout, which is a submodule whose gitlink moves the
   moment a branch lands in it:
   ```bash
   git -C <checkout> fetch <canonical-remote> <default-branch>
   git -C <checkout> worktree add <scratchpad>/<repo>-fix-<id> <canonical-remote>/<default-branch>
   git -C <scratchpad>/<repo>-fix-<id> checkout -b <branch>
   ```
   `<id>` is the issue number where one exists, a short slug otherwise.
4. **Implement** inside the worktree. Never commit, push, or open a pull request
   without the word. Run the formatter and the auto-fixer the CI lint job runs,
   over the changed packages, before any push: that job fails on their diff
   independently of the linter's own findings. Comments follow
   `skills/writing-style.md`, two lines carrying what the code cannot say; a
   reachability chain and the story of how the bug was found belong in the pull
   request body.
5. **Report** the changed files and what each change does.
6. **Keep the worktree.** It carries review feedback, rebases and follow-up work
   until the pull request merges.
7. **Schedule the CI check**, once the pull request is open, with the `/schedule`
   skill: one `fix-issue ci <number>` run, timed to the project's own CI window,
   never recurring. Skip it when the user watches the checks themselves.

The title and body are `skills/pr-body.md`. An issue drafted for a problem no
upstream issue covers is `skills/issue.md`.

## `ci`

Verify the checks on the opened pull request and patch what the diff caused.
This mode never commits and never pushes without the word.

1. **Locate the pull request.** From a worktree id, read the branch in
   `<scratchpad>/<repo>-fix-<id>/` and
   `gh pr list -R <repo> --head <branch> --state all --json number,headRefName,statusCheckRollup`.
2. **Fetch the status.**
   ```bash
   gh pr checks <n> -R <repo>
   gh pr view <n> -R <repo> --json statusCheckRollup,headRefOid
   ```
   Green: report and stop. Still running: schedule one more `ci` run and stop.
3. **Triage each failure.** `gh run view <run-id> -R <repo> --log-failed`. A
   failing check that is not an Actions run, an app check or a commit status, has
   no run id and never appears in `gh run list`: open its details URL from
   `gh pr checks`, and read the same signal on the default branch through
   `gh api repos/<repo>/commits/<sha>/check-runs` and `.../status`. Classify each
   as related, meaning it touches a path in
   `git -C <worktree> diff --name-only <canonical-remote>/<default-branch>` or
   names a symbol the diff changed; unrelated, meaning it also fails on a recent
   default-branch run; or ambiguous, which goes to the user unguessed.
4. **Fix the related ones** in the existing worktree, reproducing locally first
   where the job can run here. Report the diff and wait for the word.
5. **Report** which checks failed, how each was classified, what changed locally,
   and what still needs the user.

## `cleanup`

```bash
git -C <checkout> worktree list | grep -- -fix-
```

For each, resolve the branch to its pull request with
`gh pr list -R <repo> --head <branch> --state all --json number,state,mergedAt`.
Merged: remove the worktree and the branch. Open: keep it and report the status.
Closed unmerged: ask. Print the summary table at the end.
