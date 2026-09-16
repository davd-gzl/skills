// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! `round risk`: the changed files of a diff ranked by how likely a defect sits in them, from
//! signals git and the diff already carry, so a round spends its finders where a bug is
//! likeliest and still reads everything once. The weights sit in one table below, and the
//! retro's hit rate per tier is what tunes them.
use super::{command, options, parse_row, USAGE};
use regex::Regex;
use std::collections::{BTreeSet, HashMap, HashSet};
use std::fs;
use std::path::Path;
use std::sync::LazyLock;

/// The weights, one line each. Tuned by the retro's hit rate per tier, never by feel.
pub mod weight {
    /// A deleted line that was a guard: a condition, an early return, a panic, a lock.
    pub const GUARD_REMOVED: u32 = 3;
    pub const GUARD_REMOVED_CAP: u32 = 9;
    /// A distinct catalog keyword in the added lines: auth, sign, decode, lock, overflow.
    pub const KEYWORD: u32 = 2;
    pub const KEYWORD_CAP: u32 = 8;
    /// A code file with no test touched beside it, in the diff or in its own added lines.
    pub const NO_TEST: u32 = 2;
    /// A commit in the file's history whose subject names a fix, a bug, a crash, a regression.
    pub const FIX_HISTORY: u32 = 1;
    pub const FIX_HISTORY_CAP: u32 = 3;
    /// Fifty lines changed, and two hundred.
    pub const SIZE_50: u32 = 1;
    pub const SIZE_200: u32 = 2;
    /// A file an earlier round confirmed a finding in.
    pub const PRIOR_CONFIRMED: u32 = 3;
    /// Where warm becomes hot; a removed guard is hot on its own.
    pub const HOT: u32 = 6;
}

/// What a changed file is, which decides whether it can be hot at all.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    Code,
    Test,
    Doc,
    Generated,
    Config,
}

impl Kind {
    fn name(self) -> &'static str {
        match self {
            Kind::Code => "code",
            Kind::Test => "test",
            Kind::Doc => "doc",
            Kind::Generated => "generated",
            Kind::Config => "config",
        }
    }
}

/// How many passes a file earns: hot gets the repeats, warm one full pass, cold one cheap one.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Tier {
    Hot,
    Warm,
    Cold,
}

impl Tier {
    fn name(self) -> &'static str {
        match self {
            Tier::Hot => "hot",
            Tier::Warm => "warm",
            Tier::Cold => "cold",
        }
    }
}

/// One changed file and what was read about it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FileRisk {
    pub path: String,
    pub added: usize,
    pub deleted: usize,
    pub kind: Kind,
    /// Each signal in words, its weight already in `score`.
    pub signals: Vec<String>,
    pub score: u32,
    pub tier: Tier,
}

/// The default catalog keywords, matched as whole words in the added lines. `--keywords`
/// replaces them with a file's lines.
pub const KEYWORDS: &[&str] = &[
    "auth",
    "token",
    "secret",
    "password",
    "sign",
    "verify",
    "crypto",
    "hash",
    "decode",
    "unmarshal",
    "parse",
    "sql",
    "exec",
    "shell",
    "lock",
    "mutex",
    "atomic",
    "unsafe",
    "overflow",
    "amount",
    "balance",
    "transfer",
    "fee",
    "permission",
    "admin",
    "owner",
    "gas",
    "ttl",
    "timeout",
    "retry",
    "cache",
];

