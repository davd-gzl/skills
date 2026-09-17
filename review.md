---
name: review
description: Use whenever a pull request, a branch, a working diff or a red CI is to be reviewed, in any project, and whenever the user says `review <target>`, `quick review`, `deep review`, `plan review`, `review all`, pastes a pull request URL alone, or asks what to think of a change or why CI is red. One round, finders per angle, a verifier per candidate, a reflector, a writer, a text pass, producing overview.md, comment_<model>.md per skills/review-comment.md, claims.md and links.md. Several targets at once and a target the reviewer wrote are skills/review-modes.md.
argument-hint: <repo>#<pr-number> | <url> | <repo> <subject>
---

# Review

**Input:** `$ARGUMENTS`: a PR number or URL, a repo name plus a subject, or several of these. Process each target independently.

One word per thing, everywhere in a round: a *candidate* is what a finder
returns; a *finding* is a candidate a verifier kept; a *claim* is a sentence
the draft asserts; a *round* is one run over one head; a *pass* is one agent's
sweep; the *draft* is `comment_<model>.md`; a *verdict* is CONFIRMED,
PLAUSIBLE, REFUTED or UNVERIFIED.

Write all visible prose per `skills/writing-style.md`, read when the writer
stage opens. In every artifact, verdict first, then narrative, then findings;
every reference clickable, every file readable without the chat, and the one
number or word that carries the decision in bold.

Sections, and the moment each is read: *Workflow*, the parent, every round;
*Launch*, the parent at step 4; *Triage*, the triage agent; *Finders*, *Reflector*, *Verifiers*,
*Writer* and *Text pass*, the stage of that name; *The critical pass*, a vulnerability
fix; *Subjects*, a branch or a red CI; *Modes*, several targets, an authored
target, `plan review`; *Fetch & understand*, the parent at step 1; *Re-review
rounds*, a prior round exists; *Reproduce the failure*, the parent at step 3
and every verifier; *Review the diff*, the finders and the reflector; *Write
tests for test-shaped findings*, the finders and the judges; *Overview*, the overview
agent; *Links & citations*, the writer; *Repro rules*, the verifiers and the
writer; *Output*, the writer; *Calibration*, every stage; *Rules*, the parent
at the close; *GitHub review draft*, the writer, through
`skills/review-comment.md`.

## Workflow

One shape for every target, whatever its size: the parent prepares, a workflow
finds, verifies, criticises and writes, the parent checks and ships. Run from
the workspace root; multi-target runs wrap this via *Parallel dispatch* in
`skills/review-modes.md`.

The word sets the shape, and the word is how well the user knows the code:

| Word | For | Shape |
| --- | --- | --- |
| `quick review` | the overview of what a change is worth, the fewest tokens and the shortest clock | one finder per bundle carrying the angles that find Warnings, lines, reach, removed and the catalog, the Warning cap whole and the Nit cap 3, each finder running its own Warning checks, no reflector, judges by three at 12 calls and reads by eight, the writer, no text pass, a 500k ceiling |
| `review` | any change | one finder per bundle per angle with material, each running its own Warning checks, the reflector, judges by six over the run-shaped candidates and by twelve over the reads, the writer, the text pass, a 1M ceiling |
| `deep review` | code that is complex or unknown | every finder, a second round on every bundle that yielded a confirmed Warning or is hot, the Warning cap 16 and the Nit cap 8, one judge per run-shaped candidate at 30 calls, reads by six, the writer, the text pass, a 2.5M ceiling |

1. Prepare, per *Fetch & understand*, and dispatch the overview agent the moment the head worktree exists.
2. Run the *Re-review rounds* gate when a prior round exists.
3. *Reproduce the failure*: each suite once per tree state, the project's tool built once from the head worktree, named in `args.prebuilt`.
4. Print the plan and launch, per *Launch*; the triage names the class first, and the stages read *Finders*, *Reflector*, *Verifiers*, *Writer* and *Text pass*.
5. Run the *Final check* of `skills/review-comment.md`, then the `skills/writing-style.md` Pass over `overview.md` and the draft, `./scripts/prose-check.py <file>` first; re-run it after any later edit to that prose, an edit made in answer to a question included, and state which passes ran. Where the target fixes a reported vulnerability, *The critical pass* in `skills/review.md` runs here.
6. One commit and one push covering everything, pre-authorized per *Rules*.
7. Retro, per *Retro*.
8. Hand over, per *Handover*.

### Launch

What the parent hands the runner, and what every stage gets from it.

- `./scripts/review-setup.sh <head worktree> <base worktree> <scratch> --repo <owner/name> --target <text> --round-dir <dir> --catalog <file> --delta <project review.md> --prebuilt <tool>` does the fixed part of the launch in one command: the blanked copy of the head, the risk table, the bundles with their diffs, the rule files per stage, the diff and its material, and `args.json` for the workflow; the parent adds the threads or the blind flag and the notes. What it wraps, for a launch by hand:
- Print the plan first: `./scripts/review-plan.py --rules-out <scratch>/rules`, with `--preset` for `quick review` or `deep review`, and `--extra <stage>=<path>#<Heading>` for each section of the project delta a stage needs. Paste its table and projection in the reply that launches the run, so what is about to run and cost is on screen before it does.
- Then call the Workflow tool: `scripts/workflows/review-pipeline.js` as `scriptPath`, the prepared values as `args`, the preset as `args.preset`, the rules directory as `args.rules_dir`. The `review` word is the opt-in the harness's gate asks for, per *Consent* in the workspace `AGENTS.md`, and this sentence is the skill instruction it accepts.
- `args.risk_json` is what `round risk --json` wrote and `args.blob_url` the head repository's blob base at the sha, `https://github.com/<owner>/<repo>/blob/<sha>`: `round assemble` puts the tier on every row and the `[gh]` link on every header from them.
- `args.bundles` is what `round dispatch` wrote, and its table goes in the launch reply beside the plan's: the finder count is read off it, one per bundle per angle with material, or one carrying every angle for a bundle under the floor.
- A preset moves knobs, the Warning cap never among them. `quick` runs one finder per bundle on the Warning-finding angles, judges in short parallel batches and no reflector, and drops the text pass, so a candidate past a budget arrives as a question with its check named, the user runs it and flips the section to posted or `SKIP`, and step 5 is the only pass over the text. Every word carries an output ceiling in the config, `budget_total`, past which no verifier is dispatched; `+<n>` on the launch word overrides it.
- Every stage carries a tool-call budget from the config and returns what it has when it runs out: a call re-reads everything the agent opened on and has read since, so a stage's cache cost is its calls times its context, `./scripts/review-retro.py` printing both per stage.
- A round launched with a token target, `+2M` on the word, stops dispatching verifiers when the budget nears its floor; the candidates left unrun ship PLAUSIBLE with their check named, and the writer still runs.
- Each stage reads only the rule sections its artifact needs, the set per stage held beside the stage's model in `scripts/workflows/review-pipeline.json` and written out by the plan as one file per stage, since an agent told `path#Heading` reads the file whole. The parent never picks the list: one chosen per round left the suite rule of *Reproduce the failure* out of every verifier's once.
- The two drafting rules, `skills/review-comment.md` and `skills/writing-style.md`, are read when the writer stage opens, by the agent or the parent running it, never at the prompt: no stage before the writer drafts prose, and a rule read at the prompt sits in the parent's context through every finder and verifier call.
- The verify stage is the claim gate; no second gate runs.
- Without the runner, a harness that may dispatch agents dispatches the same stages as agents from the parent, same prompts, each returning its result as data and never a transcript; one that may run neither runs them serially in the parent. The round note names which of the three ran, what ruled out the others, and the parent's context at handover, read from the transcript's last `usage` line.

