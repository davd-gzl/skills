---
name: git
description: Use when a turn will commit, push, sync a checkout, check out a branch or clone a repository again, resolve a stale branch, or touch a submodule or worktree in this workspace. Covers the identity every commit takes, where a push goes, and what git does silently and reports as success.
---

# Git in this workspace

When a push may happen at all is the workspace `AGENTS.md`; this file assumes
the word is given.

## Commit identity

Commit with the consumer's own verb, `./scripts/commit -m <message> <path>...`,
`-C <repo>` for another tree: it measures the destination's visibility, takes
the handle from there and sets all four identity variables, `GIT_AUTHOR_NAME`,
`GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL`. Two handles, by
visibility: the user's own for a public destination, and for a private one a
machine handle tied to no account, so the commit counts toward nobody's graph.
A private destination going public takes the user's handle from now, named in
`identities.overrides` of the consumer's config, since its history goes public
with it. `--show` prints the handle it would use and commits nothing.

Pin the identity in every checkout's own git config, `./scripts/identity --write`.
The verb above sets the four variables for its own call and reaches nothing else, so `git rebase`,
`git cherry-pick`, `git commit --amend` and a bare `git commit` take whatever the machine holds,
four exported variables before the config. Rebase an unpushed commit onto a moved remote, a push
refused as non-fast-forward, with `./scripts/commit -C <repo> --rebase-onto <remote>/<branch>`: it
rewrites every replayed committer under the destination's handle and aborts on a conflict, where
a bare `git rebase` rewrites a correctly authored commit under the machine's. Local config beats
global and loses to the variables, so the two agree wherever both apply. `./scripts/identity`
alone reports drift, `--audit <n>` names every commit this machine's own config committed under
neither handle. The machine's global identity is the private handle, so an unpinned tree defaults
to the one that counts toward nobody's graph.

A commit applying a fix a reviewer proposed, a `suggestion` block or an edit
they spelled out, takes their fix as written and credits them with a
`Co-authored-by: <name> <<id>+<login>@users.noreply.github.com>` trailer,
`gh api users/<login> --jq '.id,.name'` printing both. A fix the agent wrote in
place of theirs credits nobody, so take theirs wherever it holds. Invariant 7
bars a trailer naming a model, never a human reviewer's.

A machine identity in
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

When a file you commit also holds another session's uncommitted hunk, commit
your hunks alone: save the file, write HEAD's version plus your hunks, commit
the path, restore the saved file, and `git diff` it to see only the other
hunk left.

When the tree you tested carries another session's uncommitted edits, run the
suites again on the commits alone before the push: a worktree at the new HEAD,
`git -C <checkout> worktree add --detach <path> <sha>`, removed after.

## One branch, one worktree

Git refuses a second checkout of a branch only inside one clone, so the same
branch checked out in another clone goes unnoticed, and the copy the user's
editor has open falls behind.

- Before checking out a branch other than a default one, by `git worktree
  add`, `git checkout`, `git switch`, `gh pr checkout` or a new clone, run
  `./scripts/branch-holders <branch> --repo <a checkout of the repository>`,
  `gh pr view <n> --json headRefName` naming a pull request's branch. It lists
  each worktree holding the branch, a rebase or bisect of it in progress
  included, in every clone it reaches that shares the repository's history,
  with its last commit's age and its count of changed files; the script's
  header comment names the directory it scans and what it follows from there.
- On exit 1, check out nothing: show the user the list and ask which copy to
  work in, or, in a subagent, return the list to the parent. When `here` is the
  only line besides `pinned` ones, the tree `--repo` names is already on the
  branch: work there. The uncommitted edits in a listed copy are the user's or
  another session's, so never stash, clean or revert them.
- The `checkout/` submodule that *The change directory* in `skills/change.md`
  pins to a fix branch is a record, never a working copy: adding it needs no
  check, and the script lists it as `pinned` without counting it.
- On exit 2, fix the call it names and run it again.

## Where a push goes

**A pull request's branch lives in its head repository, a fork whenever
`isCrossRepository` is true.** Read
`gh pr view <n> -R <upstream> --json headRepositoryOwner,isCrossRepository`
before the push, never the URL it is browsed at. A 403 there is the wrong
destination before it is a missing permission.

1. The token can write it and the repo is the user's: straight to the default
   branch, no feature branch, no `gh pr create`; `skills/`, below, and any
   change the consumer's `AGENTS.md` sends to a pull request excepted.
