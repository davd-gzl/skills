// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! One file through every check: `check_file` returns its findings, its health row and the
//! sentences the duplicate check compares across files.
use super::checks;
use super::patterns::{FENCE_BLOCK, HEADING, NEGATION};
use super::text::{self, ProseLine};
use super::{Corpus, FileReport, Finding, FirstSeen, Health, Level, Place};
use std::fs;
use std::path::Path;

/// What a path is, which sets how strictly it is read.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    /// Anything under projects/: one repository's measurement log, whatever it is named.
    Project,
    /// knowledge/: a measurement log like a delta. A date there says when the fact was read,
    /// not when a rule fires.
    Log,
    /// A skill of the corpus.
    Skill,
    /// Anything else: an AGENTS.md, a CLAUDE.md, a README.
    Default,
}

impl Kind {
    /// In a log a date or a sha is a lead, printed as a warning; in the core both are the
    /// staleness this lint catches.
    pub fn is_log(self) -> bool {
        matches!(self, Kind::Project | Kind::Log)
    }
}

pub fn classify(path: &str) -> Kind {
    if path.starts_with("projects/") || path.contains("/projects/") {
        Kind::Project
    } else if path.starts_with("knowledge/") || path.contains("/knowledge/") {
        Kind::Log
    } else if path.starts_with("skills/") || path.contains("/skills/") {
        Kind::Skill
    } else {
        Kind::Default
    }
}

/// Every file's text and lowercased headings, read once before any file is checked.
pub fn index(paths: &[&String]) -> Corpus {
    let mut corpus = Corpus::default();
    for path in paths {
        let contents = fs::read_to_string(path).unwrap_or_default();
        let bare = FENCE_BLOCK.replace_all(&contents, "");
        let headings = HEADING
            .captures_iter(&bare)
            .map(|c| c[1].trim().to_lowercase())
            .collect();
        corpus.headings.insert(path.to_string(), headings);
        corpus.texts.insert(path.to_string(), contents);
    }
    corpus
}

pub fn check_file(path: &str, corpus: &Corpus) -> FileReport {
    let contents = match fs::read_to_string(path) {
        Ok(contents) => contents,
        Err(e) => return unreadable(path, &e),
    };
    let kind = classify(path);
    let lines = text::prose_lines(&contents);
    let mut findings = Vec::new();
    for (i, line) in lines.iter().enumerate() {
        let next_clean = lines.get(i + 1).map(|l| l.clean.as_str()).unwrap_or("");
        findings.extend(checks::line_checks(line, next_clean, kind.is_log()));
    }
    let bare = FENCE_BLOCK.replace_all(&contents, "");
    findings.extend(checks::file_refs(path, &bare, kind));
    findings.extend(checks::section_refs(path, &bare, corpus));
    // Every word costs context, a fenced command as much as a sentence, so the count is the file.
    let words = text::word_count(&contents);
    let pointer_file = basename(path) == "CLAUDE.md";
    if pointer_file {
        findings.extend(checks::layout(words));
    }
    let rules = text::rule_units(&contents);
    let density = text::median_words(&rules);
    findings.extend(checks::density(density));
    let health = health_of(words, &lines, rules.len(), density);
    // A CLAUDE.md carries the same seven-line pointer everywhere on purpose, so it never enters
    // the duplicate set.
    let sentences = if pointer_file {
        FirstSeen::default()
    } else {
        sentence_keys(path, &lines)
    };
    FileReport {
        findings,
        health: Some(health),
        sentences,
    }
}

fn basename(path: &str) -> String {
    Path::new(path)
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default()
}

/// The one finding of a file that could not be read, worded as Python's OSError prints.
fn unreadable(path: &str, e: &std::io::Error) -> FileReport {
    let errno = e.raw_os_error().unwrap_or(0);
    let reason = e
        .to_string()
        .split(" (os error ")
        .next()
        .unwrap_or_default()
        .to_string();
    let finding = Finding {
        level: Level::Error,
        line: 0,
        code: "unreadable",
        message: format!("[Errno {errno}] {reason}: '{path}'"),
    };
    FileReport {
        findings: vec![finding],
        health: None,
        sentences: FirstSeen::default(),
    }
}

