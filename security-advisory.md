---
name: security-advisory
description: Verify a security finding against merged or deployed code by execution, and write it up for private disclosure. Produces an advisory with an executed repro, a CVSS vector, a plain-language summary, and a body ready to paste into the project's advisory form.
argument-hint: <finding description | audit-finding-id>
---

# Security advisory

**Input:** `$ARGUMENTS`, a finding as free text or the id of one an audit
recorded, whose analysis lives in the private disclosure repository.

Read the project's `SECURITY.md` and its `AGENTS.md` before anything else: the
channel, the embargo and the security semantics the finding turns on are there.

## Disclosure gate, settled before a line is written

Deployment decides, never severity.

- Against an **open pull request's own diff**: ordinary review output. Use
  `skills/review.md` and stop here.
- Against **already-merged or deployed** code: a disclosure. Every artifact stays
  out of any public tree, the decision goes to the user first, and the output
  lands in the private disclosure repository whose path comes from the user.
  Never write that repository's name into a public file, commit message or path.
  A public issue and a public fix pull request telegraph the vector equally, and
  a project whose `SECURITY.md` forbids the issue is not asking about the pull
  request.

## Verify by execution, never by reasoning

1. Throwaway worktree at the tip, at an absolute path: a relative one lands the
   worktree under the checkout while the files go elsewhere.
   ```bash
   git -C <checkout> worktree add <absolute-scratchpad>/<repo>-<slug> <canonical-remote>/<default-branch>
   ```
2. Write the exploit in the harness the project already uses for that surface,
   with the attacker and the victim as separate artifacts, printing the state
   before and after the attack.
3. Run it from the module or package root the project's own tests run from.
4. Read the numbers. Nothing moved means the finding is wrong: drop it, never
   retrofit a rationale onto it.
5. Instrument identity when the mechanism turns on who the caller is: print every
   actor and every resolved caller, so the resolution is shown and not assumed.
6. A harness convention can make a correct exploit report failure, a missing
   golden output being the common one. Read what failed before reading it as the
   exploit failing.
7. Remove the worktree, `git worktree remove --force`, and confirm the checkout
   carries no leftover artifact from the repro.

## Verify every anchor against the tip

Re-derive each `file:line` with
`git show <canonical-remote>/<default-branch>:<path> | grep -n`, never from a
remembered grep. A stale line number lands a maintainer on unrelated code.

## Sharpen the finding

Show the guards that hold before naming the crack, so the finding cannot be
dismissed with "but X already checks Y". State the precondition exactly: "the
victim must call the attacker's code directly", never "any interaction". When
asked whether it is really a bug, re-run with full instrumentation instead of
re-arguing.

## Advisory format

One file per finding, in the private repository, in this order:

- `# <impact title>`, what an attacker achieves, plain, no jargon.
- `**Severity:**`, `**Affected:**` naming the component first and then the class
  it generalizes to, and `**Status:**` naming the branch it was verified against.
- `## Summary in plain language`, two to four sentences a non-technical reader
  gets, no code.
- `## Summary`, the mechanism in prose.
- `## Details`, the minimum code, with verified anchors.
- `## Proof of concept`, the trimmed repro and the captured output.
- `## Reach`, every affected surface and consumer, as a table with anchors.
- `## Impact`, who is exposed and how large.
- A CVSS 3.1 vector, stating which axis is debatable and why.

Leave out remediation and provenance unless the user asks. Do not pin a commit
hash unless asked; name the branch.

## Second-model review

Before finalizing, dispatch one agent on another model, synchronously, to verify
each claim and each anchor against the canonical branch and to propose cuts.
Re-verify anything it flags yourself and apply only what survives.

## Deliver

- Save the advisory and the repro artifacts in the private repository. Commit on
  approval, push on the literal word `push`.
- The paste-ready body strips the H1, `tail -n +2 <file>`: the form carries the
  title separately.
- One report per finding, through the project's own private channel, never a
  public issue. Triage access does not create advisories through the API, so the
  user pastes the body and the vector into the form.