static GUARD: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"(?i)^\s*(if|else if|switch|case|return|panic\(|throw|raise|defer)\b|\b(assert|require|check|verify|validate|ensure)\w*\(|\.(Lock|Unlock|RLock|RUnlock)\(|!= nil|== nil|=== null|== null|is None|is not None",
    )
    .unwrap()
});
static FIX_SUBJECT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)\b(fix|fixes|fixed|bug|crash|panic|regress\w*|security|cve|leak|race)\b")
        .unwrap()
});
static TEST_PATH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(_test\.(go|rs)$|(^|/)test_[^/]*\.py$|\.(test|spec)\.[cm]?[jt]sx?$|(^|/)tests?/)")
        .unwrap()
});
static TEST_LINE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^\s*(#\[test\]|func Test|def test_|it\(|test\(|describe\()").unwrap()
});
static DOC_PATH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(\.(md|txt|rst|adoc)$|(^|/)docs?/|LICENSE|CHANGELOG|NOTICE)").unwrap()
});
static GENERATED_PATH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(\.pb\.go$|\.gen\.|_generated|(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|go\.sum|poetry\.lock)$)")
        .unwrap()
});
static GENERATED_LINE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(Code generated|DO NOT EDIT|@generated)").unwrap());
static CONFIG_PATH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(\.(json|ya?ml|toml|ini|cfg|env|lock)$|(^|/)(Dockerfile|Makefile|\.github/))")
        .unwrap()
});
static DIFF_HEADER: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^diff --git a/(.+?) b/(.+)$").unwrap());

/// The kind a path and its added lines settle. Generated wins over test and doc, since a
/// generated test is still not read; test over code, since a test file is never hot.
pub fn kind_of(path: &str, added_lines: &[&str]) -> Kind {
    if GENERATED_PATH.is_match(path)
        || added_lines
            .iter()
            .take(5)
            .any(|l| GENERATED_LINE.is_match(l))
    {
        Kind::Generated
    } else if TEST_PATH.is_match(path) {
        Kind::Test
    } else if DOC_PATH.is_match(path) {
        Kind::Doc
    } else if CONFIG_PATH.is_match(path) {
        Kind::Config
    } else {
        Kind::Code
    }
}

/// The deleted lines that were guards.
pub fn guards_removed(deleted_lines: &[&str]) -> usize {
    deleted_lines.iter().filter(|l| GUARD.is_match(l)).count()
}

/// The distinct keywords the added lines carry, as whole words, case folded.
pub fn keywords_in(added_lines: &[&str], keywords: &[String]) -> Vec<String> {
    let text: String = added_lines
        .iter()
        .map(|l| l.to_lowercase())
        .collect::<Vec<_>>()
        .join("\n");
    let mut hits = Vec::new();
    for word in keywords {
        let pattern = format!(r"\b{}\b", regex::escape(&word.to_lowercase()));
        if Regex::new(&pattern)
            .map(|re| re.is_match(&text))
            .unwrap_or(false)
        {
            hits.push(word.clone());
        }
    }
    hits
}

/// The changed files with their added and deleted lines, from one `git diff -U0`.
struct Hunks {
    added: HashMap<String, Vec<String>>,
    deleted: HashMap<String, Vec<String>>,
}

fn hunks(repo: &str, base: &str, head: &str) -> Result<Hunks, String> {
    let diff = command(
        "git",
        &["-C", repo, "diff", "-U0", "--no-color", "-M", base, head],
    )?;
    let diff = String::from_utf8_lossy(&diff);
    let mut out = Hunks {
        added: HashMap::new(),
        deleted: HashMap::new(),
    };
    let mut current = String::new();
    for line in diff.lines() {
        if let Some(caps) = DIFF_HEADER.captures(line) {
            current = caps[2].to_string();
            continue;
        }
        if current.is_empty() || line.starts_with("+++") || line.starts_with("---") {
            continue;
        }
        if let Some(rest) = line.strip_prefix('+') {
            out.added
                .entry(current.clone())
                .or_default()
                .push(rest.to_string());
        } else if let Some(rest) = line.strip_prefix('-') {
            out.deleted
                .entry(current.clone())
                .or_default()
                .push(rest.to_string());
        }
    }
    Ok(out)
}

