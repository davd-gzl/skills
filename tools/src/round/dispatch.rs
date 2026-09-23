// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! `round dispatch`: the changed files cut into bundles by category, each with the angles it
//! has material for and the finders it earns, so the count of finders follows the diff: one
//! for a ten-line change, one per angle for a package rewritten, never a fixed number.
use super::risk::{hunks, kind_of, numstat, Kind};
use super::{command, json_string, options, USAGE};
use regex::Regex;
use std::collections::{BTreeMap, HashMap};
use std::fs;
use std::path::Path;
use std::sync::LazyLock;

/// Under this many changed lines a bundle is small: one finder carries every angle it has.
pub const FLOOR: usize = 100;
/// Over this many changed lines a bundle of several files splits, one bundle per file.
pub const CEILING: usize = 400;
/// The added block that gives the refactor angle material, as the review skill states it.
pub const REFACTOR_BLOCK: usize = 20;

/// The angles a finder can carry, in the order the skill lists them.
pub const ANGLES: &[&str] = &[
    "lines", "removed", "claims", "tests", "reach", "refactor", "rollout", "catalog",
];

/// A path whose name says a guarantee may live at boot, in a sweep or in a one-shot job: the
/// rollout angle's material, two versions of the code running at once.
static ROLLOUT: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(migrat|boot|startup|ready|sweep|cron|command|manage|deploy|seed|init|upgrade|install)")
        .unwrap()
});

static COMMENT: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^\s*(//|#|/\*|\*|--)").unwrap());
/// A comment line in a diff keeps its marker and loses its text, as `review-plan.py` blanks it.
static BLANK: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^([-+ ])\s*(//|#|/\*|\*).*$").unwrap());
static DIFF_HEADER: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^diff --git a/(.+?) b/(.+)$").unwrap());

/// What one changed file carries, read once.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct FileFacts {
    path: String,
    kind: Kind,
    added: usize,
    deleted: usize,
    /// Added lines that are comments: the claims angle's material.
    comments: usize,
    /// The longest run of consecutive added lines: the refactor angle's material.
    block_max: usize,
}

impl FileFacts {
    fn lines(&self) -> usize {
        self.added + self.deleted
    }
}

/// One bundle: a category of the diff, the finders it earns and the diff written for it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Bundle {
    pub id: usize,
    pub name: String,
    pub files: Vec<String>,
    pub added: usize,
    pub deleted: usize,
    /// hot, warm, cold from `round risk`, or empty when no risk table was given.
    pub tier: String,
    pub angles: Vec<&'static str>,
    /// Each entry is one finder and the angles it carries: one per angle, or one carrying all.
    pub finders: Vec<Vec<&'static str>>,
    pub diff_file: String,
    pub diff_file_blank: String,
}

/// The longest run of consecutive added lines per file, from one `git diff -U0`.
fn added_blocks(repo: &str, base: &str, head: &str) -> Result<HashMap<String, usize>, String> {
    let diff = command(
        "git",
        &["-C", repo, "diff", "-U0", "--no-color", "-M", base, head],
    )?;
    let diff = String::from_utf8_lossy(&diff);
    let mut best: HashMap<String, usize> = HashMap::new();
    let mut current = String::new();
    let mut run = 0;
    for line in diff.lines() {
        if let Some(caps) = DIFF_HEADER.captures(line) {
            current = caps[2].to_string();
            run = 0;
            continue;
        }
        if line.starts_with('+') && !line.starts_with("+++") {
            run += 1;
            let entry = best.entry(current.clone()).or_default();
            *entry = (*entry).max(run);
        } else {
            run = 0;
        }
    }
    Ok(best)
}

fn facts(repo: &str, base: &str, head: &str) -> Result<Vec<FileFacts>, String> {
    let rows = numstat(repo, base, head)?;
    let lines = hunks(repo, base, head)?;
    let blocks = added_blocks(repo, base, head)?;
    let mut out = Vec::new();
    for (path, added, deleted) in rows {
        let added_lines: Vec<&str> = lines
            .added
            .get(&path)
            .map(|v| v.iter().map(String::as_str).collect())
            .unwrap_or_default();
        let kind = kind_of(&path, &added_lines);
        let comments = added_lines.iter().filter(|l| COMMENT.is_match(l)).count();
        let block_max = blocks.get(&path).copied().unwrap_or(0);
        out.push(FileFacts {
            path,
            kind,
            added,
            deleted,
            comments,
            block_max,
        });
    }
    Ok(out)
}

