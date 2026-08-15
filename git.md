---
name: git
description: Use when a turn will commit, push, resolve a stale branch, or touch a submodule or worktree in this workspace. Covers what git does silently and reports as success.
---

# Git in this workspace

The ways a push here reports success while moving nothing. When a push may
happen at all is the workspace `AGENTS.md`; this file assumes the word is given.

## Where a push goes

1. The token can write it and the repo is the user's: straight to the default
   branch, no feature branch, no `gh pr create`.
2. Refused, or not the user's repo: push a branch and open the pull request. A
   pushed branch is never left without one.
3. Creation refused: give the `compare/...?expand=1` URL.
4. The canonical remote refuses: push to the fork, open across forks.

`gno-agent-workspace` is an agent repo, so reviews, skills, reports and indexes
ride one push to `main` on `samouraiworld`, which is `origin`. The session token
holds `admin` there, so a 403 means a different token, not a protected branch. A
refused push puts the turn's whole output on one branch and one pull request
there, and later work cherry-picks onto it. The fork
`davd-gzl/gno-agent-workspace` is abandoned.

A skill edit lands in `davd-gzl/skills`. Every consumer tracks `branch = main`,
so nobody needs a bump to read it, and a commit whose whole diff is a gitlink is
not made.

## The parent races other sessions

Another machine pushes to this workspace mid-turn, so a push refused as
non-fast-forward is the normal case and not an error. Fetch, rebase, push, and
repeat: five collisions in one turn is a measured figure, not a bad day. Stop on
a conflict rather than resolving it, and report the files.

```bash
for i in 1 2 3 4 5; do
  git fetch -q origin
  [ "$(git rev-list --count HEAD..origin/main)" = 0 ] || git rebase origin/main || { git rebase --abort; break; }
  git push -q origin main && break
done
```

Set both identity pairs on that rebase. `rebase` and `cherry-pick` take the
committer from the environment exactly as `commit` does.

## Submodules

A submodule sits on a detached HEAD, and every failure here follows from that.

- **Push a submodule commit in the command that makes it.** A detached-HEAD
  commit is referenced by nothing, so the parent's next `submodule update` checks
  the recorded gitlink back out and the commit leaves `git log` unannounced. It
  survives in the submodule's own `git reflog`. Where the push waits for the
  user's word, commit on a branch there instead.
- **Push it as `git push origin HEAD:main`.** A submodule's `main` is whatever
  the last update left, usually stale, so pushing that ref is refused as behind
  while the commit that matters sits on `HEAD`. Follow with
  `git branch -f main origin/main`. The refusal does not stop a surrounding
  `set -e` script, so confirm the gitlink resolves on the remote before pushing
  the parent, never after.
- **Push the submodule, then the parent.** `git -C <path> push` sends its commits
  to its own remote and the parent tracks only a gitlink;
  `git push --recurse-submodules=on-demand` does both. A clone breaks when a
  gitlink's commit is not on the url `.gitmodules` names. Most submodules here
  point at a fork, `gno-agent-workspace` at `samouraiworld`.
- **Version a fix branch as a submodule, never a worktree.** A worktree's `.git`
  is a file into the main object store, so git cannot track it.
  `git submodule add -b <branch> <fork-url> <path>` records the branch, which
  `git submodule update --remote` follows. Every presented fix pays a second
  clone; the worktree stays scratch.
- **Restore a checkout to its default branch after working in it**, or the
  parent's gitlink moves and the tree is dirty.

## Commands that lie

- **Quote every `<sha>:<path>` argument.** Under zsh `git show $c:review.md`
  expands as `${c:r}` plus `eview.md`, so the command fails on an unknown
  revision while the loop around it keeps going and reports clean for every
  commit. Write `git show "${c}:review.md"`.
  `./scripts/env-check.sh shell` names the shell in play.
- **Stage the paths the turn touched, and read `git show --stat` before
  pushing.** A tree that looks current is a snapshot of its last sync, and a
  deletion the other side never touched merges silently. Stage under `set -e`: a
  `git add` naming a path already staged as deleted exits nonzero and stages
  nothing beside it, so the commit carries the deletion alone.

## A stale branch

Check whether the canonical branch already shipped the feature before resolving
conflicts. A branch that sat for weeks conflicts because the area moved, and the
commit that moved it is often the same work by someone else. Read the
merge-base-to-canonical log for the files it touches, and grep that branch for
the API it adds under every plausible spelling. A superseded branch closes, and
saying so is the answer.

## After a final action

Bring `pr-body.md`, `issue.md`, the change `README.md` with its `Status:` and
`Head:` lines, and the `checkout/` gitlink up to match what landed. Read the live
text back with `gh pr view <n> --json body` first: an edit made in the GitHub
interface is invisible here, and a later push from a stale draft reverts it.