/// One `added deleted path` row of `git diff --numstat`, a rename's braces resolved to the
/// new path and a binary file's dashes read as zero.
fn numstat(repo: &str, base: &str, head: &str) -> Result<Vec<(String, usize, usize)>, String> {
    let out = command("git", &["-C", repo, "diff", "--numstat", "-M", base, head])?;
    let text = String::from_utf8_lossy(&out);
    let rename = Regex::new(r"\{(.*?) => (.*?)\}").unwrap();
    let mut rows = Vec::new();
    for line in text.lines() {
        let mut parts = line.splitn(3, '\t');
        let (Some(a), Some(d), Some(path)) = (parts.next(), parts.next(), parts.next()) else {
            continue;
        };
        let path = if path.contains(" => ") && !path.contains('{') {
            path.split(" => ").last().unwrap_or(path).to_string()
        } else {
            rename.replace_all(path, "$2").to_string()
        };
        rows.push((path, a.parse().unwrap_or(0), d.parse().unwrap_or(0)));
    }
    Ok(rows)
}

/// Commits in the file's last hundred whose subject names a fix.
fn fix_history(repo: &str, head: &str, path: &str) -> usize {
    let Ok(out) = command(
        "git",
        &[
            "-C",
            repo,
            "log",
            "--format=%s",
            "-n",
            "100",
            head,
            "--",
            path,
        ],
    ) else {
        return 0;
    };
    String::from_utf8_lossy(&out)
        .lines()
        .filter(|s| FIX_SUBJECT.is_match(s))
        .count()
}

/// The files earlier rounds confirmed a finding in, from the slug's `claims.md` tables.
fn prior_confirmed(slug: &Path) -> BTreeSet<String> {
    let mut paths = BTreeSet::new();
    let Ok(dirs) = fs::read_dir(slug) else {
        return paths;
    };
    for entry in dirs.flatten() {
        let text = fs::read_to_string(entry.path().join("claims.md")).unwrap_or_default();
        for row in text.lines().filter_map(parse_row) {
            if row.state != "CONFIRMED" {
                continue;
            }
            if let Some((path, _)) = row.anchor.trim_matches('`').rsplit_once(':') {
                paths.insert(path.to_string());
            }
        }
    }
    paths
}

/// Every changed file scored. `prior` holds the paths earlier rounds confirmed findings in.
pub fn rank(
    repo: &str,
    base: &str,
    head: &str,
    keywords: &[String],
    prior: &BTreeSet<String>,
) -> Result<Vec<FileRisk>, String> {
    let rows = numstat(repo, base, head)?;
    let lines = hunks(repo, base, head)?;
    // A test touched anywhere in a directory covers the code files beside it.
    let mut tested_dirs: HashSet<String> = HashSet::new();
    for (path, _, _) in &rows {
        let added: Vec<&str> = lines
            .added
            .get(path)
            .map(|v| v.iter().map(String::as_str).collect())
            .unwrap_or_default();
        if TEST_PATH.is_match(path) || added.iter().any(|l| TEST_LINE.is_match(l)) {
            tested_dirs.insert(dir_of(path));
        }
    }
    let mut out = Vec::new();
    for (path, added, deleted) in rows {
        let added_lines: Vec<&str> = lines
            .added
            .get(&path)
            .map(|v| v.iter().map(String::as_str).collect())
            .unwrap_or_default();
        let deleted_lines: Vec<&str> = lines
            .deleted
            .get(&path)
            .map(|v| v.iter().map(String::as_str).collect())
            .unwrap_or_default();
        let kind = kind_of(&path, &added_lines);
        if added == 0 && deleted == 0 {
            out.push(FileRisk {
                path,
                added,
                deleted,
                kind,
                signals: vec!["rename or binary".to_string()],
                score: 0,
                tier: Tier::Cold,
            });
            continue;
        }
        let mut signals = Vec::new();
        let mut score = 0;
        // A file deleted whole is the removed angle's, its callers and siblings, not a guard count.
        let removed_whole = added == 0 && deleted > 0;
        if removed_whole {
            signals.push("file removed".to_string());
        }
        let guards = if removed_whole {
            0
        } else {
            guards_removed(&deleted_lines)
        };
        if guards > 0 {
            signals.push(format!("guard removed x{guards}"));
            score += (guards as u32 * weight::GUARD_REMOVED).min(weight::GUARD_REMOVED_CAP);
        }
        let hits = keywords_in(&added_lines, keywords);
        if !hits.is_empty() {
            signals.push(format!("keyword {}", hits.join(", ")));
            score += (hits.len() as u32 * weight::KEYWORD).min(weight::KEYWORD_CAP);
        }
        if kind == Kind::Code && !tested_dirs.contains(&dir_of(&path)) {
            signals.push("no test touched".to_string());
            score += weight::NO_TEST;
        }
        let fixes = fix_history(repo, head, &path);
        if fixes > 0 {
            signals.push(format!("fix history x{fixes}"));
            score += (fixes as u32 * weight::FIX_HISTORY).min(weight::FIX_HISTORY_CAP);
        }
        let size = added + deleted;
        if size >= 200 {
            signals.push(format!("{size} lines"));
            score += weight::SIZE_200;
        } else if size >= 50 {
            signals.push(format!("{size} lines"));
            score += weight::SIZE_50;
        }
        if prior
            .iter()
            .any(|p| p == &path || path.ends_with(&format!("/{p}")))
        {
            signals.push("prior confirmed".to_string());
            score += weight::PRIOR_CONFIRMED;
        }
        let tier = match kind {
            Kind::Doc | Kind::Generated | Kind::Test => Tier::Cold,
            Kind::Code | Kind::Config => {
                if guards > 0 || score >= weight::HOT {
                    Tier::Hot
                } else {
                    Tier::Warm
                }
            }
        };
        out.push(FileRisk {
            path,
            added,
            deleted,
            kind,
            signals,
            score,
            tier,
        });
    }
    out.sort_by(|a, b| {
        (a.tier, std::cmp::Reverse(a.score), &a.path).cmp(&(
            b.tier,
            std::cmp::Reverse(b.score),
            &b.path,
        ))
    });
    Ok(out)
}