fn dir_of(path: &str) -> String {
    path.rsplit_once('/')
        .map(|(d, _)| d.to_string())
        .unwrap_or_default()
}

fn parent_of(dir: &str) -> String {
    dir_of(dir)
}

/// Two directories a bundle under the floor may hold together: siblings, or a directory and
/// anything under it, however deep. `by_dir` is a `BTreeMap`, so an ancestor sorts before every
/// descendant and `a` is the ancestor of the pair whenever either is; the reverse arm cannot fire
/// and is not written. Descendant rather than child, since a name may sort between a directory and
/// its own subdirectory: `.` is 0x2E and `/` is 0x2F, so `gno.land` lands between `gno` and `gno/x`.
fn mergeable(a: &str, b: &str) -> bool {
    parent_of(a) == parent_of(b)
        || (!a.is_empty() && b.len() > a.len() && b.starts_with(a) && b[a.len()..].starts_with('/'))
}

/// The longest common directory prefix of a set of paths, for a merged bundle's name.
fn common_dir(dirs: &[String]) -> String {
    let Some(first) = dirs.first() else {
        return String::new();
    };
    let mut parts: Vec<&str> = first.split('/').collect();
    for dir in &dirs[1..] {
        let other: Vec<&str> = dir.split('/').collect();
        let shared = parts
            .iter()
            .zip(other.iter())
            .take_while(|(a, b)| a == b)
            .count();
        parts.truncate(shared);
    }
    parts.join("/")
}

/// The angles a bundle of code has material for. Lines and reach always; the rest on what the
/// files carry; the catalog when the project has one.
fn angles_for(files: &[&FileFacts], catalog: bool) -> Vec<&'static str> {
    let deleted: usize = files.iter().map(|f| f.deleted).sum();
    let comments: usize = files.iter().map(|f| f.comments).sum();
    let tests = files.iter().any(|f| f.kind == Kind::Test);
    let block = files.iter().map(|f| f.block_max).max().unwrap_or(0);
    let rollout = files.iter().any(|f| ROLLOUT.is_match(&f.path));
    let mut out = Vec::new();
    for angle in ANGLES {
        let has = match *angle {
            "lines" | "reach" => true,
            "removed" => deleted > 0,
            "claims" => comments > 0,
            "tests" => tests,
            "refactor" => block >= REFACTOR_BLOCK,
            "rollout" => rollout,
            "catalog" => catalog,
            _ => false,
        };
        if has {
            out.push(*angle);
        }
    }
    out
}

