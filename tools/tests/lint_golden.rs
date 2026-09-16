// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! The port reproduces the Python lint's output over a fixture corpus that exercises every check.
//! tests/lint/expected*.txt were written by that lint; a difference here is a lost capability.
use std::fs;
use std::path::PathBuf;

#[test]
fn lint_matches_the_golden_output() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/lint");
    std::env::set_current_dir(root.join("corpus")).unwrap();
    let args: Vec<String> = fs::read_to_string(root.join("args.txt")).unwrap().split_whitespace().map(String::from).collect();
    for (extra, expected) in [(None, "expected.txt"), (Some("--quiet"), "expected-quiet.txt")] {
        let mut all: Vec<String> = extra.map(|e| vec![e.to_string()]).unwrap_or_default();
        all.extend(args.iter().cloned());
        let mut out = Vec::new();
        assert_eq!(skills_tools::lint::run(&all, &mut out), 0);
        let got = String::from_utf8(out).unwrap();
        let want = fs::read_to_string(root.join(expected)).unwrap();
        if got != want {
            for (i, (g, w)) in got.lines().zip(want.lines()).enumerate() {
                if g != w { eprintln!("{expected} line {}:\n  got  {g}\n  want {w}", i + 1) }
            }
            eprintln!("got {} lines, want {}", got.lines().count(), want.lines().count());
            panic!("{expected} differs from the port's output");
        }
    }
}
