---
name: writing-style
description: Use when writing or editing docs, code comments, PR bodies, or review comments, in any project.
---

# Writing style

Canonical style file for all visible prose, and the file every other skill defers to on a style conflict.

The goal is one thing: a reader understands the text on a single pass. Every rule below serves that and none outranks it. Brevity is how clarity is usually reached, never what it is for. A cut that saves a word and costs a second read has failed, whatever budget it satisfies. Where a rule and the reader disagree the reader wins, and the rule is the thing that gets fixed.

- **Read what the author already published on this repo, of the kind being drafted.** A review comment takes its shape from their review comments, an issue from their issues: the opening, the length, how a claim gets its link, whether a remedy is proposed and where it sits. Read until the shape repeats, three at the least, and where they have published none, take the shape from what the repo has already accepted and say so in the handover. A rule below that contradicts what they show is the rule that is wrong.
  ```bash
  gh api "repos/<repo>/pulls/comments?per_page=100" --jq '[.[]|select(.user.login=="<login>")]|.[0:10][]|.body'
  gh api "repos/<repo>/issues?state=all&creator=<login>&per_page=10" --jq '.[]|"\(.title)\n\(.body)"'
  ```
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
- **Write the reader's words, not the codebase's.** Every term the project invented is jargon to the person reading the comment: the element's name, the API's name for a thing, the CSS property doing the work. Say the mouse, not the pointer; the area it is drawn in, not the tile; the picture does not fill it, not `object-fit: contain`. A sentence needing a term the reader has to look up has not explained the finding, it has named it.
- **Reach for a word the reader owns, never one you invented.** That swap is the same failure in a new coat, and an invented place for a thing to be is its common shape. Where no plain equivalent exists, use a contrast the reader already holds, paused against stopped, or define the term in the sentence that first uses it.
- **Three counts, never a judgement.** Words before the main verb: over five, rewrite. Subordinate clauses after it: over one, rewrite. Verbs before the first comma with the first arriving fourth or later: rewrite, since the clause sits inside the subject rather than after the verb.
- **`but` never stands in for `except`.** Where the exception does not change the outcome, drop it.
- **A finding names the scope, never one instance of it.** "a French browser" is an instance; "whatever the browser's language" is the scope.
- **A rule carries no date.** No `Stated <date>`, no `Measured <date>`, no clock time.
- **A pronoun reaches back one clause, never two.** Repeat the noun.
- **A connective states a relation that holds.** "while" and "though" promise a contrast, "so" and "because" promise cause: when the two facts merely sit beside each other, say they are related and stop. A joint that misdescribes the join sends the reader hunting for a tension that was never there.
- Plain words over jargon: name the action a caller can take, never the pattern's label. Jargon only when it saves real length and the reader surely knows it, which a specialist's vocabulary rarely satisfies.
- State the problem and stop. Keep a fix only when the remedy is non-obvious, and then name the outcome, not the steps.
- Show the code, never a description of it, and describe the change, never the diff: answer a question about code with the lines that answer it, and show a change in shape as before and after. Prose only where the code cannot speak: why the change exists, and what it rules out.
- **A picture is introduced, never dropped in.** The sentence before it says what it shows and where it came from, naming the browser, the instance or the command. A reader cannot tell a real run from a mockup by looking, so an unintroduced image argues nothing and the words it saved bought nothing. Where a claim is visible on screen, drive the app and capture it cropped to the thing in question, store the file under the artifact's `media/` directory, and embed it by its `raw.githubusercontent.com` URL so it renders inside a GitHub comment. Where the screen cannot be reached from here, name the login or device it needed.
- **Keep a real person's name out of a fixture, a test and a draft.** A copyright line copied from a real file carries an individual who never asked to appear in the repository, and the fixture needs the shape: `Copyright (c) 2019 The Authors` tests exactly what a real name tests. An organisation or project is fine, and so is a module path containing a surname, since both are how the thing is cited everywhere. Where the provenance matters, name the file or repository the shape came from and stop there.
- Write a commit sha bare in prose GitHub renders: no backticks, no link.
- Never write a section to say it is empty. Delete the heading.
- Link every named thing: a file, symbol, PR, issue, package, or external project gets a link the first time it appears.
- A claim about someone else's platform carries the link that proves it. Never assert what a browser, OS, or runtime does from memory.
- **Every factual claim carries the link that proves it, not only the named things in it.** A default, a type, a non-null column, a bound, a count, a call site: anchor the words stating the fact on the line that shows it. A sentence carrying two facts takes two links, so a value and the column default it comes from are anchored separately, one on the constant and one on the field. An absence has no line to point at and stays unlinked.
- When the source states the reason, link the line and stop. Never restate what a reader reaches in one click.
- Never fold a live observation and a source read into one setup line. Name the setup only when the claim rests on it: the instance, the browser, the device, the command. A source read owes none of that, since the permalink already carries the sha.
- A link into code carries the line, `#L37` or `#L35-L42`, on a `blob` URL; read the range back before shipping. Never link a bare file or a directory: link the one line that shows the claim. `skills/review.md` picks the ref, the branch under review, with a sha only in the two exceptions it names.
- A finding links the problem, never the definition: point at the defective line, the unbounded call, the missing guard, the wrong operator. Link the `func` line only when the claim is about the symbol itself, never when the claim is a defect inside it.
- Anchor every link on words already in the prose. Never write a sentence whose only job is to carry a link; fold it into a sentence with content of its own.
- In code comments, keep the symbols a contributor needs, and link the canonical source instead of restating it.
- Two lines is the budget for a code comment. Write the one fact the reader cannot get from the lines beside it, and stop. A comment carrying three facts is a design note in the wrong file: the alternative that was rejected, the failure the shape prevents and the invariant behind it belong in the ADR, the plan or the commit message, which a reader can skip and the code cannot. Where a second fact is load-bearing for the line under it, keep that one and move the rest.
- **Mark an opinion as an opinion.** Write "I think" in front of a preference about how the code should look or behave, so a reader tells taste from defect at a glance. Never attach it to something measured, which needs no owner, and never use it to soften a finding: a defect stays flat and unhedged.
- In a review, lead with the verdict only where no separate field carries it. One finding per block, headed by its file:line. State the problem directly; never soften with "Optional" or "non-blocking". Keep CI and merge noise out of the findings.
- Scannable, without losing anything. Lead with the state in one line, put anything with repeating structure in a table, findings left out, jobs run, commits, one row each with the consequence in the last column, and keep the reasoning behind a `<details>` block rather than cutting it: completeness lives there, speed lives above it.

