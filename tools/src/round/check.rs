//! `round check`: the mechanical half of the text pass over a round's draft and overview, so the
//! pass keeps only the judgement. An em-dash outside a fence, a visible sentence ending in a
//! question mark, a finding header without its `[gh]` link, a phrase that points at the page
//! instead of the code, a `Full review:` line, and, over the draft, `claims.md`, `findings.md`,
//! `candidates/` and `verdicts/`, an absolute path outside the reviewed repo, which a judge
//! quoting its own command line carries in. One row per hit into `<round dir>/check.md`,
//! exit 1 when any hit.

use std::fs;
use std::path::Path;

use std::sync::LazyLock;

use regex::Regex;

use super::{options, USAGE};

/// Phrases that point at the page instead of the code; each is a reader sent elsewhere.
const POINTERS: [&str; 6] = [
    "see below",
    "see above",
    "as mentioned",
    "the section above",
    "the section below",
    "as noted above",
];

/// One hit: the file, the line, what was found.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Hit {
    pub file: String,
    pub line: usize,
    pub what: String,
}

/// The lines of a file with fenced blocks blanked, so a dash or a question inside code never counts.
fn prose_lines(text: &str) -> Vec<(usize, String)> {
    let mut out = Vec::new();
    let mut fenced = false;
    for (i, line) in text.lines().enumerate() {
        if line.trim_start().starts_with("```") {
            fenced = !fenced;
            out.push((i + 1, String::new()));
            continue;
        }
        out.push((
            i + 1,
            if fenced {
                String::new()
            } else {
                line.to_string()
            },
        ));
    }
    out
}

/// Every hit in one file: `draft` says whether it is the comment draft, whose finding headers must
/// carry the link and whose sentences must not ask.
fn check_text(name: &str, text: &str, draft: bool) -> Vec<Hit> {
    let header = Regex::new(r"^## (SKIP )?\S+:\d+(-\d+)?( |$)").unwrap();
    // The band tag ./scripts/post-review.sh --band selects on, at the header's end. Without it the
    // section is invisible to every selection flag and posting means editing the draft by hand.
    let band = Regex::new(r"(·|\|)\s*(Critical|Warning|Missing test|Nit|Suggestion|Test)\s*$").unwrap();
    let question = Regex::new(r"\?\s*$").unwrap();
    let mut hits = Vec::new();
    let hit = |hits: &mut Vec<Hit>, line: usize, what: &str| {
        hits.push(Hit {
            file: name.to_string(),
            line,
            what: what.to_string(),
        })
    };
    // The Body holds one bullet per unanchored finding, each with its own link, and at most one plain
    // line, the submit sentence or the stale-base line *Body rules* in review-comment.md allows: a
    // second plain line is a paragraph, an affirmation or a re-described change.
    let (mut in_body, mut details, mut plain) = (false, 0i32, 0usize);
    for (line, content) in prose_lines(text) {
        if content.starts_with("## ") {
            in_body = content.trim_end() == "## Body";
        }
        let t = content.trim_start();
        // A fold opened and closed on one line leaves the depth where it was.
        let opens = t.matches("<details").count() as i32;
        let closes = t.matches("</details").count() as i32;
        if opens > 0 || closes > 0 {
            details = (details + opens - closes).max(0);
        } else if draft && in_body && details == 0 && !t.is_empty() && !content.starts_with("## ")
            && !t.starts_with(['<', '>', '!', '['])
        {
            let numbered = content.split_once(". ").is_some_and(|(n, _)| !n.is_empty() && n.chars().all(|c| c.is_ascii_digit()));
            if !(content.starts_with("- ") || content.starts_with("* ") || numbered || content.starts_with(' ')) {
                plain += 1;
                if plain > 1 {
                    hit(&mut hits, line, "a second Body line outside a bullet");
                }
            } else if !content.starts_with(' ') && !content.contains("](") {
                hit(&mut hits, line, "Body bullet without its own link");
            }
        }
        if content.is_empty() {
            continue;
        }
        if content.contains('\u{2014}') {
            hit(&mut hits, line, "em-dash");
        }
        let lower = content.to_lowercase();
        for p in POINTERS {
            if lower.contains(p) {
                hit(&mut hits, line, &format!("points at the page: \"{p}\""));
            }
        }
        if draft {
            if content.starts_with("## ") && header.is_match(&content) && !content.contains("[gh](")
            {
                hit(&mut hits, line, "finding header without its [gh] link");
            }
            if content.starts_with("## ") && header.is_match(&content) && !band.is_match(&content) {
                hit(
                    &mut hits,
                    line,
                    "finding header without its band tag, ' · <Band>' at the end",
                );
            }
            if !content.starts_with('#')
                && !content.starts_with('>')
                && !content.starts_with('|')
                && !content.starts_with('<')
                && question.is_match(content.trim_end())
            {
                hit(&mut hits, line, "a visible sentence ending in a question");
            }
            if content.starts_with("Full review:") {
                hit(&mut hits, line, "a Full review: line");
            }
        }
    }
    hits
}

