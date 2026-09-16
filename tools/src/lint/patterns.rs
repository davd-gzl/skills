// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! Every regex the lint reads prose with, and one line each on what it catches. The `regex`
//! crate has no lookaround, so where a check needs the characters around a match it reads them
//! by hand: `text::has_sha` and `checks::section_refs`.
use regex::Regex;
use std::sync::LazyLock;

macro_rules! pattern {
    ($(#[$attr:meta])* $name:ident = $pat:expr;) => {
        $(#[$attr])*
        pub static $name: LazyLock<Regex> = LazyLock::new(|| Regex::new($pat).unwrap());
    };
}

pub const EMDASH: char = '—';

// The frozen check.

pattern! {
    /// A clause telling the reader to stop measuring: the clause is the defect, the fact goes
    /// stale silently.
    FROZEN = r"(?i)\b(stop re-deriving|stops? re-?deriving|never re-?derive|no need to (check|verify|re-?run)|do not (re-?check|re-?measure|re-?verify)|already measured, so|settled, so stop)\b";
}

// The environment-claim check: a capability asserted as settled wants the command beside it.

pattern! {
    /// A word naming the environment.
    ENV_NOUN = r"(?i)\b(docker|dockerd|podman|sudo|unshare|namespace|CapEff|CapBnd|/dev/(fuse|kvm)|docker\.sock|rootless|chroot|bwrap|this (container|box|machine|shell)|the box)\b";
}
pattern! {
    /// A word asserting it absolutely.
    ENV_ABSOLUTE = r"(?i)\b(cannot|can never|is dead|never (start|run|work)|no \w+ binary|absent|not permitted|will never|impossible|refused)\b";
}
pattern! {
    /// The command beside the claim, read on the raw line since a code span is blanked on the
    /// clean one.
    ENV_ESCAPE = r"env-check|measure it|run it|check it|`[^`]*`|capability recorded";
}

// The dated check: a rule carries no date, it applies whenever its trigger fires.

pattern! {
    /// A provenance word followed by a date in any of three shapes.
    DATED = r"(?i)\b(stated|measured|verified|as of|since)\s+(on\s+)?(\d{4}-\d{2}-\d{2}|\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4})\b";
}
pattern! {
    /// A bare ISO date.
    ISO_DATE = r"\b20\d{2}-[01]\d-[0-3]\d\b";
}
pattern! {
    /// A clock time.
    CLOCK = r"\b[0-2]?\d:[0-5]\d\s?(am|pm|UTC|utc)?\b";
}

// The dangling check: a clause was stripped and the sentence not repaired.

pattern! {
    /// A provenance word ending a line.
    DANGLE_TAIL = r"(?i)\b(measured|stated|verified|reported)\s*$";
}
pattern! {
    /// Punctuation opening the next line.
    DANGLE_HEAD = r"^\s*[.,;:]($|\s)";
}

// The sha check.

pattern! {
    /// A run of lowercase hex digits; `text::has_sha` reads its length and its neighbours.
    HEX_RUN = r"[0-9a-f]+";
}

// The health row.

pattern! {
    /// A negation, counted per hundred words.
    NEGATION = r"(?i)\b(never|neither|nor|no|not|cannot|none|nothing|nobody)\b";
}

// Cutting a file into prose lines and rule units.

pattern! {
    /// A fence line, which toggles the fenced state.
    FENCE = r"^\s*```";
}
pattern! {
    /// A whole fenced block, removed before a check reads the file as one text.
    FENCE_BLOCK = r"(?ms)^```.*?^```";
}
pattern! {
    /// The front matter at the head of a skill file.
    FRONT_MATTER = r"(?s)^---\n.*?\n---\n";
}
pattern! {
    /// A code span, blanked to two backticks on the clean line.
    INLINE_CODE = r"`[^`]*`";
}
pattern! {
    /// A link target, blanked so its URL is not read as prose.
    LINK_TARGET = r"\]\([^)]*\)";
}
pattern! {
    /// An HTML tag, removed from the clean line.
    HTML_TAG = r"<[^>]{1,60}>";
}
pattern! {
    /// A `<placeholder>`, removed before a sentence is keyed for the duplicate check.
    PLACEHOLDER = r"(?i)<[a-z][a-z0-9 _/-]*>";
}
pattern! {
    /// Where a new rule unit starts: a list item, a numbered item or a blank line.
    UNIT_HEAD = r"^(?:\s*[-*] |\s*\d+\. |\n)";
}
pattern! {
    /// Everything a sentence key drops: anything but lowercase letters, digits and spaces.
    NON_ALNUM = r"[^a-z0-9 ]";
}

// The reference checks: a rule pointing at a file or a section that does not exist reads
// exactly like one pointing at one that does.

pattern! {
    /// A code span naming a rule file or a script by its path.
    FILE_REF = r"`\.?/?((?:skills|scripts|projects)/[A-Za-z0-9_.<>/-]+\.(?:md|py|sh))`";
}
pattern! {
    /// `*Section name*`, alone or followed by `in `file`` or `section of `file``.
    SECTION_REF = r"\*([A-Z][^*\n]{3,60})\*(?:\s+(?:rule|section)?\s*(?:in|of)\s+`([^`]+)`)?";
}
pattern! {
    /// A rule file named in a code span on the same line as a section reference.
    NAMED_FILE = r"`((?:skills|projects)/[A-Za-z0-9_./-]+\.md|AGENTS\.md)`";
}
pattern! {
    /// A markdown heading, whose text is indexed lowercased.
    HEADING = r"(?m)^#+\s+(.+)$";
}

// The parenthetical check.

pattern! {
    /// A numbered marker or a plural `(s)`, which is not a parenthetical.
    PAREN_EXEMPT = r"\(\d\)|\(s\)";
}
