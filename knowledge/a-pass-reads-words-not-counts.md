# A pass reads words, not counts

A stage that reads prose is gated on the words it will read, never on the count of things carrying them.

- One round of ten one-sentence findings skipped the text pass under a four-finding floor, and the prose check then named 14 fixes, nine of them sentences over 30 words, rewritten by hand.
- The same words in four long findings would have run the pass; the count said nothing about the prose.

Source: one public round of the review workflow, its draft against `./scripts/prose-check.py`, 2026-09.

Changes: `text.min_words` replaces `text.min_findings` in the runner, every preset gating on the kept findings' visible words and `quick` lowering the floor rather than dropping the stage.
