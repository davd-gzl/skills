// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! The deterministic steps of a review round; the logic and its tests live in the library's round module.
fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    std::process::exit(skills_tools::round::dispatch(&args))
}
