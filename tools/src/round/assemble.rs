//! `round assemble`: `claims.md` and the draft's skeleton, written from the round's verdicts
//! as data, so the writer composes the text and never retypes a row.
//!
//! Inputs, under the round directory: `candidates/*.json`, what each finder, the reflector and
//! the critic returned, `{"candidates": [...], "dropped": [...]}`; `verdicts/*.json`, what each
//! verifier returned, `{"verdicts": [...]}`. Outputs: `claims.md`, the Candidates table, the
//! rows the finders settled, the hit rate per tier and an empty Completeness section; and
//! `findings.md`, one block per finding in posting order with everything the writer needs.

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use serde_json::Value;

use super::{count_lines, options, USAGE};

/// A verdict's line may sit this far from the candidate's and still be the same finding.
const NEAR: usize = 5;

/// The bands in the order the draft posts them, `skills/review-comment.md`.
const BAND_ORDER: [&str; 5] = ["Critical", "Warning", "Missing test", "Nit", "Suggestion"];

/// One candidate a finder returned, merged with any other at the same line.
#[derive(Debug, Clone)]
struct Candidate {
    file: String,
    line: usize,
    angle: String,
    summary: String,
    verify_by: String,
    band: String,
}

/// One row the finder or the reflector settled without a verifier.
#[derive(Debug, Clone)]
struct Dropped {
    angle: String,
    file: String,
    line: usize,
    summary: String,
    settled_by: String,
}

/// One verifier's verdict, as returned.
#[derive(Debug, Clone)]
struct Verdict {
    index: Option<usize>,
    state: String,
    band: String,
    file: String,
    line: usize,
    tldr: String,
    details: String,
    evidence: String,
    repro_path: String,
    refuted_by: String,
    angle: String,
    verify_by: String,
}

/// One row of the Candidates table, a verdict joined to its candidate or a candidate no
/// verifier reached.
#[derive(Debug, Clone)]
pub struct Row {
    pub index: usize,
    pub state: String,
    pub band: String,
    pub file: String,
    pub line: usize,
    pub check: String,
    pub observed: String,
    pub artifact: String,
    pub tier: String,
    pub angle: String,
    pub tldr: String,
    pub details: String,
    pub unrun: bool,
}

/// Every `.json` file of a directory, by name, so a run is deterministic; an absent
/// directory is an empty list.
fn read_json_dir(dir: &Path) -> Result<Vec<(String, Value)>, String> {
    let Ok(entries) = fs::read_dir(dir) else {
        return Ok(Vec::new());
    };
    let mut files: Vec<PathBuf> = entries
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().map(|x| x == "json").unwrap_or(false))
        .collect();
    files.sort();
    let mut out = Vec::new();
    for path in files {
        let text = fs::read_to_string(&path).map_err(|e| format!("{}: {e}", path.display()))?;
        let value: Value =
            serde_json::from_str(&text).map_err(|e| format!("{}: {e}", path.display()))?;
        out.push((path.display().to_string(), value));
    }
    Ok(out)
}

/// A string field, empty when absent or not a string.
fn text(v: &Value, key: &str) -> String {
    v.get(key)
        .and_then(Value::as_str)
        .unwrap_or("")
        .trim()
        .to_string()
}

/// An integer field, zero when absent; a number written as a string still counts.
fn number(v: &Value, key: &str) -> usize {
    match v.get(key) {
        Some(Value::Number(n)) => n.as_u64().unwrap_or(0) as usize,
        Some(Value::String(s)) => s.trim().parse().unwrap_or(0),
        _ => 0,
    }
}

/// The objects under an array field, none when absent.
fn items<'a>(v: &'a Value, key: &str) -> Vec<&'a Value> {
    v.get(key)
        .and_then(Value::as_array)
        .map(|a| a.iter().filter(|x| x.is_object()).collect())
        .unwrap_or_default()
}

