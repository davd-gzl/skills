---
title: "The shape of a review: what a day of measuring an AI code reviewer taught us"
permalink: /blog/2026-09-17-the-shape-of-a-review/
---


A review pipeline that finds real bugs is easy to make expensive and hard to
make cheap without losing the bugs. This is the story of one day spent on that
trade, with the numbers that settled each call. The reviewer is the one in this
repository, `review.md` and the runner beside it; the target it was measured on
is a 1,200-line pull request to gnolang/gno, a token registry realm, reviewed
blind three times by three different shapes. Everything below is measured
unless it says projected.

## Where we started

The pipeline already worked. Six finders read the whole diff, one per angle,
one verifier ran every candidate from scratch in its own worktree, a critic
asked what was missing, a writer drafted the comment and a text pass proofread
it. On the token registry it confirmed seven Warnings the maintainers had not
seen, and it cost this:

| | |
| --- | --- |
| agents | 42 |
| tool calls | 1,045 |
| output tokens | 910k |
| cache read | 52.6M |
| at API list prices | about $60 |

Two facts in that table set the day's direction. Cache read was sixty times
the output: every call re-reads the agent's whole context, so a round's cache
cost is agents times turns times context, and 324 of the 1,045 calls were
`sed`, `grep` and `cat` re-deriving a four-file diff the parent already held.
And the seven Warnings were the bar: any cheaper shape had to find them again,
blind, or it was not cheaper, it was worse.

A second measurement framed the other end. One agent alone, the strongest
model at the highest effort, reviewing the same diff blind in a single
context, spent 286k tokens and 71 calls and confirmed three of the seven. Its
transcript showed why: it never enumerated angles. No mutation runs, no walk
of the invariant catalog, no refactor pass, no critic, and it stopped with
most of its call budget unspent. It also found one Warning the fleet had
missed, a documented example that fails when run from outside the package,
which became its own rule: the example in the doc is a claim, and a claim gets
its check.

## What we built

### Deterministic steps became a tool

Every step that a model was doing badly and a program does perfectly moved
into one Rust crate, `tools/`, two binaries and no model call anywhere:

| Command | What it settles |
| --- | --- |
| `round links` | every blob link of a draft resolved at its sha, its line range checked against the file |
| `round prior` | the checks earlier rounds ran, re-anchored to the new head through the diff, their verdicts withheld |
| `round risk` | every changed file ranked hot, warm or cold from what git and the diff carry |
| `round dispatch` | the diff cut into bundles by category, each naming the angles it has material for and the finders it earns |
| `round assemble` | `claims.md` and the draft's skeleton written from the verdicts as data, every anchor checked at the head |
| `rules lint` | the corpus's own prose rules, applied to the corpus |

The crate has 78 tests. Cloudflare's harness write-up, read the same day,
lists the same lesson from a fleet of security agents: deterministic code
checks that cited files exist and that patches parse, because models fabricate
evidence when nothing mechanical stops them.

### The unit became a bundle, and the finder count follows the diff

Finders used to read the whole diff, one per angle, seven of them whatever the
size of the change. Now `round dispatch` cuts the diff by category, code and
tests by directory, docs and config together, generated files skipped, with a
floor and a ceiling: a bundle under a hundred added lines gets one finder
carrying every angle, a bundle over four hundred splits by file, and every
other bundle gets one finder per angle it has material for. On the token
registry that is four bundles and thirteen finders; on a fifty-line change it
is one bundle and one finder. Each finder reads its bundle's diff with the
enclosing functions, written to a file once, and never re-derives it.

### Risk decides the order

`round risk` scores each file on what the diff did to it: a guard removed, a
catalog keyword added, no test touched, fix commits in its history, its size.
Docs, tests and generated files are cold. The table is printed before the
round, every finder reads hot files first so a budget that runs out leaves a
cold file unread and never a hot one, and every row of the claims table
carries its file's tier so the retro reads the hit rate per tier and moves the
weights.

### A reflector before any verifier is paid for

One agent reads every candidate against the diff after the finders return and
before the first verifier starts. It may only remove, and only when a quoted
line contradicts the candidate outright: the guard called missing sits three
lines up, the value called unbounded is clamped at the call site. Unsure keeps
the candidate, since a Warning dropped on a guess is the round's worst
outcome. Then it asks what is missing and returns that as candidates with the
check that settles each.

### Verification in batches, by tier

Warnings and anything needing a mutation or a comparison against the merge
base go to the full tier, three candidates of one bundle per agent, each still
run from scratch in a scratch worktree. Read-shaped checks go to a cheaper
tier in batches of four. Nits go to that tier twelve at a time, a read and
never a run, and every Nit is verified: a Nit the read cannot settle comes
back PLAUSIBLE and ships as `SKIP`, never as a posted claim. The cheaper model
earned that seat with a side-by-side on four known Nits: four of four in four
calls, against three of four in six for the strong model.

### The round's record lives on disk

