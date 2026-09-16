// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! `round links`: every blob link of a round's draft and overview, resolved at its pinned sha,
//! with the `#L` range checked against the file's length.
use super::{command_stdout, count_lines, dir_name, options, USAGE};
use regex::Regex;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;

/// One blob link, as `[text](https://github.com/<owner>/<repo>/blob/<sha>/<path>#L<a>-L<b>)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Link {
    /// The file the link was read from.
    pub file: String,
    pub url: String,
    pub owner: String,
    pub repo: String,
    pub sha: String,
    pub path: String,
    /// The first line of the anchor, when there is one.
    pub first: Option<usize>,
    /// The last line of the anchor, when it is a range.
    pub last: Option<usize>,
}

static BLOB_LINK: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"\]\((https://github\.com/([\w.-]+)/([\w.-]+)/blob/([0-9a-f]{7,40})/([^#)\s?]+)(?:\?plain=1)?(?:#L(\d+)(?:-L(\d+))?)?)\)",
    )
    .unwrap()
});

/// Every blob link in a text, tagged with the file it came from.
pub fn find_links(file: &str, text: &str) -> Vec<Link> {
    BLOB_LINK
        .captures_iter(text)
        .map(|c| {
            let line = |i: usize| c.get(i).and_then(|m| m.as_str().parse().ok());
            Link {
                file: file.to_string(),
                url: c[1].to_string(),
                owner: c[2].to_string(),
                repo: c[3].to_string(),
                sha: c[4].to_string(),
                path: c[5].to_string(),
                first: line(6),
                last: line(7),
            }
        })
        .collect()
}

/// A row's verdict: whether the link resolves, and the lines it lands on or misses.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Verdict {
    pub resolves: bool,
    pub lines: String,
}

/// Judges a link from the file's line count, None when the file is missing at the sha, and the
/// anchor's first and last lines.
pub fn judge(line_count: Option<usize>, first: Option<usize>, last: Option<usize>) -> Verdict {
    let Some(n) = line_count else {
        return Verdict {
            resolves: false,
            lines: "file missing at the sha".to_string(),
        };
    };
    let Some(a) = first else {
        return Verdict {
            resolves: true,
            lines: format!("{n} lines, no anchor"),
        };
    };
    let b = last.unwrap_or(a);
    if a >= 1 && a <= b && b <= n {
        Verdict {
            resolves: true,
            lines: format!("L{a}-L{b} of {n}"),
        }
    } else {
        Verdict {
            resolves: false,
            lines: format!("L{a}-L{b} outside {n} lines"),
        }
    }
}

pub fn links(args: &[String]) -> i32 {
    let round = PathBuf::from(&args[0]);
    let opts = match options(args) {
        Ok(opts) => opts,
        Err(e) => {
            eprintln!("{e}\n{USAGE}");
            return 2;
        }
    };
    let repo = opts.get("repo").map(PathBuf::from);
    let out = opts
        .get("out")
        .map(PathBuf::from)
        .unwrap_or_else(|| round.join("links.md"));
    let files = match round_files(&round) {
        Ok(files) => files,
        Err(e) => {
            eprintln!("{}: {e}", round.display());
            return 2;
        }
    };
    let mut found = Vec::new();
    for file in &files {
        let text = fs::read_to_string(file).unwrap_or_default();
        found.extend(find_links(&dir_name(file), &text));
    }
    // One lookup per file and sha, however many links land in it.
    let mut line_counts: HashMap<(String, String), Option<usize>> = HashMap::new();
    let mut rows = vec![
        "| File | Link | Resolves | Lines |".to_string(),
        "| --- | --- | --- | --- |".to_string(),
    ];
    let mut misses = 0;
    for link in &found {
        let key = (link.sha.clone(), link.path.clone());
        let n = *line_counts
            .entry(key)
            .or_insert_with(|| line_count(repo.as_deref(), link));
        let verdict = judge(n, link.first, link.last);
        if !verdict.resolves {
            misses += 1;
        }
        let resolves = if verdict.resolves { "yes" } else { "no" };
        rows.push(format!(
            "| {} | [{}]({}) | {} | {} |",
            link.file, link.path, link.url, resolves, verdict.lines
        ));
    }
    rows.push(String::new());
    rows.push(format!(
        "{} links over {} files, {} missing.",
        found.len(),
        files.len(),
        misses
    ));
    if let Err(e) = fs::write(&out, rows.join("\n") + "\n") {
        eprintln!("{}: {e}", out.display());
        return 2;
    }
    println!(
        "{} links over {} files, {} missing, table at {}",
        found.len(),
        files.len(),
        misses,
        out.display()
    );
    if misses > 0 {
        1
    } else {
        0
    }
}

