// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! A run over many files: each file's findings in argument order, the rules stated in two files,
//! the health table, the count.
use super::file::{check_file, index};
use super::{Finding, FirstSeen, Health, Place};
use std::collections::HashSet;
use std::io::Write;

/// How many duplicate rules a run prints, the most spread first.
const DUPES_SHOWN: usize = 10;

/// The lint over the given files, printing to `out`; the exit code is the return.
pub fn run(args: &[String], out: &mut dyn Write) -> i32 {
    let quiet = args.iter().any(|a| a == "--quiet");
    let paths: Vec<&String> = args.iter().filter(|a| !a.starts_with("--")).collect();
    if paths.is_empty() {
        let _ = writeln!(out, "usage: rules lint [--quiet] <files>");
        return 2;
    }
    let corpus = index(&paths);
    let mut found = 0;
    let mut health_rows: Vec<(String, Health)> = Vec::new();
    let mut across_files = FirstSeen::default();
    for path in &paths {
        let report = check_file(path, &corpus);
        found += print_findings(out, path, report.findings);
        // One place per file per sentence: the duplicate check asks how many files share it.
        for (key, places) in report.sentences.iter() {
            across_files.push(key, places[0].clone());
        }
        if let Some(health) = report.health {
            health_rows.push((path.to_string(), health));
        }
    }
    // A duplicate is a lead across files, outside the count, as the Python counted.
    print_duplicates(out, &across_files);
    if !quiet && !health_rows.is_empty() {
        print_health(out, &health_rows);
    }
    if found > 0 {
        let _ = writeln!(out, "\n{found} warning(s), nothing blocks");
    } else {
        let _ = writeln!(out, "\nnothing to report");
    }
    0
}

/// One file's findings, sorted by line then code, and their count.
fn print_findings(out: &mut dyn Write, path: &str, mut findings: Vec<Finding>) -> usize {
    findings.sort_by(|a, b| (a.line, a.code).cmp(&(b.line, b.code)));
    for f in &findings {
        let _ = writeln!(out, "warn  {}:{} [{}] {}", path, f.line, f.code, f.message);
    }
    findings.len()
}

/// The sentences seen in more than one file, the most spread first and first-seen among ties,
/// at most `DUPES_SHOWN`. An opening clause is skipped where a whole sentence already covers it.
fn print_duplicates(out: &mut dyn Write, seen: &FirstSeen) {
    let mut dupes: Vec<(&str, &[Place])> = seen
        .iter()
        .filter(|(_, places)| files_of(places) > 1)
        .collect();
    let whole: Vec<&str> = dupes
        .iter()
        .map(|(key, _)| *key)
        .filter(|key| !is_opening(key))
        .collect();
    dupes.sort_by_key(|(_, places)| std::cmp::Reverse(places.len()));
    let mut shown = 0;
    for (key, places) in dupes {
        if is_opening(key) && whole.iter().any(|w| w.starts_with(&key[OPEN.len()..])) {
            continue;
        }
        if shown == DUPES_SHOWN {
            break;
        }
        shown += 1;
        let where_ = places
            .iter()
            .map(|p| format!("{}:{}", p.path, p.line))
            .collect::<Vec<_>>()
            .join(", ");
        let code = if is_opening(key) { "dupe-open" } else { "dupe" };
        let short: String = key.chars().take(90).collect();
        let _ = writeln!(
            out,
            "warn  [{code}] one rule in {} files: {where_}\n      \"{short}\"",
            places.len()
        );
    }
}

/// The prefix `file::sentence_keys` gives an opening clause.
const OPEN: &str = "open: ";

fn is_opening(key: &str) -> bool {
    key.starts_with(OPEN)
}

fn files_of(places: &[Place]) -> usize {
    places
        .iter()
        .map(|p| p.path.as_str())
        .collect::<HashSet<_>>()
        .len()
}

fn print_health(out: &mut dyn Write, rows: &[(String, Health)]) {
    let _ = writeln!(
        out,
        "\n{:<34}{:>7}{:>7}{:>8}{:>6}{:>7}",
        "file", "words", "rules", "w/rule", "neg", "bold%"
    );
    for (path, h) in rows {
        let _ = writeln!(
            out,
            "{:<34}{:>7}{:>7}{:>8}{:>6}{:>7}",
            path, h.words, h.rules, h.density, h.negation, h.bold
        );
    }
    let total: usize = rows.iter().map(|(_, h)| h.words).sum();
    let _ = writeln!(out, "{:<34}{:>7}", "total", total);
    let _ = writeln!(
        out,
        "\nw/rule over 75 is a flabby rule, neg over 4.0 and bold% over 40 a file that has stopped ranking its own."
    );
}

