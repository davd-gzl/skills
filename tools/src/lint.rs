// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! Checks rule files against the contract in authoring.md, the port of the
//! Python lint whose output it reproduces line for line: the golden test under
//! tests/lint holds that output over a fixture corpus exercising every check.
//!
//! Nothing here blocks. Every finding is a warning: a rough rule lands, and a
//! later pass fixes it. A warning answered by raising its threshold is the
//! pollution this file exists to catch.
use regex::Regex;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::Write;
use std::path::Path;
use std::sync::LazyLock;

/// A file has no word cap: a rule leaves for a reason, never for the count, and
/// the word count is printed so growth is seen. What catches bloat is the size of
/// each rule: measured across the corpus, a skill runs 23 to 38 words per rule.
pub const DENSITY_CAP: u64 = 75;

macro_rules! re {
    ($name:ident, $pat:expr) => {
        static $name: LazyLock<Regex> = LazyLock::new(|| Regex::new($pat).unwrap());
    };
}

// A rule that tells the reader to stop measuring: the clause is the defect, the fact goes stale silently.
re!(FROZEN, r"(?i)\b(stop re-deriving|stops? re-?deriving|never re-?derive|no need to (check|verify|re-?run)|do not (re-?check|re-?measure|re-?verify)|already measured, so|settled, so stop)\b");
// An environment capability asserted as settled wants the command beside it.
re!(ENV_NOUN, r"(?i)\b(docker|dockerd|podman|sudo|unshare|namespace|CapEff|CapBnd|/dev/(fuse|kvm)|docker\.sock|rootless|chroot|bwrap|this (container|box|machine|shell)|the box)\b");
re!(ENV_ABSOLUTE, r"(?i)\b(cannot|can never|is dead|never (start|run|work)|no \w+ binary|absent|not permitted|will never|impossible|refused)\b");
re!(ENV_ESCAPE, r"env-check|measure it|run it|check it|`[^`]*`|capability recorded");
re!(DATED, r"(?i)\b(stated|measured|verified|as of|since)\s+(on\s+)?(\d{4}-\d{2}-\d{2}|\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4})\b");
re!(ISO_DATE, r"\b20\d{2}-[01]\d-[0-3]\d\b");
re!(CLOCK, r"\b[0-2]?\d:[0-5]\d\s?(am|pm|UTC|utc)?\b");
// A clause was stripped and the sentence not repaired: a provenance word ends one line, punctuation opens the next.
re!(DANGLE_TAIL, r"(?i)\b(measured|stated|verified|reported)\s*$");
re!(DANGLE_HEAD, r"^\s*[.,;:]($|\s)");
re!(HEX_RUN, r"[0-9a-f]+");
re!(NEGATION, r"(?i)\b(never|neither|nor|no|not|cannot|none|nothing|nobody)\b");
re!(FENCE, r"^\s*```");
re!(INLINE_CODE, r"`[^`]*`");
re!(LINK_TARGET, r"\]\([^)]*\)");
re!(HTML_TAG, r"<[^>]{1,60}>");
re!(PLACEHOLDER, r"(?i)<[a-z][a-z0-9 _/-]*>");
re!(FENCE_BLOCK, r"(?ms)^```.*?^```");
re!(FRONT_MATTER, r"(?s)^---\n.*?\n---\n");
re!(UNIT_HEAD, r"^(?:\s*[-*] |\s*\d+\. |\n)");
// A rule pointing at a file or a section that does not exist reads exactly like one pointing at one that does.
re!(FILE_REF, r"`\.?/?((?:skills|scripts|projects)/[A-Za-z0-9_.<>/-]+\.(?:md|py|sh))`");
re!(SECTION_REF, r"\*([A-Z][^*\n]{3,60})\*(?:\s+(?:rule|section)?\s*(?:in|of)\s+`([^`]+)`)?");
re!(NAMED_FILE, r"`((?:skills|projects)/[A-Za-z0-9_./-]+\.md|AGENTS\.md)`");
re!(HEADING, r"(?m)^#+\s+(.+)$");
re!(PAREN_EXEMPT, r"\(\d\)|\(s\)");
re!(NON_ALNUM, r"[^a-z0-9 ]");

const EMDASH: char = '—';

pub struct Finding { pub level: &'static str, pub line: usize, pub code: &'static str, pub message: String }

pub struct Health { pub words: usize, pub negation: String, pub bold: String, pub rules: usize, pub density: String }

/// Keys in first-seen order, as the Python dict kept them, so ties sort the same way.
#[derive(Default)]
pub struct Ordered { pub keys: Vec<String>, pub index: HashMap<String, usize>, pub values: Vec<Vec<(String, usize)>> }

impl Ordered {
    fn push(&mut self, key: &str, value: (String, usize)) {
        match self.index.get(key) {
            Some(&i) => self.values[i].push(value),
            None => { self.index.insert(key.to_string(), self.keys.len()); self.keys.push(key.to_string()); self.values.push(vec![value]) }
        }
    }
}

pub fn classify(path: &str) -> &'static str {
    // Anything under projects/ is one repository's measurement log, whatever it is named.
    if path.starts_with("projects/") || path.contains("/projects/") { "project" }
    // knowledge/ is a measurement log like a delta: a date there says when the fact was read, not when a rule fires.
    else if path.starts_with("knowledge/") || path.contains("/knowledge/") { "log" }
    else if path.contains("/skills/") || path.starts_with("skills/") { "skill" }
    else { "default" }
}

