// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! `round stop`: whether a fix loop stops, from a round's `claims.md` or a pass's own list and
//! the diff the pass before wrote. It stops when no Critical or Warning survives, or when every
//! one sits on a line `git diff -U0 -M <prev> <head>` changed, per *Fix* step 8 in
//! `skills/change.md`. With `--prior <slug dir>`, a Warning whose Mechanism cell names the
//! mechanism of an earlier round's unrefuted row counts as on the fix too, per *Own PR* in
//! `skills/review-modes.md`: the loop is patching one mechanism shape by shape.
use super::{command, dir_name, options, Hunk, LineMap, USAGE};
use regex::Regex;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;

/// A Critical or Warning that no judge refuted, and the mechanism its judge named, empty where
/// the table has no Mechanism column or the judge named none.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Blocking {
    pub band: String,
    pub anchor: String,
    pub mechanism: String,
}

/// The header of a Candidates table, with or without its leading `#` column.
static HEADER: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\|\s*(?:#\s*\|\s*)?State\s*\|\s*Band\s*\|").unwrap());

static ROW: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^\|\s*(?:\d*\s*\|\s*)?(CONFIRMED|PLAUSIBLE|UNVERIFIED|REFUTED)\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|")
        .unwrap()
});

/// A band cell opening on a band that blocks: `Warning, not posted` is a Warning.
static BLOCKING_BAND: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^(Critical|Warning)\b").unwrap());

/// A step-8 pass's own list: one `<Band> <file:line>` per line, or `none`.
static LINE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^(Critical|Warning|Suggestion|Nit|Missing test)\s+(\S+)$").unwrap()
});

/// A table line's cells, split on every pipe `cell` in `assemble.rs` left unescaped, so a Check
/// holding `\|` stays one cell.
fn cells(line: &str) -> Vec<String> {
    let line = line.trim();
    let line = line.strip_prefix('|').unwrap_or(line);
    let mut out = vec![String::new()];
    let mut chars = line.chars().peekable();
    while let Some(c) = chars.next() {
        match c {
            '\\' if chars.peek() == Some(&'|') => {
                out.last_mut().unwrap().push_str("\\|");
                chars.next();
            }
            '|' => out.push(String::new()),
            _ => out.last_mut().unwrap().push(c),
        }
    }
    if out.len() > 1 && out.last().is_some_and(|c| c.trim().is_empty()) {
        out.pop();
    }
    out.into_iter().map(|c| c.trim().to_string()).collect()
}

/// Every Critical and Warning that still blocks the stop. A text holding a Candidates header is
/// read as `claims.md`, its rows in any state but REFUTED, each with the cell under the latest
/// header's Mechanism column, counted from the end so a row without its `#` cell still finds it;
/// any other text is a pass's list, and a line in it that is neither `<Band> <file:line>` nor
/// `none` is an error, never a skipped row.
pub fn blocking_rows(text: &str) -> Result<Vec<Blocking>, String> {
    let blocking = |band: &str, anchor: &str, mechanism: &str| Blocking {
        band: band.to_string(),
        anchor: anchor.trim().to_string(),
        mechanism: mechanism.trim_matches('`').to_string(),
    };
    if text.lines().any(|line| HEADER.is_match(line)) {
        let mut rows = Vec::new();
        // The Mechanism column's place from the end of the latest header, None before one has it.
        let mut from_end: Option<usize> = None;
        for line in text.lines() {
            if HEADER.is_match(line) {
                let head = cells(line);
                from_end = head
                    .iter()
                    .position(|c| c == "Mechanism")
                    .map(|at| head.len() - at);
                continue;
            }
            let Some(caps) = ROW.captures(line) else {
                continue;
            };
            if &caps[1] == "REFUTED" {
                continue;
            }
            let Some(band) = BLOCKING_BAND.captures(&caps[2]) else {
                continue;
            };
            let row = cells(line);
            let mechanism = from_end
                .and_then(|k| row.len().checked_sub(k))
                .map_or("", |at| row[at].as_str());
            rows.push(blocking(&band[1], &caps[3], mechanism));
        }
        return Ok(rows);
    }
    let mut rows = Vec::new();
    for (n, line) in text.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line == "none" {
            continue;
        }
        let caps = LINE.captures(line).ok_or_else(|| {
            format!(
                "line {}: neither `<Band> <file:line>` nor a Candidates table: {line}",
                n + 1
            )
        })?;
        if matches!(&caps[1], "Critical" | "Warning") {
            rows.push(blocking(&caps[1], &caps[2], ""));
        }
    }
    Ok(rows)
}

