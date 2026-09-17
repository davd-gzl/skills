# Eleven measured lessons from an AI code reviewer

Context: a pipeline of agents that reviews pull requests, finders per angle,
verifiers, a writer and a text pass, run by one engineer with an AI agent. It
had found seven Warnings on a 1,200-line change to gnolang/gno, PR 6187, for
about sixty dollars. Constraint: accuracy first, the subscription second, and
no round reading a hundred million tokens of cache. What follows is what the
measurements of one day said, each with the number, what it changed, and what
a reader building or running a reviewer can reuse. Projections are marked as
such.

## 1. Cache read, not output, is where the tokens go

| the sixty-dollar round | |
| --- | --- |
| agents | 42 |
| tool calls | 1,045 |
| output tokens | 910k |
| cache read | 52.6M |

Every tool call re-reads the agent's whole context, so a round's cache cost is
agents times turns times context. 324 of the 1,045 calls were `sed`, `grep`
and `cat` re-deriving a four-file diff that already existed as a file.

Changed: each agent receives its slice of the diff as a file and a tool-call
budget. Reusable: measure agents, turns and context per turn per stage before
touching the model or the effort; the retro script prints all three.

## 2. A step a program can do is a tool

Resolving a link at a commit, re-anchoring a line across a diff, ranking files
by what the diff did to them, cutting a diff into bundles, writing a table from
verdicts, checking that a cited line exists. Asked of a model, each is slow,
paid, and sometimes wrong. They are one Rust crate with no model call:

| Command | Settles |
| --- | --- |
| `round links` | every link of a draft resolved at its sha, the line range checked |
| `round prior` | earlier rounds' checks re-anchored to the new head, verdicts withheld |
| `round risk` | changed files ranked hot, warm or cold |
| `round dispatch` | the diff cut into bundles, each naming its angles and the finders it earns |
| `round assemble` | the claims table and the draft's skeleton from the verdicts, every anchor checked |
| `rules lint` | the corpus's prose rules, applied to the corpus |

Cloudflare's vulnerability harness carries the same rule: deterministic code
checks that cited files exist and that patches parse, because models fabricate
evidence when nothing mechanical stops them. Reusable: when a step's input and
output are both files, write the tool, give it a test, and have the skill name
the command.

## 3. The finder count follows the diff

Before: seven finders read the whole diff whatever its size. After: a tool
cuts the diff into bundles by category, code and tests by directory, docs and
config together, generated files skipped, with a floor and a ceiling. Under a
hundred added lines, one finder carries every angle; over four hundred, the
bundle splits by file; between, one finder per angle with material. PR 6187
gets four bundles and thirteen finders; a fifty-line fix gets one. A second
tool ranks files by risk so a finder that runs out of budget leaves a cold
file unread, never a hot one. Reusable: cost that scales with the diff is what
makes reviewing every pull request affordable.

## 4. Thinking is four fifths of a finder's output

| thirteen finders at xhigh | |
| --- | --- |
| turns each | about 12 |
| output each | 41k |
| text and tool-call arguments | about 8k |
| thinking | about 82 percent |

An estimate written for single-turn agents with thinking off puts a finder at
one to three thousand tokens. Agentic finders, twelve turns with tools and
reasoning between them, write forty thousand, and the reasoning is most of it.
The lever is the effort level, and lesson 5 is what it costs to lower it.

## 5. One effort level down lost half the known Warnings

The same thirteen finders over the same bundles, blind, once at xhigh and once
at high, against the six Warnings an earlier review had confirmed:

| | xhigh | high |
| --- | --- | --- |
| output per finder | 41k | 34k |
| candidates | 125 | 123 |
| known Warnings returned | 6 | 3 |

A sixth of the output saved, half the known bugs gone. The three missed at
high were deep reads: a path split inside a parse function, a keyed call that
cannot be built from one argument. One run each, so a working decision, not a
proven one: finders stay at xhigh until two more rounds repeat the tally.
Reusable: test an effort change on a target with known bugs, never on cost
alone.

## 6. Two runs of the same finders overlap by half

The two candidate sets above shared 50 lines; the first named 27 the second
did not, the second 15 the first did not. Cloudflare reports the same on their
fleet: a single run finds about half of what several find. Changed: repeats
become a loop, a second round only on a bundle where the first confirmed
something, the seen list at the end of the prompt so the cached prefix holds,
and the bundle ends when a round adds nothing. Reusable: one run of a finder
is a sample, and coverage is measured by whether the next run still finds new
things.

## 7. The verification stage had stopped earning its cost

One verifier per candidate, a fresh agent rebuilding the investigation in its
own worktree, over six rounds:

| | Rows | Refuted |
| --- | --- | --- |
| all bands | 201 | 21 |
| Warnings, fleet rounds | 52 | 0 |
| Warnings, one lone agent running its own checks | 6 | 3 |

The stage came from two papers about finders that never run anything: a
tool-running agent caught 95 percent of false positives against 36 for
prompt-only, and refuters holding the claim alone killed 79 percent. Five days
after adopting it, the finders were told to run the read-shaped half of their
own check before returning, and the verifiers' refute rate on Warnings has
been zero since. What the run still buys on a Warning is the artifact, the
evidence the posted sentence quotes, and the merge-base comparison.

