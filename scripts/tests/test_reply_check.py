# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
# Behaviour of scripts/reply-check.py: what counts as prose, the numbers that
# mark a drift, the final reply read off a transcript, and the exemptions.
#
#   python3 -m unittest discover -s skills/scripts/tests

import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / 'reply-check.py'
spec = importlib.util.spec_from_file_location('reply_check', SCRIPT)
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

DRIFTED = ("On bypassable: you are right, and escaping the description does not fix it. "
           "The forged heading and rule die. The forged line does not: the renderer preserves inline "
           "links by design, so a description can still print a line that reads exactly like the page's. "
           "The cost is real and the fix is not. What holds is position, not appearance: the page's "
           "section is the one the realm emits, and it is the last thing before the tally.")
CLIPPED = ("Drift. Rule already says it: Short form, every reply, no drift back to prose as session runs. "
           "Long session, I stopped checking it. No new rule needed, one that exists covers it. "
           "Back to register from here. Next: lint, tests, then push waits on its word.")


def entry(kind, content, **extra):
    e = {'type': kind, 'message': {'content': content}, 'timestamp': '2026-09-09T10:00:00Z'}
    e.update(extra)
    return json.dumps(e)


class Prose(unittest.TestCase):
    def test_code_quotes_tables_and_rules_are_not_the_reply(self):
        text = ("Body pushed.\n```\nthe the the the\n```\n> the quoted the draft\n| the | the |\n"
                "---\nthe draft between the rules the\n---\n`the the` done.")
        self.assertEqual(rc.prose(text).split(), ['Body', 'pushed.', 'done.'])

    def test_link_targets_do_not_count(self):
        self.assertNotIn('github', rc.prose('[r1](https://github.com/the/the) on the switch'))


class Measure(unittest.TestCase):
    def test_a_drifted_reply_is_named(self):
        m = rc.measure(DRIFTED)
        self.assertGreater(m['articles'], rc.ARTICLES)
        self.assertTrue(m['reasons'])

    def test_a_clipped_reply_passes(self):
        m = rc.measure(CLIPPED)
        self.assertGreaterEqual(m['words'], rc.MIN_WORDS)
        self.assertEqual(m['reasons'], [])

    def test_a_hedge_is_named(self):
        m = rc.measure(CLIPPED + ' I think keep them, since they cost three lines and carry skim.')
        self.assertTrue(any(r.startswith('hedge') for r in m['reasons']))

    def test_a_closing_block_needs_the_did_account(self):
        tail = '\n\n📋 [file](https://x)\n\nTL;DR: done.'
        self.assertIn('a closing block with no Did: account above it', rc.measure(CLIPPED + tail)['reasons'])
        self.assertEqual(rc.measure(CLIPPED + '\n\n---\n\nDid:\n1. Lint, clean.' + tail)['reasons'], [])
        self.assertEqual(rc.measure(CLIPPED)['reasons'], [])

    def test_a_fenced_account_is_named(self):
        m = rc.measure(CLIPPED + '\n\n```\nDid:\n1. Lint, clean.\n```\n\n📋 [file](https://x)')
        self.assertIn('the Did: account sits in a code fence, write it as plain lines', m['reasons'])
        self.assertNotIn('a closing block with no Did: account above it', m['reasons'])

    def test_a_long_reply_is_named_and_the_account_does_not_count(self):
        long = ' '.join([CLIPPED] * 5)
        self.assertTrue(any(r.startswith(f'{rc.measure(long)["words"]} prose words') for r in rc.measure(long)['reasons']))
        account = '---\n\nDid:\n' + '\n'.join(f'{i}. Step {i}, ' + ' '.join(['done'] * 40) + '.' for i in range(1, 6))
        m = rc.measure(CLIPPED + '\n\n' + account + '\n\n📋 [file](https://x)')
        self.assertEqual(m['reasons'], [])

    def test_a_short_reply_is_not_measured(self):
        self.assertEqual(rc.measure('The fix is in the tree, the tests are green.')['reasons'], [])