/// One finder carrying every angle under the floor, else one finder per angle.
fn finders_for(angles: &[&'static str], lines: usize) -> Vec<Vec<&'static str>> {
    if angles.is_empty() {
        return Vec::new();
    }
    if lines < FLOOR {
        vec![angles.to_vec()]
    } else {
        angles.iter().map(|a| vec![*a]).collect()
    }
}

/// One unit per code file, each test file riding with the code file its name matches,
/// `a_test.go` with `a.go` and `test_a.py` with `a.py`, else with the first.
fn split_by_code_file<'a>(members: &[&'a FileFacts]) -> Vec<(String, Vec<&'a FileFacts>)> {
    let mut units: Vec<(String, Vec<&'a FileFacts>)> = members
        .iter()
        .filter(|f| f.kind != Kind::Test)
        .map(|f| (f.path.clone(), vec![*f]))
        .collect();
    for f in members.iter().filter(|f| f.kind == Kind::Test) {
        let stem = test_stem(&f.path);
        let at = units
            .iter()
            .position(|(p, _)| test_stem(p) == stem)
            .unwrap_or(0);
        units[at].1.push(f);
    }
    units
}

/// `pkg/a_test.go`, `pkg/test_a.py`, `src/a.spec.ts` and `pkg/a.go` all give `pkg/a`.
fn test_stem(path: &str) -> String {
    let (dir, name) = path.rsplit_once('/').unwrap_or(("", path));
    let base = name.split('.').next().unwrap_or(name);
    let base = base.strip_prefix("test_").unwrap_or(base);
    let base = base
        .strip_suffix("_filetest")
        .or_else(|| base.strip_suffix("_test"))
        .unwrap_or(base);
    if dir.is_empty() {
        base.to_string()
    } else {
        format!("{dir}/{base}")
    }
}

/// The tier of a bundle: the hottest of its files, from the risk table's lists.
fn tier_for(files: &[&FileFacts], risk: &HashMap<String, String>) -> String {
    for want in ["hot", "warm", "cold"] {
        if files
            .iter()
            .any(|f| risk.get(&f.path).map(String::as_str) == Some(want))
        {
            return want.to_string();
        }
    }
    String::new()
}

/// `{"hot": [...], "warm": [...], "cold": [...]}` from `round risk --json`, read without a JSON
/// crate: each list is scanned for its quoted strings.
fn read_risk(path: &str) -> Result<HashMap<String, String>, String> {
    let text = fs::read_to_string(path).map_err(|e| format!("{path}: {e}"))?;
    let mut out = HashMap::new();
    for tier in ["hot", "warm", "cold"] {
        let key = format!("\"{tier}\": [");
        let Some(start) = text.find(&key) else {
            continue;
        };
        let rest = &text[start + key.len()..];
        let Some(end) = rest.find(']') else { continue };
        for item in rest[..end].split(',') {
            let item = item.trim().trim_matches('"');
            if !item.is_empty() {
                out.insert(item.to_string(), tier.to_string());
            }
        }
    }
    Ok(out)
}

/// The bundles of a diff. Code and test files group by directory, small directories merge with
/// a sibling or with anything under them until the floor, a bundle over the ceiling or a hot bundle over the floor splits by
/// code file, each test file beside the code file its name matches; docs and config form one
/// bundle for the claims angle, and the removed angle too where it deletes a line; generated
/// files are skipped and listed.
pub(super) fn bundles(
    files: &[FileFacts],
    risk: &HashMap<String, String>,
    catalog: bool,
) -> (Vec<Bundle>, Vec<String>) {
    let mut by_dir: BTreeMap<String, Vec<&FileFacts>> = BTreeMap::new();
    let mut prose: Vec<&FileFacts> = Vec::new();
    let mut skipped = Vec::new();
    for f in files {
        match f.kind {
            Kind::Generated => skipped.push(f.path.clone()),
            Kind::Doc | Kind::Config => prose.push(f),
            Kind::Code | Kind::Test => by_dir.entry(dir_of(&f.path)).or_default().push(f),
        }
    }
    // Merge: a directory under the floor joins the next one beside it or under it.
    let mut groups: Vec<(Vec<String>, Vec<&FileFacts>)> = Vec::new();
    for (dir, fs_) in by_dir {
        let merge = groups.last().map(|(dirs, members)| {
            let lines: usize = members.iter().map(|f| f.lines()).sum();
            lines < FLOOR
                && dirs.iter().any(|d| mergeable(d, &dir))
        });
        match (merge, groups.last_mut()) {
            (Some(true), Some((dirs, members))) => {
                dirs.push(dir);
                members.extend(fs_);
            }
            _ => groups.push((vec![dir], fs_)),
        }
    }
    // Split: a group over the ceiling with several code files becomes one bundle per code file,
    // and so does a hot group over the floor: two finders of one angle then read different
    // material, disjoint by construction, where a second round over the same bundle re-read it.
    let mut units: Vec<(String, Vec<&FileFacts>)> = Vec::new();
    for (dirs, members) in groups {
        let lines: usize = members.iter().map(|f| f.lines()).sum();
        let code_files = members.iter().filter(|f| f.kind != Kind::Test).count();
        let hot = members
            .iter()
            .any(|f| risk.get(&f.path).map(String::as_str) == Some("hot"));
        if code_files > 1 && (lines > CEILING || (hot && lines >= FLOOR)) {
            units.extend(split_by_code_file(&members));
        } else {
            let name = if dirs.len() == 1 {
                dirs[0].clone()
            } else {
                common_dir(&dirs)
            };
            units.push((
                if name.is_empty() {
                    "root".to_string()
                } else {
                    name
                },
                members,
            ));
        }
    }
    let mut out = Vec::new();
    for (name, members) in units {
        let added: usize = members.iter().map(|f| f.added).sum();
        let deleted: usize = members.iter().map(|f| f.deleted).sum();
        let angles = angles_for(&members, catalog);
        let finders = finders_for(&angles, added + deleted);
        out.push(Bundle {
            id: out.len() + 1,
            name,
            files: members.iter().map(|f| f.path.clone()).collect(),
            added,
            deleted,
            tier: tier_for(&members, risk),
            angles,
            finders,
            diff_file: String::new(),
            diff_file_blank: String::new(),
        });
    }
    if !prose.is_empty() {
        let added: usize = prose.iter().map(|f| f.added).sum();
        let deleted: usize = prose.iter().map(|f| f.deleted).sum();
        // A doc rewrite deletes a sentence its siblings may still hold: removed sweeps for them.
        let angles: Vec<&'static str> = if deleted > 0 { vec!["removed", "claims"] } else { vec!["claims"] };
        out.push(Bundle {
            id: out.len() + 1,
            name: "docs and config".to_string(),
            files: prose.iter().map(|f| f.path.clone()).collect(),
            added,
            deleted,
            tier: tier_for(&prose, risk),
            finders: finders_for(&angles, added + deleted),
            angles,
            diff_file: String::new(),
            diff_file_blank: String::new(),
        });
    }
    // Hot first, so the table reads in the order the finders should run; untiered before cold.
    let rank = |t: &str| match t {
        "hot" => 0,
        "warm" => 1,
        "cold" => 3,
        _ => 2,
    };
    out.sort_by_key(|b| (rank(&b.tier), b.name.clone()));
    for (i, b) in out.iter_mut().enumerate() {
        b.id = i + 1;
    }
    (out, skipped)
}

/// Each bundle's diff with its enclosing functions, and a twin with comment lines blanked, into
/// `dir` as `bundle-<id>.md` and `bundle-<id>-blank.md`.
fn write_diffs(
    repo: &str,
    base: &str,
    head: &str,
    dir: &str,
    bundles: &mut [Bundle],
) -> Result<(), String> {
    fs::create_dir_all(dir).map_err(|e| format!("{dir}: {e}"))?;
    for b in bundles.iter_mut() {
        let mut args = vec![
            "-C",
            repo,
            "diff",
            "-U20",
            "--function-context",
            "--no-color",
            base,
            head,
            "--",
        ];
        args.extend(b.files.iter().map(String::as_str));
        let body = command("git", &args)?;
        let body = String::from_utf8_lossy(&body);
        let header = format!(
            "# {}..{}, bundle {} {}, {} files, +{} -{}\n\n",
            &base[..base.len().min(9)],
            &head[..head.len().min(9)],
            b.id,
            b.name,
            b.files.len(),
            b.added,
            b.deleted
        );
        let plain = Path::new(dir).join(format!("bundle-{}.md", b.id));
        let blank = Path::new(dir).join(format!("bundle-{}-blank.md", b.id));
        fs::write(&plain, format!("{header}```diff\n{body}```\n"))
            .map_err(|e| format!("{}: {e}", plain.display()))?;
        let blanked: Vec<String> = body
            .lines()
            .map(|l| BLANK.replace(l, "$1").into_owned())
            .collect();
        fs::write(
            &blank,
            format!("{header}```diff\n{}\n```\n", blanked.join("\n")),
        )
        .map_err(|e| format!("{}: {e}", blank.display()))?;
        b.diff_file = plain.to_string_lossy().into_owned();
        b.diff_file_blank = blank.to_string_lossy().into_owned();
    }
    Ok(())
}

pub fn table(bundles: &[Bundle], skipped: &[String]) -> String {
    let mut rows = vec![
        "| # | Bundle | Files | +/- | Tier | Angles | Finders |".to_string(),
        "| --- | --- | --- | --- | --- | --- | --- |".to_string(),
    ];
    for b in bundles {
        let finders = if b.finders.len() == 1 && b.finders[0].len() > 1 {
            format!("1, carrying {}", b.finders[0].join(", "))
        } else {
            b.finders.len().to_string()
        };
        rows.push(format!(
            "| {} | {} | {} | +{}/-{} | {} | {} | {} |",
            b.id,
            b.name,
            b.files.len(),
            b.added,
            b.deleted,
            if b.tier.is_empty() { "-" } else { &b.tier },
            b.angles.join(", "),
            finders
        ));
    }
    rows.push(String::new());
    rows.push(summary(bundles, skipped));
    rows.join("\n") + "\n"
}

pub fn summary(bundles: &[Bundle], skipped: &[String]) -> String {
    let finders: usize = bundles.iter().map(|b| b.finders.len()).sum();
    let merged = bundles
        .iter()
        .filter(|b| b.finders.len() == 1 && b.finders[0].len() > 1)
        .count();
    let mut s = format!(
        "{} bundles, {} finders, {} of the bundles small enough for one finder carrying every angle",
        bundles.len(),
        finders,
        merged
    );
    if !skipped.is_empty() {
        s += &format!(
            "; {} generated files skipped: {}",
            skipped.len(),
            skipped.join(", ")
        );
    }
    s + "."
}

pub fn to_json(bundles: &[Bundle], skipped: &[String]) -> String {
    let list = |items: &[&str]| {
        items
            .iter()
            .map(|s| format!("\"{}\"", json_string(s)))
            .collect::<Vec<_>>()
            .join(", ")
    };
    let items: Vec<String> = bundles
        .iter()
        .map(|b| {
            let files: Vec<&str> = b.files.iter().map(String::as_str).collect();
            let finders: Vec<String> = b.finders.iter().map(|g| format!("[{}]", list(g))).collect();
            format!(
                "{{\"id\": {}, \"name\": \"{}\", \"files\": [{}], \"added\": {}, \"deleted\": {}, \"tier\": \"{}\", \"angles\": [{}], \"finders\": [{}], \"diff_file\": \"{}\", \"diff_file_blank\": \"{}\"}}",
                b.id,
                json_string(&b.name),
                list(&files),
                b.added,
                b.deleted,
                json_string(&b.tier),
                list(&b.angles),
                finders.join(", "),
                json_string(&b.diff_file),
                json_string(&b.diff_file_blank)
            )
        })
        .collect();
    let skipped_refs: Vec<&str> = skipped.iter().map(String::as_str).collect();
    let finders: usize = bundles.iter().map(|b| b.finders.len()).sum();
    format!(
        "{{\"bundles\": [{}], \"skipped\": [{}], \"finders\": {}}}",
        items.join(", "),
        list(&skipped_refs),
        finders
    )
}

pub fn dispatch_cmd(args: &[String]) -> i32 {
    if args.len() < 3 {
        eprintln!("dispatch needs <repo> <base> <head>\n{USAGE}");
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
    let risk = match opts.get("risk") {
        Some(path) => match read_risk(path) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("{e}");
                return 2;
            }
        },
        None => HashMap::new(),
    };
    let catalog = opts
        .get("catalog")
        .map(|v| v != "0" && v != "false")
        .unwrap_or(false);
    let files = match facts(repo, base, head) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("{e}");
            return 2;
        }
    };
    let (mut bundles, skipped) = bundles(&files, &risk, catalog);
    if let Some(dir) = opts.get("diff-dir") {
        if let Err(e) = write_diffs(repo, base, head, dir, &mut bundles) {
            eprintln!("{e}");
            return 2;
        }
    }
    if let Some(path) = opts.get("json") {
        if let Err(e) = fs::write(path, to_json(&bundles, &skipped) + "\n") {
            eprintln!("{path}: {e}");
            return 2;
        }
    }
    let table = table(&bundles, &skipped);
    match opts.get("out") {
        Some(path) => {
            if let Err(e) = fs::write(path, &table) {
                eprintln!("{path}: {e}");
                return 2;
            }
            println!("{}, table at {path}", summary(&bundles, &skipped));
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

    fn lines(n: usize, prefix: &str) -> String {
        (0..n).map(|i| format!("{prefix}{i}\n")).collect()
    }

    /// A diff with one large package carrying a comment, a deletion and a test; two tiny sibling
    /// packages; two huge files in one directory; a doc; a generated file.
    fn fixture(name: &str) -> (PathBuf, String, String) {
        let dir = tmp(name);
        git(&dir, &["init", "-q"]);
        write(
            &dir,
            "pkg/a/a.go",
            &format!("package a\n{}", lines(10, "var old")),
        );
        write(&dir, "pkg/b/b.go", "package b\n");
        write(&dir, "pkg/c/c.go", "package c\n");
        write(&dir, "keep.go", "package keep\n");
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "one"]);
        let base = git(&dir, &["rev-parse", "HEAD"]);
        write(
            &dir,
            "pkg/a/a.go",
            &format!(
                "package a\n// a comment on the change\n{}",
                lines(120, "func A")
            ),
        );
        write(
            &dir,
            "pkg/a/a_test.go",
            "package a\nfunc TestA(t *testing.T) {}\n",
        );
        write(&dir, "pkg/b/b.go", "package b\nfunc B() {}\nfunc B2() {}\n");
        write(
            &dir,
            "pkg/c/c.go",
            "package c\nfunc C() {}\nfunc C2() {}\nfunc C3() {}\n",
        );
        write(
            &dir,
            "big/one.go",
            &format!("package big\n{}", lines(250, "func One")),
        );
        write(
            &dir,
            "big/two.go",
            &format!("package big\n{}", lines(250, "func Two")),
        );
        write(&dir, "docs/guide.md", "# guide\nmore\n");
        write(
            &dir,
            "gen/x.pb.go",
            "// Code generated by protoc. DO NOT EDIT.\npackage gen\n",
        );
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "two"]);
        let head = git(&dir, &["rev-parse", "HEAD"]);
        (dir, base, head)
    }

    fn named<'a>(bundles: &'a [Bundle], name: &str) -> &'a Bundle {
        bundles.iter().find(|b| b.name == name).unwrap_or_else(|| {
            panic!(
                "no bundle {name}: {:?}",
                bundles.iter().map(|b| &b.name).collect::<Vec<_>>()
            )
        })
    }

    #[test]
    fn angles_follow_the_material_and_finders_follow_the_size() {
        let big = FileFacts {
            path: "p/a.go".into(),
            kind: Kind::Code,
            added: 60,
            deleted: 10,
            comments: 1,
            block_max: 60,
        };
        let test = FileFacts {
            path: "p/a_test.go".into(),
            kind: Kind::Test,
            added: 2,
            deleted: 0,
            comments: 0,
            block_max: 2,
        };
        let angles = angles_for(&[&big, &test], true);
        assert_eq!(
            angles,
            vec!["lines", "removed", "claims", "tests", "reach", "refactor", "catalog"]
        );
        assert_eq!(
            finders_for(&angles, 172).len(),
            7,
            "one finder per angle over the floor"
        );
        assert_eq!(
            finders_for(&angles, 72).len(),
            1,
            "one finder carrying all seven under the floor"
        );
        let tiny = FileFacts {
            path: "p/b.go".into(),
            kind: Kind::Code,
            added: 3,
            deleted: 0,
            comments: 0,
            block_max: 3,
        };
        let angles = angles_for(&[&tiny], false);
        assert_eq!(angles, vec!["lines", "reach"]);
        assert_eq!(
            finders_for(&angles, 3),
            vec![vec!["lines", "reach"]],
            "one finder carrying both under the floor"
        );
        assert!(finders_for(&[], 3).is_empty());
    }

    fn fact(path: &str, kind: Kind, added: usize) -> FileFacts {
        FileFacts { path: path.to_string(), kind, added, deleted: 0, comments: 0, block_max: 0 }
    }

    #[test]
    fn a_hot_bundle_over_the_floor_splits_by_code_file() {
        let files = vec![
            fact("pkg/x.go", Kind::Code, 80),
            fact("pkg/y.go", Kind::Code, 60),
            fact("pkg/y_test.go", Kind::Test, 10),
        ];
        let (cold, _) = bundles(&files, &HashMap::new(), false);
        assert_eq!(cold.len(), 1, "under the ceiling and not hot, one bundle: {cold:?}");
        assert_eq!(cold[0].files, vec!["pkg/x.go", "pkg/y.go", "pkg/y_test.go"]);
        let risk = HashMap::from([("pkg/x.go".to_string(), "hot".to_string())]);
        let (hot, _) = bundles(&files, &risk, false);
        assert_eq!(hot.len(), 2, "{hot:?}");
        assert_eq!(hot[0].files, vec!["pkg/x.go"]);
        assert_eq!(hot[1].files, vec!["pkg/y.go", "pkg/y_test.go"], "the test rides with its code file");
        assert_eq!(hot[0].tier, "hot");
        assert_eq!(test_stem("pkg/test_a.py"), "pkg/a");
        assert_eq!(test_stem("src/a.spec.ts"), "src/a");
        assert_eq!(test_stem("r/x/x_filetest.gno"), "r/x/x");
    }

    #[test]
    fn bundles_merge_split_and_skip() {
        let (dir, base, head) = fixture("dispatch");
        let files = facts(&dir.to_string_lossy(), &base, &head).unwrap();
        let (bundles, skipped) = bundles(&files, &HashMap::new(), false);
        assert_eq!(skipped, vec!["gen/x.pb.go"]);
        let a = named(&bundles, "pkg/a");
        assert_eq!(a.files, vec!["pkg/a/a.go", "pkg/a/a_test.go"]);
        assert_eq!(
            a.angles,
            vec!["lines", "removed", "claims", "tests", "reach", "refactor"],
            "{a:?}"
        );
        assert_eq!(a.finders.len(), 6);
        let bc = named(&bundles, "pkg");
        assert_eq!(
            bc.files,
            vec!["pkg/b/b.go", "pkg/c/c.go"],
            "two tiny siblings merge under their parent"
        );
        assert_eq!(
            bc.finders,
            vec![vec!["lines", "reach"]],
            "and earn one finder carrying both angles"
        );
        assert_eq!(
            named(&bundles, "big/one.go").files,
            vec!["big/one.go"],
            "a directory over the ceiling splits by file"
        );
        assert_eq!(
            named(&bundles, "big/two.go").angles,
            vec!["lines", "reach", "refactor"]
        );
        let docs = named(&bundles, "docs and config");
        assert_eq!(docs.files, vec!["docs/guide.md"]);
        assert_eq!(docs.finders, vec![vec!["claims"]]);
        let total: usize = bundles.iter().map(|b| b.finders.len()).sum();
        assert_eq!(total, 6 + 1 + 3 + 3 + 1, "{}", table(&bundles, &skipped));
        assert!(
            summary(&bundles, &skipped)
                .starts_with("5 bundles, 14 finders, 1 of the bundles small enough"),
            "{}",
            summary(&bundles, &skipped)
        );
    }

    #[test]
    fn a_directory_merges_into_its_own_parent_under_the_floor() {
        let dir = tmp("dispatch-child");
        git(&dir, &["init", "-q"]);
        write(&dir, "web/components/layout_test.go", "package components\n");
        write(&dir, "web/components/layouts/head.html", "<head></head>\n");
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "one"]);
        let base = git(&dir, &["rev-parse", "HEAD"]);
        write(
            &dir,
            "web/components/layout_test.go",
            "package components\nfunc TestHead(t *testing.T) {}\n",
        );
        write(
            &dir,
            "web/components/layouts/head.html",
            "<head>\n<title>x</title>\n</head>\n",
        );
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "two"]);
        let head = git(&dir, &["rev-parse", "HEAD"]);
        let files = facts(&dir.to_string_lossy(), &base, &head).unwrap();
        let (bundles, _) = bundles(&files, &HashMap::new(), false);
        assert_eq!(
            bundles.len(),
            1,
            "a template and the test asserting it are one bundle, not two: {:?}",
            bundles.iter().map(|b| &b.name).collect::<Vec<_>>()
        );
        assert_eq!(bundles[0].files.len(), 2, "{:?}", bundles[0].files);
    }

    #[test]
    fn a_name_sorting_between_a_directory_and_its_child_does_not_split_them() {
        // `.` is 0x2E and `/` is 0x2F, so `gno.land` sorts between `gno` and `gno/x`. Matching only
        // the group's last directory left `gno/x` its own bundle with a finder of its own.
        let dir = tmp("dispatch-dotsort");
        git(&dir, &["init", "-q"]);
        for path in ["gno/a.go", "gno.land/b.go", "gno/x/c.go"] {
            write(&dir, path, "package p\n");
        }
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "one"]);
        let base = git(&dir, &["rev-parse", "HEAD"]);
        for path in ["gno/a.go", "gno.land/b.go", "gno/x/c.go"] {
            write(&dir, path, "package p\nfunc F() {}\n");
        }
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "two"]);
        let head = git(&dir, &["rev-parse", "HEAD"]);
        let files = facts(&dir.to_string_lossy(), &base, &head).unwrap();
        let (bundles, _) = bundles(&files, &HashMap::new(), false);
        assert_eq!(
            bundles.len(),
            1,
            "three directories under the floor are one bundle: {:?}",
            bundles.iter().map(|b| &b.name).collect::<Vec<_>>()
        );
    }

    #[test]
    fn a_grandchild_directory_merges_into_its_ancestor_under_the_floor() {
        let dir = tmp("dispatch-grandchild");
        git(&dir, &["init", "-q"]);
        for path in ["web/a.go", "web/deep/nested/b.go"] {
            write(&dir, path, "package p\n");
        }
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "one"]);
        let base = git(&dir, &["rev-parse", "HEAD"]);
        for path in ["web/a.go", "web/deep/nested/b.go"] {
            write(&dir, path, "package p\nfunc F() {}\n");
        }
        git(&dir, &["add", "."]);
        git(&dir, &["commit", "-qm", "two"]);
        let head = git(&dir, &["rev-parse", "HEAD"]);
        let files = facts(&dir.to_string_lossy(), &base, &head).unwrap();
        let (bundles, _) = bundles(&files, &HashMap::new(), false);
        assert_eq!(
            bundles.len(),
            1,
            "a directory two levels down still joins its ancestor: {:?}",
            bundles.iter().map(|b| &b.name).collect::<Vec<_>>()
        );
    }

    #[test]
    fn tiers_come_from_the_risk_table_and_diffs_are_written() {
        let (dir, base, head) = fixture("dispatch-run");
        let out = tmp("dispatch-out");
        let risk = out.join("risk.json");
        fs::write(&risk, "{\"files\": [], \"hot\": [\"pkg/a/a.go\"], \"warm\": [\"big/one.go\"], \"cold\": [\"docs/guide.md\"]}\n").unwrap();
        let diffs = out.join("diffs");
        let json = out.join("bundles.json");
        let table_path = out.join("bundles.md");
        let code = dispatch_cmd(&[
            dir.to_string_lossy().into_owned(),
            base.clone(),
            head.clone(),
            "--risk".into(),
            risk.to_string_lossy().into_owned(),
            "--diff-dir".into(),
            diffs.to_string_lossy().into_owned(),
            "--json".into(),
            json.to_string_lossy().into_owned(),
            "--out".into(),
            table_path.to_string_lossy().into_owned(),
        ]);
        assert_eq!(code, 0);
        let table = fs::read_to_string(&table_path).unwrap();
        assert!(table.contains("| 1 | pkg/a | 2 | +123/-10 | hot | lines, removed, claims, tests, reach, refactor | 6 |"), "{table}");
        assert!(
            table.contains("| pkg | 2 | +5/-0 | - | lines, reach | 1, carrying lines, reach |"),
            "{table}"
        );
        let json = fs::read_to_string(&json).unwrap();
        assert!(
            json.starts_with("{\"bundles\": [{\"id\": 1, \"name\": \"pkg/a\", \"files\": [\"pkg/a/a.go\", \"pkg/a/a_test.go\"], \"added\": 123, \"deleted\": 10, \"tier\": \"hot\""),
            "{json}"
        );
        assert!(
            json.contains("\"finders\": [[\"lines\", \"reach\"]]"),
            "{json}"
        );
        assert!(
            json.ends_with("\"skipped\": [\"gen/x.pb.go\"], \"finders\": 14}\n"),
            "{json}"
        );
        let plain = fs::read_to_string(diffs.join("bundle-1.md")).unwrap();
        assert!(
            plain.starts_with(&format!(
                "# {}..{}, bundle 1 pkg/a, 2 files, +123 -10\n\n```diff\n",
                &base[..9],
                &head[..9]
            )),
            "{plain}"
        );
        assert!(plain.contains("+// a comment on the change"));
        let blank = fs::read_to_string(diffs.join("bundle-1-blank.md")).unwrap();
        assert!(
            blank.contains("\n+\n") && !blank.contains("a comment on the change"),
            "the twin blanks the comment line: {blank}"
        );
        assert_eq!(dispatch_cmd(&["x".into()]), 2);
        assert_eq!(
            dispatch_cmd(&["/nonexistent".into(), "a".into(), "b".into()]),
            2
        );
    }

    #[test]
    fn risk_lists_are_read_without_a_json_crate() {
        let dir = tmp("dispatch-risk");
        let path = dir.join("risk.json");
        fs::write(&path, "{\"files\": [{\"path\": \"x\"}], \"hot\": [\"a.go\", \"b/c.go\"], \"warm\": [], \"cold\": [\"d.md\"]}").unwrap();
        let risk = read_risk(&path.to_string_lossy()).unwrap();
        assert_eq!(risk.get("a.go").map(String::as_str), Some("hot"));
        assert_eq!(risk.get("b/c.go").map(String::as_str), Some("hot"));
        assert_eq!(risk.get("d.md").map(String::as_str), Some("cold"));
        assert_eq!(risk.len(), 3);
        assert!(read_risk("/nonexistent/risk.json").is_err());
    }

    #[test]
    fn a_docs_bundle_that_deletes_a_line_carries_the_removed_angle() {
        let mut rewrite = fact("docs/a.md", Kind::Doc, 3);
        rewrite.deleted = 3;
        let (b, _) = bundles(&[rewrite, fact("docs/b.md", Kind::Doc, 2)], &HashMap::new(), false);
        assert_eq!(b[0].angles, vec!["removed", "claims"], "{b:?}");
        assert_eq!(b[0].finders, vec![vec!["removed", "claims"]], "under the floor one finder carries both");
        let (b, _) = bundles(&[fact("docs/c.md", Kind::Doc, 2)], &HashMap::new(), false);
        assert_eq!(b[0].angles, vec!["claims"], "an added-only doc has nothing removed");
    }

    #[test]
    fn common_dir_of_siblings() {
        assert_eq!(common_dir(&["pkg/b".into(), "pkg/c".into()]), "pkg");
        assert_eq!(
            common_dir(&["a/b/c".into(), "a/b/d".into(), "a/b/e/f".into()]),
            "a/b"
        );
        assert_eq!(common_dir(&["x".into(), "y".into()]), "");
    }
}
