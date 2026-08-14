# Skills

My skills: the instruction sets my agents load before working on my projects.
One file per task, each self-contained.

## How I work

Everything starts with a review, on a PR, a branch, or a red CI.
[`review.md`](review.md) drives it in ten steps:

1. **Fetch and understand.** Sync the checkout, pull the diff, read every
   comment and past review, then read every changed file in full and map its
   callers.
2. **Re-review gate.** When a prior round exists, compare patch-ids to tell
   new code from a branch that just moved on its base. A base-only move copies
   the old round forward; nobody re-reviews unchanged code.
3. **Reproduce.** Run the project's own CI commands locally. Every failure is
   re-run on the merge base before the diff gets the blame.
4. **Review the diff.** The hunt itself, under one discipline: a behavior
   claim ships with the run that proves it, and a repro that also fires on the
   merge base is not a finding.
5. **Write the tests.** A finding whose fix is a test ships the test itself,
   paste-ready, not a description of one.
6. **Review file.** The complete record: verdict, findings graded Critical to
   Suggestion, repros, every claim linked to the reviewed line.
7. **Comment draft.** The postable artifact, one anchored comment per finding,
   at most three sentences each, pruned by hand before anything ships.
8. **Style pass.** The closing Pass of
   [`writing-style.md`](writing-style.md): six mechanical checks, in order,
   against the file and not from memory. Never skipped.
9. **Commit and push.** The record lands in my workspace, nothing else moves.
10. **Hand over.** I read the draft and decide; nothing reaches GitHub until I
    say so.

Around the review, six more skills. [`issue.md`](issue.md) drafts an issue when
a problem outlives its fix, stating the problem and never the remedy.
[`pr-body.md`](pr-body.md) writes the PR title and body for a reader with no
context, symptom first, looping until a full pass changes nothing.
[`fix-issue.md`](fix-issue.md) takes an issue to a pull request on my fork,
planned first, implemented in a worktree, then watches its CI.
[`security-advisory.md`](security-advisory.md) handles the findings a review
cannot publish, the ones that work against deployed code: verified by running
the exploit, written up privately, disclosed through the project's own channel.
[`review-history.md`](review-history.md) answers what was already reviewed,
read-only, from the corpus on disk rather than by reviewing it again. And
[`report.md`](report.md) turns a period of repository activity into a status
report, generated only after I have edited its context file.

## Why the style matters most

Everything posted lands in front of a maintainer who did not ask for it. The
one favor to do them is a comment that reads in one pass: the problem, its
stake, the line it sits on, and nothing else. At most three sentences, plain
English, no jargon, no walkthrough of their own code, the problem and not the
fix. A finding that cannot be said simply is not understood yet. Depth is
never lost, it just lives in the review file; the comment carries only what
changes what the author does next.