/// Every line outside a fenced block, with code spans, link targets and tags blanked: a
/// rule and its example live in one file, so a check reading the example reports the
/// file's own illustrations and gets switched off.
fn prose_lines(text: &str) -> Vec<(usize, String, String)> {
    let mut out = Vec::new();
    let mut in_fence = false;
    for (i, raw) in text.lines().enumerate() {
        if FENCE.is_match(raw) { in_fence = !in_fence; continue }
        if in_fence { continue }
        let line = INLINE_CODE.replace_all(raw, "``");
        let line = LINK_TARGET.replace_all(&line, "]");
        let line = HTML_TAG.replace_all(&line, "");
        out.push((i + 1, raw.to_string(), line.into_owned()));
    }
    out
}

fn word_count(s: &str) -> usize { s.split_whitespace().count() }

/// The smallest blocks that carry one rule, for the density measure.
fn rule_units(text: &str) -> Vec<String> {
    let body = FENCE_BLOCK.replace_all(text, "");
    let body = FRONT_MATTER.replace(&body, "");
    let mut blocks = Vec::new();
    let mut start = 0;
    for (i, b) in body.bytes().enumerate() {
        if b == b'\n' && UNIT_HEAD.is_match(&body[i + 1..]) { blocks.push(&body[start..i]); start = i + 1 }
    }
    blocks.push(&body[start..]);
    blocks.iter().filter(|b| word_count(b) >= 12 && !b.trim_start().starts_with('#'))
        .map(|b| b.split_whitespace().collect::<Vec<_>>().join(" ")).collect()
}

/// The line split at every whitespace run that follows a full stop, a bang or a question mark.
fn sentences(line: &str) -> Vec<String> {
    let mut parts = Vec::new();
    let mut cur = String::new();
    let mut prev: Option<char> = None;
    let mut chars = line.chars().peekable();
    while let Some(c) = chars.next() {
        if c.is_whitespace() && matches!(prev, Some('.') | Some('!') | Some('?')) {
            while chars.peek().map(|d| d.is_whitespace()).unwrap_or(false) { chars.next(); }
            parts.push(std::mem::take(&mut cur));
            prev = Some(' ');
            continue;
        }
        cur.push(c);
        prev = Some(c);
    }
    parts.push(cur);
    parts.into_iter().map(|s| s.trim().to_string()).filter(|s| word_count(s) >= 8).collect()
}

fn normalize(sentence: &str) -> String {
    let lower = sentence.to_lowercase();
    let s = PLACEHOLDER.replace_all(&lower, "");
    NON_ALNUM.replace_all(&s, "").trim().to_string()
}

fn is_word(c: char) -> bool { c.is_alphanumeric() || c == '_' }

/// A bare commit, 7 to 40 hex digits with nothing word-like, no slash and no hash before it and nothing word-like after.
fn has_sha(s: &str) -> bool {
    HEX_RUN.find_iter(s).any(|m| {
        let n = m.end() - m.start();
        let before = s[..m.start()].chars().next_back();
        let after = s[m.end()..].chars().next();
        (7..=40).contains(&n) && !before.map(|c| is_word(c) || c == '/' || c == '#').unwrap_or(false) && !after.map(is_word).unwrap_or(false)
    })
}

/// Half to even, as Python's round.
fn round_even(x: f64) -> i64 {
    let r = x.round();
    if (x - x.trunc()).abs() == 0.5 { let t = x.trunc() as i64; if t % 2 == 0 { t } else { r as i64 } } else { r as i64 }
}

fn line_of(bare: &str, at: usize) -> usize { bare[..at].matches('\n').count() + 1 }

/// Every file and section a rule points at. Headings match on prefix: a reference names the
/// section, never its parenthetical. Where the same line names a file, that file is the target.
fn check_refs(path: &str, text: &str, corpus: &HashMap<String, String>, headings: &HashMap<String, HashSet<String>>) -> Vec<Finding> {
    let mut out = Vec::new();
    let bare = FENCE_BLOCK.replace_all(text, "");
    for m in FILE_REF.captures_iter(&bare) {
        let target = &m[1];
        // A file inside skills/ names its own repository's scripts by their path there, which renders on that
        // repository's page; the workspace's scripts/ is tried first, that one second.
        if target.contains('<') || Path::new(target).exists() || (path.starts_with("skills/") && Path::new("skills").join(target).exists()) { continue }
        // A delta's paths are read from inside its own checkout, so a miss here is a lead rather than a defect.
        out.push(Finding { level: if matches!(classify(path), "project" | "log") { "warn" } else { "error" }, line: line_of(&bare, m.get(0).unwrap().start()), code: "xref", message: format!("points at {target}, which does not exist") });
    }
    let bytes = bare.as_bytes();
    for m in SECTION_REF.captures_iter(&bare) {
        let whole = m.get(0).unwrap();
        let name_m = m.get(1).unwrap();
        // The star before the name and the star after it stand alone: a bold label is not a reference.
        if whole.start() > 0 && bytes[whole.start() - 1] == b'*' { continue }
        if bytes.get(name_m.end() + 1) == Some(&b'*') { continue }
        let name = name_m.as_str().trim_end_matches(['.', ',']);
        let mut where_: Option<String> = m.get(2).map(|w| w.as_str().to_string());
        if where_.is_none() {
            let from = bare[..whole.start()].rfind('\n').map(|i| i + 1).unwrap_or(0);
            let to = bare[whole.end()..].find('\n').map(|i| i + whole.end()).unwrap_or(bare.len() - 1);
            let line = &bare[from..to.max(from)];
            where_ = NAMED_FILE.captures(line).map(|c| c[1].to_string());
        }
        let target = match &where_ { Some(w) if headings.contains_key(w) => w.clone(), _ => path.to_string() };
        let low = name.to_lowercase();
        if headings.get(&target).map(|hs| hs.iter().any(|h| h.starts_with(&low))).unwrap_or(false) { continue }
        if corpus.get(&target).map(|t| t.contains(&format!("**{name}"))).unwrap_or(false) { continue }
        out.push(Finding { level: "warn", line: line_of(&bare, whole.start()), code: "xref", message: format!("*{name}* has no heading in {target}") });
    }
    out
}