/// Whether the hunk changed `line` at the new side: inside its added range, or, for a pure
/// deletion `+<start>,0`, on either line the removed span sat between.
pub fn touches(hunk: &Hunk, line: usize) -> bool {
    if hunk.new_len == 0 {
        line == hunk.new_start || line == hunk.new_start + 1
    } else {
        line >= hunk.new_start && line < hunk.new_start + hunk.new_len
    }
}

/// The hunks of a whole `git diff -U0 -M`, keyed by each file's path at the new side, so a file
/// the diff renamed carries only the lines it changed.
pub fn hunks_by_path(diff: &str) -> HashMap<String, Vec<Hunk>> {
    let mut out: HashMap<String, Vec<Hunk>> = HashMap::new();
    let mut path: Option<String> = None;
    for line in diff.lines() {
        if let Some(new) = line.strip_prefix("+++ ") {
            path = new.strip_prefix("b/").map(str::to_string);
        } else if line.starts_with("@@ ") {
            if let Some(p) = &path {
                out.entry(p.clone())
                    .or_default()
                    .extend(LineMap::parse(line).hunks);
            }
        }
    }
    out
}

/// The hunks `<prev>..<head>` wrote in `repo`; Err when either sha is not a commit there.
pub fn fix_hunks(
    repo: &Path,
    prev: &str,
    head: &str,
) -> Result<HashMap<String, Vec<Hunk>>, String> {
    let repo = repo.to_string_lossy();
    for sha in [prev, head] {
        command(
            "git",
            &[
                "-C",
                &repo,
                "rev-parse",
                "--verify",
                "--quiet",
                &format!("{sha}^{{commit}}"),
            ],
        )
        .map_err(|_| format!("{sha} is not a commit in {repo}"))?;
    }
    let diff = command(
        "git",
        &[
            "-C",
            &repo,
            "diff",
            "-U0",
            "-M",
            "--no-color",
            "--src-prefix=a/",
            "--dst-prefix=b/",
            prev,
            head,
        ],
    )?;
    Ok(hunks_by_path(&String::from_utf8_lossy(&diff)))
}

/// Where a blocking row sits against the previous pass's diff.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Place {
    OnFix,
    Outside,
    /// No `file:line` anchor: nothing proves it sits on the fix, so it blocks the stop.
    Unanchored,
}

fn split_anchor(anchor: &str) -> Option<(&str, usize)> {
    let (path, line) = anchor.trim_matches('`').rsplit_once(':')?;
    let first = line.split('-').next().unwrap_or(line);
    Some((path, first.parse().ok()?))
}

/// Each blocking row's place against the fix's hunks.
pub fn place_rows(rows: &[Blocking], hunks: &HashMap<String, Vec<Hunk>>) -> Vec<Place> {
    rows.iter()
        .map(|row| match split_anchor(&row.anchor) {
            None => Place::Unanchored,
            Some((path, line)) => {
                let on_fix = hunks
                    .get(path)
                    .is_some_and(|hs| hs.iter().any(|h| touches(h, line)));
                if on_fix {
                    Place::OnFix
                } else {
                    Place::Outside
                }
            }
        })
        .collect()
}

/// The mechanism of every unrefuted Critical and Warning in the slug's rounds before `own`, the
/// round directory the input sits in: `(round directory, mechanism)`, held rows included, since a
/// row the author kept open names its mechanism as surely as one a commit closed. A round is
/// earlier by the number its directory opens on; a directory with none is read unless it is
/// `own`. A claims.md with no Mechanism column gives nothing.
pub fn prior_mechanisms(slug: &Path, own: &str) -> Result<Vec<(String, String)>, String> {
    let number = |name: &str| name.split('-').next().and_then(|n| n.parse::<usize>().ok());
    let own_n = number(own);
    let mut dirs: Vec<(Option<usize>, String, PathBuf)> = fs::read_dir(slug)
        .map_err(|e| format!("{}: {e}", slug.display()))?
        .flatten()
        .map(|entry| entry.path())
        .filter(|path| path.join("claims.md").exists())
        .map(|path| (number(&dir_name(&path)), dir_name(&path), path))
        .filter(|(n, name, _)| name != own && !matches!((n, own_n), (Some(n), Some(o)) if n >= &o))
        .collect();
    dirs.sort();
    let mut out = Vec::new();
    for (_, name, path) in dirs {
        let text = fs::read_to_string(path.join("claims.md")).unwrap_or_default();
        for row in blocking_rows(&text).unwrap_or_default() {
            if !row.mechanism.is_empty() {
                out.push((name.clone(), row.mechanism));
            }
        }
    }
    Ok(out)
}

