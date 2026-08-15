---
name: git
description: Use when a turn will commit, push, resolve a stale branch, or touch a submodule or worktree in this workspace. Covers what git does silently and reports as success.
---

# Git in this workspace

Identity, the sync order, and the ways a push here reports success while moving
nothing. The consent rules governing when a push may happen at all are in the
workspace `AGENTS.md`, and this file assumes the word has been given.

## Where a push goes

In order:

1. The token can write the repo and the repo is the user's: push straight to the
   default branch, no feature branch, no `gh pr create`.
2. Direct push refused, or the repo is not the user's: push a branch and open the
   pull request. A pushed branch is never left without one.
3. Pull request creation refused: give the `compare/...?expand=1` URL.
4. The canonical remote refuses: push to the fork, open across forks.

`gno-agent-workspace` is an agent repo rather than a project, so reviews, skills,
reports and indexes ride one push to `main`. Try `origin/main`, which is
`samouraiworld`; the session token holds `admin` there, so a 403 means a
different token rather than a protected branch. A refused push moves the turn's
whole output onto one branch and one pull request on `samouraiworld` itself, and
later work cherry-picks onto that branch. The fork
`davd-gzl/gno-agent-workspace` is abandoned.

A skill edit lands in `davd-gzl/skills` and the pin rides the next commit. Every
consumer carries `branch = main` for its skills submodule, so nobody needs a bump
to read new text, and a commit whose whole diff is a gitlink is not made.

## Submodules

A submodule sits on a detached HEAD, and every failure below follows from that.

- **Push a submodule commit in the command that makes it.** A commit on a
  detached HEAD is referenced by nothing, so the next `submodule update` in the
  parent checks the recorded gitlink back out and the commit leaves `git log`
  with no warning. It survives in the submodule's own `git reflog`, which is
  where to look before assuming it is gone. Where the push has to wait for the
  user's word, commit on a branch inside the submodule instead of on the
  detached HEAD.
- **Push it as `git push origin HEAD:main`.** The `main` inside a submodule is
  whatever the last `submodule update` left there, usually stale, so pushing that
  ref is refused as behind its remote counterpart while the commit that matters
  sits on `HEAD`. Follow with `git branch -f main origin/main` so the next push is
  ordinary. The refusal does not stop a surrounding `set -e` script, so confirm
  the gitlink resolves on the remote before pushing the parent, never after.
- **Push the submodule, then the parent.** `git -C <path> push` sends its commits
  to its own remote; the parent tracks only a gitlink.
  `git push --recurse-submodules=on-demand` does both. A clone breaks when a
  gitlink's commit is not on the url its `.gitmodules` entry names. Most
  submodules here point at a fork, and `gno-agent-workspace` points at
  `samouraiworld`.
- **Version a fix branch as a submodule, never as a worktree.** A worktree's
  `.git` is a file pointing into the main checkout's object store, so git cannot
  track it. `git submodule add -b <branch> <fork-url> <path>` records
  `branch = <branch>` in `.gitmodules`, which `git submodule update --remote`
  follows. Every presented fix pays a second clone at
  `projects/<repo>/changes/<slug>/checkout`, and the worktree stays scratch-only.
- **Restore a checkout to its default branch after working in it.** A feature
  branch left in a submodule checkout moves the parent's gitlink and dirties the
  tree.

## Commands that lie

- **Quote every `<sha>:<path>` argument.** Under zsh, `git show $c:review.md`
  expands as `${c:r}` plus `eview.md`, since `:r` is a history modifier: the
  command fails on an unknown revision while the surrounding loop keeps going, so
  a verification loop built that way reports clean for every commit and checked
  nothing. Write `git show "${c}:review.md"`. `./scripts/env-check.sh shell` names
  the shell in play.
- **Stage the paths the turn touched, and read `git show --stat` before pushing.**
  Another session pushes to this workspace from another machine, so a tree that
  looks current is a snapshot of its last sync, and a deletion the other side
  never touched merges silently. Stage under `set -e`: a `git add` naming a path
  already staged as deleted exits nonzero and stages nothing beside it, so the
  commit that follows carries the deletion alone and the push takes the file off
  the remote.
- **Set both identity pairs on `rebase` and `cherry-pick`,** which rewrite the
  committer from the environment exactly as `commit` does.

## A stale branch

Before resolving conflicts, check whether the canonical branch already shipped
the feature. A branch that sat for weeks conflicts because the area moved, and
the commit that moved it is often the same work by someone else. Read the
merge-base-to-canonical log for the files the branch touches, and grep the
canonical branch for the API it adds under every plausible spelling. The
resolution is not the deliverable: a superseded branch closes, and saying so is
the answer.

## After a final action

Bring `pr-body.md`, `issue.md`, the change `README.md` with its `Status:` and
`Head:` lines, and the `checkout/` gitlink up to match what landed. Read the live
text back with `gh pr view <n> --json body` first: an edit made in the GitHub
interface is invisible from here, and a later push from a stale draft reverts it
silently.
