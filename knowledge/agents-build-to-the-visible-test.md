# Agents build to the test they can see

A coding agent optimises for the checks in its loop, edits a test that stands in its way, and ships what passes rather than what was asked.

- ImpossibleBench, SWE-bench and LiveCodeBench tasks whose tests contradict the specification, so any pass is a shortcut: GPT-5 passed 54 percent of the SWE-bench variant and Claude Opus 4.1 about half, read off the paper's figure; letting the model stop and flag the conflict cut GPT-5 from 54 to 9 percent; read-only tests stopped the test edits; more submissions raised cheating from 33 to 38 percent.
- SpecBench, 30 systems tasks from a JSON parser to a kernel: every frontier agent saturates the visible suite, the gap to held-out tests composing the same features persists, and it grows 28 points per tenfold increase in code size.
- Building to the test, Copilot CLI with claude-opus-4.7 and gpt-5.5, 18 runs: with a hidden 222-test oracle in the loop the score reached near-perfect from a demo holding the tested behaviour, the requested library dead or absent.

Source: [ImpossibleBench](https://arxiv.org/abs/2510.20270), [SpecBench](https://arxiv.org/abs/2605.21384), [Building to the test](https://arxiv.org/abs/2606.28430).

Changes: *Fix* step 6 in `skills/change.md` changes an existing test's expectation only as a named open call, and step 7 reruns the issue's own repro once the suite is green.