fn dir_of(path: &str) -> String {
    path.rsplit_once('/')
        .map(|(d, _)| d.to_string())
        .unwrap_or_default()
}

/// The table a launch reply pastes: hot first, so a finder reads in this order.
pub fn table(files: &[FileRisk]) -> String {
    let mut rows = vec![
        "| File | +/- | Kind | Signals | Score | Tier |".to_string(),
        "| --- | --- | --- | --- | --- | --- |".to_string(),
    ];
    for f in files {
        rows.push(format!(
            "| {} | +{}/-{} | {} | {} | {} | {} |",
            f.path,
            f.added,
            f.deleted,
            f.kind.name(),
            f.signals.join(", "),
            f.score,
            f.tier.name()
        ));
    }
    rows.push(String::new());
    rows.push(summary(files));
    rows.join("\n") + "\n"
}

pub fn summary(files: &[FileRisk]) -> String {
    let count = |t: Tier| files.iter().filter(|f| f.tier == t).count();
    format!(
        "{} files: {} hot, {} warm, {} cold. Hot first: a finder that runs out leaves a cold file unread and never a hot one.",
        files.len(),
        count(Tier::Hot),
        count(Tier::Warm),
        count(Tier::Cold)
    )
}

/// `{"files": [...], "hot": [...], "warm": [...], "cold": [...]}`.
pub fn to_json(files: &[FileRisk]) -> String {
    use super::json_string as js;
    let items: Vec<String> = files
        .iter()
        .map(|f| {
            let signals: Vec<String> = f.signals.iter().map(|s| format!("\"{}\"", js(s))).collect();
            format!(
                "{{\"path\": \"{}\", \"added\": {}, \"deleted\": {}, \"kind\": \"{}\", \"signals\": [{}], \"score\": {}, \"tier\": \"{}\"}}",
                js(&f.path),
                f.added,
                f.deleted,
                f.kind.name(),
                signals.join(", "),
                f.score,
                f.tier.name()
            )
        })
        .collect();
    let tier = |t: Tier| {
        files
            .iter()
            .filter(|f| f.tier == t)
            .map(|f| format!("\"{}\"", js(&f.path)))
            .collect::<Vec<_>>()
            .join(", ")
    };
    format!(
        "{{\"files\": [{}], \"hot\": [{}], \"warm\": [{}], \"cold\": [{}]}}",
        items.join(", "),
        tier(Tier::Hot),
        tier(Tier::Warm),
        tier(Tier::Cold)
    )
}

