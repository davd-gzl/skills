# Skills

My skills: the instruction sets my agents load before working on my projects.

## The concept

Rules matter at the moment an agent writes, and a rule it read an hour ago is
a rule it samples. So every artifact has one skill, the skill is put in context
whole before the first line of the artifact, and a command records that it was.
The hooks do the putting; the gate warns on anything written unread.

Three principles outrank every rule. Build what the task asks for and nothing
speculative. Read the rule before writing the artifact. Measure, never assume:
a convention, a capability and a count come from a command run this session,
never from memory or from a file that recorded them once.

Nothing reaches anyone without my word, typed in the current turn: `post`,
`push`, `merge`. `go`, `ok` and `yes` authorise nothing, and every draft is shown
before it goes. A claim carries the run that proves it. A posted comment says
the problem, its stake and the line it sits on, and stops, so a maintainer who
did not ask for it reads it once; the depth lives in the review file. Replies
to me are clipped, measured, rewritten when they drift, and end on an account
of everything the turn did.

The corpus shrinks on purpose. A rule has one home; it leaves when a script
enforces it or a broader rule covers it; a wording in doubt is measured against
its alternatives before it lands; the lint prints what each file costs. A
workspace mounts this repository as a `skills/` submodule on `main`, live on
the next sync with no bump, and keeps one measured delta per repository in
`projects/<repo>/AGENTS.md`, which wins where the two disagree.

## The words

What I type, and what each word starts, from [`shortcuts.md`](shortcuts.md).

| Word | What it starts |
| --- | --- |
| `review <target>` | one review round: the file, the overview, the comment draft, pushed, nothing posted |
| `deep review <target>` | the same round with lens agents on one target |
| `review all` | every open target not yet reviewed, the scope written down first |
| `fix <issue or finding>` | a change on the fork: spec, plan, worktree, fix, CI; nothing pushed |
| `try <pr> on <repo>` | the project booted locally, ready to click through |
| `video` | the clip, only once the finding's text is frozen |
| `stop` | the stack and the worktree torn down |
| `report [date]` | the period's status report |
| `post` | the shown draft goes to its target; `post as an AI` adds the marker; `upload` sends media |
| `push` | the whole git flow, every commit and push the work needs, once |
| `merge`, `close`, `delete` | that one action on the named target |
| `make this review public` | the round to the public artifact repo, links repointed |
| `path` | the worktree the work sits in, its path alone |
| "a comment" | the `comment_<model>.md` draft and the text for the target, never an explanation |
| `TLDR` | the answer in one line, and the word it waits on |
| `continue` | the local work resumed, dead agents re-dispatched first; nothing published |
| `+` or `-` on a prompt | that reply lifted to explanation, or cut to the shortest true answer |
| `go`, `ok`, `yes`, `sure`, anything else | local work only, never a publish |

## How I work

Everything starts with a review, on a PR, a branch, or a red CI.
[`review.md`](review.md) drives it:

1. **Fetch and understand.** Sync the checkout, work from a worktree, pull the
   diff, read every comment and past review, then read every changed file in
   full and map its callers. A branch from outside the project gets a static
   danger pass before it is fetched.
2. **Re-review gate.** When a prior round exists, compare patch-ids to tell new
   code from a branch that just moved on its base. A base-only move copies the
   old round forward; nobody re-reviews unchanged code.
3. **Reproduce.** Run the project's own CI commands locally. Every failure is
   re-run on the merge base before the diff gets the blame.
4. **Review the diff.** The hunt itself, under one discipline: a behavior claim
   ships with the run that proves it, and a repro that also fires on the merge
   base is not a finding.
5. **Refactor pass.** Every added block is rewritten shorter, run against the
   project's own tests, and shipped as a one-click suggestion with both line
   counts.
6. **Write the tests.** A finding whose fix is a test ships the test itself,
   paste-ready, not a description of one.
7. **Overview and review file.** `overview.md` for the reader who knows nothing
   about the subject, then the record: verdict, findings graded Critical to
   Suggestion, repros, every claim linked to the reviewed line.
8. **Comment draft.** One anchored comment per finding, its final check, three
   QA agents over every edit, pruned by hand before anything ships.
9. **Style pass.** The closing Pass of [`writing-style.md`](writing-style.md),
   run against the file and not from memory. Never skipped.
10. **Commit and push.** The record lands in my workspace, nothing else moves.
11. **Hand over.** I read the draft and decide.

## The files