Changed, the same evening: the finder runs the checks of its own
Warning-band candidates and writes the artifact; a judge, six candidates per
agent, reruns the artifact, reads the code and answers correct, incorrect or
unproven, keeping the base comparison for causal claims; Missing tests,
Suggestions and Nits go to a judge by read, twelve per agent, and the cheaper
tier is gone. Every production reviewer read for this keeps an independent
check after the finder and none repeats the finder's work; Cloudflare's finder
produces the executable proof and a validator that cannot file findings tries
to break it. Not yet measured: the first judged round is the acceptance run.
Reusable: re-measure every stage against the finders you have now, not the
ones the stage was built for.

## 8. Two agents asking one question

A reflector dropped, before verification, what the diff contradicts; a critic
asked, beside the verifiers, what was missing. Same question, the second at
three times the cost. Of the reflector's five drops on the measured round,
three were settled by quoting a comment, the code's own claim about itself,
which the finders are told to distrust. Changed: one reflector, dropping only
on a quoted line of code, asking the completeness question before any
verifier runs. Reusable: when two stages ask the same question, fold them, and
never let a comment settle a drop.

## 9. Minutes are a chain, not a sum

Cutting the cheapest word from 23 agents to 9 cut its cost by two thirds and
its clock by nothing. Measured per agent: a finder 7 to 11 minutes, a verifier
10 to 15, a writer 10 to 16, at twenty to thirty-five turns and about fifteen
seconds a turn, one stage after the other. Only removing a stage or shortening
a call budget moves the clock; the writer is the floor.

## 10. A fresh editor over the draft finds what the writer cannot

The text pass, a separate agent reading the draft after the writer, resolved
232 links, re-pointed one wrong anchor, added the second link 35 headers were
missing and rewrote 16 sentences, for 52k output and 3.4M cache read. The
mechanical half of that list is now a tool, `round check`, run by the writer
before it returns, so the pass keeps the judgement. Reusable: the author of a
text does not see its errors; a second context does, cheaply.

## 11. The shape follows the change, not the word

A seven-line fix and a 1,200-line feature were getting the same round, and
the projection made the seven lines cost half the twelve hundred: a 40k
overview, a full judge for one candidate, a text pass over three findings.
Changed: a triage agent runs before any stage is sized, one short read of the
diff, the risk table and the material, and names the change's class. Trivial,
no behaviour changes: one solo agent finds, runs, judges and writes. Simple, one
local change and its callers: one finder per bundle carrying every angle, one
judge, the writer, no reflector, no text pass. Normal: the word's shape.
Complex, concurrency, consensus, funds, permissions, a state machine, unknown
code: a second round by yield, one judge per candidate, the text pass. The word
caps the class, `quick` at simple and `deep` at complex. A round that finds
nothing runs no judge and no editor. The seven lines project at two to five
agents and a sixth of the tokens; the twelve hundred are unchanged. Reusable:
decide the shape from what the change is, with size one factor among several,
and let empty stages skip themselves.

## Three failures, with the cause

- **A shared spend counter.** The round's output ceiling read the harness
  counter, which is the whole turn's; a stopped run earlier in the turn had
  spent 530k on it, so the round opened at its floor and shipped 75
  candidates unverified. Fix: count from the round's own start.
- **Two rulers.** A review projected at $44 in the morning measured $69 in
  the evening. The planner's finder constant was a sixth of the measured one
  and its verifier constant three times too high; the errors cancelled in the
  total. Fix: the planner carries measured constants, and a projection is
  labelled as one wherever it sits beside a measurement.
- **The overview written last.** The rule says the overview agent, which
  explains the subject to a reader who knows nothing, is dispatched first so
  the human reads while the finders run. A launch without it produced the
  overview an hour later. Fix: the runner starts the agent itself beside the
  finders when the launch did not.

## The words, on measured constants

| Word | Shape | PR 6187, 1,200 lines | PR gno-fixes 104, 7 lines |
| --- | --- | --- | --- |
| `quick review` | the triage capped at simple: one finder per bundle on the Warning-finding angles, each running its own Warning checks, judges in short parallel batches, the writer | 7 agents, ~260k output, about 28 minutes | 5 agents, ~80k, about 17 minutes |
| `review` | the triage's class; at normal, one finder per bundle per angle, the reflector, judges by six and by twelve, the writer, the text pass | 24 agents, ~1.1M, ~61M cache, about $73 | 7 agents, ~113k, about 25 minutes |
| `deep review` | complex: a second round on every bundle that yielded, one judge per candidate, the text pass | 57 agents, ~2.2M, about $146 if every bundle yields | |

Each word has an output ceiling; past it no judge is dispatched and the writer
still runs. `review` on the large change costs more than the sixty-dollar round
because it runs thirteen finders at xhigh where the old round ran six, chosen
for recall; every number in this table is a projection until the first judged
round measures it.

## Reusable, in one list

- Measure agents, turns and context per stage; cache read is the bill.
- Hand each agent its slice as a file.
- Every step a program can do, a program does, with a test.
- Keep the thinking; cut the turns.
- Test an effort change on known bugs.
- One finder run is a sample; overlap between runs measures coverage.
- Re-measure every stage against the finders you have now.
- One question, one agent; a comment never settles a drop.
- A budget counts from the round's start; projections are labelled.
- The overview goes to the human first.

## Next

The blind review of the token registry is still the acceptance test, now of
the judged shape: seven Warnings, none wrong, under 40M of cache read. Then the
opening context cut, since half of every finder's cache read is the system
prompt and the rule bundle, and outcome tables from posted rounds, the only
number a tier or a cap is finally measured against.

Sources: the review skill and its runner in this repository; the rounds under
the gno workspace's `reviews/pr/6xxx/6187-*`; Cloudflare, *Build your own
vulnerability harness*, 2026; the knowledge files beside this one.