pub fn risk(args: &[String]) -> i32 {
    if args.len() < 3 {
        eprintln!("risk needs <repo> <base> <head>\n{USAGE}");
        return 2;
    }
    let (repo, base, head) = (args[0].as_str(), args[1].as_str(), args[2].as_str());
    let opts = match options(&args[2..]) {
        Ok(opts) => opts,
        Err(e) => {
            eprintln!("{e}\n{USAGE}");
            return 2;
        }
    };
    let keywords: Vec<String> = match opts.get("keywords") {
        Some(file) => match fs::read_to_string(file) {
            Ok(text) => text
                .lines()
                .map(str::trim)
                .filter(|l| !l.is_empty() && !l.starts_with('#'))
                .map(String::from)
                .collect(),
            Err(e) => {
                eprintln!("{file}: {e}");
                return 2;
            }
        },
        None => KEYWORDS.iter().map(|k| k.to_string()).collect(),
    };
    let prior = opts
        .get("prior")
        .map(|slug| prior_confirmed(Path::new(slug)))
        .unwrap_or_default();
    let files = match rank(repo, base, head, &keywords, &prior) {
        Ok(files) => files,
        Err(e) => {
            eprintln!("{e}");
            return 2;
        }
    };
    let table = table(&files);
    if let Some(path) = opts.get("json") {
        if let Err(e) = fs::write(path, to_json(&files) + "\n") {
            eprintln!("{path}: {e}");
            return 2;
        }
    }
    match opts.get("out") {
        Some(path) => {
            if let Err(e) = fs::write(path, &table) {
                eprintln!("{path}: {e}");
                return 2;
            }
            println!("{}, table at {path}", summary(&files));
        }
        None => print!("{table}"),
    }
    0
}

#[cfg(test)]
mod tests {
    use super::super::testutil::{git, tmp};
    use super::*;
    use std::path::PathBuf;