| File | Fires when | Produces |
| --- | --- | --- |
| [`review.md`](review.md) | a pull request, a branch or a repository-level failure is reviewed | the review round |
| [`review-modes.md`](review-modes.md) | a run covers many targets, goes deep with several lenses on one, or the reviewer authored the target | the deltas of that mode |
| [`review-output.md`](review-output.md) | the review file is written | its metadata block and every section in order |
| [`review-comment.md`](review-comment.md) | `comment_<model>.md` is drafted, regenerated or posted | the Body, the inline-comment shape, the final check, the posting gate |
| [`issue.md`](issue.md) | a fix needs an upstream issue nobody has filed | `issue.md`, the problem and never the remedy |
| [`change.md`](change.md) | an issue or a finding goes to a pull request | `spec.md` and `plan.md` with their numbered open calls, the worktree, the fix, the local CI run, the pull request on my fork |
| [`pr-body.md`](pr-body.md) | a change is proposed, before the pull request opens | the title and body, in one of four shapes, looping until a full pass changes nothing |
| [`pr-body/docs.md`](pr-body/docs.md) | the change is documentation pages | no headers, the fact the pages had wrong first, a worked example |
| [`pr-body/one-concern.md`](pr-body/one-concern.md) | one concern, which is every bug fix | `## Problem` and `## Fix`, four short paragraphs, a worked example |
| [`pr-body/several-changes.md`](pr-body/several-changes.md) | several independent changes share one pull request | one `###` section per change, each readable alone, a worked example |
| [`pr-body/surface.md`](pr-body/surface.md) | one change with a surface someone sees | `## Problem` with the shot, `## Design` with one `###` per decision, a worked example |
| [`try.md`](try.md) | a project is booted at a pull request, a branch or its default branch | a URL, a login, the click path; the clip once the claim is settled |
| [`report.md`](report.md) | a periodic status report over a set of repositories | the report, generated only after I have edited its context file |
| [`git.md`](git.md) | a turn will commit, push, sync a checkout, or touch a submodule or worktree | the identity every commit takes, where a push goes, the commands that report success and move nothing |
| [`writing-style.md`](writing-style.md) | any visible prose, in any project | the rules every other skill defers to, the closing Pass, the chat register, the posted-comment shape |
| [`shortcuts.md`](shortcuts.md) | every reply, in any workspace | the words, the shape of a reply, the account of what a turn did, the closing block |
| [`authoring.md`](authoring.md) | a rule is added, edited or removed | where it lives, the shape it takes, what it displaces |
| [`archive/`](archive/) | nothing loads it | snapshots of a skill before a change that altered its voice, and the advisory shape for a disclosure |
| [`TODO.md`](TODO.md) | skill work I own but have not started | one line per item, newest last |

## The chat register

cvm is the register every chat reply takes, defined in the Short form section
of [`writing-style.md`](writing-style.md). The rules live there and are not
restated here.

[`tests/chat-register/`](tests/chat-register/) is the harness that chose the
wording: candidate wordings against no rule and against the caveman plugin on
that plugin's own benchmark prompts, articles, filler, hedges and words per
sentence counted with code excluded, and a blind judge ranking every answer on
single-pass readability; [`results.md`](tests/chat-register/results.md) is the
run.

[`scripts/reply-check.py`](scripts/reply-check.py) is what keeps it: run as the
harness's stop hook, it reads the turn's final reply off the transcript, drops
fenced code, inline code, blockquotes, table rows, link targets and anything
between two `---` rules, since a quoted draft stays as written, and measures
what is left. Over 5 articles per hundred words, over 12 words per sentence,
any hedge or pleasantry, or a closing block with no `Did:` account above it,
and the numbers come back with the register for one rewrite; a reply under 30
words of prose, or one answering a `+` prompt, is not measured.

```bash
./skills/scripts/reply-check.py <file>                          # the numbers for a text file
./skills/scripts/reply-check.py --scan <transcript>.jsonl... --since 2026-09-06   # replies measured and drifted, per session
```

## The read gate

[`scripts/skill-gate.py`](scripts/skill-gate.py) records every read made
through [`scripts/skill`](scripts/skill), `./scripts/skill review` for a skill,
`./scripts/skill pr-body/docs` for a shape, `./scripts/skill meet` for a
project's delta. It puts the skills a write still lacks into the context with a
warning and lets the write through, and puts the rules in the context itself:
the four every session needs as it opens, `writing-style`, `shortcuts`, `git`
and the workspace layout, the task's and the repository's on the prompt that
names them, everything again after a compaction. A read holds while the file's
hash matches and the session is the same; a stale read prints only the diff
since it was made.

[`scripts/git-hooks/`](scripts/git-hooks/) holds the commit, merge-commit and
push hooks, which warn on a mapped artifact whose skill was not read, whatever
made the commit. [`scripts/tests/`](scripts/tests/) holds the tests of the gate
and of the register check.

```bash
git config core.hooksPath skills/scripts/git-hooks
git -C skills config core.hooksPath scripts/git-hooks
python3 -m unittest discover -s skills/scripts/tests
```

The harness adapter lives in the workspace's own settings file, never here:
its before-write hook on `Write|Edit|MultiEdit|Bash` calls
`skill-gate.py hook-claude`, its session-start hook `session-start`, its prompt
hook `prompt`, and its stop hook `reply-check.py`. Another harness wires its
before-write hook to `skill-gate.py check <path>` and exports its session id as
`CLAUDE_CODE_SESSION_ID`; the git hooks hold without any harness.

## The lint

[`lint.py`](lint.py) warns and never blocks: a rule that tells the reader to
stop measuring, a date or a sha inside a rule, an em-dash or a parenthetical in
prose, a capability asserted without the command that reads it, a pointer at a
file or a section that does not exist, one sentence living in two files, and a
health table per file with its word count, words per rule, negation density and
the share of bullets in bold.

```bash
./skills/lint.py AGENTS.md skills/*.md skills/pr-body/*.md projects/*/AGENTS.md
```
