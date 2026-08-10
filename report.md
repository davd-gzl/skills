---
name: report
description: Generate or update a periodic status report over a set of repositories. Gathers data via script, carries context forward period to period, and produces the report only after the user has edited the context.
argument-hint: "[date expression]"
---

# Report

A periodic report is three files in a directory named by the period's end
date: `context.md`, the user-editable input; `report.md`, the generated
output; and a ping draft when stale items need chasing. The consuming
workspace defines the team, the repositories, the categories and the markers;
this file defines the mechanism.

**Input:** `$ARGUMENTS`, an optional date expression for the end date, default
today. Parse to YYYY-MM-DD.

## Workflow

1. **Gather data** with the workspace's script into a JSON file. Verify every
   listed handle first: a renamed handle returns zero results with no error,
   silently dropping that member. On a missing-entry complaint, check the
   handle before anything else.
2. **Load the previous period's context**, found by directory-name sort,
   never by mtime. It supplies carry-forward priorities and manual notes
   only, never the new-this-period markers. A previous directory older than
   one period gets flagged to the user before anything is produced.
3. **Build the new `context.md`**: one line per open item,
   `` <number> [priority]: [note] - `<title>` ``. A manual entry carried
   forward always beats an auto-detected status; auto-detection follows the
   workspace's first-match table, and a bare line is the fallback, never a
   guess. Save it, present it, and **wait for the user's edits**. Never
   generate the report before this gate clears.
4. **Produce `report.md`**, re-reading `context.md` from disk first, even
   after approval: the user edits between steps, and the on-disk file is the
   source of truth. Sections come from the workspace's category rules; empty
   category sections are omitted. Never fabricate an entry.
5. **Save and present.** Write both files, show the report, and name what is
   new and what disappeared since the previous period.
6. **Draft the ping** for stale items: plain markdown, oldest first, the
   empty set stated as `None.`. Present the block; nothing posts itself.

## Rules

- The highlight block comes from the user each period. Ask when the request
  does not carry it, fall back to the previous report's block, and reproduce
  entries verbatim: refresh the markers, never add, drop, reorder or retitle.
- The previously generated report is the source of truth for flaky live
  fields; hit the live API only for what the JSON cannot carry.
- Deterministic ordering everywhere: marker tiers between groups, one stated
  tie-break inside them.
