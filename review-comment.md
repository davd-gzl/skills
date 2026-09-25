---
name: review-comment
description: Use when drafting, regenerating, or posting comment_<model>.md, the GitHub artifact a review ships. Extends skills/review.md with the body rules, the inline-comment shape, the final check, and posting.
---

# The review comment

`comment_<model>.md` is the deliverable and `claims.md` is the record, which
holds the evidence, the arithmetic and the rejected candidates. Spend the effort
here: a finding that changes what the author does and lives only in `claims.md`
has not been reported. Where the two disagree on wording, this one is right and
`claims.md` follows it.

Draft in the round directory beside `claims.md`. Visible prose follows the *Posted comments* section of `skills/writing-style.md`. `SKIP` prefixed to a header, `## SKIP <path>:<line>`, marks a finding that never goes out, whatever the round decides; never delete a dropped comment, since the marker survives regeneration. Which of the rest go out this time is chosen at posting, by band or by anchor, per *Posting*, so a round that posts the Warnings alone writes no marker for what it holds.

A target with no PR, a branch or a repository-level failure, gets a GitHub issue draft in the same filename: `Target:` and `Event: ISSUE` in place of the PR header, then `## Title`, `## Body`, and the anchored `## <path>:<line>` sections posting as plain headers inside the body. Each section still runs 1-3 sentences and closes with fixed-on-branch or left-out and why. Post with `gh issue create -R <repo> --title ... --body-file ...` under the `post` word of Invariant 1.

Auto-SKIP duplicates: when another reviewer, or the posting account itself, already raised a finding, prefix its header with `SKIP` while drafting, attribute the reviewer in `claims.md`, and make `Already raised: <comment-url>` the section's first body line. When a section bundles an already-raised finding with a novel one, split it so the novel part posts. Where the raised finding is one case of a broader one being posted, name that case in the broader sentence and link it to the original instead of splitting.

Sections, and the moment each is read: *Body rules* and *General rules*,
the writer; *Building each inline comment* and *Visible-text style*, the writer
and the text pass; *Answering a finding on your own pull request*, a reply on
the user's own change; *Repros*, the writer; *Rounds & regeneration*, a second
round or an edit of a posted draft; *Posting*, the word `post`; *Final check*,
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
<One-sentence bullets for unanchored findings only, and empty when every finding is anchored.>

## <path>:<line> · <Band>
<1-3 sentences: the problem and why it matters>

<details><summary>repro</summary>

