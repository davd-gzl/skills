# Nothing is measured until labelled

A finding is real when the author acts on it; a verdict of confirmed says the check ran, not that the finding mattered.

- 401 rounds on disk, one with an outcome table, none with a finding labelled real or false by the user.
- The one number production teams watch is the resolution rate, findings the author fixed or resolved over findings posted; one tool moved it from 52 to over 70 percent in six months.
- A precision and recall benchmark exists, 200 pull requests over 50 repositories with 1,505 annotated issues.

Source: the corpus on 2026-09-17; the Bugbot post and the AACR benchmark linked from `narrow-first-filter-after.md`.

Changes: `review-outcomes.py` prints the resolution rate per round and per preset, and one labelled round per preset is the first data point for any shape change.
