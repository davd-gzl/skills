#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
"""scripts/snapshot over a linked worktree in a scratch repository: the printed commit holds every
uncommitted edit over HEAD, ignored files left out, and the worktree's files, index and HEAD stay as
they were."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent.parent / 'snapshot'
ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x',
       'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x', 'GIT_CONFIG_GLOBAL': os.devnull}


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True,
                          text=True, env=ENV).stdout.strip()


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        main = root / 'main'
        main.mkdir()
        git(main, 'init', '-q')
        (main / 'a.txt').write_text('committed\n')
        (main / 'gone.txt').write_text('deleted in the worktree\n')
        (main / '.gitignore').write_text('build/\n')
        git(main, 'add', '-A')
        git(main, 'commit', '-qm', 'base')
        self.wt = root / 'wt'
        git(main, 'worktree', 'add', '-q', '-b', 'fix', str(self.wt))
        (self.wt / 'a.txt').write_text('edited, unstaged\n')
        (self.wt / 'staged.txt').write_text('staged\n')
        git(self.wt, 'add', 'staged.txt')
        (self.wt / 'untracked.txt').write_text('untracked\n')
        (self.wt / 'gone.txt').unlink()
        (self.wt / 'build').mkdir()
        (self.wt / 'build' / 'out.bin').write_text('ignored\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_commit_holds_the_uncommitted_build_and_the_worktree_is_untouched(self):
        status = git(self.wt, 'status', '--porcelain')
        index = Path(git(self.wt, 'rev-parse', '--path-format=absolute', '--git-path', 'index'))
        index_bytes, head = index.read_bytes(), git(self.wt, 'rev-parse', 'HEAD')
        run = subprocess.run([str(SNAPSHOT), str(self.wt)], capture_output=True, text=True, env=ENV)
        self.assertEqual(run.returncode, 0, run.stderr)
        sha = run.stdout.strip()
        self.assertRegex(sha, r'^[0-9a-f]{40}$', 'stdout is the sha alone')
        self.assertEqual(index.read_bytes(), index_bytes, 'the worktree index is not rewritten')
        self.assertEqual(git(self.wt, 'rev-parse', 'HEAD'), head, 'HEAD does not move')
        self.assertEqual(git(self.wt, 'status', '--porcelain'), status, 'files and staging stay as they were')
        self.assertEqual(git(self.wt, 'rev-parse', f'{sha}^'), head, 'the snapshot sits over HEAD')
        self.assertEqual(git(self.wt, 'show', f'{sha}:a.txt'), 'edited, unstaged')
        self.assertEqual(git(self.wt, 'show', f'{sha}:staged.txt'), 'staged')
        self.assertEqual(git(self.wt, 'show', f'{sha}:untracked.txt'), 'untracked')
        files = git(self.wt, 'ls-tree', '-r', '--name-only', sha).splitlines()
        self.assertNotIn('gone.txt', files, 'a deletion in the worktree is a deletion in the snapshot')
        self.assertNotIn('build/out.bin', files, 'an ignored file stays out')
        self.assertEqual(git(self.wt, 'branch', '--contains', sha), '', 'no branch points at it')

    def test_a_path_outside_a_repository_exits_non_zero(self):
        run = subprocess.run([str(SNAPSHOT), self.tmp.name], capture_output=True, text=True, env=ENV)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '', 'nothing a caller could take for a sha')


if __name__ == '__main__':
    unittest.main()
