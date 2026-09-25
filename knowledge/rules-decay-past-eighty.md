# Rules decay past eighty

What instruction count and context length do to adherence, read against the
set every session loads. Each line is one paper's measurement on the models
and instruction shapes it names, a claim to test here and not a fact.

- Perfect adherence falls to zero by 80 simultaneous rules, five models, one synthetic corpus, keyword-style rules. Source: [Prompt design at scale](https://arxiv.org/abs/2607.19257).
- Omission is the dominant failure as instructions grow from 10 to 500, earlier instructions are followed more, and the best model keeps 68% at 500; 20 models, keyword-inclusion instructions only. Source: [IFScale](https://arxiv.org/pdf/2507.11538). A year on, the ceiling sits near 2,000 and decay still starts far below it, a vendor blog and not a paper. Source: [Arize](https://arize.com/blog/llm-instruction-following-benchmark-2026/).
- Reasoning degrades at input lengths far under the context maximum; padding alone does it; 2024 models. Source: [Same task, more tokens](https://aclanthology.org/2024.acl-long.818/).
- The smallest set of high-signal tokens, with brittle if-else prompts named as a failure mode. Source: [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), kept whole in `skills/knowledge/context-engineering.md`.

- A source named inside a rule is context every turn loads for a reader who never opens it, so the rule states the action and this directory keeps the why.

Measure: `wc -w` over the files a session opens with for the loaded set, and
`grep -cE '^\s*[-0-9]' <file>` for its rule lines.

Changes: the thinking section sits first in `skills/short-form.md`; a rule
with no incident behind it leaves, per `skills/authoring.md`.
