---
name: shortcuts
description: When a word the user types counts, in context as the session opens. The words and what each starts are skills/words.md.
---

# Shortcuts

A word the user types counts only at the start of a message, each word
separated from the next by whitespace: `p d` gives `push` and `delete`, while
`pd`, `please p` and a question give nothing. What each word starts is its row
in `skills/words.md`, which `scripts/words.py` puts in context when a message
opens with it.
