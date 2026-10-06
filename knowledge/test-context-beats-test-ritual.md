# Test context beats a test ritual

Telling a coding agent which existing tests reach the code it edits cuts the regressions it ships; telling it to work test-first does not, and neither does asking it for more tests of its own.

- TDAD, SWE-bench Verified, Qwen3-Coder 30B on 100 instances: regressions 6.08 percent with no intervention, 9.94 percent with test-driven instructions alone, 1.82 percent with a code-to-test map the agent queries; as a skill on another model and harness, resolved issues went from 24 to 32 percent. Small open-weight models and a small sample.
- Agent-written tests, SWE-bench Verified, trajectories of six strong models: resolved and unresolved tasks show the same test-writing rate, the tests mostly print values rather than assert, and prompting four models for more or fewer tests left the outcome statistically unchanged.

Source: [TDAD](https://arxiv.org/abs/2603.17973), [Rethinking the value of agent-generated tests](https://arxiv.org/abs/2602.07900).

Changes: *Fix* step 2 in `skills/change.md` lists and runs the tests reaching the touched code before the first edit, and adds no test-first step.
