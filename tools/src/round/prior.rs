// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! `round prior`: the Check cell of every candidate row in a slug's earlier `claims.md` files,
//! each row's line carried from its round's sha to the head through `git diff -U0`.
use super::{command_stdout, dir_name, options, USAGE};
use regex::Regex;
use std::collections::{BTreeMap, HashMap};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;

/// One hunk header of a unified diff: `@@ -old_start,old_len +new_start,new_len @@`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Hunk {
    pub old_start: usize,
    pub old_len: usize,
    pub new_start: usize,
    pub new_len: usize,
}

/// Old-line to new-line mapping of one file between two commits.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LineMap {
    pub hunks: Vec<Hunk>,
}

static HUNK_HEADER: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@").unwrap());

impl LineMap {
    /// The map from `git diff -U0` in `repo`, None when git cannot diff the two commits there.
    pub fn load(repo: &Path, old: &str, new: &str, path: &str) -> Option<LineMap> {
        let repo = repo.to_string_lossy();
        let diff = command_stdout(
            "git",
            &[
                "-C",
                &repo,
                "diff",
                "-U0",
                "--no-color",
                old,
                new,
                "--",
                path,
            ],
        )?;
        Some(LineMap::parse(&String::from_utf8_lossy(&diff)))
    }

    /// The hunk headers of a diff; a length left out of a header is 1.
    pub fn parse(diff: &str) -> LineMap {
        let number = |caps: &regex::Captures, i: usize, default: usize| {
            caps.get(i)
                .and_then(|m| m.as_str().parse().ok())
                .unwrap_or(default)
        };
        let hunks = diff
            .lines()
            .filter_map(|line| HUNK_HEADER.captures(line))
            .map(|caps| Hunk {
                old_start: number(&caps, 1, 0),
                old_len: number(&caps, 2, 1),
                new_start: number(&caps, 3, 0),
                new_len: number(&caps, 4, 1),
            })
            .collect();
        LineMap { hunks }
    }

    /// The line at the head, or None when the line sits inside a hunk's removed range: the head
    /// no longer holds it.
    pub fn map(&self, line: usize) -> Option<usize> {
        let mut offset: isize = 0;
        for hunk in &self.hunks {
            let removed =
                hunk.old_len > 0 && line >= hunk.old_start && line < hunk.old_start + hunk.old_len;
            if removed {
                return None;
            }
            let last_old = hunk.old_start + hunk.old_len.saturating_sub(1);
            if line <= last_old {
                break;
            }
            offset += hunk.new_len as isize - hunk.old_len as isize;
        }
        Some((line as isize + offset).max(1) as usize)
    }
}

/// A candidate row of `claims.md`: its `file:line` anchor and its Check cell.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Row {
    pub anchor: String,
    pub check: String,
}

static CANDIDATE_ROW: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^\|\s*(?:(\d*)\s*\|\s*)?([A-Z]+)\s*\|[^|]*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|")
        .unwrap()
});

/// A candidate row, with or without the leading `#` column an earlier round's table lacks: the
/// state in capitals, the band, the anchor, the check.
pub fn parse_row(line: &str) -> Option<Row> {
    let caps = CANDIDATE_ROW.captures(line)?;
    Some(Row {
        anchor: caps[3].trim().to_string(),
        check: caps[4].trim().to_string(),
    })
}

/// An anchor split into its path and line, None when it is not `file:line`.
fn split_anchor(anchor: &str) -> Option<(&str, usize)> {
    let (path, line) = anchor.rsplit_once(':')?;
    Some((path, line.parse().ok()?))
}

/// One earlier check, keyed at the head by `file:line`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PriorCheck {
    pub round: String,
    pub check: String,
}

/// Where a row's line landed at the head.
enum Landed {
    /// Its line, unmoved, or unmapped because the round's sha is the head's.
    Same(usize),
    /// A different line, the diff between the shas having shifted it.
    Moved(usize),
    /// Nowhere: the head removed the line.
    Removed,
}

/// The line maps between each round's sha and the head, loaded once per file and sha.
struct HeadMaps {
    repo: Option<PathBuf>,
    head: Option<String>,
    loaded: HashMap<(String, String), Option<LineMap>>,
}

impl HeadMaps {
    fn land(&mut self, old_sha: &str, path: &str, line: usize) -> Landed {
        let (Some(repo), Some(head)) = (&self.repo, &self.head) else {
            return Landed::Same(line);
        };
        let same_commit =
            old_sha.is_empty() || head.starts_with(old_sha) || old_sha.starts_with(head.as_str());
        if same_commit {
            return Landed::Same(line);
        }
        let key = (old_sha.to_string(), path.to_string());
        let map = self
            .loaded
            .entry(key)
            .or_insert_with(|| LineMap::load(repo, old_sha, head, path));
        match map {
            // Git could not diff the two commits: the row keeps its line rather than vanishing.
            None => Landed::Same(line),
            Some(map) => match map.map(line) {
                None => Landed::Removed,
                Some(n) if n == line => Landed::Same(n),
                Some(n) => Landed::Moved(n),
            },
        }
    }
}