    fn write(dir: &Path, rel: &str, content: &str) {
        let path = dir.join(rel);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, content).unwrap();
    }

    /// A repository whose second commit removes a guard and adds a token in a.go, adds a test
    /// beside b.go, rewrites c.go at length, touches a doc, a generated file and a lockfile,
    /// with a fix commit in a.go's history between the two.
    fn fixture(name: &str) -> (PathBuf, String, String) {
        let dir = tmp(name);
        git(&dir, &["init", "-q"]);
        write(&dir, "pkg/a.go", "package pkg\nfunc A(err error) error {\n\tif err != nil {\n\t\treturn err\n\t}\n\treturn nil\n}\n");
        write(&dir, "pkg/b.go", "package pkg\nfunc B() int { return 1 }\n");
        write(&dir, "other/c.go", "package other\nfunc C() {}\n");
        write(&dir, "README.md", "# readme\n");
        write(&dir, "other/d.go", "package other\nfunc D() {}\n");
        write(&dir, "pkg/e.go", "package pkg\nfunc E() {}\n");
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "one"]);
        let base = git(&dir, &["rev-parse", "HEAD"]);
        write(&dir, "pkg/a.go", "package pkg\nfunc A(err error) error {\n\tif err != nil {\n\t\treturn err\n\t}\n\treturn nil\n}\n// fixed\n");
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "fix: crash in A"]);
        write(
            &dir,
            "pkg/a.go",
            "package pkg\nfunc A(err error) error {\n\ttoken := sign(err)\n\treturn token\n}\n",
        );
        write(
            &dir,
            "pkg/b.go",
            "package pkg\nfunc B() int { return 2 }\nfunc B2() int { return 3 }\n",
        );
        write(
            &dir,
            "pkg/b_test.go",
            "package pkg\nfunc TestB(t *testing.T) {}\n",
        );
        let long: String = (0..60).map(|i| format!("func C{i}() {{}}\n")).collect();
        write(&dir, "other/c.go", &format!("package other\n{long}"));
        write(&dir, "README.md", "# readme\nmore\n");
        write(
            &dir,
            "gen/x.pb.go",
            "// Code generated by protoc. DO NOT EDIT.\npackage gen\n",
        );
        write(&dir, "Cargo.lock", "[[package]]\n");
        fs::remove_file(dir.join("other/d.go")).unwrap();
        git(&dir, &["mv", "pkg/e.go", "pkg/e2.go"]);
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "two"]);
        let head = git(&dir, &["rev-parse", "HEAD"]);
        (dir, base, head)
    }

    fn by_path<'a>(files: &'a [FileRisk], path: &str) -> &'a FileRisk {
        files
            .iter()
            .find(|f| f.path == path)
            .unwrap_or_else(|| panic!("{path} not ranked: {files:?}"))
    }

    #[test]
    fn kinds_by_path_and_content() {
        assert_eq!(kind_of("pkg/a.go", &[]), Kind::Code);
        assert_eq!(kind_of("pkg/a_test.go", &[]), Kind::Test);
        assert_eq!(kind_of("tests/x.py", &[]), Kind::Test);
        assert_eq!(kind_of("src/x.spec.ts", &[]), Kind::Test);
        assert_eq!(kind_of("docs/guide.md", &[]), Kind::Doc);
        assert_eq!(kind_of("LICENSE", &[]), Kind::Doc);
        assert_eq!(kind_of("api/x.pb.go", &[]), Kind::Generated);
        assert_eq!(kind_of("go.sum", &[]), Kind::Generated);
        assert_eq!(
            kind_of("gen/x.go", &["// Code generated by x. DO NOT EDIT."]),
            Kind::Generated
        );
        assert_eq!(kind_of(".github/workflows/ci.yml", &[]), Kind::Config);
        assert_eq!(kind_of("Dockerfile", &[]), Kind::Config);
    }

    #[test]
    fn guards_and_keywords() {
        assert_eq!(
            guards_removed(&[
                "\tif err != nil {",
                "\t\treturn err",
                "\tx := 1",
                "mu.Lock()",
                "assertValid(x)"
            ]),
            4
        );
        assert_eq!(guards_removed(&["plain line", "y = 2"]), 0);
        let words: Vec<String> = KEYWORDS.iter().map(|k| k.to_string()).collect();
        assert_eq!(
            keywords_in(&["token := Sign(x)", "authorize()"], &words),
            vec!["token", "sign"],
            "whole words, case folded, authorize is not auth"
        );
    }

    #[test]
    fn ranks_the_fixture() {
        let (dir, base, head) = fixture("risk-rank");
        let words: Vec<String> = KEYWORDS.iter().map(|k| k.to_string()).collect();
        let files = rank(
            &dir.to_string_lossy(),
            &base,
            &head,
            &words,
            &BTreeSet::new(),
        )
        .unwrap();
        let a = by_path(&files, "pkg/a.go");
        assert_eq!(a.tier, Tier::Hot, "{a:?}");
        assert!(
            a.signals.iter().any(|s| s.starts_with("guard removed x")),
            "{a:?}"
        );
        assert!(
            a.signals.iter().any(|s| s == "keyword token, sign"),
            "{a:?}"
        );
        assert!(a.signals.iter().any(|s| s == "fix history x1"), "{a:?}");
        assert!(
            !a.signals.iter().any(|s| s == "no test touched"),
            "b_test.go beside it covers the directory: {a:?}"
        );
        let b = by_path(&files, "pkg/b.go");
        assert_eq!(b.tier, Tier::Warm);
        assert!(b.signals.is_empty(), "{b:?}");
        let c = by_path(&files, "other/c.go");
        assert_eq!(c.tier, Tier::Warm);
        assert!(
            c.signals.contains(&"no test touched".to_string())
                && c.signals.iter().any(|s| s.ends_with(" lines")),
            "{c:?}"
        );
        assert_eq!(by_path(&files, "README.md").tier, Tier::Cold);
        assert_eq!(by_path(&files, "gen/x.pb.go").kind, Kind::Generated);
        assert_eq!(by_path(&files, "Cargo.lock").tier, Tier::Cold);
        assert_eq!(by_path(&files, "pkg/b_test.go").tier, Tier::Cold);
        let d = by_path(&files, "other/d.go");
        assert!(
            d.signals.contains(&"file removed".to_string())
                && !d.signals.iter().any(|s| s.starts_with("guard removed")),
            "{d:?}"
        );
        assert_eq!(
            by_path(&files, "pkg/e2.go").tier,
            Tier::Cold,
            "a pure rename is cold"
        );
        assert_eq!(files[0].path, "pkg/a.go", "hot first");
        assert!(
            table(&files).contains("| pkg/a.go | +2/-4 | code | "),
            "{}",
            table(&files)
        );
        assert!(
            summary(&files).starts_with("9 files: 1 hot, 3 warm, 5 cold."),
            "{}",
            summary(&files)
        );
    }

    #[test]
    fn prior_confirmed_files_score_and_the_command_writes_both_files() {
        let (dir, base, head) = fixture("risk-prior");
        let slug = tmp("risk-slug");
        let round = slug.join("1-abcdef0");
        fs::create_dir_all(&round).unwrap();
        fs::write(round.join("claims.md"), "| 1 | CONFIRMED | Warning | `pkg/b.go:2` | go test | red | |\n| 2 | REFUTED | Nit | other/c.go:1 | ls | | |\n").unwrap();
        let out = slug.join("risk.md");
        let json = slug.join("risk.json");
        let code = risk(&[
            dir.to_string_lossy().into_owned(),
            base.clone(),
            head.clone(),
            "--prior".into(),
            slug.to_string_lossy().into_owned(),
            "--out".into(),
            out.to_string_lossy().into_owned(),
            "--json".into(),
            json.to_string_lossy().into_owned(),
        ]);
        assert_eq!(code, 0);
        let table = fs::read_to_string(&out).unwrap();
        assert!(
            table.contains("| pkg/b.go | +2/-1 | code | prior confirmed | 3 | warm |"),
            "{table}"
        );
        assert!(
            !table.contains(
                "| other/c.go | +61/-1 | code | no test touched, 62 lines, prior confirmed"
            ),
            "a refuted row is not a confirmed one: {table}"
        );
        let json = fs::read_to_string(&json).unwrap();
        assert!(
            json.starts_with("{\"files\": [{\"path\": \"pkg/a.go\""),
            "{json}"
        );
        assert!(json.contains("\"hot\": [\"pkg/a.go\"]"), "{json}");
        assert_eq!(risk(&["x".into()]), 2);
        assert_eq!(risk(&["/nonexistent".into(), "a".into(), "b".into()]), 2);
    }

    #[test]
    fn keywords_file_replaces_the_defaults() {
        let (dir, base, head) = fixture("risk-words");
        let words = tmp("risk-words-file").join("words.txt");
        fs::write(&words, "# one per line\nB2\n").unwrap();
        let out = tmp("risk-words-out").join("risk.md");
        let code = risk(&[
            dir.to_string_lossy().into_owned(),
            base,
            head,
            "--keywords".into(),
            words.to_string_lossy().into_owned(),
            "--out".into(),
            out.to_string_lossy().into_owned(),
        ]);
        assert_eq!(code, 0);
        let table = fs::read_to_string(&out).unwrap();
        assert!(
            table.contains("| pkg/b.go | +2/-1 | code | keyword B2 | 2 | warm |"),
            "{table}"
        );
        assert!(!table.contains("keyword token"), "{table}");
    }
}
