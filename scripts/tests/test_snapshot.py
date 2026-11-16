#!/usr/bin/env python3
# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
"""scripts/snapshot over a linked worktree in a scratch repository: the printed commit holds every
uncommitted edit over HEAD, ignored files and untracked compiled executables left out, and the
worktree's files, index and HEAD stay as they were."""
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

    def snapshot(self):
        run = subprocess.run([str(SNAPSHOT), str(self.wt)], capture_output=True, text=True, env=ENV)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r'^[0-9a-f]{40}\n$', 'stdout is the sha alone')
        return run.stdout.strip(), run.stderr

    def blob(self, rev):
        return subprocess.run(['git', '-C', str(self.wt), 'cat-file', 'blob', rev], check=True,
                              capture_output=True, env=ENV).stdout

    def test_an_untracked_compiled_executable_stays_out_and_is_named_on_stderr(self):
        pe = bytearray(128)
        pe[:2], pe[0x3c:0x40], pe[0x40:0x44] = b'MZ', (0x40).to_bytes(4, 'little'), b'PE\0\0'
        builds = {'bin/tool': b'\x7fELF' + bytes(60), 'tool.macho': b'\xcf\xfa\xed\xfe' + bytes(60),
                  'tool.exe': bytes(pe)}
        for name, data in builds.items():
            (self.wt / name).parent.mkdir(exist_ok=True)
            (self.wt / name).write_bytes(data)
        sha, err = self.snapshot()
        files = git(self.wt, 'ls-tree', '-r', '--name-only', sha).splitlines()
        changed = git(self.wt, 'diff', '--name-only', 'HEAD', sha).splitlines()
        for name in builds:
            self.assertNotIn(name, files, 'a build output stays out of the commit')
            self.assertNotIn(name, changed, 'and out of its diff')
        self.assertEqual(sorted(line.rsplit(': ', 1)[1] for line in err.splitlines()), sorted(builds),
                         'each left-out path is named on stderr, one line each')
        self.assertIn('untracked.txt', files, 'every other untracked file still goes in')

    def test_an_untracked_binary_that_is_not_an_executable_goes_in(self):
        fixtures = {'golden.png': b'\x89PNG\r\n\x1a\n' + bytes(56), 'codes.csv': b'MZ,Mozambique\n'}
        for name, data in fixtures.items():
            (self.wt / name).write_bytes(data)
        sha, err = self.snapshot()
        for name, data in fixtures.items():
            self.assertEqual(self.blob(f'{sha}:{name}'), data)
        self.assertEqual(err, '', 'nothing is left out')

    def test_a_tracked_executable_that_changed_goes_in(self):
        tool = self.wt / 'tool'
        tool.write_bytes(b'\x7fELF' + bytes(60))
        git(self.wt, 'add', 'tool')
        git(self.wt, 'commit', '-qm', 'track a binary')
        tool.write_bytes(b'\x7fELF' + b'\x01' * 60)
        sha, err = self.snapshot()
        self.assertEqual(self.blob(f'{sha}:tool'), b'\x7fELF' + b'\x01' * 60)
        self.assertEqual(err, '', 'a tracked file is never filtered')

    def test_a_path_outside_a_repository_exits_non_zero(self):
        run = subprocess.run([str(SNAPSHOT), self.tmp.name], capture_output=True, text=True, env=ENV)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '', 'nothing a caller could take for a sha')


if __name__ == '__main__':
    unittest.main()