#[cfg(test)]
mod tests {
    use super::super::testutil::{file, tmp};
    use super::*;

    fn run_to_string(args: &[String]) -> (i32, String) {
        let mut out = Vec::new();
        let code = run(args, &mut out);
        (code, String::from_utf8(out).unwrap())
    }

    #[test]
    fn usage_without_files() {
        let (code, text) = run_to_string(&["--quiet".to_string()]);
        assert_eq!(code, 2);
        assert!(text.starts_with("usage:"));
    }

    #[test]
    fn quiet_anywhere_and_paths_in_order() {
        let dir = tmp("quiet");
        let a = file(&dir, "a.md", "clean\n");
        let b = file(&dir, "b.md", "clean\n");
        let (_, text) = run_to_string(&[a.clone(), "--quiet".to_string(), b.clone()]);
        assert!(!text.contains("w/rule") && text.ends_with("nothing to report\n"));
        let (_, text) = run_to_string(&[b.clone(), a.clone()]);
        assert!(
            text.find(&b).unwrap() < text.find(&a).unwrap(),
            "rows keep the argument order"
        );
    }

    #[test]
    fn sorts_findings_and_reports_the_count() {
        let dir = tmp("run");
        let path = file(&dir, "AGENTS.md", "docker cannot (x)\nstop re-deriving\n");
        let (code, text) = run_to_string(&["--quiet".to_string(), path.clone()]);
        assert_eq!(code, 0);
        let lines: Vec<&str> = text.lines().collect();
        assert_eq!(lines[0], format!("warn  {path}:1 [env-claim] environment capability asserted without the command that reads it"));
        assert_eq!(
            lines[1],
            format!("warn  {path}:1 [paren] parenthetical; rework into the sentence")
        );
        assert_eq!(lines[2], format!("warn  {path}:2 [frozen] tells the reader to stop measuring; state the command instead"));
        assert_eq!(lines.last().unwrap(), &"3 warning(s), nothing blocks");
        assert!(!text.contains("w/rule"), "--quiet drops the health table");
    }

    #[test]
    fn health_table_and_nothing_to_report() {
        let dir = tmp("run-clean");
        let path = file(&dir, "AGENTS.md", "a clean line\n");
        let (_, text) = run_to_string(std::slice::from_ref(&path));
        assert!(text.contains(&format!("{:<34}{:>7}", path, 3)));
        assert!(text.ends_with("\nnothing to report\n"));
        assert!(text.contains("total"));
    }

    #[test]
    fn dupes_cap_at_ten_and_skip_covered_openings() {
        let dir = tmp("dupes");
        let body: String = (0..12)
            .map(|i| {
                format!("rule number {i} says one two three four five six seven, then tail {i}.\n")
            })
            .collect();
        let a = file(&dir, "a.md", &body);
        let b = file(&dir, "b.md", &body);
        let (_, text) = run_to_string(&["--quiet".to_string(), a, b]);
        assert_eq!(text.matches("[dupe]").count(), 10, "ten shown of twelve");
        assert_eq!(
            text.matches("[dupe-open]").count(),
            0,
            "an opening a full dupe covers is not shown twice"
        );
        assert!(text.contains("one rule in 2 files:"));
    }

    #[test]
    fn dupe_open_when_the_tails_differ() {
        let dir = tmp("dupes-open");
        let a = file(
            &dir,
            "a.md",
            "this opening clause appears in two files, but the tail is one thing here now.\n",
        );
        let b = file(
            &dir,
            "b.md",
            "this opening clause appears in two files, but the tail is another thing entirely.\n",
        );
        let (_, text) = run_to_string(&["--quiet".to_string(), a, b]);
        assert!(text.contains("[dupe-open] one rule in 2 files:"), "{text}");
        assert!(text.contains("\"open: this opening clause appears in two files\""));
    }

    #[test]
    fn dupes_stay_out_of_the_count() {
        let dir = tmp("dupes-count");
        let sentence = "one rule stated in two files counts as a lead and not a warning.\n";
        let a = file(&dir, "a.md", sentence);
        let b = file(&dir, "b.md", sentence);
        let (_, text) = run_to_string(&["--quiet".to_string(), a, b]);
        assert!(text.contains("[dupe]"));
        assert!(text.ends_with("nothing to report\n"), "{text}");
    }
}
