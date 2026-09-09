---
name: pr-body/several-changes
description: The pull request body for several independent changes sharing one pull request. Read through ./scripts/skill pr-body/several-changes once skills/pr-body.md has picked this shape.
---

# Several independent changes

One `### <symbol>: <one-line diagnosis>` section per change, separated by `---`, each readable alone. About 150 words per section, a target and not a minimum.

- Two or three framing paragraphs first: what the changes share and what none of them is, in the reader's terms. Then a one-line bridge counting what follows.
- Each section carries its own symptom, mechanism and fix as a property of the new code, and a diagram where the reader would otherwise assemble the shape in their head, per *Diagrams* in `skills/pr-body.md`.
- What was proved goes in the section it belongs to. Where several sections share one method, one closing section names the method once and gives one row per section.
- A section naming another change, in this pull request or another, says what the two have in common in one sentence and stops.

Why: a reviewer reads the section for the file they own and skips the rest, so a section that depends on its neighbour is read without it.

## Example

```markdown
Eight tests fail intermittently and pass locally, four of them seen on CI. None is caused by the pull request it failed on; each sits outside that pull request's diff, and one is in a package that does not depend on the changed one. They are pre-existing races that only surface when the runner is loaded.

Three are races in the test itself. The other five report a race in consensus, where a proposer can prevote nil for the block it has just signed.

---

### TestProposeValidBlock: the proposer times out on its own proposal

`enterPropose` schedules the propose timeout, then `decideProposal` signs the proposal and pushes it onto `internalMsgQueue`. `receiveRoutine` reads the queue and the timeout ticker in one `select`, so once the timeout elapses both arms are ready and Go picks between them at random:

    enterPropose
    ├── scheduleTimeout(TimeoutPropose)  ──────────► tick ready after 500ms
    └── decideProposal ─► proposal + parts on internalMsgQueue

    receiveRoutine select
    ├── internalMsgQueue ─► proposal completes, step Propose → Prevote, tick dropped
    └── timeoutTicker ────► enterPrevote with ProposalBlock still nil
                            ↑ the proposer prevotes nil for the block it just signed

`receiveRoutine` now handles the messages already queued when it read the tick, before the tick moves the step, so a proposal this node signed is never overruled by the timeout waiting for it. The count is taken once and not refreshed: handling one internal message can queue the next, and a node making progress would otherwise keep the queue non-empty across heights. A production node gives the propose step three seconds and only loses that race when its consensus goroutine stalls for the whole step; a test node gives it 500ms, which a loaded runner reaches.

---

### TestNodeBootWithInitialHeight: asserting on a value that is still moving

It checks that a chain configured to start at height 100 starts there rather than at 1. It waited on Ready(), which only means some block arrived, and then read the block store:

    block 100 committed
    Ready() fires
                            <- test goroutine waits to be scheduled
    block 101 committed
    BlockStore().Height() -> 101, expected 100

Observed values ranged from 101 to 105. The test now records the height carried by the first NewBlock event, which is fixed at the moment consensus commits the block. finalizeCommit saves the block before firing the event, so that height is still a committed block.

---

### How each was proved

The initial height test went from 36 failures in 50 runs under load to 100 passes in 100.

Forcing `TimeoutPropose` down to one microsecond makes the tick ready every time, which turns the consensus race into a coin flip per round and gives a clean before and after. Six runs of each test without the `receiveRoutine` change and six with it:

                                            failures before   after
    TestProposeValidBlock                          4/6         0/6
    TestStateLockPOLSafety1                        2/6         0/6

Each test still fails against a build with its fix reverted, so none of them guards nothing.
```

Provenance: the body of [gno#6006](https://github.com/gnolang/gno/pull/6006), cut from four sections to two and the proof section to the rows those two need; its diagrams sit in fenced blocks there, indented here so the example stays one block.
