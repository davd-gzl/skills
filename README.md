# Skills

Canonical, repo-agnostic skill definitions for agent workspaces. Consumed as a
git submodule, never copied: `davd-gzl/agent-workspace` mounts this repo at
`skills/`, `samouraiworld/gno-agent-workspace` at `skills/core/` with its
gno-specific deltas beside it. A delta file only adds or overrides; it never
restates what a core file says.

Paths inside the files (`skills/writing-style.md`) resolve from the consuming
workspace root. Edits land here first; consumers pick them up by bumping their
submodule pin.

- `review.md` — reviewing a PR, a branch, or a repository-level failure.
- `pr-body.md` — the title and body of a pull request.
- `issue.md` — drafting an issue for a problem a review found.
- `writing-style.md` — all visible prose, and the mandatory closing pass.
