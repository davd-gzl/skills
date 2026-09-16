# Narrow first, filter after

Production reviewers narrow the work with code before any model reads, run one bounded agent per unit, and filter with one pass that can only remove.

| Tool | Before the model | The agent | After |
| --- | --- | --- | --- |
| OpenCodeReview | rules pick files, four tiers, first match wins | one per file, six capped tools, 30 calls, context compressed at 60 percent | a reflector on the diff alone, filter-only |
| Bugbot | rules per repository, 44k learned | one agentic loop over the diff, effort levels | a validator, then prompts kept aggressive |
| CodeRabbit | context deduplicated, compressed, ranked; cheap models triage | the strong model on what triage kept | a verification agent per suggestion |
| Anthropic's review agents | | several agents in parallel | a verification stage of more agents |

- On the same model, the paper's shape reached F1 25 and precision 34 at 385k tokens and 83 seconds per pull request; the general agent F1 12, precision 7, 5.7M tokens, 13 minutes.
- Anthropic reports under 1 percent of findings marked wrong at 15 to 25 dollars a pull request; Bugbot a dollar or two.

Source: the [paper](https://arxiv.org/html/2608.09290v1), [Building a better Bugbot](https://cursor.com/blog/building-bugbot), the [CodeRabbit deep dive](https://www.coderabbit.ai/blog/coderabbit-deep-dive), the [review agents](https://tessl.io/blog/anthropic-launches-ai-code-review-agents-that-scan-pull-requests-for-bugs), the [cost survey](https://blog.codacy.com/ai-code-review-cost-per-pull-request-what-engineering-teams-actually-pay-in-2026).

Changes: `round dispatch` narrows, one agent per bundle reads, a reflector filters; the run-per-claim verifier is the `deep` step, not the default.
