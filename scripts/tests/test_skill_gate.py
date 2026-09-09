# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
# Behaviour of scripts/skill-gate.py: the path-to-skill map, the read record,
# the refusal, and the parsing of a shell command for write targets.
#
#   python3 -m unittest discover -s skills/scripts/tests

import importlib.util
import io
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / 'skill-gate.py'
spec = importlib.util.spec_from_file_location('skill_gate', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

SKILLS = ['review', 'review-output', 'review-comment', 'writing-style', 'shortcuts', 'issue',
          'pr-body', 'change', 'authoring', 'git']


class GateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / 'skills').mkdir()
        for name in SKILLS:
            (self.root / 'skills' / f'{name}.md').write_text(f'# {name}\n')
        (self.root / 'projects' / 'meet').mkdir(parents=True)
        (self.root / 'projects' / 'meet' / 'AGENTS.md').write_text('# meet\n')
        (self.root / 'projects' / 'bare').mkdir(parents=True)
        (self.root / 'workspace.md').write_text('# workspace\n')
        os.environ['SKILL_GATE_ROOT'] = str(self.root)
        os.environ['CLAUDE_CODE_SESSION_ID'] = 'session-a'

    def tearDown(self):
        os.environ.pop('SKILL_GATE_ROOT', None)
        os.environ.pop('CLAUDE_CODE_SESSION_ID', None)
        self.tmp.cleanup()


class RequiredReads(GateCase):
    def test_review_file_needs_review_output_style_and_delta(self):
        got = gate.required_reads('projects/meet/reviews/1498-x/3-abc/review_claude_reviewer.md')
        self.assertEqual(got, {'review', 'review-output', 'writing-style', 'meet'})

    def test_overview_is_a_review_artifact(self):
        got = gate.required_reads('projects/meet/reviews/1498-x/overview.md')
        self.assertEqual(got, {'review', 'review-output', 'writing-style', 'meet'})

    def test_comment_draft(self):
        got = gate.required_reads('projects/meet/reviews/1498-x/3-abc/comment_claude.md')
        self.assertEqual(got, {'review-comment', 'writing-style', 'meet'})

    def test_issue_and_pr_body(self):
        self.assertEqual(gate.required_reads('projects/meet/reviews/x/1-a/issue.md'),
                         {'issue', 'writing-style', 'meet'})
        self.assertEqual(gate.required_reads('projects/meet/changes/x/pr-body.md'),
                         {'pr-body', 'writing-style', 'meet'})

    def test_change_directory_files(self):
        for name in ('plan.md', 'spec.md', 'README.md'):
            self.assertEqual(gate.required_reads(f'projects/meet/changes/x/{name}'),
                             {'change', 'writing-style', 'meet'}, name)

    def test_rule_files_need_authoring(self):
        self.assertEqual(gate.required_reads('AGENTS.md'), {'authoring'})
        self.assertEqual(gate.required_reads('skills/review.md'), {'authoring'})
        self.assertEqual(gate.required_reads('projects/meet/AGENTS.md'), {'authoring', 'meet'})

    def test_a_shape_under_a_skill_reads_by_its_slashed_name(self):
        (self.root / 'skills' / 'pr-body').mkdir()
        (self.root / 'skills' / 'pr-body' / 'docs.md').write_text('# docs\n')
        out = io.StringIO()
        self.assertEqual(gate.cmd_read('pr-body/docs', out), 0)
        self.assertEqual(out.getvalue(), '# docs\n')
        self.assertTrue(gate.is_read('pr-body/docs'))
        self.assertEqual(gate.cmd_read('skills/pr-body/docs.md', io.StringIO()), 1)

    def test_a_skill_named_like_an_artifact_is_still_a_rule_file(self):
        self.assertEqual(gate.required_reads('skills/issue.md'), {'authoring'})
        self.assertEqual(gate.required_reads('skills/pr-body.md'), {'authoring'})
        self.assertEqual(gate.required_reads('skills/pr-body/docs.md'), {'authoring'})
        self.assertEqual(gate.required_reads('skills/archive/overview.md'), set())

    def test_project_without_delta_needs_no_delta_read(self):
        self.assertEqual(gate.required_reads('projects/bare/reviews/x/1-a/issue.md'),
                         {'issue', 'writing-style'})

    def test_unmapped_paths_need_nothing(self):
        self.assertEqual(gate.required_reads('scripts/foo.py'), set())
        self.assertEqual(gate.required_reads('skills/README.md'), set())
        self.assertEqual(gate.required_reads('projects/meet/checkout/AGENTS.md'), {'meet'})

    def test_checkout_code_needs_only_the_delta(self):
        self.assertEqual(gate.required_reads('projects/meet/checkout/src/app.py'), {'meet'})

    def test_a_symlink_at_a_mapped_path_is_still_mapped(self):
        link = self.root / 'projects/meet/changes/x/plan.md'
        link.parent.mkdir(parents=True)
        link.symlink_to('/tmp/elsewhere.md')
        self.assertEqual(gate.required_reads(str(link)), {'change', 'writing-style', 'meet'})

    def test_absolute_path_inside_root_is_relative(self):
        got = gate.required_reads(str(self.root / 'projects/meet/changes/x/plan.md'))
        self.assertEqual(got, {'change', 'writing-style', 'meet'})

    def test_a_symlinked_ancestor_still_maps(self):
        (self.root / 'projects/meet/changes/x').mkdir(parents=True)
        link = pathlib.Path(self.tmp.name) / 'outlink'
        link.symlink_to(self.root / 'projects/meet/changes/x')
        self.assertEqual(gate.required_reads(str(link / 'plan.md')), {'change', 'writing-style', 'meet'})

    def test_path_outside_root_needs_nothing(self):
        self.assertEqual(gate.required_reads('/tmp/elsewhere/plan.md'), set())


