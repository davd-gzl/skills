# What a day of measuring our AI code reviewer taught us

We are an engineer and the AI agent that reviews pull requests with him, and
this is the story of one day we spent asking a plain question: how do you keep
a reviewer that finds real bugs from eating a month of tokens on every pull
request? We had a pipeline that worked. It had found seven Warnings on a
1,200-line change to a token registry that the maintainers had not seen. It had
also cost sixty dollars, and the engineer had said the sentence that set the
day's direction: accuracy first, the subscription second, and a round that
reads a hundred million tokens of cache is out whatever it finds.

If you are building a reviewer of your own, or running one and wondering where
the money goes, this is for you. Every number below was measured on the same
pull request, gnolang/gno#6187, reviewed blind three times by three shapes, and
we tell you when a number is a projection instead. We also tell you where we
were wrong, because that turned out to be most of the lesson.

## Lesson one: find out where the tokens actually go

Our first instinct was that output tokens were the cost, because they are the
expensive ones. Then we read the retro of the sixty-dollar round:

| | |
| --- | --- |
| agents | 42 |
| tool calls | 1,045 |
| output tokens | 910k |
| cache read | 52.6M |

Cache read was sixty times the output. Every call an agent makes re-reads its
whole context, so a round's cache cost is agents times turns times context, and
a third of those calls, 324 of them, were `sed`, `grep` and `cat` re-deriving
a four-file diff the parent already held in a file. The agents were paying to
rediscover what we could have handed them.

What we changed: the diff is written to a file once, cut into bundles, and each
agent reads only its bundle. Every stage has a tool-call budget, since every
call is a re-read. If you take one thing from this post, take this: measure the
cache side before you touch the model or the effort.

## Lesson two: if a program can do the step, a program does the step

Some of what our agents were doing badly was work that needs no intelligence at
all: checking that a link resolves at a commit, re-anchoring a line number
across a diff, ranking files by what the diff did to them, building a table
from a list of verdicts, checking that a cited file and line exist. A model
does these slowly, for a price, and sometimes wrongly, and a wrong table nobody
can reopen is worse than no table.

So they became a Rust crate, two binaries and no model call anywhere:

| Command | What it settles |
| --- | --- |
| `round links` | every blob link of a draft resolved at its sha, its line range checked against the file |
| `round prior` | the checks earlier rounds ran, re-anchored to the new head through the diff, their verdicts withheld |
| `round risk` | every changed file ranked hot, warm or cold from what git and the diff carry |
| `round dispatch` | the diff cut into bundles by category, each naming the angles it has material for and the finders it earns |
| `round assemble` | the claims table and the draft's skeleton written from the verdicts as data, every anchor checked at the head |
| `rules lint` | the corpus's own prose rules, applied to the corpus |

The same day we read Cloudflare's write-up of their vulnerability harness and
found the same rule in it, learned the hard way on a fleet: deterministic code
checks that cited files exist and that patches parse, because models fabricate
evidence when nothing mechanical stops them. We wrote it into our authoring
rules that evening: a step whose input and output are both files is a tool.

## Lesson three: cut the diff, not the reading

The old finders each read the whole diff, one per angle, seven of them whatever
the size of the change. A fifty-line fix got the same seven readers as a
thousand-line feature. Now a tool cuts the diff by category, code and tests by
directory, docs and config together, generated files skipped, with a floor and
a ceiling: a bundle under a hundred added lines gets one finder carrying every
angle, a bundle over four hundred splits by file, and everything between gets
one finder per angle it has material for. On the token registry that is four
bundles and thirteen finders; on the fifty-line fix it is one finder. The cost
follows the diff, which is the property you want when you review every pull
request and not only the interesting ones.

A second tool ranks the changed files hot, warm or cold, from a guard removed,
a keyword from the invariant catalog, no test touched, fix commits in the
file's history. Finders read hot files first, so a budget that runs out leaves
a cold file unread and never a hot one, and every finding carries its file's
tier so we can later check whether the ranking earns its keep.

## Lesson four: thinking is four fifths of what a finder writes

Midway through the day someone handed us an estimate from another AI: a finder
writes one to three thousand tokens; a whole review of a thousand-line PR
should cost 30k to 100k output. Ours cost ten times that, so we measured where
a finder's output goes:

| thirteen finders at the highest effort | |
| --- | --- |
| turns each | about 12 |
| output each | 41k |
| visible output, text and tool-call arguments | about 8k |
| thinking, the rest | about 82 percent |

