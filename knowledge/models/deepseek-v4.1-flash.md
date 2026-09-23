# deepseek-v4.1-flash
DeepSeek's DeepSeek-V4.1-Flash, released 2026-09-10, open-weight (MIT) multimodal MoE, 552B backbone, 8B active on prefill and 16B on decode, the small tier of a new Causal Encoder-Decoder family; `deepseek-v4.1-flash` is the OpenCode (Zen and Go) id, DeepSeek's own API id is `deepseek-flash`. Source: [DeepSeek-V4.1-Flash release note](https://api-docs.deepseek.com/news/news260910/).

## Inference for review stages, not measured here

Read first; a measurement in `scripts/workflows/review-pipeline.json` outranks every line of it.

- Finder diff size: no MRCR for this model; AA-LCR 84% and DeepSeek's own flag on sparse long-context retrieval suggest keeping one finder's context near the 128K band where the V4 family's MRCR held flat, roughly 1,500 changed lines with context per finder.
- Judge batch: about 89k output tokens per agentic task at max (AA) and 1.6–1.8x longer trajectories at max; 5–8 candidates per judge context at `high`, fewer if each reruns a test suite.
- Effort: finder `high` (75, the 60–80 band recovers most accuracy), judge `high`, `max` only for a candidate that stays unresolved; writer `low`; triage `low`. Vals ran `high` and still placed #2 open-weight on Terminal-Bench 2.1.

## Sources

Identity and limits
- DeepSeek API: model name `deepseek-flash`, version DeepSeek-V4.1-Flash, context 1M, max output 384K, thinking on by default, tool calls, JSON output, vision, Responses API and Anthropic API; legacy `deepseek-v4-flash` and `deepseek-v4-flash-vision-exp` now served by V4.1-Flash. Source: [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing).
- Tech report: 45T-token multimodal pretraining, sparse attention trained at 64K and extended to 1M at 34T tokens; submitted to arXiv 2026-09-17. Source: [DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression](https://arxiv.org/abs/2609.19969).
- Model card: recommends temperature 1.0, top_p 0.95 or 1.0, max output of at least 256K. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- models.dev lists OpenCode Zen `opencode/deepseek-v4.1-flash` and OpenCode Go `opencode-go/deepseek-v4.1-flash`: context 1,000,000, output 384,000, tool_call true, image input, interleaved reasoning in `reasoning_content`, reasoning_options effort `low`, `high`, `max`, release 2026-09-10. Source: [models.dev api.json](https://models.dev/api.json).

Reasoning effort
- DeepSeek API: thinking toggled by `{"thinking": {"type": "enabled"|"disabled"}}`; `reasoning_effort` accepts `low`, `high`, `max`, default `high`; `minimal`→low, `medium`/`xhigh`→high, `ultra`→max. Source: [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode).
- Underlying control is a scalar effort 1–100; API tiers map low=50, high=75, max=100 (Table 2). Source: [V4.1-Flash tech report, arXiv PDF](https://arxiv.org/pdf/2609.19969).
- OpenCode builds variants from models.dev's reasoning_options effort values (`reasoningVariants` in `packages/opencode/src/provider/transform.ts`, dev branch); models.dev currently lists `low`, `high`, `max`, so the harness's `high` and `max` variants map to effort 75 and 100. Source: [opencode transform.ts](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/provider/transform.ts).
- Effort 25→100: DeepSWE v1.1 66.0%→74.2%, Terminal-Bench 2.1 82.4%→90.6%, about 2.5x output tokens; effort 60–80 recovers most of max accuracy at under half the tokens; the step to 100 lengthens agent trajectories 1.6–1.8x for marginal gains. Source: [V4.1-Flash tech report, arXiv PDF](https://arxiv.org/pdf/2609.19969).

Scores, vendor-reported (max effort = reasoning_effort 100, 2026-09-10)
- DeepSWE v1.1 74.2% resolved, mini-SWE scaffold, N=8 per task, max_steps 500, 1M context; V4-Pro 62.7%, Opus-5.0 74.0%. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- Terminal-Bench 2.1 90.6% pass@1, DeepSeek Harness Minimal, N=3, no network; V4-Pro 87.9%. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- Terminal-Bench 3.0 30.0% and Terminal-Bench 4.0 31.2% pass@1; V4-Pro 11.8% and 12.4%, Opus-5.0 43.3% and 51.8%. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- By scaffold, max effort: DeepSWE v1.1 Claude Code 69.8%, Codex 65.6%, OpenCode 65.5%, Pi 66.2%, mini-SWE 74.2%; Terminal-Bench 2.1 Claude Code 88.0%, Codex 84.1%, OpenCode 85.0%, Pi 86.1%. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- NL2Repo-Bench 64.0, CyberGym 88.1% pass@1, SEC-Bench Pro 62.8% pass@1, HLE with tools 63.9%, AutomationBench 54.8%. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).
- Long context: only LongBench-V2 on the base model, 45.2 EM 1-shot (V4-Pro-Base 51.5); no MRCR or CorpusQA for the instruct model in the card or report. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).

Scores, independent
- Artificial Analysis Intelligence Index v4.3.2: 39 (V4-Pro 0813: 36), reasoning max effort; Terminal-Bench 4.0 27%, AA-LCR v1.1 long-context 84%, AA-Omniscience −5, SciCode 52%, AutomationBench-AA 69%, checked 2026-09-24. Source: [AA: V4.1 Flash vs V4 Pro](https://artificialanalysis.ai/models/comparisons/deepseek-v4-pro-vs-deepseek-v4-1-flash).
- Artificial Analysis speed: 227 output tokens/s, TTFT 1.08 s, 89k output tokens per task of which 63k reasoning, 253M tokens to run the index. Source: [AA: V4.1 Flash vs MiniMax-M3](https://artificialanalysis.ai/models/comparisons/deepseek-v4-1-flash-vs-minimax-m3).
- Vals.ai, high reasoning effort, temperature 1: Terminal-Bench 2.1 74.53% across three full trials (#2 open-weight), Vals Index 57.86%, Vibe Code Bench 84.74%, Code Migration 45.62%, SkillsBench 69.80% with skills, evaluated 2026-09-10. Source: [Vals AI: DeepSeek V4.1 Flash](https://www.vals.ai/models/deepseek_deepseek-v4.1-flash).
- SWE-bench official leaderboard data: no DeepSeek V4-family row; newest Verified row dated 2026-02-26. Source: [SWE-bench leaderboards.json](https://raw.githubusercontent.com/SWE-bench/swe-bench.github.io/master/data/leaderboards.json).
- Aider polyglot: no V4-family row; newest DeepSeek row is V3.2-Exp. Source: [Aider leaderboards](https://aider.chat/docs/leaderboards/).
- tbench.ai and contextarena MRCR: pages render client-side, no data found. Source: [tbench.ai leaderboard](https://www.tbench.ai/leaderboard), [Context Arena](https://contextarena.ai/).
- Code-review or bug-finding benchmark: none in the vendor card; no data found. Source: [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash).

Known weaknesses
- DeepSeek: new CSA2 selection and SWA Bounded Replay "may still cause capability degradation in untested boundary cases", naming sparse retrieval over long contexts as the area under stress-testing. Source: [V4.1-Flash tech report, arXiv PDF](https://arxiv.org/pdf/2609.19969).
- DeepSeek: a gap remains to leading closed models on the hardest tasks despite near-parity scores. Source: [V4.1-Flash tech report, arXiv PDF](https://arxiv.org/pdf/2609.19969).
- OpenCode issue #49673 (logser13, 2026-09-18, open): answer emitted only in reasoning (finish stop, output 0) in 5 of 1,715 messages, and reasoning leaking into visible text on the direct DeepSeek API. Source: [opencode #49673](https://github.com/anomalyco/opencode/issues/49673).
- Verbosity: 250M output tokens to run AA's index versus a 140M median; community reports of reasoning continuing after the work is done, over an hour in one CLI session (unverified by the author). Source: [OrcaRouter: V4.1 Flash in OpenCode](https://www.orcarouter.ai/blog/deepseek-v4-1-flash-opencode).
- Tool calls on self-hosted vLLM: new spaced tag format passes through as text unless `--tool-parser deepseek_v41` is set (2026-09-22). Source: [OrcaRouter: V4.1 tool calling in vLLM](https://www.orcarouter.ai/blog/deepseek-v4-1-tool-calling-vllm).
- Thinking mode with tools: all prior `reasoning_content` must be passed back when `tools` is set. Source: [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode).

Price per 1M tokens
- DeepSeek API `deepseek-flash`: input cache miss $0.15 off-peak / $0.30 peak, cache hit $0.003 / $0.006, output $0.60 / $1.20; peak 01:00–04:00 and 06:00–10:00 UTC weekdays; no cache-write fee and no long-context tier listed. Source: [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing).
- OpenCode Zen `deepseek-v4.1-flash`: input $0.30, output $1.20, cached read $0.006, cached write none. Source: [OpenCode Zen](https://opencode.ai/docs/zen/).
- OpenCode Go `deepseek-v4.1-flash`: input $0.15–$0.30, output $0.60–$1.20, cached read $0.003–$0.006 (off-peak/peak), monthly limit $60 under a 4x promo. Source: [OpenCode Go](https://opencode.ai/docs/go/).
- OpenCode usage data: #1 by OpenCode usage last week, 13% token share, 97% of input tokens cached, Jul 30–Sep 23 2026. Source: [OpenCode Data: DeepSeek V4.1 Flash](https://opencode.ai/data/deepseek/deepseek-v4.1-flash).

Changes: the reading the triage plans for a round on this model, *Triage* in `skills/review.md`: finder groups, judge batches and each stage's effort, read here through `./scripts/review-setup.sh --model`.
