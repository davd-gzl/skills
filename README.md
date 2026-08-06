# Skills

Canonical, repo-agnostic skill definitions for the agent workspaces of
[davd-gzl](https://github.com/davd-gzl). Consumed as a git submodule, never
copied: `davd-gzl/agent-workspace` mounts this repo at `skills/`,
`samouraiworld/gno-agent-workspace` at `skills/core/` with its gno-specific
deltas beside it. A delta file only adds or overrides; it never restates what a
core file says.

## The workflow

Reviews run on demand, from chat: a PR, a branch, or a red CI, in any project
the workspace tracks. The agent syncs the checkout, reads the full diff and its
blast radius, verifies every claim with a real run, and drafts two artifacts:
the review file, the complete record, and a comment draft, the postable one.
Nothing reaches GitHub until the word `post` in the turn; drafts get pruned by
hand first.

## Why the style rules exist

Everything posted lands in front of a human maintainer who did not ask for it.
The one favor to do them is a comment that reads in one pass: the problem, its
stake, the line it sits on, and nothing else. Short sentences, plain English,
no jargon, no walkthrough of their own code, at most three sentences per
comment. A finding that cannot be said simply is not understood yet.
`writing-style.md` encodes this, and its closing Pass runs over every artifact
before it ships. The human reader outranks completeness: depth stays in the
review file, the comment carries only what changes what the author does next.

## Files

Paths inside the files (`skills/writing-style.md`) resolve from the consuming
workspace root. Edits land here first; consumers pick them up by bumping their
submodule pin.

- `review.md` — reviewing a PR, a branch, or a repository-level failure.
- `pr-body.md` — the title and body of a pull request.
- `issue.md` — drafting an issue for a problem a review found.
- `writing-style.md` — all visible prose, and the mandatory closing pass.
