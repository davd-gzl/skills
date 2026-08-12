---
name: writing-style
description: Use when writing or editing docs, code comments, PR bodies, or review comments, in any project.
---

# Writing style

Canonical style file for all visible prose, and the file every other skill defers to on a style conflict. Earlier snapshots live in `archive/` and are superseded by this one.

- Lead with the conclusion: the rule in a doc, the verdict in a review. If the first sentence is not the conclusion, move it up.
- Pitch to the audience. A user-facing doc states what the reader observes in one or two sentences, then links the deeper doc; internals stay out.
- Keep it small. The deeper doc has three parts, no more: the rule, one short example, the why in one sentence. No second example, no footnote, no table of cases. Deeper mechanism goes in code comments or the source, linked.
- Write headings that mean something before the section is read. Define a term before first use.
- Use a precise term over a hedge, naming the state rather than the range of states it might be in. Spell out an abbreviation a reader outside the project could not expand, and leave the ones they read daily alone.
- Cut filler: delete any clause the reader can infer from the rest of the sentence.
- Never sign-post from inside the document: no "see below", no "as mentioned above". Restructure instead.
- No em-dashes, no parentheticals, no "This page" openers. Short sentences, one idea each. A separator dash mandated by a template, `skills/review.md` for one, is structure, not prose.
- Wrap committed docs and comments around 80 columns, no trailing whitespace. Never hard-wrap text destined for a GitHub PR body, issue, or comment, which render every newline: write one unwrapped line per paragraph. A `comment_<model>.md` or `pr-body.md` draft is that text and not a committed doc, so it stays unwrapped in the file too.
- Never vouch for code with a bare adjective or a bare absence. State the checks run and what each showed, or locate the findings.
- Prefer one plain claim covering several verifications; list them separately only when the combined claim drops something load-bearing.
- State a verification only when it is a runtime check no CI job covers: a revert-repro, cross-language parity, an end-to-end path the harness cannot assert. Map every claim to the job that already runs it and delete the ones that map; what survives carries the reason the job cannot reach it. When the only proof is the tests, name what they cover in one line and stop.
- Plain words over jargon: name the action a caller can take, never the pattern's label. Jargon only when it saves real length and the reader surely knows it, which a specialist's vocabulary rarely satisfies.
- State the problem and stop. Keep a fix only when the remedy is non-obvious, and then name the outcome, not the steps.
- Show the code, never a description of it, and describe the change, never the diff: answer a question about code with the lines that answer it, and show a change in shape as before and after. Prose only where the code cannot speak: why the change exists, and what it rules out.
- Write a commit sha bare in prose GitHub renders: no backticks, no link.
- Never write a section to say it is empty. Delete the heading.
- Link every named thing: a file, symbol, PR, issue, package, or external project gets a link the first time it appears.
- A claim about someone else's platform carries the link that proves it. Never assert what a browser, OS, or runtime does from memory.
- When the source states the reason, link the line and stop. Never restate what a reader reaches in one click.
- Never fold a live observation and a source read into one setup line. Name the setup only when the claim rests on it: the instance, the browser, the device, the command. A source read owes none of that, since the permalink already carries the sha.
- A link into code carries the line, `#L37` or `#L35-L42`, on a `blob` URL; read the range back before shipping. Never link a bare file or a directory: link the one line that shows the claim. `skills/review.md` picks the ref, the branch under review, with a sha only in the two exceptions it names.
- A finding links the problem, never the definition: point at the defective line, the unbounded call, the missing guard, the wrong operator. Link the `func` line only when the claim is about the symbol itself, never when the claim is a defect inside it.
- Anchor every link on words already in the prose. Never write a sentence whose only job is to carry a link; fold it into a sentence with content of its own.
- In code comments, keep the symbols a contributor needs, and link the canonical source instead of restating it.
- In a review, lead with the verdict only where no separate field carries it. One finding per block, headed by its file:line. State the problem directly; never soften with "Optional" or "non-blocking". Keep CI and merge noise out of the findings.
- Scannable, without losing anything. Lead with the state in one line, put anything with repeating structure in a table, findings left out, jobs run, commits, one row each with the consequence in the last column, and keep the reasoning behind a `<details>` block rather than cutting it: completeness lives there, speed lives above it.

## Pass

Run this over every drafted artifact as the last step of writing it, against the file and not from memory, per artifact and per revision. Having read this file earlier in the session does not discharge it, and each of the seven steps is a search over the draft. When a draft comes back bloated or wrong, run the step that was skipped before proposing a new rule. Where the artifact's own skill mandates a loop, `skills/pr-body.md` for one, run that loop first and this pass over its result. Report the outcome in the reply: what it changed, or that a full pass changed nothing.

