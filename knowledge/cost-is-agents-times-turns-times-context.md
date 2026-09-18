# Cost is agents times turns times context

A round's cache read is every agent's turn count times the context each turn re-reads; output tokens are the minor term.

- One measured round: 55 agents, 984 turns, 52.6M cache read against 910k output.
- Every turn re-reads the opening context: the imports, the stage's rule bundle, the harness's tool schemas. On one machine the schemas alone were 30k of a 45k open; on another, 15k.
- Batching independent reads into one message cut the turns, not the work.
- One round set every baseline for weeks; a store of one row per agent, written as it ends, gives a median over hundreds. First read: 184 agents on one machine, median 20 turns, 29k output, 1.6M cache read, 88k context per turn. Source: `./scripts/agent-metrics.py summary` in the consumer workspace.

Source: the round's retro, `review-retro.py`, 2026-09.

Changes: cut the context first, the turns second, the agents last; a lever on agents alone loses findings; a baseline is read from the metrics store's summary, never from one round.