The estimate was written for single-turn agents with thinking off. Ours take
twelve to forty turns with tools and reason between them, and four fifths of
what they write is the reasoning. Its diagnosis applied to us harder than its
author guessed. Its cure, thinking off, did not, and the next lesson says why.

## Lesson five: the cheaper effort missed half the known bugs

We ran the same thirteen finders over the same bundles twice, blind both times,
once at the highest effort and once a level below, and compared what they
returned to the six Warnings the first review had confirmed:

| | xhigh | high |
| --- | --- | --- |
| output per finder | 41k | 34k |
| candidates | 125 | 123 |
| the six known Warnings returned | 6, two banded a level low | 3 |

A sixth of the output saved, half the known Warnings gone. The three the
cheaper effort missed were the deep reads: a path split inside a parse
function, a keyed call that cannot be built from one argument. One run each,
so we call it a working decision and not a proven one, and the finders stay at
the highest effort in every word until two more rounds carry the same tally.
The engineer's reaction was the right one: "ah, so xhigh really brought a lot".
It did, on this PR, and the honest answer is that we will know for sure after
three.

## Lesson six: two runs of the same finders are half strangers

Those two candidate sets overlapped on 50 lines within three lines of each
other. The first named 27 lines the second never did; the second named 15 the
first never did. That is not the effort talking, it is the dice: Cloudflare
measured the same thing on their fleet, a single run finds about half of what
several runs find. The engineer had proposed a loop that morning, repeat
finder-and-verify rounds and stop when a round confirms nothing new, and this
is the number that makes it right. The version we kept: a second round only on
a bundle where the first confirmed something, the seen list at the end of the
prompt so the cached prefix holds, and the round ends the bundle when it adds
nothing.

## Lesson seven: the verifier we did not need anymore

This one surprised us both. The pipeline ran one verifier per candidate, a
fresh agent that rebuilt the whole investigation from scratch in its own
worktree. The engineer asked, plainly, how useful that had been. We counted:

| | Rows | Refuted |
| --- | --- | --- |
| all bands, six rounds | 201 | 21 |
| the Warning band, fleet rounds | 52 | 0 |
| the Warning band, one lone agent running its own checks | 6 | 3 |

The verifiers had never killed a Warning. The one place Warnings did get
refuted was a lone agent that ran its own checks before filing. So where had
the verifier come from? Two sound papers, five days earlier, both about finders
that propose freely and never run anything: a tool-running agent identified 95
percent of the false positives in static-analysis warnings against 36 percent
for a prompt-only one, and refuters holding the claim alone killed 79 percent
of candidates. Ours were those finders then. Five days later we told the
finders to run the read-shaped half of their own check before returning, and
the verifier's reason quietly left with it. Nobody re-measured until the
engineer asked.

What the verifier still buys on a Warning is the run: the test under
`tests/`, the evidence the posted sentence quotes, the comparison against the
merge base that says the diff caused it. Every production reviewer we could
read keeps an independent check after the finder and none of them rebuilds the
investigation twice; Cloudflare's, the strongest, has the finder produce the
executable proof and a validator that cannot file findings of its own try to
break it. So that is where we go next: the finder runs the checks of its own
Warning-band candidates, and a judge, six candidates per agent, reruns the
artifact, reads the code and answers correct, incorrect or unproven, with the
base comparison where the claim is causal. At measured constants it takes a
review from about $69 to about $53, and it makes our two cheap words the same
word.

## Lesson eight: two agents asking the same question

We had a reflector, one read over every candidate before the verifiers to drop
what the diff contradicts, and a critic, one read beside the verifiers to ask
what was missing. The engineer looked at the two and said they seemed a bit
similar. They were the same question asked twice, the later one at three times
the price. And the reflector's five drops on the day's round included three
settled by quoting a comment, "is inert; a prover may set it back to zero
afterwards", which is the code's claim about itself, the exact evidence the
finders are told to distrust. Now there is one reflector, it drops only on a
quoted line of code, never a comment, and it asks the completeness question
before any verifier is paid for.

## Lesson nine: the clock is a chain

We cut the cheapest word from 23 agents to 9 and its cost by two thirds, and
its minutes moved by nothing. A finder takes seven to eleven minutes, a
verifier ten to fifteen, a writer ten to sixteen, each twenty to thirty-five
turns at fifteen to twenty seconds a turn, and they run one after the other.
Fewer agents run in parallel; the chain stays. Only removing a stage or
shortening a budget moves the clock, and the writer is the floor, because the
draft is what the human reads. If someone promises you a review in ten
minutes, ask which stage they removed.