pub fn check_file(path: &str, corpus: &HashMap<String, String>, headings: &HashMap<String, HashSet<String>>) -> (Vec<Finding>, Option<Health>, Ordered) {
    let text = match fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => return (vec![Finding { level: "error", line: 0, code: "unreadable", message: format!("[Errno {}] {}: '{}'", e.raw_os_error().unwrap_or(0), os_error_text(&e), path) }], None, Ordered::default()),
    };
    let mut findings = Vec::new();
    let lines = prose_lines(&text);
    // Every word costs context, a fenced command as much as a sentence, so the budget counts the file.
    let words = word_count(&text);
    let bullets: Vec<&str> = lines.iter().filter(|(_, _, c)| c.trim_start().starts_with("- ")).map(|(_, _, c)| c.as_str()).collect();
    let bold = bullets.iter().filter(|c| c.trim_start().starts_with("- **")).count();
    let negations: usize = lines.iter().map(|(_, _, c)| NEGATION.find_iter(c).count()).sum();
    // A project delta is a measurement log: a date says when to re-check and a sha which tree was read.
    // In the core both are the staleness this file catches, so they downgrade to warnings there and nowhere else.
    let log = matches!(classify(path), "project" | "log");
    for (i, (n, raw, clean)) in lines.iter().enumerate() {
        let heading = clean.trim_start().starts_with('#');
        let nxt = lines.get(i + 1).map(|l| l.2.as_str()).unwrap_or("");
        // A dash separating a term from its definition, in a heading or at the head of a list item, is structure.
        let sep = clean.chars().position(|c| c == EMDASH);
        let structural = heading || ((clean.trim_start().starts_with("- ") || clean.trim_start().starts_with("* ")) && sep.map(|s| s < 60).unwrap_or(false));
        if FROZEN.is_match(clean) {
            findings.push(Finding { level: "error", line: *n, code: "frozen", message: "tells the reader to stop measuring; state the command instead".into() });
        }
        // A heading may date a block of measurements; a rule carries no date, it applies whenever its trigger fires.
        if !heading && (DATED.is_match(clean) || ISO_DATE.is_match(clean) || CLOCK.is_match(clean)) {
            findings.push(Finding { level: if log { "warn" } else { "error" }, line: *n, code: "dated", message: "a rule carries no date; the incident belongs in the artifact".into() });
        }
        if clean.contains(EMDASH) && !structural {
            findings.push(Finding { level: "error", line: *n, code: "emdash", message: "em-dash in prose".into() });
        }
        if DANGLE_TAIL.is_match(clean.trim_end()) && DANGLE_HEAD.is_match(nxt) {
            findings.push(Finding { level: "error", line: *n, code: "dangling", message: "sentence ends on a provenance word and the next line opens on punctuation; a clause was cut and not repaired".into() });
        }
        if clean.trim_start().starts_with("- ") && has_sha(clean) {
            findings.push(Finding { level: if log { "warn" } else { "error" }, line: *n, code: "sha", message: "a rule pins no commit; cite the behaviour, not the incident".into() });
        }
        if ENV_NOUN.is_match(clean) && ENV_ABSOLUTE.is_match(clean) && !ENV_ESCAPE.is_match(raw) {
            findings.push(Finding { level: "warn", line: *n, code: "env-claim", message: "environment capability asserted without the command that reads it".into() });
        }
        let stripped = PAREN_EXEMPT.replace_all(clean, "");
        if stripped.contains('(') && !heading && !clean.trim_start().starts_with('|') {
            findings.push(Finding { level: "warn", line: *n, code: "paren", message: "parenthetical; rework into the sentence".into() });
        }
    }
    findings.extend(check_refs(path, &text, corpus, headings));
    // CLAUDE.md exists so the harness finds the rules at all; it holds a pointer and nothing else.
    let basename = Path::new(path).file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    if basename == "CLAUDE.md" && words > 60 {
        findings.push(Finding { level: "error", line: 1, code: "layout", message: format!("{words} words in a CLAUDE.md; the rules belong in AGENTS.md beside it, which this file imports") });
    }
    let rules = rule_units(&text);
    let density: Option<u64> = if rules.len() >= 8 {
        let mut counts: Vec<usize> = rules.iter().map(|r| word_count(r)).collect();
        counts.sort_unstable();
        let mid = counts.len() / 2;
        let median = if counts.len() % 2 == 1 { counts[mid] as f64 } else { (counts[mid - 1] + counts[mid]) as f64 / 2.0 };
        Some(round_even(median) as u64)
    } else { None };
    if let Some(d) = density {
        if d > DENSITY_CAP {
            findings.push(Finding { level: "warn", line: 0, code: "density", message: format!("{d} words per rule against a {DENSITY_CAP} ceiling; cut the clause naming the session, not the rule") });
        }
    }
    let health = Health {
        words,
        negation: format!("{:.1}", negations as f64 * 100.0 / words.max(1) as f64),
        // Under eight bullets the share says nothing, so it is not reported.
        bold: if bullets.len() >= 8 { round_even(bold as f64 * 100.0 / bullets.len() as f64).to_string() } else { "-".into() },
        rules: rules.len(),
        density: density.map(|d| d.to_string()).unwrap_or_else(|| "-".into()),
    };
    let mut seen = Ordered::default();
    // A CLAUDE.md carries the same seven-line pointer everywhere on purpose.
    if basename == "CLAUDE.md" { return (findings, Some(health), seen) }
    for (n, _, clean) in &lines {
        for sentence in sentences(clean) {
            let key = normalize(&sentence);
            if word_count(&key) >= 8 { seen.push(&key, (path.to_string(), *n)) }
            // A paraphrase keeps the trigger and reworks the tail, so the opening clause is keyed too.
            let opening = normalize(sentence.split([',', ';', ':']).next().unwrap_or(""));
            if word_count(&opening) >= 6 && opening != key { seen.push(&format!("open: {opening}"), (path.to_string(), *n)) }
        }
    }
    (findings, Some(health), seen)
}

