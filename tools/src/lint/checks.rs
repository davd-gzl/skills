// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! One function per check. Each returns its finding or nothing, and `file::check_file` runs
//! them in order over one file. Nothing here reads the disk except `file_refs`, which asks
//! whether a pointed-at file exists.
use super::patterns::*;
use super::text::{has_sha, line_of, ProseLine};
use super::{Corpus, Finding, Kind, Level};
use std::path::Path;

/// A file has no word cap: a rule leaves for a reason, never for the count, and the word count
/// is printed so growth is seen. What catches bloat is the size of each rule: measured across
/// the corpus, a skill runs 23 to 38 words per rule.
pub const DENSITY_CAP: u64 = 75;

fn finding(level: Level, line: usize, code: &'static str, message: impl Into<String>) -> Finding {
    Finding {
        level,
        line,
        code,
        message: message.into(),
    }
}

/// A date or a sha in a log is a lead; in the core it is the staleness the lint catches.
fn lead_or_error(log: bool) -> Level {
    if log {
        Level::Warn
    } else {
        Level::Error
    }
}

fn is_heading(line: &ProseLine) -> bool {
    line.clean.trim_start().starts_with('#')
}

fn is_bullet(line: &ProseLine) -> bool {
    line.clean.trim_start().starts_with("- ")
}

fn is_list_item(line: &ProseLine) -> bool {
    let text = line.clean.trim_start();
    text.starts_with("- ") || text.starts_with("* ")
}

/// Every check that reads one line. `next_clean` is the line after it, for the dangling check;
/// `log` says the file is a measurement log, where a date or a sha is a lead and not a defect.
pub fn line_checks(line: &ProseLine, next_clean: &str, log: bool) -> Vec<Finding> {
    [
        frozen(line),
        dated(line, log),
        emdash(line),
        dangling(line, next_clean),
        sha(line, log),
        env_claim(line),
        paren(line),
    ]
    .into_iter()
    .flatten()
    .collect()
}

/// A rule that tells the reader to stop measuring.
fn frozen(line: &ProseLine) -> Option<Finding> {
    if !FROZEN.is_match(&line.clean) {
        return None;
    }
    Some(finding(
        Level::Error,
        line.number,
        "frozen",
        "tells the reader to stop measuring; state the command instead",
    ))
}

/// A date in a rule. A heading may date a block of measurements; a rule carries no date, it
/// applies whenever its trigger fires.
fn dated(line: &ProseLine, log: bool) -> Option<Finding> {
    if is_heading(line) {
        return None;
    }
    let clean = &line.clean;
    let dated = DATED.is_match(clean) || ISO_DATE.is_match(clean) || CLOCK.is_match(clean);
    if !dated {
        return None;
    }
    Some(finding(
        lead_or_error(log),
        line.number,
        "dated",
        "a rule carries no date; the incident belongs in the artifact",
    ))
}

/// An em-dash in prose. One separating a term from its definition, in a heading or near the
/// head of a list item, is structure and passes.
fn emdash(line: &ProseLine) -> Option<Finding> {
    let position = line.clean.chars().position(|c| c == EMDASH)?;
    let structural = is_heading(line) || (is_list_item(line) && position < 60);
    if structural {
        return None;
    }
    Some(finding(
        Level::Error,
        line.number,
        "emdash",
        "em-dash in prose",
    ))
}

/// A provenance word ends one line and punctuation opens the next: a clause was stripped and the
/// sentence not repaired.
fn dangling(line: &ProseLine, next_clean: &str) -> Option<Finding> {
    if !(DANGLE_TAIL.is_match(line.clean.trim_end()) && DANGLE_HEAD.is_match(next_clean)) {
        return None;
    }
    Some(finding(
        Level::Error,
        line.number,
        "dangling",
        "sentence ends on a provenance word and the next line opens on punctuation; a clause was cut and not repaired",
    ))
}

/// A bullet pinning a commit: a rule cites the behaviour, not the incident.
fn sha(line: &ProseLine, log: bool) -> Option<Finding> {
    if !(is_bullet(line) && has_sha(&line.clean)) {
        return None;
    }
    Some(finding(
        lead_or_error(log),
        line.number,
        "sha",
        "a rule pins no commit; cite the behaviour, not the incident",
    ))
}