fn health_of(words: usize, lines: &[ProseLine], rules: usize, density: Option<u64>) -> Health {
    let bullets: Vec<&str> = lines
        .iter()
        .map(|l| l.clean.as_str())
        .filter(|clean| clean.trim_start().starts_with("- "))
        .collect();
    let bold = bullets
        .iter()
        .filter(|clean| clean.trim_start().starts_with("- **"))
        .count();
    let negations: usize = lines
        .iter()
        .map(|l| NEGATION.find_iter(&l.clean).count())
        .sum();
    Health {
        words,
        rules,
        density: density.map(|d| d.to_string()).unwrap_or_else(|| "-".into()),
        negation: format!("{:.1}", negations as f64 * 100.0 / words.max(1) as f64),
        // Under eight bullets the share says nothing, so it is not reported.
        bold: if bullets.len() >= 8 {
            text::round_even(bold as f64 * 100.0 / bullets.len() as f64).to_string()
        } else {
            "-".into()
        },
    }
}

/// Every sentence of eight words or more, keyed whole, and its opening clause keyed apart under
/// `open: `, since a paraphrase keeps the trigger and reworks the tail.
fn sentence_keys(path: &str, lines: &[ProseLine]) -> FirstSeen {
    let mut seen = FirstSeen::default();
    for line in lines {
        let place = || Place {
            path: path.to_string(),
            line: line.number,
        };
        for sentence in text::sentences(&line.clean) {
            let key = text::normalize(&sentence);
            if text::word_count(&key) >= 8 {
                seen.push(&key, place());
            }
            let opening = text::normalize(sentence.split([',', ';', ':']).next().unwrap_or(""));
            if text::word_count(&opening) >= 6 && opening != key {
                seen.push(&format!("open: {opening}"), place());
            }
        }
    }
    seen
}

#[cfg(test)]
mod tests {
    use super::super::testutil::{file, in_dir, tmp};
    use super::*;

    /// One file alone, checked against a corpus holding only itself.
    fn lint_of(dir: &Path, rel: &str, content: &str) -> FileReport {
        let path = file(dir, rel, content);
        let owned = [path.clone()];
        let refs: Vec<&String> = owned.iter().collect();
        check_file(&path, &index(&refs))
    }

    /// `target` checked against a corpus of relative paths, which needs the working directory.
    fn lint_rel(names: &[&str], target: &str) -> Vec<Finding> {
        let owned: Vec<String> = names.iter().map(|n| n.to_string()).collect();
        let refs: Vec<&String> = owned.iter().collect();
        check_file(target, &index(&refs)).findings
    }

    fn codes(findings: &[Finding]) -> Vec<&str> {
        findings.iter().map(|f| f.code).collect()
    }

    fn lines_with(findings: &[Finding], code: &str) -> Vec<usize> {
        findings
            .iter()
            .filter(|f| f.code == code)
            .map(|f| f.line)
            .collect()
    }

    fn messages_with(findings: &[Finding], code: &str) -> Vec<String> {
        findings
            .iter()
            .filter(|f| f.code == code)
            .map(|f| f.message.clone())
            .collect()
    }

    #[test]
    fn classify_by_path() {
        assert_eq!(classify("skills/knowledge/cost.md"), Kind::Log);
        assert_eq!(classify("knowledge/cost.md"), Kind::Log);
        assert_eq!(classify("projects/meet/AGENTS.md"), Kind::Project);
        assert_eq!(classify("/x/projects/meet/running.md"), Kind::Project);
        assert_eq!(classify("skills/review.md"), Kind::Skill);
        assert_eq!(classify("/x/skills/review.md"), Kind::Skill);
        assert_eq!(classify("AGENTS.md"), Kind::Default);
    }

    #[test]
    fn frozen_clause() {
        let dir = tmp("frozen");
        let report = lint_of(
            &dir,
            "AGENTS.md",
            "Stop re-deriving it.\nNo need to check.\nDo not re-verify.\nsettled, so stop.\n",
        );
        assert_eq!(
            codes(&report.findings),
            vec!["frozen", "frozen", "frozen", "frozen"]
        );
        assert!(report.findings.iter().all(|f| f.level == Level::Error));
    }

    #[test]
    fn dated_forms_and_the_heading_exemption() {
        let dir = tmp("dated");
        let text = "# Measured on 2026-01-02\nmeasured on 3 March 2026\nverified March 3, 2026\nsince 2026-01-02\nat 9:15 am\nplain line\n2025-12-31 bare\n";
        let report = lint_of(&dir, "AGENTS.md", text);
        assert_eq!(lines_with(&report.findings, "dated"), vec![2, 3, 4, 5, 7]);
    }