/// The candidates of every file, merged by file:line the way the runner merges them, and every
/// dropped row.
fn candidates(files: &[(String, Value)]) -> (Vec<Candidate>, Vec<Dropped>) {
    let mut merged: Vec<Candidate> = Vec::new();
    let mut dropped = Vec::new();
    for (_, value) in files {
        for c in items(value, "candidates") {
            let cand = Candidate {
                file: text(c, "file"),
                line: number(c, "line"),
                angle: text(c, "angle"),
                summary: text(c, "summary"),
                verify_by: text(c, "verify_by"),
                band: text(c, "band"),
            };
            if cand.file.is_empty() {
                continue;
            }
            match merged
                .iter_mut()
                .find(|m| m.file == cand.file && m.line == cand.line)
            {
                Some(prev) => merge_into(prev, &cand),
                None => merged.push(cand),
            }
        }
        for d in items(value, "dropped") {
            dropped.push(Dropped {
                angle: text(d, "angle"),
                file: text(d, "file"),
                line: number(d, "line"),
                summary: text(d, "summary"),
                settled_by: text(d, "settled_by"),
            });
        }
    }
    (merged, dropped)
}

/// A second candidate at the same line joins the first: angles, summaries and checks side by
/// side, the higher band kept.
fn merge_into(prev: &mut Candidate, next: &Candidate) {
    if !next.angle.is_empty() && !prev.angle.contains(next.angle.as_str()) {
        prev.angle = format!("{} + {}", prev.angle, next.angle);
    }
    if !next.summary.is_empty() {
        prev.summary = format!("{} | {}", prev.summary, next.summary);
    }
    if !next.verify_by.is_empty() {
        prev.verify_by = format!("{} | {}", prev.verify_by, next.verify_by);
    }
    if band_rank(&next.band) < band_rank(&prev.band) {
        prev.band = next.band.clone();
    }
}

/// A band's place in the posting order; an unknown band posts last.
fn band_rank(band: &str) -> usize {
    BAND_ORDER
        .iter()
        .position(|b| *b == band)
        .unwrap_or(BAND_ORDER.len())
}

/// The verdicts of every file.
fn verdicts(files: &[(String, Value)]) -> Vec<Verdict> {
    let mut out = Vec::new();
    for (_, value) in files {
        for v in items(value, "verdicts") {
            let index = v.get("index").and_then(Value::as_u64).map(|n| n as usize);
            let verdict = Verdict {
                index,
                state: text(v, "state"),
                band: text(v, "band"),
                file: text(v, "file"),
                line: number(v, "line"),
                tldr: text(v, "tldr"),
                details: text(v, "details"),
                evidence: text(v, "evidence"),
                repro_path: text(v, "repro_path"),
                refuted_by: text(v, "refuted_by"),
                angle: text(v, "angle"),
                verify_by: text(v, "verify_by"),
            };
            if !verdict.file.is_empty() {
                out.push(verdict);
            }
        }
    }
    out
}

/// The candidate a verdict answers: the one at its exact line, else the nearest in the same
/// file within `NEAR` lines that no verdict has taken yet.
fn join_candidate(v: &Verdict, cands: &[Candidate], taken: &[bool]) -> Option<usize> {
    let exact = cands
        .iter()
        .position(|c| c.file == v.file && c.line == v.line && !taken_at(taken, c, cands));
    if exact.is_some() {
        return exact;
    }
    let mut best: Option<(usize, usize)> = None;
    for (i, c) in cands.iter().enumerate() {
        if c.file != v.file || taken[i] {
            continue;
        }
        let distance = c.line.abs_diff(v.line);
        if distance <= NEAR && best.map(|(_, d)| distance < d).unwrap_or(true) {
            best = Some((i, distance));
        }
    }
    best.map(|(i, _)| i)
}

