---
name: review-comment
description: Use when drafting, regenerating, or posting comment_<model>.md, the GitHub artifact a review ships. Extends skills/review.md with the body rules, the inline-comment shape, the final check, and posting.
---

# The review comment

`comment_<model>.md` is the deliverable and `claims.md` the record: the
evidence, the arithmetic and the rejected candidates. Spend the effort
here: a finding that changes what the author does and lives only in `claims.md`
has not been reported. Where the two disagree on wording, the comment wins and
`claims.md` follows it.

Draft in the round directory beside `claims.md`. Visible prose follows *Posted comments* in `skills/writing-style.md`. A `## SKIP <path>:<line>` header marks a finding that never goes out, whatever the round decides; never delete a dropped comment, since the marker survives regeneration. Which of the rest go out this time is chosen at posting, by band or by anchor, per *Posting*, so a round posting the Warnings alone writes no marker for what it holds.

A target with no PR, a branch or a repository-level failure, gets a GitHub issue draft in the same filename: `Target:` and `Event: ISSUE` in place of the PR header, then `## Title`, `## Body`, and the anchored `## <path>:<line>` sections posting as plain headers inside the body. Each section still runs 1-3 sentences and closes with fixed-on-branch or left-out and why, in place of the `**Proposed fix:**` line. Post with `gh issue create -R <repo> --title ... --body-file ...` on `/post`, per Invariant 1.

Auto-SKIP duplicates: when another reviewer, or the posting account itself, already raised a finding, prefix its header with `SKIP` while drafting, attribute the reviewer in `claims.md`, and make `Already raised: <comment-url>` the section's first body line. A section bundling an already-raised finding with a novel one is split so the novel part posts. Where the raised finding is one case of a broader one being posted, name that case in the broader sentence, linked to the original, instead of splitting.

Sections, and the moment each is read: *Body rules* and *General rules*,
the writer; *Building each inline comment* and *Visible-text style*, the writer
and the text pass; *Answering a finding on your own pull request*, a reply on
the user's own change; *Repros*, the writer; *Rounds & regeneration*, a second
round or an edit of a posted draft; *Posting*, `/post`; *Final check*,
the parent before the handover.

Format:

```markdown
# Review: [#<number>](https://github.com/<repo>/pull/<number>)
Event: APPROVE | REQUEST_CHANGES | COMMENT
Verdict: APPROVE | REQUEST CHANGES | NEEDS DISCUSSION | CLOSE, then one sentence naming the open concerns
Model: <model>, <preset> review <— quick, standard or deep, the preset the round ran under>
Commit: <short-sha> (latest, or stale — +N commits since)
Overview: [overview](../overview.md)
Open the code: <github.dev and vscode.dev links at the head repository and the reviewed sha>
Round: <n>. <the round note, re-review rounds only>

## Body
<The summary, per *Body rules*, then one-sentence bullets for unanchored findings only.>

## <path>:<line> · <Band>
<1-3 sentences: the problem and why it matters>

**Proposed fix:** <the change, one sentence, only where a run proved it>

<details><summary>repro</summary>

<fenced bash repro block + fenced observed-output block>
</details>
```

### Body rules