/// The C library's text for the error, which is what Python prints after the errno: "No such file or directory".
fn os_error_text(e: &std::io::Error) -> String {
    e.to_string().split(" (os error ").next().unwrap_or_default().to_string()
}

/// Every file's text and the lowercased headings of each, so a reference into another file resolves.
pub fn index(paths: &[&String]) -> (HashMap<String, String>, HashMap<String, HashSet<String>>) {
    let mut corpus: HashMap<String, String> = HashMap::new();
    let mut headings: HashMap<String, HashSet<String>> = HashMap::new();
    for p in paths {
        let text = fs::read_to_string(p).unwrap_or_default();
        let bare = FENCE_BLOCK.replace_all(&text, "");
        headings.insert(p.to_string(), HEADING.captures_iter(&bare).map(|c| c[1].trim().to_lowercase()).collect());
        corpus.insert(p.to_string(), text);
    }
    (corpus, headings)
}

/// The lint over the given files, printing to `out`; the exit code is the return.
pub fn run(args: &[String], out: &mut dyn Write) -> i32 {
    let quiet = args.iter().any(|a| a == "--quiet");
    let paths: Vec<&String> = args.iter().filter(|a| !a.starts_with("--")).collect();
    if paths.is_empty() { let _ = writeln!(out, "usage: rules lint [--quiet] <files>"); return 2 }
    let (corpus, headings) = index(&paths);
    let mut found = 0;
    let mut health_rows: Vec<(String, Health)> = Vec::new();
    let mut sentences_seen = Ordered::default();
    for p in &paths {
        let (mut findings, health, seen) = check_file(p, &corpus, &headings);
        for (key, places) in seen.keys.iter().zip(seen.values.iter()) { sentences_seen.push(key, places[0].clone()) }
        findings.sort_by(|a, b| (a.line, a.code).cmp(&(b.line, b.code)));
        for f in &findings {
            found += 1;
            let _ = writeln!(out, "warn  {}:{} [{}] {}", p, f.line, f.code, f.message);
        }
        if let Some(h) = health { health_rows.push((p.to_string(), h)) }
    }
    let mut dupes: Vec<(&String, &Vec<(String, usize)>)> = sentences_seen.keys.iter().zip(sentences_seen.values.iter())
        .filter(|(_, v)| v.iter().map(|(p, _)| p).collect::<HashSet<_>>().len() > 1).collect();
    let full: Vec<&String> = dupes.iter().filter(|(k, _)| !k.starts_with("open: ")).map(|(k, _)| *k).collect();
    dupes.sort_by_key(|(_, v)| std::cmp::Reverse(v.len()));
    let mut shown = 0;
    for (key, places) in dupes {
        if key.starts_with("open: ") && full.iter().any(|f| f.starts_with(&key[6..])) { continue }
        if shown == 10 { break }
        shown += 1;
        let where_ = places.iter().map(|(p, n)| format!("{p}:{n}")).collect::<Vec<_>>().join(", ");
        let code = if key.starts_with("open: ") { "dupe-open" } else { "dupe" };
        let short: String = key.chars().take(90).collect();
        let _ = writeln!(out, "warn  [{code}] one rule in {} files: {where_}\n      \"{short}\"", places.len());
    }
    if !quiet && !health_rows.is_empty() {
        let _ = writeln!(out, "\n{:<34}{:>7}{:>7}{:>8}{:>6}{:>7}", "file", "words", "rules", "w/rule", "neg", "bold%");
        for (p, h) in &health_rows {
            let _ = writeln!(out, "{:<34}{:>7}{:>7}{:>8}{:>6}{:>7}", p, h.words, h.rules, h.density, h.negation, h.bold);
        }
        let total: usize = health_rows.iter().map(|(_, h)| h.words).sum();
        let _ = writeln!(out, "{:<34}{:>7}", "total", total);
        let _ = writeln!(out, "\nw/rule over 75 is a flabby rule, neg over 4.0 and bold% over 40 a file that has stopped ranking its own.");
    }
    if found > 0 { let _ = writeln!(out, "\n{found} warning(s), nothing blocks"); } else { let _ = writeln!(out, "\nnothing to report"); }
    0
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn tmp(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("skills-tools-lint-{}", std::process::id())).join(name);
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }
    fn file(dir: &Path, rel: &str, content: &str) -> String {
        let p = dir.join(rel);
        fs::create_dir_all(p.parent().unwrap()).unwrap();
        fs::write(&p, content).unwrap();
        p.to_string_lossy().into_owned()
    }
    fn lint_of(dir: &Path, rel: &str, content: &str) -> (Vec<Finding>, Option<Health>, Ordered) {
        let p = file(dir, rel, content);
        let owned = vec![p.clone()];
        let refs: Vec<&String> = owned.iter().collect();
        let (corpus, headings) = index(&refs);
        check_file(&p, &corpus, &headings)
    }
    fn codes(f: &[Finding]) -> Vec<&str> { f.iter().map(|x| x.code).collect() }
    /// The file checks resolve paths against the working directory, so a test that names one holds this lock.
    static CWD: std::sync::Mutex<()> = std::sync::Mutex::new(());
    fn in_dir<T>(dir: &Path, f: impl FnOnce() -> T) -> T {
        let _guard = CWD.lock().unwrap_or_else(|e| e.into_inner());
        let prev = std::env::current_dir().unwrap();
        std::env::set_current_dir(dir).unwrap();
        let out = f();
        std::env::set_current_dir(prev).unwrap();
        out
    }
    fn lint_rel(names: &[&str], target: &str) -> Vec<Finding> {
        let owned: Vec<String> = names.iter().map(|n| n.to_string()).collect();
        let refs: Vec<&String> = owned.iter().collect();
        let (corpus, headings) = index(&refs);
        check_file(target, &corpus, &headings).0
    }

    #[test] fn classify_by_path() {
        assert_eq!(classify("skills/knowledge/cost.md"), "log");
        assert_eq!(classify("knowledge/cost.md"), "log");
        assert_eq!(classify("projects/meet/AGENTS.md"), "project");
        assert_eq!(classify("/x/projects/meet/running.md"), "project");
        assert_eq!(classify("skills/review.md"), "skill");
        assert_eq!(classify("/x/skills/review.md"), "skill");
        assert_eq!(classify("AGENTS.md"), "default");
    }
    #[test] fn prose_lines_skip_fences_and_blank_code() {
        let out = prose_lines("a `code` b\n```\nfenced\n```\n[t](http://x) <em>tag</em>\n");
        assert_eq!(out.len(), 2);
        assert_eq!(out[0], (1, "a `code` b".into(), "a `` b".into()));
        assert_eq!(out[1].0, 5);
        assert_eq!(out[1].2, "[t] tag");
    }
    #[test] fn prose_lines_indented_fence_toggles() {
        let out = prose_lines("x\n   ```\nin\n   ```\ny\n");
        assert_eq!(out.iter().map(|l| l.0).collect::<Vec<_>>(), vec![1, 5]);
    }
    #[test] fn rule_units_split_and_floor() {
        let twelve = "one two three four five six seven eight nine ten eleven twelve";
        let text = format!("---\nname: x\n---\n# Heading {twelve}\n\n- {twelve}\n- short\n1. {twelve} more\n```\n- {twelve} fenced\n```\n{twelve}\n");
        let units = rule_units(&text);
        assert_eq!(units.len(), 3, "{units:?}");
        assert!(units[0].starts_with("- one"));
        assert!(units[1].starts_with("1. one"));
        assert!(units[2].starts_with("one"));
    }
    #[test] fn rule_units_join_whitespace() {
        let units = rule_units("- a  b\n  c   d e f g h i j k l m\n");
        assert_eq!(units, vec!["- a b c d e f g h i j k l m"]);
    }
    #[test] fn sentences_split_after_stops() {
        let eight = "w1 w2 w3 w4 w5 w6 w7 w8";
        let s = sentences(&format!("{eight}. {eight}!  {eight}? short one. {eight}, not split here"));
        assert_eq!(s.len(), 4);
        assert_eq!(s[0], format!("{eight}."));
        assert_eq!(s[3], format!("{eight}, not split here"));
    }
    #[test] fn sentences_under_eight_words_drop() {
        assert!(sentences("a b c d e f g. h i j k l m n.").is_empty());
    }
    #[test] fn normalize_lowers_and_strips() {
        assert_eq!(normalize("Run `X` on <the Repo>, Twice!"), "run x on  twice");
        assert_eq!(normalize("  A.B  "), "ab");
    }
    #[test] fn sha_shapes() {
        assert!(has_sha("at 0123456 here"));
        assert!(has_sha("at 0123456789abcdef0123456789abcdef01234567 end"));
        assert!(!has_sha("at 012345 six"));
        assert!(!has_sha("at 0123456789abcdef0123456789abcdef012345678 forty one"));
        assert!(!has_sha("path/0123456 after a slash"));
        assert!(!has_sha("#0123456 after a hash"));
        assert!(!has_sha("x0123456 after a word char"));
        assert!(!has_sha("0123456x before a word char"));
        assert!(!has_sha("ABCDEF1 upper"));
        assert!(has_sha("(deadbeef)"));
    }
    #[test] fn rounding_half_to_even() {
        assert_eq!(round_even(0.5), 0); assert_eq!(round_even(1.5), 2); assert_eq!(round_even(2.5), 2);
        assert_eq!(round_even(2.4), 2); assert_eq!(round_even(2.6), 3); assert_eq!(round_even(37.5), 38); assert_eq!(round_even(36.5), 36);
    }
    #[test] fn line_numbers_in_bare_text() { assert_eq!(line_of("a\nb\nc", 4), 3); assert_eq!(line_of("a", 0), 1); }
    #[test] fn ordered_keeps_first_seen_order() {
        let mut o = Ordered::default();
        o.push("b", ("f".into(), 1)); o.push("a", ("f".into(), 2)); o.push("b", ("g".into(), 3));
        assert_eq!(o.keys, vec!["b", "a"]); assert_eq!(o.values[0].len(), 2);
    }
    #[test] fn frozen_clause() {
        let d = tmp("frozen");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "Stop re-deriving it.\nNo need to check.\nDo not re-verify.\nsettled, so stop.\n");
        assert_eq!(codes(&f), vec!["frozen", "frozen", "frozen", "frozen"]);
        assert!(f.iter().all(|x| x.level == "error"));
    }
    #[test] fn dated_forms_and_the_heading_exemption() {
        let d = tmp("dated");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "# Measured on 2026-01-02\nmeasured on 3 March 2026\nverified March 3, 2026\nsince 2026-01-02\nat 9:15 am\nplain line\n2025-12-31 bare\n");
        assert_eq!(f.iter().filter(|x| x.code == "dated").map(|x| x.line).collect::<Vec<_>>(), vec![2, 3, 4, 5, 7]);
    }
    #[test] fn dated_is_a_warning_in_a_delta_and_an_error_in_the_core() {
        let d = tmp("dated-level");
        let (core, _, _) = lint_of(&d, "AGENTS.md", "measured on 2026-01-02\n");
        let (delta, _, _) = lint_of(&d, "projects/p/AGENTS.md", "measured on 2026-01-02\n");
        let (know, _, _) = lint_of(&d, "skills/knowledge/k.md", "measured on 2026-01-02\n");
        assert_eq!((core[0].level, delta[0].level, know[0].level), ("error", "warn", "warn"));
    }
    #[test] fn emdash_prose_against_structure() {
        let d = tmp("emdash");
        let long = "x".repeat(70);
        let (f, _, _) = lint_of(&d, "AGENTS.md", &format!("# Term — definition\n- term — definition\n- {long} — late\nprose — dash\n* star — head\n"));
        assert_eq!(f.iter().filter(|x| x.code == "emdash").map(|x| x.line).collect::<Vec<_>>(), vec![3, 4]);
    }
    #[test] fn dangling_clause() {
        let d = tmp("dangle");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "it was measured\n, and so\nit was measured\nand so\nreported  \n: next\n");
        assert_eq!(f.iter().filter(|x| x.code == "dangling").map(|x| x.line).collect::<Vec<_>>(), vec![1, 5]);
    }
    #[test] fn sha_only_in_a_bullet() {
        let d = tmp("sha");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "- at 0123456789 pinned\nat 0123456789 in prose\n- in `0123456789` code\n");
        assert_eq!(f.iter().filter(|x| x.code == "sha").map(|x| x.line).collect::<Vec<_>>(), vec![1]);
    }
    #[test] fn env_claim_and_its_escapes() {
        let d = tmp("env");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "docker cannot start\ndocker cannot start, run it\nthe box is dead per `env-check`\nsudo is fine\n");
        assert_eq!(f.iter().filter(|x| x.code == "env-claim").map(|x| x.line).collect::<Vec<_>>(), vec![1]);
    }
    #[test] fn parenthetical_and_its_exemptions() {
        let d = tmp("paren");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "a (b)\n# head (x)\n| cell (x) |\nmarker (s) and (2)\n[t](http://x/(y))\n");
        assert_eq!(f.iter().filter(|x| x.code == "paren").map(|x| x.line).collect::<Vec<_>>(), vec![1]);
    }
    #[test] fn layout_of_a_claude_md() {
        let d = tmp("layout");
        let many = "w ".repeat(61);
        let (f, _, seen) = lint_of(&d, "CLAUDE.md", &many);
        assert_eq!(codes(&f), vec!["layout"]);
        assert!(f[0].message.starts_with("61 words"));
        assert!(seen.keys.is_empty(), "a CLAUDE.md never enters the dupe set");
        let (g, _, _) = lint_of(&d, "CLAUDE.md", "@AGENTS.md\n");
        assert!(g.is_empty());
    }
    #[test] fn density_needs_eight_rules() {
        let d = tmp("density");
        let long = format!("- {}.\n", "w ".repeat(80));
        let (f, h, _) = lint_of(&d, "a.md", &long.repeat(7));
        assert!(f.is_empty()); assert_eq!(h.unwrap().density, "-");
        let (f, h, _) = lint_of(&d, "b.md", &long.repeat(8));
        assert_eq!(codes(&f), vec!["density"]); assert_eq!(h.unwrap().density, "82", "the dash, eighty words and the full stop");
    }
    #[test] fn density_median_rounds_to_even() {
        let d = tmp("median");
        let text: String = (0..8).map(|i| format!("- {}.\n", "w ".repeat(if i < 4 { 20 } else { 21 }))).collect();
        let (_, h, _) = lint_of(&d, "a.md", &text);
        assert_eq!(h.unwrap().density, "22", "median 21.5 rounds to 22, the even side");
    }
    #[test] fn health_counts() {
        let d = tmp("health");
        let text = "- **a** no\n- b not\n- c\n- d\n- e\n- f\n- g\n- h never\n";
        let (_, h, _) = lint_of(&d, "a.md", text);
        let h = h.unwrap();
        assert_eq!(h.words, 19); assert_eq!(h.bold, "12"); assert_eq!(h.negation, "15.8"); assert_eq!(h.rules, 0);
        let (_, h, _) = lint_of(&d, "b.md", "- **a**\n- b\n");
        assert_eq!(h.unwrap().bold, "-", "under eight bullets the share says nothing");
    }
    #[test] fn seen_keys_full_and_opening() {
        let d = tmp("seen");
        let (_, _, seen) = lint_of(&d, "a.md", "one two three four five six seven eight, then a tail.\nshort words.\nthe <placeholder> opening clause has six words here: tail.\n");
        assert_eq!(seen.keys, vec!["one two three four five six seven eight then a tail", "open: one two three four five six seven eight", "the  opening clause has six words here tail", "open: the  opening clause has six words here"], "a tag is blanked before the sentence is keyed, and the double space it leaves stays");
    }
    #[test] fn unreadable_file() {
        let (f, h, _) = check_file("/nonexistent/skills-tools/x.md", &HashMap::new(), &HashMap::new());
        assert_eq!(codes(&f), vec!["unreadable"]); assert!(h.is_none());
        assert_eq!(f[0].message, "[Errno 2] No such file or directory: '/nonexistent/skills-tools/x.md'");
    }
    #[test] fn unreadable_directory_and_empty_file() {
        let d = tmp("empty");
        let (f, h, _) = check_file(&d.to_string_lossy(), &HashMap::new(), &HashMap::new());
        assert_eq!(f[0].message, format!("[Errno 21] Is a directory: '{}'", d.display())); assert!(h.is_none());
        let (f, h, seen) = lint_of(&d, "empty.md", "");
        assert!(f.is_empty()); let h = h.unwrap();
        assert_eq!((h.words, h.negation.as_str(), h.bold.as_str(), h.rules, h.density.as_str()), (0, "0.0", "-", 0, "-")); assert!(seen.keys.is_empty());
    }
    #[test] fn crlf_lines_and_no_final_newline() {
        let d = tmp("crlf");
        let (f, _, _) = lint_of(&d, "AGENTS.md", "stop re-deriving\r\n- a (b)\r\nlast line *Nowhere here* without a newline");
        assert_eq!(f.iter().map(|x| (x.line, x.code)).collect::<Vec<_>>(), vec![(1, "frozen"), (2, "paren"), (3, "xref")]);
    }
    #[test] fn section_ref_lengths_and_forms() {
        let d = tmp("section-forms");
        let longest = "A".to_string() + &"b".repeat(60);
        let too_long = "A".to_string() + &"b".repeat(61);
        let (f, _, _) = lint_of(&d, "AGENTS.md", &format!("*Abc* three chars\n*Abcd* four chars\n*{longest}* sixty-one\n*{too_long}* sixty-two\n*Trailing dot.* here\n*lower case* here\n"));
        let names: Vec<String> = f.iter().filter(|x| x.code == "xref").map(|x| x.message.clone()).collect();
        assert_eq!(names.len(), 3, "four to sixty-one characters, a capital first: {names:?}");
        assert!(names[0].starts_with("*Abcd* has no heading"));
        assert!(names[1].starts_with(&format!("*{longest}* has no heading")));
        assert!(names[2].starts_with("*Trailing dot* has no heading"), "the dot is trimmed: {}", names[2]);
    }
    #[test] fn section_ref_section_of_form_and_prefix_case() {
        let d = tmp("section-of");
        file(&d, "skills/a.md", "# A\n## Final Check Items\n");
        file(&d, "AGENTS.md", "run the *Final check* section of `skills/a.md` first\n");
        let f = in_dir(&d, || lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md"));
        assert!(f.iter().all(|x| x.code != "xref"), "prefix match, case folded: {:?}", codes(&f));
    }
    #[test] fn quiet_anywhere_and_paths_in_order() {
        let d = tmp("quiet");
        let a = file(&d, "a.md", "clean\n"); let b = file(&d, "b.md", "clean\n");
        let mut out = Vec::new();
        run(&[a.clone(), "--quiet".to_string(), b.clone()], &mut out);
        let text = String::from_utf8(out).unwrap();
        assert!(!text.contains("w/rule") && text.ends_with("nothing to report\n"));
        let mut out = Vec::new();
        run(&[b.clone(), a.clone()], &mut out);
        let text = String::from_utf8(out).unwrap();
        assert!(text.find(&b).unwrap() < text.find(&a).unwrap(), "rows keep the argument order");
    }
    #[test] fn only_fences_count_words_but_report_nothing() {
        let d = tmp("fences");
        let (f, h, _) = lint_of(&d, "a.md", "```\nstop re-deriving (x) — 2026-01-01\n```\n");
        assert!(f.is_empty()); assert_eq!(h.unwrap().words, 7, "the fence lines count as words, as every token in the file does");
    }
    #[test] fn refs_to_placeholders_are_skipped_and_missing_files_named() {
        let d = tmp("refs");
        file(&d, "AGENTS.md", "see `skills/<name>.md` and `skills/none-of-this.md` and `./scripts/nope.sh` and `skills/here.md`\n```\n`skills/fenced.md`\n```\n");
        file(&d, "skills/here.md", "# here\n");
        file(&d, "skills/scripts/own.sh", "");
        file(&d, "skills/b.md", "`./scripts/own.sh` resolves inside skills/ too\n");
        file(&d, "projects/p/AGENTS.md", "see `scripts/nope.sh`\n");
        let (f, g, h) = in_dir(&d, || (lint_rel(&["AGENTS.md"], "AGENTS.md"), lint_rel(&["projects/p/AGENTS.md"], "projects/p/AGENTS.md"), lint_rel(&["skills/b.md"], "skills/b.md")));
        let xrefs: Vec<&str> = f.iter().filter(|x| x.code == "xref").map(|x| x.message.as_str()).collect();
        assert_eq!(xrefs, vec!["points at skills/none-of-this.md, which does not exist", "points at scripts/nope.sh, which does not exist"]);
        assert_eq!(f[0].level, "error");
        assert_eq!(g[0].level, "warn", "a delta's miss is a lead");
        assert!(h.iter().all(|x| x.code != "xref"), "{:?}", codes(&h));
    }
    #[test] fn section_refs_resolve_by_heading_prefix_bold_label_or_named_file() {
        let d = tmp("sections");
        file(&d, "skills/a.md", "# A\n## Present heading (with a tail)\n**Bold label** text\n");
        file(&d, "AGENTS.md", "*Present* in `skills/a.md` ok\n*Bold label* in `skills/a.md` ok\n*Missing* in `skills/a.md` no\n*Own heading* here\n**Not a ref** here\n*Too* short\n");
        let f = in_dir(&d, || lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md"));
        let xrefs: Vec<String> = f.iter().filter(|x| x.code == "xref").map(|x| x.message.clone()).collect();
        assert_eq!(xrefs, vec!["*Missing* has no heading in skills/a.md", "*Own heading* has no heading in AGENTS.md"]);
    }
    #[test] fn section_ref_takes_the_file_named_on_its_line() {
        let d = tmp("sections-line");
        file(&d, "skills/a.md", "# A\n## Setup\n");
        file(&d, "AGENTS.md", "run *Setup*, per `skills/a.md`, first\nand *Setup* alone names this file, which has no such heading\n");
        let f = in_dir(&d, || lint_rel(&["skills/a.md", "AGENTS.md"], "AGENTS.md"));
        let xrefs: Vec<String> = f.iter().filter(|x| x.code == "xref").map(|x| x.message.clone()).collect();
        assert_eq!(xrefs, vec!["*Setup* has no heading in AGENTS.md"]);
    }
    #[test] fn run_prints_usage_without_files() {
        let mut out = Vec::new();
        assert_eq!(run(&["--quiet".to_string()], &mut out), 2);
        assert!(String::from_utf8(out).unwrap().starts_with("usage:"));
    }
    #[test] fn run_sorts_findings_and_reports_the_count() {
        let d = tmp("run");
        let p = file(&d, "AGENTS.md", "docker cannot (x)\nstop re-deriving\n");
        let mut out = Vec::new();
        assert_eq!(run(&["--quiet".to_string(), p.clone()], &mut out), 0);
        let text = String::from_utf8(out).unwrap();
        let lines: Vec<&str> = text.lines().collect();
        assert_eq!(lines[0], format!("warn  {p}:1 [env-claim] environment capability asserted without the command that reads it"));
        assert_eq!(lines[1], format!("warn  {p}:1 [paren] parenthetical; rework into the sentence"));
        assert_eq!(lines[2], format!("warn  {p}:2 [frozen] tells the reader to stop measuring; state the command instead"));
        assert_eq!(lines.last().unwrap(), &"3 warning(s), nothing blocks");
        assert!(!text.contains("w/rule"), "--quiet drops the health table");
    }
    #[test] fn run_health_table_and_nothing_to_report() {
        let d = tmp("run-clean");
        let p = file(&d, "AGENTS.md", "a clean line\n");
        let mut out = Vec::new();
        run(&[p.clone()], &mut out);
        let text = String::from_utf8(out).unwrap();
        assert!(text.contains(&format!("{:<34}{:>7}", p, 3)));
        assert!(text.ends_with("\nnothing to report\n"));
        assert!(text.contains("total"));
    }
    #[test] fn run_dupes_cap_at_ten_and_skip_covered_openings() {
        let d = tmp("dupes");
        let body: String = (0..12).map(|i| format!("rule number {i} says one two three four five six seven, then tail {i}.\n")).collect();
        let a = file(&d, "a.md", &body);
        let b = file(&d, "b.md", &body);
        let mut out = Vec::new();
        run(&["--quiet".to_string(), a, b], &mut out);
        let text = String::from_utf8(out).unwrap();
        assert_eq!(text.matches("[dupe]").count(), 10, "ten shown of twelve");
        assert_eq!(text.matches("[dupe-open]").count(), 0, "an opening a full dupe covers is not shown twice");
        assert!(text.contains("one rule in 2 files:"));
    }
    #[test] fn run_dupe_open_when_the_tails_differ() {
        let d = tmp("dupes-open");
        let a = file(&d, "a.md", "this opening clause appears in two files, but the tail is one thing here now.\n");
        let b = file(&d, "b.md", "this opening clause appears in two files, but the tail is another thing entirely.\n");
        let mut out = Vec::new();
        run(&["--quiet".to_string(), a, b], &mut out);
        let text = String::from_utf8(out).unwrap();
        assert!(text.contains("[dupe-open] one rule in 2 files:"), "{text}");
        assert!(text.contains("\"open: this opening clause appears in two files\""));
    }
}
