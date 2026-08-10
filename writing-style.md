---
name: writing-style
description: Use when writing or editing docs, code comments, PR bodies, or review comments, in any project.
---

# Writing style

Canonical style file for all visible prose; other skills point here.

- Lead with the conclusion: the rule in a doc, the verdict in a review. If the first sentence is not the conclusion, move it up.
- Pitch to the audience. A user-facing doc states what the reader observes in one or two sentences, then links the deeper doc; internals stay out.
- Keep it small. The deeper doc has three parts, no more: the rule, one short example, the why in one sentence. Deeper mechanism goes in code comments or the source, linked.
- Write headings that mean something before the section is read. Define a term before first use.
- Use a precise term over a hedge. Spell out only opaque abbreviations.
- Cut filler: delete any clause the reader can infer from the rest of the sentence.
- Never sign-post from inside the document: no "see below", no "as mentioned above". Restructure instead.
- No em-dashes, no parentheticals, no "This page" openers. Short sentences, one idea each. A separator dash a template mandates is structure, not prose.
- Wrap committed docs and comments around 80 columns, no trailing whitespace. Never hard-wrap text destined for a GitHub PR body, issue, or comment: those fields render every newline, so write one unwrapped line per paragraph, in the draft file too, so what ships is what was reviewed.
- Never vouch for code with a bare adjective or a bare absence. State the checks run and what each showed, or locate the findings.
- Prefer one plain claim covering several verifications; list them separately only when the combined claim drops something load-bearing.
- State a verification only when it is a runtime check no CI job covers. Map every claim to the job that already runs it and delete the ones that map; what survives carries the reason the job cannot reach it. When the only proof is the tests, name what they cover in one line and stop.
- Plain words over jargon; jargon only when it saves real length and the reader surely knows it.
- State the problem and stop. Keep a fix only when the remedy is non-obvious, and then name the outcome, not the steps.
- Show the code, never a description of it, and describe the change, never the diff: answer a question about code with the lines that answer it, and show a change in shape as before and after. Prose earns its place only where the code cannot speak: why the change exists, and what it rules out.
- Write a commit sha bare in prose GitHub renders: no backticks, no link. Both suppress the native hovercard.
- Never write a section to say it is empty. Delete the heading.
- Link every named thing: a file, symbol, PR, issue, package, or external project gets a link the first time it appears.
- A claim about someone else's platform carries the link that proves it. Never assert what a browser, OS, or runtime does from memory.
- When the source states the reason, link the line and stop. Never restate what a reader reaches in one click.
- Never fold a live observation and a source read into one setup line. Name the setup only when the claim rests on it; the permalink already says which sha a source read came from.
- A link into code carries the line, `#L37` or `#L35-L42`, on a `blob` URL; read the range back before shipping. Never link a bare file or a directory: link the one line that shows the claim. The reviewing skill picks the ref; this file only requires that the line be there and the claim be on it.
- A finding links the problem, never the definition: point at the defective line. A signature link makes the reader hunt for what you already found; link the `func` line only when the claim is about the symbol itself.
- Anchor every link on words already in the prose. Never write a sentence whose only job is to carry a link; fold it into a sentence that earns its place.
- In code comments, keep the symbols a contributor needs, and link the canonical source instead of restating it.
- In a review, lead with the verdict only where no separate field carries it. One finding per block, headed by its file:line. State the problem directly; never soften with "Optional" or "non-blocking". Keep CI and merge noise out of the findings.
- Scannable, without losing anything. Lead with the state in one line, put anything with repeating structure in a table, one row each with the consequence in the last column, and keep the reasoning behind a `<details>` block rather than cutting it: completeness lives there, speed lives above it.

## Pass

Run this over every drafted artifact as the last step of writing it, against the file and not from memory, per artifact and per revision: having read this file earlier in the session does not discharge it. When a draft comes back bloated or wrong, run the step that was skipped before proposing a new rule; the caps here are already binding. Where the artifact's own skill mandates a loop, run that loop first and this pass over its result. Report the outcome in the reply: what it changed, or that a full pass changed nothing.

Take the checks in order. Each is a search over the draft, not an impression of it.

