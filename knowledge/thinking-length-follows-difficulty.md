# Thinking length follows difficulty

What research says about cutting the reasoning before a reply. Each line is
one paper's measurement on the models and benchmarks it names, a claim to test
here and not a fact.

- Every prompt cap, "be concise", "ten words or less", "no punctuation", sits on one accuracy-versus-length curve; each problem has its own minimum token count, and the gain is adaptive length, short on easy steps, long on hard ones; GSM8K and math sets, no code. Source: [Token complexity](https://arxiv.org/abs/2503.01141).
- Which step is cut decides the outcome: 80% of low-entropy intermediate steps prune with no significant accuracy loss, while random or high-entropy pruning severely impairs the same models; DeepSeek-R1-7B, 14B and Qwen3-8B. Source: [Step entropy](https://mlanthology.org/iclr/2026/li2026iclr-making/).
- Telling a model that already reasons internally how to reason buys little: o3-mini +2.9%, o4-mini +3.1%, Gemini Flash 2.5 -3.3%, for 20 to 80% more wall clock. Source: [The decreasing value of chain of thought](https://gail.wharton.upenn.edu/research-and-insights/tech-report-chain-of-thought/).
- A per-question budget cuts output tokens 67% with under 3% accuracy lost; a tight fixed budget is overrun anyway; GPT-4o-mini over seven math and reasoning sets. Source: [TALE](https://aclanthology.org/2025.findings-acl.1274/).
- Drafts of a few words per step keep accuracy at 7.6% of chain-of-thought tokens on math and commonsense, GPT-4o and Claude 3.5 Sonnet, visible reasoning and not a thinking block. Source: [Chain of Draft](https://arxiv.org/abs/2502.18600).
- On SWE-bench the same drafts cost 55% of the tokens and hold over 90% of the quality; the shortest variant fits routine fixes, a hierarchical one multi-layer problems; 300 samples, quality judged and not resolve rate. Source: [Chain of Draft for software engineering](https://arxiv.org/abs/2506.10987).
- "Be concise" alone halves reasoning length with no measured accuracy loss on GPT-4, and a loss on GPT-3.5 math. Source: [Concise chain of thought](https://arxiv.org/pdf/2401.05618).
- Suppressing "Wait" and "Hmm" self-reflection shortens chains 27 to 51% across ten benchmarks on R1-style open models, accuracy held or up, a logit filter and not a prompt. Source: [NoWait](https://aclanthology.org/2025.findings-emnlp.394/).
- Notation for arithmetic, concept chains for logic and expert terms for a domain cut up to 84% over 18 datasets, with a router picking the form. Source: [Sketch-of-Thought](https://aclanthology.org/2025.emnlp-main.1236/).
- Skipping thinking matches long thinking at low budget on AIME and AMC, distilled open models. Source: [NoThinking](https://arxiv.org/abs/2504.09858).
- On SWE-bench, reasoning in place of acting lowers success; picking the low-overthinking run gains near 30% at 43% less cost, and analysis paralysis is the top pattern; 4,018 trajectories, one scaffold. Source: [The danger of overthinking](https://arxiv.org/abs/2502.08235).
- Reusable reasoning recipes retrieved at inference cut tokens and raise accuracy on code and math, an industry-track result. Source: [Thinking with reasoning skills](https://aclanthology.org/2026.acl-industry.154/).
- Prompt-based length control works but is not robust across models, so a wording is measured. Sources: [Stop overthinking](https://arxiv.org/abs/2503.16419), [Concise and adaptive thinking](https://arxiv.org/pdf/2507.09662).
- Claude's adaptive thinking follows system-prompt guidance, wording-sensitive; effort is the calibrated lever and comes first, and a change is measured on sample traffic. Sources: [Steering thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost), [Effort](https://platform.claude.com/docs/en/build-with-claude/effort).

Changes: `skills/thinking.md`: length by difficulty and never a count, each
step opening with how it is known, one pass, nothing already in context
restated, lifted where effort sets the model's thinking; *Claims* in
`skills/short-form.md`: a claim in the reply rests on a command.
