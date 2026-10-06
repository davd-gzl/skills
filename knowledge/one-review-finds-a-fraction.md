# One review finds a fraction of the issues

Review agents on real pull requests find a minority of what human reviewers found, and extra reflection buys recall with noise.

- c-CRAB, tasks built from human reviews of real pull requests, PR-agent and the review agents of Devin, Claude Code and Codex: all of them together solve about 40 percent of the tasks, and they often look at different aspects than the human reviewers did.
- SWR-Bench, 1000 manually verified pull requests with full project context: current tools and models underperform, and aggregating several reviews raises F1 by up to 43.67 percent.
- CR-Bench, two frontier models: a reflect-and-revise review agent found more hidden issues than a single-shot one at a lower signal-to-noise ratio, on GPT-5.2 recall 27.0 to 32.8 percent and the ratio 5.11 to 1.95, from the paper's results table.
- Inferred, measured by none of these: a loop that waits for an empty round keeps sampling new findings rather than converging. Aggregating several reviews inside one round, what SWR-Bench measured, is what a round's parallel finders already do, and runs against stopping early only within a round.

Source: [c-CRAB](https://arxiv.org/abs/2603.23448), [SWR-Bench](https://arxiv.org/abs/2509.01494), [CR-Bench](https://arxiv.org/abs/2603.11078).

Changes: *Fix* step 8 in `skills/change.md` and the Own PR round loop in `skills/review-modes.md` stop on a pass or round with no Critical or Warning, or one whose Criticals and Warnings all sit on the previous one's fix. Porting each applied Critical's and Warning's repro into the branch's suite comes from the workspace's own rounds, not from these sources.
