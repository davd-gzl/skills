# Context engineering

The guide the corpus follows for what an agent reads.

- Right altitude: specific enough to guide, flexible enough to leave heuristics; neither brittle logic nor vague guidance.
- Sections with headers: background, instructions, tool guidance, output description.
- The minimal set that outlines the behaviour, then examples for the failure modes found; canonical examples over a list of edge cases.
- Tools self-contained and unambiguous: where a person cannot say which tool applies, the agent cannot either.
- Just-in-time retrieval: identifiers and paths in context, the data loaded by a tool when needed.
- Compaction clears tool results first; notes persisted outside the window; sub-agents on clean contexts returning a distilled summary of one to two thousand tokens.

Source: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

Changes: each stage's section opens on its contract and a filled example; the runner's prompt carries the round's values and points at the section; agents return data, never transcripts.