## Pass

Run this over every drafted artifact as the last step of writing it, against the file and not from memory, per artifact and per revision. Having read this file earlier in the session does not discharge it, and each of the ten steps is a search over the draft. When a draft comes back bloated or wrong, run the step that was skipped before proposing a new rule. Where the artifact's own skill mandates a loop, `skills/pr-body.md` for one, run that loop first and this pass over its result. Report the outcome in the reply: what it changed, or that a full pass changed nothing.

Take the checks in order. Each is a search over the draft, not an impression of it.

1. **Mechanical bans.** Search for the em-dash, `U+2014`, and for `(`. Every hit is a rewrite: a colon, a period or a comma for the first, a reworked sentence for the second.
2. **Verification padding.** For every claim that something passes, open the workflow file and find the job that already runs it. Delete the claim if the job exists. What survives names the reason the job cannot reach it.
3. **Unlinked names.** List every file, symbol, package, PR, issue and project named in the draft. The first appearance of each carries a link. A link into code carries `#L37` or `#L35-L42` on a `blob` URL and points at the line the claim is about, never the definition; read the range back and confirm the claim is on it. `skills/review.md` fixes the ref: the branch under review, with a sha only in the two exceptions it names.
4. **Unproved claims.** List every sentence asserting a fact about the code, a default, a type, a bound, a count, a call site, and confirm the words stating it carry a link to the line that shows it. Two facts in one sentence need two. Then list every sentence asserting what a browser, an operating system, a runtime, a device or a third-party library does. Each carries a link to the documentation that states it, or the run that produced it, or the words naming it unmeasured. One with none of the three is deleted, never softened, and the sentences around it are re-read: a claim that cannot be sourced is often load-bearing for the one beside it.
5. **Sign-posting.** Search for "see below", "as mentioned", "the section above", and any sentence whose only job is to carry a link. Restructure so the content sits where the reader needs it.
6. **Budget.** Count the words against the shape's own budget. Past it, cut; never restructure.
7. **Bare adjectives.** Search for "sound", "correct", "safe", "fine", "nothing broken". Replace each with the check that was run and what it showed.
8. **Counts.** Per sentence: words before the main verb, over five; subordinate clauses after it, over one; two verbs before the first comma with the first arriving fourth or later. A participle in the subject is not a clause; a finite one is.
9. **Promises.** Every edit named in prose is one the author has to retype. Move it into a ` ```suggestion ` block or cut it, and never ship one that was not run.
10. **The cut.** Delete each sentence's last clause. If what remains carries the same fact, the same number and the same stake, keep the shorter one and repeat. Then read each sentence once, left to right, and rewrite any that needs a second pass to parse. Stop at the first cut that removes a fact, a number, or the reason to care: past that the line is being deleted rather than shortened, which is the worse failure. Apply to every sentence.

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

**Count the words the author reads, not the words in the file.** Link text counts; the URL inside it does not, nor do the `## path:line` headers, the fenced blocks, or anything collapsed behind `<details>`. Measured against the reviewer's own posted comments: 20 to 49 read-words per finding, median 27. That figure is a density, one finding written tightly, and never a budget for the review as a whole: a review carrying six findings costs six times it and is not over-long. Cut padding to reach it, never a finding. Every finding the author should see is anchored and posted; the total is whatever that comes to.

