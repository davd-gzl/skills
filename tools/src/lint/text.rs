// NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
//! Cutting a file into what the checks read: the prose lines, the rule units, the sentences.
use super::patterns::*;

/// One line of prose: its number in the file, the raw text, and the text with code spans, link
/// targets and tags blanked, which is what every check reads.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProseLine {
    pub number: usize,
    pub raw: String,
    pub clean: String,
}

/// Every line outside a fenced block, blanked: a rule and its example live in one file, so a
/// check reading the example reports the file's own illustrations and gets switched off.
pub fn prose_lines(text: &str) -> Vec<ProseLine> {
    let mut lines = Vec::new();
    let mut in_fence = false;
    for (i, raw) in text.lines().enumerate() {
        if FENCE.is_match(raw) {
            in_fence = !in_fence;
            continue;
        }
        if in_fence {
            continue;
        }
        let clean = INLINE_CODE.replace_all(raw, "``");
        let clean = LINK_TARGET.replace_all(&clean, "]");
        let clean = HTML_TAG.replace_all(&clean, "");
        lines.push(ProseLine {
            number: i + 1,
            raw: raw.to_string(),
            clean: clean.into_owned(),
        });
    }
    lines
}

pub fn word_count(s: &str) -> usize {
    s.split_whitespace().count()
}

/// The smallest blocks that carry one rule, for the density measure: the text split before every
/// list item, numbered item and blank line, with fences and front matter removed, blocks under
/// twelve words and headings dropped, and whitespace joined.
pub fn rule_units(text: &str) -> Vec<String> {
    let body = FENCE_BLOCK.replace_all(text, "");
    let body = FRONT_MATTER.replace(&body, "");
    let mut blocks = Vec::new();
    let mut start = 0;
    for (i, byte) in body.bytes().enumerate() {
        if byte == b'\n' && UNIT_HEAD.is_match(&body[i + 1..]) {
            blocks.push(&body[start..i]);
            start = i + 1;
        }
    }
    blocks.push(&body[start..]);
    blocks
        .iter()
        .filter(|block| word_count(block) >= 12 && !block.trim_start().starts_with('#'))
        .map(|block| block.split_whitespace().collect::<Vec<_>>().join(" "))
        .collect()
}

/// The line split at every whitespace run that follows a full stop, a bang or a question mark,
/// with pieces under eight words dropped.
pub fn sentences(line: &str) -> Vec<String> {
    let mut parts = Vec::new();
    let mut current = String::new();
    let mut previous: Option<char> = None;
    let mut chars = line.chars().peekable();
    while let Some(c) = chars.next() {
        let ends_sentence = c.is_whitespace() && matches!(previous, Some('.' | '!' | '?'));
        if ends_sentence {
            while chars.peek().map(|d| d.is_whitespace()).unwrap_or(false) {
                chars.next();
            }
            parts.push(std::mem::take(&mut current));
            previous = Some(' ');
            continue;
        }
        current.push(c);
        previous = Some(c);
    }
    parts.push(current);
    parts
        .into_iter()
        .map(|s| s.trim().to_string())
        .filter(|s| word_count(s) >= 8)
        .collect()
}

/// The sentence lowercased, with placeholders and everything but letters, digits and spaces
/// removed: the key two files' wordings of one rule share.
pub fn normalize(sentence: &str) -> String {
    let lower = sentence.to_lowercase();
    let without_placeholders = PLACEHOLDER.replace_all(&lower, "");
    NON_ALNUM
        .replace_all(&without_placeholders, "")
        .trim()
        .to_string()
}

fn is_word(c: char) -> bool {
    c.is_alphanumeric() || c == '_'
}

/// A bare commit: 7 to 40 hex digits with nothing word-like, no slash and no hash before it and
/// nothing word-like after.
pub fn has_sha(s: &str) -> bool {
    HEX_RUN.find_iter(s).any(|m| {
        let length = m.end() - m.start();
        let before = s[..m.start()].chars().next_back();
        let after = s[m.end()..].chars().next();
        let before_ok = !before
            .map(|c| is_word(c) || c == '/' || c == '#')
            .unwrap_or(false);
        let after_ok = !after.map(is_word).unwrap_or(false);
        (7..=40).contains(&length) && before_ok && after_ok
    })
}

/// Half to even, as Python's round.
pub fn round_even(x: f64) -> i64 {
    let halfway = (x - x.trunc()).abs() == 0.5;
    if !halfway {
        return x.round() as i64;
    }
    let truncated = x.trunc() as i64;
    if truncated % 2 == 0 {
        truncated
    } else {
        x.round() as i64
    }
}

