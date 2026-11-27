# Keep the loaded rules short

What every session loads costs attention on every task, and a rule that cannot bend holds better as a hook than as a line of prose.

- Claude Code's best practices, the maintained documentation page: CLAUDE.md loads into every session, so it holds only what the agent could not work out from the code and anything the user has had to correct twice; a rule that cannot bend becomes a hook or a deny rule, which the harness runs every time; a line lost in a long file means the file needs to be shorter; `/clear` between unrelated tasks, and after two failed corrections a fresh context with one prompt beats a third correction.
- Effective context engineering for AI agents, Anthropic engineering: context is a finite attention budget with diminishing returns, so the aim is the smallest set of high-signal tokens; hardcoding complex, brittle logic into a system prompt is one of the two named failure modes, raising fragility and maintenance cost; the closing advice is to do the simplest thing that works.
- Building effective agents, Anthropic engineering: start from the simplest solution and add complexity only when it measurably helps; a generate-and-critique loop fits where the evaluation criteria are clear and the refinement brings measurable value.
- Agentic Coding Recommendations, Armin Ronacher, one practitioner's experience: agents handle a task well until the total amount they must consider passes a threshold, and the dumbest thing that works beats a clever one; tools are plain scripts that answer fast and fail loudly.

Source: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices), [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), [Agentic Coding Recommendations](https://lucumr.pocoo.org/2025/6/12/agentic-coding/).

Changes: `skills/shortcuts.md` keeps only the rule for when a typed word counts, and each word's row in `skills/words.md` reaches the session through `scripts/words.py` when a message opens with it. *Editing this corpus* in `skills/authoring.md` fixes a rule found wrong during other work in that turn only where it blocks the task or the user asks for it.