2. Refused, or not the user's repo: push a branch and open the pull request. A
   pushed branch is never left without one.
3. Creation refused: give the `compare/...?expand=1` URL.
4. The canonical remote refuses: push to the fork, open across forks.

Push a pull request's branch with `-u`, `git push -u <head remote> HEAD:<branch>`,
so the branch tracks its head repository and the editor's pull request view
links it; a branch pushed without it shows no pull request there.

A commit stays on top of a pushed branch, whatever the repo's measured
granularity: squashing an already-pushed branch costs a second force push, and
the maintainer squashes at merge. A squash the user asks for, `squash push`
included, folds only the commits the remote lacks, onto the pushed tip; one
reaching below that tip is a force push, named as one before it is built.

**A change to `skills/` goes on a branch of its own in its own worktree,
`git -C skills worktree add <scratch>/skills-<branch> -b <branch> origin/main`,
pushed with `-u` and opened as a pull request, never straight to its `main`.**
A session's changes to `skills/`, whatever their subjects, share that one
branch and pull request, one commit each: every extra pull request is one more
for the user to read and one more conflict.
The workspace's own `skills/` stays on `main`, which its sync fast-forwards. The pin moves in the workspace commit after that pull request
merges, `skills at <sha>: <what it carries>`, so a clone resolves to merged
rules.

## The parent races other sessions

Another machine pushes to this workspace mid-turn, so a push refused as
non-fast-forward is the normal case and not an error.
`./scripts/sync-push.sh '<subject>' <path>...` commits the named paths, rebases
over what landed, retries, and carries the other session's uncommitted files
across the rebase. Stop on a conflict rather than resolving it, and report the files.

## Submodules

A submodule sits on a detached HEAD, and every failure here follows from that.
`skills/` takes its own branch instead, per *Where a push goes*.

- **Push a submodule commit in the command that makes it.** A detached-HEAD
  commit is referenced by nothing, so the parent's next `submodule update` checks
  the recorded gitlink back out and the commit leaves `git log` unannounced. It
  survives in the submodule's own `git reflog`. Where the push waits for the
  user's word, commit on a branch there instead.
- **Push it as `git push origin HEAD:main`.** A submodule's `main` is whatever
  the last update left, usually stale, so pushing that ref is refused as behind
  while the commit that matters sits on `HEAD`. On a detached HEAD, follow with
  `git branch -f main origin/main`.
- Restore a checkout to its default branch after working in it, or the
  parent's gitlink moves and the tree is dirty.

## Commands that lie

- Brace every `<sha>:` argument, a push refspec as much as a `git show` path.
  Under zsh `git show $c:review.md` expands as `${c:r}` plus `eview.md`, and
  `git push origin "$sha:refs/heads/$b"` goes out as `<sha>efs/heads/<b>`, so
  the command fails on an unknown revision or an unmatched refspec while the
  loop around it keeps going and reports clean for every commit. Write
  `"${c}:review.md"` and `"${sha}:refs/heads/${b}"`.
  `./scripts/env-check.sh shell` names the shell in play.
- Loop over a literal list or an array, never an unquoted `$VAR` holding
  several words. zsh does not split it, so `for n in $N` runs once on the whole
  string and the command inside fails on `"a b c"` as one argument. Write
  the words out, or run the loop under `bash -c`.
- Read a push's own exit status, never a line printed beside it. A `git push`
  piped into `sed` or `tee` under `set -e` hands the shell the pipe's status, so
  a refused push prints its error and the script's next line still reports the
  push as done. Push every refspec of one remote in a single `git push --atomic`
  and let its status stand.
- `gh pr edit` exits 0 on a token scope failure and sends nothing. A body goes
  up through `./scripts/pr-body-apply`, any other field over REST,
  `gh api -X PATCH repos/<owner>/<repo>/pulls/<n>`, read back after the edit.

## Merging

**Merge with `git merge --no-commit --no-ff`.** The merge stays open, so the
editor's source control lists the conflicted files alone and the user resolves
from there.

- When every side of a conflict is a branch the session built for the change
  in hand, resolve it without a word: keep what each side meant, commit the
  merge, run the checks the branches ran, and name each resolution in the next
  reply. The rules below hold for any side someone else wrote.
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
`Head:` lines, and the `checkout/` gitlink up to match what landed.
