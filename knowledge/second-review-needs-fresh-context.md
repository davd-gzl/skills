# A second review needs a fresh context

Reviewing again in the session that produced the work finds less than reviewing once in a session that never saw it.

- Cross-Context Review, 30 artifacts, code, technical documents and scripts, with 150 injected errors, four conditions over three runs: a review in a fresh session reached F1 28.6 percent against 21.7 percent for a second review in the producing session, Holm-adjusted p=0.004. Against a single same-session review, 27.1 percent, and a context-aware subagent, 23.8 percent, the fresh session was not significantly ahead. Claude Opus 4.6 through the Claude Code agent tool; one small controlled set, its code ten single Python functions.

Source: [Cross-Context Review](https://arxiv.org/abs/2603.12123).

Changes: *Fix* step 8 in `skills/change.md` reads its first pass in the session and runs every later pass in a fresh agent given the issue, the plan and the diff.
