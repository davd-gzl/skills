#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
"""scripts/rule-growth.py in a scratch repository: a commit adding words to the rule files is refused
unless its message carries a real `Grows:` line, measured against HEAD, an amend included;
a merge passes; pre-push refuses a grown commit no remote holds and leaves the rest alone."""
import os
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / 'rule-growth.py'
_l = SourceFileLoader('rule_growth', str(SCRIPT))
rg = module_from_spec(spec_from_loader('rule_growth', _l)); _l.exec_module(rg)
ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x',
       'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x', 'GIT_CONFIG_GLOBAL': os.devnull}
YES = 'Grows: the user asked for the new skill'


class Answer(unittest.TestCase):
    def test_a_reason_counts_and_a_placeholder_does_not(self):
        for message in (f'subject\n\n{YES}', 'x\n\nGrows: the new `<details>` rule has no older twin',
                        'x\n\nGrows: <= 3 retries need a rule here'):
            self.assertTrue(rg.answered(message), message)
        for message in ('subject', 'x\n\nGrows: <why it may grow>', 'x\n\nGrows: <why>', 'x\n\nGrows: ---',
                        'x\n\nGrows:', 'x\n\nGrows: none', 'x\n\nGrows: yes.', 'x\n\nGrows: yes ok',
                        'x\n\nGrows: <why', 'x\n\nGrows: `<why  it may grow>`', 'x\n\nGrows: why',
                        'x\n\ngrow\x0cGrows: because the user said so', 'x\n\nGrows: <why it may'):
            self.assertFalse(rg.answered(message), message)

    def test_the_diff_below_the_scissors_is_no_part_of_the_message(self):
        for lead in ('# ', '// ', ';'):
            self.assertEqual(rg.message_text(f'subject\n{lead}{rg.SCISSORS}\n {YES}\n'), 'subject', lead)


class Hooks(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        (self.repo / '.hooks').mkdir()
        (self.repo / '.hooks' / 'commit-msg').write_text(f'#!/bin/sh\nexec {SCRIPT} commit-msg "$1"\n')
        (self.repo / '.hooks' / 'commit-msg').chmod(0o755)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'core.hooksPath', '.hooks')
        self.write('rule.md', 'one two three four')
        self.assertEqual(self.commit(f'first\n\n{YES}').returncode, 0)

    def git(self, *args, **env):
        return subprocess.run(['git', '-C', str(self.repo), *args], env={**ENV, **env}, capture_output=True, text=True)

    def write(self, path, text):
        (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / path).write_text(text + '\n')
        self.git('add', path)

    def commit(self, message, *flags):
        return self.git('commit', '-q', *flags, '-m', message)

    def head(self):
        return self.git('rev-parse', 'HEAD').stdout.strip()

    def push(self, local, remote='0' * 40):
        return subprocess.run([str(SCRIPT), 'pre-push'], cwd=self.repo, env=ENV, capture_output=True, text=True,
                              input=f'refs/heads/main {local} refs/heads/main {remote}\n')

    def test_growth_is_refused_until_the_message_says_why(self):
        self.write('rule.md', 'one two three four five')
        r = self.commit('grow')
        self.assertEqual(r.returncode, 1)
        self.assertIn('rule.md +1', r.stderr)
        self.assertEqual(self.commit(f'grow\n\n{YES}').returncode, 0)

    def test_other_files_shrinks_and_moves_pass(self):
        for path in ('README.md', 'TODO.md', 'pr-body/README.md', 'notes/x.md', 'pr-body/examples/x.md'):
            self.write(path, 'a b c')
        self.assertEqual(self.commit('not rules').returncode, 0)
        self.write('rule.md', 'one two')
        self.write('other.md', 'three four')
        self.assertEqual(self.commit('moved two words').returncode, 0)
        self.write('pr-body/shape.md', 'a b')
        self.assertEqual(self.commit('a pr-body file is a rule').returncode, 1)

    def test_an_amend_is_measured_against_the_commit_it_replaces(self):
        base = self.head()
        self.write('rule.md', 'one')
        self.assertEqual(self.commit('shrink by three').returncode, 0)
        self.write('rule.md', 'one two')
        self.assertEqual(self.commit('shrink by two', '--amend').returncode, 1)
        self.commit('shrink by two', '--amend', '--no-verify')
        self.assertEqual(self.push(self.head(), base).returncode, 0, 'pre-push measures the real parent')

    def test_a_merge_passes_and_pre_push_measures_its_sides(self):
        base = self.head()
        self.git('checkout', '-q', '-b', 'side')
        self.write('side.md', 'x y')
        self.commit('side grows', '--no-verify')
        self.git('checkout', '-q', 'main')
        self.write('rule.md', 'one two three')
        self.commit('main shrinks')
        r = self.git('merge', '-q', '--no-ff', '--no-edit', 'side')
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.push(self.head(), base)
        self.assertEqual(r.returncode, 1)
        self.assertIn('side grows', r.stderr)
        self.assertNotIn('Merge', r.stderr)
        bad = subprocess.run([str(SCRIPT), 'pre-push'], cwd=self.repo, env=ENV, capture_output=True,
                             input=b'refs/heads/\xff\xc2\xa0 ' + self.head().encode() + b' refs/heads/\xff ' + b'0' * 40 + b'\n')
        self.assertEqual(bad.returncode, 1, 'a ref name git accepts, neither UTF-8 nor free of odd spaces')

    def test_commit_v_reads_the_message_not_the_diff(self):
        self.write('rule.md', 'one two three four\nGrows: an old line of the rule')
        self.commit(f'seed\n\n{YES}')
        self.write('rule.md', 'one two three four five\nGrows: an old line of the rule')
        self.assertEqual(self.git('commit', '-q', '-v', '-e', '-m', 'plain', GIT_EDITOR='true').returncode, 1)

    def test_pre_push_refuses_a_skipped_hook_and_spares_what_a_remote_holds(self):
        base = self.head()
        self.git('update-ref', 'refs/remotes/origin/main', base)
        self.write('rule.md', 'one two three four five')
        self.commit('sneaky', '--no-verify')
        r = self.push(self.head(), base)
        self.assertEqual(r.returncode, 1)
        self.assertIn('sneaky', r.stderr)
        self.git('update-ref', 'refs/remotes/origin/main', self.head())
        self.git('checkout', '-q', '-b', 'feat', base)
        self.git('merge', '-q', '--no-edit', 'main')
        self.assertEqual(self.push(self.head(), base).returncode, 0)


if __name__ == '__main__':
    unittest.main()
