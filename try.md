---
name: try
description: Boot a project locally at a pull request, a branch, or its default branch, prove the running code is the target, and hand the user a URL with the exact click path to the change. Records every boot failure it hit. Offers a GIF when the change is visual.
argument-hint: <pr-number> on <repo> | <repo>#<pr> | <branch> on <repo> | <repo>
---

# Try

**Input:** `$ARGUMENTS` — a PR number and a repo (`1507 on meet`, `meet#1507`), a branch and a repo (`feat/a11y on meet`), or a repo alone, which means its default branch. The repo name resolves to `projects/<repo>/`.

The output is the user testing the change themselves, in a browser, in under a minute of their attention. Everything here serves that: they get a URL, a login, the click path, and what to watch for. They never get a command to run.

## Workflow

1. **Read `projects/<repo>/AGENTS.md` first**, its *Local development* and *Ports* sections, before touching the checkout. That file carries the boot recipe measured on this machine: the system package a build needs, the node version, the seed data a manual test needs, the port a realm whitelists. Skipping it re-buys every failure it lists.
2. **Read the target.** `gh pr view <n> --repo <owner>/<repo> --json title,state,isDraft,headRefName,body,files`. The changed-file list decides the boot shape: a frontend-only diff needs the backend from the existing checkout and nothing else rebuilt.
3. **Sync**, per the root `AGENTS.md`: fetch every remote from inside `projects/<repo>/checkout`, never from the workspace root.
4. **Worktree, never the checkout.** `git worktree add <scratchpad>/try-<repo>-<target> <sha>` off that checkout, at `refs/pull/<n>/head` fetched explicitly so a cross-fork PR resolves. The submodule gitlink never moves and the workspace tree stays clean.
   ```bash
   git fetch upstream "refs/pull/<n>/head:refs/remotes/upstream/pr/<n>" -f
   ```
5. **Boot.** Recipe from `AGENTS.md`; absent one, read `compose.yml`, `Makefile` and `package.json` and derive it. Long-running processes go to the background with their logs in a scratch file. Reuse what is already built: rebuild only what the diff touches.
6. **Resolve port collisions before starting, not after.** List what the compose file publishes against what is already listening, and move the collisions rather than killing the user's other stacks:
   ```bash
   grep -nE '^\s+- "[0-9]+:' compose.yml
   ss -ltn | awk 'NR>1{print $4}' | sed 's/.*://' | sort -un
   ```
   A port named in an OIDC realm, a redirect whitelist or a CORS list is load-bearing and moves only to another whitelisted value; every other port is free to move.
7. **Prove the running code is the target.** A boot that silently served the base branch is the failure this catches, and it looks identical on screen. Fetch a file the diff added straight from the dev server, or hit the route it added:
   ```bash
   curl -s http://localhost:<port>/src/<path-added-by-the-diff> | head -5
   ```
8. **Smoke-test to the change, not to the front page.** Drive the app as far as the diff: log in, seed the fixture, enter the room, open the panel. Report the state you reached from the DOM or the API, not from a screenshot alone. When the diff is behavioural, exercise the behaviour once and report what it did.
9. **Hand over, and stop there.** URL, login, the click path in numbered steps, and one line per changed surface naming what to look at. The user tries it themselves next, so do not script a drive of the whole feature before they have looked at it.

## Boot recipes

Write the recipe into `projects/<repo>/AGENTS.md` the moment it is measured, with the symptom beside each failure, so the next run recognises the failure instead of diagnosing it again. A recipe taken from the project's own documentation is not measured until it has run here.

- **Backend from the checkout, frontend from the worktree**, when the diff is frontend-only. The backend stack is unchanged by the PR, so it boots once and serves every later run.
- **Fixture first.** A manual test that needs seed data needs it before the URL is handed over, never as a step the user discovers.
- **A failure inside the boot is reported, never patched around.** A stack that will not start because the PR broke it is the finding; say so and stop.

## Video

**The video is the last step, never the first.** Recording costs a full scripted drive of the app, and every wording change to the finding costs it again. So the order is: the user tries it by hand, the claim settles, then the recording proves the settled claim.

1. **Hand over first.** The URL, the login, the click path. The user's own run is the fastest verification available and it costs nothing here.
2. **Script the measurement, not the movie.** Once they report what they saw, drive the same path headless and print the state after each step. A table of states is what turns their observation into a finding, and it reruns in seconds. Save the script under the review's `tests/`.
3. **Show the shot list before recording, and wait.** One numbered line per shot: the claim it proves, the clicks and keys in order, and what the screen must show for the claim to hold. The user reads that list in seconds and cuts the shots they do not want, where a recorded minute they did not ask for is a minute of both your time and theirs. A shot whose expected outcome cannot be written down is not understood well enough to film.
4. **Record only once the finding text is frozen**, and only on the word `video`. Reuse the measurement script: the recording adds an overlay naming each click and keypress, and captions that contradict a later correction are the cost of recording early.
5. **Re-run the shot list against the recording** before sending it. Every caption states a claim, and a caption the run contradicts is a false statement shipped in a file the user will forward.

The overlay is the point: a video of a UI moving proves nothing about what was typed. Draw a marker at each click and name every key on screen, so a reader sees the input, not just the result. Export a GIF, which renders inline in a GitHub comment where an mp4 does not, and keep the mp4 beside it for anything longer than a few seconds. The files land in the review's `media/`, and reach the user in the chat.

A private workspace cannot embed the GIF in a comment on someone else's repo, so say so rather than writing a link that renders as a broken image.

## Teardown

The worktree and the stack survive the turn: the user tests after the reply. On `stop`, kill the processes, remove the worktree, and leave the checkout as it was found.

## Rules

- **Nothing reaches the target repository.** No commit, no branch, no push, no comment, no review. This skill reads a PR and boots it; the review skill judges it.
- **Never edit the PR's code**, including the config it ships. A local-only file the boot needs (an env file, a compose override) lives in the scratchpad or in a gitignored path, never in the diff.
- **Report what did not run.** A stack that could not start on this host is not a passing test, and a step skipped for a missing device or key is named in the handover.
- Findings noticed while driving the app belong in the reply as observations, not in a review file. A finding worth writing down means running the review skill on the target.
