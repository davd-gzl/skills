---
name: shortcuts
description: When a word the user types counts, in context as the session opens. The words and what each starts are skills/words.md.
---

# Shortcuts

A word that publishes, a push, a post, a merge, a close, a delete or a
ready-marking, is typed as its slash command, `/p`, `/post`, `/m`, and nothing
else gives it: typed prose publishes nothing, `p` without its slash included.
An argument that is itself such a command adds its word, so `/p d` pushes and
deletes. Every other word in `skills/words.md` counts opening a line of the
message, and `scripts/words.py` puts its row in context then.