Every stage now writes what it returns under the round directory as it goes,
`candidates/` for the finders, the reflector and the critic, `verdicts/` for
the verifiers, so a dead agent loses its own file and nothing else, and the
writer's prompt carries no row and no evidence. `round assemble` reads those
files, joins each verdict to its candidate, writes the claims table, the rows
the finders settled, the hit rate per tier, and `findings.md`, one block per
finding in posting order with its check on it, and exits 1 naming every anchor
that is not at the head. The writer composes the text from that file and
retypes nothing.

### Four words, each with a ceiling

| Word | Shape | Projected on the 1,200-line diff |
| --- | --- | --- |
| `cheap review` | one finder per bundle on the angles that find Warnings, one full-tier verifier over the top six by band, the rest handed over with their checks named, one Nit batch, the writer; 400k ceiling | 8 agents, 225k output, about $10 |
| `quick review` | the same finders, no reflector, every candidate above Nit verified in short parallel batches, the writer; 500k ceiling | 10 agents, 220k output, about 40 minutes, about $10 |
| `review` | one finder per bundle per angle, the reflector, verifier batches per bundle, Nit batches, the critic, the writer, the text pass; 1M ceiling | 33 agents, 760k output, about $45 |
| `deep review` | `review` with the hot bundles' finders twice, one verifier per candidate at 30 calls, Nits by six on the full tier; 2.5M ceiling | 66 agents, 1.5M output, about $100 |

`cheap` is flat: one verifier whatever the diff, so a large change costs the
same ten dollars and hands the reviewer more checks to run by hand. `quick` is
flat on the clock and grows with the diff. `deep` came down from a projected
193 agents and $300 by running the hot bundles twice instead of every bundle,
capping Nits at eight instead of sixteen, and batching. A fifth word, `lean`,
cost more than `cheap` for less recall and was folded away. The ceiling on
every word is the runner's own: past it no verifier is dispatched, the
candidates left ship with their checks named, and the writer still runs.

## What we learned

### Thinking is four fifths of a finder's output

The estimate that started this thread said a finder writes one to three
thousand tokens. Ours write forty thousand, and the split, measured on
thirteen finders at the highest effort, is this:

| | |
| --- | --- |
| turns per finder | about 12 |
| output per finder | 41k |
| visible output, text and tool-call arguments | about 8k |
| thinking | about 82 percent |

The estimate was written for single-turn agents with thinking off. Ours take
twelve to forty turns with tools and reason between them. Its diagnosis
applied to us harder than its author would have guessed; its cure, thinking
off, did not, because a finder reading 740 lines of realm code against an
invariant catalog has to reason, and the one-agent run that found the missed
Warning was the one that reasoned hardest.

### The effort dial: one measurement, one call

The same thirteen finders over the same bundles ran once at the highest effort
and once a level below, blind both times:

| | xhigh | high |
| --- | --- | --- |
| output per finder | 41k | 34k |
| candidates | 125 | 123 |
| the six known Warnings returned | 6, two banded Nit | 3 |
| Warning-band lines named | 19 | 16 |

A sixth of the output saved for half the known Warnings gone. The three high
missed were the deep reads: a path split inside a parse function, a keyed call
that cannot be built from one argument. One run each, so it is a working call
and not a proven one, and the finders stay at the highest effort in every word
until two more rounds carry the same tally.

### Two runs of the same finders are half strangers

The two candidate sets above overlapped on 50 lines within three lines of each
other. The first named 27 lines the second did not; the second named 15 the
first did not. That is the spread Cloudflare measured on its fleet, a single
run finds about half of what several runs find, and it is the case for a
second round on a bundle that yielded. The plan's answer is a loop rather than
a fixed repeat: round two runs only where round one confirmed something or the
bundle is hot, with the seen list at the end of the prompt so the cached
prefix holds, and a round confirming nothing new ends the bundle.

### The clock is a chain

Cutting `quick` from 23 agents to 9 cut its cost by two thirds and its minutes
by nothing. A finder takes seven to eleven minutes, a verifier ten to fifteen,
a writer ten to sixteen, each twenty to thirty-five turns at fifteen to twenty
seconds a turn, and they run one after the other. Fewer agents run in
parallel; the chain stays. Only removing a stage or shortening a budget moves
the clock, and the writer is the floor, since the draft is what the reviewer
reads.

### The text pass is the cheapest stage and not the least useful

On a draft the writer had just produced, the text pass, 52k output and 3.4M
cache read, about three dollars, resolved 232 links at the sha, re-pointed one
wrong anchor, added the second link 35 headers were missing, and rewrote 16
sentences that were questions or carried an em-dash. A fresh context catches
what the author cannot see, the same reason the verifier is not the finder.
The mechanical half of that list belongs in a tool run before it, and that is
the next command in the crate.

### A shared counter is not a budget

The first run of the new shape shipped 75 candidates unrun: no verdict, no
test, no critic. The ceiling read the harness's spend counter, which is the
whole turn's pool, and a stopped run earlier in the same turn had already put
530k on it, so the round opened at the floor. The fix is one line, count from
the round's own start, and the lesson is older than the bug: a budget check
that does not know what it is counting stops the wrong thing at the wrong
time, silently.

### Two rulers make one doubling