### Triage

One short agent before any stage is sized, reading the diff, the risk table
and the material, and naming the change's class; the class sets the shape and
the word caps it. Size is one factor and never the trigger.

| Class | The change | The round |
| --- | --- | --- |
| trivial | no behaviour changes: a doc, a comment, a rename, a version bump, a test-only edit that adds no case | one solo agent finds, runs what it bands Warning, judges and writes; `solo.agents` 2 puts a fresh judge and writer behind a finder |
| simple | one local behaviour change whose blast radius is one function and its direct callers | one finder per bundle carrying every angle, one judge batch, the writer, no reflector, no text pass |
| normal | a behaviour change with more than one reach, a new invariant, a guard removed, a test that must turn red | the word's shape as configured |
| complex | **one reading does not hold it**: the mechanism is new here, or two of them interact, or the reader cannot say from the diff alone what the code now does. The subjects that usually fail that test, and never pass it on their own: concurrency, consensus, gas or allocation accounting, funds, permissions or caller identity, cryptography, a state machine, a migration, a hot file with a removed guard | a second round by yield, one judge per run-shaped candidate, the text pass |

- Unsure between two classes takes the higher, once the reading has been tried.
- Name what a second reading buys before naming a class, since a subject on the complex row is not the trigger. Nothing to name means normal.
- `quick` caps the class at simple; `deep` skips the triage and takes complex; `args.shape` names a class outright; a round with topics, the critical pass, is never triaged.
- A round that finds nothing runs no judge, no reflector and no text pass: the writer ships the header, the verdict and one true sentence, and `claims.md` the empty table.

### Finders

One finder per bundle per angle the bundle has material for, the bundles from
`round dispatch`; a bundle under the floor gets one finder carrying every angle it
has, so the count follows the diff. Under `deep` every bundle's angles run twice
and a hot bundle's a third time, on independent contexts, merged per line like any
two finders. Every bundle is read once whatever its tier.

A finder returns candidates as data, never prose. One, filled:

```json
{"file": "pkg/store/cache.go", "line": 88, "angle": "reach",
 "summary": "a zero TTL never expires an entry",
 "failure_scenario": "Set(key, v, 0) stores with expiry 0; Get compares now > expiry, which is false forever, so the entry outlives every restart of the config",
 "verify_by": "go test ./pkg/store -run TestTTL with a 0 TTL case: expect eviction, observe none",
 "band": "Warning", "checked": true}
```

- Read the diff written out at `args.diff_file`, the head worktree and the catalog; run nothing that writes. Reads of at most 500 lines and searches of at most 100 hits: a call re-reads the whole context, so a wide read costs every later turn.
- Read the code before the description, since a description calling something safe lowers what a reader finds. Five angles read the copy of head with comment lines blanked and the blanked twin of the diff; the claims angle reads the description and the comments first, its subject; the refactor angle reads head.
- Run the read-shaped half of your own `verify_by` before returning a candidate, the grep, the count, the file read. For a candidate banded Critical or Warning, and for a rewrite, run the check itself in your own scratch worktree, `git -C <head worktree> worktree add --detach <scratch>/find-<job> <sha>`, removed at the end; write the artifact under `tests/<job>-<slug>.<ext>` per *Write tests for test-shaped findings*, and return the candidate with `run` true, its evidence, the key output quoted, and `repro_path`. A check the run refutes goes under `dropped` with the output as its settling line; one the budget did not reach returns with `run` false. The merge-base comparison belongs to the judge. A Nit, a Suggestion and a Missing test are read, never run.
- Work the bands in order: the checks of every Critical, Warning and Missing test candidate before any Nit's or Suggestion's, so a budget that runs out leaves a Nit unchecked and never a Warning. Mark each candidate `checked` or not; one you did not reach goes back with its check named, never dropped.
- Work the files in the risk table's order, hot first, then warm, then cold: a budget that runs out leaves a cold file unread and never a hot one, and every file is read once whatever its tier.
- Drop only what the read settles beyond doubt, and return every dropped one under `dropped` with the command and the line that settled it: a claim killed with no row is one nobody can reopen. Unsure is not settled; it goes forward.
- Write the object you return to `<round dir>/candidates/find-<job>.json` before returning.
- Return at most `cap_high` candidates banded Critical, Warning or Missing test and at most `cap` banded Nit or Suggestion, each list ordered by how likely a verifier confirms it, since everything past a cap is dropped unread; a Nit never takes a Warning's slot.
- Band on what a user loses when the line runs, never on the size of the fix: a read surface that aborts on ordinary input, a write that cannot be undone and a value another party can move are Warnings whatever their patch size; Nit is polish a maintainer would not block on.
- A candidate whose only fix is a comment's or a doc's wording is never returned: it ships `SKIP` per *Calibration* and costs a verifier; the code a comment misdescribes is the candidate where the code is wrong.

| Angle | Walks | Runs when |
| --- | --- | --- |
| lines | every hunk and its enclosing function, for the input, state, timing or caller that makes a line wrong | always |
| removed | every deleted or rewritten line, the invariant it enforced, and the siblings the diff missed, swept by shape and never by name | the diff deletes a line |
| claims | every claim the diff writes about itself, a godoc, a comment, a test header, the description, a decision record, each returned with the check that settles it, a doc example with its run from outside the package | the diff carries a comment, a doc or a decision record |
| tests | every test the diff adds or changes, with the mutation that must turn it red | the diff carries a test file |
| reach | callers and callees of every changed function, and the extremes through every path the diff makes reachable for the first time | always |
| refactor | every added block rewritten shorter and run, and the depth of each fix | the diff adds a block of twenty lines |
| catalog | every class of the project's invariant catalog against the diff | the project has a catalog |

`./scripts/review-plan.py --diff <head worktree> <base> <head>` prints which angles run and writes the measurement the workflow reads.

### Reflector

One agent, after every finder has returned and before any verifier is paid for:
one read over every candidate against the diff.

A drop, filled:

```json
{"index": 14, "settled_by": "cache.go:31 `if ttl <= 0 { ttl = defaultTTL }`: the zero the candidate says reaches Set is rewritten two lines above the call"}
```

