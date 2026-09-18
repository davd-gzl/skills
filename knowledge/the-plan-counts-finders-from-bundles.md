# The plan counts finders from bundles

A finder count taken from the angles alone assumes one bundle, and a projection
built on it over-counts agents and minutes while its context per turn holds,
since that term reads the stage's rules and never the repository.

- On a 262-line change over eight files the plan projected 13 agents and 39 minutes off the angles; the round ran 7 agents in 10 minutes off the bundles, and median context per turn came in at 88k against a 91k baseline measured on a monorepo. A session reasoning from the repository's size talked the cost down by 4.4x and was wrong.

Source: [gnolang/getting-started#8](https://github.com/gnolang/getting-started/pull/8), `./scripts/review-plan.py --preset standard` against `./scripts/review-retro.py` over its round.

Changes: `./scripts/review-plan.py --diff` runs `round risk` and `round dispatch` itself when no `--bundles` file is given, and counts the finders from the cut.
