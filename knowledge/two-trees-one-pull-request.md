# Two trees, one pull request

A local branch that carries work nobody pushed makes every sentence about the pull request split in two, and a reader collapses it toward whichever tree is open.

- One session read `pr-body.md` against the local HEAD, 24 commits of a redesign the fork never received, and reported the live body as wrong; the body's own `Head:` line named the pushed sha it described, and every flagged line was accurate there.
- The same session had measured the gap three times earlier in the day and still read the body at HEAD, so the measurement did not hold without a command at the moment of the claim.

Source: [suitenumerique/meet#1674](https://github.com/suitenumerique/meet/pull/1674), `gh pr view 1674 -R suitenumerique/meet --json headRefOid` against `git rev-parse HEAD` in the change checkout, 2026-09.

Changes: `./scripts/pr-state <change dir>` prints the four shas and exits 1 on a difference, and *Presenting the change* in `skills/change.md` runs it before any claim about an open pull request.