- Drop a candidate only when a line of code in the diff or at the head, quoted, contradicts it outright; a comment, a doc line or a description never settles a drop, being the code's claim about itself: the guard it calls missing sits three lines up, the value it calls unbounded is clamped at the call site, the function it names was deleted.
- Unsure keeps it. The verifiers do the killing a read cannot, and a Warning dropped on a guess is the round's worst outcome.
- Under `reflector.min_candidates`, six, the stage is skipped: a read over three candidates is not worth an agent.
- Every drop is a row of `claims.md`, the line quoted, so a later round reads what was cleared and why: write `<round dir>/candidates/reflector.json` before returning, `dropped` holding each drop with its candidate's file, line, angle and summary and your `settled_by`, and `candidates` holding the missing list.
- Then ask what is missing, the round's one completeness question: an angle that came back thin, a class of the catalog no candidate touches, a changed test not re-added; return each as a candidate with the check that settles it, never a line already listed.

### Verifiers

The judges. The finder ran the check of every Critical and Warning it
returned and wrote the artifact; a judge takes a batch, reruns the artifact,
reads the code and answers, and files no finding of its own. Routing by band:

| Candidate | Who | Where |
| --- | --- | --- |
| a Critical, a Warning, a rewrite | one judge per `verifier.batch` run-shaped candidates of one bundle, six by default, one under `deep`; the artifact rerun from the file, the code read, the same check at the merge base where the claim is causal | one scratch worktree per judge, `git -C <head worktree> worktree add --detach <scratch>/judge-<n> <sha>`, the tree restored between candidates, removed at the end |
| a Missing test, a Suggestion, a Nit | one judge per `verifier.read_batch`, twelve, under `verifier.read_tools` calls; a read settles it and never a mutation, a Missing test being an absence a grep settles | the head worktree, untouched |

A verdict, filled:

```json
{"state": "REFUTED", "band": "Warning", "file": "pkg/store/cache.go", "line": 88,
 "tldr": "a zero TTL is rewritten to the default before Set stores it",
 "details": "New() clamps ttl <= 0 to defaultTTL at cache.go:31, so Set never sees 0.",
 "evidence": "go test ./pkg/store -run TestTTL -v: the 0 case evicts after 5m, PASS",
 "repro_path": "", "base_behaves_the_same": true,
 "refuted_by": "cache.go:31 if ttl <= 0 { ttl = defaultTTL }"}
```

- CONFIRMED needs the exact lines or a concrete triggering input in the judge's own words, never the finder's evidence alone: a finder grades itself when the judge takes its word. Rerun the artifact from the file and read its output; where none exists or it does not reproduce the claim, build the smallest check that would.
- When the claim is that the diff causes the behaviour, run the same check at the merge base and report both; enumerate the case space first, both, first only, second only, neither.
- State exactly one of CONFIRMED, the run or the read reproduced it with the key output or the lines quoted; PLAUSIBLE, the mechanism is real and no reproducer exists in this environment, with what would confirm it; REFUTED, the run or the read shows it guarded, covered or unreachable, with the proving line quoted. A PLAUSIBLE Nit or Suggestion ships `SKIP`.
- Give each candidate its own verdict; no verdict borrows from another's, and a batch that confirms every item has been read against that habit.
- Band per *Calibration*; severity measures whether the defect is real, not how big. A refactor candidate whose rewrite passes the tests is a Suggestion carrying both line counts.
- An artifact the judge builds itself goes under `tests/judge-<candidate>-<slug>.<ext>` per *Write tests for test-shaped findings*; the finder's keeps its name.
- Report what the user loses, never the artifact that causes it.
- Write the verdicts you return to `<round dir>/verdicts/<agent>.json`, each carrying its candidate's index, angle and check, so `round assemble` joins it to its row.
- The judge runs at the finder's tier today; the upgrade, when the plan allows it, is another model as capable or more on `verifier.model`, since a family confirms its own reading and the adversary is worth most when its weights are not the finder's. Never a smaller tier.
- An earlier round's command for the same line arrives with the candidate, never its verdict; re-run it before building your own.
- Every judge carries a tool-call budget and returns PLAUSIBLE with the check still to run when it runs out, since the slowest judge holds every stage behind it. The project's tool sits prebuilt on the PATH, so none builds one and none runs `go build`, `make` or `go run`, since a named test compiles what it needs; run named tests, never a module sweep.
- Over six rounds the fresh verifiers this stage replaced refuted none of 52 Warnings and a tenth of the lower bands; the three Warnings ever refuted were a lone agent's, refuted by its own runs, which is why the finder runs and the judge judges.

### Writer

One agent, or several past `writer.batch` kept findings, drafting sections by
file and one merge pass assembling the whole.

- `overview.md` is never the writer's: the parent's overview agent wrote it at step 1, or the runner's, started beside the finders when the launch came without `overview_exists`; the writer links it.
- `comment_<model>.md` per `skills/review-comment.md`, its header opening on the `Verdict:` line, every finding a section, posted or `SKIP`. A PLAUSIBLE Warning is a question; a PLAUSIBLE Nit or Suggestion ships `SKIP`, since a read that cannot settle it is no ground to post.
- `./scripts/round assemble <round dir> --repo <head worktree> --sha <sha> --risk <risk.json> --url <blob url base> --title <text> --shape <text>` first: it writes `claims.md` whole, the Candidates table from the verdicts as data, the rows the finders settled, the hit rate per tier and an empty Completeness section, and `findings.md`, one block per finding in posting order with `SKIP` in front of a PLAUSIBLE Nit or Suggestion. It exits 1 listing every anchor not at the head; such a row is settled by reading the code and moving the anchor, never by dropping the finding.
- `claims.md` per *Output*: the table is the tool's and stays as written; the writer replaces the Completeness placeholder with its answers.
- The draft's sections come from `findings.md`, never from the JSON under `candidates/` or `verdicts/`.
- `./scripts/round check <round dir>` last, before returning: it lists every em-dash, every visible question, every finding header without its link and every phrase that points at the page, into `check.md`; the writer clears the list, so the text pass reads the wording and not the mechanics.
- The `Round:` line names the shape: how many finders, whether a reflector ran, how many candidates, and that each was run from scratch by an agent that was not its finder, the Nits in their batches counted apart.

### Text pass

One agent, last, per the QA rule in `skills/review-comment.md`, over the
draft and the overview.
Under `text.min_findings`, four, the pass is skipped: `round check` and the writer's own read cover a draft that short.

1. Run `./scripts/round links <round dir> --repo <head worktree>` first: it writes `links.md`, one row per link with whether the file resolves at the pinned sha and the range fits, and exits 1 on a miss.
2. Read that table and add, per row, whether the landed lines carry the claim beside the link; none of it enters `claims.md`, which a reader opens for the findings.
3. Rewrite any line shorter or clearer without dropping fact, stake or fix, fix every anchor the table flags, and run the `skills/writing-style.md` Pass over both files.

