---
name: review-comment
description: Use when drafting, regenerating, or posting comment_<model>.md, the GitHub artifact a review ships. Extends skills/review.md with the body rules, the inline-comment shape, the final check, and the posting gate.
---

# The review comment

`comment_<model>.md` is the deliverable and the review file is the record, which
holds the evidence, the arithmetic and the rejected attacks. Draft this first and
spend the effort here: a finding that changes what the author does and lives only
in the review file has not been reported, because the author never opens that
file. Where the two disagree on wording, this one is right and the review file
follows it.

Draft in the round directory beside the review file, same `<model>`. Visible prose follows the *Posted comments* section of `skills/writing-style.md`. The user prunes by hand: `SKIP` prefixed to a header, `## SKIP <path>:<line>`, drops the comment. Never delete a dropped comment; the marker survives regeneration.

A target with no PR, a branch or a repository-level failure, gets a GitHub issue draft in the same filename: `Target:` and `Event: ISSUE` in place of the PR header, then `## Title`, `## Body`, and the anchored `## <path>:<line>` sections posting as plain headers inside the body. Each section still runs 1-3 sentences and closes with fixed-on-branch or left-out and why. Post with `gh issue create -R <repo> --title ... --body-file ...` under the same `post` gate.

Before writing a `Full review:` link into anything posted, check this repo's visibility with `gh repo view <this-repo> --json visibility`. Private: carry no link, inline the substance instead.

Auto-SKIP duplicates: when another reviewer already raised a finding, prefix its header with `SKIP` while drafting, attribute the reviewer in the review file, and make `Already raised: <comment-url>` the section's first body line. When a section bundles an already-raised finding with a novel one, split it so the novel part posts. Where the raised finding is one case of a broader one being posted, name that case in the broader sentence and link it to the original instead of splitting.

Format:

```markdown
# Review: [#<number>](https://github.com/<repo>/pull/<number>)
Event: APPROVE | REQUEST_CHANGES | COMMENT

## Body
<One-line assessment, then one-sentence bullets for unanchored findings only. When clean: "Looks good." plus one CI-invisible check, and nothing else.>

Full review: <link to the review file in this repo>

## <path>:<line>
<1-3 sentences: the problem and why it matters>

<details><summary>repro</summary>

<fenced bash repro block + fenced observed-output block>
</details>
```

### Body rules

- A finding with more than one case is a claim and a list, never a paragraph. One line for the claim and its mechanism, then one nested bullet per case naming its condition and outcome. Put the cases where it does not bite beside the ones where it does.
- The Body has exactly two jobs: cross-cutting synthesis the per-line comments cannot carry, and every finding no single line owns. Write those as a list, one bullet per problem, each bullet carrying its own links so a reader connects a claim to the line it rests on. Below the list goes the clip showing the feature doing what the bullets say. A paragraph there is a finding that should have been anchored.
- **A finding naming an edit is anchored on the line that gets edited, and every demonstrative in it points at that anchor.** This timer, this map, this call carrying a link somewhere else is the symptom: the sentence wanted a second anchor and got a link instead.
- **The Body is about the branch, never about the review.** Two shapes fail it and both read as filler: the imperative, `Read the caption path`, which sets homework for the author who wrote that path; and the report, `This looked at the three token routes`, which names the reviewer's afternoon. Neither asserts anything that can be wrong, which is the tell. Write the problem no line owns, or the one property of the branch the anchored comments cannot carry between them.
- **Never write a Body line whose only job is to fill the field**: no line that counts the inline comments or points at them. Anchor what is about code; the Body carries what is about the branch and survives the two rules below, which take a stale base, a rebase and a conflict out of it.
- **An empty Body is refused at submit and accepted on edit.** The submit call rejects an empty string for REQUEST_CHANGES and COMMENT; a later edit of the same review sets it to empty and holds. A review whose every finding is anchored ships with its shortest true sentence and is cleared afterwards.
- **Post every finding the author should act on, and open with the one that changes what they do next.** An action is a fix, a decision or an answer, and severity never gates it: a Nit asking for a concrete modification gets its own section. What stays behind in the review file is what needs no action from them: a check CI already reports, a finding already raised by someone else. Never drop a real finding to make the review shorter; shorten the finding instead.
- **A measured defect on a line the diff touches is posted, whatever argument the measurement suggests against it.** It never fires, it predates the branch, the branch only makes it worse: each of those is the finding. Reasoning from a defect to its own exemption is the failure, and Open questions hold what the reviewer could not decide, never what they decided not to send.
- **Name the event beside the draft, never after it.** The review file's verdict is the reviewer's judgement and does not move. What gets posted, APPROVE, COMMENT or REQUEST_CHANGES, is the user's call: show it with the text and let one word settle both.
- Never mention an anchored finding in the Body, in any form: no bullets, no recap, no pointer to it, no count.
- Do not re-describe the change, list what passed, narrate the review process, or restate thread state.
- Stateless, like every inline comment: never name a round, never frame current code as a fix relative to a prior draft. State the code's current property, not its history.
- **Nothing about CI reaches the comment, in any check state.** The one exception is the stale-base sentence named below.
- A CI-invisible check must pass the verification rule in `skills/writing-style.md`; one that fails never appears. Nothing runtime-only checked: no verification line at all.
- At most three checks, the strongest. State each as an action and its result, never as a characterization. When naming a revert, describe the concrete edit and tie cause to effect in one chain.
- When a Body check asserts a property a committed test could assert, write the test instead.
- **No sha pin in anything posted.** The reviewed sha belongs in the review file's metadata.

