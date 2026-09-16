# A guard needs its own test

A guard that exits without a word passes every audit that reads its exit code; only a test that demands the hit line catches it.

- The push scrub exited 1 silently twice under `set -e`: a false test at the end of a function, then a grep selecting nothing under `pipefail`.
- A tree audit through `git grep` skipped every untracked file, so a fixture naming a private repository passed it.
- A fixture holding a token shape is itself a hit; the shape is built at run time instead.

Source: `scripts/tests/test_scrub.sh`, 2026-09-17.

Changes: every guard in `scripts/` ships with a test that asserts its output, and a first audit reads untracked files too.