    #[test]
    fn dated_is_a_warning_in_a_log_and_an_error_in_the_core() {
        let dir = tmp("dated-level");
        let core = lint_of(&dir, "AGENTS.md", "measured on 2026-01-02\n");
        let delta = lint_of(&dir, "projects/p/AGENTS.md", "measured on 2026-01-02\n");
        let knowledge = lint_of(&dir, "skills/knowledge/k.md", "measured on 2026-01-02\n");
        assert_eq!(core.findings[0].level, Level::Error);
        assert_eq!(delta.findings[0].level, Level::Warn);
        assert_eq!(knowledge.findings[0].level, Level::Warn);
    }

    #[test]
    fn emdash_prose_against_structure() {
        let dir = tmp("emdash");
        let long = "x".repeat(70);
        let text = format!("# Term — definition\n- term — definition\n- {long} — late\nprose — dash\n* star — head\n");
        let report = lint_of(&dir, "AGENTS.md", &text);
        assert_eq!(lines_with(&report.findings, "emdash"), vec![3, 4]);
    }

    #[test]
    fn dangling_clause() {
        let dir = tmp("dangle");
        let report = lint_of(
            &dir,
            "AGENTS.md",
            "it was measured\n, and so\nit was measured\nand so\nreported  \n: next\n",
        );
        assert_eq!(lines_with(&report.findings, "dangling"), vec![1, 5]);
    }

    #[test]
    fn sha_only_in_a_bullet() {
        let dir = tmp("sha");
        let report = lint_of(
            &dir,
            "AGENTS.md",
            "- at 0123456789 pinned\nat 0123456789 in prose\n- in `0123456789` code\n",
        );
        assert_eq!(lines_with(&report.findings, "sha"), vec![1]);
    }

    #[test]
    fn env_claim_and_its_escapes() {
        let dir = tmp("env");
        let text = "docker cannot start\ndocker cannot start, run it\nthe box is dead per `env-check`\nsudo is fine\n";
        let report = lint_of(&dir, "AGENTS.md", text);
        assert_eq!(lines_with(&report.findings, "env-claim"), vec![1]);
    }

    #[test]
    fn parenthetical_and_its_exemptions() {
        let dir = tmp("paren");
        let report = lint_of(
            &dir,
            "AGENTS.md",
            "a (b)\n# head (x)\n| cell (x) |\nmarker (s) and (2)\n[t](http://x/(y))\n",
        );
        assert_eq!(lines_with(&report.findings, "paren"), vec![1]);
    }

    #[test]
    fn layout_of_a_claude_md() {
        let dir = tmp("layout");
        let many = "w ".repeat(61);
        let report = lint_of(&dir, "CLAUDE.md", &many);
        assert_eq!(codes(&report.findings), vec!["layout"]);
        assert!(report.findings[0].message.starts_with("61 words"));
        assert!(
            report.sentences.is_empty(),
            "a CLAUDE.md never enters the dupe set"
        );
        let pointer = lint_of(&dir, "CLAUDE.md", "@AGENTS.md\n");
        assert!(pointer.findings.is_empty());
    }

    #[test]
    fn density_needs_eight_rules() {
        let dir = tmp("density");
        let long = format!("- {}.\n", "w ".repeat(80));
        let seven = lint_of(&dir, "a.md", &long.repeat(7));
        assert!(seven.findings.is_empty());
        assert_eq!(seven.health.unwrap().density, "-");
        let eight = lint_of(&dir, "b.md", &long.repeat(8));
        assert_eq!(codes(&eight.findings), vec!["density"]);
        assert_eq!(
            eight.health.unwrap().density,
            "82",
            "the dash, eighty words and the full stop"
        );
    }

    #[test]
    fn density_median_rounds_to_even() {
        let dir = tmp("median");
        let text: String = (0..8)
            .map(|i| format!("- {}.\n", "w ".repeat(if i < 4 { 20 } else { 21 })))
            .collect();
        let report = lint_of(&dir, "a.md", &text);
        assert_eq!(
            report.health.unwrap().density,
            "22",
            "median 21.5 rounds to 22, the even side"
        );
    }