### General rules

- `Event:` defaults from the verdict: APPROVE → APPROVE, REQUEST CHANGES → REQUEST_CHANGES, NEEDS DISCUSSION and CLOSE → COMMENT. It is a default, not a lock: the user may post a lighter event than the verdict, and then the review file keeps the verdict while the draft records what went out. The `Event:` line carries it; the Body never restates it.
- An own-PR target is not posted at all. If the user insists, `Event: COMMENT` whatever the verdict: GitHub rejects APPROVE and REQUEST_CHANGES on one's own PR.
- **Two defects where fixing one leaves the other are two sections, never one clause.** The test is the author's next edit: if applying the first still ships the second, the second has its own anchor, so that fixing the headline defect does not close the comment on a defect that survives it.
- Order findings by what the reader needs first: the one that makes the others legible leads, whatever its band, then Critical, Warning, Missing test, Nit, Suggestion; file order within a band.
- **A finding that needs a third explanation leaves the comment.** Mark the section `SKIP` with a line saying why and keep it in the review file.
- Never explain routine fixes: merge the base, regenerate assets, re-run a flaky job. A red check with a routine cause gets one short Body line, naming what is no longer readable rather than the fix.
- **Never tell the author to rebase.** They meet the conflict the moment they try to merge, and a reviewer spending the body on it says nothing the branch does not already say. What a rebase costs, a behaviour it drops or a build it breaks, is a finding anchored on the line that carries it. Nothing else about the base branch reaches the comment. One exception: when the stale base is why the review is not an APPROVE, the Body says so in one line, because a withheld approval whose reason is unstated is the same defect in the other direction.

### Building each inline comment

1. **Anchor.** One `## <path>:<line>` section per finding, every severity; ranges `## <path>:<start>-<end>`. Line numbers reference the head commit, side RIGHT. Read those exact lines first; the anchor covers exactly the lines the sentence talks about. Validate every anchor against the diff hunks now, not at posting time: a line outside the diff is rejected and takes the whole review with it, so that finding belongs in the Body and the draft must say so.
2. **Opener.** `Critical:` / `Nit:` / `Suggestion:` prefix matching the review file's band, then the TL;DR. A Warning gets NO prefix. A missing-test finding opens `Missing test:` plus the uncovered scenario. No bracketed priority tags in comment.md.
3. **Sentences.** One visible sentence, two only when the second carries an action the first does not; code blocks and `<details>` do not count; no headers, no bold. Order: gap and stake, evidence, fix sentence last. Over one: cut evidence, never the gap. What ships is the defect, the anchor and the repro: the reasoning, the prototyping cost and the verification pins stay in the review file.
4. **Fix sentence.** Default none, per `skills/writing-style.md`.
5. **Links.** Every named file or test, every behavioral claim, per *Links & citations*.
6. **Repro.** Critical and Warning get a collapsed repro block when the claim is behavioral.