class Transcript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 't.jsonl')

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *lines):
        pathlib.Path(self.path).write_text('\n'.join(lines) + '\n')

    def test_the_final_reply_is_the_text_after_the_last_tool_result(self):
        self.write(entry('user', 'do the thing'),
                   entry('assistant', [{'type': 'text', 'text': 'Reading first.'}]),
                   entry('assistant', [{'type': 'tool_use', 'name': 'Bash'}]),
                   entry('user', [{'type': 'tool_result', 'content': 'ok'}]),
                   entry('assistant', [{'type': 'thinking', 'thinking': 'x'}]),
                   entry('assistant', [{'type': 'text', 'text': 'Done.'}]),
                   entry('assistant', [{'type': 'text', 'text': 'Push waits.'}]))
        text, prompt = rc.final_reply(self.path)
        self.assertEqual(text, 'Done.\n\nPush waits.')
        self.assertEqual(prompt, 'do the thing')

    def test_a_turn_ending_on_a_tool_call_has_no_reply(self):
        self.write(entry('user', 'go'), entry('assistant', [{'type': 'tool_use', 'name': 'Bash'}]))
        self.assertEqual(rc.final_reply(self.path), ('', ''))

    def test_a_sidechain_is_not_the_reply(self):
        self.write(entry('user', 'go'),
                   entry('assistant', [{'type': 'text', 'text': 'Done.'}]),
                   entry('assistant', [{'type': 'text', 'text': DRIFTED}], isSidechain=True))
        self.assertEqual(rc.final_reply(self.path)[0], 'Done.')

    def test_replies_pairs_each_with_its_prompt(self):
        self.write(entry('user', 'one'), entry('assistant', [{'type': 'text', 'text': 'A.'}]),
                   entry('user', 'two +'), entry('assistant', [{'type': 'text', 'text': 'B.'}]))
        self.assertEqual([(t, p) for t, p, _ in rc.replies(self.path)], [('A.', 'one'), ('B.', 'two +')])


class Hook(Transcript):
    def run_hook(self, payload):
        err = io.StringIO()
        code = rc.main([], stdin=io.StringIO(json.dumps(payload)), stderr=err)
        return code, err.getvalue()

    def test_a_drifted_reply_blocks_once_with_the_numbers(self):
        self.write(entry('user', 'why'), entry('assistant', [{'type': 'text', 'text': DRIFTED}]))
        code, err = self.run_hook({'transcript_path': self.path, 'stop_hook_active': False})
        self.assertEqual(code, 2)
        self.assertIn('articles per 100', err)
        self.assertIn('cvm', err)
        code, _ = self.run_hook({'transcript_path': self.path, 'stop_hook_active': True})
        self.assertEqual(code, 0)

    def test_a_plus_prompt_exempts_the_reply(self):
        self.write(entry('user', '+ why'), entry('assistant', [{'type': 'text', 'text': DRIFTED}]))
        self.assertEqual(self.run_hook({'transcript_path': self.path})[0], 0)

    def test_a_clipped_reply_passes(self):
        self.write(entry('user', 'why'), entry('assistant', [{'type': 'text', 'text': CLIPPED}]))
        self.assertEqual(self.run_hook({'transcript_path': self.path})[0], 0)

    def test_last_steps_over_the_prompt_just_typed(self):
        self.write(entry('user', 'why'), entry('assistant', [{'type': 'text', 'text': DRIFTED}]),
                   entry('user', 'next question'))
        out = io.StringIO()
        self.assertEqual(rc.main(['--last', self.path], stdout=out), 0)
        self.assertIn('articles per 100', out.getvalue())
        self.write(entry('user', 'why'), entry('assistant', [{'type': 'text', 'text': CLIPPED}]),
                   entry('user', 'next question'))
        out = io.StringIO()
        rc.main(['--last', self.path], stdout=out)
        self.assertEqual(out.getvalue(), '')

    def test_a_missing_transcript_never_blocks(self):
        self.assertEqual(self.run_hook({'transcript_path': '/nonexistent/t.jsonl'})[0], 0)
        self.assertEqual(rc.main([], stdin=io.StringIO('not json'), stderr=io.StringIO()), 0)


if __name__ == '__main__':
    unittest.main()


class Unlinked(unittest.TestCase):
    def test_named_path_with_no_link_is_a_reason(self):
        m = rc.measure("Rule sits in `skills/review.md`, step 4. Done.")
        self.assertEqual(m['unlinked'], ['skills/review.md'])
        self.assertTrue(any(r.startswith('named with no link') for r in m['reasons']))

    def test_linked_path_passes(self):
        m = rc.measure("Rule sits in `skills/review.md`.\n\n[review.md](https://github.com/davd-gzl/skills/blob/main/review.md)")
        self.assertEqual(m['unlinked'], [])

    def test_urls_and_fences_are_not_paths(self):
        m = rc.measure("See https://github.com/x/y/blob/main/a.md and\n```\ncat skills/x.md\n```\n")
        self.assertEqual(m['unlinked'], [])