<fenced bash repro block + fenced observed-output block>
</details>
```

### Body rules

- A finding with more than one case is a claim and a list, never a paragraph. One line for the claim and its mechanism, then one nested bullet per case naming its condition and outcome. Put the cases where it does not bite beside the ones where it does.
- The Body has exactly two jobs: cross-cutting synthesis the per-line comments cannot carry, and every finding no single line owns, as a list per *Posted comments* in `skills/writing-style.md`. Below the list goes the clip showing the feature doing what the bullets say. A paragraph there is a finding that should have been anchored.
- A finding naming an edit is anchored on the line that gets edited, and every demonstrative in it points at that anchor. This timer, this map, this call carrying a link somewhere else is the symptom: the sentence wanted a second anchor and got a link instead.
- **Never pin a line the finding does not want changed.** An anchor reads as a request to edit that line, so a finding whose edit lands elsewhere sends the author at code it never disputed. Where the line to edit sits outside the diff the finding has no anchor at all, and it goes in the Body as a bullet carrying its own links, never on the nearest changed line.
- The Body is about the branch, never about the review. Two shapes fail it and both read as filler: the imperative, `Read the caption path`, which sets homework for the author who wrote that path; and the report, `This looked at the three token routes`, which names the reviewer's afternoon. Neither asserts anything that can be wrong, which is the tell. Write the problem no line owns, or the one property of the branch the anchored comments cannot carry between them.
- On a security fix, an advisory or an embargoed repository, post only what changes behaviour, the fix's coverage or the verdict. A Nit on a test's wording, a comment, a count or a name ships `SKIP` and stays here: noise on that thread costs the reviewers reading it.
- Post every finding the author should act on, and open with the one that changes what they do next. An action is a fix, a decision or an answer, and severity never gates it: a Nit asking for a concrete modification gets its own section. Never drop a real finding to make the review shorter; shorten the finding instead.
- **Every finding gets a section here, and the ones that will not go out get `SKIP`.** A finding kept in `claims.md` alone is one the user cannot send without rewriting it. Draft it as `## SKIP <path>:<line>` with the same text a posted section would carry, closing with one line saying why it is skipped, `Not posted: <reason>` as its own paragraph with a blank line above it, and let un-SKIPping be the whole decision. Run onto the finding's own line the reason reads as a third sentence of the comment, which is what the section would post if the marker came off. This covers what needs no action from the author, a check CI already reports, a cosmetic nit no enabled linter enforces, and a finding about a code comment's own wording.
- **A Critical or a Warning is never skipped as the same defect as another finding of the round.** Post both: the one whose line the diff holds is anchored there, and the one whose line sits outside the diff is a Body bullet opening on its band, carrying its own link.
- A measured defect on a line the diff touches is posted, whatever argument the measurement suggests against it. It never fires, it predates the branch, the branch only makes it worse: each of those is the finding. Reasoning from a defect to its own exemption is the failure, and Open questions hold what the reviewer could not decide, never what they decided not to send.
- Name the event beside the draft, never after it. The header's `Verdict:` line is the reviewer's judgement and does not move. What gets posted, APPROVE, COMMENT or REQUEST_CHANGES, is the user's call: show it with the text and let one word settle both.
- **The draft's `Event:` is what goes out.** Never soften it on the way to the forge: an `APPROVE` posted as a `COMMENT` because a past turn asked for one reads as the reviewer withholding approval. The event changes when they name the new one in the turn, and a stale default is raised as a question rather than resolved quietly. The one override is `post as an AI`, per *Posting*: the marker goes out as `COMMENT`, whatever the draft says.
- Never mention an anchored finding in the Body, in any form: no bullets, no recap, no pointer to it, no count.
- Do not re-describe the change or restate thread state.
- **Stateless: state the code's current property, never its history.** Out with the history go the round, a prior draft, a sibling pull request, a competing branch, how somebody else solved it, and every sha, message, ordering and count of what landed when; a comparison stays in `claims.md`. Where the branch's own sequencing is the finding, the finding is what the code does now and what a reader has to split to fix it. Search a finding for `this change`, `this fix`, `now`, `still` and `no longer` before it ships, and rewrite it on what the highlighted line does.
- Nothing about CI reaches the comment, in any check state. The one exception is the stale-base sentence named below.
- **The Body names what is broken, never what held, and never fills the field.** A check that passed, a mutation that reddened the right test, a suite that stayed green: each is the reviewer's working, and the author did not ask for it. It goes in `claims.md`, or in a collapsed `<details>` beside the finding it supports, and never in visible text. An affirmation carries no more: a review whose findings are all anchored ships an empty Body, which the submit call takes for `APPROVE` and an edit sets afterwards for the other two events.
- When a Body check asserts a property a committed test could assert, write the test instead.
- No sha pin in anything posted. The reviewed sha belongs in the draft's `Commit:` line, which the script never sends.

### General rules

- `Event:` defaults from the verdict: APPROVE → APPROVE, REQUEST CHANGES → REQUEST_CHANGES, NEEDS DISCUSSION and CLOSE → COMMENT. It is a default, not a lock: the user may post a lighter event than the verdict, and then the `Verdict:` line keeps the judgement while `Event:` records what went out. The `Event:` line carries it; the Body never restates it.
- Never review your own pull request. No verdict, no findings, no `self-review.md`: an author grading their own diff is read as talking to themselves. What the author posts instead is one inline comment per part a reviewer should open, saying why that line matters, on the line itself and never as a section of the body. What the diff read back turns up goes in the change's `plan.md`. If the user asks for one anyway, `Event: COMMENT`: GitHub rejects APPROVE and REQUEST_CHANGES on one's own pull request.
- Two defects where fixing one leaves the other are two sections, never one clause. The test is the author's next edit: if applying the first still ships the second, the second has its own anchor.
- Order findings by what the reader needs first: the one that makes the others legible leads, whatever its band, then Critical, Warning, Missing test, Nit, Suggestion; file order within a band.
- A finding that needs a third explanation leaves the comment. Mark the section `SKIP` with a line saying why; the explanation goes to `claims.md`.
- Never explain routine fixes: merge the base, regenerate assets, re-run a flaky job. A red check with a routine cause gets one short Body line, naming what is no longer readable rather than the fix.
- **A mistake in the pull request's own title or description never reaches the draft.** The author rewrites both from the findings, and a reader of the code sees nothing that correction changes. Where either is the only source of a claim, anchor the claim on the code carrying it: a change riding along unannounced is a finding about the change, never about the words that failed to mention it. What the title or the description got wrong stays in `claims.md`, and a section that cannot be re-anchored ships `SKIP`.
- Never tell the author to rebase. They meet the conflict the moment they try to merge, and a reviewer spending the body on it says nothing the branch does not already say. What a rebase costs, a behaviour it drops or a build it breaks, is a finding anchored on the line that carries it. Nothing else about the base branch reaches the comment. One exception: when the stale base is why the review is not an APPROVE, the Body says so in one line, because a withheld approval whose reason is unstated is the same defect in the other direction.