The planner projects cache read as agents times turns times context from the
last measured round's per-stage constants. Its constants said a bundle finder
writes 24k, halved again on a guess; the day measured 41k. Its verifier
constants said four million of cache per agent; the first review's round-wide
mean was 1.3M. The two errors hid each other in the total, and a `review`
quoted at $44 in the morning was $69 on measured constants by the evening, with
the first review's $60 between them. Nothing had grown; thirteen finders at
the highest effort cost what they cost. The planner now carries the measured
constants, and a projection is a number until an outcome table measures it.

### The verifier outlived the finders it was built for

The one-verifier-per-claim stage came from two papers on 2026-09-11: a
tool-running agent identified 95 percent of the false positives in
static-analysis warnings against 36 percent for a prompt-only one, and
refuters holding the claim and none of the finder's reasoning killed 79
percent of candidates. Both describe finders that propose freely and never
run anything, and ours were those finders then. Five days later the finder
rule changed, run the read-shaped half of your own check before returning,
and the verifiers' refute rate on Warnings has been zero since:

| | Rows | Refuted |
| --- | --- | --- |
| all bands, six rounds | 201 | 21 |
| the Warning band, fleet rounds | 52 | 0 |
| the Warning band, the lone agent running its own checks | 6 | 3 |

What the verifier still buys on a Warning is the run: the artifact under
`tests/`, the evidence the posted sentence quotes, the merge-base comparison.
Every production reviewer we could read keeps an independent check after the
finder and none rebuilds the investigation twice; the strongest, Cloudflare's,
has the finder produce the executable proof and a validator that cannot file
findings of its own try to break it. That is where the next round goes: the
finder runs the checks of its own Warning-band candidates, and a judge, six
candidates per agent, reruns the artifact, reads the code and answers correct,
incorrect or unproven, with the base comparison where the claim is causal. At
measured constants it takes `review` from about $69 to about $53, and it makes
`cheap` and `quick` the same word.

### An overview at the end is an overview nobody read

The skill says the overview agent is the round's first dispatch, so the reader
has the subject on disk and linked while the finders run. The blind round was
launched without it and the writer produced the overview at the end, an hour
later, when the reader who wanted to review beside the machine had nothing to
start from. The runner now starts that agent itself beside the finders when a
launch comes without one; a rule a parent can forget is a rule the runner
keeps.

### Where sonnet sits, and where it does not

The cheaper model verifies Nits and read-shaped checks, on a measurement. It
runs nothing that decides, drops or writes: not the reflector, not the
verifier of a Warning, not the critic, not the writer, not the text pass. A
proposal to seat it as a cross-model reflector was refused on the ground that
it is less capable, and the rule that came out of it is the right one: a
second model for the adversary is worth having when it is as capable as the
first, and an upgrade to note until the plan allows it, never a tier down.

### What Cloudflare's fleet taught a pull request reviewer

Their harness scans repositories continuously; ours reviews one change. The
lessons that carried over: state the loss before the claim, so the schema's
field order puts the failure scenario first; check every cited file and line
mechanically before a human reads it; flag a finder returning nothing as a
possible crash and rerun it once; let an agent name what it lacked, so a
missing toolchain requeues instead of shipping a PLAUSIBLE; measure coverage
by whether re-runs still surface new findings. The lessons that did not: per-PR
review too slow for them, and static analysis they never invoked, since neither
is what a reviewer of one diff runs on.

## What the numbers say together

| Round | Agents | Output | Cache read | Known Warnings | About |
| --- | --- | --- | --- | --- | --- |
| one agent alone, blind | 1 | 286k in all | | 3 of 7 | $6 |
| the first fleet | 42 | 910k | 52.6M | 7 of 7 | $60 |
| the new `review`, projected | 33 | 760k | 36M | the bar | $45 |
| the new `review`, finders measured | 13 of 33 | 443k | 14.5M | | |

The saving the new shape was built for is on the cache side, from bundle-scoped
diffs, bounded calls, batched verification and a writer that reads the record
from disk. The output side barely moves, because four fifths of it is thinking
and the thinking is where the Warnings come from. Accuracy ranks first; the
subscription second; and a round reading a hundred million tokens of cache is
out whatever it finds.

## What is next

Three changes landed as the day closed, on the numbers above: the critic folded into the reflector, one read that drops on code lines only, never on a comment, and asks what is missing before any verifier runs, since the two agents asked the same question and the later one cost three times more; the overview agent started by the runner beside the finders; and every word carrying its own output ceiling. The blind `review` on the token registry is the acceptance run: it passes when
it confirms the seven Warnings with none wrong and its cache read sits under
40M. Its retro replaces the projection's constants. After it: rounds by yield
in place of `deep`'s fixed repeat, a deterministic draft check before the text
pass, the opening context cut for review sessions since half of every finder's
cache read is the system prompt and the rule bundle, and outcome tables from
posted rounds, which are the only number a tier, a cap or a batch is measured
against.

Sources: the review skill and its runner in this repository; the rounds under
the gno workspace's `reviews/pr/6xxx/6187-*`; Cloudflare, *Build your own
vulnerability harness*, 2026; the knowledge files beside this one, one
measured fact each.
