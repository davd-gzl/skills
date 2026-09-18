---
name: git
description: Use when a turn will commit, push, sync a checkout, resolve a stale branch, or touch a submodule or worktree in this workspace. Covers the identity every commit takes, where a push goes, and what git does silently and reports as success.
---

# Git in this workspace

When a push may happen at all is the workspace `AGENTS.md`; this file assumes
the word is given.

## Commit identity

Commit with the consumer's own verb, `./scripts/commit -m <message> <path>...`,
`-C <repo>` for another tree: it measures the destination's visibility, takes
the handle from there and sets all four identity variables. Two handles, by
visibility: the user's own for a public destination, and for a private one a
machine handle tied to no account, so the commit counts toward nobody's graph.
`--show` prints the handle it would use and commits nothing.

Pin the identity in every checkout's own git config, `./scripts/identity --write`.
The verb above sets the four variables for its own call and reaches nothing else, so `git rebase`,
`git cherry-pick`, `git commit --amend` and a bare `git commit` take the config identity: a push
refused as non-fast-forward is retried with a rebase, and that rebase rewrites a correctly authored
commit under whatever the machine holds. Local config beats global and loses to the variables, so
the two agree wherever both apply. `./scripts/identity` alone reports drift, `--audit <n>` names
every commit this machine's own config committed under neither handle. The machine's global
identity is the private handle, so an unpinned tree defaults to the one that counts toward nobody's
graph.

Why it is a verb rather than a line to type. Author and committer must both be
set, in `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` and
`GIT_COMMITTER_EMAIL`: a variable set beats config, local and global,
and `git -c` too, so the verb holds in a tree the pin has not reached. `--amend` keeps the original
author however those four are set, so an amend meant to repair an identity
repairs the committer alone; the verb passes `--reset-author`. `rebase` and
`cherry-pick` take the committer where `commit` does, so a rebase run bare
commits under the config identity.

A fix branch under `projects/<repo>/changes/<slug>/checkout/` targets a public
upstream and takes the user's handle even though the parent tree is private;
only the parent's own commit takes the machine handle. A machine identity in
either field of a public commit is co-authorship in another shape. Check with
`git log -1 --format='%an <%ae> / %cn <%ce>'` before pushing, and leave past
commits as they are.

## Sync a checkout

Before the first task in a checkout and before reading any state out of its
tree. The workspace-level sync, `./scripts/sync.sh`, does not reach inside a
submodule.

1. Enter the checkout. `git remote -v` there, and fetch every remote it lists.
2. `git rev-list --left-right --count HEAD...<remote>/<branch>` per remote. The
   numbers are commits only on HEAD, then commits only on the remote.
3. Decide which remote is canonical, meaning where the project actually
   develops. Often `upstream`, not `origin`.

Take the distant version. Diverged, meaning both numbers are nonzero, resets the
local branch onto the remote rather than merging or rebasing. Report after the
reset: every commit and file it dropped, and whether the same content survives on
the remote under another sha.

Stage the paths the turn touched, never the whole tree, and read
`git show --stat` before pushing. Run the CI locally first, per *Fix* in
`skills/change.md`.

## Where a push goes

**A pull request's branch lives in its head repository, a fork whenever
`isCrossRepository` is true.** Read
`gh pr view <n> -R <upstream> --json headRepositoryOwner,isCrossRepository`
before the push, never the URL it is browsed at. A 403 there is the wrong
destination before it is a missing permission.

1. The token can write it and the repo is the user's: straight to the default
   branch, no feature branch, no `gh pr create`.
2. Refused, or not the user's repo: push a branch and open the pull request. A
   pushed branch is never left without one.
3. Creation refused: give the `compare/...?expand=1` URL.
4. The canonical remote refuses: push to the fork, open across forks.

A commit stays on top of a pushed branch, whatever the repo's measured
granularity: squashing an already-pushed branch costs a second force push, and
the maintainer squashes at merge.

A skill edit lands in `davd-gzl/skills`. Every consumer tracks `branch = main`
and its sync takes the tip at session start, so nobody needs a bump to read it.
The pin moves once per `upgrade skills` pass, in one commit of its own at the
close, `skills at <sha>: <what it carries>`, after the skills push landed, so a
clone resolves to the rules the pass wrote about; between passes `git status`
reading `M skills` is the expected state.

## The parent races other sessions

Another machine pushes to this workspace mid-turn, so a push refused as
non-fast-forward is the normal case and not an error.
`./scripts/sync-push.sh '<subject>' <path>...` commits the named paths, rebases
over what landed, retries, and carries the other session's uncommitted files
across the rebase. Stop on a conflict rather than resolving it, and report the
files.

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
  gitlink's commit is not on the url `.gitmodules` names, and `workspace.md`
  says which submodules point at a fork.
- Version a fix branch as a submodule, never a worktree. A worktree's `.git`
  is a file into the main object store, so git cannot track it.
  `git submodule add -b <branch> <fork-url> <path>` records the branch, which
  `git submodule update --remote` follows. Every presented fix pays a second
  clone; the worktree stays scratch.
- Write the submodule push and the parent's gitlink bump as one script of
  `git -C <path>` commands, never a `cd` chain. A `cd` inside a compound
  command leaves every later line running from the wrong tree, so the parent
  bump fails after the submodule push already landed and the turn ends half
  pushed. Neither half waits for a word the other did not need.
- Restore a checkout to its default branch after working in it, or the
  parent's gitlink moves and the tree is dirty.

## Commands that lie

- Quote every `<sha>:<path>` argument. Under zsh `git show $c:review.md`
  expands as `${c:r}` plus `eview.md`, so the command fails on an unknown
  revision while the loop around it keeps going and reports clean for every
  commit. Write `git show "${c}:review.md"`.
  `./scripts/env-check.sh shell` names the shell in play.
- `gh pr edit` reports a scope failure as success. It resolves reviewers and
  assignees over GraphQL before it patches, so a token without `read:org`
  prints `Your token has not been granted the required scopes`, sends no edit,
  exits 0, and the old body stays. Patch over REST,
  `gh api -X PATCH repos/<owner>/<repo>/pulls/<n> -F body=@<file>`, and read
  the body back after every edit.
- Stage under `set -e` with care. A `git add` naming a path already staged
  as deleted exits nonzero and stages nothing beside it, so the commit carries
  the deletion alone. A tree that looks current is a snapshot of its last sync,
  and a deletion the other side never touched merges silently.

## Merging

**Merge with `git merge --no-commit --no-ff`.** The merge stays open, so the
editor's source control lists the conflicted files alone and the user resolves
from there.

- Stop at the first conflict and report the files. No `git checkout --ours`
  or `--theirs`, and no edit to a conflicted file on the session's own judgement.
- Explain each conflict before any resolution is written: what each side wants,
  why they differ, and what the resolution costs to maintain. The user picks;
  apply the choice once they have made it.
- Commit the merge after the user confirms the resolution, never before.

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