/// The table `check.md` holds, and the summary line.
fn table(hits: &[Hit]) -> String {
    let mut out = String::from("| File | Line | Found |\n| --- | --- | --- |\n");
    for h in hits {
        out.push_str(&format!("| {} | {} | {} |\n", h.file, h.line, h.what));
    }
    out
}

/// The command: every `comment_*.md` in the round directory as the draft, the `overview.md` beside
/// the directory as prose; `check.md` written, the hits printed, exit 1 on any.
pub fn check_cmd(args: &[String]) -> i32 {
    match run(args) {
        Ok(hits) => {
            for h in &hits {
                println!("{}:{}: {}", h.file, h.line, h.what);
            }
            println!(
                "{} hit{}",
                hits.len(),
                if hits.len() == 1 { "" } else { "s" }
            );
            if hits.is_empty() {
                0
            } else {
                1
            }
        }
        Err(why) => {
            eprintln!("{why}\n\n{USAGE}");
            2
        }
    }
}

/// The work of `check_cmd`.
fn run(args: &[String]) -> Result<Vec<Hit>, String> {
    let round = Path::new(&args[0]);
    let opts = options(args)?;
    let mut hits = Vec::new();
    let mut drafts = 0;
    let entries = fs::read_dir(round).map_err(|e| format!("{}: {e}", round.display()))?;
    let mut names: Vec<_> = entries
        .flatten()
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .collect();
    names.sort();
    for name in names {
        if name.starts_with("comment_") && name.ends_with(".md") {
            drafts += 1;
            let text = fs::read_to_string(round.join(&name)).map_err(|e| format!("{name}: {e}"))?;
            hits.extend(check_text(&name, &text, true));
        }
    }
    if drafts == 0 {
        return Err(format!("{}: no comment_*.md", round.display()));
    }
    let overview = match opts.get("overview") {
        Some(p) => Path::new(p).to_path_buf(),
        None => round.join("..").join("overview.md"),
    };
    if let Ok(text) = fs::read_to_string(&overview) {
        hits.extend(check_text("overview.md", &text, false));
    }
    if let Some(list) = opts.get("private") {
        hits.extend(private_names(round, list)?);
    }
    hits.extend(absolute_paths(round, &overview));
    for file in round.read_dir().into_iter().flatten().flatten().map(|e| e.path()).chain([overview.clone()]) {
        let name = file.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        // The draft posts to the target, where a bare number resolves; these two render only here.
        let wanted = name == "claims.md" || name == "overview.md";
        if let (true, Ok(text)) = (wanted, fs::read_to_string(&file)) {
            hits.extend(bare_refs(&name, &text));
        }
    }
    let out = opts
        .get("out")
        .map(|p| Path::new(p).to_path_buf())
        .unwrap_or_else(|| round.join("check.md"));
    fs::write(&out, table(&hits)).map_err(|e| format!("{}: {e}", out.display()))?;
    Ok(hits)
}

