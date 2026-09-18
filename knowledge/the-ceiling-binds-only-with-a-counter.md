# The ceiling binds only with a counter

The runner reads its spend from a counter the harness keeps, and the harness
keeps one only when the word carries `+<n>`; the config's `budget_total` alone
sets a ceiling nothing measures against.

- One round on the standard word, ceiling 1M, stood at 3.83M output with the writer still to run, 3.04M of it from the finders, every stage launched.

Source: [gnolang/gno#6194](https://github.com/gnolang/gno/pull/6194), `./scripts/review-retro.py` over its round's workflow directory.

Changes: the Launch bullet of `review.md`, the preset row of `shortcuts.md` and the README's ceiling sentence say the ceiling binds with `+<n>` alone, and the runner logs at launch when no counter runs.
