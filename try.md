---
name: try
description: Boot a project locally at a pull request, a branch, or its default branch, prove the running code is the target, and hand the user a URL with the click path to the change. Records every boot failure. Offers a GIF when the change is visual.
argument-hint: <pr-number> on <repo> | <repo>#<pr> | <branch> on <repo> | <repo>
---

# Try

**Input:** `$ARGUMENTS`. A PR and a repo as `<n> on <repo>` or `<repo>#<n>`, a branch as `<branch> on <repo>`, or a repo alone, which means its default branch. The repo name resolves to `projects/<repo>/`.

The output is a URL, a login, the click path, and what to watch for. The user tests the change themselves in a browser. Never hand over a command to run.

## Workflow

1. **Read `projects/<repo>/AGENTS.md` first**, its *Local development* and *Ports* sections, before touching the checkout. It carries the boot recipe measured on this machine: system packages, runtime versions, seed data, whitelisted ports.
2. **Read the target.** `gh pr view <n> --repo <owner>/<repo> --json title,state,isDraft,headRefName,body,files`. The changed-file list decides the boot shape: a frontend-only diff takes the backend from the existing checkout, nothing else rebuilt.
3. **Sync**, per the root `AGENTS.md`: fetch every remote from inside `projects/<repo>/checkout`, never from the workspace root.
4. **Worktree, never the checkout.** `git worktree add <scratchpad>/try-<repo>-<target> <sha>` off that checkout, at `refs/pull/<n>/head` fetched explicitly so a cross-fork PR resolves. The submodule gitlink never moves.
   ```bash
   git fetch <remote> "refs/pull/<n>/head:refs/remotes/<remote>/pr/<n>" -f
   ```
5. **Boot.** Recipe from `AGENTS.md`; absent one, derive it from the project's compose, build and package files. Long-running processes go to the background, logs in a scratch file. Reuse what is already built: rebuild only what the diff touches.
6. **Resolve port collisions before starting, not after.** List the ports the stack publishes against what already listens, and move the collisions rather than killing the user's other stacks:
   ```bash
   ss -ltn | awk 'NR>1{print $4}' | sed 's/.*://' | sort -un
   ```
   A port named in an auth config, a redirect whitelist or a CORS list is load-bearing and moves only to another whitelisted value; every other port is free to move.
7. **Prove the running code is the target.** A boot that silently served the base branch looks identical on screen. Fetch a file the diff added straight from the dev server, or hit the route it added:
   ```bash
   curl -s http://localhost:<port>/<path-the-diff-added> | head -5
   ```
8. **Smoke-test to the change, not the front page.** Drive the app as far as the diff: log in, seed the fixture, reach the screen it changes. Report the state from the DOM or the API, not from a screenshot alone. When the diff is behavioural, exercise the behaviour once and report what it did.
9. **Hand over, and stop.** URL, login, the click path in numbered steps, and one line per changed surface naming what to look at. Do not script a drive of the whole feature before the user has looked.

## Boot recipes

Write the recipe into `projects/<repo>/AGENTS.md` the moment it is measured, each failure with its symptom. A recipe from the project's own documentation is not measured until it has run here.

- **Backend from the checkout, frontend from the worktree**, when the diff is frontend-only. Boot the backend once and reuse it for every later run.
- **Fixture first.** Seed data a manual test needs is in place before the URL is handed over, never a step the user discovers.
- **A failure inside the boot is reported, never patched around.** A stack the PR broke is the finding; say so and stop.

## Video

**The video is the last step, never the first.** Order: the user tries it by hand, the claim settles, the recording proves the settled claim.

1. **Hand over first**, per the workflow's last step, and wait for the user's report before scripting anything.
2. **Script the measurement, not the movie.** Once the user reports what they saw, drive the same path headless and print the state after each step. Save the script under the review's `tests/`.
3. **Show the shot list before recording, and wait.** One numbered line per shot: the claim it proves, the clicks and keys in order, and what the screen must show for the claim to hold. A shot whose expected outcome cannot be written down is not understood well enough to film.
4. **Record only once the finding text is frozen**, and only on the word `video`. Reuse the measurement script.
5. **Re-run the shot list against the recording** before sending it. A caption the run contradicts is a false statement.

A video of a UI moving proves nothing about what was typed: mark each click and name every key on screen. Export a GIF, which renders inline in a GitHub comment where an mp4 does not, and keep the mp4 beside it for anything longer than a few seconds. Files land in the review's `media/` and reach the user in the chat.

A private workspace cannot embed the GIF in a comment on someone else's repo: say so rather than shipping a link that renders broken.

## Teardown

The worktree and the stack survive the turn. On `stop`, kill the processes, remove the worktree, and leave the checkout as it was found.

## Rules

- **Nothing reaches the target repository.** No commit, branch, push, comment or review.
- **Never edit the PR's code**, including the config it ships. A local-only file the boot needs lives in the scratchpad or a gitignored path, never in the diff.
- **Report what did not run.** A stack that could not start on this host is not a passing test, and a step skipped for a missing device or key is named in the handover.
- Findings noticed while driving the app belong in the reply as observations, not in a review file. A finding worth writing down means running the review skill on the target.