/// Every whole-word hit of a name in `list` over the round's draft, claims.md, candidates/ and
/// verdicts/: a private repository name reaches a public artifact through the target's own body,
/// and nothing between the finder and the commit reads the round against the list otherwise.
fn private_names(round: &Path, list: &str) -> Result<Vec<Hit>, String> {
    let names: Vec<String> = fs::read_to_string(list)
        .map_err(|e| format!("{list}: {e}"))?
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty())
        .map(String::from)
        .collect();
    let mut hits = Vec::new();
    for f in record_files(round) {
        let text = fs::read_to_string(&f).unwrap_or_default();
        let short = short_name(round, &f);
        for (i, line) in text.lines().enumerate() {
            for name in &names {
                let re = Regex::new(&format!(r"(?i)(^|[^A-Za-z0-9_-]){}([^A-Za-z0-9_-]|$)", regex::escape(name))).unwrap();
                if re.is_match(line) {
                    hits.push(Hit { file: short.clone(), line: i + 1, what: format!("private name: {name}") });
                }
            }
        }
    }
    Ok(hits)
}

/// A local path a verifier quoted from its own command line: a home directory, the scratch
/// directory, a worktree. The reviewed repo's own paths are relative and never match.
/// A `#<number>` with nothing before it but a space, a bracket's opening or punctuation: GitHub
/// links it to the repository the file renders in, the workspace, never the target.
static BARE_REF: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"(^|[\s(,;:])#\d+\b").unwrap());
static CODE_SPAN: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"`[^`]*`|\[[^\]]*\]\([^)]*\)").unwrap());

/// Every bare `#<number>` in prose, outside fences, code spans and links.
fn bare_refs(name: &str, text: &str) -> Vec<Hit> {
    prose_lines(text)
        .into_iter()
        .filter(|(_, content)| BARE_REF.is_match(&CODE_SPAN.replace_all(content, "")))
        .map(|(line, _)| Hit {
            file: name.to_string(),
            line,
            what: "bare #<number>: it links to the repository the file renders in; write <owner>/<repo>#<number> or a link".to_string(),
        })
        .collect()
}

static LOCAL_PATH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r#"(^|[^A-Za-z0-9_./-])((/home/|/Users/|/root/|/tmp/claude|/tmp/agent-workspace|(/[^\s"'`)]*)?/\.worktrees/)[^\s"'`)]*)"#).unwrap()
});

/// Every absolute path outside the reviewed repo over the round's record and the overview.
fn absolute_paths(round: &Path, overview: &Path) -> Vec<Hit> {
    let mut files = record_files(round);
    if overview.is_file() {
        files.push(overview.to_path_buf());
    }
    let mut hits = Vec::new();
    for f in files {
        let text = fs::read_to_string(&f).unwrap_or_default();
        let short = short_name(round, &f);
        for (i, line) in text.lines().enumerate() {
            if let Some(m) = LOCAL_PATH.captures(line) {
                let path: String = m[2].chars().take(60).collect();
                hits.push(Hit { file: short.clone(), line: i + 1, what: format!("absolute path: {path}") });
            }
        }
    }
    hits
}

/// The file's name relative to the round, for the table.
fn short_name(round: &Path, f: &Path) -> String {
    f.strip_prefix(round)
        .map(|p| p.to_string_lossy().into_owned())
        .unwrap_or_else(|_| f.to_string_lossy().into_owned())
}

/// The round's record: the draft, `claims.md`, `findings.md`, `candidates/` and `verdicts/`.
fn record_files(round: &Path) -> Vec<std::path::PathBuf> {
    let mut files: Vec<std::path::PathBuf> = Vec::new();
    if let Ok(entries) = fs::read_dir(round) {
        for e in entries.flatten() {
            let p = e.path();
            let name = e.file_name().to_string_lossy().into_owned();
            if p.is_file() && (name.starts_with("comment_") || name == "claims.md" || name == "findings.md") {
                files.push(p);
            } else if p.is_dir() && (name == "candidates" || name == "verdicts" || name == "tests") {
                if let Ok(inner) = fs::read_dir(&p) {
                    files.extend(inner.flatten().map(|f| f.path()).filter(|f| f.is_file()));
                }
            }
        }
    }
    files.sort();
    files
}

