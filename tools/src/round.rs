// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! The deterministic steps of a review round, one subcommand each. Prose in
//! skills/review.md names the step; this binary runs it, so no agent turn does.
use regex::Regex;
use std::collections::{BTreeMap, HashMap};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

pub const USAGE: &str = "round <subcommand> ...

  links <round dir> [--repo <git dir>] [--out <file>]
      Every blob link in the round's comment_*.md and the overview.md beside it: the
      file at the pinned sha, through git show in --repo when the sha is there, else
      gh api, and the #L range inside it. One row per link into <round dir>/links.md,
      exit 1 when any link misses.

  prior <slug dir> --repo <git dir> --sha <head sha> [--json <file>]
      The Check cell of every candidate row in the slug's earlier claims.md files,
      keyed file:line at the head: a row's line is mapped from its round's sha to the
      head through git diff, and a row whose line the head removed is dropped. The
      State and Observed cells never leave the file. JSON to --json, else to stdout.";

pub fn dispatch(args: &[String]) -> i32 {
    match args.first().map(String::as_str) {
        Some("links") if args.len() >= 2 => links(&args[1..]),
        Some("prior") if args.len() >= 2 => prior(&args[1..]),
        _ => { eprintln!("{USAGE}"); 2 }
    }
}

/// Named options after the positional argument: `--flag value` pairs into a map.
pub fn options(args: &[String]) -> Result<HashMap<String, String>, String> {
    let mut out = HashMap::new();
    let mut i = 1;
    while i < args.len() {
        let (k, v) = (args[i].as_str(), args.get(i + 1));
        match (k.strip_prefix("--"), v) {
            (Some(k), Some(v)) => { out.insert(k.to_string(), v.clone()); i += 2 }
            _ => return Err(format!("unexpected argument {k}")),
        }
    }
    Ok(out)
}

fn run(cmd: &str, args: &[&str]) -> Option<Vec<u8>> {
    let o = Command::new(cmd).args(args).output().ok()?;
    if o.status.success() { Some(o.stdout) } else { None }
}

pub fn count_lines(b: &[u8]) -> usize {
    let n = b.iter().filter(|&&c| c == b'\n').count();
    if b.last().map(|&c| c != b'\n').unwrap_or(false) { n + 1 } else { n }
}

// ---- links ---------------------------------------------------------------

pub struct Link { pub file: String, pub url: String, pub owner: String, pub repo: String, pub sha: String, pub path: String, pub a: Option<usize>, pub b: Option<usize> }

/// Every blob link in a text, with the file name it came from.
pub fn find_links(file: &str, text: &str) -> Vec<Link> {
    let re = Regex::new(r"\]\((https://github\.com/([\w.-]+)/([\w.-]+)/blob/([0-9a-f]{7,40})/([^#)\s?]+)(?:\?plain=1)?(?:#L(\d+)(?:-L(\d+))?)?)\)").unwrap();
    re.captures_iter(text).map(|c| Link {
        file: file.to_string(),
        url: c[1].to_string(), owner: c[2].to_string(), repo: c[3].to_string(), sha: c[4].to_string(), path: c[5].to_string(),
        a: c.get(6).and_then(|m| m.as_str().parse().ok()),
        b: c.get(7).and_then(|m| m.as_str().parse().ok()),
    }).collect()
}

/// The row's verdict: whether the file resolves and whether the range fits its line count.
pub fn judge(n: Option<usize>, a: Option<usize>, b: Option<usize>) -> (&'static str, String) {
    match (n, a) {
        (None, _) => ("no", "file missing at the sha".to_string()),
        (Some(n), None) => ("yes", format!("{n} lines, no anchor")),
        (Some(n), Some(a)) => {
            let end = b.unwrap_or(a);
            if a >= 1 && a <= end && end <= n { ("yes", format!("L{a}-L{end} of {n}")) } else { ("no", format!("L{a}-L{end} outside {n} lines")) }
        }
    }
}

