# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#   python3 -m unittest discover -s skills/scripts/tests
import importlib.util
import io
import json
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('words', pathlib.Path(__file__).resolve().parent.parent / 'words.py')
words = importlib.util.module_from_spec(spec)
spec.loader.exec_module(words)


def context(prompt):
    out = io.StringIO()
    words.hook(io.StringIO(json.dumps({'prompt': prompt})), out)
    return json.loads(out.getvalue())['hookSpecificOutput']['additionalContext'] if out.getvalue() else ''


class Words(unittest.TestCase):
    def test_words_opening_the_message_count_and_nothing_after_them(self):
        vocab = words.vocabulary()
        self.assertEqual(words.lead('p d', vocab), [('p',), ('d',)])
        self.assertEqual(words.lead('pd', vocab), [], 'letters typed together are no word')
        self.assertEqual(words.lead('please p', vocab), [], 'a word past prose is no word')
        self.assertEqual(words.lead('review as ai https://github.com/o/r/pull/5', vocab), [('review', 'as', 'ai')])
        self.assertEqual(words.lead('ok p', vocab), [], 'a vague yes ends the run')
        self.assertEqual(words.lead('p?', vocab), [], 'a question gives no word')

    def test_the_hook_puts_only_the_typed_rows_in_context(self):
        text = context('p d')
        self.assertIn('`p`, `push`', text)
        self.assertIn('`m`, `x`, `d`', text)
        self.assertNotIn('`post`', text)
        self.assertIn('`fix <issue or finding>`', context('fix the flaky test please'), 'a word with its target')
        self.assertEqual(context('please fix it'), '', 'nothing opens the message, nothing is added')


if __name__ == '__main__':
    unittest.main()
