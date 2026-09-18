# A doc with catalog words is not cold

The risk score weighs changed lines, catalog keywords and fix history and tiered
every doc cold, while the claims angle walks a doc for what it asserts about the
running code, which no line count measures.

- On one round the tiers came out inverted: cold confirmed 5 of 5 rows, hot 8 of 14, warm 0 of 6. The cold rows were a 109-line decision record under the claims angle, where the round's only Warning sat, and two test files; the warm rows were two code files whose candidates all refuted or came back PLAUSIBLE.

Source: [gnolang/gno#6206](https://github.com/gnolang/gno/pull/6206), the hit rate per tier in the Retro of https://github.com/samouraiworld/gno-agent-workspace/blob/main/reviews/pr/6xxx/6206-gnoweb-user-page-gate/1-876762b/claims.md; one round, the first recorded.

Changes: the tier of a doc in `round risk`: cold with no catalog keyword in its added lines, warm with one, hot past the threshold code takes.
