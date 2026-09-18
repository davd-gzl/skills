# Rules are read by position

What research says about how a model reads a rule file, read for *The shape*
in `skills/authoring.md`. Each line is one paper's measurement on the models it
names, a claim to test here and not a fact.

- Rules at a prompt's start and end are followed; mid-prompt rules lose 30 to 50% of compliance, a U-shaped curve from position embeddings; older chat models, summarised by a vendor. Sources: [Primacy effect of ChatGPT](https://arxiv.org/pdf/2310.13206), [position bias summary](https://intuitionlabs.ai/articles/llm-position-bias-primacy-recency-effects).
- A prohibition is read as the action it names often enough to fail audits; late attention heads promote the positive answer on a negated prompt; open models, comprehension tasks. Sources: [When prohibitions become permissions](https://arxiv.org/html/2601.21433), [How language models process negation](https://arxiv.org/html/2605.03052v1).
- Three-shot examples help 15 of 20 models and hurt some; past a few, domain examples degrade answers; instruction-tuned models on benchmark tasks. Sources: [The atomic instruction gap](https://arxiv.org/pdf/2510.17388), [The few-shot dilemma](https://arxiv.org/html/2509.13196v1).
- Perfect adherence falls to zero by 80 simultaneous rules and placement, system prompt against user turn, moves results as much as format, direction per model; five models, synthetic corpus. Source: [Prompt design at scale](https://arxiv.org/abs/2607.19257).

Changes: *The shape* puts what matters first and last, names the action over
its absence, and takes one example, never a list; the intro says what decays
is the set loaded at once.