/// For each row, the earlier round whose row names the same mechanism, when the row is a Warning
/// and its mechanism is not empty; case and surrounding space aside, the slugs must be equal.
pub fn recurring(rows: &[Blocking], prior: &[(String, String)]) -> Vec<Option<String>> {
    rows.iter()
        .map(|row| {
            let mechanism = row.mechanism.trim().to_lowercase();
            if row.band != "Warning" || mechanism.is_empty() {
                return None;
            }
            prior
                .iter()
                .find(|(_, m)| m.trim().to_lowercase() == mechanism)
                .map(|(round, _)| round.clone())
        })
        .collect()
}

pub fn stop(args: &[String]) -> i32 {
    let input = PathBuf::from(&args[0]);
    let opts = match options(args) {
        Ok(opts) => opts,
        Err(e) => {
            eprintln!("{e}\n{USAGE}");
            return 2;
        }
    };
    let (Some(repo), Some(prev), Some(head)) =
        (opts.get("repo"), opts.get("prev"), opts.get("head"))
    else {
        eprintln!("--repo, --prev and --head are required\n{USAGE}");
        return 2;
    };
    let rows = match fs::read_to_string(&input)
        .map_err(|e| e.to_string())
        .and_then(|t| blocking_rows(&t))
    {
        Ok(rows) => rows,
        Err(e) => {
            eprintln!("{}: {e}", input.display());
            return 2;
        }
    };
    let hunks = match fix_hunks(Path::new(repo), prev, head) {
        Ok(hunks) => hunks,
        Err(e) => {
            eprintln!("{e}");
            return 2;
        }
    };
    let prior = match opts.get("prior") {
        Some(slug) => {
            let own = input.parent().map(dir_name).unwrap_or_default();
            match prior_mechanisms(Path::new(slug), &own) {
                Ok(prior) => prior,
                Err(e) => {
                    eprintln!("{e}");
                    return 2;
                }
            }
        }
        None => Vec::new(),
    };
    let mut places = place_rows(&rows, &hunks);
    let recurs = recurring(&rows, &prior);
    for ((row, place), earlier) in rows.iter().zip(places.iter_mut()).zip(&recurs) {
        if earlier.is_some() {
            *place = Place::OnFix;
        }
        let word = match place {
            Place::OnFix => "on the fix",
            Place::Outside => "outside",
            Place::Unanchored => "unanchored",
        };
        let mechanism = match (row.mechanism.as_str(), earlier) {
            ("", _) => String::new(),
            (m, Some(round)) => format!("\tmechanism {m}, as in {round}"),
            (m, None) => format!("\tmechanism {m}"),
        };
        println!("{word}\t{}\t{}{mechanism}", row.band, row.anchor);
    }
    let blocking = places.iter().filter(|p| **p != Place::OnFix).count();
    let by_mechanism = recurs.iter().any(Option::is_some);
    if rows.is_empty() {
        println!("stop: no Critical or Warning");
        0
    } else if blocking == 0 && by_mechanism {
        println!("stop: every Critical and Warning sits on lines {prev}..{head} changed or repeats an earlier round's mechanism; measure a design that removes the mechanism, per Own PR in skills/review-modes.md");
        0
    } else if blocking == 0 {
        println!("stop: every Critical and Warning sits on lines {prev}..{head} changed");
        0
    } else {
        println!("another pass: {blocking} Critical or Warning outside {prev}..{head}");
        1
    }
}

#[cfg(test)]
mod tests {
    use super::super::testutil::{git, tmp};
    use super::*;

    fn hunk(new_start: usize, new_len: usize) -> Hunk {
        Hunk {
            old_start: 1,
            old_len: 1,
            new_start,
            new_len,
        }
    }

    #[test]
    fn touches_added_ranges_and_deletions() {
        assert!(touches(&hunk(5, 3), 5) && touches(&hunk(5, 3), 7));
        assert!(!touches(&hunk(5, 3), 4) && !touches(&hunk(5, 3), 8));
        assert!(touches(&hunk(8, 0), 8) && touches(&hunk(8, 0), 9));
        assert!(!touches(&hunk(8, 0), 10));
        assert!(
            touches(&hunk(0, 0), 1),
            "a deletion at the top touches line 1"
        );
    }