#[cfg(test)]
mod tests {
    use super::super::testutil::tmp;
    use super::*;

    #[test]
    fn a_bare_number_reference_is_a_hit_and_a_qualified_or_linked_one_is_not() {
        let round = round_with("check-bare", "# Review: [#160](https://github.com/o/r/pull/160)\n\n## pkg/a.go:10 [gh](https://x/a.go#L10) \u{b7} Warning\nPR #160's bound, posted where it resolves.\n", "# S\n\n[Issue #159](https://x) and o/r#12 and `#9`.\n");
        fs::write(round.join("claims.md"), "# Claims: #160 round 1\n").unwrap();
        let code = check_cmd(&[round.display().to_string()]);
        assert_eq!(code, 1);
        let table = fs::read_to_string(round.join("check.md")).unwrap();
        assert!(table.contains("claims.md") && table.contains("bare #<number>"), "{table}");
        assert!(!table.contains("comment_x.md") && !table.contains("overview.md"), "a draft, a link, a qualified or a code-span number is not a hit: {table}");
    }

    #[test]
    fn a_private_name_in_a_candidate_is_a_hit() {
        let round = round_with("check-private", "# Review\n\n## pkg/a.go:10 [gh](https://x/a.go#L10) \u{b7} Warning\nFine.\n", "# S\n\nOk.\n");
        fs::create_dir_all(round.join("candidates")).unwrap();
        fs::write(round.join("candidates").join("find-1.json"), "{\"summary\": \"tracked in acme/secret-fixes#12\"}\n").unwrap();
        let list = round.join("names.txt");
        fs::write(&list, "secret-fixes\nacme/secret-fixes\n").unwrap();
        let code = check_cmd(&[round.display().to_string(), "--private".into(), list.display().to_string()]);
        assert_eq!(code, 1);
        let table = fs::read_to_string(round.join("check.md")).unwrap();
        assert!(table.contains("private name: secret-fixes"), "{table}");
    }

    #[test]
    fn an_absolute_path_in_the_record_is_a_hit_and_a_repo_path_is_not() {
        let round = round_with("check-abs", "# Review\n\n## pkg/a.go:10 [gh](https://x/a.go#L10) \u{b7} Warning\nRun `go test ./pkg` from the clone.\n", "# S\n\nOk.\n");
        fs::create_dir_all(round.join("verdicts")).unwrap();
        fs::write(round.join("verdicts").join("judge-1.json"), "{\"evidence\": \"grep -n Foo /home/someone/work/.worktrees/repo-1/pkg/a.go: 12\"}\n").unwrap();
        fs::write(round.join("claims.md"), "| 1 | CONFIRMED | Warning | pkg/a.go:10 | grep -n Foo pkg/a.go | 12 | | hot |\n").unwrap();
        let code = check_cmd(&[round.display().to_string()]);
        assert_eq!(code, 1);
        let table = fs::read_to_string(round.join("check.md")).unwrap();
        assert!(table.contains("verdicts/judge-1.json") && table.contains("absolute path: /home/someone/work/.worktrees/repo-1/pkg/a.go"), "{table}");
        assert!(!table.contains("claims.md"), "a relative path is not a hit: {table}");
    }

    #[test]
    fn a_scratch_path_in_a_test_artifact_is_a_hit_and_a_repro_path_is_not() {
        let round = round_with("check-tests", "# Review\n\n## pkg/a.go:10 [gh](https://x/a.go#L10) \u{b7} Warning\nFine.\n", "# S\n\nOk.\n");
        fs::create_dir_all(round.join("tests")).unwrap();
        fs::write(round.join("tests").join("judge-1-x.patch"), "--- a/pkg/a.go\n+++ /tmp/agent-workspace/s/work/judge-1/pkg/a.go\n").unwrap();
        fs::write(round.join("tests").join("find-2-y.sh"), "go build -o /tmp/gnopreview .\n").unwrap();
        assert_eq!(check_cmd(&[round.display().to_string()]), 1);
        let table = fs::read_to_string(round.join("check.md")).unwrap();
        assert!(table.contains("tests/judge-1-x.patch | 2 | absolute path: /tmp/agent-workspace/s"), "{table}");
        assert!(!table.contains("find-2-y.sh"), "a repro's own /tmp output is not a hit: {table}");
    }