class SessionKey(GateCase):
    def test_harness_session_id_wins(self):
        self.assertEqual(gate.session_key(), 'session-a')

    def test_without_harness_id_names_a_non_shell_ancestor(self):
        os.environ.pop('CLAUDE_CODE_SESSION_ID')
        key = gate.session_key()
        self.assertRegex(key, r'^\d+-\d+$')
        self.assertEqual(key, gate.session_key())
        pid = int(key.split('-')[0])
        self.assertNotIn(pathlib.Path(f'/proc/{pid}/comm').read_text().strip(), gate.PASS_THROUGH)


class ReadRecord(GateCase):
    PATH = 'projects/meet/reviews/1498-x/3-abc/comment_claude.md'

    def test_nothing_read_means_every_read_missing(self):
        self.assertEqual(gate.missing_reads(self.PATH), ['meet', 'review-comment', 'writing-style'])

    def test_a_recorded_read_is_no_longer_missing(self):
        gate.record_read('review-comment')
        self.assertEqual(gate.missing_reads(self.PATH), ['meet', 'writing-style'])

    def test_read_prints_the_file_whole(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = gate.main(['read', 'review-comment'])
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue(), '# review-comment\n')

    def test_read_resolves_a_project_delta(self):
        out = io.StringIO()
        with redirect_stdout(out):
            gate.main(['read', 'meet'])
        self.assertEqual(out.getvalue(), '# meet\n')
        self.assertNotIn('meet', gate.missing_reads(self.PATH))

    def test_a_name_with_a_slash_is_refused(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['read', 'skills/git'])
        self.assertEqual(rc, 1)
        self.assertIn('name', err.getvalue())
        self.assertIn('git', gate.missing_reads('git') or ['git'])

    def test_a_read_sent_to_dev_null_is_not_recorded(self):
        with open(os.devnull, 'w') as sink:
            rc = gate.main(['read', 'git'], stdout=sink)
        self.assertEqual(rc, 1)
        self.assertFalse(gate.is_read('git'))

    def test_a_mapped_name_that_resolves_nowhere_is_not_read(self):
        (self.root / 'skills' / 'git.md').unlink()
        self.assertFalse(gate.is_read('git'))

    def test_a_read_already_current_prints_one_line_not_the_file(self):
        gate.record_read('git')
        out = io.StringIO()
        with redirect_stdout(out):
            rc = gate.main(['read', 'git'])
        self.assertEqual(rc, 0)
        self.assertNotIn('# git', out.getvalue())
        self.assertIn('unchanged', out.getvalue())
        self.assertTrue(gate.is_read('git'))

    def test_a_stale_read_prints_only_what_changed(self):
        with redirect_stdout(io.StringIO()):
            gate.main(['read', 'git'])
        (self.root / 'skills' / 'git.md').write_text('# git\n\nA new rule another session added.\n')
        self.assertFalse(gate.is_read('git'))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = gate.main(['read', 'git'])
        self.assertEqual(rc, 0)
        self.assertIn('+A new rule another session added.', out.getvalue())
        self.assertIn('--- git as read', out.getvalue())
        self.assertNotIn('# git\n\nA new rule', out.getvalue())
        self.assertTrue(gate.is_read('git'))

    def test_a_read_with_no_stored_copy_prints_the_whole_file(self):
        gate.record_read('git')
        for f in (self.root / '.skill-gate').rglob('*'):
            if f.is_file():
                f.unlink()
        (self.root / 'skills' / 'git.md').write_text('# git\n\nchanged\n')
        out = io.StringIO()
        with redirect_stdout(out):
            gate.main(['read', 'git'])
        self.assertEqual(out.getvalue(), '# git\n\nchanged\n')

    def test_unknown_name_is_an_error(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['read', 'nope'])
        self.assertEqual(rc, 1)
        self.assertIn('nope', err.getvalue())

    def test_editing_the_skill_invalidates_the_read(self):
        gate.record_read('writing-style')
        self.assertNotIn('writing-style', gate.missing_reads(self.PATH))
        (self.root / 'skills' / 'writing-style.md').write_text('# writing-style, edited\n')
        self.assertIn('writing-style', gate.missing_reads(self.PATH))

    def test_another_session_does_not_inherit_the_read(self):
        gate.record_read('writing-style')
        os.environ['CLAUDE_CODE_SESSION_ID'] = 'session-b'
        self.assertIn('writing-style', gate.missing_reads(self.PATH))


