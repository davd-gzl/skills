// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! The deterministic steps of a review round, one subcommand each. Prose in skills/review.md
//! names the step; this binary runs it, so no agent turn does. `links` checks every blob link
//! of a round, `prior` carries the earlier rounds' checks to the head.
mod links;
mod prior;

use std::collections::HashMap;
use std::path::Path;
use std::process::Command;

pub use links::{find_links, judge, links, Link, Verdict};
pub use prior::{checks_to_json, json_string, parse_row, prior, Hunk, LineMap, PriorCheck, Row};

pub const USAGE: &str = "round <subcommand> ...

  links <round dir> [--repo <git dir>] [--out <file>]
      Every blob link in the round's comment_*.md and the overview.md beside it: the
      file at the pinned sha, through git show in --repo when the sha is there, else
      gh api, and the #L range inside it. One row per link into <round dir>/links.md,
      exit 1 when any link misses.

  prior <slug dir> --repo <git dir> --sha <head sha> [--json <file>]
      The Check cell of every candidate row in the slug's earlier claims.md files,
      keyed file:line at the head: a row's line is mapped from its round's sha to the
      head through git diff, and a row whose line the head removed is dropped. The
      State and Observed cells never leave the file. JSON to --json, else to stdout.";

pub fn dispatch(args: &[String]) -> i32 {
    match args.first().map(String::as_str) {
        Some("links") if args.len() >= 2 => links(&args[1..]),
        Some("prior") if args.len() >= 2 => prior(&args[1..]),
        _ => {
            eprintln!("{USAGE}");
            2
        }
    }
}

/// The named options after the positional argument: every `--flag value` pair, into a map.
pub fn options(args: &[String]) -> Result<HashMap<String, String>, String> {
    let mut out = HashMap::new();
    let mut i = 1;
    while i < args.len() {
        let flag = args[i].as_str();
        match (flag.strip_prefix("--"), args.get(i + 1)) {
            (Some(name), Some(value)) => {
                out.insert(name.to_string(), value.clone());
                i += 2;
            }
            _ => return Err(format!("unexpected argument {flag}")),
        }
    }
    Ok(out)
}

/// The command's stdout when it succeeds, nothing when it fails or cannot start.
fn command_stdout(cmd: &str, args: &[&str]) -> Option<Vec<u8>> {
    let output = Command::new(cmd).args(args).output().ok()?;
    if output.status.success() {
        Some(output.stdout)
    } else {
        None
    }
}

/// Lines in a blob, a last line without its newline counted.
pub fn count_lines(bytes: &[u8]) -> usize {
    let newlines = bytes.iter().filter(|&&c| c == b'\n').count();
    let unterminated = bytes.last().map(|&c| c != b'\n').unwrap_or(false);
    if unterminated {
        newlines + 1
    } else {
        newlines
    }
}

fn dir_name(path: &Path) -> String {
    path.file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default()
}

/// Directories and git repositories the tests build.
#[cfg(test)]
pub(crate) mod testutil {
    use std::fs;
    use std::path::{Path, PathBuf};
    use std::process::Command;

    pub fn tmp(name: &str) -> PathBuf {
        let dir = std::env::temp_dir()
            .join(format!("skills-tools-round-{}", std::process::id()))
            .join(name);
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    pub fn git(dir: &Path, args: &[&str]) -> String {
        let output = Command::new("git")
            .arg("-C")
            .arg(dir)
            .args(args)
            .env("GIT_AUTHOR_NAME", "t")
            .env("GIT_AUTHOR_EMAIL", "t@x")
            .env("GIT_COMMITTER_NAME", "t")
            .env("GIT_COMMITTER_EMAIL", "t@x")
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "git {:?}: {}",
            args,
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8_lossy(&output.stdout).trim().to_string()
    }

    /// A repository with f.go at two commits: lines x, y inserted at the top, d deleted, g
    /// appended. Returns the directory and the two short shas.
    pub fn shifted_repo(name: &str) -> (PathBuf, String, String) {
        let dir = tmp(name);
        git(&dir, &["init", "-q"]);
        fs::write(dir.join("f.go"), "a\nb\nc\nd\ne\nf\n").unwrap();
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "one"]);
        let first = git(&dir, &["rev-parse", "--short=9", "HEAD"]);
        fs::write(dir.join("f.go"), "x\ny\na\nb\nc\ne\nf\ng\n").unwrap();
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "two"]);
        let second = git(&dir, &["rev-parse", "--short=9", "HEAD"]);
        (dir, first, second)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args(list: &[&str]) -> Vec<String> {
        list.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn options_pairs_and_errors() {
        let opts = options(&args(&["x", "--repo", "r", "--out", "o"])).unwrap();
        assert_eq!(opts["repo"], "r");
        assert_eq!(opts["out"], "o");
        assert!(options(&args(&["x", "--repo"])).is_err());
        assert!(options(&args(&["x", "stray"])).is_err());
    }

    #[test]
    fn count_lines_with_and_without_a_final_newline() {
        assert_eq!(count_lines(b""), 0);
        assert_eq!(count_lines(b"a"), 1);
        assert_eq!(count_lines(b"a\n"), 1);
        assert_eq!(count_lines(b"a\nb"), 2);
    }

    #[test]
    fn dispatch_usage() {
        assert_eq!(dispatch(&[]), 2);
        assert_eq!(dispatch(&args(&["nope"])), 2);
        assert_eq!(dispatch(&args(&["links"])), 2);
    }
}