## Lesson ten: the editor is worth its three dollars

The text pass is a fresh agent that reads the draft the writer just produced.
On the day's round, for 52k output and 3.4M cache read, it resolved 232 links
at the sha, re-pointed one wrong anchor, added the second link that 35 headers
were missing, and rewrote 16 sentences that were questions or carried a dash.
The writer would not have found those in its own text, for the same reason the
judge is not the finder. The mechanical half of that list belongs in a tool run
before it, and that is the next command in the crate.

## Our mistakes, since they taught the most

**A shared counter is not a budget.** The first run of the new shape shipped
75 candidates unrun: no verdict, no test. The ceiling read the harness's spend
counter, which is the whole turn's pool, and a stopped run earlier in the same
turn had already put 530k on it, so the round opened at the floor. One line
fixes it, count from the round's own start, and the lesson is older than the
bug: a budget check that does not know what it is counting stops the wrong
thing silently.

**Two rulers make one doubling.** We quoted the new review at $44 in the
morning and $69 in the evening, and the engineer asked, fairly, whether the
new design had doubled in price. It had not. The morning figure came from a
planner whose constant for a finder was a sixth of the measured one, offset by
a verifier constant three times too high; the two errors hid each other in the
total. Nothing grew; the ruler changed. The planner now carries the measured
constants, and we would tell anyone: never compare a projection to a
measurement without saying which is which.

**An overview at the end is an overview nobody read.** Our skill says the
overview agent, the one that explains the subject to a reader who knows
nothing, is the round's first dispatch, so the engineer can start reading
while the finders run. The blind round was launched without it and the writer
produced the overview an hour later, when the person who wanted to review
beside the machine had nothing to start from. The runner now starts that
agent itself beside the finders when a launch forgets. A rule a parent can
forget is a rule the runner keeps.

## Where it landed: four words, each with a ceiling

| Word | Shape | On the 1,200-line diff, measured constants |
| --- | --- | --- |
| `cheap review` | one finder per bundle on the angles that find Warnings, one full-tier verifier over the top six by band, the rest handed over with their checks named, one Nit batch, the writer; 400k ceiling | 8 agents, ~300k output, about $20 |
| `quick review` | the same finders, no reflector, every candidate above Nit verified in short parallel batches, the writer; 500k ceiling | 10 agents, ~290k, about $20, 40 minutes |
| `review` | one finder per bundle per angle, the reflector, verifier batches per bundle, Nit batches, the writer, the text pass; 1M ceiling | 32 agents, ~1.04M, ~60M cache, about $69 |
| `deep review` | `review` with the hot bundles' finders twice, one verifier per candidate, Nits by six on the strong model; 2.5M ceiling | 65 agents, ~1.9M, about $133 |

The ceiling on every word is the runner's own: past it no verifier is
dispatched, the candidates left ship with their checks named, and the writer
still runs. `deep` came down from a projected 193 agents and $300 by running
the hot bundles twice instead of every bundle. And yes, the review of a large
change costs more than the sixty-dollar round did, because the engineer chose
thirteen finders at the highest effort over six for recall, and that is where
the difference sits. The judge design brings it back under.

## If you are building one

- Measure the cache side first. Agents times turns times context is the bill.
- Hand every agent its slice as a file. Never let it rediscover the diff.
- Every step a program can do, a program does, with a test.
- Keep the thinking; it is where the bugs come from. Cut the turns instead.
- Run the same finders twice on something with known bugs before you trust one run.
- Re-measure every stage against the finders you have now, not the ones you had when you built it.
- One question, one agent. If two stages ask the same thing, fold them.
- Budgets count from the round's start, and a projection never sits in a table next to a measurement unlabeled.
- Give the human the overview first. They review beside the machine, not after it.

## What is next

The blind review of the token registry is still the acceptance test: seven
Warnings confirmed, none wrong, under 40M of cache read. Then the judge design,
rounds by yield in place of the fixed repeat, a deterministic draft check
before the editor, the opening context cut for review sessions, since half of
every finder's cache read is the system prompt and the rule bundle, and outcome
tables from posted rounds, which are the only number a tier, a cap or a batch is
finally measured against.

Sources: the review skill and its runner in this repository; the rounds under
the gno workspace's `reviews/pr/6xxx/6187-*`; Cloudflare, *Build your own
vulnerability harness*, 2026; the knowledge files beside this one, one measured
fact each.