    #[test]
    fn health_counts() {
        let dir = tmp("health");
        let text = "- **a** no\n- b not\n- c\n- d\n- e\n- f\n- g\n- h never\n";
        let health = lint_of(&dir, "a.md", text).health.unwrap();
        assert_eq!(health.words, 19);
        assert_eq!(health.bold, "12");
        assert_eq!(health.negation, "15.8");
        assert_eq!(health.rules, 0);
        let few = lint_of(&dir, "b.md", "- **a**\n- b\n").health.unwrap();
        assert_eq!(few.bold, "-", "under eight bullets the share says nothing");
    }

    #[test]
    fn seen_keys_full_and_opening() {
        let dir = tmp("seen");
        let text = "one two three four five six seven eight, then a tail.\nshort words.\nthe <placeholder> opening clause has six words here: tail.\n";
        let report = lint_of(&dir, "a.md", text);
        assert_eq!(
            report.sentences.keys(),
            vec![
                "one two three four five six seven eight then a tail",
                "open: one two three four five six seven eight",
                "the  opening clause has six words here tail",
                "open: the  opening clause has six words here",
            ],
            "a tag is blanked before the sentence is keyed, and the double space it leaves stays"
        );
    }

    #[test]
    fn unreadable_file() {
        let report = check_file("/nonexistent/skills-tools/x.md", &Corpus::default());
        assert_eq!(codes(&report.findings), vec!["unreadable"]);
        assert!(report.health.is_none());
        assert_eq!(
            report.findings[0].message,
            "[Errno 2] No such file or directory: '/nonexistent/skills-tools/x.md'"
        );
    }

    #[test]
    fn unreadable_directory_and_empty_file() {
        let dir = tmp("empty");
        let report = check_file(&dir.to_string_lossy(), &Corpus::default());
        assert_eq!(
            report.findings[0].message,
            format!("[Errno 21] Is a directory: '{}'", dir.display())
        );
        assert!(report.health.is_none());
        let empty = lint_of(&dir, "empty.md", "");
        assert!(empty.findings.is_empty());
        let health = empty.health.unwrap();
        assert_eq!((health.words, health.rules), (0, 0));
        assert_eq!(
            (
                health.negation.as_str(),
                health.bold.as_str(),
                health.density.as_str()
            ),
            ("0.0", "-", "-")
        );
        assert!(empty.sentences.is_empty());
    }

    #[test]
    fn crlf_lines_and_no_final_newline() {
        let dir = tmp("crlf");
        let report = lint_of(
            &dir,
            "AGENTS.md",
            "stop re-deriving\r\n- a (b)\r\nlast line *Nowhere here* without a newline",
        );
        let seen: Vec<(usize, &str)> = report.findings.iter().map(|f| (f.line, f.code)).collect();
        assert_eq!(seen, vec![(1, "frozen"), (2, "paren"), (3, "xref")]);
    }

    #[test]
    fn only_fences_count_words_but_report_nothing() {
        let dir = tmp("fences");
        let report = lint_of(
            &dir,
            "a.md",
            "```\nstop re-deriving (x) — 2026-01-01\n```\n",
        );
        assert!(report.findings.is_empty());
        assert_eq!(
            report.health.unwrap().words,
            7,
            "the fence lines count as words, as every token in the file does"
        );
    }

    #[test]
    fn section_ref_lengths_and_forms() {
        let dir = tmp("section-forms");
        let longest = "A".to_string() + &"b".repeat(60);
        let too_long = "A".to_string() + &"b".repeat(61);
        let text = format!("*Abc* three chars\n*Abcd* four chars\n*{longest}* sixty-one\n*{too_long}* sixty-two\n*Trailing dot.* here\n*lower case* here\n");
        let report = lint_of(&dir, "AGENTS.md", &text);
        let names = messages_with(&report.findings, "xref");
        assert_eq!(
            names.len(),
            3,
            "four to sixty-one characters, a capital first: {names:?}"
        );
        assert!(names[0].starts_with("*Abcd* has no heading"));
        assert!(names[1].starts_with(&format!("*{longest}* has no heading")));
        assert!(
            names[2].starts_with("*Trailing dot* has no heading"),
            "the dot is trimmed: {}",
            names[2]
        );
    }

