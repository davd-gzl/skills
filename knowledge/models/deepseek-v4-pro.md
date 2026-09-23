# deepseek-v4-pro
DeepSeek's DeepSeek-V4-Pro, preview released 2026-04-24 and GA build DeepSeek-V4-Pro-0813 released 2026-08-13, open-weight (MIT) MoE flagship of the V4 series, 1.6T total and 49B active in the preview; the API id `deepseek-v4-pro` and the OpenCode id `deepseek-v4-pro` now serve the 0813 build. Source: [DeepSeek Change Log](https://api-docs.deepseek.com/updates/).

Identity and limits
- DeepSeek API: model `deepseek-v4-pro`, version DeepSeek-V4-Pro-0813, context 1M, max output 384K, thinking on by default, tool calls, JSON output, Responses API and Anthropic API, no vision. Source: [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing).
- 2026-09-10 release note said all `deepseek-v4-pro` requests would route to V4.1-Flash from 2026-09-14 until V4.1-Pro ships; the change log entry of the same date reverses it: V4 Pro API continues after 2026-09-14 with billing unchanged. Source: [DeepSeek-V4.1-Flash release note](https://api-docs.deepseek.com/news/news260910/), [DeepSeek Change Log](https://api-docs.deepseek.com/updates/).
- Preview card: 1.6T params, 49B activated, 1M context, FP4 + FP8 mixed weights, 32T+ training tokens. Source: [deepseek-ai/DeepSeek-V4-Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro).
- 0813 card: efforts low, high, max; max output 384K for high and max; temperature 1.0, top_p 0.95 for agentic use. Source: [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813).
- models.dev: OpenCode Zen `opencode/deepseek-v4-pro` reasoning_options toggle plus effort `high`, `max`; OpenCode Go `opencode-go/deepseek-v4-pro` ("DeepSeek V4 Pro (New)") effort `high`, `max`; both context 1,000,000, output 384,000, text only, interleaved `reasoning_content`. Source: [models.dev api.json](https://models.dev/api.json).

Reasoning effort
- GA update 2026-08-13: thinking modes of V4-Pro and V4-Flash support `low` / `high` / `max`; DeepSeek advises low for simple tasks, high for daily agent tasks, max for complex scenarios. Source: [DeepSeek Change Log](https://api-docs.deepseek.com/updates/).
- API: `reasoning_effort` default `high`; `medium`/`xhigh` map to high, `ultra` to max; thinking disabled with `{"thinking": {"type": "disabled"}}`. Source: [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode).
- V4 paper: reasoning tasks evaluated with context windows of 8K, 128K and 384K for Non-think, High and Max; Max adds a system-prompt instruction and uses reduced length penalties in RL. Source: [DeepSeek-V4 tech report, arXiv PDF](https://arxiv.org/pdf/2606.19348).
- OpenCode derives variants from models.dev's effort values (`reasoningVariants` in `packages/opencode/src/provider/transform.ts`, dev branch), giving `high` and `max` for this id. Source: [opencode transform.ts](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/provider/transform.ts).

Scores, vendor-reported
- Preview (2026-04-24), in-house harness with bash and file-edit tools, 500 steps, 512K context: SWE-bench Verified 73.6 / 79.4 / 80.6% for Non-think / High / Max; SWE-bench Pro 52.1 / 54.4 / 55.4%; SWE Multilingual 69.8 / 74.1 / 76.2%; Terminal-Bench 2.0 59.1 / 63.3 / 67.9%. Source: [deepseek-ai/DeepSeek-V4-Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro).
- Preview, tool use: MCPAtlas 69.4 / 74.2 / 73.6%, Toolathlon 46.3 / 49.0 / 51.8%, BrowseComp — / 80.4 / 83.4% (Non-think / High / Max). Source: [deepseek-ai/DeepSeek-V4-Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro).
- Preview, long context: MRCR 1M 44.7 / 83.3 / 83.5 MMR, CorpusQA 1M 35.6 / 56.5 / 62.0% (Non-think / High / Max); LiveCodeBench 56.8 / 89.8 / 93.5% pass@1. Source: [deepseek-ai/DeepSeek-V4-Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro).
- Preview, MRCR 8-needle curve (Figure 9, Pro-Max and Flash-Max): average MMR 0.84–0.94 from 8K to 128K, falling to 0.49–0.66 at 1024K; DeepSeek: "degradation becomes visible beyond the 128K mark". Source: [DeepSeek-V4 tech report, arXiv PDF](https://arxiv.org/pdf/2606.19348).
- 0813 GA (2026-08-13): Terminal-Bench 2.1 87.9, DeepSWE 62.7, NL2Repo 61.5, Toolathlon-Verified 74.1, CyberGym 83.3, HLE with tools 60.0, internal DSBench-FullStack 71.1 and DSBench-Hard 67.2. Source: [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813).
- DeepSeek's V4.1-Flash card, max effort, 2026-09-10: V4-Pro Terminal-Bench 3.0 11.8%, Terminal-Bench 4.0 12.4%, SEC-Bench Pro 56.4%, versus V4.1-Flash 30.0%, 31.2%, 62.8%. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).

Scores, independent
- Vals.ai, V4 Pro 0813 at max effort (no temperature parameter), 2026-08-12: SWE-bench Verified 96.40% in Vals' harness, #2 of 82 and top open-weight, $0.02 per test; Terminal-Bench 2.1 54.68% across three full trials, #33 of 52, 28.89% on hard tasks; Vals Index 52.37%. Source: [Vals AI: DeepSeek V4 Pro 0813](https://www.vals.ai/models/deepseek_deepseek-v4-pro-0813).
- Artificial Analysis Intelligence Index v4.3.2, 0813 max effort: 36; Terminal-Bench 4.0 14%, AA-LCR v1.1 80%, AA-Omniscience 1, SciCode 51%, AutomationBench-AA 57%; 67 output tokens/s, TTFT 1.66 s, time to first answer token 31.48 s, 55k output tokens per task of which 38k reasoning, checked 2026-09-24. Source: [AA: V4.1 Flash vs V4 Pro](https://artificialanalysis.ai/models/comparisons/deepseek-v4-pro-vs-deepseek-v4-1-flash).
- Artificial Analysis: 160M output tokens to run the index, verbosity #21/114. Source: [AA: DeepSeek V4 Pro 0813](https://artificialanalysis.ai/models/deepseek-v4-pro).
- SWE-bench official leaderboard data: no DeepSeek V4-family row; newest Verified row dated 2026-02-26. Source: [SWE-bench leaderboards.json](https://raw.githubusercontent.com/SWE-bench/swe-bench.github.io/master/data/leaderboards.json).
- Aider polyglot: no V4-family row. Source: [Aider leaderboards](https://aider.chat/docs/leaderboards/).
- tbench.ai and contextarena MRCR: pages render client-side, no data found. Source: [tbench.ai leaderboard](https://www.tbench.ai/leaderboard), [Context Arena](https://contextarena.ai/).
- Code-review or bug-finding benchmark: none in the vendor cards; no data found. Source: [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813).

Known weaknesses
- Vals.ai: "struggles on terminal-driven coding and Excel tasks" (Terminal-Bench 2.1 54.68%, EMB 52.80%). Source: [Vals AI: DeepSeek V4 Pro 0813](https://www.vals.ai/models/deepseek_deepseek-v4-pro-0813).
- DeepSeek: long-context retrieval degrades past 128K on MRCR 8-needle. Source: [DeepSeek-V4 tech report, arXiv PDF](https://arxiv.org/pdf/2606.19348).
- DeepSeek's own later card puts V4-Pro well behind V4.1-Flash on long-horizon terminal tasks (Terminal-Bench 3.0 11.8 vs 30.0). Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- OpenClaw issue #72044 (2026-04-26, open): thinking `high` fails multi-turn tool-call flows with "400 The `reasoning_content` in the thinking mode must be passed back to the API." when a client replays empty reasoning. Source: [openclaw #72044](https://github.com/openclaw/openclaw/issues/72044).
- Slow: 67 tokens/s and 31 s to first answer token at max, per Artificial Analysis. Source: [AA: V4.1 Flash vs V4 Pro](https://artificialanalysis.ai/models/comparisons/deepseek-v4-pro-vs-deepseek-v4-1-flash).

Price per 1M tokens
- DeepSeek API `deepseek-v4-pro`: input cache miss $0.66 off-peak / $1.32 peak, cache hit $0.022 / $0.044, output $1.98 / $3.96; peak 01:00–04:00 and 06:00–10:00 UTC weekdays; no cache-write fee and no long-context tier listed. Source: [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing).
- OpenCode Zen `deepseek-v4-pro`: input $1.74, output $3.48, cached read $0.145, cached write none (models.dev lists output $3.84). Source: [OpenCode Zen](https://opencode.ai/docs/zen/).
- OpenCode Go `deepseek-v4-pro`: input $0.66–$1.32, output $1.98–$3.96, cached read $0.022–$0.044 (off-peak/peak), monthly limit $15. Source: [OpenCode Go](https://opencode.ai/docs/go/).
- models.dev `deepseek/deepseek-v4-pro` still lists $0.435 in / $0.87 out / $0.003625 cache read, older than DeepSeek's current page. Source: [models.dev api.json](https://models.dev/api.json).

Inference for review stages (not measured here):
- Finder diff size: MRCR held flat to 128K and degraded past it; keep one finder's context under about 128K, roughly 1,500 changed lines with context per finder.
- Judge batch: 67 tokens/s and 55k output tokens per task at max make each rerun slow; 3–5 candidates per judge context at `high`.
- Effort: finder `high` (SWE-bench Verified 79.4 vs 80.6 at max, MRCR 1M 83.3 vs 83.5), judge `high`, writer `low`, triage `low`. DeepSeek's own and Vals' terminal numbers put V4.1-Flash ahead at lower price for judge reruns.

Changes: the reading the triage plans for a round on this model, *Triage* in `skills/review.md`: finder groups, judge batches and each stage's effort, read here through `./scripts/review-setup.sh --model`.