### Building each inline comment

1. Anchor. One `## <path>:<line>` section per finding, every severity; ranges `## <path>:<start>-<end>`. Line numbers reference the head commit, side RIGHT. Read those exact lines first, and anchor on the shortest run that shows the code the claim is about: GitHub prints the anchor and a few lines above it, so an anchor on a `func` line shows its doc comment and none of its body, and one on a whole block pushes the diff off the screen. Pick the switch, the guard or the list the sentence is about, and stop there. Validate every anchor against the diff hunks now, not at posting time: a line outside the diff is rejected and takes the whole review with it, so that finding belongs in the Body and the draft must say so. **Close the header with ` · <Band>`**, the verifier's band in the words *Calibration* in `skills/review.md` uses, Critical, Warning, Missing test, Nit, Suggestion or Test.
2. Opener. `Critical:` / `Nit:` / `Suggestion:` prefix matching the verifier's band, then the TL;DR. A Warning gets NO prefix. **A finding on code the diff did not introduce, reachable or worsened through it, opens `Related:` in front, `Related suggestion:` with a band**, so the author reads first that the highlighted line is the way in and not the cause. **The first clause names what the highlighted line does**, the `true` argument, the `init()`, the parameter, before any function the line does not show: a sentence opening on a symbol elsewhere in the file reads as anchored on the wrong line. A missing-test finding opens `Missing test:` plus the uncovered scenario. **A finding proposing an edit to test code opens `Test:`**, in place of its band on an inline comment and in front of a Body bullet, since a change confined to tests carries no production risk and the opener is what tells the author so before they read the line. No bracketed priority tags.
3. Sentences. One visible sentence, two only when the second carries an action the first does not; code blocks and `<details>` do not count; no headers, no bold. Order: gap and stake, evidence, fix sentence last. Over one: cut evidence, never the gap. What ships is the defect, the anchor and the repro: the reasoning, the prototyping cost and the verification pins stay in `claims.md`.
4. Fix sentence. Default none, per `skills/writing-style.md`. **A fix is stated only where this round applied it and ran it**: the leak closed, the case it must keep still passing, the related tests green, the run named in `claims.md`. A fix a judge proposed and nobody ran, one run on a sample of the files it covers, or one with two readings the author must choose between leaves the finding on the problem alone.
5. Links. Every named file or test, every behavioral claim, per *Links & citations* in `skills/review.md`.
6. Repro. Critical and Warning get a collapsed repro block when the claim is behavioral.

### Visible-text style

Governed by the *Posted comments* section of `skills/writing-style.md`. The rules below are the review-specific additions.

- Essentials only: the problem and why it matters. No stacked clauses, no symbol-chain walkthroughs, no scenario-painting.
- Lead with the specific gap. Never open by explaining the author's own code or restating what the change claims.
- **Every term in a finding is one a maintainer who has not seen the code can expand**, and a cut that leaves one they cannot has deleted the claim rather than shortened it. Name the expression, the guard or the call, never its position: `the line below` and `this comparison` have no referent under a range anchor, and a word coined to compress, a link that `names no package` for one pointing at a path no package occupies, reads as jargon the reader looks up and does not find.
- A latent-risk finding states the current safety in one clause and stops.
- State the position as the reviewer's own, in one line. This covers design and layering calls.
- A layer named is a symbol named. "on the model", "in the serializer", "at the view" tells the reader where the code is not, never what putting it there would cost. Name the class and the call that makes the claim true, `BaseModel.save()` running `full_clean()` on every write for one, then the consequence in the same sentence.

### Answering a finding on your own pull request

The register is the shortest thing that settles it. A bot posts each finding
twice, once inline and once as a summary comment, and the reply belongs in the
inline thread, where it nests under the finding it answers: a summary comment
cannot be threaded at all. A finding that holds is fixed in the same turn rather than
reported back, and the bullet is `Fixed: <sha>`. One that does not gets the
sentence that refutes it and a collapsed run. Never argue a finding across a
paragraph: the reader is deciding whether to look, not reading the analysis.
Close the reply with one link, a range:
`https://github.com/<owner>/<repo>/pull/<n>/changes/<base>..<head>` with full
shas, base being what the reviewer last saw, so one range covers work spread
over several commits, and the anchor text is the two shas, seven characters
each. A bare sha outside a link renders as plain text on another repository.