    fn anchors(text: &str) -> Vec<String> {
        blocking_rows(text)
            .unwrap()
            .into_iter()
            .map(|r| r.anchor)
            .collect()
    }

    #[test]
    fn a_candidates_table_keeps_its_unrefuted_criticals_and_warnings() {
        let claims = "| # | State | Band | file:line | Check |\n\
            | --- | --- | --- | --- | --- |\n\
            | 1 | CONFIRMED | Warning | a.go:3 | x |\n\
            | 2 | REFUTED | Critical | a.go:4 | x |\n\
            | 3 | PLAUSIBLE | Critical | `b.go:9-12` | x |\n\
            | 4 | CONFIRMED | Suggestion | a.go:5 | x |\n\
            | 5 | CONFIRMED | Warning, not posted | d.go:2 | x |\n\
            | UNVERIFIED | Warning | c.go:1 | x |\n\
            | claims | a.go:3 | suspected | settled |\n";
        assert_eq!(
            anchors(claims),
            ["a.go:3", "`b.go:9-12`", "d.go:2", "c.go:1"]
        );
    }

    #[test]
    fn a_pass_list_is_read_strictly() {
        let list = "Warning f.go:2\nCritical `g.go:7`\nSuggestion f.go:3\n\nnone\n";
        assert_eq!(anchors(list), ["f.go:2", "`g.go:7`"]);
        for bad in [
            "- Warning f.go:1",
            "**Warning** f.go:1",
            "Warning: f.go:1",
            "WARNING f.go:1",
            "Warning f.go:1 the stop is wrong",
        ] {
            assert!(
                blocking_rows(bad).is_err(),
                "a line of another shape is an error: {bad}"
            );
        }
        let outcomes =
            "| Section | Band | Outcome |\n| --- | --- | --- |\n| a.go:3 | Warning | open |\n";
        assert!(
            blocking_rows(outcomes).is_err(),
            "a table that is not the Candidates table is an error"
        );
    }

    fn mechanisms(text: &str) -> Vec<String> {
        blocking_rows(text)
            .unwrap()
            .into_iter()
            .map(|r| r.mechanism)
            .collect()
    }

    #[test]
    fn the_mechanism_cell_is_read_from_the_end_and_an_old_table_has_none() {
        let claims = "| # | State | Band | file:line | Check | Observed | Artifact | Tier | Mechanism |\n\
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n\
            | 1 | CONFIRMED | Warning | a.go:3 | go test -run A \\| go test -run B | red | | hot | code-fence-parse |\n\
            | 2 | PLAUSIBLE | Critical | a.go:9 | x | | | hot | |\n\
            | UNVERIFIED | Warning | c.go:1 | x | | | cold | `nest-depth` |\n";
        assert_eq!(
            mechanisms(claims),
            ["code-fence-parse", "", "nest-depth"],
            "an escaped pipe stays in its cell, an empty cell is no mechanism, a row without # still finds the column"
        );
        let old = "| # | State | Band | file:line | Check | Observed | Artifact | Tier |\n\
            | 1 | CONFIRMED | Warning | a.go:3 | x | red | | code-fence-parse |\n";
        assert_eq!(mechanisms(old), [""], "no Mechanism header, no mechanism, whatever the last cell holds");
        let two = format!("{claims}\n## Critical pass 1\n\n{old}");
        assert_eq!(
            mechanisms(&two),
            ["code-fence-parse", "", "nest-depth", ""],
            "each row reads the header above it"
        );
    }

    const HEADER_9: &str = "| # | State | Band | file:line | Check | Observed | Artifact | Tier | Mechanism |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n";

