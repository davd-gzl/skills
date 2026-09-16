# Cost is agents times turns times context

A round's cache read is every agent's turn count times the context each turn re-reads; output tokens are the minor term.

- One measured round: 55 agents, 984 turns, 52.6M cache read against 910k output.
- Every turn re-reads the opening context: the imports, the stage's rule bundle, the harness's tool schemas. On one machine the schemas alone were 30k of a 45k open; on another, 15k.
- Batching independent reads into one message cut the turns, not the work.

Source: the round's retro, `review-retro.py`, 2026-09.

Changes: cut the context first, the turns second, the agents last; a lever on agents alone loses findings.
