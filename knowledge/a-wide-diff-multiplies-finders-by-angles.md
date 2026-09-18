# A wide diff multiplies finders by angles

The finder count is bundles times angles, and a directory over the ceiling is
cut into one bundle per file, so a large new package earns every angle on every
file while the Nit cap, per finder, scales with it.

- One pull request adding 2986 lines in one package over 16 files was cut into 10 file bundles, each with every angle: 40 finders, 4 second-round finders and a reflector, then 23 run judges and 9 read judges, 77 agents and 111M cache read before the writer, against a launch projection of 20 agents and 63M. They returned 246 candidates, 171 of them Nit or Suggestion, the judges confirmed 162 of 170, and the draft to come carries about 119 small sections over 24 Warnings; the user's read of that round was that most were not worth the author's time.

Source: [gnolang/gno#6194](https://github.com/gnolang/gno/pull/6194), `./scripts/agent-metrics.py summary` over that workflow's rows in the metrics store, and the round's `candidates/` and `verdicts/` counted by band.

Changes: `finder.fold_past_bundles`, past which one finder per bundle carries every angle; `finder.small_per_round`, the Nit and Suggestion slots shared across a round's finders; `finder.skip_classes`, the runner dropping a wording or no-action Nit outside `deep`.