/// Whether the candidate at this position was already joined.
fn taken_at(taken: &[bool], c: &Candidate, cands: &[Candidate]) -> bool {
    cands
        .iter()
        .position(|x| std::ptr::eq(x, c))
        .map(|i| taken[i])
        .unwrap_or(false)
}

/// Every row of the table: a row per verdict, its Check from the candidate it answers, then a
/// row per candidate no verifier reached, UNVERIFIED for a Nit or a Suggestion and PLAUSIBLE
/// with its check still to run for anything above. Numbered by the verdict's index where the
/// runner gave one, the rest after the highest.
fn rows(
    verdicts: &[Verdict],
    cands: &[Candidate],
    dropped: &[Dropped],
    tiers: &HashMap<String, String>,
) -> Vec<Row> {
    let mut taken = vec![false; cands.len()];
    let mut out = Vec::new();
    for v in verdicts {
        let joined = join_candidate(v, cands, &taken);
        if let Some(i) = joined {
            taken[i] = true;
        }
        let cand = joined.map(|i| &cands[i]);
        let check = cand
            .map(|c| c.verify_by.clone())
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| v.verify_by.clone());
        let angle = cand
            .map(|c| c.angle.clone())
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| v.angle.clone());
        let refuted = v.state == "REFUTED";
        let observed = if refuted && !v.refuted_by.is_empty() {
            v.refuted_by.clone()
        } else {
            v.evidence.clone()
        };
        out.push(Row {
            index: v.index.unwrap_or(0),
            state: v.state.clone(),
            band: v.band.clone(),
            file: v.file.clone(),
            line: v.line,
            check,
            observed,
            artifact: v.repro_path.clone(),
            tier: tiers.get(&v.file).cloned().unwrap_or_default(),
            angle,
            tldr: v.tldr.clone(),
            details: v.details.clone(),
            unrun: false,
        });
    }
    for (i, c) in cands.iter().enumerate() {
        let settled = dropped.iter().any(|d| d.file == c.file && d.line == c.line);
        if taken[i] || settled {
            continue;
        }
        let small = c.band == "Nit" || c.band == "Suggestion";
        out.push(Row {
            index: 0,
            state: if small { "UNVERIFIED" } else { "PLAUSIBLE" }.to_string(),
            band: c.band.clone(),
            file: c.file.clone(),
            line: c.line,
            check: c.verify_by.clone(),
            observed: if small {
                "not run: on the finder's read".to_string()
            } else {
                "not run: no verifier reached it; the check is still to run".to_string()
            },
            artifact: String::new(),
            tier: tiers.get(&c.file).cloned().unwrap_or_default(),
            angle: c.angle.clone(),
            tldr: c.summary.clone(),
            details: String::new(),
            unrun: true,
        });
    }
    number_rows(&mut out);
    out
}

/// Rows keep the runner's numbers and the unnumbered take the next ones, so a number in a
/// verifier's transcript still finds its row.
fn number_rows(rows: &mut [Row]) {
    let mut next = rows.iter().map(|r| r.index).max().unwrap_or(0) + 1;
    let mut used: Vec<usize> = Vec::new();
    for r in rows.iter_mut() {
        if r.index == 0 || used.contains(&r.index) {
            r.index = next;
            next += 1;
        }
        used.push(r.index);
    }
}

