---
name: project-background
description: Use when the user asks for full background on a repository, a "how X works" doc for someone who has never read its code, or the same doc as one already made for another project. Produces a living doc pinned to one upstream commit, every claim linked to the line that proves it, with an architecture diagram and screenshots of the running app. A project's own user-facing documentation site is skills/docs-site.md instead.
---

# Project background

The outline every such doc converges on, the middle sections named after the
product's own flows:

```
# How <project> works
<as-of date> · <author>
## TL;DR              what it is, the design choice the rest follows from, the pinned sha
## What it does       one captioned screenshot per feature, from the running app
## Words              each project term the doc uses, one line, in the reader's words
## The pieces         a diagram of the services and their calls, then a table: piece, code, stack, job
## <core flow>        one section per flow a user drives, end to end, as numbered steps
## Who can do what    roles and sharing, as a table of what each role adds
## Background work    every async job: when it runs, what it does
## Other entry points every door besides the browser, with the setting that opens it
## Configuration      the settings that change behaviour: default, effect
## Running it locally first boot, ports, logins, traps on a fresh machine
## Contributing       each CI job with its local command; commit and changelog rules; traps
## Repo map           where each kind of change lands
```

A sibling doc the user names sets the depth: read it whole first and match
its sections, then add what this project has and that one did not.

## Before the first section

- Resolve the repository before anything builds on its name: `gh api
  repos/<owner>/<name> --jq .full_name`. A name typed from memory can 404 under
  a sibling organisation, and the doc names the real one.
- Create the doc as the docs connector instructs, the outline above as pending
  blocks, before any research. Fill one section per call while the user watches.
- Clone the default branch and pin its head: every code link is
  `blob/<sha>/<path>#L<a>-L<b>`, and the TL;DR names the sha and its date. Clone
  where the container daemon can mount it when the app will be booted, which
  `./scripts/env-check.sh containers` answers.

## Measuring

- Every sentence comes from code read this session. The README, the
  contributing guide and `docs/` are claims to check against the code and the
  CI files, and a gap between them is stated as a finding: a rule the guide sets
  that no job enforces, a default the docs give that the settings contradict.
- A default is read from the settings line, never from the dev env file, which
  overrides it.
- A fact about people or history carries the result of the command that
  counted it: who merges, commits per merged pull request, changelog lines per
  pull request.
- **Before a sentence saying `never`, `only`, `every` or `the one` ships, list
  every exception the code holds and narrow the sentence to the scope that has
  none.** The TL;DR is where the absolute hides, and a later section then
  contradicts it.
- Before a line range goes into a link, print its first and last lines: a range
  copied from a grep is off by the decorator or the blank line above it.

## Pictures

- The pieces take a diagram drawn per the connector's diagram guide, looked at
  through its screenshot read before it stays.
- What it does takes screenshots of the app running at the pinned sha. Boot it
  per `skills/try.md`, moving any port another stack holds to one the project's
  auth config already whitelists, then reading every origin list back from the
  running containers, the bucket's CORS and the backend's trusted origins
  among them: an override that did not take shows up later as a 403 or a failed
  upload, never at boot.
- Seed through the app's own API from inside the signed-in page, so the
  session, the CSRF token and any signed upload behave as the browser's do, with
  invented names and contents and the project's own fixture users. Capture each
  screen headless with `./scripts/capture-web.mjs --script <walkthrough>`, with
  a first-run dialog turned off by its setting and dev-only overlays hidden.
- Open every screenshot before it is uploaded and retake the one whose screen
  shows a dialog, a blank preview or an error instead of the feature. Upload it
  per the connector's uploads guide under a caption naming the feature and the
  route it was taken on.
- A feature the local stack cannot show, a third-party service it needs, is
  named under the screenshots as not shown, with the reason.

## Editing the doc

- Change a link or a code span by replacing its whole block, with `ifHash` and
  `ifRev` from the last read. A `find` on part of a link's text duplicates the
  text, and a `find` matches without case, so a setting name also hits the
  lower-case path that contains it.

## Before calling it done

1. Links. Write every link the doc holds into `comment_doc.md` in an empty
   scratch directory and run `round links <dir> --repo <clone>`; exit 1 names
   each link whose file or range is missing. A `tree` link is checked with
   `git cat-file -t <sha>:<path>`.
2. Read the whole doc back as text, once, as a newcomer, and fix each sentence
   that needed a second read.
3. Hand the rendered text, the clone path and the sibling doc to an agent with
   no context of this work. It returns where a newcomer stumbles and which of
   these the doc misses, each grounded in a file it opened: sign-in and
   sessions, frontend structure and data fetching, the data model, every async
   job, every entry point, configuration, deployment and releases,
   translations, theming, analytics, quotas, the test layout and how to run one
   test. Apply what it finds and read the changed sections back.
4. Run the Pass of `skills/writing-style.md` over the result.

A trap the boot or the measuring cost goes into `projects/<repo>/AGENTS.md`
where the project has one, with its symptom, per `skills/authoring.md`.
