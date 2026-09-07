# Chat register test

Measures a wording of *Short form* in `writing-style.md` against the caveman
plugin's skill text and against no rule, on that plugin's ten benchmark
prompts, per *Measuring a rule* in `authoring.md`.

- `run.py` fetches the plugin's `SKILL.md` and `prompts.json` at the pinned
  sha, then runs `claude -p` with tools, skills, plugins and settings off, two
  trials per prompt and condition, into `out2/`. `MODEL` and `EFFORT` come from
  the environment, default `fable` and `medium`.
- `metrics.py` counts prose words, articles, filler, hedges and pleasantries
  with code excluded, and drops answers that are fake tool transcripts.
- `judge.py` scores every clean answer blind, labels hidden and order shuffled,
  on single-pass readability and substance; `judge_report.py` tabulates it.
- `rule.md` to `rule6.md` are the wordings tried, `results.md` the run of
  2026-09-06 at effort `xhigh` that chose `rule5.md`, trimmed into `rule6.md`
  for the word budget.