/// The round's `comment_*.md` files in name order, then the `overview.md` beside the round.
fn round_files(round: &Path) -> std::io::Result<Vec<PathBuf>> {
    let mut files: Vec<PathBuf> = fs::read_dir(round)?
        .flatten()
        .map(|entry| entry.path())
        .filter(|path| {
            let name = dir_name(path);
            name.starts_with("comment_") && name.ends_with(".md")
        })
        .collect();
    files.sort();
    if let Some(parent) = round.parent() {
        let overview = parent.join("overview.md");
        if overview.exists() {
            files.push(overview);
        }
    }
    Ok(files)
}

/// Lines of the file at the sha: through git in the repo when it holds the commit, else through
/// gh api.
fn line_count(repo: Option<&Path>, link: &Link) -> Option<usize> {
    if let Some(repo) = repo {
        let object = format!("{}:{}", link.sha, link.path);
        if let Some(blob) = command_stdout("git", &["-C", &repo.to_string_lossy(), "show", &object])
        {
            return Some(count_lines(&blob));
        }
    }
    let endpoint = format!(
        "repos/{}/{}/contents/{}?ref={}",
        link.owner, link.repo, link.path, link.sha
    );
    command_stdout(
        "gh",
        &["api", "-H", "Accept: application/vnd.github.raw", &endpoint],
    )
    .map(|b| count_lines(&b))
}

#[cfg(test)]
mod tests {
    use super::super::testutil::{shifted_repo, tmp};
    use super::*;

    #[test]
    fn find_links_parses_every_shape() {
        let text = "[a](https://github.com/o/r/blob/0123456789/p/q.go#L3-L5) \
                    [b](https://github.com/o/r/blob/0123456789/d.md?plain=1#L7) \
                    [c](https://github.com/o/r/blob/0123456789/x.rs) \
                    [d](https://example.com/blob/0123456789/x) \
                    [e](https://github.com/o/r/pull/1)";
        let links = find_links("f", text);
        assert_eq!(links.len(), 3);
        assert_eq!(
            (links[0].path.as_str(), links[0].first, links[0].last),
            ("p/q.go", Some(3), Some(5))
        );
        assert_eq!(
            (links[1].path.as_str(), links[1].first, links[1].last),
            ("d.md", Some(7), None)
        );
        assert_eq!(links[2].path, "x.rs");
        assert_eq!(links[2].first, None);
        assert_eq!(
            (links[2].owner.as_str(), links[2].sha.as_str()),
            ("o", "0123456789")
        );
    }

    #[test]
    fn judge_ranges() {
        assert!(!judge(None, Some(1), None).resolves);
        assert_eq!(
            judge(Some(10), None, None),
            Verdict {
                resolves: true,
                lines: "10 lines, no anchor".into()
            }
        );
        assert_eq!(
            judge(Some(10), Some(3), Some(10)),
            Verdict {
                resolves: true,
                lines: "L3-L10 of 10".into()
            }
        );
        assert!(!judge(Some(10), Some(3), Some(11)).resolves);
        assert!(!judge(Some(10), Some(0), None).resolves);
        assert!(!judge(Some(10), Some(5), Some(4)).resolves);
    }

    #[test]
    fn links_over_a_round_directory() {
        let (repo, _first, head) = shifted_repo("links");
        let slug = tmp("links-slug");
        let round = slug.join(format!("1-{head}"));
        fs::create_dir_all(&round).unwrap();
        let draft = format!(
            "[ok](https://github.com/o/r/blob/{head}/f.go#L2-L4) and [far](https://github.com/o/r/blob/{head}/f.go#L9) and [gone](https://github.com/o/r/blob/{head}/nope.go#L1)\n"
        );
        fs::write(round.join("comment_x.md"), draft).unwrap();
        fs::write(
            slug.join("overview.md"),
            format!("[whole](https://github.com/o/r/blob/{head}/f.go)\n"),
        )
        .unwrap();
        let call = || {
            links(&[
                round.to_string_lossy().into_owned(),
                "--repo".into(),
                repo.to_string_lossy().into_owned(),
            ])
        };
        assert_eq!(call(), 1);
        let table = fs::read_to_string(round.join("links.md")).unwrap();
        assert!(
            table.contains("| comment_x.md | [f.go](https://github.com/o/r/blob/"),
            "{table}"
        );
        assert!(table.contains("| yes | L2-L4 of 8 |"), "{table}");
        assert!(table.contains("| no | L9-L9 outside 8 lines |"));
        assert!(table.contains("| no | file missing at the sha |"));
        assert!(
            table.contains("| overview.md | [f.go]")
                && table.contains("| yes | 8 lines, no anchor |")
        );
        assert!(table
            .trim_end()
            .ends_with("4 links over 2 files, 2 missing."));
        fs::write(
            round.join("comment_x.md"),
            format!("[ok](https://github.com/o/r/blob/{head}/f.go#L2-L4)\n"),
        )
        .unwrap();
        assert_eq!(call(), 0);
        assert_eq!(links(&["/nonexistent/round".into()]), 2);
    }
}
