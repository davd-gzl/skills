---
name: writing-style
description: Use when writing or editing docs, code comments, PR bodies, or review comments, in any project.
---

# Writing style

Canonical style file for all visible prose; other skills point here.

- Lead with the conclusion. In a doc it is the rule; in a review, the verdict. If the first sentence is not the conclusion, move it up.
- Pitch to the audience. A user-facing doc states what the reader observes in one or two sentences, then links the deeper doc. Keep internals out of user-facing docs.
- Keep it small. The deeper doc has three parts, no more: the rule, one short example, the why in one sentence. No second example, no footnote, no table of cases. Deeper mechanism goes in code comments or the source, linked.
- Write headings that mean something before the section is read. Define a term before first use.
- Use a precise term over a hedge: "unspecified", not "may be true or false". Spell out only opaque abbreviations: copy-on-write, not COW.
- Cut filler: delete any clause the reader can infer from the rest of the sentence.
- Never sign-post from inside the document: no "see below", no "as mentioned above". Restructure instead.
- No em-dashes, no parentheticals, no "This page" openers. Short sentences, one idea each. Exception: the separator dash a `skills/review.md` template mandates is structure, not prose.
- Wrap committed docs and comments around 80 columns, no trailing whitespace. Never hard-wrap text destined for a GitHub PR body, issue, or comment: those fields render every newline, so write one unwrapped line per paragraph. A `comment_<model>.md` or `pr-body.md` draft is that text, not a committed doc: unwrap it in the file, so what ships is what was reviewed.
- Never vouch for code with a bare adjective ("sound", "safe") or a bare absence ("nothing broken"). State the specific checks run and what each showed, or locate the findings.
- Prefer one plain claim covering several verifications; list them separately only when the combined claim drops something load-bearing.
- State a verification only when it is a runtime check no CI job covers: a revert-repro, cross-language parity, an end-to-end path the harness cannot assert. Map every claim to the workflow job that already runs it and delete the ones that map; what survives carries the reason the job cannot reach it. When the only proof is the tests, name what they cover in one line and stop.
- Plain words over jargon: "a caller can skip the admin check", not "no confused-deputy path". Jargon only when it saves real length and the reader surely knows it.
- State the problem and stop. Keep a fix only when the remedy is non-obvious, and then name the outcome, not the steps.
- Show the code, never a description of it. A question about what the code does is answered by the lines that answer it. A change in shape is shown as before and after, not narrated. Prose earns its place only where the code cannot speak: why the change exists, and what it rules out.
- Write a commit sha bare in prose GitHub renders: no backticks, no link. Both suppress the native hovercard.
- Never write a section to say it is empty. Delete the heading.
- Link every named thing: a file, symbol, PR, issue, package, or external project gets a link the first time it appears.
- A claim about someone else's platform carries the link that proves it. Never assert what a browser, OS, or runtime does from memory.
- When the source states the reason, link the line and stop. Never restate in prose what a reader reaches in one click.
- Describe the change, never the diff. Write only what the code cannot say: why the change is there, and what it rules out.
- Never fold a live observation and a source read into one setup line. Name the setup only when the claim rests on it: the instance, the browser, the device, the command. The permalink already says which sha a source read came from.
- A link into code carries the line: `#L37`, or `#L35-L42` for a range, on a `blob` URL pinned to a sha. A symbol links to the line the sentence is about: the call site when the claim is what the code does there, the definition when the claim is what the symbol is. Read the range back before shipping. Never link a bare file or a directory: link the one line that shows the claim.
- Anchor every link on words already in the prose. Never write a sentence whose only job is to carry a link; fold it into a sentence that earns its place.
- In code comments, keep the symbols a contributor needs, and link the canonical source instead of restating it.
- In a review, lead with the verdict only where no separate field carries it. One finding per block, headed by its file:line. State the problem directly; never soften with "Optional" or "non-blocking". Keep CI and merge noise out of the findings.
- Scannable, without losing anything. Lead with the state in one line. Put anything with repeating structure (findings left out, jobs run, commits) in a table, one row each, the consequence in the last column. Keep the reasoning behind a `<details>` block rather than cutting it: completeness lives there, speed lives above it.

## Pass

Run this over every drafted artifact as the last step of writing it, against the file and not from memory. Per artifact and per revision: having read this file earlier in the session does not discharge it, and each of the six steps is a search over the draft rather than an impression of it. When a draft comes back bloated or wrong, run the step that was skipped before proposing a new rule; the caps here are already binding. Where the artifact's own skill mandates a loop, `skills/pr-body.md` for one, run that loop first and this pass over its result. Report the outcome in the reply: what it changed, or that a full pass changed nothing.

Take the checks in order. Each is a search over the draft, not an impression of it.

1. **Mechanical bans.** Search the draft for the em-dash, `U+2014`, and for `(`. Every hit is a rewrite: a colon, a period or a comma for the first, a reworked sentence for the second. This check is first because it is the only one that cannot be argued with.
2. **Verification padding.** For every claim that something passes, open the workflow file and find the job that already runs it. Delete the claim if the job exists. What survives names the reason the job cannot reach it.
3. **Unlinked names.** List every file, symbol, package, PR, issue and project named in the draft. The first appearance of each carries a link. A link into code carries `#L37` or `#L35-L42` on a `blob` URL pinned to a sha; read the range back before shipping it.
4. **Sign-posting.** Search for "see below", "as mentioned", "the section above", and any sentence whose only job is to carry a link. Restructure so the content sits where the reader needs it.
5. **Budget.** Count the words against the shape's own budget. Past it, cut; never restructure.
6. **Bare adjectives.** Search for "sound", "correct", "safe", "fine", "nothing broken". Replace each with the check that was run and what it showed.

A pass that changes nothing is the exit condition. A pass never run is not the same thing, and reporting one as the other is worse than skipping it.

## Short form

One-line comments, questions, chat replies. All rules above hold; the register is clipped.

- One idea. Stop when it lands.
- Imperative: "put all fixes in one branch", not "could you put".
- Open with `And` or `But` when adding to a previous point.
- No greeting, no thanks, no apology, no "just", no "I think", no "feel free".
- A question is one line and ends there.

Sample, hand-typed: "You should rephrase that introduction and move it in #profiling-a-transaction".

## Provenance warning

Most `davd-gzl` PR bodies and inline review comments on GitHub were produced by this workflow, not typed by hand. Do not mine them as style samples; re-derive from a fresh hand-typed sample when one appears.
