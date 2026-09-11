# TODO

Skill work the user owns. One line each, newest last.
- The finished-work account in `shortcuts.md` is prose, so it renders differently
  every turn. It needs a fixed template: the exact lines, in order, with the
  slots named. Written as a rule it drifts; written as a shape it does not.
- The caveman register in `writing-style.md` is described with adjectives, so it
  drifts back to prose as a session runs and nothing measures it: `prose-check.py`
  reads drafted artifacts, never a chat reply. Give it a ceiling that can be
  checked, and consider injecting the register's sample line on every prompt
  rather than once at session start.
- `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` are exported in this environment,
  and env beats `git -c user.email`, so the *Commit identity* table in
  `workspace.md` is silently unenforceable: a public-repo commit goes out under
  the real address whatever the `-c` flag says. 18 commits in
  `samouraiworld/gno-agent-workspace` already carry it. The rule needs the env
  form, or a hook that refuses the commit.
- `prose-check.py` counts words, clauses and verbs, so it passes a finding whose
  terms only the session can expand: three in one review had to be explained in
  chat before they could be read. Steps 8 and 9 of the `writing-style.md` Pass
  are the checks for it and neither has a runnable form, so a clean
  `prose-check.py` reads as a finished pass. The expandability test is now a
  rule in `review-comment.md`; what is left here is whether a check can run, or
  whether the Pass has to say it is a human read. Estimate: one afternoon for a
  term-extraction check, or one line if the Pass just states it.
