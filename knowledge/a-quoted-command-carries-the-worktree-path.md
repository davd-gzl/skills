# A quoted command carries the worktree path

A judge is handed absolute worktree paths in its prompt and quotes the command it
ran back into its verdict, which is right for a record and wrong for a public
artifact: the path names the machine's home directory and the workspace.

- On one round nine occurrences of the head worktree's absolute path went into `claims.md`, `findings.md` and one finder's candidates file, pasted from `grep -n <file>` command lines into the Check column, and the parent caught them with a hand-written grep before the push; the private-names list holds repository names and handles and no path prefix, so the check passed them.

Source: `grep -rlE '/home/|/tmp/claude' <round dir>` over the round at https://github.com/samouraiworld/gno-agent-workspace/blob/main/reviews/pr/6xxx/6206-gnoweb-user-page-gate/1-876762b/claims.md, before that pass.

Changes: `round check` fails on an absolute path outside the reviewed repo over the round's record, and `round assemble` cuts the head worktree and every scratch worktree prefix from each cell it writes.