pub fn links(args: &[String]) -> i32 {
    let round = PathBuf::from(&args[0]);
    let opts = match options(args) { Ok(o) => o, Err(e) => { eprintln!("{e}\n{USAGE}"); return 2 } };
    let repo = opts.get("repo").map(PathBuf::from);
    let out = opts.get("out").map(PathBuf::from).unwrap_or_else(|| round.join("links.md"));
    let mut files: Vec<PathBuf> = match fs::read_dir(&round) {
        Ok(rd) => rd.flatten().map(|e| e.path()).filter(|p| {
            let name = p.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
            name.starts_with("comment_") && name.ends_with(".md")
        }).collect(),
        Err(e) => { eprintln!("{}: {e}", round.display()); return 2 }
    };
    files.sort();
    if let Some(parent) = round.parent() {
        let overview = parent.join("overview.md");
        if overview.exists() { files.push(overview) }
    }
    let mut found = Vec::new();
    for f in &files {
        let name = f.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        found.extend(find_links(&name, &fs::read_to_string(f).unwrap_or_default()));
    }
    let mut cache: HashMap<(String, String), Option<usize>> = HashMap::new();
    let mut rows = vec!["| File | Link | Resolves | Lines |".to_string(), "| --- | --- | --- | --- |".to_string()];
    let mut misses = 0;
    for l in &found {
        let n = *cache.entry((l.sha.clone(), l.path.clone())).or_insert_with(|| line_count(repo.as_deref(), &l.owner, &l.repo, &l.sha, &l.path));
        let (resolves, lines) = judge(n, l.a, l.b);
        if resolves == "no" { misses += 1 }
        rows.push(format!("| {} | [{}]({}) | {} | {} |", l.file, l.path, l.url, resolves, lines));
    }
    rows.push(String::new());
    rows.push(format!("{} links over {} files, {} missing.", found.len(), files.len(), misses));
    if let Err(e) = fs::write(&out, rows.join("\n") + "\n") { eprintln!("{}: {e}", out.display()); return 2 }
    println!("{} links over {} files, {} missing, table at {}", found.len(), files.len(), misses, out.display());
    if misses > 0 { 1 } else { 0 }
}

/// Lines of the file at the sha: through git in the repo when it holds the commit, else through gh api.
fn line_count(repo: Option<&Path>, owner: &str, name: &str, sha: &str, path: &str) -> Option<usize> {
    if let Some(r) = repo {
        if let Some(b) = run("git", &["-C", &r.to_string_lossy(), "show", &format!("{sha}:{path}")]) { return Some(count_lines(&b)) }
    }
    run("gh", &["api", "-H", "Accept: application/vnd.github.raw", &format!("repos/{owner}/{name}/contents/{path}?ref={sha}")]).map(|b| count_lines(&b))
}

// ---- prior ---------------------------------------------------------------

/// Old-line to new-line mapping of one file between two commits, from the hunks of `git diff -U0`.
pub struct LineMap { pub hunks: Vec<(usize, usize, usize, usize)> }