The whole comment is countable, and counting is the check: one sentence per section, one line or nothing in the body, and one section per distinct action the author has to take. Two sections that resolve in the same edit are one finding. Count before shipping; a draft that fails the count is not trimmed later, it is rewritten from the one finding that changes what the author does next.

- State the fix, or state the defect, never both unless the fix is non-obvious from the defect.
- Cut every clause the fix already implies. A trailing clause naming what the current code omits, misses, or does differently restates the gap the fix has already closed; delete it.
- No process words: no `Verified`, `measured`, `I ran`, `reproduced`, `on <sha>`. Evidence lives in the collapsed repro or the review file, never in the visible line. A picture is the exception, and it keeps the sentence naming what it shows and what produced it.
- **A fact stating a condition says what breaks when it breaks, or is cut.**
- **A band says how much, never what to type.** `Suggestion:` and `Nit:` open on the defect, same as every other finding. Where an exact edit exists, it ships as a GitHub ` ```suggestion ` block the author applies in one click, and it was run both ways before it shipped.
- A number carries its repro directly under it, collapsed, in the same comment. Never leave the repro in a private review file while the number goes public.
- The `## path:line` header already says where, and the band prefix, `Nit:`, `Suggestion:`, `Refactor:` or `Missing test:`, already says how much: repeat neither in the sentence. Name the kind in the prefix rather than leaving the reader to infer it: `Refactor:` when the same behaviour fits in fewer lines, so the author knows before the first word whether anything is broken.
- Write sentences, not notation: no label fragment without a verb, no dropped pronoun. Every line is a grammatical sentence with a subject and a verb, readable once, left to right, without backtracking.
- **Carry the expectation and the defect in one clause.** "X pulls Y toward the centre rather than holding it in place", never "X should hold Y, and pulls it toward the centre instead", which splices two halves onto a comma and switches subject in the middle.
- The user's shorthand names the fact to convey, never the copy to post. Write the fact they named as a sentence for a reader who does not know the code.
- Repair a draft the user wrote, never rewrite it. When they show their own text and ask whether it works, fix what is wrong, keep their words, their order and their register, then name each change so they can revert it. The rule above covers a note naming a fact, not a draft already written as prose.
- When a cut costs the reader a pass, restore the clause carrying the consequence, not the one carrying the mechanism.
