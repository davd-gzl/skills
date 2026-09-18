# Three angles return polish, not defects

The claims, tests and refactor angles return what an author acts on after
merge: a Suggestion, a Nit, a missing test. On one 3,000-line target reviewed
at the complex class, they produced 88 of 168 verdicts and 5 of the 15
confirmed Warnings, four of them from claims and one from refactor, while
lines, reach and the catalog carried the other 10. All five sat on code files,
so a claims angle gated on doc bundles drops them.
The same round's low-band output was 77 Nits and 58 Suggestions, and its cost
was about 360 dollars against a 31 dollar projection for the quick preset.

Conditions: one target, one project, one round, judged by agents whose refute
rate that round was 12 of 168, and 73 of its 241 findings never reached a judge, so the confirmed counts are an upper bound.

Source: `./scripts/review-retro.py` over the round's workflow directory, and
the verdict files under the round directory grouped by angle and band.

Changes: tests and refactor moved to the `deep` preset in
`scripts/workflows/review-pipeline.json`, claims to a bundle carrying a doc
under `finder.claims_docs_only`, and the `review` word's low-band cap from 6 to
3 under a round-wide 24.