    /// An own pull request loop's slug: round 2 holds the code-fence Warning the author kept
    /// open and a refuted row, round 3 a padding fix, round 4 the foreign-body Warning on the
    /// code-fence mechanism, and round 5 one that must not count as earlier than round 4.
    fn loop_slug(name: &str) -> PathBuf {
        let slug = tmp(name);
        let round = |dir: &str, rows: &str| {
            fs::create_dir_all(slug.join(dir)).unwrap();
            fs::write(slug.join(dir).join("claims.md"), format!("## Candidates\n\n{HEADER_9}{rows}")).unwrap();
        };
        round("2-aaa", "| 2 | CONFIRMED | Warning | f.go:3 | x | | | hot | code-fence-parse |\n| 9 | REFUTED | Warning | f.go:4 | x | | | hot | tilde-fence |\n");
        round("3-bbb", "| 1 | CONFIRMED | Warning | f.go:2 | x | | | hot | summary-offset |\n");
        round("4-ccc", "| 1 | CONFIRMED | Warning | f.go:6 | x | | | hot | Code-Fence-Parse |\n| 2 | CONFIRMED | Critical | f.go:7 | x | | | hot | summary-offset |\n| 3 | CONFIRMED | Warning | f.go:1 | x | | | hot | tilde-fence |\n");
        round("5-ddd", "| 1 | CONFIRMED | Warning | f.go:1 | x | | | hot | tilde-fence |\n");
        fs::create_dir_all(slug.join("1-old")).unwrap();
        fs::write(slug.join("1-old/claims.md"), "| # | State | Band | file:line | Check | Observed | Artifact | Tier |\n| 1 | CONFIRMED | Warning | f.go:1 | x | | | hot |\n").unwrap();
        slug
    }

    #[test]
    fn a_warning_on_an_earlier_rounds_mechanism_recurs_and_a_critical_does_not() {
        let slug = loop_slug("stop-prior");
        let prior = prior_mechanisms(&slug, "4-ccc").unwrap();
        assert_eq!(
            prior,
            [("2-aaa".to_string(), "code-fence-parse".to_string()), ("3-bbb".to_string(), "summary-offset".to_string())],
            "earlier rounds only, the refuted row and the old table left out"
        );
        let rows = blocking_rows(&fs::read_to_string(slug.join("4-ccc/claims.md")).unwrap()).unwrap();
        assert_eq!(
            recurring(&rows, &prior),
            [Some("2-aaa".to_string()), None, None],
            "the Warning matches case aside; the Critical waits on its line; a refuted mechanism is no match"
        );
        assert!(prior_mechanisms(&slug.join("absent"), "4-ccc").is_err());
    }

    fn run_with(repo: &Path, prev: &str, head: &str, input: &Path, extra: &[&str]) -> i32 {
        let mut args: Vec<String> = [
            &*input.to_string_lossy(),
            "--repo",
            &repo.to_string_lossy(),
            "--prev",
            prev,
            "--head",
            head,
        ]
        .iter()
        .map(|s| s.to_string())
        .collect();
        args.extend(extra.iter().map(|s| s.to_string()));
        stop(&args)
    }

    #[test]
    fn a_loop_stops_on_the_held_rows_mechanism() {
        let (repo, prev, head) = fixed_repo("stop-held");
        let slug = tmp("stop-held-slug");
        fs::create_dir_all(slug.join("2-aaa")).unwrap();
        fs::create_dir_all(slug.join("4-ccc")).unwrap();
        fs::write(
            slug.join("2-aaa/claims.md"),
            format!("{HEADER_9}| 2 | CONFIRMED | Warning | f.go:6 | x | | | hot | code-fence-parse |\n\n## Applied\n\nRow 2 waits on the author.\n"),
        )
        .unwrap();
        let input = slug.join("4-ccc/claims.md");
        fs::write(
            &input,
            format!("{HEADER_9}| 1 | CONFIRMED | Warning | f.go:6 | x | | | hot | code-fence-parse |\n| 2 | CONFIRMED | Warning | f.go:2 | x | | | hot | |\n"),
        )
        .unwrap();
        let prior = slug.to_string_lossy().to_string();
        assert_eq!(run_with(&repo, &prev, &head, &input, &[]), 1, "by line alone, f.go:6 sits outside the fix");
        assert_eq!(
            run_with(&repo, &prev, &head, &input, &["--prior", &prior]),
            0,
            "f.go:6 repeats round 2's mechanism"
        );
        fs::write(
            &input,
            format!("{HEADER_9}| 1 | CONFIRMED | Warning | f.go:6 | x | | | hot | stale-cache |\n"),
        )
        .unwrap();
        assert_eq!(
            run_with(&repo, &prev, &head, &input, &["--prior", &prior]),
            1,
            "a new mechanism outside the fix still blocks"
        );
        assert_eq!(
            run_with(&repo, &prev, &head, &input, &["--prior", &slug.join("absent").to_string_lossy()]),
            2,
            "an unreadable slug is a bad call"
        );
    }

