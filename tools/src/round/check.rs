//! `round check`: the mechanical half of the text pass over a round's draft and overview, so the
//! pass keeps only the judgement. An em-dash outside a fence, a visible sentence ending in a
//! question mark, a finding header without its `[gh]` link, a phrase that points at the page
//! instead of the code, a `Full review:` line. One row per hit into `<round dir>/check.md`,
//! exit 1 when any hit.

use std::fs;
use std::path::Path;

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
    for (line, content) in prose_lines(text) {
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
    let out = opts
        .get("out")
        .map(|p| Path::new(p).to_path_buf())
        .unwrap_or_else(|| round.join("check.md"));
    fs::write(&out, table(&hits)).map_err(|e| format!("{}: {e}", out.display()))?;
    Ok(hits)
}

#[cfg(test)]
mod tests {
    use super::super::testutil::tmp;
    use super::*;

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
    fn a_round_without_a_draft_is_an_error() {
        let round = tmp("check-empty");
        assert_eq!(check_cmd(&[round.display().to_string()]), 2);
    }
}