### Retro

Before the handover, run `./scripts/review-retro.py <workflow-dir>` and write
`## Retro` at the end of `claims.md`, three parts from that table and the run's
notifications, never from memory:

- what failed: an agent that died, a cap hit, an escalation, an angle whose candidates were mostly refuted, minutes over the plan;
- what worked: an angle whose candidates held, a batch that verified clean;
- the hit rate per tier: confirmed rows over rows per tier, from the Tier column, beside the files per tier in the risk table; a tier whose rate is not above the next one's is a weight to revisit in `round risk`;
- one upgrade to the workflow with its estimate per *A change to the run's shape* in `skills/authoring.md`, written the same turn as a line of the workspace's `TODO.md`, where `upgrade skills` picks it up.

The handover repeats the retro in three lines.

### Handover

Name the cost first: agents, minutes and tokens per stage from the task
notifications. The draft and the overview go in the closing links every reply
ends on, per *The shape of a reply* in `skills/shortcuts.md`, never
mid-reply. Add a "Decisions needed" list, one line each, a borderline verdict
or a PLAUSIBLE worth a decision, and omit it when empty; never list an APPROVE
as needing confirmation. Post only on the literal word `post`. Acting on the
findings is `skills/change.md`; they stay here.

## The critical pass

**A round whose target fixes a reported vulnerability closes on one pass per
bound the fix claims to hold.** The fix's own description names the bounds.

- Each bound is an entry of `args.topics`, one finder each, under the `critical` preset of `scripts/workflows/review-pipeline.json`: no general angle, no text pass.
- The writer appends its verdicts to the round's `claims.md` under `## Critical pass <n>` rather than writing a round.
- Pass the round's own `prior_checks`, so no check runs twice, and print the cost first with `./scripts/review-plan.py --preset critical --topics <n>`.
- **Run another pass while the last one returned a candidate the verifiers banded above Nit.** Stop at two whatever the second returns, and name in the round note which bound is left standing on one pass.
- A bound the round already broke is a finding, never a topic: a pass attacks the bounds that survived.

## Subjects

The subject is a PR by default. Two others recur; they change only *Fetch & understand* and the anchors, the `file:line` a finding attaches to:

- **Branch or working diff**: no PR yet. Anchor findings to `file:line` at the branch head.
- **Repository-level failure**: red CI on the default branch, a failing gate, a broken release. The "diff" is the failing surface. Enumerate every failing condition from its authoritative source, attribute each to the code or config causing it, and separate what a PR can fix from what only a maintainer with project permissions can. `<slug>` names the failure, not a commit.

Both live in `projects/<repo>/reviews/<slug>/`.

## Modes

Two cases change part of this workflow: multi-target parallel dispatch, and a
target the reviewer authored. Both are in `skills/review-modes.md`, read when
the trigger fires.

A third is the user's briefing, `plan review <target>`: steps 1 to 3 run, then
the parent asks what it could not read, three to five questions in one reply,
the target's purpose, the invariants it must keep, where the user expects the
risk and what they know of the area. Each answer naming a place or a property
becomes a topic, `args.topics`, one finder each with that topic as its angle,
and the run launches on `go`.

## For each target

### Fetch & understand

What the parent prepares, each one line, each a value the runner takes:

- the checkout synced, per *Sync a checkout* in `skills/git.md`: `git remote -v`, fetch every remote, compare `git rev-list --left-right --count HEAD...<remote>/<branch>`; the canonical remote is often `upstream`;
- the head and merge-base worktrees, per the worktree rules below;
- a copy of head with comment lines blanked, `./scripts/blank-comments.py <head worktree> <scratch>/head-nocomments`, line numbers kept;
- the diff with its enclosing functions and its comment-blanked twin, `./scripts/review-plan.py --diff-out <scratch>/diff.md`, as `args.diff_file` and `args.diff_file_blank`, so no stage spends a call deriving what the parent holds;
- the changed files ranked, `./scripts/round risk <head worktree> <base> <head> --prior <slug dir> --out <scratch>/risk.md --json <scratch>/risk.json`: the table pasted in the launch reply and passed as `args.risk_file`, the JSON's `hot`, `warm` and `cold` lists as `args.risk`, so the finders read the hot files first and every `claims.md` row carries its tier;
- the diff cut into bundles, `./scripts/round dispatch <head worktree> <base> <head> --risk <scratch>/risk.json --diff-dir <scratch>/bundles --json <scratch>/bundles.json --out <scratch>/bundles.md`, with `--catalog 1` where the project has one: each bundle's diff with its enclosing functions and its blanked twin, the angles it has material for and the finders it earns, as `args.bundles`;
- what earlier rounds ran on each line, `./scripts/round prior <slug dir> --repo <head worktree> --sha <head sha> --json <scratch>/prior.json`, as `args.prior_checks`: the Check cell alone and never the verdict, which would anchor the one stage paid to decide for itself;
- the toolchain line every shell opens with;
- the free space on the scratch filesystem, `df -Pm <scratch> | awk 'NR==2{print $4}'`, as `args.free_mb`, since a per-candidate worktree runs to 150MB and the runner holds 16 agents at once;
- the round directory, the catalog, the prior rounds, and each stage's model, effort, rule sections and tool budget from `scripts/workflows/review-pipeline.json`;
- the overview agent, dispatched the moment the head worktree exists, one agent per *Overview*, so `overview.md` is committed, pushed and linked in the reply that launches the run; the workflow then gets `overview_exists`.

Reading the target:

- Never review from a dirty tree without saying so. Never write into the reviewed checkout outside a dedicated fix branch.
- **Review from a worktree, never from the checkout itself.** A checkout tracked as a submodule sits on whatever detached HEAD the last update left, so a grep, a lint run or a test suite there answers about code nobody is reviewing. `git worktree add <scratch>/<repo>-review-<target> <canonical-remote>/<default-branch>`, check the target out inside it, and run every command of the review there.
- **A worktree that already exists is reused, never cleaned.** `worktree add` fails on an existing path: re-run only the checkout. It may carry uncommitted edits from another session, so never stash, clean or revert; report them and work around them.
- For a PR: `gh pr view <number> -R <repo> --json title,body,author,baseRefName,headRefName,files,additions,deletions,commits` and `gh pr diff <number> -R <repo>`.
- Read the description, linked issues, all comments via `gh api repos/<repo>/issues/<number>/comments`, and all review comments via `gh api repos/<repo>/pulls/<number>/comments`. Note unresolved threads. Paginate every list call with `gh api --paginate`: truncation at 30 items is silent.
- Read past reviews in `projects/<repo>/reviews/` first; focus on what changed since the last reviewed commit.
- Read `projects/<repo>/CONTEXT.md` before the target and take the round's pace from it, which outranks the plan's projection: a launch weeks away means a lower finder cap and more targets, a quiet stretch the full cap and a second round. An author's stated wants shape the draft, and a finding class they asked not to receive ships `SKIP`.
- Read every changed file in full, and map callers, dependents, and siblings. A guard the diff rewrites, a nil check, a panic, an early return, is mapped at the merge base before its replacement is read: what the rewrite changes is what each of those callers now gets, and a reader who opens the new code first finds the base's reachability last.
- **A finding the description already names is one sentence at most, and often none.** The author wrote it down on purpose, so restating it back at them spends the review's attention on the one thing they cannot learn from it. What is left worth saying is the consequence they may not have pictured, and a clip says that better than a paragraph.