    #[test]
    fn hunks_by_path_follow_the_new_side() {
        let diff = "diff --git a/old.go b/new.go\nsimilarity index 90%\nrename from old.go\nrename to new.go\n\
            --- a/old.go\n+++ b/new.go\n@@ -3 +3 @@\n-x\n+y\n\
            diff --git a/gone.go b/gone.go\n--- a/gone.go\n+++ /dev/null\n@@ -1,2 +0,0 @@\n";
        let hunks = hunks_by_path(diff);
        assert_eq!(
            hunks["new.go"],
            [hunk(3, 1)].map(|h| Hunk { old_start: 3, ..h })
        );
        assert!(!hunks.contains_key("old.go") && !hunks.contains_key("gone.go"));
    }

    /// f.go at two commits: line 2 rewritten, line 5 deleted, and r.go renamed from q.go with
    /// its line 3 edited. Returns the repo and both shas.
    fn fixed_repo(name: &str) -> (PathBuf, String, String) {
        let dir = tmp(name);
        let body: String = (1..=20).map(|n| format!("line {n}\n")).collect();
        git(&dir, &["init", "-q"]);
        fs::write(dir.join("f.go"), "a\nb\nc\nd\ne\nf\ng\n").unwrap();
        fs::write(dir.join("q.go"), &body).unwrap();
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "round head"]);
        let prev = git(&dir, &["rev-parse", "HEAD"]);
        fs::write(dir.join("f.go"), "a\nB\nc\nd\nf\ng\n").unwrap();
        git(&dir, &["mv", "q.go", "r.go"]);
        fs::write(dir.join("r.go"), body.replace("line 3\n", "line three\n")).unwrap();
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "fix"]);
        let head = git(&dir, &["rev-parse", "HEAD"]);
        (dir, prev, head)
    }

    fn row(anchor: &str) -> Blocking {
        Blocking {
            band: "Warning".into(),
            anchor: anchor.into(),
            mechanism: String::new(),
        }
    }

    #[test]
    fn place_rows_against_git() {
        let (repo, prev, head) = fixed_repo("stop-place");
        let hunks = fix_hunks(&repo, &prev, &head).unwrap();
        let rows = [
            row("f.go:2"),
            row("f.go:5"),
            row("f.go:6"),
            row("f.go:1"),
            row("r.go:3"),
            row("r.go:5"),
            row("no anchor"),
        ];
        assert_eq!(
            place_rows(&rows, &hunks),
            [Place::OnFix, Place::OnFix, Place::Outside, Place::Outside, Place::OnFix, Place::Outside, Place::Unanchored],
            "f.go: line 2 rewritten, line 5 beside the deletion; r.go: the rename carries only line 3"
        );
        assert!(
            fix_hunks(&repo, "0000000", &head).is_err(),
            "an unknown sha is an error"
        );
    }

    fn run(repo: &Path, prev: &str, head: &str, input: &str) -> i32 {
        let file = repo.join("input.md");
        fs::write(&file, input).unwrap();
        let args: Vec<String> = [
            &file.to_string_lossy(),
            "--repo",
            &repo.to_string_lossy(),
            "--prev",
            prev,
            "--head",
            head,
        ]
        .iter()
        .map(|s| s.to_string())
        .collect();
        stop(&args)
    }

    #[test]
    fn stop_exit_codes() {
        let (repo, prev, head) = fixed_repo("stop-exit");
        let table = "| # | State | Band | file:line | Check |\n";
        assert_eq!(
            run(
                &repo,
                &prev,
                &head,
                &format!("{table}| 1 | CONFIRMED | Nit | f.go:6 | x |\n")
            ),
            0,
            "no Critical or Warning"
        );
        assert_eq!(
            run(&repo, &prev, &head, "Warning f.go:2\n"),
            0,
            "all on the fix"
        );
        assert_eq!(
            run(&repo, &prev, &head, "Warning f.go:2\nCritical f.go:6\n"),
            1,
            "one outside the fix"
        );
        assert_eq!(
            run(&repo, &prev, &head, "- Warning f.go:6\n"),
            2,
            "a list line of another shape"
        );
        assert_eq!(
            run(&repo, "deadbeef", &head, "none\n"),
            2,
            "an unknown sha, even with nothing to place"
        );
        assert_eq!(stop(&["input.md".to_string()]), 2, "the shas are required");
    }
}
