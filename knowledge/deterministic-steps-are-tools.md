# Deterministic steps are tools

A step a script can decide is written once as a tool; as prose it is re-derived by a model every round, differently each time, and paid for in turns.

- About twenty parent turns per round before a finder started, each fixed work.
- 324 of 1045 agent calls on one round were `sed`, `grep` and `cat` re-deriving a four-file diff the parent already held.
- A 304-line link table built by an agent; `round links` writes it in seven seconds.
- The paper's reviewer gives its agent six output-capped tools and a 30-call loop, and credits the caps for stopping the token snowball.

Source: the retro of one round and `round links` timed, 2026-09; the OpenCodeReview paper.

Changes: setup, the diff, the prior checks, the links, the sweep and the retro are `round` subcommands; every stage sees a tools manifest before a shell verb.