/// A cell of a markdown table: pipes escaped, whitespace collapsed.
fn cell(s: &str) -> String {
    s.replace('|', "\\|")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

/// The rows in the table's order: everything kept by number, then the refuted by number.
fn table_order(rows: &[Row]) -> Vec<&Row> {
    let mut kept: Vec<&Row> = rows.iter().filter(|r| r.state != "REFUTED").collect();
    let mut refuted: Vec<&Row> = rows.iter().filter(|r| r.state == "REFUTED").collect();
    kept.sort_by_key(|r| r.index);
    refuted.sort_by_key(|r| r.index);
    kept.extend(refuted);
    kept
}

/// The rows in posting order: by band as the draft posts them, then by file and line; a
/// refuted row never posts.
fn posting_order(rows: &[Row]) -> Vec<&Row> {
    let mut out: Vec<&Row> = rows.iter().filter(|r| r.state != "REFUTED").collect();
    out.sort_by(|a, b| {
        band_rank(&a.band)
            .cmp(&band_rank(&b.band))
            .then_with(|| a.file.cmp(&b.file))
            .then_with(|| a.line.cmp(&b.line))
    });
    out
}

/// Whether a row ships SKIP: a PLAUSIBLE Nit or Suggestion, a read that could not settle it.
fn skips(row: &Row) -> bool {
    row.state == "PLAUSIBLE" && (row.band == "Nit" || row.band == "Suggestion")
}

/// `claims.md`: the title and shape lines when given, the Candidates table, the hit rate per
/// tier when a risk table was given, the rows the finders settled, and an empty Completeness
/// section for the writer's answers.
fn claims_md(
    title: &str,
    shape: &str,
    rows: &[Row],
    dropped: &[Dropped],
    tiers: &HashMap<String, String>,
) -> String {
    let mut out = String::new();
    if !title.is_empty() {
        out.push_str(&format!("# {title}\n\n"));
    }
    if !shape.is_empty() {
        out.push_str(&format!("Round shape: {shape}\n\n"));
    }
    out.push_str("## Candidates\n\n| # | State | Band | file:line | Check | Observed | Artifact | Tier |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n");
    for r in table_order(rows) {
        out.push_str(&format!(
            "| {} | {} | {} | {}:{} | {} | {} | {} | {} |\n",
            r.index,
            r.state,
            cell(&r.band),
            r.file,
            r.line,
            cell(&r.check),
            cell(&r.observed),
            cell(&r.artifact),
            r.tier
        ));
    }
    if !tiers.is_empty() {
        out.push_str(&format!("\n{}\n", hit_rate(rows, tiers)));
    }
    if !dropped.is_empty() {
        out.push_str("\n### Settled by the finder, no verifier\n\n| Angle | file:line | Suspected | Settled by |\n| --- | --- | --- | --- |\n");
        for d in dropped {
            out.push_str(&format!(
                "| {} | {}:{} | {} | {} |\n",
                cell(&d.angle),
                d.file,
                d.line,
                cell(&d.summary),
                cell(&d.settled_by)
            ));
        }
    }
    out.push_str("\n## Completeness\n\n(the writer's answers)\n");
    out
}

/// The hit rate per tier: confirmed rows over rows, over the files the tier holds.
fn hit_rate(rows: &[Row], tiers: &HashMap<String, String>) -> String {
    let parts: Vec<String> = ["hot", "warm", "cold"]
        .iter()
        .map(|t| {
            let of_tier: Vec<&Row> = rows.iter().filter(|r| r.tier == *t).collect();
            let confirmed = of_tier.iter().filter(|r| r.state == "CONFIRMED").count();
            let files = tiers.values().filter(|v| v == t).count();
            format!(
                "{t} {confirmed}/{} confirmed over {files} files",
                of_tier.len()
            )
        })
        .collect();
    format!(
        "Hit rate per tier, from the rows above: {}.",
        parts.join(", ")
    )
}

/// `findings.md`: one block per finding in posting order, the header the draft will carry,
/// SKIP in front where the row ships none, and every field the writer composes from; the
/// check is on every block, since an unrun row is one the reader runs by hand.
fn findings_md(rows: &[Row], url: &str, misses: &[String]) -> String {
    let posting = posting_order(rows);
    let skipped = posting.iter().filter(|r| skips(r)).count();
    let refuted = rows.len() - posting.len();
    let mut out = format!(
        "# Findings in posting order, from round assemble: {} to post, {skipped} SKIP, {refuted} refuted kept out\n",
        posting.len() - skipped
    );
    if !misses.is_empty() {
        out.push_str("\n## Anchors that miss at the head\n\n");
        for m in misses {
            out.push_str(&format!("- {m}\n"));
        }
    }
    for r in posting {
        let skip = if skips(r) { "SKIP " } else { "" };
        let link = if url.is_empty() {
            String::new()
        } else {
            format!(
                " [gh]({}/{}#L{})",
                url.trim_end_matches('/'),
                r.file,
                r.line
            )
        };
        out.push_str(&format!("\n## {skip}{}:{}{link}\n", r.file, r.line));
        let read_only = if r.unrun {
            ", on the finder's read only"
        } else {
            ""
        };
        out.push_str(&format!(
            "State: {}, band: {}, angle: {}{read_only}\n",
            r.state, r.band, r.angle
        ));
        out.push_str(&format!("TL;DR: {}\n", r.tldr));
        if !r.check.is_empty() {
            out.push_str(&format!("Check: {}\n", r.check));
        }
        if !r.details.is_empty() {
            out.push_str(&format!("Details: {}\n", r.details));
        }
        if !r.observed.is_empty() {
            out.push_str(&format!("Evidence: {}\n", r.observed));
        }
        if !r.artifact.is_empty() {
            out.push_str(&format!("Artifact: {}\n", r.artifact));
        }
    }
    out
}

/// Every row whose file is not at the head or whose line lies past its end: with a sha,
/// through `git show`; without, the file in the worktree.
fn anchor_misses(rows: &[Row], repo: &str, sha: &str) -> Vec<String> {
    let mut out = Vec::new();
    for r in rows {
        if r.state == "REFUTED" {
            continue;
        }
        let blob = if sha.is_empty() {
            fs::read(Path::new(repo).join(&r.file)).map_err(|e| e.to_string())
        } else {
            super::command("git", &["-C", repo, "show", &format!("{sha}:{}", r.file)])
        };
        match blob {
            Err(why) => out.push(format!(
                "#{} {}:{}: the file is not at the head: {}",
                r.index,
                r.file,
                r.line,
                why.lines().next().unwrap_or("")
            )),
            Ok(bytes) => {
                let lines = count_lines(&bytes);
                if r.line > lines {
                    out.push(format!(
                        "#{} {}:{}: the file has {lines} lines",
                        r.index, r.file, r.line
                    ));
                }
            }
        }
    }
    out
}

/// The tiers of `round risk --json`: the file lists under hot, warm and cold.
fn read_tiers(path: &str) -> Result<HashMap<String, String>, String> {
    let text = fs::read_to_string(path).map_err(|e| format!("{path}: {e}"))?;
    let value: Value = serde_json::from_str(&text).map_err(|e| format!("{path}: {e}"))?;
    let mut out = HashMap::new();
    for tier in ["hot", "warm", "cold"] {
        for f in value
            .get(tier)
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            if let Some(name) = f.as_str() {
                out.insert(name.to_string(), tier.to_string());
            }
        }
    }
    Ok(out)
}

