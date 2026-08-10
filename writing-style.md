---
name: writing-style
description: Use when writing or editing docs, code comments, PR bodies, or review comments, in any project.
---

# Writing style

Canonical style file for all visible prose.

- Lead with the conclusion: the rule in a doc, the verdict in a review. If the first sentence is not the conclusion, move it up.
- Pitch to the audience. A user-facing doc states what the reader observes in one or two sentences, then links the deeper doc; internals stay out.
- Keep it small. The deeper doc has three parts, no more: the rule, one short example, the why in one sentence. Deeper mechanism goes in code comments or the source, linked.
- Write headings that mean something before the section is read. Define a term before first use.
- Use a precise term over a hedge. Spell out only opaque abbreviations.
- Cut filler: delete any clause the reader can infer from the rest of the sentence.
- Never sign-post from inside the document: no "see below", no "as mentioned above". Restructure instead.
- No em-dashes, no parentheticals, no "This page" openers. Short sentences, one idea each. A separator dash a template mandates is structure, not prose.
- Wrap committed docs and comments around 80 columns, no trailing whitespace. Never hard-wrap text destined for a GitHub PR body, issue, or comment: write one unwrapped line per paragraph, in the draft file too.
- Never vouch for code with a bare adjective or a bare absence. State the checks run and what each showed, or locate the findings.
- Prefer one plain claim covering several verifications; list them separately only when the combined claim drops something load-bearing.
- State a verification only when it is a runtime check no CI job covers. Map every claim to the job that already runs it and delete the ones that map; what survives carries the reason the job cannot reach it. When the only proof is the tests, name what they cover in one line and stop.
- Plain words over jargon; jargon only when it saves real length and the reader surely knows it.
- State the problem and stop. Keep a fix only when the remedy is non-obvious, and then name the outcome, not the steps.
- Show the code, never a description of it, and describe the change, never the diff: answer a question about code with the lines that answer it, and show a change in shape as before and after. Prose only where the code cannot speak: why the change exists, and what it rules out.
- Write a commit sha bare in prose GitHub renders: no backticks, no link.
- Never write a section to say it is empty. Delete the heading.
- Link every named thing: a file, symbol, PR, issue, package, or external project gets a link the first time it appears.
- A claim about someone else's platform carries the link that proves it. Never assert what a browser, OS, or runtime does from memory.
- When the source states the reason, link the line and stop. Never restate what a reader reaches in one click.
- Never fold a live observation and a source read into one setup line. Name the setup only when the claim rests on it.
- A link into code carries the line, `#L37` or `#L35-L42`, on a `blob` URL; read the range back before shipping. Never link a bare file or a directory: link the one line that shows the claim. The reviewing skill picks the ref.
- A finding links the problem, never the definition: point at the defective line. Link the `func` line only when the claim is about the symbol itself.
- Anchor every link on words already in the prose. Never write a sentence whose only job is to carry a link; fold it into a sentence with content of its own.
- In code comments, keep the symbols a contributor needs, and link the canonical source instead of restating it.
- In a review, lead with the verdict only where no separate field carries it. One finding per block, headed by its file:line. State the problem directly; never soften with "Optional" or "non-blocking". Keep CI and merge noise out of the findings.
- Scannable, without losing anything. Lead with the state in one line, put anything with repeating structure in a table, one row each with the consequence in the last column, and keep the reasoning behind a `<details>` block rather than cutting it.

## Pass

Run this over every drafted artifact as the last step of writing it, against the file and not from memory, per artifact and per revision. When a draft comes back bloated or wrong, run the step that was skipped before proposing a new rule. Where the artifact's own skill mandates a loop, run that loop first and this pass over its result. Report the outcome in the reply: what it changed, or that a full pass changed nothing.

Take the checks in order. Each is a search over the draft, not an impression of it.