class Check(GateCase):
    PATH = 'projects/meet/changes/x/pr-body.md'

    def test_names_the_reads_to_run_and_lets_it_through(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['check', self.PATH])
        self.assertEqual(rc, 0)
        self.assertEqual(err.getvalue().splitlines(), [
            f'Run ./scripts/skill meet before writing {self.PATH}',
            f'Run ./scripts/skill pr-body before writing {self.PATH}',
            f'Run ./scripts/skill writing-style before writing {self.PATH}',
        ])

    def test_passes_once_every_read_is_recorded(self):
        for name in ('meet', 'pr-body', 'writing-style'):
            gate.record_read(name)
        self.assertEqual(gate.main(['check', self.PATH]), 0)

    def test_git_pseudo_path_needs_the_git_skill_and_the_workspace_file(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['check', 'git'])
        self.assertEqual(rc, 0)
        self.assertEqual(err.getvalue().splitlines(), [
            'Run ./scripts/skill git before a commit or push',
            'Run ./scripts/skill workspace before a commit or push'])
        gate.record_read('git')
        gate.record_read('workspace')
        self.assertEqual(gate.main(['check', 'git']), 0)

    def test_a_root_file_resolves_by_name(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(gate.main(['read', 'workspace']), 0)
        self.assertEqual(out.getvalue(), '# workspace\n')


class BashTargets(unittest.TestCase):
    def test_any_written_path_is_a_target(self):
        self.assertEqual(gate.bash_targets('echo x > projects/meet/checkout/src/app.py'), {'projects/meet/checkout/src/app.py'})
        self.assertEqual(gate.bash_targets('cp /tmp/x projects/meet/checkout/src/app.py 2>/dev/null'), {'projects/meet/checkout/src/app.py'})

    def test_quoted_redirect_target(self):
        self.assertEqual(gate.bash_targets('cat > "projects/meet/changes/my change/plan.md" <<EOF\nx\nEOF'), {'projects/meet/changes/my change/plan.md'})

    def test_cd_carries_into_later_segments(self):
        self.assertEqual(gate.bash_targets('cd projects/meet/changes/x && cat > pr-body.md <<EOF\nx\nEOF'), {'projects/meet/changes/x/pr-body.md'})

    def test_heredoc_body_is_not_a_command(self):
        self.assertEqual(gate.bash_targets("cat > /tmp/notes.txt <<'EOF'\necho hi > projects/a/changes/s/plan.md\nEOF"), {'/tmp/notes.txt'})

    def test_script_runner_heredoc_names_the_files_it_writes(self):
        cmd = "python3 - <<'EOF'\nimport pathlib\npathlib.Path('projects/meet/changes/x/plan.md').write_text('x')\nEOF"
        self.assertEqual(gate.bash_targets(cmd), {'projects/meet/changes/x/plan.md'})

    def test_git_writers_and_prefixed_git(self):
        self.assertEqual(gate.bash_targets('git mv a.md projects/a/changes/s/spec.md'), {'projects/a/changes/s/spec.md'})
        self.assertEqual(gate.bash_targets('git -C skills commit -m x'), {'git'})
        self.assertEqual(gate.bash_targets('/usr/bin/git -c a=b push'), {'git'})
        self.assertEqual(gate.bash_targets('command git merge topic'), {'git'})
        self.assertEqual(gate.bash_targets('git rebase --continue'), {'git'})
        self.assertEqual(gate.bash_targets('git cherry-pick abc'), {'git'})
        self.assertEqual(gate.bash_targets('git commit --no-verify -m x'), {'git'})
        self.assertEqual(gate.bash_targets('bash scripts/sync-push.sh s p'), {'git'})

    def test_one_liners_name_the_files_they_write(self):
        self.assertEqual(gate.bash_targets("""python3 -c "open('projects/meet/changes/x/plan.md','w').write('x')\""""), {'projects/meet/changes/x/plan.md'})
        self.assertEqual(gate.bash_targets("""python3 -c 'import sys; open("projects/meet/changes/x/plan.md","w").write(sys.argv[0])'"""), {'projects/meet/changes/x/plan.md'})
        self.assertEqual(gate.bash_targets("""node -e "require('fs').writeFileSync('projects/meet/changes/x/plan.md', 'x')\""""), {'projects/meet/changes/x/plan.md'})

    def test_a_script_file_run_with_a_path_argument_is_not_a_write(self):
        self.assertEqual(gate.bash_targets('python3 scripts/prose-check.py "projects/meet/changes/x/pr-body.md"'), set())

    def test_wrappers_and_prefixes(self):
        self.assertEqual(gate.bash_targets('GIT_AUTHOR_NAME=x git commit -m y'), {'git'})
        self.assertEqual(gate.bash_targets('env FOO=1 tee projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets('sudo -u ci tee projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("bash -c 'tee projects/a/changes/s/plan.md < /tmp/x'"), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("bash <<'EOF'\necho x > projects/a/changes/s/plan.md\nEOF"), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("find . -name x | xargs sed -i 's/a/b/' projects/a/changes/s/plan.md"), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("sed -Ei 's/a/b/' projects/a/changes/s/plan.md"), {'projects/a/changes/s/plan.md'})

    def test_here_string_is_not_a_heredoc(self):
        self.assertEqual(gate.bash_targets('cat <<< hello\necho x > projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})

    def test_input_redirect_is_not_a_target(self):
        self.assertEqual(gate.bash_targets('tee -a skills/review.md < projects/a/changes/s/plan.md'), {'skills/review.md'})

    def test_perl_module_flag_is_not_in_place(self):
        self.assertEqual(gate.bash_targets("perl -Mstrict -e 'print 1' skills/review.md"), set())

    def test_an_unresolvable_cd_resets_the_base(self):
        self.assertEqual(gate.bash_targets('cd "$(git rev-parse --show-toplevel)" && echo x > projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})

    def test_branch_switches_are_not_writes(self):
        self.assertEqual(gate.bash_targets('git checkout -q -b topic'), set())
        self.assertEqual(gate.bash_targets('git checkout main'), set())
        self.assertEqual(gate.bash_targets('git checkout -- projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets('git restore --staged skills/review.md'), set())
        self.assertEqual(gate.bash_targets('git restore skills/review.md'), {'skills/review.md'})
        self.assertEqual(gate.bash_targets('git pull'), {'git'})

    def test_more_writers(self):
        self.assertEqual(gate.bash_targets('dd if=/tmp/x of=projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("perl -pi -e 's/a/b/' projects/a/changes/s/plan.md"), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("sed --in-place 's/a/b/' projects/a/changes/s/plan.md"), {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets('echo x >| projects/a/changes/s/plan.md'), {'projects/a/changes/s/plan.md'})

    def test_redirect_and_heredoc(self):
        cmd = "mkdir -p projects/meet/changes/x && cat > projects/meet/changes/x/pr-body.md <<'EOF'\nhi\nEOF"
        self.assertEqual(gate.bash_targets(cmd), {'projects/meet/changes/x/pr-body.md'})

    def test_append_tee_sed_cp_mv(self):
        self.assertEqual(gate.bash_targets('echo x >> projects/a/reviews/s/1-a/issue.md'),
                         {'projects/a/reviews/s/1-a/issue.md'})
        self.assertEqual(gate.bash_targets('printf x | tee projects/a/changes/s/plan.md'),
                         {'projects/a/changes/s/plan.md'})
        self.assertEqual(gate.bash_targets("sed -i 's/a/b/' projects/a/reviews/s/1-a/comment_c.md"),
                         {'projects/a/reviews/s/1-a/comment_c.md'})
        self.assertEqual(gate.bash_targets('cp /tmp/x projects/a/changes/s/spec.md'),
                         {'projects/a/changes/s/spec.md'})
        self.assertEqual(gate.bash_targets('mv /tmp/x skills/review.md'), {'skills/review.md'})

    def test_a_read_only_command_has_no_target(self):
        self.assertEqual(gate.bash_targets('grep foo projects/a/reviews/s/1-a/comment_c.md'), set())
        self.assertEqual(gate.bash_targets('cat skills/review.md'), set())

    def test_a_syntax_check_of_the_push_script_is_not_a_push(self):
        self.assertEqual(gate.bash_targets('bash -n scripts/sync-push.sh && echo ok'), set())
        self.assertEqual(gate.bash_targets('cat scripts/sync-push.sh'), set())
        self.assertEqual(gate.bash_targets('bash scripts/sync-push.sh s p'), {'git'})

    def test_commit_and_push_name_git(self):
        self.assertEqual(gate.bash_targets('git add -A && git commit -m x'), {'git'})
        self.assertEqual(gate.bash_targets('git push origin HEAD:main'), {'git'})
        self.assertEqual(gate.bash_targets("./scripts/sync-push.sh 'subject' projects/a"), {'git'})
        self.assertEqual(gate.bash_targets('git log -1'), set())


class ClaudeHook(GateCase):
    def test_a_malformed_payload_warns_and_lets_it_through(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['hook-claude'], stdin=io.StringIO('not json'))
        self.assertEqual(rc, 0)
        self.assertIn('skill-gate', err.getvalue())

    def run_hook(self, payload):
        err, out = io.StringIO(), io.StringIO()
        with redirect_stderr(err), redirect_stdout(out):
            rc = gate.main(['hook-claude'], stdin=io.StringIO(json.dumps(payload)), stdout=out)
        text = out.getvalue()
        return rc, json.loads(text)['hookSpecificOutput']['additionalContext'] if text else ''

    def test_write_of_an_unread_artifact_injects_its_skills(self):
        rc, context = self.run_hook({'tool_name': 'Write', 'tool_input': {
            'file_path': str(self.root / 'projects/meet/changes/x/spec.md')}})
        self.assertEqual(rc, 0)
        for piece in ('# change', '# writing-style', '# meet', 'the write goes ahead'):
            self.assertIn(piece, context)
        for name in ('change', 'writing-style', 'meet'):
            self.assertTrue(gate.is_read(name), name)

    def test_edit_after_the_reads_passes(self):
        for name in ('meet', 'change', 'writing-style'):
            gate.record_read(name)
        rc, context = self.run_hook({'tool_name': 'Edit', 'tool_input': {
            'file_path': str(self.root / 'projects/meet/changes/x/spec.md')}})
        self.assertEqual((rc, context), (0, ''))

    def test_bash_write_is_parsed(self):
        rc, context = self.run_hook({'tool_name': 'Bash', 'tool_input': {
            'command': 'cat > projects/meet/reviews/x/1-a/issue.md <<EOF\nx\nEOF'}})
        self.assertEqual(rc, 0)
        self.assertIn('# issue', context)

    def test_other_tools_pass(self):
        rc, _ = self.run_hook({'tool_name': 'Read', 'tool_input': {'file_path': 'x'}})
        self.assertEqual(rc, 0)


class PreCommit(GateCase):
    def test_a_commit_needs_the_git_reads_too(self):
        repo = self.root
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        (repo / 'notes.txt').write_text('x')
        subprocess.run(['git', '-C', str(repo), 'add', 'notes.txt'], check=True)
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['pre-commit'], cwd=str(repo))
        self.assertEqual(rc, 0)
        self.assertIn('Run ./scripts/skill git before a commit or push', err.getvalue())
        self.assertIn('Run ./scripts/skill workspace before a commit or push', err.getvalue())


    def test_staged_mapped_path_is_named_until_read(self):
        repo = self.root
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        target = repo / 'projects/meet/changes/x/plan.md'
        target.parent.mkdir(parents=True)
        target.write_text('plan\n')
        subprocess.run(['git', '-C', str(repo), 'add', 'projects/meet/changes/x/plan.md'], check=True)
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['pre-commit'], cwd=str(repo))
        self.assertEqual(rc, 0)
        self.assertIn('Run ./scripts/skill change', err.getvalue())
        for name in ('meet', 'change', 'writing-style', 'git', 'workspace'):
            gate.record_read(name)
        self.assertEqual(gate.main(['pre-commit'], cwd=str(repo)), 0)


class PrePush(GateCase):
    def test_pushed_commits_are_checked_whatever_made_them(self):
        repo = self.root
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@x', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@x')
        run = lambda *a: subprocess.run(['git', '-C', str(repo), *a], check=True, env=env, capture_output=True, text=True).stdout.strip()
        run('init', '-q'); (repo / 'base.txt').write_text('b'); run('add', 'base.txt'); run('commit', '-q', '-n', '-m', 'base')
        base = run('rev-parse', 'HEAD')
        target = repo / 'projects/meet/changes/x/plan.md'; target.parent.mkdir(parents=True); target.write_text('p')
        run('add', 'projects/meet/changes/x/plan.md'); run('commit', '-q', '-n', '-m', 'plan')
        head = run('rev-parse', 'HEAD')
        for name in ('git', 'workspace'):
            gate.record_read(name)
        line = f'refs/heads/main {head} refs/heads/main {base}\n'
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['pre-push'], stdin=io.StringIO(line), cwd=str(repo))
        self.assertEqual(rc, 0)
        self.assertIn('Run ./scripts/skill change before writing projects/meet/changes/x/plan.md', err.getvalue())
        for name in ('meet', 'change', 'writing-style'):
            gate.record_read(name)
        self.assertEqual(gate.main(['pre-push'], stdin=io.StringIO(line), cwd=str(repo)), 0)
        zeros = f'refs/heads/main {head} refs/heads/main {"0" * 40}\n'
        self.assertEqual(gate.main(['pre-push'], stdin=io.StringIO(zeros), cwd=str(repo)), 0)

    def test_a_first_push_checks_only_the_commits_no_remote_has(self):
        repo = self.root
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@x', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@x')
        run = lambda *a: subprocess.run(['git', '-C', str(repo), *a], check=True, env=env, capture_output=True, text=True).stdout.strip()
        run('init', '-q')
        remote = pathlib.Path(self.tmp.name) / 'remote.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(remote)], check=True)
        run('remote', 'add', 'origin', str(remote))
        old = repo / 'projects/meet/changes/old/plan.md'; old.parent.mkdir(parents=True); old.write_text('old')
        run('add', '-A'); run('commit', '-q', '-n', '-m', 'base with an old plan'); run('push', '-q', 'origin', 'HEAD:main')
        run('checkout', '-q', '-b', 'topic'); (repo / 'notes.txt').write_text('n'); run('add', 'notes.txt'); run('commit', '-q', '-n', '-m', 'notes')
        head = run('rev-parse', 'HEAD')
        for name in ('git', 'workspace'):
            gate.record_read(name)
        line = f'refs/heads/topic {head} refs/heads/topic {"0" * 40}\n'
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['pre-push'], stdin=io.StringIO(line), cwd=str(repo))
        self.assertEqual((rc, err.getvalue()), (0, ''))


class HookCase(GateCase):
    REGISTER = '# Writing style\n\n## The rules\n\n- rule\n\n## Short form\n\nClipped, every reply.\n\n## Posted comments\n\nFull sentences.\n'

    def setUp(self):
        super().setUp()
        (self.root / 'skills' / 'writing-style.md').write_text(self.REGISTER)
        (self.root / 'scripts').mkdir()
        self.sync = self.root / 'scripts' / 'sync.sh'
        self.sync.write_text('#!/bin/sh\necho synced here\n')
        self.sync.chmod(0o755)
        (self.root / 'projects' / 'gno').mkdir()
        (self.root / 'projects' / 'gno' / 'AGENTS.md').write_text('# gno delta\n')
        (self.root / 'projects' / 'gno-agent-workspace').mkdir()
        (self.root / 'projects' / 'gno-agent-workspace' / 'AGENTS.md').write_text('# gno-agent-workspace delta\n')
        (self.root / '.gitmodules').write_text(
            '[submodule "projects/meet/checkout"]\n\tpath = projects/meet/checkout\n'
            '\turl = https://github.com/suitenumerique/meet.git\n')

    def run_hook(self, op, payload):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = gate.main([op], stdin=io.StringIO(payload), stdout=out)
        text = out.getvalue()
        return rc, json.loads(text)['hookSpecificOutput']['additionalContext'] if text else ''


class SessionStart(HookCase):
    def test_startup_syncs_and_injects_the_four_whole(self):
        rc, context = self.run_hook('session-start', json.dumps({'source': 'startup'}))
        self.assertEqual(rc, 0)
        self.assertIn('Sync ran: synced here', context)
        for piece in ('## Short form\n\nClipped, every reply.', '- rule', '# shortcuts', '# git', '# workspace'):
            self.assertIn(piece, context)
        for name in ('writing-style', 'shortcuts', 'git', 'workspace'):
            self.assertTrue(gate.is_read(name), name)

    def test_compact_reinjects_everything_read_without_a_sync(self):
        gate.record_read('review')
        rc, context = self.run_hook('session-start', json.dumps({'source': 'compact'}))
        self.assertEqual(rc, 0)
        self.assertNotIn('Sync', context)
        for piece in ('## Short form', '# git', '# review'):
            self.assertIn(piece, context)

    def test_a_failing_sync_still_injects(self):
        self.sync.write_text('#!/bin/sh\necho no network >&2\nexit 1\n')
        rc, context = self.run_hook('session-start', json.dumps({'source': 'startup'}))
        self.assertEqual(rc, 0)
        self.assertIn('Sync failed: no network', context)
        self.assertIn('## Short form', context)

    def test_a_malformed_payload_still_injects(self):
        rc, context = self.run_hook('session-start', 'not json')
        self.assertEqual(rc, 0)
        self.assertIn('## Short form', context)

    def test_the_payload_session_id_keys_the_record(self):
        os.environ.pop('CLAUDE_CODE_SESSION_ID')
        self.run_hook('session-start', json.dumps({'source': 'startup', 'session_id': 'from-payload'}))
        self.assertIn('from-payload:git', gate.load())


class Prompt(HookCase):
    def test_a_review_prompt_loads_the_review_skills_and_the_repo_delta(self):
        rc, context = self.run_hook('prompt', json.dumps(
            {'prompt': 'deep review https://github.com/suitenumerique/meet/pull/1675'}))
        self.assertEqual(rc, 0)
        for piece in ('# review\n', '# review-output', '# review-comment', '# meet'):
            self.assertIn(piece, context)
        self.assertNotIn('# change', context)
        self.assertTrue(gate.is_read('meet'))

    def test_a_second_prompt_adds_nothing_already_read(self):
        self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675'}))
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675 again'}))
        self.assertEqual((rc, context), (0, ''))

    def test_a_word_with_no_skill_injects_nothing(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'push'}))
        self.assertEqual((rc, context), (0, ''))

    def test_a_family_word_loads_every_project_sharing_it(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'fix gnolang/gno-fixes 64'}))
        for piece in ('# change', '# pr-body', '# issue', '# gno delta', '# gno-agent-workspace delta'):
            self.assertIn(piece, context)
        self.assertNotIn('# meet', context)

    def test_a_malformed_payload_is_quiet(self):
        rc, context = self.run_hook('prompt', 'not json')
        self.assertEqual((rc, context), (0, ''))


if __name__ == '__main__':
    unittest.main()