### Visible-text style

Governed by the *Posted comments* section of `skills/writing-style.md`: state the fix or the defect in the fewest words, cut every clause the fix already implies, no process words. The rules below are the review-specific additions.

- Essentials only: the problem and why it matters. No stacked clauses, no symbol-chain walkthroughs, no scenario-painting.
- Do not re-prove the claim in visible text; mechanism and secondary evidence go in the repro block or the full review.
- Lead with the specific gap. Never open by explaining the author's own code or restating what the change claims.
- A latent-risk finding states the current safety in one clause and stops.
- Lowercase a source's emphasis caps in prose; caps survive only in code spans.
- **Never post a question.** State the position as the reviewer's own, in one line. This covers design and layering calls.
- Link the full review inside an inline comment only when the details block is not enough.

### Repros (comment.md deltas)

- Attempt a repro for every Critical and Warning before drafting. No run proof: word it as an observation, never "I ran X". Source-visible facts: cite the anchor, drop the block.
- A repro lives in exactly one file: comment.md owns it for findings anchored there; the review file states the result and links it. Line-specific repros stay with their comment; suite-wide ones go in a Body `<details>` block, pointed to.
- A missing-test finding carries ready-to-add cases in a collapsed `<details><summary>test cases</summary>` block, in the file's own test style, paste-ready.
- **A table or repro no remaining sentence cites leaves the comment.** Tightening a finding takes its number with it, and the evidence block outlives the claim it was proving: it then reads as support for an argument nobody is making. Re-read every collapsed block against the visible text on each revision, and move the orphan to the review file.

### Rounds & regeneration

- **Before offering a draft to the user, measure its target and offer the live ones alone.** Merged, closed, or already carrying a review from this reviewer means the draft is a record rather than a pending action, and a handover listing it asks them to decide something they decided already. Write the answer into the draft's `Status:` line in the same turn, so the next session reads the file instead of the API.
  ```bash
  gh api repos/<repo>/pulls/<n> --jq '"\(.state) \(.merged)"'
  gh api --paginate repos/<repo>/pulls/<n>/reviews --jq '.[]|select(.user.login=="<login>")|.state'
  ```
- Update comment.md whenever the review changes; it never lags.
- **A draft embedding media hosted elsewhere is stale until that host is pushed.** Push it, then compare the raw URL's byte count against the file on disk. The host's API answers immediately; the raw URL lags minutes.
- Port carried findings verbatim; change only shas, repro URLs, and stale anchors. No round-relative phrasing.
- A SKIPped finding stays SKIPped when ported, with a one-line note, until the user un-SKIPs it. Before regenerating, read the existing file and preserve every surviving `SKIP` marker.
- When the head advanced past the reviewed commit: diff `<reviewed-sha>..<head>`, drop findings that diff fixed, re-run remaining repros on the new head, re-verify every anchor.

### Posting

- Never without the literal word `post` or `upload` in the current turn; `push` covers git push only. The same gate covers mutating already-posted content: update the draft, show the exact new text, touch GitHub only after approval.
- A `gh` write refused 403 `Resource not accessible by personal access token` is a missing scope: never retry or work around. Record the refused command in the artifact's `Status:` line and end the reply with `post <github url of the artifact>` alone on its own line.
- The word `post` covers every verdict, APPROVE included: post an approving review on the same word as any other, with no extra confirmation. A post still always needs the word; never auto-post.
- Post every verdict as a PR review, never a plain issue comment: `gh api repos/<repo>/pulls/<number>/reviews -f event=<EVENT> -f body='...'`, inline comments as `comments[]` entries with `path`, `line`, `side=RIGHT`, `body`.
- **A pending review the user already has on the target takes the draft's findings, and the two go out as one review.** GitHub folds new comments into it rather than opening a second, so the draft joins their unsent line rather than displacing it. Never submit theirs alone, and never ask them to clear it first. `POST /repos/<repo>/pulls/<n>/comments` cannot append: it opens a review of its own and answers `422 user_id can only have one pending review per pull request`. Add each anchor through GraphQL `addPullRequestReviewThread` against the review's `node_id`, then `POST /repos/<repo>/pulls/<n>/reviews/<review-id>/events` with the event and the body submits both.
  ```bash
  gh api graphql -f query='mutation($rid:ID!,$path:String!,$line:Int!,$body:String!){addPullRequestReviewThread(input:{pullRequestReviewId:$rid,path:$path,line:$line,side:RIGHT,body:$body}){thread{id}}}' -f rid=<node-id> -f path=<path> -F line=<n> -f body=<body>
  ```