- A finding with more than one case is a claim and a list, never a paragraph: one line for the claim and its mechanism, then one nested bullet per case naming its condition and outcome. Put the cases where it does not bite beside the ones where it does.
- The Body opens on a summary of one or two sentences, a plain paragraph and never a list item: whether the change can go in as it is and why, in one clause, then which comments block it and which are optional, each named by what it is about, never its `path:line`, where no comment posts the first clause alone, and where the gate did not run the sentence saying so: `This keeps a revoked token valid until logout, so it can't go in yet. The expiry comment is the blocker; the naming one is optional.` A line another rule asks of the Body, a red check or a carried finding, follows it in the same paragraph.
- Under the summary, the Body has two jobs: cross-cutting synthesis the per-line comments cannot carry, and every finding no single line owns, as a list per *Posted comments* in `skills/writing-style.md`. Below the list goes the clip showing the feature doing what the bullets say. A paragraph there is a finding that should have been anchored.
- Every demonstrative in a finding naming an edit points at its anchor. This timer, this map, this call carrying a link somewhere else is the tell: the sentence wanted a second anchor.
- **Never pin a line the finding does not want changed.** Anchor a finding naming an edit on the line that gets edited. Where that line sits outside the diff the finding has no anchor at all, and it goes in the Body as a bullet carrying its own links, never on the nearest changed line.
- The Body is about the branch, never about the review. Two shapes fail it: the imperative, `Read the caption path`, homework for the author who wrote that path, and the report, `This looked at the three token routes`, the reviewer's afternoon. The tell: neither asserts anything that can be wrong. Write the problem no line owns, or the one property the anchored comments cannot carry between them.
- On a security fix, an advisory or an embargoed repository, post only what changes behaviour, the fix's coverage or the verdict. A Nit on a test's wording, a comment, a count or a name ships `SKIP`. A Missing test there counts as coverage only where the mutation it catches reopens the bound the fix closes; one pinning a boundary no deployment reaches, a size its application caps far below, ships `SKIP` too, with the cap and its command on the `Not posted:` line.
- Post every finding the author should act on, and open with the one that changes what they do next. An action is a fix, a decision or an answer, and severity never gates it: a Nit naming a concrete problem gets its own section. Never drop a real finding to make the review shorter; shorten the finding instead.
- **Every finding gets a section here, and the ones that will not go out get `SKIP`.** Draft each skipped finding as `## SKIP <path>:<line>` with the text a posted section would carry, closed by one line, `Not posted: <reason>`, as its own paragraph with a blank line above it, so un-SKIPping is the whole decision. `SKIP` covers what needs no action from the author, a check CI already reports, a cosmetic nit no enabled linter enforces, and a finding about a code comment's own wording. Every finding about the changelog ships `SKIP` too, a missing or misplaced entry included, and never becomes a Body bullet.
- **A Critical or a Warning whose line sits outside the diff is never skipped as the same defect as one the diff holds.** Post both: the one in the diff anchored there, the one outside it a Body bullet carrying its own link, opening per *Building each inline comment*: `Related` only where the merge base shows the same symptom.
- Where every site of one defect sits in the diff and one edit closes them all, the defect is one section: anchored on the line that edit changes, carrying every site's evidence, the other sites shipping `SKIP` with a `Not posted:` line naming that section. Name the one edit in `claims.md`; a group no single edit closes stays one section per site.
- A measured defect on a line the diff touches is posted, whatever argument the measurement suggests against it. It never fires, it predates the branch, the branch only makes it worse: each of those is the finding. Open questions hold what the reviewer could not decide, never what they decided not to send.
- Name the event beside the draft, never after it. The header's `Verdict:` line is the reviewer's judgement and does not move. What gets posted, APPROVE, COMMENT or REQUEST_CHANGES, is the user's call: show it with the text and let one word settle both.
- **The draft's `Event:` is what goes out.** Never soften it on the way to the forge: an `APPROVE` posted as a `COMMENT` because a past turn asked for one reads as withheld approval. The event changes when the user names the new one in the turn, and a stale default is raised as a question, never resolved quietly. The one override is `/post as ai`, per *Posting*: the marker goes out as `COMMENT`, whatever the draft says.
- Past the opening summary, never mention an anchored finding in the Body: no bullets, no recap, no pointer to it, no count.
- Do not re-describe the change or restate thread state.
- **Stateless: state the code's current property, never its history.** History includes the round, a prior draft, a sibling pull request, a competing branch, how somebody else solved it, and every sha, message, ordering and count of what landed when; a comparison stays in `claims.md`. Where the branch's own sequencing is the finding, the finding is what the code does now and what a reader has to split to fix it. Search a finding for `this change`, `this fix`, `now`, `still` and `no longer` before it ships, and rewrite it on what the highlighted line does.
- Nothing about CI reaches the comment, in any check state, except the stale-base sentence named below.
- When a Body check asserts a property a committed test could assert, write the test instead.