impl LineMap {
    pub fn load(repo: &Path, old: &str, new: &str, path: &str) -> Option<LineMap> {
        let out = run("git", &["-C", &repo.to_string_lossy(), "diff", "-U0", "--no-color", old, new, "--", path])?;
        Some(LineMap::parse(&String::from_utf8_lossy(&out)))
    }
    pub fn parse(diff: &str) -> LineMap {
        let re = Regex::new(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@").unwrap();
        let num = |c: &regex::Captures, i: usize, default: usize| c.get(i).and_then(|m| m.as_str().parse().ok()).unwrap_or(default);
        LineMap { hunks: diff.lines().filter_map(|l| re.captures(l)).map(|c| (num(&c, 1, 0), num(&c, 2, 1), num(&c, 3, 0), num(&c, 4, 1))).collect() }
    }
    /// None when the line sits inside a hunk's removed range: the head no longer holds it.
    pub fn map(&self, line: usize) -> Option<usize> {
        let mut offset: isize = 0;
        for &(old_start, old_len, _, new_len) in &self.hunks {
            if old_len > 0 && line >= old_start && line < old_start + old_len { return None }
            let last = old_start + old_len.saturating_sub(1);
            if line > last { offset += new_len as isize - old_len as isize } else { break }
        }
        Some((line as isize + offset).max(1) as usize)
    }
}

/// A candidate row of claims.md, with or without the leading # column an earlier round's table lacks.
pub fn parse_row(line: &str) -> Option<(String, String)> {
    let row = Regex::new(r"^\|\s*(?:(\d*)\s*\|\s*)?([A-Z]+)\s*\|[^|]*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|").unwrap();
    let c = row.captures(line)?;
    Some((c[3].trim().to_string(), c[4].trim().to_string()))
}

pub fn prior(args: &[String]) -> i32 {
    let slug = PathBuf::from(&args[0]);
    let opts = match options(args) { Ok(o) => o, Err(e) => { eprintln!("{e}\n{USAGE}"); return 2 } };
    let repo = opts.get("repo").map(PathBuf::from);
    let head = opts.get("sha").cloned();
    if repo.is_none() != head.is_none() { eprintln!("--repo and --sha go together\n{USAGE}"); return 2 }
    let mut dirs: Vec<PathBuf> = match fs::read_dir(&slug) {
        Ok(rd) => rd.flatten().map(|e| e.path()).filter(|p| p.join("claims.md").exists()).collect(),
        Err(e) => { eprintln!("{}: {e}", slug.display()); return 2 }
    };
    dirs.sort();
    let mut checks: BTreeMap<String, Vec<(String, String)>> = BTreeMap::new();
    let mut maps: HashMap<(String, String), Option<LineMap>> = HashMap::new();
    let (mut kept, mut dropped, mut moved) = (0, 0, 0);
    for d in &dirs {
        let round = d.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
        let old_sha = round.split_once('-').map(|(_, s)| s.to_string()).unwrap_or_default();
        let text = fs::read_to_string(d.join("claims.md")).unwrap_or_default();
        for line in text.lines() {
            let Some((anchor, check)) = parse_row(line) else { continue };
            if check.is_empty() || check == "---" { continue }
            let Some((path, ln)) = anchor.rsplit_once(':') else { continue };
            let Ok(ln) = ln.parse::<usize>() else { continue };
            let mapped = match (&repo, &head) {
                (Some(r), Some(new)) if !old_sha.is_empty() && !new.starts_with(&old_sha) && !old_sha.starts_with(new.as_str()) => {
                    match maps.entry((old_sha.clone(), path.to_string())).or_insert_with(|| LineMap::load(r, &old_sha, new, path)) {
                        Some(m) => { let n = m.map(ln); if n.is_some() && n != Some(ln) { moved += 1 } n }
                        None => Some(ln),
                    }
                }
                _ => Some(ln),
            };
            match mapped {
                Some(n) => { kept += 1; checks.entry(format!("{path}:{n}")).or_default().push((round.clone(), check)) }
                None => dropped += 1,
            }
        }
    }
    let json = to_json(&checks);
    let summary = format!("{} anchors from {} prior claims.md: {kept} rows kept, {moved} re-anchored to the head, {dropped} dropped whose line the head removed", checks.len(), dirs.len());
    match opts.get("json") {
        Some(p) => { if let Err(e) = fs::write(p, json + "\n") { eprintln!("{p}: {e}"); return 2 } println!("{summary}, written to {p}") }
        None => { println!("{json}"); eprintln!("{summary}") }
    }
    0
}

pub fn esc(s: &str) -> String {
    let mut o = String::with_capacity(s.len() + 2);
    for ch in s.chars() {
        match ch { '"' => o.push_str("\\\""), '\\' => o.push_str("\\\\"), '\n' => o.push_str("\\n"), '\t' => o.push_str("\\t"), c if (c as u32) < 0x20 => o.push_str(&format!("\\u{:04x}", c as u32)), c => o.push(c) }
    }
    o
}

pub fn to_json(checks: &BTreeMap<String, Vec<(String, String)>>) -> String {
    let entries: Vec<String> = checks.iter().map(|(k, rows)| {
        let items: Vec<String> = rows.iter().map(|(r, c)| format!("{{\"round\": \"{}\", \"check\": \"{}\"}}", esc(r), esc(c))).collect();
        format!("\"{}\": [{}]", esc(k), items.join(", "))
    }).collect();
    format!("{{{}}}", entries.join(", "))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("skills-tools-round-{}", std::process::id())).join(name);
        let _ = fs::remove_dir_all(&d);
        fs::create_dir_all(&d).unwrap();
        d
    }
    fn git(dir: &Path, args: &[&str]) -> String {
        let o = Command::new("git").arg("-C").arg(dir).args(args)
            .env("GIT_AUTHOR_NAME", "t").env("GIT_AUTHOR_EMAIL", "t@x").env("GIT_COMMITTER_NAME", "t").env("GIT_COMMITTER_EMAIL", "t@x")
            .output().unwrap();
        assert!(o.status.success(), "git {:?}: {}", args, String::from_utf8_lossy(&o.stderr));
        String::from_utf8_lossy(&o.stdout).trim().to_string()
    }
    /// A repository with f.go at two commits: lines x, y inserted at the top, d deleted, g appended.
    fn shifted_repo(name: &str) -> (PathBuf, String, String) {
        let d = tmp(name);
        git(&d, &["init", "-q"]);
        fs::write(d.join("f.go"), "a\nb\nc\nd\ne\nf\n").unwrap();
        git(&d, &["add", "."]); git(&d, &["commit", "-qm", "one"]);
        let s1 = git(&d, &["rev-parse", "--short=9", "HEAD"]);
        fs::write(d.join("f.go"), "x\ny\na\nb\nc\ne\nf\ng\n").unwrap();
        git(&d, &["add", "."]); git(&d, &["commit", "-qm", "two"]);
        let s2 = git(&d, &["rev-parse", "--short=9", "HEAD"]);
        (d, s1, s2)
    }

    #[test] fn options_pairs_and_errors() {
        let o = options(&["x".into(), "--repo".into(), "r".into(), "--out".into(), "o".into()]).unwrap();
        assert_eq!(o["repo"], "r"); assert_eq!(o["out"], "o");
        assert!(options(&["x".into(), "--repo".into()]).is_err());
        assert!(options(&["x".into(), "stray".into()]).is_err());
    }
    #[test] fn count_lines_with_and_without_a_final_newline() {
        assert_eq!(count_lines(b""), 0); assert_eq!(count_lines(b"a"), 1); assert_eq!(count_lines(b"a\n"), 1); assert_eq!(count_lines(b"a\nb"), 2);
    }
    #[test] fn find_links_parses_every_shape() {
        let t = "[a](https://github.com/o/r/blob/0123456789/p/q.go#L3-L5) [b](https://github.com/o/r/blob/0123456789/d.md?plain=1#L7) [c](https://github.com/o/r/blob/0123456789/x.rs) [d](https://example.com/blob/0123456789/x) [e](https://github.com/o/r/pull/1)";
        let l = find_links("f", t);
        assert_eq!(l.len(), 3);
        assert_eq!((l[0].path.as_str(), l[0].a, l[0].b), ("p/q.go", Some(3), Some(5)));
        assert_eq!((l[1].path.as_str(), l[1].a, l[1].b), ("d.md", Some(7), None));
        assert_eq!((l[2].path.as_str(), l[2].a, l[2].owner.as_str(), l[2].sha.as_str()), ("x.rs", None, "o", "0123456789"));
    }
    #[test] fn judge_ranges() {
        assert_eq!(judge(None, Some(1), None).0, "no");
        assert_eq!(judge(Some(10), None, None), ("yes", "10 lines, no anchor".into()));
        assert_eq!(judge(Some(10), Some(3), Some(10)), ("yes", "L3-L10 of 10".into()));
        assert_eq!(judge(Some(10), Some(3), Some(11)).0, "no");
        assert_eq!(judge(Some(10), Some(0), None).0, "no");
        assert_eq!(judge(Some(10), Some(5), Some(4)).0, "no");
    }
    #[test] fn line_map_hunks() {
        let m = LineMap::parse("@@ -0,0 +1,2 @@\n+x\n+y\n@@ -4 +6,0 @@\n-d\n@@ -6,0 +8 @@\n+g\n");
        assert_eq!(m.hunks, vec![(0, 0, 1, 2), (4, 1, 6, 0), (6, 0, 8, 1)]);
        assert_eq!(m.map(1), Some(3)); assert_eq!(m.map(2), Some(4)); assert_eq!(m.map(4), None); assert_eq!(m.map(5), Some(6)); assert_eq!(m.map(6), Some(7));
    }
    #[test] fn line_map_replacement_and_no_hunks() {
        let m = LineMap::parse("@@ -3,2 +3,3 @@\n-c\n-d\n+C\n+D\n+E\n");
        assert_eq!(m.map(2), Some(2)); assert_eq!(m.map(3), None); assert_eq!(m.map(4), None); assert_eq!(m.map(5), Some(6));
        assert_eq!(LineMap::parse("").map(9), Some(9));
    }
    #[test] fn line_map_from_git() {
        let (d, s1, s2) = shifted_repo("linemap");
        let m = LineMap::load(&d, &s1, &s2, "f.go").unwrap();
        assert_eq!((m.map(2), m.map(4), m.map(5), m.map(6)), (Some(4), None, Some(6), Some(7)));
        assert!(LineMap::load(&d, "0000000", &s2, "f.go").is_none(), "an unknown sha yields no map");
    }
    #[test] fn parse_row_both_shapes() {
        assert_eq!(parse_row("| 3 | CONFIRMED | Warning | a/b.go:12 | grep x | out | art |"), Some(("a/b.go:12".into(), "grep x".into())));
        assert_eq!(parse_row("| REFUTED | Nit | a.go:1 | ls | out | |"), Some(("a.go:1".into(), "ls".into())));
        assert_eq!(parse_row("| # | State | Band | file:line | Check | Observed | Artifact |"), None);
        assert_eq!(parse_row("| --- | --- | --- | --- | --- |"), None);
        assert_eq!(parse_row("plain text"), None);
    }
    #[test] fn json_escaping() {
        assert_eq!(esc("a\"b\\c\nd\te\u{1}"), "a\\\"b\\\\c\\nd\\te\\u0001");
        let mut m = BTreeMap::new(); m.insert("f:1".to_string(), vec![("r".to_string(), "c \"q\"".to_string())]);
        assert_eq!(to_json(&m), "{\"f:1\": [{\"round\": \"r\", \"check\": \"c \\\"q\\\"\"}]}");
        assert_eq!(to_json(&BTreeMap::new()), "{}");
    }
    #[test] fn prior_reanchors_drops_and_keeps() {
        let (d, s1, s2) = shifted_repo("prior");
        let slug = tmp("prior-slug");
        let r1 = slug.join(format!("1-{s1}")); fs::create_dir_all(&r1).unwrap();
        fs::write(r1.join("claims.md"), "| # | State | Band | file:line | Check | Observed | Artifact |\n| --- | --- | --- | --- | --- | --- | --- |\n| 1 | CONFIRMED | Warning | f.go:2 | grep -n b f.go | 2:b | |\n| 2 | REFUTED | Nit | f.go:4 | grep -n d f.go | 4:d | |\n| 3 | PLAUSIBLE | Warning | f.go:5 | --- | | |\n| 4 | CONFIRMED | Nit | f.go:6 | grep -n f f.go | 6:f | |\n| 5 | CONFIRMED | Nit | noline | grep | | |\n").unwrap();
        let out = slug.join("prior.json");
        let code = prior(&[slug.to_string_lossy().into_owned(), "--repo".into(), d.to_string_lossy().into_owned(), "--sha".into(), s2.clone(), "--json".into(), out.to_string_lossy().into_owned()]);
        assert_eq!(code, 0);
        let json = fs::read_to_string(&out).unwrap();
        assert_eq!(json.trim(), format!("{{\"f.go:4\": [{{\"round\": \"1-{s1}\", \"check\": \"grep -n b f.go\"}}], \"f.go:7\": [{{\"round\": \"1-{s1}\", \"check\": \"grep -n f f.go\"}}]}}"));
        let code = prior(&[slug.to_string_lossy().into_owned(), "--json".into(), out.to_string_lossy().into_owned()]);
        assert_eq!(code, 0);
        assert!(fs::read_to_string(&out).unwrap().contains("\"f.go:2\""), "without a head the rows keep their lines");
        assert_eq!(prior(&[slug.to_string_lossy().into_owned(), "--repo".into(), "x".into()]), 2, "--repo without --sha");
        assert_eq!(prior(&["/nonexistent/slug".into()]), 2);
    }
    #[test] fn links_over_a_round_directory() {
        let (d, _s1, s2) = shifted_repo("links");
        let slug = tmp("links-slug");
        let round = slug.join(format!("1-{s2}")); fs::create_dir_all(&round).unwrap();
        fs::write(round.join("comment_x.md"), format!("[ok](https://github.com/o/r/blob/{s2}/f.go#L2-L4) and [far](https://github.com/o/r/blob/{s2}/f.go#L9) and [gone](https://github.com/o/r/blob/{s2}/nope.go#L1)\n")).unwrap();
        fs::write(slug.join("overview.md"), format!("[whole](https://github.com/o/r/blob/{s2}/f.go)\n")).unwrap();
        let out = round.join("links.md");
        let code = links(&[round.to_string_lossy().into_owned(), "--repo".into(), d.to_string_lossy().into_owned()]);
        assert_eq!(code, 1);
        let table = fs::read_to_string(&out).unwrap();
        assert!(table.contains("| comment_x.md | [f.go](https://github.com/o/r/blob/") && table.contains("| yes | L2-L4 of 8 |"), "{table}");
        assert!(table.contains("| no | L9-L9 outside 8 lines |"));
        assert!(table.contains("| no | file missing at the sha |"));
        assert!(table.contains("| overview.md | [f.go]") && table.contains("| yes | 8 lines, no anchor |"));
        assert!(table.trim_end().ends_with("4 links over 2 files, 2 missing."));
        fs::write(round.join("comment_x.md"), format!("[ok](https://github.com/o/r/blob/{s2}/f.go#L2-L4)\n")).unwrap();
        assert_eq!(links(&[round.to_string_lossy().into_owned(), "--repo".into(), d.to_string_lossy().into_owned()]), 0);
        assert_eq!(links(&["/nonexistent/round".into()]), 2);
    }
    #[test] fn dispatch_usage() {
        assert_eq!(dispatch(&[]), 2); assert_eq!(dispatch(&["nope".into()]), 2); assert_eq!(dispatch(&["links".into()]), 2);
    }
}
