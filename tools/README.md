# tools

One Rust crate, `skills-tools`, holding the deterministic steps of this corpus
as two binaries, so no agent turn runs them: `round`, a review round's fixed
steps, and `rules`, the corpus lint. Prose in a skill names the step; the
binary runs it.

## Binaries

| Binary | Subcommand | Does | Exit |
| --- | --- | --- | --- |
| `round` | `links <round dir> [--repo <git dir>] [--out <file>]` | resolves every blob link of the round's `comment_*.md` and the `overview.md` beside it at the pinned sha, `git show` in `--repo` when the sha is there and `gh api` otherwise, and checks the `#L` range against the file; one row per link into `<round dir>/links.md`, and a file the forge could not serve says why rather than reading as missing | 1 when any link misses |
| `round` | `prior <slug dir> --repo <git dir> --sha <head sha> [--json <file>]` | the Check cell of every candidate row in the slug's earlier `claims.md` files, keyed `file:line` at the head, each line mapped from its round's sha through `git diff -U0`; an anchor in backticks or with a line range is read, a row whose line the head removed is dropped, a row with no `file:line` anchor is counted in the summary and left out, and the State and Observed cells never leave the file | 2 on a bad call |
| `round` | `risk <repo> <base> <head> [--prior <slug dir>] [--keywords <file>] [--out <file>] [--json <file>]` | every changed file ranked hot, warm or cold from what git and the diff carry: a guard removed, a catalog keyword added, no test touched, fix commits in its history, its size, a finding an earlier round confirmed in it; docs, tests and generated files are cold; the weights sit in one table in `src/round/risk.rs`, tuned by the retro's hit rate per tier | 2 on a bad call |
| `round` | `dispatch <repo> <base> <head> [--risk <risk.json>] [--catalog 1] [--diff-dir <dir>] [--json <file>] [--out <file>]` | the changed files cut into bundles by category: code and tests by directory, small directories merged with a sibling, a bundle over the ceiling split by file, docs and config in one bundle, generated files skipped; each bundle lists the angles it has material for and the finders it earns, one per angle or one carrying every angle under the floor, so the finder count follows the diff; `--diff-dir` writes each bundle's diff with its enclosing functions and a comment-blanked twin | 2 on a bad call |
| `round` | `assemble <round dir> [--repo <head worktree>] [--sha <sha>] [--risk <risk.json>] [--url <blob url base>] [--title <text>] [--shape <text>]` | `claims.md` and `findings.md` from the round's verdicts as data: `candidates/*.json`, what each finder, the reflector and the critic returned, and `verdicts/*.json`, what each verifier returned; `claims.md` holds the Candidates table, one row per verdict joined to its candidate, exact line first and the nearest within five lines after, one row per candidate no verifier reached, the rows a finder settled, the hit rate per tier and an empty Completeness section; `findings.md` one block per finding in posting order, band then file then line, `SKIP` in front of a PLAUSIBLE Nit or Suggestion, so the writer composes the text and never retypes a row | 1 when a row's `file:line` is not at the head, 2 on a bad call |
| `rules` | `lint [--quiet] <files>` | the corpus lint, the contract in `authoring.md`: a frozen clause, a date or a sha inside a rule, an em-dash or a parenthetical in prose, a dangling clause, a capability asserted with no command, a pointer at a file or a section that does not exist, a rule stated in two files, and each file's cost; `--quiet` drops the health table | 0 always: nothing blocks |

## Build and reach

- `cargo build --release --manifest-path tools/Cargo.toml`. `regex` and `serde_json` are the dependencies; a clean build takes about ten seconds and each binary is 3MB. `tools/target/` is ignored.
- A consumer workspace's sync installs both onto `~/bin` and reaches them through its `scripts/round` and `scripts/rules` shims, since `~/bin` is not on `PATH`. A machine without `cargo` has shims that run nothing: install the toolchain first.

## Tests

`cargo test --manifest-path tools/Cargo.toml` runs 71 tests: unit tests beside
the code in each module, the line map among them against a git repository
built in a temporary directory, and one golden test in
`tests/lint_golden.rs`.

The golden test runs the lint over `tests/lint/corpus/`, a fixture exercising
every check, with the arguments in `tests/lint/args.txt`, and compares the
whole output to `tests/lint/expected.txt` and `tests/lint/expected-quiet.txt`,
written by the Python lint this crate replaced: a difference is a lost
capability. When a check changes on purpose, regenerate both from the corpus
directory and read the diff before committing it:

```bash
cd tools/tests/lint/corpus && ../../../target/release/rules lint $(cat ../args.txt) > ../expected.txt; ../../../target/release/rules lint --quiet $(cat ../args.txt) > ../expected-quiet.txt
```

## Shape

- `src/lint/`, in reading order: `patterns.rs`, every regex with one line on what it catches; `text.rs`, a file cut into prose lines, rule units and sentences, with fences, code spans, link targets and tags blanked first so a rule's own example never trips a check; `checks.rs`, one function per check, each returning its finding or nothing; `file.rs`, one file through every check; `report.rs`, a run over many files, the duplicates and the health table. The `regex` crate has no lookaround, so the sha and section-reference checks read the characters around a match by hand, and the tests pin that.
- `src/round/`: `links.rs`, `prior.rs`, `risk.rs`, `dispatch.rs` and `assemble.rs`, one subcommand each; `LineMap` in `prior.rs` maps a line from one sha to another through the hunks of `git diff -U0`; the risk weights sit in one table at the top of `risk.rs`; `mod.rs` holds the usage, the dispatch and the option parsing.
- Every struct has named fields, every function one job under a doc comment saying what it catches or returns, one statement per line, `cargo fmt` over all of it and `cargo clippy` clean.
- `src/bin/`: two `main` functions of a few lines each. Everything else is in the library, so a test calls what the binary calls.