### General rules

- `Event:` defaults from the verdict: APPROVE → APPROVE, REQUEST CHANGES → REQUEST_CHANGES, NEEDS DISCUSSION and CLOSE → COMMENT. It is a default, not a lock: the user may post a lighter event than the verdict, and then the `Verdict:` line keeps the judgement while `Event:` records what went out. The `Event:` line carries it; the Body states it only in its opening summary.
- Never review your own pull request: no verdict, no findings, no `self-review.md`. Instead the author posts one inline comment per part a reviewer should open, saying why that line matters, on the line itself and never as a section of the body. What the diff read back turns up goes in the change's `plan.md`.
- Two defects where fixing one leaves the other are two sections, never one clause. The test is the author's next edit: if applying the first still ships the second, the second has its own anchor.
- Order findings by what the reader needs first: the one that makes the others legible leads, whatever its band, then Critical, Warning, Missing test, Nit, Suggestion; file order within a band.
- A finding that needs a third explanation leaves the comment. Mark the section `SKIP` with a line saying why; the explanation goes to `claims.md`.
- Never explain routine fixes: merge the base, regenerate assets, re-run a flaky job. A red check with a routine cause gets one short Body line, naming what is no longer readable rather than the fix.
- **A mistake in the pull request's own title or description never reaches the draft.** The author rewrites both from the findings. Where either is the only source of a claim, anchor the claim on the code carrying it: a change riding along unannounced is a finding about the change, never about the words that failed to mention it. What the title or the description got wrong stays in `claims.md`, and a section that cannot be re-anchored ships `SKIP`.
- Never tell the author to rebase. They meet the conflict the moment they try to merge, and a reviewer spending the body on it says nothing the branch does not already say. What a rebase costs, a behaviour it drops or a build it breaks, is a finding anchored on the line that carries it. Nothing else about the base branch reaches the comment. One exception: when the stale base is why the review is not an APPROVE, the opening summary says so, because a withheld approval whose reason is unstated is the same defect in the other direction.

### Building each inline comment

