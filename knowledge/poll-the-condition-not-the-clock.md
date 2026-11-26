# Poll the condition, not the clock

A test that sleeps a fixed time before checking async work guesses how long the work takes, so it passes on a fast machine and fails under load or in CI.

- One debugging session, reported by the author of a public skill pack with a TypeScript example drawn from it: 15 flaky tests across 3 files rewritten to poll the condition they waited for, under a timeout, took the pass rate from 60 to 100 percent and the run 40 percent faster. The project goes unnamed, and no control run is reported.

Source: [condition-based-waiting, Real-World Impact](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/condition-based-waiting.md#real-world-impact).

Changes: *Write tests for test-shaped findings* in `skills/review.md` has a test that waits on async work poll its condition under a timeout.