#[derive(Default)]
struct Tally {
    kept: usize,
    moved: usize,
    dropped: usize,
}

pub fn prior(args: &[String]) -> i32 {
    let slug = PathBuf::from(&args[0]);
    let opts = match options(args) {
        Ok(opts) => opts,
        Err(e) => {
            eprintln!("{e}\n{USAGE}");
            return 2;
        }
    };
    let repo = opts.get("repo").map(PathBuf::from);
    let head = opts.get("sha").cloned();
    if repo.is_none() != head.is_none() {
        eprintln!("--repo and --sha go together\n{USAGE}");
        return 2;
    }
    let rounds = match round_dirs(&slug) {
        Ok(dirs) => dirs,
        Err(e) => {
            eprintln!("{}: {e}", slug.display());
            return 2;
        }
    };
    let mut checks: BTreeMap<String, Vec<PriorCheck>> = BTreeMap::new();
    let mut maps = HeadMaps {
        repo,
        head,
        loaded: HashMap::new(),
    };
    let mut tally = Tally::default();
    for dir in &rounds {
        // A round directory is `<n>-<sha>`.
        let round = dir_name(dir);
        let old_sha = round
            .split_once('-')
            .map(|(_, sha)| sha.to_string())
            .unwrap_or_default();
        let text = fs::read_to_string(dir.join("claims.md")).unwrap_or_default();
        for row in text.lines().filter_map(parse_row) {
            if row.check.is_empty() || row.check == "---" {
                continue;
            }
            let Some((path, line)) = split_anchor(&row.anchor) else {
                continue;
            };
            let at_head = match maps.land(&old_sha, path, line) {
                Landed::Same(n) => n,
                Landed::Moved(n) => {
                    tally.moved += 1;
                    n
                }
                Landed::Removed => {
                    tally.dropped += 1;
                    continue;
                }
            };
            tally.kept += 1;
            checks
                .entry(format!("{path}:{at_head}"))
                .or_default()
                .push(PriorCheck {
                    round: round.clone(),
                    check: row.check,
                });
        }
    }
    let json = checks_to_json(&checks);
    let summary = format!(
        "{} anchors from {} prior claims.md: {} rows kept, {} re-anchored to the head, {} dropped whose line the head removed",
        checks.len(),
        rounds.len(),
        tally.kept,
        tally.moved,
        tally.dropped
    );
    match opts.get("json") {
        Some(path) => {
            if let Err(e) = fs::write(path, json + "\n") {
                eprintln!("{path}: {e}");
                return 2;
            }
            println!("{summary}, written to {path}");
        }
        None => {
            println!("{json}");
            eprintln!("{summary}");
        }
    }
    0
}

/// The slug's round directories holding a `claims.md`, in name order.
fn round_dirs(slug: &Path) -> std::io::Result<Vec<PathBuf>> {
    let mut dirs: Vec<PathBuf> = fs::read_dir(slug)?
        .flatten()
        .map(|entry| entry.path())
        .filter(|path| path.join("claims.md").exists())
        .collect();
    dirs.sort();
    Ok(dirs)
}

/// A JSON string body: quotes, backslashes, newlines, tabs and control characters escaped.
pub fn json_string(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out
}

/// `{"file:line": [{"round": "...", "check": "..."}, ...], ...}`, keys in order.
pub fn checks_to_json(checks: &BTreeMap<String, Vec<PriorCheck>>) -> String {
    let entries: Vec<String> = checks
        .iter()
        .map(|(anchor, rows)| {
            let items: Vec<String> = rows
                .iter()
                .map(|row| {
                    format!(
                        "{{\"round\": \"{}\", \"check\": \"{}\"}}",
                        json_string(&row.round),
                        json_string(&row.check)
                    )
                })
                .collect();
            format!("\"{}\": [{}]", json_string(anchor), items.join(", "))
        })
        .collect();
    format!("{{{}}}", entries.join(", "))
}

#[cfg(test)]
mod tests {
    use super::super::testutil::{shifted_repo, tmp};
    use super::*;

    fn hunk(old_start: usize, old_len: usize, new_start: usize, new_len: usize) -> Hunk {
        Hunk {
            old_start,
            old_len,
            new_start,
            new_len,
        }
    }

    #[test]
    fn line_map_hunks() {
        let map = LineMap::parse("@@ -0,0 +1,2 @@\n+x\n+y\n@@ -4 +6,0 @@\n-d\n@@ -6,0 +8 @@\n+g\n");
        assert_eq!(
            map.hunks,
            vec![hunk(0, 0, 1, 2), hunk(4, 1, 6, 0), hunk(6, 0, 8, 1)]
        );
        assert_eq!(map.map(1), Some(3));
        assert_eq!(map.map(2), Some(4));
        assert_eq!(map.map(4), None);
        assert_eq!(map.map(5), Some(6));
        assert_eq!(map.map(6), Some(7));
    }