### Repros (comment.md deltas)

- Attempt a repro for every Critical and Warning before drafting. No run proof: word it as an observation, never "I ran X". Source-visible facts: cite the anchor, drop the block.
- A repro lives in exactly one file: the draft owns it for findings anchored there; `claims.md` states the result and links it. Line-specific repros stay with their comment; suite-wide ones go in a Body `<details>` block, pointed to.
- A missing-test finding carries ready-to-add cases in a collapsed `<details><summary>test cases</summary>` block, in the file's own test style, paste-ready.
- A table or repro no remaining sentence cites leaves the comment. Tightening a finding takes its number with it, and the evidence block outlives the claim it was proving: it then reads as support for an argument nobody is making. Re-read every collapsed block against the visible text on each revision, and move the orphan to `claims.md`.

### Rounds & regeneration

- Before offering a draft to the user, measure its target and offer the live ones alone. Merged, closed, or already carrying a review from this reviewer means the draft is a record rather than a pending action, and a handover listing it asks them to decide something they decided already. Write the answer into the draft's `Status:` line in the same turn, so the next session reads the file instead of the API.
  ```bash
  gh api repos/<repo>/pulls/<n> --jq '"\(.state) \(.merged)"'
  gh api --paginate repos/<repo>/pulls/<n>/reviews --jq '.[]|select(.user.login=="<login>")|.state'
  ```
- **A second pass over a head whose review is already posted writes its own draft**, `comment_<model>-take2.md` beside the first, and the posted file goes back byte-for-byte to what went out. GitHub refuses new inline comments on a submitted review, so folding new findings into the posted draft leaves a file that can neither post nor be re-posted.
- A draft embedding media hosted elsewhere is stale until that host is pushed: push it, then read the raw URL back per the picture rule in `skills/writing-style.md`.
- Port carried findings verbatim; change only shas, repro URLs, and stale anchors. No round-relative phrasing.
- A carried finding whose thread from an earlier round is still open is not posted again, as neither a new inline section nor a reply restating it: the thread the author has not answered is already where it waits. The Body names it unresolved in one clause and stops, each carried finding a hyperlink on its own words pointing at its thread, so one click reaches the discussion instead of a second copy of it. Two clauses means two findings, and a paragraph there is the finding posted twice. List the open threads before showing the draft, `gh api --paginate repos/<repo>/pulls/<n>/comments --jq '.[]|select(.user.login=="<login>" and .in_reply_to_id==null)|"\(.id) \(.path):\(.line)"'`, and drop every section anchored on one.
- A SKIPped finding stays SKIPped when ported, with a one-line note, until the user un-SKIPs it. Before regenerating, read the existing file and preserve every surviving `SKIP` marker.

### Posting