The danger pass, before a branch from outside the project is fetched into a local checkout, nothing executed:

- The trigger is `author_association` of `NONE` or `FIRST_TIME_CONTRIBUTOR`, from `gh api repos/<repo>/pulls/<n> --jq '.author_association'`; `gh pr list --json` has no such field. A target nobody has reviewed on the forge yet gets the pass whatever its author's association.
- Read the raw diff for changes to the build and dependency surface, the CI workflows, the lockfile, the manifest, container files and any shell script.
- Read it for calls that execute, reach the network, read credentials or the environment, or write the filesystem; for encoded or generated code; and for Trojan Source, non-ASCII added lines, bidirectional overrides, zero-width characters and homoglyphs.
- Say in the review what the pass covered and what it found, and carry anything not malicious but risky into the findings.

The catalog:

- **A project with no invariant catalog gets one proposed before its first round starts**, built from the repository's own bug history, its past reviews and the classes its domain is known for, one class per entry with the check that settles it; the round waits for the user's word on the draft, since a finder walking no catalog walks nothing.
- A CONFIRMED finding whose class the catalog lacks adds that class to the catalog in the same round, with the check that found it, so the next round's finders walk it.

Treat CI as a first-class source. `gh run list` shows only GitHub Actions; external checks from apps are check runs. Read the authoritative list for the exact commit:

```bash
sha=$(gh api repos/<repo>/commits/<branch> --jq '.sha')
gh api --paginate repos/<repo>/commits/$sha/check-runs --jq '.check_runs[] | "\(.conclusion)\t\(.name)"'
gh api repos/<repo>/commits/$sha/status --jq '.state'
```

Query each failing check's own API for detail, not its GitHub summary blurb; quote the gate's own numbers. When that API refuses, fall back to the check run's `output` fields and label every number as read from the summary, never as gate-verified.

### Re-review rounds (head advanced)

When a prior round exists and the head moved from `<old-sha>` to `<new-sha>`, compare patch-ids, stable hashes of each diff's content:

```bash
git fetch <remote> <base-branch>
git diff $(git merge-base <remote>/<base-branch> <old-sha>) <old-sha> | git patch-id --stable
git diff $(git merge-base <remote>/<base-branch> <new-sha>) <new-sha> | git patch-id --stable
```

- **Equal**: base-only move. Do NOT re-author: copy the latest round's `.md` files into `<n+1>-<new-sha>/`, rewrite shas, remap anchors, reading the checkout to fix any that no longer map, add a one-line round note saying the head advanced with content unchanged, anchors re-cut, verdict unchanged, then commit. Skip the rest of the workflow.
- **Differ**: full re-review round, focused on what changed since `<old-sha>`. A file the head adds gets first-round depth, whatever round it lands in.
- **New head is a merge of the base branch**: never base-only. Run `git show <new-sha> --cc`; any hunk it prints is conflict-resolution content, reviewed like any diff. Base commits may add tests the branch now fails: run the affected suite on the new head.
- **`<old-sha>` unreachable**: skip the gate, run a full round against the merge-base, note the fallback.

Open every full re-review round with a `Round:` line in the draft's header: `Round <n>.`, how the head moved, what changed, which prior findings and `SKIP` sections were resolved or carried.

### Reproduce the failure

- `gh pr checks <number> -R <repo>` first, plus the check-runs API. Note every failure.
- Run the project's own test and lint commands, taken from its CI workflow file, never guessed. Match the invocation exactly, pinned versions included.
- Record pass or fail per affected package or job.
- **Run each suite and each linter once per tree state, into a file under `<scratch>`, and read only a grep of that file: the exit code, the failing names, the counts.** A suite piped into the context carries the toolchain's every build warning, re-read on every later call, and re-running that state shows nothing new. *Repro rules* still paste that run's output, trimmed, which the file holds.
- **Where the harness cannot select one fixture, run a probe in a copy of the package pruned to that fixture, never in the worktree**, with the copy recipe in the project's delta.
- Before attributing any failure to the diff, run the same check on the merge-base. A failure that also occurs there is pre-existing.
- **Run the project's own tool from the branch's source, never an installed binary.** An installed binary exercises the code it was built from, not the branch's, so a change to the tool tests itself out of the run.
- A repository-level failure gets the same discipline: reproduce each condition on the default branch and identify the introducing commit where history allows.
- When a target changes runtime behavior of a server or tool, boot it and exercise it live; record what was verified live as rows in `claims.md`.

### Review the diff

Read every line. Look for correctness defects: logic errors, missing nil checks, unchecked type assertions, off-by-one. Untested paths. Breaking changes without migration. Style inconsistencies. Reuse and simplification: duplicated helpers, foldable code, unclear naming, missing doc comments, undocumented invariants, filed as Suggestions or Nits, never blockers. Docs impact.

- **Refactor pass, over every added block.** Ask whether fewer lines carry the same behaviour: a value computed twice, a guard the caller already applied, memoization that stabilises nothing, an abstraction with one call site. Where they do, post the replacement as a `Refactor:` suggestion the author applies in one click, never prose describing the change, and record both line counts in `claims.md`.
- **Ask whether each fix sits at the right depth.** A special case added to shared code for one caller, a new root or flag where the cause could be removed, a guard at the call site while the callee stays unsafe for its next caller: each is a Suggestion naming the deeper form and what the shallow one costs to maintain.
- **Inline a local read once that exists only to fit the line width**, and let the formatter wrap the expression: a name is a claim that something is worth naming, and one repeating the expression beside it promises uses that do not exist.
- **A silent fallback where a human has to decide is a finding.** Code that cannot satisfy a rule and quietly returns the old value leaves nobody told: the state that needs a person belongs in the return, a flag beside it or an error, and the surface that person reads has to carry it. The same pass covers a lookup into a fixed list, `list.index(value)` and friends, which raises on a value the list lost and takes every read of that record down with it.
- **Check every claim the diff writes about itself before clearing the code it decorates.** A godoc, a comment, a test header, the description and a decision record name symbols, counts, tests and shapes they call safe: grep each symbol, count each number, run each test the prose says catches something, and run each shape the prose calls bounded or harmless. A claim that fails anchors a finding on the code or the comment, per *Calibration*.
- **Save the tree before the first mutation, `git diff > <scratch>/fixes.patch`, and restore with `git checkout -- <dir> && git apply <scratch>/fixes.patch`.** A mutation loop against an uncommitted fix cannot tell a revert of the mutation from a revert of the fix, so a bare `git checkout -- <dir>` takes the whole branch and the tests written beside it.
- **Make every test the diff adds go red before crediting it.** Revert the fix, swap the configuration the test claims to pin, and plant a sentinel panic in a body a comment says runs. A test still green after that pins nothing: it is a Warning on the test, and the claim it decorated stays unverified.
- **Sweep again, by shape, any class the diff removes or rewrites one member of.** Grep the package for the return type, the signature, the sentence or the pattern that member had, never its name: the sibling that was missed carries a different name and the same shape, and it is in scope per *Calibration*.
- **Feed a path the diff makes reachable for the first time its extremes, and its own read-back.** When a setter, a decoder or a write path starts working, send the type's maximum, zero, empty and a foreign unit through it and follow each to the reader that consumes it; then read the record out and write it back whole, since a field that reads as one value and stores another is rewritten by the next full save.