Take the checks in order. Each is a search over the draft, not an impression of it.

1. **Mechanical bans.** Search for the em-dash, `U+2014`, and for `(`. Every hit is a rewrite: a colon, a period or a comma for the first, a reworked sentence for the second.
2. **Verification padding.** For every claim that something passes, open the workflow file and find the job that already runs it. Delete the claim if the job exists. What survives names the reason the job cannot reach it.
3. **Unlinked names.** List every file, symbol, package, PR, issue and project named in the draft. The first appearance of each carries a link. A link into code carries `#L37` or `#L35-L42` on a `blob` URL and points at the line the claim is about, never the definition; read the range back and confirm the claim is on it. `skills/review.md` fixes the ref: the branch under review, with a sha only in the two exceptions it names.
4. **Sign-posting.** Search for "see below", "as mentioned", "the section above", and any sentence whose only job is to carry a link. Restructure so the content sits where the reader needs it.
5. **Budget.** Count the words against the shape's own budget. Past it, cut; never restructure.
6. **Bare adjectives.** Search for "sound", "correct", "safe", "fine", "nothing broken". Replace each with the check that was run and what it showed.
7. **The cut.** Delete each sentence's last clause. If what remains carries the same fact, the same number and the same stake, keep the shorter one and repeat. Then read each sentence once, left to right, and rewrite any that needs a second pass to parse. Stop at the first cut that removes a fact, a number, or the reason to care: past that the line is being deleted rather than shortened, which is the worse failure. Apply to every sentence.

A pass that changes nothing is the exit condition. Never report a pass not run as a pass that changed nothing.

## Short form

One-line comments, questions, chat replies. All rules above hold; the register is clipped.

- One idea. Stop when it lands.
- Imperative, never a request.
- Open with `And` or `But` when adding to a previous point.
- No greeting, no thanks, no apology, no "just", no "I think", no "feel free".
- A question is one line and ends there.

Sample of the register: "Rephrase that opening and move it under the profiling section."

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

**Count the words the author reads, not the words in the file.** Link text counts; the URL inside it does not, nor do the `## path:line` headers, the fenced blocks, or anything collapsed behind `<details>`. Measured against the reviewer's own posted reviews: 20 to 49 read-words per inline comment, median 27, and 27 to 50 for a whole review including its body. A draft at two hundred is not over-long by a little, it is carrying findings that belong in the review file.

The whole comment is countable, and counting is the check: one sentence per section, one line or nothing in the body, and one section per distinct action the author has to take. Two sections that resolve in the same edit are one finding. Count before shipping; a draft that fails the count is not trimmed later, it is rewritten from the one finding that changes what the author does next.

- State the fix, or state the defect, never both unless the fix is non-obvious from the defect.
- Cut every clause the fix already implies. A trailing clause naming what the current code omits, misses, or does differently restates the gap the fix has already closed; delete it.
- No process words: no `Verified`, `measured`, `I ran`, `reproduced`, `on <sha>`. Evidence lives in the collapsed repro or the review file, never in the visible line.
- Give the data and stop. Delete the clause drawing the conclusion, the sentence naming the obvious fix, and the comparison to what the change gets right; keep the defect, the measurement, and the one piece of mechanism the reader cannot derive.
- A number carries its repro directly under it, collapsed, in the same comment. Never leave the repro in a private review file while the number goes public.
- One clause of mechanism, only if the reader cannot act without it; never a walkthrough.
- The `## path:line` header already says where, and the band prefix, `Nit:`, `Suggestion:`, `Refactor:` or `Missing test:`, already says how much: repeat neither in the sentence. Name the kind in the prefix rather than leaving the reader to infer it: `Refactor:` when the same behaviour fits in fewer lines, so the author knows before the first word whether anything is broken.
- Write sentences, not notation: no label fragment without a verb, no dropped pronoun. Every line is a grammatical sentence with a subject and a verb, readable once, left to right, without backtracking.
- **Carry the expectation and the defect in one clause.** "X pulls Y toward the centre rather than holding it in place", never "X should hold Y, and pulls it toward the centre instead", which splices two halves onto a comma and switches subject in the middle.
- The user's shorthand names the fact to convey, never the copy to post. Write the fact they named as a sentence for a reader who does not know the code.
- Repair a draft the user wrote, never rewrite it. When they show their own text and ask whether it works, fix what is wrong, keep their words, their order and their register, then name each change so they can revert it. The rule above covers a note naming a fact, not a draft already written as prose.
- Read the finished line and delete the last clause; if it still means the same thing, repeat, and stop when the next cut takes the stake with it. Test the finished line cold, as someone who has never seen the code, and when it fails, restore the clause carrying the consequence, not the one carrying the mechanism.
