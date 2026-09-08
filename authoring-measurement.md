---
name: authoring-measurement
description: Use when a rule's wording is in doubt and its effect is being measured, rather than argued. The isolation flags, the one-run design, and the blind judge pass.
---

# Measuring a rule

Read when a wording's effect is in doubt, never when writing an ordinary rule.

A wording whose effect is in doubt is measured, and the whole run is designed
before the first call: isolation flags first, `--tools "" --strict-mcp-config
--disable-slash-commands --setting-sources ""`, since a plugin hook or a skill
injection contaminates every answer and `--bare` drops OAuth; every variant in
that one run at effort `medium`; one blind judge pass, labels hidden and order
shuffled, on single-pass readability and substance kept. A round per variant
multiplies the calls by the rounds and waits for each round's slowest call.
`skills/tests/chat-register/` is the harness that measured *Short form* in
`skills/writing-style.md`.