1. **Mechanical bans.** Search for the em-dash, `U+2014`, and for `(`. Every hit is a rewrite: a colon, a period or a comma for the first, a reworked sentence for the second.
2. **Verification padding.** For every claim that something passes, open the workflow file and find the job that already runs it. Delete the claim if the job exists. What survives names the reason the job cannot reach it.
3. **Unlinked names.** List every file, symbol, package, PR, issue and project named in the draft. The first appearance of each carries a link. A link into code carries `#L37` or `#L35-L42` on a `blob` URL and points at the line the claim is about, never the definition; read the range back and confirm the claim is on it. The reviewing skill fixes the ref.
4. **Sign-posting.** Search for "see below", "as mentioned", "the section above", and any sentence whose only job is to carry a link. Restructure so the content sits where the reader needs it.
5. **Budget.** Count the words against the shape's own budget. Past it, cut; never restructure.
6. **Bare adjectives.** Search for "sound", "correct", "safe", "fine", "nothing broken". Replace each with the check that was run and what it showed.
7. **The cut.** Delete each sentence's last clause. If what remains carries the same fact, the same number and the same stake, keep the shorter one and repeat. Then read each sentence once, left to right, and rewrite any that needs a second pass to parse. Stop at the first cut that removes a fact, a number, or the reason to care. Apply to every sentence.

A pass that changes nothing is the exit condition. Never report a pass not run as a pass that changed nothing.

## Short form

One-line comments, questions, chat replies. All rules above hold; the register is clipped.

- One idea. Stop when it lands.
- Imperative, never a request.
- Open with `And` or `But` when adding to a previous point.
- No greeting, no thanks, no apology, no "just", no "I think", no "feel free".
- A question is one line and ends there.

## Posted comments

A comment posted to a pull request is the most compressed register: the defect or the fix, in the fewest words that still land it.

The settled shape, in order:

1. **The finding, one sentence.** The defect, the measurement, and the single piece of mechanism the reader cannot derive. Nothing else: not the consequence the number implies, not the fix the defect implies, not what the change gets right. A second sentence says the first one failed, and usually means the section holds two findings; split it and post the one that matters.
2. **A collapsed `<details>` repro**, in the harness the repo already uses, paste-and-run, header per `skills/review.md`.
3. **One line above the output** saying what failed and why the failure is the finding.
4. **The output**, pasted from a run of that exact block.
5. **Mechanism and any sweep table**, after the output, still inside the `<details>`.
6. **Inline findings**, each `## <path>:<line> [gh](<url>)` with the path a bare token, then a band prefix and plain sentences.

Everything a reader needs to act sits above the fold; everything they need to check sits below it. Write the visible part first, then move each surviving sentence down until one remains above.

The whole comment is countable, and counting is the check: one sentence per section, one line or nothing in the body, and one section per distinct action the author has to take. Two sections that resolve in the same edit are one finding. Count before shipping; a draft that fails the count is not trimmed later, it is rewritten from the one finding that changes what the author does next.

- State the fix, or state the defect, never both unless the fix is non-obvious from the defect.
- Cut every clause the fix already implies.
- No process words: no `Verified`, `measured`, `I ran`, `reproduced`, `on <sha>`. Evidence lives in the collapsed repro or the review file, never in the visible line.
- Give the data and stop. Delete the clause drawing the conclusion, the sentence naming the obvious fix, and the comparison to what the change gets right.
- A number carries its repro directly under it, collapsed, in the same comment. Never leave the repro in a private review file while the number goes public.
- One clause of mechanism, only if the reader cannot act without it; never a walkthrough.
- The `## path:line` header already says where and the band prefix already says how much: repeat neither in the sentence.
- Write sentences, not notation: no label fragment without a verb, no dropped pronoun. Every line is a grammatical sentence with a subject and a verb, readable once, left to right, without backtracking.
- The user's shorthand names the fact to convey, never the copy to post. Write the fact they named as a sentence for a reader who does not know the code.
- Read the finished line and delete the last clause; if it still means the same thing, repeat, and stop when the next cut takes the stake with it. Test the finished line cold, as someone who has never seen the code, and when it fails, restore the clause carrying the consequence, not the one carrying the mechanism.