1. **Mechanical bans.** Search for the em-dash, `U+2014`, and for `(`. Every hit is a rewrite: a colon, a period or a comma for the first, a reworked sentence for the second. First because it cannot be argued with.
2. **Verification padding.** For every claim that something passes, open the workflow file and find the job that already runs it. Delete the claim if the job exists. What survives names the reason the job cannot reach it.
3. **Unlinked names.** List every file, symbol, package, PR, issue and project named in the draft. The first appearance of each carries a link. A link into code carries `#L37` or `#L35-L42` on a `blob` URL and points at the line the claim is about, never the definition; read the range back and confirm the claim is on it. The reviewing skill fixes the ref.
4. **Sign-posting.** Search for "see below", "as mentioned", "the section above", and any sentence whose only job is to carry a link. Restructure so the content sits where the reader needs it.
5. **Budget.** Count the words against the shape's own budget. Past it, cut; never restructure.
6. **Bare adjectives.** Search for "sound", "correct", "safe", "fine", "nothing broken". Replace each with the check that was run and what it showed.
7. **The cut.** Delete each sentence's last clause. If what remains carries the same fact, the same number and the same stake, keep the shorter one and repeat. Then read each sentence once, left to right, and rewrite any that needs a second pass to parse. Stop at the first cut that removes a fact, a number, or the reason to care: past that the line is being deleted rather than shortened, the worse failure. Last because every earlier step can add words, and a search like the others: every sentence.

A pass that changes nothing is the exit condition. A pass never run is not the same thing, and reporting one as the other is worse than skipping it.

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

1. **The finding, one or two sentences.** The defect, the measurement, and the single piece of mechanism the reader cannot derive. Nothing else: not the consequence the number implies, not the fix the defect implies, not what the change gets right.
2. **A collapsed `<details>` repro**, in the harness the repo already uses, paste-and-run, header per `skills/review.md`.
3. **One line above the output** saying what failed and why the failure is the finding.
4. **The output**, pasted from a run of that exact block.
5. **Mechanism and any sweep table**, after the output, still inside the `<details>`.
6. **Inline findings**, each `## <path>:<line> [gh](<url>)` with the path a bare token, then a band prefix and plain sentences.

Everything a reader needs to act sits above the fold; everything they need to check sits below it. Write the visible part first, then move each surviving sentence down until one remains above.

- State the fix, or state the defect, never both unless the fix is non-obvious from the defect: a fix stated as simpler needs no sentence on what the old code did wrong.
- Cut every clause the fix already implies: restating the gap the fix closes is padding.
- No process words: no `Verified`, `measured`, `I ran`, `reproduced`, `on <sha>`. Evidence lives in the collapsed repro or the review file, never in the visible line.
- Give the data and stop. A measurement implies its own consequence to the reader who owns the code, and a missing bound implies the fix. Delete the clause drawing the conclusion, the sentence naming the obvious fix, and the comparison to what the change gets right.
- A number carries its repro directly under it, collapsed, in the same comment: the repro is what makes it true, and a number the reader cannot re-run is worth less than the sentence it displaced. Never leave the repro in a private review file while the number goes public.
- One clause of mechanism, only if the reader cannot act without it; a walkthrough never earns its place.
- Anchor and band do the framing work: the `## path:line` header already says where, the band prefix already says how much. Repeat neither in the sentence.
- Write sentences, not notation. A label fragment with no verb, or with its pronoun dropped, strands the reader mid-clause. Every line is a grammatical sentence with a subject and a verb, readable once, left to right, without backtracking. Terse is a word count, never a licence to drop the words that make it parse.
- The user's shorthand describes the content, never the copy: it names the fact to convey, in the compressed register of two people who already know the code. Write the fact they named as a sentence for a reader who does not.
- Read the finished line and delete the last clause; if it still means the same thing, it was padding, so repeat, and stop when the next cut takes the stake with it. Every line owes the reader why they should care; trimmed past that it is not short, it is empty. Test the finished line cold, as someone who has never seen the code, and when it fails, restore the clause carrying the consequence, not the one carrying the mechanism.
