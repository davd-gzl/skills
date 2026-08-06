# Skills

My skills: the instruction sets my agents load before working on my projects.
One file per task, each self-contained.

## How I work

1. **Everything starts with a review.** On a PR, a branch, or a red CI,
   [`review.md`](review.md) drives it: sync the checkout, read every changed
   file in full plus its callers, then verify each claim with a real run. A
   behavior claim ships with the run that proves it, and a repro that also
   fires on the merge base is not a finding. Findings come out graded:
   Critical, Warning, Missing test, Nit, Suggestion.
2. **Two artifacts per review.** The review file is the complete record:
   verdict, findings, repros, everything verified. The comment draft is the
   postable one, pruned by hand comment by comment. Nothing reaches GitHub
   until I say so.
3. **A problem that outlives its fix gets an issue.** [`issue.md`](issue.md)
   searches upstream first, then drafts one that states the problem and where
   it comes from, never the remedy: naming a fix is designing it, and the
   issue is the wrong place.
4. **A fix gets a body worth its diff.** [`pr-body.md`](pr-body.md) writes the
   title and the body for a reader with no context who must decide whether to
   merge: symptom first, fix as a property of the new code, verification as
   claims, and a revision loop that only stops when a full pass changes
   nothing.
5. **Style is enforced, not hoped for.**
   [`writing-style.md`](writing-style.md) governs every visible line the other
   skills produce, and its closing Pass runs over each artifact before it
   ships: six mechanical checks, in order, against the file and not from
   memory.

## Why the style matters most

Everything posted lands in front of a maintainer who did not ask for it. The
one favor to do them is a comment that reads in one pass: the problem, its
stake, the line it sits on, and nothing else. At most three sentences, plain
English, no jargon, no walkthrough of their own code, the problem and not the
fix. A finding that cannot be said simply is not understood yet. Depth is
never lost, it just lives in the review file; the comment carries only what
changes what the author does next.