    #[test]
    fn section_ref_section_of_form_and_prefix_case() {
        let dir = tmp("section-of");
        file(&dir, "skills/a.md", "# A\n## Final Check Items\n");
        file(
            &dir,
            "AGENTS.md",
            "run the *Final check* section of `skills/a.md` first\n",
        );
        let findings = in_dir(&dir, || {
            lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md")
        });
        assert!(
            findings.iter().all(|f| f.code != "xref"),
            "prefix match, case folded: {:?}",
            codes(&findings)
        );
    }

    #[test]
    fn refs_to_placeholders_are_skipped_and_missing_files_named() {
        let dir = tmp("refs");
        file(&dir, "AGENTS.md", "see `skills/<name>.md` and `skills/none-of-this.md` and `./scripts/nope.sh` and `skills/here.md`\n```\n`skills/fenced.md`\n```\n");
        file(&dir, "skills/here.md", "# here\n");
        file(&dir, "skills/scripts/own.sh", "");
        file(
            &dir,
            "skills/b.md",
            "`./scripts/own.sh` resolves inside skills/ too\n",
        );
        file(&dir, "projects/p/AGENTS.md", "see `scripts/nope.sh`\n");
        let (core, delta, skill) = in_dir(&dir, || {
            (
                lint_rel(&["AGENTS.md"], "AGENTS.md"),
                lint_rel(&["projects/p/AGENTS.md"], "projects/p/AGENTS.md"),
                lint_rel(&["skills/b.md"], "skills/b.md"),
            )
        });
        assert_eq!(
            messages_with(&core, "xref"),
            vec![
                "points at skills/none-of-this.md, which does not exist",
                "points at scripts/nope.sh, which does not exist"
            ]
        );
        assert_eq!(core[0].level, Level::Error);
        assert_eq!(delta[0].level, Level::Warn, "a delta's miss is a lead");
        assert!(
            skill.iter().all(|f| f.code != "xref"),
            "{:?}",
            codes(&skill)
        );
    }

    #[test]
    fn section_refs_resolve_by_heading_prefix_bold_label_or_named_file() {
        let dir = tmp("sections");
        file(
            &dir,
            "skills/a.md",
            "# A\n## Present heading (with a tail)\n**Bold label** text\n",
        );
        file(&dir, "AGENTS.md", "*Present* in `skills/a.md` ok\n*Bold label* in `skills/a.md` ok\n*Missing* in `skills/a.md` no\n*Own heading* here\n**Not a ref** here\n*Too* short\n");
        let findings = in_dir(&dir, || {
            lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md")
        });
        assert_eq!(
            messages_with(&findings, "xref"),
            vec![
                "*Missing* has no heading in skills/a.md",
                "*Own heading* has no heading in AGENTS.md"
            ]
        );
    }

    #[test]
    fn section_ref_takes_the_file_named_on_its_line() {
        let dir = tmp("sections-line");
        file(&dir, "skills/a.md", "# A\n## Setup\n");
        file(&dir, "AGENTS.md", "run *Setup*, per `skills/a.md`, first\nand *Setup* alone names this file, which has no such heading\n");
        let findings = in_dir(&dir, || {
            lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md")
        });
        assert_eq!(
            messages_with(&findings, "xref"),
            vec!["*Setup* has no heading in AGENTS.md"]
        );
    }

    #[test]
    fn section_ref_named_file_at_the_end_of_a_file_without_newline() {
        let dir = tmp("sections-eof");
        file(&dir, "skills/a.md", "# A\n## Setup\n");
        file(&dir, "AGENTS.md", "run *Setup*, per `skills/a.md`");
        let findings = in_dir(&dir, || {
            lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md")
        });
        assert!(
            findings.iter().all(|f| f.code != "xref"),
            "the last line is read whole: {:?}",
            codes(&findings)
        );
    }

    #[test]
    fn index_reads_headings_outside_fences() {
        let dir = tmp("index");
        let path = file(
            &dir,
            "a.md",
            "# Top\n```\n# Fenced\n```\n## Second (tail)\n",
        );
        let owned = [path.clone()];
        let refs: Vec<&String> = owned.iter().collect();
        let corpus = index(&refs);
        let headings = &corpus.headings[&path];
        assert_eq!(headings.len(), 2);
        assert!(headings.contains("top") && headings.contains("second (tail)"));
    }
}