    #[test]
    fn line_map_replacement_and_no_hunks() {
        let map = LineMap::parse("@@ -3,2 +3,3 @@\n-c\n-d\n+C\n+D\n+E\n");
        assert_eq!(map.map(2), Some(2));
        assert_eq!(map.map(3), None);
        assert_eq!(map.map(4), None);
        assert_eq!(map.map(5), Some(6));
        assert_eq!(LineMap::parse("").map(9), Some(9));
    }

    #[test]
    fn line_map_from_git() {
        let (repo, first, second) = shifted_repo("linemap");
        let map = LineMap::load(&repo, &first, &second, "f.go").unwrap();
        assert_eq!(
            (map.map(2), map.map(4), map.map(5), map.map(6)),
            (Some(4), None, Some(6), Some(7))
        );
        assert!(
            LineMap::load(&repo, "0000000", &second, "f.go").is_none(),
            "an unknown sha yields no map"
        );
    }

    #[test]
    fn parse_row_both_shapes() {
        let row = |anchor: &str, check: &str| {
            Some(Row {
                anchor: anchor.into(),
                check: check.into(),
            })
        };
        assert_eq!(
            parse_row("| 3 | CONFIRMED | Warning | a/b.go:12 | grep x | out | art |"),
            row("a/b.go:12", "grep x")
        );
        assert_eq!(
            parse_row("| REFUTED | Nit | a.go:1 | ls | out | |"),
            row("a.go:1", "ls")
        );
        assert_eq!(
            parse_row("| # | State | Band | file:line | Check | Observed | Artifact |"),
            None
        );
        assert_eq!(parse_row("| --- | --- | --- | --- | --- |"), None);
        assert_eq!(parse_row("plain text"), None);
    }

    #[test]
    fn json_escaping() {
        assert_eq!(
            json_string("a\"b\\c\nd\te\u{1}"),
            "a\\\"b\\\\c\\nd\\te\\u0001"
        );
        let mut checks = BTreeMap::new();
        checks.insert(
            "f:1".to_string(),
            vec![PriorCheck {
                round: "r".into(),
                check: "c \"q\"".into(),
            }],
        );
        assert_eq!(
            checks_to_json(&checks),
            "{\"f:1\": [{\"round\": \"r\", \"check\": \"c \\\"q\\\"\"}]}"
        );
        assert_eq!(checks_to_json(&BTreeMap::new()), "{}");
    }

    #[test]
    fn prior_reanchors_drops_and_keeps() {
        let (repo, first, second) = shifted_repo("prior");
        let slug = tmp("prior-slug");
        let round = slug.join(format!("1-{first}"));
        fs::create_dir_all(&round).unwrap();
        let claims = "| # | State | Band | file:line | Check | Observed | Artifact |\n\
                      | --- | --- | --- | --- | --- | --- | --- |\n\
                      | 1 | CONFIRMED | Warning | f.go:2 | grep -n b f.go | 2:b | |\n\
                      | 2 | REFUTED | Nit | f.go:4 | grep -n d f.go | 4:d | |\n\
                      | 3 | PLAUSIBLE | Warning | f.go:5 | --- | | |\n\
                      | 4 | CONFIRMED | Nit | f.go:6 | grep -n f f.go | 6:f | |\n\
                      | 5 | CONFIRMED | Nit | noline | grep | | |\n";
        fs::write(round.join("claims.md"), claims).unwrap();
        let out = slug.join("prior.json");
        let slug_arg = slug.to_string_lossy().into_owned();
        let out_arg = out.to_string_lossy().into_owned();
        let code = prior(&[
            slug_arg.clone(),
            "--repo".into(),
            repo.to_string_lossy().into_owned(),
            "--sha".into(),
            second.clone(),
            "--json".into(),
            out_arg.clone(),
        ]);
        assert_eq!(code, 0);
        let json = fs::read_to_string(&out).unwrap();
        assert_eq!(
            json.trim(),
            format!(
                "{{\"f.go:4\": [{{\"round\": \"1-{first}\", \"check\": \"grep -n b f.go\"}}], \"f.go:7\": [{{\"round\": \"1-{first}\", \"check\": \"grep -n f f.go\"}}]}}"
            )
        );
        assert_eq!(prior(&[slug_arg.clone(), "--json".into(), out_arg]), 0);
        assert!(
            fs::read_to_string(&out).unwrap().contains("\"f.go:2\""),
            "without a head the rows keep their lines"
        );
        assert_eq!(
            prior(&[slug_arg, "--repo".into(), "x".into()]),
            2,
            "--repo without --sha"
        );
        assert_eq!(prior(&["/nonexistent/slug".into()]), 2);
    }
}