- **Before rewriting anything already posted, a review, a comment or a pull request body, read the live text back and merge the draft over it**: `gh api repos/<repo>/pulls/<n> --jq .body`, `pulls/comments/<id>` or `pulls/<n>/reviews/<id>`. An edit made in the GitHub interface is invisible here, and a rewrite from a stale draft reverts it. Bring the draft's own tree to its remote first, `git fetch` and `git rev-list --count HEAD..origin/main` reading 0: the posting session wrote the `Posted:` line and the `[posted]` anchors back there, and a draft edited behind it has neither.
- `./scripts/post-review.sh <draft>` posts it as one pull request review, never a plain issue comment: it validates every anchor against the current diff, folds the comments into a pending review the user already has on the target, reacts to each `Already raised:` duplicate, and writes `Posted: <review-url>` under the title and `[posted](<comment-url>)` on each anchor. Run `--dry-run` first when anything about the draft is uncertain.
- **One posted review per head.** A pass finished after the post goes as replies in the threads it touches, or waits for the head to move; a second review on an unchanged head is the same review read twice. A finding the first pass missed and no thread carries goes as one reply on the review's own thread, never a new review.
- **`post as an AI` sends the draft with `> AI review, <model>, <preset> review, [skills](https://github.com/davd-gzl/skills) · [overview](<url>) · Status: <verdict>` as the Body's first line and `COMMENT` as the event**, whatever the verdict. `--as-ai` builds that string: it reads the visibility of the repository holding `overview.md`, carries the link at that repository's default branch when it is public and omits it when it is private. The model and preset come from the draft's `Model:` line. **Nothing is composed beside the marker**, and words the user typed for it go on its line behind a second `·`, verbatim. The word covers the one post it was said for, and it is the only phrase that puts an AI marker in a posted string.
- A `gh` write refused 403 `Resource not accessible by personal access token` is a missing scope: never retry or work around. Do everything the scope allows first. The script records the refused command in the draft's `Status:` line; end the reply with `post <github url of the artifact>` alone on its own line, and for a refusal larger than one post name the repo, the branch, both shas, the steps in order, and which token was refused where.
- **Post a subset by band or by anchor, never by editing the draft**: `--band 'Warning,Critical'` posts the sections whose header carries one of those bands, `--only <path>:<line>,<path>:<line>` posts the named ones, and `--list` prints every section with its band and first sentence for the user to choose from. What the selection holds back is reported as held, keeps its text and its band, and goes out unchanged in a later post once the head moves.
- The word `post` covers every verdict, APPROVE included, with no extra confirmation.
- A draft already carrying `Posted:` is re-posted by rewriting that review in place, by hand since the script refuses it: the `updatePullRequestReview` GraphQL mutation on the review's `node_id` for the Body, `gh api graphql -f query='mutation($id:ID!,$b:String!){updatePullRequestReview(input:{pullRequestReviewId:$id,body:$b}){pullRequestReview{state}}}' -f id=<node-id> -F b=@<body-file>`, since the REST `PUT` on the review answers 404 for its own author, and `gh api -X PATCH repos/<repo>/pulls/comments/<comment-id> -f body=<body>` per anchor, the ids from the `Posted:` and `[posted]` URLs; the event cannot change, and an anchor with no `[posted]` link aborts the re-post rather than opening a second review, since comments cannot be added to a submitted review.
- Commit the written-back draft in the same turn as the post, never later, and name its push as pending: the `Posted:` line is what makes a re-post rewrite the existing review, and another session reads it only once `push` sends it. Before any post, check whether the target already carries a review from this author and reconcile the draft first; the script warns and continues.

### Final check

Verify each line before handing over:

1. The header carries `Verdict:`, `Model:`, `Commit:` and `Overview:`, and the overview link resolves. `Model:` names the models and efforts `./scripts/review-retro.py <workflow-dir> --served` prints, since the config names what was asked for and not what ran.
2. The Body names at most three checks, each runtime-only, none CI-visible, none recapping anchored findings.
3. No repro block has a passing run as its only output.
4. Every non-Warning inline comment opens with its band; Warnings open with the TL;DR. Every comment asks for a fix, a decision, or an answer, and carries no fix sentence its problem statement already implies.
5. `./scripts/prose-check.py <draft>` counts the sentences per section and the Body's lines; one section per distinct action. Count the `<details>` blocks too, and delete the one attached to a merge conflict or to anything the author confirms by opening the app.
6. No verdict restating the `Event:` line, no bold, no imported emphasis caps, every `skills/writing-style.md` rule holds.
7. Every `Suggestion:` was applied in a worktree and run both ways, the case the finding is about and the case the current code already handles. Run the path carrying no user action, the page load, the reconnect, the re-render: a guard exists for that path, the finding is about the path with a click in it, and dropping the guard is how a fix becomes the bug it was written against. Name every result in `claims.md`.
8. Every finding names the set it holds for, and the band follows the size of that set. One example value standing in for the set understates both: "a French browser" where every non-English browser fails is a Critical wearing a Warning's clothes.
9. Every embedded image resolves at its raw URL and its bytes match the file on disk.
10. Open every link and read the lines it lands on: each must contain the number, symbol, or behavior claimed. `./scripts/round links` proves that every link resolves at the pinned ref and that its range fits the file; the claim on the lines is read.
11. Re-run every claim against the tree before the draft is shown, including the ones carried from an earlier revision. Print the code beside the sentence.

Then the text pass, once, over the finished draft. An edit after the text pass gets the parent's own pass over the edited section, its cited lines re-read, and a run only where the edit adds or changes a claim, that run's row going to `claims.md`.

- **The text pass**: one agent with the draft, `overview.md`, the checkout and *Visible-text style* in `skills/review-comment.md`, running the three steps of *Text pass* in `skills/review.md`. Its one delta: the per-link row saying whether the landed lines carry the claim stays in `links.md` and never enters `claims.md`, which a reader opens for the findings.
