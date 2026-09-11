# Review shapes, measured on one target

Three shapes the review has run as, each measured on one private target, a
27-file fix. A record, nothing loads it: the current shape is in
`README.md` under *The architecture*.

## Lens shape, August 2026

The *Deep mode* of `review-2026-08-09.md` beside this file. Rounds 1 and 3 of
the target ran it.

| Stage | Agents | What it did |
| --- | --- | --- |
| lens agents | 3 to 4 | red team, blue team, correctness, and consensus impact on a large diff |
| synthesis | the parent | dedupe, re-rank, verify each finding itself |
| critics | 2 to 3 | verdict-check, missing-blocking, severity-calibration, one round |
| claim gate | 1 | every falsifiable claim of the draft, one check each |
| draft | the parent | |

The parent held the diff, the lens reports, the verification and the draft in
one context. Measured: round 2, the plain shape with no lenses, approved with
no finding, and a reader by hand then found six on the same head. Round 3, the lens
shape at `high`, posted two Warnings, both fixed before the merge. Tokens were not
recorded.

## Maximum shape, 2026-09-10

The first pipeline config, "set for the maximum result, cost aside": every
stage opus at `xhigh`, twelve candidates per finder, three voting verifiers per
candidate, one more per refactor candidate.

| Stage | Effort | Knob | Agents |
| --- | --- | --- | --- |
| finder x7 | xhigh | cap 12 | 7 |
| verifier | xhigh | votes 3 | ~216 |
| critic, writer, text | xhigh | | 3 |

Measured before the run was stopped for cost: 72 candidates, six finders at
the cap; the finders 491k output tokens; 14 verifiers done at 17k output and
3M cache reads each; one CONFIRMED. A full run projected ~226 agents and ~4.3M
output tokens.

## Presets, 2026-09-12

The same seven finders, one verifier per hard claim, small claims batched by
file, a critic, a writer and a text pass; every stage opus. A preset moves caps
and effort, never the model or the shape.

| Preset | Finder cap | Verifier effort | Agents | Output tokens |
| --- | --- | --- | --- | --- |
| quick | 3 | high | 19 | ~531k |
| standard | 6 | xhigh | 30 | ~734k |
| deep | 10, catalog and reach twice | xhigh | 53 | ~1.5M |

## What each shape is for

- Lens shape: a diff one context holds, and a fast opinion. The context that
  suspected also confirms, so what it clears leaves no record.
- Pipeline: a diff past one context, and any security fix. A finder names a
  candidate with the check that would refute it; a verifier holding nothing
  else runs that check; `claims.md` keeps the refuted rows and the outcome
  table measures the posted ones.
- Maximum: the recall ceiling at six times standard's cost. Three same-family
  votes changed no verdict a single verifier gave.