/// The command: reads the round directory, writes `claims.md` and `findings.md` beside its
/// inputs, prints the counts, and exits 1 when an anchor misses at the head.
pub fn assemble_cmd(args: &[String]) -> i32 {
    match run(args) {
        Ok((summary, misses)) => {
            println!("{summary}");
            for m in &misses {
                println!("anchor miss: {m}");
            }
            if misses.is_empty() {
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

/// The work of `assemble_cmd`: the summary line and the anchor misses.
fn run(args: &[String]) -> Result<(String, Vec<String>), String> {
    let round = Path::new(&args[0]);
    let opts = options(args)?;
    let empty = String::new();
    let cand_files = read_json_dir(&round.join("candidates"))?;
    let verdict_files = read_json_dir(&round.join("verdicts"))?;
    if cand_files.is_empty() && verdict_files.is_empty() {
        return Err(format!(
            "{}: no candidates/*.json and no verdicts/*.json",
            round.display()
        ));
    }
    let tiers = match opts.get("risk") {
        Some(path) => read_tiers(path)?,
        None => HashMap::new(),
    };
    let (cands, dropped) = candidates(&cand_files);
    let verdicts = verdicts(&verdict_files);
    let rows = rows(&verdicts, &cands, &dropped, &tiers);
    let misses = match opts.get("repo") {
        Some(repo) => anchor_misses(&rows, repo, opts.get("sha").unwrap_or(&empty)),
        None => Vec::new(),
    };
    let claims = claims_md(
        opts.get("title").unwrap_or(&empty),
        opts.get("shape").unwrap_or(&empty),
        &rows,
        &dropped,
        &tiers,
    );
    let findings = findings_md(&rows, opts.get("url").unwrap_or(&empty), &misses);
    fs::write(round.join("claims.md"), claims).map_err(|e| format!("claims.md: {e}"))?;
    fs::write(round.join("findings.md"), findings).map_err(|e| format!("findings.md: {e}"))?;
    Ok((
        summary(&rows, &dropped, &verdict_files, &cand_files),
        misses,
    ))
}

/// One line of counts: rows by state, dropped rows, files read, and what posts.
fn summary(
    rows: &[Row],
    dropped: &[Dropped],
    verdict_files: &[(String, Value)],
    cand_files: &[(String, Value)],
) -> String {
    let count = |state: &str| rows.iter().filter(|r| r.state == state).count();
    let posting = posting_order(rows);
    let skipped = posting.iter().filter(|r| skips(r)).count();
    format!(
        "assemble: {} rows from {} verdict files and {} candidate files: {} CONFIRMED, {} PLAUSIBLE, {} REFUTED, {} UNVERIFIED, {} settled by a finder; {} to post, {} SKIP; claims.md and findings.md written",
        rows.len(),
        verdict_files.len(),
        cand_files.len(),
        count("CONFIRMED"),
        count("PLAUSIBLE"),
        count("REFUTED"),
        count("UNVERIFIED"),
        dropped.len(),
        posting.len() - skipped,
        skipped
    )
}

#[cfg(test)]
mod tests {
    use super::super::testutil::tmp;
    use super::*;

    /// A round directory with two finders' candidates, one reflector drop and two verifiers'
    /// verdicts, over a head worktree of two files.
    fn fixture(name: &str) -> (PathBuf, PathBuf) {
        let round = tmp(&format!("assemble-{name}"));
        let head = tmp(&format!("assemble-{name}-head"));
        fs::create_dir_all(round.join("candidates")).unwrap();
        fs::create_dir_all(round.join("verdicts")).unwrap();
        fs::create_dir_all(head.join("pkg")).unwrap();
        fs::write(head.join("pkg/a.go"), "package a\n".repeat(50)).unwrap();
        fs::write(head.join("pkg/b.go"), "package b\n".repeat(10)).unwrap();
        fs::write(
            round.join("candidates/b1-lines.json"),
            r#"{"candidates": [
                {"file": "pkg/a.go", "line": 10, "angle": "lines", "summary": "zero ttl never expires", "verify_by": "go test ./pkg -run TestTTL", "band": "Warning", "checked": true},
                {"file": "pkg/a.go", "line": 30, "angle": "lines", "summary": "name shadows import", "verify_by": "grep -n 'ttl :=' pkg/a.go", "band": "Nit", "checked": true},
                {"file": "pkg/b.go", "line": 4, "angle": "lines", "summary": "unchecked error", "verify_by": "grep -n 'err' pkg/b.go", "band": "Nit", "checked": false}
              ], "dropped": [
                {"file": "pkg/a.go", "line": 40, "angle": "lines", "summary": "missing guard", "settled_by": "a.go:38 guards it"}
              ]}"#,
        )
        .unwrap();
        fs::write(
            round.join("candidates/b1-tests.json"),
            r#"{"candidates": [
                {"file": "pkg/a.go", "line": 10, "angle": "tests", "summary": "no test for zero ttl", "verify_by": "mutate TTL to 0", "band": "Missing test", "checked": true}
              ]}"#,
        )
        .unwrap();
        fs::write(
            round.join("verdicts/big-1.json"),
            r#"{"verdicts": [
                {"index": 1, "state": "CONFIRMED", "band": "Warning", "file": "pkg/a.go", "line": 12, "tldr": "a zero TTL never expires", "details": "The clamp is missing. Fix: clamp at the setter.", "evidence": "go test -run TestTTL: FAIL, entry alive at 5m", "repro_path": "tests/01-ttl.go", "base_behaves_the_same": false, "refuted_by": ""}
              ]}"#,
        )
        .unwrap();
        fs::write(
            round.join("verdicts/nits-1.json"),
            r#"{"verdicts": [
                {"index": 2, "state": "REFUTED", "band": "Nit", "file": "pkg/a.go", "line": 30, "tldr": "shadowing", "details": "", "evidence": "grep shows one binding", "repro_path": "", "base_behaves_the_same": true, "refuted_by": "a.go:30 declares ttl once"},
                {"index": 3, "state": "PLAUSIBLE", "band": "Nit", "file": "pkg/b.go", "line": 60, "tldr": "unchecked error", "details": "", "evidence": "the read could not settle it", "repro_path": "", "base_behaves_the_same": true, "refuted_by": ""}
              ]}"#,
        )
        .unwrap();
        (round, head)
    }

    fn run_on(round: &Path, extra: &[&str]) -> (i32, String, String) {
        let mut args: Vec<String> = vec![round.display().to_string()];
        args.extend(extra.iter().map(|s| s.to_string()));
        let code = assemble_cmd(&args);
        let claims = fs::read_to_string(round.join("claims.md")).unwrap_or_default();
        let findings = fs::read_to_string(round.join("findings.md")).unwrap_or_default();
        (code, claims, findings)
    }

    #[test]
    fn joins_a_verdict_to_the_nearest_candidate_and_merges_angles() {
        let (round, _) = fixture("join");
        let (code, claims, _) = run_on(&round, &[]);
        assert_eq!(code, 0);
        assert!(
            claims.contains("| 1 | CONFIRMED | Warning | pkg/a.go:12 | go test ./pkg -run TestTTL \\| mutate TTL to 0 | go test -run TestTTL: FAIL, entry alive at 5m | tests/01-ttl.go |  |"),
            "{claims}"
        );
    }

    #[test]
    fn a_refuted_row_keeps_its_proving_line_and_sits_last() {
        let (round, _) = fixture("refuted");
        let (_, claims, findings) = run_on(&round, &[]);
        let candidates = claims.split("### Settled").next().unwrap();
        let table: Vec<&str> = candidates
            .lines()
            .filter(|l| l.starts_with("| ") && !l.starts_with("| #"))
            .collect();
        assert!(table.last().unwrap().starts_with("| 2 | REFUTED | Nit | pkg/a.go:30 | grep -n 'ttl :=' pkg/a.go | a.go:30 declares ttl once |"), "{claims}");
        assert!(!findings.contains("pkg/a.go:30"), "{findings}");
    }

    #[test]
    fn a_plausible_nit_ships_skip_and_the_moved_line_stays_the_verdicts() {
        let (round, _) = fixture("skip");
        let (_, _, findings) = run_on(&round, &["--url", "https://x/blob/abc"]);
        assert!(
            findings.contains("## SKIP pkg/b.go:60 [gh](https://x/blob/abc/pkg/b.go#L60)"),
            "{findings}"
        );
        assert!(
            findings.contains("2 to post, 1 SKIP, 1 refuted kept out"),
            "{findings}"
        );
    }

    #[test]
    fn a_candidate_no_verifier_reached_is_a_row_and_a_dropped_one_is_not() {
        let (round, _) = fixture("unrun");
        fs::write(
            round.join("candidates/critic.json"),
            r#"{"candidates": [{"file": "pkg/b.go", "line": 2, "angle": "critic", "summary": "nothing covers the empty case", "verify_by": "go test -run TestEmpty", "band": "Warning", "checked": false}]}"#,
        )
        .unwrap();
        let (_, claims, findings) = run_on(&round, &[]);
        assert!(claims.contains("| 5 | PLAUSIBLE | Warning | pkg/b.go:2 | go test -run TestEmpty | not run: no verifier reached it; the check is still to run |  |  |"), "{claims}");
        assert!(
            claims.contains("| lines | pkg/a.go:40 | missing guard | a.go:38 guards it |"),
            "{claims}"
        );
        assert!(!claims.contains("pkg/a.go:40 | grep"), "{claims}");
        assert!(findings.contains("## pkg/b.go:2\nState: PLAUSIBLE, band: Warning, angle: critic, on the finder's read only\nTL;DR: nothing covers the empty case\nCheck: go test -run TestEmpty\n"), "{findings}");
    }

    #[test]
    fn posting_order_is_band_then_file_then_line() {
        let (round, _) = fixture("order");
        fs::write(
            round.join("verdicts/big-2.json"),
            r#"{"verdicts": [{"index": 5, "state": "CONFIRMED", "band": "Missing test", "file": "pkg/a.go", "line": 20, "tldr": "no zero case", "details": "", "evidence": "mutation survives", "repro_path": "tests/05-zero.go", "base_behaves_the_same": true, "refuted_by": ""}]}"#,
        )
        .unwrap();
        let (_, _, findings) = run_on(&round, &[]);
        let a = findings.find("## pkg/a.go:12").unwrap();
        let m = findings.find("## pkg/a.go:20").unwrap();
        let s = findings.find("## SKIP pkg/b.go:60").unwrap();
        assert!(a < m && m < s, "{findings}");
    }

    #[test]
    fn an_anchor_past_the_file_exits_one_and_is_listed() {
        let (round, head) = fixture("anchor");
        let (code, _, findings) = run_on(&round, &["--repo", &head.display().to_string()]);
        assert_eq!(code, 1);
        assert!(
            findings.contains("- #3 pkg/b.go:60: the file has 10 lines"),
            "{findings}"
        );
        assert!(!findings.contains("#1 pkg/a.go:12"), "{findings}");
    }

    #[test]
    fn tiers_and_the_hit_rate_come_from_the_risk_json() {
        let (round, _) = fixture("tiers");
        let risk = round.join("risk.json");
        fs::write(
            &risk,
            r#"{"hot": ["pkg/a.go"], "warm": [], "cold": ["pkg/b.go", "docs/x.md"]}"#,
        )
        .unwrap();
        let (_, claims, _) = run_on(
            &round,
            &[
                "--risk",
                &risk.display().to_string(),
                "--title",
                "Claims: PR 1 round 1",
                "--shape",
                "2 finders",
            ],
        );
        assert!(
            claims.starts_with("# Claims: PR 1 round 1\n\nRound shape: 2 finders\n\n## Candidates"),
            "{claims}"
        );
        assert!(claims.contains("| tests/01-ttl.go | hot |"), "{claims}");
        assert!(claims.contains("Hit rate per tier, from the rows above: hot 1/2 confirmed over 1 files, warm 0/0 confirmed over 0 files, cold 0/2 confirmed over 2 files."), "{claims}");
    }

    #[test]
    fn an_empty_round_and_a_bad_file_are_errors() {
        let round = tmp("assemble-empty");
        assert_eq!(assemble_cmd(&[round.display().to_string()]), 2);
        fs::create_dir_all(round.join("verdicts")).unwrap();
        fs::write(round.join("verdicts/x.json"), "{not json").unwrap();
        assert_eq!(assemble_cmd(&[round.display().to_string()]), 2);
    }
}