1. Anchor. One `## <path>:<line>` section per finding, every severity; ranges `## <path>:<start>-<end>`. Line numbers reference the head commit, side RIGHT. Read those exact lines first, and anchor on the shortest run that shows the code the claim is about: GitHub prints the anchor and a few lines above it, so a `func` line shows its doc comment and none of its body, and a whole block pushes the diff off the screen. Pick the switch, the guard or the list the sentence is about, and stop there.
2. Opener. `Critical:` / `Nit:` / `Suggestion:` prefix matching the verifier's band, then the TL;DR. A Warning gets NO prefix. **A finding on code the diff did not introduce, whose symptom the merge base already shows, opens `Related:` in front, `Related critical:` or `Related suggestion:` with a band**, an inline comment and a Body bullet alike. A symptom the merge base lacks is the branch's own, whatever file holds the line to edit: no `Related`, and the first clause says what the branch now does. **The first clause names what the highlighted line does**, the `true` argument, the `init()`, the parameter, before any function the line does not show. A missing-test finding opens `Missing test:` plus the uncovered scenario. **A finding proposing an edit to test code opens `Test:`**, in place of its band on an inline comment and in front of a Body bullet, since a change confined to tests carries no production risk. No bracketed priority tags.
3. Sentences. One visible sentence, two only when the second carries a fact the first does not; code blocks, `<details>` and the `Proposed fix:` line do not count; no headers, and no bold but the `Proposed fix:` label. Order: gap and stake, evidence, then the `Proposed fix:` line where one goes. Over one: cut evidence, never the gap. What ships is the defect, the anchor and the repro: the reasoning, the prototyping cost and the verification pins stay in `claims.md`.
4. Fix line. **A section carries a fix only where its judge applied it and the rerun ended on `fix: fixed`**, per *Verifiers* in `skills/review.md`. That fix is a proposal, its own paragraph closing the visible text, `**Proposed fix:** <the change>`, one sentence above any `<details>` and above a SKIP section's `Not posted:` line, over the no-fix default of `skills/writing-style.md`: `**Proposed fix:** check the token's expiry on each request.` Every other section states the problem and stops, with no fix line, no direction and no `for instance`. A refactor's `suggestion` block, banded only once its rewrite passed the tests, is its own proof, its line naming the edit in a few words above the block.
   - Before stating a fix to a script that runs in a container, run it in the image the deployment runs: pulled where it ships ready-made, built from its Dockerfile's final stage otherwise, or that stage's `FROM` image where the build cannot run here.

### Visible-text style

Governed by *Posted comments* in `skills/writing-style.md`; the rules below are the review-specific additions.

- Essentials only: the problem and why it matters. No stacked clauses, no symbol-chain walkthroughs, no scenario-painting.
- Rule out only a design the author raised, in the code, the description or a thread.
- **Every term in a finding is one a maintainer who has not seen the code can expand**, and a cut that leaves one they cannot has deleted the claim rather than shortened it. Name the expression, the guard or the call, never its position: `the line below` and `this comparison` have no referent under a range anchor, and a word coined to compress, a link that `names no package` for one pointing at a path no package occupies, reads as jargon the reader looks up and does not find.
- A latent-risk finding states the current safety in one clause and stops.
- A layer named is a symbol named. "on the model", "in the serializer", "at the view" tells the reader where the code is not, never what putting it there would cost. Name the class and the call that makes the claim true, `BaseModel.save()` running `full_clean()` on every write for one, then the consequence in the same sentence.

### Answering a finding on your own pull request

The register is the shortest thing that settles it. A bot posts each finding
twice, once inline and once as a summary comment, and the reply belongs in the
inline thread.
A finding that holds is fixed in the same turn rather than
reported back, and the bullet is `Fixed: <sha>`. One that does not gets the
sentence that refutes it and a collapsed run. Never argue a finding across a
paragraph.
Every reply names the pushed sha and stops, with no range or compare link
after it.

### Repros (comment.md deltas)

- Attempt a repro for every Critical and Warning before drafting. No run proof: word it as an observation, never "I ran X". Source-visible facts: cite the anchor, drop the block.
- A repro whose check also fails at the merge base says so inside its block, with the base's output beside the head's.
- A repro lives in exactly one file: the draft owns it for findings anchored there; `claims.md` states the result and links it. Line-specific repros stay with their comment; suite-wide ones go in a Body `<details>` block, pointed to.
- A missing-test finding carries ready-to-add cases in a collapsed `<details><summary>test cases</summary>` block, in the file's own test style, paste-ready.
- A table or repro no remaining sentence cites leaves the comment. Re-read every collapsed block against the visible text on each revision, and move the orphan to `claims.md`.

### Rounds & regeneration

- Before offering a draft to the user, measure its target and offer the live ones alone. Merged, closed, or already carrying a review from this reviewer means the draft is a record rather than a pending action. Write the answer into the draft's `Status:` line in the same turn.
  ```bash
  gh api repos/<repo>/pulls/<n> --jq '"\(.state) \(.merged)"'
  gh api --paginate repos/<repo>/pulls/<n>/reviews --jq '.[]|select(.user.login=="<login>")|.state'
  ```
- **A second pass over a head whose review is already posted writes its own draft**, `comment_<model>-take2.md` beside the first, and the posted file goes back byte-for-byte to what went out.
- Port carried findings verbatim; change only shas, repro URLs, and stale anchors. No round-relative phrasing.
- A carried finding whose thread from an earlier round is still open is not posted again, as neither a new inline section nor a reply restating it. The Body names it unresolved in one clause and stops, each carried finding a hyperlink on its own words pointing at its thread. Two clauses means two findings, and a paragraph there is the finding posted twice. List the open threads before showing the draft, `gh api --paginate repos/<repo>/pulls/<n>/comments --jq '.[]|select(.user.login=="<login>" and .in_reply_to_id==null)|"\(.id) \(.path):\(.line)"'`, and drop every section anchored on one.
- A SKIPped finding stays SKIPped when ported, with a one-line note, until the user un-SKIPs it. Before regenerating, read the existing file and preserve every surviving `SKIP` marker.

### Posting

- **Before rewriting anything already posted, a review, a comment or a pull request body, read the live text back and merge the draft over it**: `gh api repos/<repo>/pulls/<n> --jq .body`, `pulls/comments/<id>` or `pulls/<n>/reviews/<id>`. Bring the draft's own tree to its remote first, `git fetch` and `git rev-list --count HEAD..origin/main` reading 0: the posting session wrote the `Posted:` line and the `[posted]` anchors back there.
- `./scripts/post-review.sh <draft>` posts it as one pull request review, never a plain issue comment: it validates every anchor against the current diff, folds the comments into a pending review the user already has on the target, reacts to each `Already raised:` duplicate, and writes `Posted: <review-url>` under the title and `[posted](<comment-url>)` on each anchor. Run `--dry-run` first when anything about the draft is uncertain.
- **One posted review per head.** A pass finished after the post goes as replies in the threads it touches, or waits for the head to move. A finding the first pass missed and no thread carries goes as one reply on the review's own thread, never a new review.
- **`/post as ai` sends the draft with `> AI review, <model>, <preset> review, reviewed at [<sha>](<pull request>/commits/<sha>), [skills](https://github.com/davd-gzl/skills) · [overview](<url>) · [claims](<url>) · Status: <verdict>` as the Body's first line and `COMMENT` as the event**, whatever the verdict. A reply carrying the marker opens on the same line. `--as-ai` builds that string, the commit from the draft's `Commit:` line, and refuses a draft whose line carries no sha: it reads the visibility of the repository holding `overview.md` and the round's `claims.md`, carries each link at that repository's default branch when it is public and omits it when it is private. **Nothing is composed beside the marker**, and words the user typed for it go on its line behind a second `·`, verbatim; the Body's summary follows in its own paragraph. The command covers the one post it was typed for, and it is the only one that puts an AI marker in a posted string, a standing word in *Consent* of the workspace `AGENTS.md` aside. It posts every section the draft does not mark `SKIP`, every band included, unless the user names bands or anchors, per the subset bullet below.
- A reply sent under `/fai` opens on `> AI reply, <model>`, then the reply per *Answering a finding on your own pull request*. Nothing in the reply speaks for the user.
- To post replies in review threads, write one `<comment-id>.md` per thread into `<scratch>/replies-<pr>/`, `@SHA@` and `@SHORT@` where the pushed commit goes, and send them all in one command after the push: `./scripts/post-replies <owner/repo> <pr> <scratch>/replies-<pr> --head <sha>`. A `gh api` write per reply asks the user once per reply, and a loop of them hides from the open-thread gate which threads it answers, so the gate refuses the run. On the user's own pull request the script then re-requests the review of each thread's author still requesting changes by their last review other than a comment, and `--no-rerequest`, passed where the user says so, skips it for those threads on every later run. The reply offering `post` names whoever will be asked on its word line, from the same command run with `--dry-run`.
- A `gh` write refused 403 `Resource not accessible by personal access token` is a missing scope: never retry or work around. Do everything the scope allows first. The script records the refused command in the draft's `Status:` line; end the reply with `post <github url of the artifact>` on its own line, and for a refusal larger than one post name the repo, the branch, both shas, the steps in order, and which token was refused where.
- **Post a subset by band or by anchor, never by editing the draft**: `--band 'Warning,Critical'` posts the sections whose header carries one of those bands, `--only <path>:<line>,<path>:<line>` posts the named ones, and `--list` prints every section with its band and first sentence for the user to choose from. What the selection holds back is reported as held, keeps its text and its band, and goes out unchanged in a later post once the head moves.
- `/post` covers every verdict, APPROVE included, with no extra confirmation.
- A draft already carrying `Posted:` is re-posted by rewriting that review in place, by hand since the script refuses it: the `updatePullRequestReview` GraphQL mutation on the review's `node_id` for the Body, `gh api graphql -f query='mutation($id:ID!,$b:String!){updatePullRequestReview(input:{pullRequestReviewId:$id,body:$b}){pullRequestReview{state}}}' -f id=<node-id> -F b=@<body-file>`, since the REST `PUT` on the review answers 404 for its own author, and `gh api -X PATCH repos/<repo>/pulls/comments/<comment-id> -f body=<body>` per anchor, the ids from the `Posted:` and `[posted]` URLs; the event cannot change, and an anchor with no `[posted]` link aborts the re-post rather than opening a second review.
- Before any post, check whether the target already carries a review from this author and reconcile the draft first; the script warns and continues.

### Final check

Verify each line before handing over:

1. The header carries `Verdict:`, `Model:`, `Commit:` and `Overview:`, and the overview link resolves. `Model:` names the models and efforts `./scripts/review-retro.py <workflow-dir> --served` prints, since the config names what was asked for and not what ran.
2. The Body names at most three checks, each runtime-only, none CI-visible, none recapping anchored findings past the opening summary.
3. No repro block has a passing run as its only output.
4. Every non-Warning inline comment opens with its band; Warnings open with the TL;DR. Every comment names a problem the author should act on, and carries a `**Proposed fix:**` line only where its judge's rerun ended on `fix: fixed`, or above a refactor's `suggestion` block.
5. `./scripts/prose-check.py <draft>` counts the sentences per section, its `**Proposed fix:**` line out of every count, the code names per sentence, the Body's lines and the sentences of the `Verdict:` line: a hit is rewritten in plain words, naming only the symbols the claim needs. Each section carries one distinct problem. Count the `<details>` blocks too, and delete the one attached to a merge conflict or to anything the author confirms by opening the app.
6. No verdict restating the `Event:` line outside the opening summary, no bold but the `Proposed fix:` label, no imported emphasis caps, every `skills/writing-style.md` rule holds.
7. Every `Suggestion:` was applied in a worktree and run both ways, the case the finding is about and the case the current code already handles. Run the path carrying no user action: the page load, the reconnect, the re-render. The current code guards that path and the finding is about the path with a click in it, so a fix that drops the guard becomes the bug it was written against. Name every result in `claims.md`.
8. Every finding names the set it holds for, and the band follows the size of that set. One example value standing in for the set understates both: "a French browser" where every non-English browser fails is a Critical wearing a Warning's clothes.
9. Open every link and read the lines it lands on: each must contain the number, symbol, or behavior claimed. `./scripts/round links` proves that every link resolves at the pinned ref and that its range fits the file; the claim on the lines is read.
10. Re-run every claim against the tree before the draft is shown, including the ones carried from an earlier revision. Print the code beside the sentence.

Then the text pass, once, over the finished draft. An edit after the text pass gets the parent's own pass over the edited section, its cited lines re-read, and a run only where the edit adds or changes a claim, that run's row going to `claims.md`.

- **The text pass**: one agent with the draft, `overview.md`, the checkout and *Visible-text style* in `skills/review-comment.md`, running the three steps of *Text pass* in `skills/review.md`. Its one delta: the per-link row saying whether the landed lines carry the claim stays in `links.md` and never enters `claims.md`.