- Comments cannot be added to a review already submitted. A draft carrying a `Posted:` line re-posts by rewriting that review in place, so every anchor it holds must already carry a `[posted]` link; one that does not aborts the re-post rather than posting a second review.
- A reaction on the review body itself is not in the REST reactions API. Resolve the node id, then react through GraphQL, skipping any target where `viewerHasReacted` is already true:
  ```bash
  gh api repos/<repo>/pulls/<n>/reviews --jq '.[] | select(.id==<id>) | .node_id'
  gh api graphql -f query='mutation($id:ID!){addReaction(input:{subjectId:$id,content:THUMBS_UP}){reaction{content}}}' -f id=<node-id>
  ```
- Thumbs-up acknowledged duplicates in the same `post`, from each SKIPped section's `Already raised:` URL. Inline thread: `gh api -X POST repos/<repo>/pulls/comments/<id>/reactions -f content=+1`; top-level: `.../issues/comments/<id>/reactions`. Skip targets already reacted to.
- After a successful post, write the URLs back: `Posted: <review-url>` under the title, `[posted](<comment-url>)` on each anchor. Commit and push in the same turn as the post, never later: the `Posted:` line is what makes a re-post rewrite the existing review instead of adding a second one. Before any post, check whether the target already carries a review from this author and reconcile the draft first.

### Final check

Verify each line before handing over:

1. The Full review line points at this repo and resolves.
2. The Body names at most three checks, each runtime-only, none CI-visible, none recapping anchored findings.
3. No repro block has a passing run as its only output.
4. Every non-Warning inline comment opens with its band; Warnings open with the TL;DR. Every comment asks for a fix, a decision, or an answer, and carries no fix sentence its problem statement already implies.
5. Count, do not judge: one visible sentence per section, one line or nothing in the Body, one section per distinct action. Count the `<details>` blocks too, and delete the one attached to a merge conflict or to anything the author confirms by opening the app.
6. No verdict restating the `Event:` line, no bold, no imported emphasis caps, every `skills/writing-style.md` rule holds.
7. Every `Suggestion:` was applied in a worktree and run both ways, the case the finding is about and the case the current code already handles. Run the path carrying no user action, the page load, the reconnect, the re-render: a guard exists for that path, the finding is about the path with a click in it, and dropping the guard is how a fix becomes the bug it was written against. Name every result in the review file.
8. Every finding names the set it holds for, and the band follows the size of that set. One example value standing in for the set understates both: "a French browser" where every non-English browser fails is a Critical wearing a Warning's clothes.
9. Every `## <path>:<line>` header carries its `[gh]` link to the branch under review.
10. Every embedded image resolves at its raw URL and its bytes match the file on disk.
11. Open every link and read the lines it lands on: each must contain the number, symbol, or behavior claimed, and every external link must resolve at the pinned ref.
12. **Re-run every claim against the tree before the draft is shown, including the ones carried from an earlier revision.** Each rewrite moves a fact off the line that supported it, and a sentence that was true in the paragraph it came from goes out as a claim nobody checked. Print the code beside the sentence: `boots clean` was wrong for a config the guard rejects, and `prewarm already loads Silero` holds only where the flag it sits behind is on.

Then two QA agents, re-run on every regeneration of comment.md:

- **Concision recheck**: one `Agent`, `subagent_type: general-purpose`, given the comment.md path, the checkout path, and the *Visible-text style* rules. Only question: can any line be shorter or clearer without dropping fact, stake, or fix? Apply the rewrites that hold against the cited lines.
- **Citation audit**: one `Agent`, `subagent_type: general-purpose`, given both file paths and the checkout. For every link it fetches the target and returns only anchors whose lines do not contain the claim, plus unresolvable external links. It skips the `Full review:` self-link, which 404s until pushed. Fix each returned finding.