    fn round_with(name: &str, draft: &str, overview: &str) -> std::path::PathBuf {
        let slug = tmp(name);
        let round = slug.join("1-abc");
        fs::create_dir_all(&round).unwrap();
        fs::write(round.join("comment_x.md"), draft).unwrap();
        fs::write(slug.join("overview.md"), overview).unwrap();
        round
    }

    #[test]
    fn a_clean_draft_has_no_hits() {
        let round = round_with(
            "check-clean",
            "# Review\n\n## pkg/a.go:10 [gh](https://x/a.go#L10) \u{b7} Warning\nThe clamp is missing.\n\n```go\n// a — dash in code is fine?\n```\n",
            "# Subject\n\nWhat it is for.\n",
        );
        assert_eq!(check_cmd(&[round.display().to_string()]), 0);
        assert_eq!(
            fs::read_to_string(round.join("check.md"))
                .unwrap()
                .lines()
                .count(),
            2
        );
    }

    #[test]
    fn dashes_questions_missing_links_and_pointers_are_hits() {
        let round = round_with(
            "check-dirty",
            "# Review\n\n## SKIP pkg/a.go:10\nIs the clamp missing?\nFull review: elsewhere\n\n## pkg/b.go:4-6 [gh](https://x)\nSee below — the guard.\n",
            "# Subject\n\nAs mentioned, the tree — see above.\n",
        );
        assert_eq!(check_cmd(&[round.display().to_string()]), 1);
        let table = fs::read_to_string(round.join("check.md")).unwrap();
        for what in [
            "finding header without its [gh] link",
            "a visible sentence ending in a question",
            "a Full review: line",
            "em-dash",
            "points at the page: \"see below\"",
            "points at the page: \"as mentioned\"",
            "points at the page: \"see above\"",
            "finding header without its band tag",
        ] {
            assert!(table.contains(what), "{what} missing in\n{table}");
        }
        assert!(table.contains("| overview.md | 3 |"), "{table}");
    }

    #[test]
    fn a_numbered_body_list_is_bullets_and_a_one_line_fold_closes() {
        let numbered = check_text("comment_x.md", "# Review\n\n## Body\nOne sentence.\n1. [f](https://x) is dead.\n2. [g](https://x) is dead.\n", true);
        assert!(numbered.is_empty(), "{:?}", numbered.iter().map(|h| &h.what).collect::<Vec<_>>());
        let folded = check_text("comment_x.md", "# Review\n\n## Body\n<details><summary>s</summary>x</details>\nFirst.\nSecond.\n", true);
        assert_eq!(folded.iter().map(|h| (h.line, h.what.as_str())).collect::<Vec<_>>(), vec![(6, "a second Body line outside a bullet")]);
    }

    #[test]
    fn a_second_plain_body_line_and_an_unlinked_bullet_are_hits() {
        let hits = check_text(
            "comment_x.md",
            "# Review\n\n## Body\nOne true sentence.\n- [`f`](https://x) is never called.\n- `g` is dead.\nComment-only in Go: `pipe.go` changes no statement.\n\n<details>\n<summary>Sweep</summary>\nprose in details\n</details>\n\n## pkg/a.go:10 [gh](https://x) \u{b7} Warning\nThe clamp is missing.\n",
            true,
        );
        let what: Vec<_> = hits.iter().map(|h| (h.line, h.what.as_str())).collect();
        assert_eq!(what, vec![(6, "Body bullet without its own link"), (7, "a second Body line outside a bullet")]);
    }

    #[test]
    fn a_round_without_a_draft_is_an_error() {
        let round = tmp("check-empty");
        assert_eq!(check_cmd(&[round.display().to_string()]), 2);
    }
}
