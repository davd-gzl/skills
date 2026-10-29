---
name: docs-site
description: Use when writing, restructuring or reviewing a project's user-facing documentation site, its home page, guides, how-it-works page, FAQ, install guides, and the screenshots and GIFs in them. Covers the shape of the site and of each page, the pictures, and checking every claim against the code. Prose rules stay in skills/writing-style.md.
---

# A documentation site

The shape a page converges on, a guide for one kind of reader:

```markdown
# Hosting a large meeting

For teachers and anyone running a meeting with many people.

## Before the meeting

<figure markdown="span">
  ![Room settings](../assets/room-settings.png)
  <figcaption>Settings → Room: who can join</figcaption>
</figure>

Sign in before you create the room, so you own it. Then pick who can join.

## What it cannot do

- No breakout rooms. In progress: [#123](<url>).
```

Who it is for in the first line, the most useful action next, a picture beside
every control the text names, the limits last with the upstream work linked.
Every sentence follows `skills/writing-style.md`, its rules on linking every
named thing and on pitching to the audience included.

## The site

- Before writing a page, name every kind of reader who opens the site, and give
  each an entry on the home page: a card titled with the reader, holding the
  links they need, each link worded as the thing they want to do. A table whose
  second column only repeats the link's name is a list.
- Order sibling pages and guides by how likely a reader needs them, the most
  common first, in the navigation, on the home page and in every list naming them.
- A reader with one specific need, an accessibility need, a role, a weak device,
  gets one guide page: who it is for, the most useful action first, then what the
  product cannot do for them. Each guide is one click from the home page, from
  the getting-started page and from the reference page it extends; a page that
  only lists the guides is cut.
- An install overview opens on the fastest path, a tip with one button, then the
  other paths as a list saying when each fits. What each path needs lives in its
  own prerequisites page, never in the overview, since it differs per path.
- A lookup table, permissions, ports, variables, browser support, lives on one
  page; every other page keeps one clause and links it.
- A technical overview answers questions, the most asked first, each heading
  the question a reader would type, in short paragraphs that explain. A *Key
  concepts* section near the top defines each term of the field once, the
  architecture the product rests on first, and links to the section detailing
  it.
- Every code block carries a copy button, and a terminal block's copies its
  commands alone, without the `$` prompt or the output: the theme's copy feature
  on, plus a page script setting each terminal block's copy text.
- Feature support across browsers or devices is one table, a row per place and
  a column per feature that varies, ✅ and ❌ in the cells, under one line saying
  what works everywhere. An all-❌ row without that line reads as nothing working.

## A page

- When asked to review a page or a section, run the reader-persona read unasked,
  step 11 of the pass in `skills/writing-style.md`: take each reader whose
  home-page card leads there, walk the pages doing that reader's likeliest task
  start to finish, and fix every place they stop in the same turn. The tell is
  the user naming the personas in the request.
- Keep a line only if the reader acts on it or would be bitten without it. Cut
  what the screen already shows, an intro listing the headings, a sentence
  restating its table or diagram, and every detail written only for
  completeness.
- Prefer one plain sentence to a precise paragraph: `One script installs Meet and
  everything it needs on a fresh Linux server.` beat a sentence naming each
  piece it installs. A first line that repeats its page's or its box's title is
  cut.
- A page about a concept opens on a one-line definition of it, the term linked:
  `A reverse proxy receives your domains' HTTPS traffic and passes each request
  to the right container.`
- A page offering an alternative to the default path opens on why a reader
  takes it: what the default cannot do, `The Quick Start script always installs
  its own reverse proxy and Keycloak.`
- Keep the structure flat. A heading wrapping a single subsection is flattened,
  two sections about one thing merge, a section whose one fact fits a table row
  folds into that row, and no `---` separates sections.
- A list repeating what is kept whole elsewhere becomes one link to it: a
  checklist restating the page's own sections is deleted, and a partial copy of
  another page's list is replaced by a link to that page, its top rather than
  an optional section of it.
- Every step leads with its example, a command, a config or the output it
  prints; the prose after it carries only what the example cannot show. A value
  the reader replaces in a command is named in one line before the block, since
  the copy button copies the example as is.
