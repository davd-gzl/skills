# Nothing is measured until labelled

A finding is real when the author acts on it; a verdict of confirmed says the check ran, not that the finding mattered.

- 401 rounds on disk, one with an outcome table, none with a finding labelled real or false by the user.
- The one number production teams watch is the resolution rate, findings the author fixed or resolved over findings posted; one tool moved it from 52 to over 70 percent in six months, self-reported by its vendor.
- A precision and recall benchmark exists, 200 pull requests over 50 repositories, ten languages, expert-verified labels; the 1,505 issue count is from an earlier read and not on the abstract. Source: [AACR-Bench](https://arxiv.org/abs/2601.19494).

Source: the corpus on 2026-09-17; the Bugbot post linked from `narrow-first-filter-after.md`; AACR-Bench above.

Changes: `review-outcomes.py` prints the resolution rate per round and per preset, and one labelled round per preset is the first data point for any shape change.