**Verification discipline.** Every finding passes all of these before it enters the review:

- Verify against the actual file, never from memory or a summary.
- **A finding or Open question carried from an earlier round is re-verified before it ships**, to the same standard as a new one: it arrived with a conclusion and no run attached, and the round that wrote it may have stopped one call short of the code that settles it.
- Follow a carried finding's path to its end: the handler that queues the work, the store that debounces it, the default the framework already applies. Its `tests/*` headers run verbatim from a plain clone before the handover, since a fixture that cannot collect is a claim with no artifact.
- **Browser behaviour needs a browser, and headless is not one.** Anything the browser itself does rather than the page, exiting fullscreen on Escape, a shortcut, a permission prompt, is absent from a headless run and a null result there proves nothing. Run it headful on a virtual display, `xvfb-run -a`, before writing that it cannot be measured.
- Back every behavioral claim with an actual run, at every severity. Never assert stdlib or runtime behavior from memory.
- **Enumerate the case space before writing the finding.** Two sets that must agree give four cells: both, first only, second only, neither. The neither cell is usually the live one.
- **Report what the user loses, never the artifact that causes it.** A conflict, a deleted file, a moved import and a missing guard are mechanical facts; name the action that stops working, for whom, and where. Test it by reading the line cold as a maintainer, deciding in one pass whether to care.
- **When the base has moved, build the merged state and run it.** Apply the base's version of the disputed hunk into the running branch, exercise the path, then revert.
- **A synthetic event is not a run, for anything a user drives with a mouse or keyboard.** A dispatched event skips the focus moves, default actions and library handlers a real input goes through, so it passes where the real input fails. Drive the real app with real input; a synthetic event is only a probe for which listener fired.
- For any claim that the diff *causes* a behavior, run the repro on the merge-base too. Reproduces there: pre-existing, causation false; attribute only the delta and state both numbers.
- When a baseline run or a test kills a finding, drop the finding. Never keep the conclusion and attach a new rationale.
- Treat every "bound" or "leak" claim as quantitative: name the quantity, vary what claims to bound it, confirm they track.
- **Two files carrying the same line are not the same file.** A claim that deployed or released code shares a defect names the revision it was read at, or says the line matched and the revision was not compared. "Identical" over a grep hit is the failure, because the surrounding code that decides reachability was never looked at.
- A reachability claim is proved by construction, never by survey. Build the smallest artifact that would fail if the claim were false and run it, from outside the boundary the claim is about: never a test that builds its own victim, never a grep for existing instances.
- Vary the conditions before naming them. A finding that holds under one shape and not another states which, having tried both.
- When a second condition, tried once, changes no verdict, stop varying it: run the remaining cases under the first alone, and give the artifact one line naming what the try ruled out, never the doubled table.
- Run greps and lint in the reviewed checkout at the reviewed commit.
- **Sweep for callers or consumers over the whole tree, never the diff's own directory.** The consumer a change breaks sits where the diff was not looking, an integration fixture beside a package's own tests for one.
- Confirm a symbol exists with the project's own linter or compiler, sanity-checked first with a bogus symbol.

**Static-analysis findings** are leads, not findings. Before one enters the review: read the flagged lines and state the concrete failure in the project's own terms, never a rule ID plus stock message. Separate real defects from unadopted policies; only the defect may be a Warning or above. Say what the fix costs; a behavior-change fix is a maintainer decision, say so. Never report a count as a finding: group by rule, name one representative, give the full list once.

### Write tests for test-shaped findings

When findings suggest fragile or under-tested code, write edge-case tests, run them, report the failures. Save to `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/tests/`.

When a finding's fix is a test the author should add, ship the test: write it under `tests/`, assert the post-fix state, never the bug's current output, run it, and when it also proves a bug show it failing before the fix and passing after. Embed it in the comment.md finding so the author can paste it in.

Pair the defect with the baseline it breaks in one assertion, and ship both expectations side by side, the current one active and the fixed one commented, each labelled. The pair shows in one screen what the code does and what it should do, and the commented line is what the author uncomments once the fix lands.

Start each test file with a comment block carrying exact repro commands runnable from a plain clone: no workspace paths, no `$HOME`. Pin `git checkout <hash>` in test-file headers only; a draft's repro blocks never pin. The header stands alone, shaped per *Repro rules*. Name code paths by their actual symbol. One-line in-test comments per non-obvious step.

## Overview (`overview.md`)

Write one for every target, first: its own agent, dispatched at step 1 while the parent prepares the round, so it is on disk and linked before a finder starts; a run launched without `overview_exists` starts that agent itself beside the finders, so the reader has it minutes in and never at the end. The findings are written for a reader who already knows the subject; the overview is the only artifact that assumes nothing, and it is what the user opens first, the draft second. A judgement call about complexity was the rule before this one, and it answered "skip" for subjects a reader could not follow.

The skeleton, filled per subject:

```markdown
# <the subject, in the reader's words>
<the generating model, once>

## What it is for
## How it works today
## What the change does
## Concepts
```

- Write it as `overview.md`, never `overview.html`: GitHub serves an `.html` blob as source, so the reader downloads the file to read it.
- **Every code block, diagram and table says whether it is the before or the after.** A reader who cannot tell which side they are looking at reads the defect as the fix. Put it in the prose introducing the block or in the block's own caption, never leave it to be inferred from the surrounding argument.
- It goes at the review directory root, `projects/<repo>/reviews/<slug>/overview.md`, never inside a round directory: it explains the subject, not one commit.
- Explainer only, carrying no review state: no verdict, no findings, no reviewed sha, no round. Name the generating model once, under the title.
- Use anything GitHub renders: a `mermaid` diagram, a `$$` formula, a decision table, before and after values, a `> [!NOTE]`, a `<details>` fold, a committed image, a Concepts section. No emoji, and nothing needing a script or a click, which the blob page strips.
- Where a page would have used a simulator, compute the interesting inputs and put the results in a table. The reader gets the answer without moving a slider, and every number is checkable from the file.
- Run the mirrored logic before publishing its numbers, against the project's own tests where they exist and against the mirrored source where they do not, and say which of the two it was.
- Update it only when new commits change the subject's own files. A base-only head bump, a new finding, a verdict change and a new round never touch it. Link it from the draft's `Overview:` line.