- A step that runs a command opens on a `console` block, the command after a
  `$` prompt and its real output under it, captured from a run, a blank line
  before each command that follows output; one line of prose follows. Prose
  saying what the output shows is the tell. Every typed line starts with `$`:
  a command wider than the block gets shorter, through an alias or a variable
  set on the line before, never a `\` and `>` continuation.
- Files a reader downloads are fetched in one command per source folder, each
  file still named on the line, `curl -fsSL --remote-name-all $RAW/dir/{a,b}`,
  never one `curl` per file and never a fetch script that hides which files a
  stack is made of.
- Put what a command is for in a comment above it in the block, never at the
  line's end, and keep every code line narrower than the block: a comment or a
  command past the edge is hidden behind a scroll bar.
- Before asking the reader to fill placeholders, name each one and the file it
  sits in. Placeholders a script could fill are filled by the script, extended
  if it falls short, never by hand-typed `sed` lines.
- Open a sentence with a question only where the answer sends the reader one
  of two ways, `Already run a reverse proxy? Skip to Stack 2.` A question the
  page itself answers, `No proxy yet?` on the proxy page, is cut.
- Explain in short paragraphs; a paragraph naming three or more parallel items
  becomes a list, and a list of things that are not parallel goes back to prose.
  A table is for a lookup, never for prose split into cells.
- A section headed What it cannot do closes a guide: one line per limit, each
  traced to the code. Where an issue or pull request is open on the limit, the
  line ends `In progress: [#n](<url>)`.
- After the user flags one line, grep the site for the same fault and fix every
  instance in that turn, listing each changed line: a remark names a kind of
  fault, never one sentence.
- An emoji carries meaning or goes: ✅ and ❌ in a grid, one icon per component
  shared by a diagram and its table. None in a heading or a sentence.
- A UI label is written exactly as the app's locale file has it, case included,
  checked by grep before it ships.

## Pictures

- Wherever a page names a button, a setting or a menu, show where it sits: a
  screenshot cropped to it, beside the sentence naming it, with a `figcaption`
  giving the path to reach it. A control named with no picture is the tell.
- A picture on a site page takes a `figcaption` and a path relative to the
  page, in place of the blockquote and the raw URL `skills/writing-style.md`
  asks of a picture in a review or a pull request.
- Never a screenshot of what a text table beside it already lists: the text is
  searchable and a screen reader reads it, the picture neither.
- A page for mouse users names the button and its icon, never the keyboard
  shortcut. Shortcuts belong on the page for keyboard and screen-reader users.
- A walkthrough of a few clicks is a recording of the real motion, the pointer
  drawn and routed over no other control, sped up until nothing on screen argues
  for its length. It ends on half a second more of live footage, never a frozen
  last frame. A long sequence of keys is a GIF of one still per step, each held
  one to two seconds, with the key named on the frame.
- A browser dialog, a share picker or a permission prompt, is drawn outside the
  page, so headless screenshots never show it: film a headed browser on a
  virtual display, per the headful rule in `skills/try.md`, and record the
  display.
- Capture with the browser's fake camera and microphone and with test accounts,
  and name the fake source when the user asks about a frame.

## Facts

- After a pass of edits, check every claim the pass added against the code
  before pushing: read-only checkers per area, each sorting a claim into wrong,
  unverifiable here, or misleading, with the source line and the replacement
  text, then one pass applying them, re-checking each first. A pass that edits
  and checks in one agent checks its own edits.
- When a check turns up something to fix, a contradiction between two pages or
  with the code, or a line to simplify, loop before reporting: fix what it
  found, then run a fresh checker over the whole site again, until a full pass
  finds nothing. Report the fixes of every pass at once. The tell is the user
  meeting a new one in the next reply.
- A claim about a browser, an operating system or a provider carries the vendor
  page that settles it, or is made general, per the unproved-claims step of the
  pass in `skills/writing-style.md`. A wrong precise claim is worse than a
  vague true one.

## Versions

- A rework pushed before it is done goes up as numbered versions, the commit
  title `WIP vN`, the body naming the part finished and saying the rest is not.
