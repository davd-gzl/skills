// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! Checks rule files against the contract in authoring.md, the port of the Python lint whose
//! output it reproduces line for line: the golden test under tests/lint holds that output over
//! a fixture corpus exercising every check.
//!
//! Nothing here blocks. Every finding is a warning: a rough rule lands, and a later pass fixes
//! it. A warning answered by raising its threshold is the pollution this lint exists to catch.
//!
//! The pieces, in reading order: `patterns` holds every regex with what it catches; `text` cuts
//! a file into the prose lines, rule units and sentences the checks read; `checks` is one
//! function per check; `file` runs them over one file; `report` prints a run over many.

mod checks;
mod file;
mod patterns;
mod report;
mod text;

use std::collections::{HashMap, HashSet};

pub use checks::DENSITY_CAP;
pub use file::{check_file, classify, index, Kind};
pub use report::run;

/// One thing the lint found in a file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Finding {
    pub level: Level,
    /// The line in the file, 0 for a finding about the whole file.
    pub line: usize,
    /// The short name printed in brackets: `frozen`, `dated`, `xref`.
    pub code: &'static str,
    pub message: String,
}

/// What a finding would be in a lint that blocked. Every finding prints as `warn`; the level
/// records which are the contract's defects and which are leads, and the tests read it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Level {
    Warn,
    Error,
}

/// The health row of one file, what the table at the end of a run prints.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Health {
    pub words: usize,
    /// Rules the file holds, the units `text::rule_units` cuts.
    pub rules: usize,
    /// Median words per rule, or `-` under eight rules.
    pub density: String,
    /// Negations per hundred words, one decimal.
    pub negation: String,
    /// The share of bullets opening bold, a whole percent, or `-` under eight bullets.
    pub bold: String,
}

/// Where a sentence was seen.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Place {
    pub path: String,
    pub line: usize,
}

/// Sentences keyed by their normalised text, in first-seen order, as the Python dict kept them,
/// so ties in the duplicate report sort the same way.
#[derive(Debug, Default)]
pub struct FirstSeen {
    entries: Vec<(String, Vec<Place>)>,
    index: HashMap<String, usize>,
}

impl FirstSeen {
    pub fn push(&mut self, key: &str, place: Place) {
        match self.index.get(key) {
            Some(&i) => self.entries[i].1.push(place),
            None => {
                self.index.insert(key.to_string(), self.entries.len());
                self.entries.push((key.to_string(), vec![place]));
            }
        }
    }

    pub fn iter(&self) -> impl Iterator<Item = (&str, &[Place])> {
        self.entries
            .iter()
            .map(|(key, places)| (key.as_str(), places.as_slice()))
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    pub fn keys(&self) -> Vec<&str> {
        self.entries.iter().map(|(key, _)| key.as_str()).collect()
    }
}

/// Everything `check_file` returns for one file.
#[derive(Debug, Default)]
pub struct FileReport {
    pub findings: Vec<Finding>,
    /// None when the file could not be read.
    pub health: Option<Health>,
    /// The sentences the duplicate check compares across files.
    pub sentences: FirstSeen,
}

/// Every file's text and lowercased headings, so a reference into another file resolves.
#[derive(Debug, Default)]
pub struct Corpus {
    pub texts: HashMap<String, String>,
    pub headings: HashMap<String, HashSet<String>>,
}

impl Corpus {
    /// Whether `file` has a heading that `name` opens, case folded, or a bold label `**name`.
    /// Prefix, since a reference names the section and never its parenthetical.
    pub fn has_heading(&self, file: &str, name: &str) -> bool {
        let wanted = name.to_lowercase();
        let by_heading = self
            .headings
            .get(file)
            .map(|headings| headings.iter().any(|h| h.starts_with(&wanted)))
            .unwrap_or(false);
        let by_label = self
            .texts
            .get(file)
            .map(|text| text.contains(&format!("**{name}")))
            .unwrap_or(false);
        by_heading || by_label
    }
}

/// Files and directories the tests build, and the lock the file checks need.
#[cfg(test)]
pub(crate) mod testutil {
    use std::fs;
    use std::path::{Path, PathBuf};
    use std::sync::Mutex;

    /// A fresh directory under the system temp directory, named for the test.
    pub fn tmp(name: &str) -> PathBuf {
        let dir = std::env::temp_dir()
            .join(format!("skills-tools-lint-{}", std::process::id()))
            .join(name);
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    /// Writes `content` at `rel` under `dir` and returns the path as a string.
    pub fn file(dir: &Path, rel: &str, content: &str) -> String {
        let path = dir.join(rel);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(&path, content).unwrap();
        path.to_string_lossy().into_owned()
    }

    /// The file checks resolve paths against the working directory, so a test that names one
    /// holds this lock while it runs there.
    static CWD: Mutex<()> = Mutex::new(());

    pub fn in_dir<T>(dir: &Path, f: impl FnOnce() -> T) -> T {
        let _guard = CWD.lock().unwrap_or_else(|e| e.into_inner());
        let previous = std::env::current_dir().unwrap();
        std::env::set_current_dir(dir).unwrap();
        let out = f();
        std::env::set_current_dir(previous).unwrap();
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn at(path: &str, line: usize) -> Place {
        Place {
            path: path.into(),
            line,
        }
    }

    #[test]
    fn first_seen_keeps_first_seen_order() {
        let mut seen = FirstSeen::default();
        seen.push("b", at("f", 1));
        seen.push("a", at("f", 2));
        seen.push("b", at("g", 3));
        assert_eq!(seen.keys(), vec!["b", "a"]);
        let (_, places) = seen.iter().next().unwrap();
        assert_eq!(places.len(), 2);
    }

    #[test]
    fn corpus_headings_match_on_prefix_and_bold_labels() {
        let mut corpus = Corpus::default();
        corpus
            .texts
            .insert("a.md".into(), "**Bold label** text".into());
        corpus
            .headings
            .insert("a.md".into(), ["present heading (tail)".to_string()].into());
        assert!(corpus.has_heading("a.md", "Present heading"));
        assert!(corpus.has_heading("a.md", "Bold label"));
        assert!(!corpus.has_heading("a.md", "Missing"));
        assert!(!corpus.has_heading("b.md", "Present heading"));
    }
}
