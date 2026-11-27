---
name: shortcuts
description: What the user types and what it starts, in context as the session opens. Every action is a slash command under skills/commands/; the words below only shape the reply.
---

# Shortcuts

Every action the user starts is a slash command, one file under
`skills/commands/`: `/review`, `/fix`, `/p`, `/post`, `/m`. A harness without
slash commands reads `skills/commands/<name>.md` when a line of the message
opens with `/<name>`. A publish, a push, a post, a merge, a close, a delete or
a ready-marking, is given by its command alone: typed prose publishes nothing,
`p` without its slash included. An argument that is itself such a command adds
its word, so `/p d` pushes and deletes.

A reply may coin a letter for a next step outside the request that publishes
nothing, defined beside it, `s`: run the simplify pass; it holds for the next
message only and never takes a command's name. On a pull request the user did
not author, the next step offered for a fix is its comment draft, sent on
`/post`.

These words shape the reply and start no action:

| Word | What the reply gives |
| --- | --- |
| `TLDR` | the answer in one line, and the command it waits on |
| `ag`, `all good?` | the work in flight in one or two lines, no list: running, stuck or failed, and what comes next; the work carries on under the request's word |
| `path` | the worktree the work sits in, its path alone |
| "a comment" | the `comment_<model>.md` draft and the text for the target, never an explanation |
| `links <target>` | three markdown hyperlinks on one line, each to its page on the remote hosting it: the pull request, its latest round's `overview.md`, and that round's `comment_<model>.md` |
| a pull request number alone | what the session changed on that pull request's branch, read from its diff, and the comment or finding each change answers |
| `continue` | the local work resumed, dead agents re-dispatched first; nothing published |
| `pause`, `I have <n> min` | what stops when the laptop closes, that the worktree keeps every edit, what restarts on return, and `/p` offered for what is finished |
| `retro` | the session's retro, per *The closing block* in `skills/reply.md` |
| `go`, `ok`, `yes`, `sure` | local work only, never a publish, per Invariant 2 |
