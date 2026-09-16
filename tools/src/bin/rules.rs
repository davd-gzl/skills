// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! The corpus tools: `rules lint` checks rule files against the contract in authoring.md.
use std::process::exit;

const USAGE: &str = "rules lint [--quiet] <files>

Checks rule files against the contract in skills/authoring.md: a frozen clause, a
date or a sha inside a rule, an em-dash or a parenthetical in prose, a dangling
clause, a capability asserted with no command, a pointer at a file or a section
that does not exist, a rule stated in two files, and each file's cost. Nothing
blocks; --quiet drops the health table.";

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let code = match args.first().map(String::as_str) {
        Some("lint") => {
            let mut out = std::io::stdout().lock();
            skills_tools::lint::run(&args[1..], &mut out)
        }
        _ => { eprintln!("{USAGE}"); 2 }
    };
    exit(code)
}