/// An environment capability asserted as settled with no command beside it. The escape reads
/// the raw line, since the command usually sits in a code span the clean line blanks.
fn env_claim(line: &ProseLine) -> Option<Finding> {
    let claimed = ENV_NOUN.is_match(&line.clean) && ENV_ABSOLUTE.is_match(&line.clean);
    if !claimed || ENV_ESCAPE.is_match(&line.raw) {
        return None;
    }
    Some(finding(
        Level::Warn,
        line.number,
        "env-claim",
        "environment capability asserted without the command that reads it",
    ))
}

/// A parenthetical in prose. A heading, a table row, a numbered marker and a plural `(s)` pass.
fn paren(line: &ProseLine) -> Option<Finding> {
    if is_heading(line) || line.clean.trim_start().starts_with('|') {
        return None;
    }
    let stripped = PAREN_EXEMPT.replace_all(&line.clean, "");
    if !stripped.contains('(') {
        return None;
    }
    Some(finding(
        Level::Warn,
        line.number,
        "paren",
        "parenthetical; rework into the sentence",
    ))
}

/// Every file a rule points at, over `bare`, the text with its fences removed. A file inside
/// skills/ names its own repository's scripts by their path there, which renders on that
/// repository's page: the workspace's scripts/ is tried first, that one second. A delta's paths
/// are read from inside its own checkout, so a miss there is a lead rather than a defect.
pub fn file_refs(path: &str, bare: &str, kind: Kind) -> Vec<Finding> {
    let mut out = Vec::new();
    for caps in FILE_REF.captures_iter(bare) {
        let target = &caps[1];
        if target.contains('<') || file_exists(path, target) {
            continue;
        }
        out.push(finding(
            lead_or_error(kind.is_log()),
            line_of(bare, caps.get(0).unwrap().start()),
            "xref",
            format!("points at {target}, which does not exist"),
        ));
    }
    out
}

fn file_exists(from: &str, target: &str) -> bool {
    Path::new(target).exists()
        || (from.starts_with("skills/") && Path::new("skills").join(target).exists())
}

/// Every section a rule points at, `*Name*` alone or `*Name* in `file``. The star before the
/// name and the star after it stand alone: a bold label is not a reference. The target is the
/// file the reference names, else the file named on the same line, else the file itself; the
/// name matches a heading on prefix or a bold label, per `Corpus::has_heading`.
pub fn section_refs(path: &str, bare: &str, corpus: &Corpus) -> Vec<Finding> {
    let bytes = bare.as_bytes();
    let mut out = Vec::new();
    for caps in SECTION_REF.captures_iter(bare) {
        let whole = caps.get(0).unwrap();
        let name_match = caps.get(1).unwrap();
        let bold_before = whole.start() > 0 && bytes[whole.start() - 1] == b'*';
        let bold_after = bytes.get(name_match.end() + 1) == Some(&b'*');
        if bold_before || bold_after {
            continue;
        }
        let name = name_match.as_str().trim_end_matches(['.', ',']);
        let named = caps
            .get(2)
            .map(|m| m.as_str().to_string())
            .or_else(|| file_named_on_line(bare, whole.start(), whole.end()));
        let target = match named {
            Some(file) if corpus.headings.contains_key(&file) => file,
            _ => path.to_string(),
        };
        if corpus.has_heading(&target, name) {
            continue;
        }
        out.push(finding(
            Level::Warn,
            line_of(bare, whole.start()),
            "xref",
            format!("*{name}* has no heading in {target}"),
        ));
    }
    out
}

/// The rule file named in a code span on the line holding `start..end`, when there is one.
fn file_named_on_line(bare: &str, start: usize, end: usize) -> Option<String> {
    let from = bare[..start].rfind('\n').map(|i| i + 1).unwrap_or(0);
    let to = bare[end..]
        .find('\n')
        .map(|i| i + end)
        .unwrap_or(bare.len());
    NAMED_FILE
        .captures(&bare[from..to])
        .map(|c| c[1].to_string())
}

/// A CLAUDE.md exists so the harness finds the rules at all; it holds a pointer and nothing else.
pub fn layout(words: usize) -> Option<Finding> {
    if words <= 60 {
        return None;
    }
    Some(finding(
        Level::Error,
        1,
        "layout",
        format!("{words} words in a CLAUDE.md; the rules belong in AGENTS.md beside it, which this file imports"),
    ))
}

/// The median rule over the ceiling.
pub fn density(median: Option<u64>) -> Option<Finding> {
    let words = median?;
    if words <= DENSITY_CAP {
        return None;
    }
    Some(finding(
        Level::Warn,
        0,
        "density",
        format!("{words} words per rule against a {DENSITY_CAP} ceiling; cut the clause naming the session, not the rule"),
    ))
}