## Links & citations

Shared by the draft, `claims.md` and `overview.md`.

- A private reviewed repo does not strip links from `comment_<model>.md`; the no-blob-link rule covers artifacts living outside the reviewed repo. Strip links from `claims.md` and `overview.md` when a delta file says so, never from the draft.
- Every `file:line` reference is a link to a blob at the reviewed sha: `` [`file:line`](https://github.com/<head-owner>/<repo>/blob/<sha>/<path>#L<line>) ``, ranges `#L<a>-L<b>`. Take the owner from `gh pr view <n> --json headRepositoryOwner`: a fork's commits live in the fork, so the upstream form can 404 on a cross-fork pull request. This covers every reference, including files and tests cited by name. Never a bare backticked `file:line`.
- Pin the reviewed sha, never the branch: the link shows the code the finding was written against whatever the branch does next, and a new round cuts its anchors at its own sha.
- A blob link into a rendered file such as `.md` needs `?plain=1` before the `#L` anchor.
- A link must prove the exact clause it anchors. Read the cited lines and confirm the number, symbol, or behavior appears in the range. One claim per anchor: two numbers, two links. For a pinned tag, fetch the file at that tag.
- Attribute a behavior to what guarantees it: a toolchain detail cites the toolchain, never a spec that does not require it. When the spec guarantees less than observed, say so.
- A bare sha autolinks only in the repository holding that commit. Prose in `comment_<model>.md` writes the reviewed repo's shas bare, for the hovercard; `claims.md` keeps its own shas as they are, since the reviewed repo's sha resolves to nothing in the workspace repo.

## Repro rules

Shared by the repro blocks of the draft and `claims.md`. A repro is the runnable sequence demonstrating a claimed behavior.

Settle where the repro goes before writing one. A finding on a surface the reader reaches in a browser ships no harness in the comment, whatever the rules below say: the author opens the page instead of cloning, installing a test runner and writing a config by heredoc. Post the clip, or the steps in the sentence, and keep the harness in `claims.md`, the claim that is a number included, which goes in the sentence with what it was counted over.

- Every empirical claim ships a copy-pasteable repro: fenced `bash`, self-contained, one clear pass/fail signal, restoring modified files at the end. Pin env vars only when depended on.
- **No repro for a merge conflict.** State what the resolution costs and stop; the conflict itself is not the finding.
- Start with `# from a local clone of <repo>:`, then the checkout command. Zero local paths, no trailing `git checkout <hash>` pin. Inline needed files with heredocs; never `curl`, never reference into the reviews tree. Clean up at the end.
- Follow the block with the observed output in a second fenced block, trimmed to the signal-bearing 5-20 lines, `# …` marking omissions.
- A repro whose output is a failure says so in one line directly above that output, naming what failed and why the failure is the finding.
- A repro demonstrates behavior. Source inspection and greps are not repros.
- A fixture's header comment is three or four lines: what it asserts, the measurement, and that it fails at the reviewed head. The mechanism belongs in the finding. Keep a measured table; cut the prose around it.
- Write the repro in the harness the repo already uses for that surface, found by reading the test the diff itself adds. A defect on a surface the project covers with an integration fixture belongs in that fixture format, not a unit test poking an internal function. Copy the neighbouring fixture's structure, naming and assertions.
- Size the fixture against the threshold it asserts. A repro claiming a bound is exceeded must exceed it: check the input against the real constant.
- A measured number is committed with the artifact that produced it, in the round directory, before the number is written down anywhere. A number whose repro is gone: delete it or re-measure it, never carry it forward.
- Run the repro from the draft, verbatim: extract the block from the file and execute it. Every number in the prose comes from that run's output, pasted, never from an earlier run, a rounder figure, or memory.
- Heredoc behavioral tests, asserting the post-fix state, fail now and pass fixed, for Critical and Warning only. Nits and Suggestions cite the anchor; a one-line "confirmed behaviorally: X" note is enough.
- **Film every finding whose symptom shows on screen, in the round that finds it, unasked.** Ship the clip beside the finding in both artifacts, captured per the picture rule in `skills/writing-style.md`. Where the browser cannot reach the screen, name what stood in for it.

## Output

A round directory, `projects/<repo>/reviews/<slug>/<n>-<short-commit-hash>/`,
and the overview beside it at the slug root:

```text
projects/<repo>/reviews/<slug>/
  overview.md            the subject for a reader who knows nothing, no review state
  <n>-<sha>/
    comment_<model>.md   the draft: Verdict, Event, Model, Commit, Overview, Open the code, Round;
                         the Body; one section per finding, posted or SKIP, its repro collapsed
    claims.md            one row per candidate, then the completeness answers, then Outcomes
    findings.md          the draft's skeleton, one block per finding in posting order, from `round assemble`
    links.md             one row per link of the draft and the overview
    tests/               every artifact a verifier ran
    candidates/          what each finder and the reflector returned, as JSON
    verdicts/            what each verifier returned, as JSON
```

A row of `claims.md`, and the round note above it in the draft:

```markdown
| 7 | REFUTED | Warning | pkg/store/cache.go:88 | go test ./pkg/store -run TestTTL, 0 TTL case | evicts after 5m, PASS; cache.go:31 clamps ttl <= 0 | | hot |

Round: 1. 7 finders, one reflector, 58 candidates, 23 of them Nits on the finder's own read and the rest run from scratch by an agent that was not its finder.
```

- `comment_<model>.md`, the draft, per `skills/review-comment.md`: every finding as a section, posted or `SKIP`, with its repro. Its header carries the verdict, the model and effort, the reviewed sha, the overview link and the round note, and `./scripts/post-review.sh` sends nothing above the first section, so the round's judgement and its shape live in the one file the user opens.
- `claims.md`, the record, written by `./scripts/round assemble <round dir>` from `candidates/` and `verdicts/`: one row per candidate the verifiers ran, and one at state `UNVERIFIED` per Nit the round's ceiling left unrun: state, band, `file:line`, the check, the observed output, the artifact under `tests/`, and the tier the risk table gave its file. A refuted candidate keeps its row with the proving line, so a later round reads what was cleared and why. Then the completeness answers.
- `tests/`, every artifact a verifier ran, per *Write tests for test-shaped findings*.
- `links.md`, the text pass's row per link, which is the pass's own coverage proof and not a finding.
- `candidates/` and `verdicts/`, one JSON file per agent, the same object it returned, so the record is on disk before the writer runs and a stage that dies loses its own file and nothing else.

When a posted round's target merges or closes, `./scripts/review-outcomes.py <draft> --write` adds an Outcomes table to `claims.md`: per posted finding, fixed, resolved or open, and whether the author replied. That table is what a change to a tier, a cap or a batch is measured against.

### Calibration

- No target finding count. Stop when the diff is read in full and the blast radius is mapped: callers, dependents, siblings.
- State only what CI does not show, per `skills/writing-style.md`; never "tests pass", "lint clean", "build green".
- A defect a CI job catches is never a comment, at any severity. Name the job that fails on it and drop the finding, because the author reads the red job before they read the review. What survives names the reason no job reaches it.
- Severity is binary. Warning = a maintainer could plausibly block: correctness, security, decay, missing invariant. Nit = style, polish, optional. In doubt: Nit.
- A wrong finding spends the author's trust, and the author stops reading after two: a thin Warning is a Nit or a `SKIP`, never a Warning posted on the chance it holds, and the outcome table, fixed against open per posted finding, is where that cost is measured.
- The verdict answers to the severities, and a surviving Warning rules out APPROVE. Reconcile before shipping: either the finding is a Nit and the band was wrong, or the verdict is COMMENT. COMMENT when the change improves strictly on its base and the Warning is a defect it did not introduce; REQUEST CHANGES when the branch causes the Warning or ships it to users. Either way the verdict line names the Warning and says why it does or does not block.
- Severity measures whether the defect is real, not how big. A small genuine correctness bug is a Warning; magnitude goes in the details. Suggestion is for non-bugs: latent-only risks, design tradeoffs.
- **Weigh the recovery before the band, and read the finding's own limits paragraph as the reader will.** A reproduction proves the defect is reachable and says nothing about what it costs. Where the write-up already says the state is recoverable, the attack unrepeatable, or the loss one more ordinary transaction, that paragraph has set the band and it is low: a defect whose worst case is doing the same thing again is a Nit, however cleanly it reproduces. The tell is a finding arguing its own severity down in its second half while its first half claims the opposite.
- **A published vector decodes itself, and the score line is what opens it.** The severity line goes in the `<summary>`, so it reads as it always did and expands to one row per metric: the code beside the metric's name, its rating, then what that metric means for this finding, never boilerplate. The score is then stated once, not in a metadata row as well. No link: a reader cannot get this from `AV:N`, and an advisory that needs a third party to be readable has taken a dependency for nothing.
- **Score the vector from what the attack requires, and never move a base metric once a band has been named.** Editing `UI`, `PR` or `AV` in the turn someone asks for a different severity is scoring backwards, whatever reason the edit carries. Deployment context has its own metrics: raise `IR`, `CR` or `AR`, publish the environmental score beside the base one, and the higher band is computed rather than asserted.
- **A finding about an ADR's own text is a Nit, whatever it concerns.** An ADR records a decision and ships no behaviour, so an omission in one costs a paragraph and never a defect: the permanence it fails to state, the alternative it skips, the filename it keeps. Its claims about the code are run like a comment's, per *Review the diff*, and one that fails is a finding on the code with the ADR as the evidence.
- A cosmetic nit no enabled linter enforces carries the config link and ships `SKIP`, per `skills/review-comment.md`. Check the linter config before flagging a style convention.
- A finding about a code comment's own wording ships `SKIP`, whatever band it lands in: it changes no behaviour, so it does not earn an inline slot by default. Keep the measurement that shows the comment wrong in `claims.md`.
- A pre-existing defect is in scope in three cases: the diff sweeps that defect's class and missed it, the change makes the code permanent, or the change makes the defect reachable for the first time. Name the sweep, the freeze or the new path, and say it predates the diff. Read the diff, never recall: promoting something to a security boundary, or adding a test asserting the behaviour, is the first case, and the verdict moves with it.
- A pre-existing defect found while reviewing, in scope or not, goes the same turn to an issue draft per `skills/issue.md`, or to the project's audit tracking where its delta names one, under the disclosure invariant when the code is deployed. A row in `claims.md` is where such a finding dies.
- Map the full call graph before claiming anything dead, redundant, or unused.
- Code that cannot run is a finding, never a reason to drop one: an impossible guard, an unreachable branch, a default the type forbids. **Ask for its removal, and name every site the removal touches**, the symbol it declares included. A rename, a reworded message or a tidied comment keeps the code and ships as polish on protection that is not there, so a wording finding inside proven-dead code is that same finding, one band down.
- Clearing something needs the same evidence as flagging it. To clear "X is safe because guard G covers it": find G's construction site, list its callers, and confirm X is one. Never infer that a guard reaches a member from a grouping made by the diff, its docs, or its author. A cleared item whose mechanism was not traced is unverified; say so.
- A suspected defect leaves the review only through a run showing it guarded, with the proving line quoted. Without that run it is a Warning, never an Open question.
- When the finding is a missed member of a class, measure the whole class in one harness and publish the table.
- Never flag contribution-policy compliance as a code finding; mention it in the narrative only when it is why CI is red.
- Never critique the project's own governing document, meaning its wording, the symbols it names or the claims it makes, and never reference it to editorialize. Where the code is wrong the finding is about the code, and where a code or test comment repeats a claim the document has outrun, the finding anchors on that comment.
- Post a deferred-scope or extension question only when there is a concrete risk or a decision the author must make now; otherwise a `SKIP` section in the draft closing with the question.

### Rules

- One directory per round, per *Output*. `<slug>`: for a PR, `<number>-<3-4 words from the title>`, lowercase, hyphenated; otherwise a name for the subject. `<n>`: the round number, from the existing directories. `<model>` in the draft's name: lowercase, hyphenated. Hash = reviewed head. A second round over a reviewed commit gets `<n+1>-<same-sha>`.
- On the first review for a repo, create `projects/<repo>/reviews/README.md` with the repo's GitHub link and one line.
- Minimal bold. Every file renders in GitHub-flavored markdown: blank line after `<summary>`, continuation indented 2 spaces under list items, `<details>` nested at most one level.
- Delete empty sections' headings. Never write "None". Never fabricate findings.
- Priority order: correctness > security > determinism > state safety > tests > docs > style.
- A diff spanning several packages or directories is summarized by area first, then its critical paths in depth.
- One final push covers the round, to this repo only. The push is pre-authorized for this skill and overrides any global ask-before-push rule.
- Fold a late finding into the draft and `claims.md`, verify it with a real run, commit and push in the same turn without asking. Posting still waits for `post`.
- Never push to a reviewed repo's canonical remote; a fix branch goes to the fork.
- Reviews may be published. A finding exploitable against already-merged or deployed code is not: it takes the disclosure gate in the workspace `AGENTS.md` Invariants before anything is written. A finding on an open PR's own diff is fine at any severity.

## GitHub review draft (`comment_<model>.md`)

The writer's artifact, step 4 of the workflow. The draft, its body rules, the shape of each inline
comment, the final check and the posting gate are in `skills/review-comment.md`.
Draft it whether or not anything will be posted.