/// The median words per rule, half to even, or None under eight rules, where it says nothing.
pub fn median_words(rules: &[String]) -> Option<u64> {
    if rules.len() < 8 {
        return None;
    }
    let mut counts: Vec<usize> = rules.iter().map(|rule| word_count(rule)).collect();
    counts.sort_unstable();
    let mid = counts.len() / 2;
    let median = if counts.len() % 2 == 1 {
        counts[mid] as f64
    } else {
        (counts[mid - 1] + counts[mid]) as f64 / 2.0
    };
    Some(round_even(median) as u64)
}

/// The line number of a byte offset in a text.
pub fn line_of(text: &str, at: usize) -> usize {
    text[..at].matches('\n').count() + 1
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prose_lines_skip_fences_and_blank_code() {
        let lines = prose_lines("a `code` b\n```\nfenced\n```\n[t](http://x) <em>tag</em>\n");
        assert_eq!(lines.len(), 2);
        assert_eq!(
            lines[0],
            ProseLine {
                number: 1,
                raw: "a `code` b".into(),
                clean: "a `` b".into()
            }
        );
        assert_eq!(lines[1].number, 5);
        assert_eq!(lines[1].clean, "[t] tag");
    }

    #[test]
    fn prose_lines_indented_fence_toggles() {
        let lines = prose_lines("x\n   ```\nin\n   ```\ny\n");
        let numbers: Vec<usize> = lines.iter().map(|l| l.number).collect();
        assert_eq!(numbers, vec![1, 5]);
    }

    #[test]
    fn rule_units_split_and_floor() {
        let twelve = "one two three four five six seven eight nine ten eleven twelve";
        let text = format!(
            "---\nname: x\n---\n# Heading {twelve}\n\n- {twelve}\n- short\n1. {twelve} more\n```\n- {twelve} fenced\n```\n{twelve}\n"
        );
        let units = rule_units(&text);
        assert_eq!(units.len(), 3, "{units:?}");
        assert!(units[0].starts_with("- one"));
        assert!(units[1].starts_with("1. one"));
        assert!(units[2].starts_with("one"));
    }

    #[test]
    fn rule_units_join_whitespace() {
        let units = rule_units("- a  b\n  c   d e f g h i j k l m\n");
        assert_eq!(units, vec!["- a b c d e f g h i j k l m"]);
    }

    #[test]
    fn sentences_split_after_stops() {
        let eight = "w1 w2 w3 w4 w5 w6 w7 w8";
        let parts = sentences(&format!(
            "{eight}. {eight}!  {eight}? short one. {eight}, not split here"
        ));
        assert_eq!(parts.len(), 4);
        assert_eq!(parts[0], format!("{eight}."));
        assert_eq!(parts[3], format!("{eight}, not split here"));
    }

    #[test]
    fn sentences_under_eight_words_drop() {
        assert!(sentences("a b c d e f g. h i j k l m n.").is_empty());
    }

    #[test]
    fn normalize_lowers_and_strips() {
        assert_eq!(
            normalize("Run `X` on <the Repo>, Twice!"),
            "run x on  twice"
        );
        assert_eq!(normalize("  A.B  "), "ab");
    }

    #[test]
    fn sha_shapes() {
        assert!(has_sha("at 0123456 here"));
        assert!(has_sha("at 0123456789abcdef0123456789abcdef01234567 end"));
        assert!(!has_sha("at 012345 six"));
        assert!(!has_sha(
            "at 0123456789abcdef0123456789abcdef012345678 forty one"
        ));
        assert!(!has_sha("path/0123456 after a slash"));
        assert!(!has_sha("#0123456 after a hash"));
        assert!(!has_sha("x0123456 after a word char"));
        assert!(!has_sha("0123456x before a word char"));
        assert!(!has_sha("ABCDEF1 upper"));
        assert!(has_sha("(deadbeef)"));
    }

    #[test]
    fn rounding_half_to_even() {
        assert_eq!(round_even(0.5), 0);
        assert_eq!(round_even(1.5), 2);
        assert_eq!(round_even(2.5), 2);
        assert_eq!(round_even(2.4), 2);
        assert_eq!(round_even(2.6), 3);
        assert_eq!(round_even(37.5), 38);
        assert_eq!(round_even(36.5), 36);
    }

    #[test]
    fn median_needs_eight_rules_and_rounds_to_even() {
        let rule = |words: usize| "w ".repeat(words).trim().to_string();
        let seven: Vec<String> = (0..7).map(|_| rule(20)).collect();
        assert_eq!(median_words(&seven), None);
        let eight: Vec<String> = (0..8).map(|i| rule(if i < 4 { 20 } else { 21 })).collect();
        assert_eq!(
            median_words(&eight),
            Some(20),
            "median 20.5 rounds to 20, the even side"
        );
        let nine: Vec<String> = (0..9).map(|i| rule(10 + i)).collect();
        assert_eq!(median_words(&nine), Some(14));
    }

    #[test]
    fn line_numbers_in_bare_text() {
        assert_eq!(line_of("a\nb\nc", 4), 3);
        assert_eq!(line_of("a", 0), 1);
    }
}
