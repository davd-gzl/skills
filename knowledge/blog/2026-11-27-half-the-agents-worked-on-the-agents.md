# Half the agents were working on the agents

Context: one engineer, a workspace of agents that review and fix pull requests,
and a rule corpus that tells every agent how to work. One day felt slow and
noisy, so the agents' own transcripts were read back as a retro: what each
session cost, what it changed, and who it changed it for. The finding was not
a bad model or a bad prompt. It was the operator's habits, and the rules those
habits had piled up. What follows is each mistake, the measurement behind it,
what changed, and what another team running agents can reuse.

## 1. The workflow had become the product

About seven commits in ten that day changed the workflow itself: rules, the
review runner, its sandbox, worktree plumbing. About one in four shipped
project work, and about half the subagent spend went to the workflow. Every
friction met during real work became a rule edit in that turn, because a rule
said so.

Changed: a workflow problem is fixed in the turn only when it blocks the task
or the operator asks for it; anything else becomes one line in `TODO.md` and
the task carries on. Reusable: count commits by what they touch. When the
tooling outgrows the work, freeze the tooling and measure output instead.

## 2. A rule that cannot bend belongs in a hook

The corrections log split mistakes into classes and dated each against the
rule meant to prevent it. In every class checked, long drafts, false claims,
the wrong register, an ignored skill rule, a publish without its word and an AI
marker in a commit, every correction came after the rule existed. The prose
stopped none of them. Of those classes, the publish without its word and the
marker are the two a hook now refuses, which a script can do and a sentence
cannot.

Claude Code's [best practices](https://code.claude.com/docs/en/best-practices)
draw the same line between instructions the model reads and settings the
harness enforces, and send a rule with no exceptions to a hook or a deny rule.
Reusable: before writing a rule for a repeated mistake, ask whether a script
can refuse it. If it can, write the script and delete the prose.

## 3. The rulebook was past what a model follows

Every session opened on the same imports and hooks, well over eighty rules
before the first prompt, and every subagent carried the imported part on every
call. A [knowledge file](../rules-decay-past-eighty.md) in this repository
already said adherence collapses past about eighty simultaneous rules. The
public half of the corpus grew from about 25,500 words to about 60,900 in
ninety days.

[Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
names the failure: hardcoding complex, brittle logic into the prompt, which
raises fragility and maintenance cost. The corpus had clauses saying which
phrase of which list another rule outranks. Changed: a deletion pass toward
one short always-loaded file. Reusable: keep what loads every time to what the
agent cannot work out from the code, and read the rest on demand.

## 4. Review loops did not converge because the rules were coupled

Every rule change ran a review loop that repeated until a fresh reviewer found
only minor defects. Loops of four to eight passes were normal. The cause showed
on the change that fixed it: two fresh reviews of a small edit each found three
real contradictions, mostly in sentences the edit never touched. The reviewers
were fine; the rules were tangled, so any edit broke a sentence two files away.

Changed: one fresh review per rule change, two for a change to what an agent
may push, post or delete, and what the last pass finds is fixed and lands. The
cap rests first on these loops. [GIER](https://arxiv.org/abs/2509.00325) points
the same way: across three reasoning tasks, its first three rounds of
self-critique carried most of the gain, and later ones changed little or
reversed it. It ran on GPT-4.1, GPT-4o Mini, Gemini 1.5 Pro and Llama 3.3,
older than the models doing this work, and on reasoning answers rather than
rule review, so it supports the cap without proving it here. Reusable: cap the
loop, read a loop that keeps finding real defects as a coupling problem, and
weigh a paper by the models and setup it measured: one that agrees with your
own data supports it, and one that does not is a question to measure, not a
rule.

## 5. One correction became one rule

An agent corrected once wrote a rule about it, in the same turn, reviewed only
by other agents. Claude Code's best practices set the bar at a mistake corrected
twice. Changed: the agent proposes a rule as a `TODO.md` line, and the operator
writes it after the second correction. Reusable: a rule is a cost every session
pays, so it should earn its place with a pattern, not one incident.

## 6. Long sessions with many topics

The longest sessions ran nine to fourteen hours across unrelated topics. Their
mean context per call was four to five times their opening size, each was
compacted several times, and decisions were lost across the compactions: a
session went back to a sandbox approach after the operator had chosen another.
The same page recommends clearing context between unrelated tasks.

Changed: one master session stays as a dispatcher for small problems. Each task
goes to its own session or subagent and comes back as a summary, so the
master's context stays near its opening size. Every other session takes one
task and ends when its pull request is pushed. Reusable: the session that holds
the plan should not also hold the tool output.

## 7. The operator became the scheduler

Running many sessions at once made the operator the bottleneck. About half of
each long session's wall time was spent waiting for a reply, and about one
typed prompt in twenty asked whether things were going well or corrected drift.
Changed: three working sessions at most, beside the dispatcher. Reusable:
parallel agents pay off until the human is the queue; measure the waiting.

## 8. The typed words stayed, and stopped loading

The operator types short words, `p` to push, `post`, `fix`, `review`. The
median prompt over a month was six words, so the words are worth keeping: they
are the operator's speed. Their cost was that all of their definitions, about
1,500 words, loaded into every session. Changed: a word counts only at the
start of a message, each separated by whitespace, so `p d` pushes and deletes
while `pd` and `please p` do nothing. The always-loaded file now holds that
rule in 84 words, and a prompt hook puts in context only the rows of the words
a message opens with. The same parser feeds the push gate, so the gate and the
definitions can no longer disagree. Reusable: a vocabulary the operator types
is worth keeping; load each word when it is typed.

## The mistakes, in one list

- Letting the agent rewrite its own rules after a single correction.
- Treating every workflow friction as urgent.
- Writing prose rules for mistakes a script could refuse.
- Running review loops until a reviewer found nothing.
- Keeping one session open for a day across unrelated work.
- Running more sessions than one person can steer.
- Measuring the cost of every agent and never the value of its output.

## Reusable, in one list

- Count commits and spend by what they touch: product or tooling.
- Fix a tooling problem now only when it blocks the task.
- A rule that cannot bend is a hook; delete its prose.
- Keep the always-loaded rules short and load the rest on demand.
- One review pass, two at most, and treat non-convergence as coupling.
- Weigh a paper by the models and setup it measured, beside your own data.
- A rule earns its place on the second correction.
- One task per session; a dispatcher session keeps only summaries.
- Load a typed word's definition when it is typed.

## Next

A two-week freeze on the workflow: no rule, runner or script change unless it
blocks shipping. What gets measured instead is pull requests merged, findings a
maintainer confirmed, and the cost per merged pull request. Then the deletion
pass, which has to make the always-loaded rules fit one short file.

Sources: the transcripts and commits of the day; the corrections log; Claude
Code's [best practices](https://code.claude.com/docs/en/best-practices);
Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
and [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents);
Armin Ronacher, [Agentic Coding Recommendations](https://lucumr.pocoo.org/2025/6/12/agentic-coding/);
[GIER](https://arxiv.org/abs/2509.00325); the knowledge files beside this one.
