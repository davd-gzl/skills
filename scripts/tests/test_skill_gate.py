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
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / 'skill-gate.py'
spec = importlib.util.spec_from_file_location('skill_gate', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

SKILLS = ['review', 'review-comment', 'writing-style', 'shortcuts', 'short-form', 'issue',
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
        self.assertEqual(got, {'review', 'writing-style', 'meet'})

    def test_overview_is_a_review_artifact(self):
        got = gate.required_reads('projects/meet/reviews/1498-x/overview.md')
        self.assertEqual(got, {'review', 'writing-style', 'meet'})

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

    def test_a_project_context_rides_with_the_delta_and_is_a_rule_file(self):
        (self.root / 'projects' / 'meet' / 'CONTEXT.md').write_text('# meet context\n')
        self.assertEqual(gate.required_reads('projects/meet/checkout/src/app.py'), {'meet', 'meet/context'})
        self.assertEqual(gate.required_reads('projects/meet/CONTEXT.md'), {'authoring', 'meet', 'meet/context'})
        self.assertEqual(gate.required_reads('projects/meet/context-log.md'), {'authoring', 'meet', 'meet/context'})
        self.assertEqual(gate.required_reads('projects/bare/reviews/x/1-a/issue.md'), {'issue', 'writing-style'})

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

    def test_read_resolves_a_project_context_by_its_slashed_name(self):
        (self.root / 'projects' / 'meet' / 'CONTEXT.md').write_text('# meet context\n')
        out = io.StringIO()
        with redirect_stdout(out):
            rc = gate.main(['read', 'meet/context'])
        self.assertEqual((rc, out.getvalue()), (0, '# meet context\n'))
        self.assertTrue(gate.is_read('meet/context'))
        self.assertFalse(gate.is_read('bare/context'))

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

    def test_a_file_over_the_bash_bound_is_named_not_printed(self):
        (self.root / 'skills' / 'review.md').write_text('# review\n' + 'x' * (gate.BASH_BOUND + 1))
        out = io.StringIO()
        rc = gate.main(['read', 'review'], stdout=out)
        self.assertEqual(rc, 0)
        self.assertIn('Read', out.getvalue())
        self.assertNotIn('xxxx', out.getvalue())
        self.assertFalse(gate.is_read('review'))

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

    def test_a_fixture_string_in_an_inline_script_is_not_a_write(self):
        cmd = ("python3 - <<'EOF'\nprefixes = ['- `skills/review.md` rule', 'projects/meet/changes/x/plan.md']\n"
               "assert 'projects/meet/AGENTS.md' not in prefixes\np = 'TODO.md'\nopen(p, 'w').write('x')\nEOF")
        self.assertEqual(gate.bash_targets(cmd), set())
        cmd = "python3 - <<'EOF'\nnames = ['projects/meet/AGENTS.md']\nopen('projects/meet/changes/x/plan.md', 'w').write('x')\nEOF"
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

    def test_write_of_an_unread_artifact_names_its_skills_by_path(self):
        rc, context = self.run_hook({'tool_name': 'Write', 'tool_input': {
            'file_path': str(self.root / 'projects/meet/changes/x/spec.md')}})
        self.assertEqual(rc, 0)
        for piece in ('skills/change.md', 'skills/writing-style.md', 'projects/meet/AGENTS.md', 'the write goes ahead'):
            self.assertIn(piece, context)
        self.assertNotIn('# change', context)
        for name in ('change', 'writing-style', 'meet'):
            self.assertFalse(gate.is_read(name), name)

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
        self.assertIn('skills/issue.md', context)

    def test_other_tools_pass(self):
        rc, _ = self.run_hook({'tool_name': 'Read', 'tool_input': {'file_path': 'x'}})
        self.assertEqual(rc, 0)


class PublishWords(GateCase):
    """A publish, a push outside the standing list, a forced push and an AI marker wait for their word."""

    def turn(self, prompt, queued=()):
        path = self.root / 'transcript.jsonl'
        rows = [{'type': 'user', 'message': {'role': 'user', 'content': 'an earlier turn: post'}},
                {'type': 'assistant', 'message': {'role': 'assistant', 'content': []}},
                {'type': 'user', 'message': {'role': 'user', 'content': prompt}},
                {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'content': 'post'}]}}]
        rows += [{'type': 'attachment', 'attachment': {'type': 'queued_command', 'prompt': q, 'origin': {'kind': 'human'}}}
                 for q in queued]
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
        return str(path)

    def hook(self, command, prompt='fix it', queued=(), cwd=None):
        err = io.StringIO()
        payload = {'tool_name': 'Bash', 'tool_input': {'command': command},
                   'transcript_path': self.turn(prompt, queued), 'cwd': cwd or str(self.root)}
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = gate.main(['hook-claude'], stdin=io.StringIO(json.dumps(payload)), stdout=io.StringIO())
        return rc, err.getvalue()

    def repo(self, url):
        repo = self.root / 'r'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin', url], check=True)
        return str(repo)

    def test_a_post_waits_for_the_word_in_this_turn_only(self):
        post = 'gh pr comment 5 -R o/r -b hi'
        self.assertEqual(self.hook(post)[0], 2, 'the word in an earlier turn or in a tool result is not the word')
        self.assertEqual(self.hook(post, prompt='post it')[0], 0)
        self.assertEqual(self.hook(post, queued=['post'])[0], 0, 'a message queued into the turn carries it')
        self.assertEqual(self.hook(post, prompt='ok go')[0], 2, 'a vague yes authorises nothing')

    def test_reads_dry_runs_and_an_open_pr_body_edit_pass(self):
        for cmd in ('gh pr view 5 -R o/r', 'gh api repos/o/r/pulls/5/comments --paginate',
                    "gh api graphql -f query='query{viewer{login}}'", 'gh api -X PATCH repos/o/r/pulls/5 -F body=@b.md',
                    './scripts/post-review.sh d.md --dry-run', 'git commit -m "quote gh pr comment | x"'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)

    def test_writes_through_the_api_and_the_post_scripts_wait(self):
        for cmd in ('gh api repos/o/r/issues/1/comments -f body=x', "gh api graphql -f query='mutation{x}'",
                    './scripts/post-review.sh d.md', 'gh issue create -R o/r -t t -b b'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)
        self.assertEqual(self.hook('gh pr merge 5', prompt='post')[0], 2, 'a merge takes merge, not post')
        self.assertEqual(self.hook('gh pr merge 5', prompt='merge 5')[0], 0)

    def test_an_ai_marker_is_refused_whatever_the_turn_says(self):
        rc, err = self.hook('git commit -m "fix\n\nCo-Authored-By: someone"', prompt='post push')
        self.assertEqual(rc, 2)
        self.assertIn('Invariant 7', err)

    def test_a_push_outside_the_standing_list_waits_for_push(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine, other = self.repo('https://github.com/me/private.git'), None
        self.assertEqual(self.hook(f'git -C {mine} push origin HEAD:main')[0], 0)
        shutil.rmtree(self.root / 'r')
        other = self.repo('https://github.com/me/public.git')
        self.assertEqual(self.hook(f'git -C {other} push origin HEAD:main')[0], 2)
        self.assertEqual(self.hook(f'git -C {other} push origin HEAD:main', prompt='push')[0], 0)

    def test_a_forced_push_waits_for_force_even_on_a_standing_repo(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine = self.repo('https://github.com/me/private.git')
        self.assertEqual(self.hook(f'git -C {mine} push --force origin HEAD:main', prompt='push')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push origin +HEAD:main', prompt='push')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push --force origin HEAD:main', prompt='push, force it')[0], 0)


class PublishWordsEdges(PublishWords):
    """The cases a checker found: none of these may block ordinary work, and none may slip a publish through."""

    def test_ordinary_work_is_never_refused(self):
        for cmd in ('git stash push -q -u -m wip', 'git stash push -m "a push note"',
                    "cat > n.md <<'X'\ngh pr close 5 --comment x\nX", 'git push --dry-run origin HEAD:main',
                    'gh api --method=GET repos/o/r/pulls -f state=open', "gh api graphql -f query='query{x}' --jq '.mutation'",
                    'echo "the merge-base looks off"'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)

    def test_nul_lines_and_notifications_do_not_lose_the_word(self):
        path = self.root / 't.jsonl'
        path.write_text('\n'.join([
            json.dumps({'type': 'user', 'message': {'role': 'user', 'content': 'post it'}}),
            '\x00\x00\x00',
            json.dumps({'type': 'user', 'message': {'role': 'user', 'content': '<task-notification>ready to go</task-notification>'}}),
            json.dumps({'type': 'user', 'isCompactSummary': True, 'message': {'role': 'user', 'content': 'summary: merge'}}),
        ]) + '\n')
        self.assertIn('post it', gate.turn_text(str(path)))
        self.assertNotIn('merge', gate.turn_text(str(path)))

    def test_a_standing_push_needs_no_transcript(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine = self.repo('https://github.com/me/private.git')
        err = io.StringIO()
        payload = {'tool_name': 'Bash', 'tool_input': {'command': f'git -C {mine} push origin HEAD:main'}, 'cwd': str(self.root)}
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = gate.main(['hook-claude'], stdin=io.StringIO(json.dumps(payload)), stdout=io.StringIO())
        self.assertEqual(rc, 0, err.getvalue())

    def test_wrapped_and_flagged_publishes_are_seen(self):
        for cmd in ('gh -R o/r pr comment 5 -b x', 'env GH_REPO=o/r gh pr comment 5 -b x', 'GH_REPO=o/r gh pr comment 5 -b x',
                    'command gh pr comment 5 -b x', '/usr/bin/gh pr comment 5 -b x', "bash -c 'gh pr comment 5 -b x'",
                    'for n in 1 2; do gh pr comment $n -b x; done', 'x=$(gh pr merge 5)', 'bash scripts/post-review.sh d.md',
                    'python3 scripts/post-pr-review.py 5 d.md', 'gh api -X PATCH repos/o/r/pulls/5 -f state=closed'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_every_publish_on_the_line_needs_its_own_word(self):
        both = 'gh pr comment 5 -b x && gh pr merge 5'
        self.assertEqual(self.hook(both, prompt='post')[0], 2)
        self.assertEqual(self.hook(both, prompt='post and merge')[0], 0)
        self.assertEqual(self.hook('gh pr comment 5 -b x', prompt="don't post anything yet")[0], 2)

    def test_combined_force_flags_and_mirror_are_forced(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine = self.repo('https://github.com/me/private.git')
        for flag in ('-fu', '-uf', '--mirror'):
            self.assertEqual(self.hook(f'git -C {mine} push {flag} origin HEAD:main', prompt='push')[0], 2, flag)

    def test_marker_forms_are_all_caught(self):
        for cmd in ('git commit --message="x\n\nCo-Authored-By: a"', 'git commit -m"Co-Authored-By: a"',
                    'git commit -am "Co-Authored-By: a"', 'git commit -m x --trailer "Co-authored-by: a"'):
            self.assertEqual(self.hook(cmd, prompt='post push')[0], 2, cmd)


class PublishWordsRoundThree(PublishWords):
    """What replaying every recorded command through the gate turned up."""

    def standing(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        return self.repo('https://github.com/me/private.git')

    def test_a_directory_in_a_shell_variable_resolves(self):
        mine = self.standing()
        self.assertEqual(self.hook(f'G={mine}; git -C $G push origin main')[0], 0)
        self.assertEqual(self.hook(f'R={self.root}; C=$R/r; git -C "$C" push -q origin main')[0], 0)
        self.assertEqual(self.hook(f'W={mine}; cd $W && git push origin main')[0], 0)
        self.assertEqual(self.hook(f'git -C{mine} push origin main')[0], 0)

    def test_a_push_to_a_path_on_this_machine_publishes_nothing(self):
        bare = self.root / 'bare.git'
        subprocess.run(['git', 'init', '-q', '--bare', str(bare)], check=True)
        repo = self.repo(str(bare))
        self.assertEqual(self.hook(f'git -C {repo} push origin main')[0], 0)

    def test_a_push_option_value_is_not_the_remote(self):
        mine = self.standing()
        self.assertEqual(self.hook(f'git -C {mine} push -o ci.skip origin main')[0], 0)

    def test_subshells_wrappers_and_eval_are_seen(self):
        for cmd in ('(gh pr comment 5 -b x)', 'timeout 30 gh pr comment 5 -b x', 'nice -n 5 gh pr comment 5 -b x',
                    'sudo -u me gh pr comment 5 -b x', 'eval gh pr comment 5 -b x', "fish -c 'gh pr comment 5 -b x'",
                    'gh issue edit 5 -b x', 'gh gist create --public f.md', 'gh release upload v1 f.tgz'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_marker_in_a_heredoc_commit_message_is_caught_and_a_mention_elsewhere_is_not(self):
        heredoc = 'git commit -m "$(cat <<\'EOF\'\nfix\n\nCo-Authored-By: someone\nEOF\n)"'
        self.assertEqual(self.hook(heredoc, prompt='push')[0], 2)
        elsewhere = './scripts/todo add "refuse Co-Authored-By: lines" && ./scripts/commit -m "TODO: a line" TODO.md'
        self.assertEqual(self.hook(elsewhere)[0], 0)

    def test_a_prompt_carrying_an_image_still_opens_the_turn(self):
        path = self.root / 'img.jsonl'
        path.write_text(json.dumps({'type': 'user', 'message': {'role': 'user', 'content': [
            {'type': 'image', 'source': {}}, {'type': 'text', 'text': 'post this'}]}}) + '\n')
        self.assertIn('post this', gate.turn_text(str(path)))


class PublishWordsRoundFour(PublishWordsRoundThree):
    """What the fourth check round found."""

    def test_a_scratch_repo_made_on_the_same_line_can_take_a_push(self):
        cmd = 'S=$(mktemp -d); git init -q --bare $S/r.git; git clone -q $S/r.git $S/w; git -C $S/w push origin HEAD:main'
        self.assertEqual(self.hook(cmd)[0], 0)

    def test_a_subshell_cd_ends_at_its_parenthesis(self):
        mine = self.standing()
        self.assertEqual(self.hook(f'cd {mine} && (cd /tmp && true); git push origin main')[0], 0)
        (self.root / 'other').mkdir()
        other = self.root / 'other'
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        subprocess.run(['git', '-C', str(other), 'remote', 'add', 'origin', 'https://github.com/me/public.git'], check=True)
        self.assertEqual(self.hook(f'cd {other} && (cd {mine} && git status); git push origin main')[0], 2)

    def test_a_contents_upload_is_free_on_a_standing_repo_only(self):
        self.standing()
        self.assertEqual(self.hook('gh api -X PUT repos/me/private/contents/a.png -f content=x -f message=m')[0], 0)
        self.assertEqual(self.hook('gh api -X PUT repos/me/public/contents/a.png -f content=x -f message=m')[0], 2)
        self.assertEqual(self.hook('gh api -X PUT repos/me/public/contents/a.png -f content=x', prompt='upload')[0], 0)

    def test_a_branch_delete_waits_for_delete(self):
        mine = self.standing()
        self.assertEqual(self.hook(f'git -C {mine} push origin --delete old')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push origin :old')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push origin :old', prompt='delete old')[0], 0)

    def test_a_repo_where_every_change_takes_the_word(self):
        (self.root / 'workspace.json').write_text(json.dumps({'word_for_every_change': ['up/strict']}))
        self.assertEqual(self.hook('gh api -X PATCH repos/up/strict/pulls/5 -f body=x')[0], 2)
        self.assertEqual(self.hook('gh api -X PATCH repos/up/loose/pulls/5 -f body=x')[0], 0)
        self.assertEqual(self.hook('gh pr edit 5 -R up/strict --body x')[0], 2)

    def test_login_shells_force_sync_and_rendering(self):
        self.assertEqual(self.hook("bash -lc 'gh pr comment 5 -b x'")[0], 2)
        self.assertEqual(self.hook('gh repo sync me/fork --force')[0], 2)
        self.assertEqual(self.hook('gh api markdown -f text=hi')[0], 0)

    def test_a_malformed_transcript_row_is_skipped(self):
        path = self.root / 'bad.jsonl'
        path.write_text('[1, 2]\n"a string"\n' + json.dumps({'type': 'user', 'message': {'role': 'user', 'content': 'post'}}) + '\n')
        self.assertIn('post', gate.turn_text(str(path)))


class PublishWordsRoundFive(PublishWordsRoundFour):
    """What the fifth check round found."""

    def test_an_unreadable_remote_is_refused_unless_this_line_made_it(self):
        for cmd in ('T=$(mktemp -d); D=$(ls -d nowhere); git -C "$D" push origin x',
                    'git init -q /tmp/x-probe && git -C "$(pwd)/nowhere" push origin x',
                    'git -C "$(pwd)/nowhere" push origin x; mktemp'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)
        self.assertEqual(self.hook('S=$(mktemp -d); git init -q $S/w; git -C $S/w push origin main')[0], 0)
        self.assertEqual(self.hook('git clone -q /tmp/src /tmp/dst-probe && git -C /tmp/dst-probe/sub push origin main')[0], 0)

    def test_bash_options_before_c(self):
        for cmd in ("bash -e -c 'gh pr comment 5 -b x'", "bash -o pipefail -c 'gh pr comment 5 -b x'",
                    "bash --login -c 'gh pr comment 5 -b x'"):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_every_form_of_a_strict_repository(self):
        (self.root / 'workspace.json').write_text(json.dumps({'word_for_every_change': ['up/strict']}))
        self.assertEqual(self.hook('gh pr edit 5 --repo=up/strict --body x')[0], 2)
        self.assertEqual(self.hook('gh pr edit https://github.com/up/strict/pull/5 --body x')[0], 2)
        co = self.repo('https://github.com/up/strict.git')
        self.assertEqual(self.hook(f'cd {co} && gh pr edit 5 --body x')[0], 2)

    def test_a_sync_is_a_push_and_a_forced_sync_is_never_allowed(self):
        self.assertEqual(self.hook('gh repo sync me/fork')[0], 2)
        self.assertEqual(self.hook('gh repo sync me/fork', prompt='push')[0], 0)
        self.assertEqual(self.hook('gh repo sync me/fork --force', prompt='push, force it')[0], 2)
        self.assertEqual(self.hook('gh api markdown/raw --input f.md')[0], 0)


class PublishWordsRoundSix(PublishWordsRoundFive):
    """A push the gate cannot place waits for the word: what the sixth check round tried."""

    def test_every_way_to_point_a_push_elsewhere_waits(self):
        for cmd in ('git clone https://github.com/me/public y; cd y; git push origin HEAD:x',
                    'T=$(mktemp -d); cd $T; git init; git remote add origin https://github.com/me/public; git push origin HEAD',
                    'T=$(mktemp -d); git -C $T/../../etc push origin HEAD', 'git init x; git -C x/../elsewhere push origin HEAD',
                    'T=$(mktemp -d); git -C $T push --repo=https://github.com/me/public',
                    'git --git-dir=/elsewhere/.git push origin HEAD', 'GIT_DIR=/elsewhere/.git git push origin HEAD',
                    'T=$(mktemp -d); pushd $T; popd; git push origin HEAD', 'f(){ cd /elsewhere; }; cd /tmp; f; git push origin HEAD',
                    'git subtree push --prefix d origin main'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_strict_repository_in_any_spelling(self):
        (self.root / 'workspace.json').write_text(json.dumps({'word_for_every_change': ['up/strict']}))
        for cmd in ('gh pr edit 5 --repo github.com/up/strict --body x', 'gh pr edit 5 --repo https://github.com/up/strict --body x',
                    'gh pr edit 5 -Rup/strict --body x', 'GH_REPO=up/strict gh pr edit 5 --body x',
                    'gh pr edit 5 --repo Up/Strict --body x', 'gh api -X PATCH repos/UP/strict/pulls/5 -f body=x'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)
        self.assertEqual(self.hook('gh api /markdown -f text=hi')[0], 0)


class PublishWordsRoundSeven(PublishWordsRoundSix):
    """What the seventh check round found."""

    def test_the_post_wrapper_and_a_strict_body_apply_wait(self):
        self.assertEqual(self.hook('./scripts/post d.md')[0], 2)
        (self.root / 'workspace.json').write_text(json.dumps({'word_for_every_change': ['up/strict']}))
        (self.root / 'b.md').write_text('# PR\nTarget: https://github.com/up/strict/pull/4\n')
        (self.root / 'c.md').write_text('# PR\nTarget: https://github.com/up/loose/pull/4\n')
        self.assertEqual(self.hook('./scripts/pr-body-apply b.md')[0], 2)
        self.assertEqual(self.hook('./scripts/pr-body-apply c.md')[0], 0)

    def test_redirects_and_config_reads_do_not_refuse_a_standing_push(self):
        mine = self.standing()
        for cmd in (f'cd {mine} && git push 2>&1 | tail -3', f'cd {mine} && git push >/dev/null 2>&1',
                    f'cd {mine} && git add a.config.ts && git push origin main',
                    f'cd {mine} && git push origin main && git config --get user.name'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)
        self.assertEqual(self.hook(f'cd {mine} && git config remote.origin.url https://x && git push')[0], 2)

    def test_recursive_and_submodule_pushes_wait(self):
        mine = self.standing()
        self.assertEqual(self.hook(f'cd {mine} && git push --recurse-submodules=on-demand origin main')[0], 2)
        self.assertEqual(self.hook(f'cd {mine} && git submodule foreach git push origin main')[0], 2)
        self.assertEqual(self.hook('test -d .git; and gh pr comment 5 -b x')[0], 2)


class PublishWordsRoundEight(PublishWordsRoundSeven):
    """What the eighth check round found."""

    def test_a_mutation_the_gate_cannot_read_ahead_waits(self):
        for cmd in ("cat > /tmp/q-probe.json <<'J'\n{\"query\":\"mutation{submitPullRequestReview}\"}\nJ\ngh api graphql --input /tmp/q-probe-missing.json",
                    'Q=$(cat m.graphql); gh api graphql -f query="$Q"', 'gh api graphql -F query=@nowhere.graphql',
                    'gh api graphql --input nowhere.json'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)
        (self.root / 'q.graphql').write_text('query { viewer { login } }')
        self.assertEqual(self.hook(f'cd {self.root} && gh api graphql -F query=@q.graphql')[0], 0)

    def test_a_pr_edit_beyond_its_body_waits(self):
        self.assertEqual(self.hook('gh pr edit 5 -R o/r --body x')[0], 0)
        self.assertEqual(self.hook("gh pr edit 5 -R o/r --body-file - <<'MD'\nbody\nMD")[0], 0)
        for cmd in ('gh pr edit 5 -R o/r --title t', 'gh pr edit 5 -R o/r --add-label l', 'gh pr edit 5 --add-reviewer me'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_redirect_is_never_an_argument(self):
        cmd = 'git init -q --bare /tmp/rp.git && git clone -q /tmp/rp.git /tmp/rp-w 2>/dev/null && git -C /tmp/rp-w push origin HEAD'
        self.assertEqual(self.hook(cmd)[0], 0)


class HookRead(GateCase):
    def read(self, payload):
        return gate.main(['hook-read'], stdin=io.StringIO(json.dumps(payload)))

    def test_a_whole_read_of_a_skill_records_it(self):
        rc = self.read({'tool_name': 'Read', 'tool_input': {'file_path': str(self.root / 'skills/review.md')}})
        self.assertEqual(rc, 0)
        self.assertTrue(gate.is_read('review'))

    def test_a_partial_read_records_nothing(self):
        self.read({'tool_name': 'Read', 'tool_input': {'file_path': str(self.root / 'skills/review.md'), 'offset': 10}})
        self.read({'tool_name': 'Read', 'tool_input': {'file_path': str(self.root / 'skills/review.md'), 'limit': 5}})
        self.assertFalse(gate.is_read('review'))

    def test_a_delta_a_shape_and_a_root_file_record(self):
        (self.root / 'skills' / 'pr-body').mkdir()
        (self.root / 'skills' / 'pr-body' / 'docs.md').write_text('# docs\n')
        for path, name in ((self.root / 'projects/meet/AGENTS.md', 'meet'),
                           (self.root / 'skills/pr-body/docs.md', 'pr-body/docs'),
                           (self.root / 'workspace.md', 'workspace')):
            self.read({'tool_name': 'Read', 'tool_input': {'file_path': str(path)}})
            self.assertTrue(gate.is_read(name), name)

    def test_a_project_context_records_under_its_slashed_name(self):
        (self.root / 'projects' / 'meet' / 'CONTEXT.md').write_text('# meet context\n')
        self.read({'tool_name': 'Read', 'tool_input': {'file_path': str(self.root / 'projects/meet/CONTEXT.md')}})
        self.assertTrue(gate.is_read('meet/context'))
        self.assertFalse(gate.is_read('meet'))

    def test_a_relative_path_resolves_against_cwd(self):
        self.read({'tool_name': 'Read', 'tool_input': {'file_path': 'skills/git.md'}, 'cwd': str(self.root)})
        self.assertTrue(gate.is_read('git'))

    def test_other_paths_and_tools_record_nothing(self):
        self.read({'tool_name': 'Read', 'tool_input': {'file_path': str(self.root / 'projects/meet/checkout/README.md')}})
        self.read({'tool_name': 'Write', 'tool_input': {'file_path': str(self.root / 'skills/review.md')}})
        self.assertEqual(gate.session_reads(), [])

    def test_a_malformed_payload_is_quiet(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['hook-read'], stdin=io.StringIO('not json'))
        self.assertEqual((rc, err.getvalue()), (0, ''))


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


class PreCommitRefusals(GateCase):
    def _repo(self):
        repo = self.root
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        for name in ('git', 'workspace'):
            gate.record_read(name)
        return repo

    def test_a_workflow_script_with_a_bare_backtick_is_refused(self):
        if shutil.which('node') is None:
            self.skipTest('node absent')
        repo = self._repo()
        script = repo / 'scripts/workflows/x.js'
        script.parent.mkdir(parents=True)
        script.write_text('export const meta = { name: "x" }\nconst p = `a ` b`\nreturn p\n')
        subprocess.run(['git', '-C', str(repo), 'add', 'scripts/workflows/x.js'], check=True)
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['pre-commit'], cwd=str(repo))
        self.assertEqual(rc, 1)
        self.assertIn('scripts/workflows/x.js does not parse as a workflow script', err.getvalue())
        script.write_text('export const meta = { name: "x" }\nconst p = `a \\` b`\nreturn p\n')
        subprocess.run(['git', '-C', str(repo), 'add', 'scripts/workflows/x.js'], check=True)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(gate.main(['pre-commit'], cwd=str(repo)), 0, 'a top-level return parses once wrapped')

    def test_a_gitlink_no_remote_holds_is_refused(self):
        repo = self._repo()
        sub = repo / 'sub'
        subprocess.run(['git', 'init', '-q', str(sub)], check=True)
        (sub / 'f').write_text('x')
        env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x'}
        subprocess.run(['git', '-C', str(sub), 'add', 'f'], check=True)
        subprocess.run(['git', '-C', str(sub), 'commit', '-qm', 'one'], check=True, env=env)
        sha = subprocess.run(['git', '-C', str(sub), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(['git', '-C', str(repo), 'update-index', '--add', '--cacheinfo', f'160000,{sha},sub'], check=True)
        err = io.StringIO()
        with redirect_stderr(err):
            rc = gate.main(['pre-commit'], cwd=str(repo))
        self.assertEqual(rc, 1)
        self.assertIn('sub points at', err.getvalue())
        self.assertIn('push the submodule first', err.getvalue())
        subprocess.run(['git', '-C', str(sub), 'update-ref', 'refs/remotes/origin/main', sha], check=True)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(gate.main(['pre-commit'], cwd=str(repo)), 0, 'held by a remote branch, the pointer passes')


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
    def setUp(self):
        super().setUp()
        (self.root / 'skills' / 'writing-style.md').write_text('# Writing style\n\n## The rules\n\n- rule\n')
        (self.root / 'skills' / 'short-form.md').write_text('# Short form\n\nClipped, every reply.\n')
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
    def test_startup_syncs_and_records_the_imports(self):
        rc, context = self.run_hook('session-start', json.dumps({'source': 'startup'}))
        self.assertEqual(rc, 0)
        self.assertIn('Sync ran: synced here', context)
        self.assertIn('Read tool', context)
        for piece in ('- rule', 'Clipped', 'skills/writing-style.md'):
            self.assertNotIn(piece, context)
        for name in ('shortcuts', 'short-form'):
            self.assertTrue(gate.is_read(name), name)
        for name in ('writing-style', 'git', 'workspace'):
            self.assertFalse(gate.is_read(name), name)

    def test_compact_forgets_the_reads_and_names_them_for_rereading(self):
        gate.record_read('review')
        gate.record_read('shortcuts')
        rc, context = self.run_hook('session-start', json.dumps({'source': 'compact'}))
        self.assertEqual(rc, 0)
        self.assertNotIn('Sync', context)
        self.assertIn('- review: Read `skills/review.md`', context)
        self.assertNotIn('- shortcuts: Read', context)
        self.assertFalse(gate.is_read('review'))
        self.assertTrue(gate.is_read('shortcuts'))

    def test_a_failing_sync_still_reports(self):
        self.sync.write_text('#!/bin/sh\necho no network >&2\nexit 1\n')
        rc, context = self.run_hook('session-start', json.dumps({'source': 'startup'}))
        self.assertEqual(rc, 0)
        self.assertIn('Sync failed: no network', context)
        self.assertTrue(gate.is_read('short-form'))

    def test_a_malformed_payload_still_records_the_imports(self):
        rc, context = self.run_hook('session-start', 'not json')
        self.assertEqual(rc, 0)
        self.assertIn('Read tool', context)
        self.assertTrue(gate.is_read('shortcuts'))

    def test_the_payload_session_id_keys_the_record(self):
        os.environ.pop('CLAUDE_CODE_SESSION_ID')
        self.run_hook('session-start', json.dumps({'source': 'startup', 'session_id': 'from-payload'}))
        self.assertIn('from-payload:shortcuts', gate.load())

    def test_the_context_stays_under_the_hook_bound(self):
        for name in SKILLS:
            gate.record_read(name)
        rc, context = self.run_hook('session-start', json.dumps({'source': 'compact'}))
        self.assertLess(len(context), 10000)


class Prompt(HookCase):
    def test_a_review_prompt_names_the_review_skills_and_the_repo_delta(self):
        rc, context = self.run_hook('prompt', json.dumps(
            {'prompt': 'deep review https://github.com/suitenumerique/meet/pull/1675'}))
        self.assertEqual(rc, 0)
        for piece in ('skills/review.md', 'projects/meet/AGENTS.md'):
            self.assertIn(piece, context)
        # the drafting rules are the writer stage's, per review.md step 4; the write hook names them
        for piece in ('skills/review-comment.md', 'skills/change.md'):
            self.assertNotIn(piece, context)
        self.assertNotIn('# review', context)
        self.assertFalse(gate.is_read('meet'))

    def test_a_repo_with_a_context_file_names_it_beside_the_delta(self):
        (self.root / 'projects' / 'meet' / 'CONTEXT.md').write_text('# meet context\n')
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675'}))
        self.assertEqual(rc, 0)
        for piece in ('projects/meet/AGENTS.md', 'projects/meet/CONTEXT.md'):
            self.assertIn(piece, context)
        self.assertNotIn('projects/gno/CONTEXT.md', context)
        gate.record_read('meet/context')
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675'}))
        self.assertNotIn('CONTEXT.md', context)

    def test_a_second_prompt_names_nothing_already_read(self):
        for name in ('review', 'review-comment', 'meet'):
            gate.record_read(name)
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675 again'}))
        self.assertEqual((rc, context), (0, ''))

    def test_an_unread_skill_is_named_on_every_prompt_until_read(self):
        self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675'}))
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review meet 1675 again'}))
        self.assertIn('skills/review.md', context)

    def test_a_word_with_no_skill_names_nothing(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'push'}))
        self.assertEqual((rc, context), (0, ''))

    def test_a_family_word_names_every_project_sharing_it(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'fix gnolang/gno-sandbox 64'}))
        for piece in ('skills/change.md', 'skills/pr-body.md', 'skills/issue.md', 'projects/gno/AGENTS.md', 'projects/gno-agent-workspace/AGENTS.md'):
            self.assertIn(piece, context)
        self.assertNotIn('projects/meet', context)

    def test_an_owner_in_a_slug_or_a_url_names_no_project(self):
        (self.root / 'projects' / 'tx-indexer').mkdir(parents=True)
        (self.root / 'projects' / 'tx-indexer' / 'AGENTS.md').write_text('# tx-indexer\n')
        (self.root / '.gitmodules').write_text(
            '[submodule "projects/tx-indexer/checkout"]\n\tpath = projects/tx-indexer/checkout\n'
            '\turl = https://github.com/gnolang/tx-indexer.git\n')
        for prompt in ('review https://github.com/gnolang/tx-indexer/pull/241', 'review gnolang/tx-indexer#241'):
            rc, context = self.run_hook('prompt', json.dumps({'prompt': prompt}))
            self.assertIn('projects/tx-indexer/AGENTS.md', context, prompt)
            self.assertNotIn('projects/gno/AGENTS.md', context, prompt)
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review gnolang/gno#123'}))
        self.assertIn('projects/gno/AGENTS.md', context)
        self.assertNotIn('projects/tx-indexer/AGENTS.md', context)

    def test_a_repo_name_carrying_fixes_names_no_change_skill(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review acme/acme-fixes 12'}))
        self.assertIn('skills/review.md', context)
        for piece in ('skills/change.md', 'skills/pr-body.md', 'skills/issue.md'):
            self.assertNotIn(piece, context)

    def test_a_hyphenated_fix_still_names_the_change_skill(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'a hot-fix for the crash'}))
        self.assertIn('skills/change.md', context)

    def test_a_shortcut_word_past_the_head_names_nothing(self):
        for prompt in ('the finder cap sits where the last round left it, so fix nothing', 'a note on the writer: it reads every candidate, so simplify later',
                       'yes change both lines to samourai.coop', 'TLDR what did you change'):
            rc, context = self.run_hook('prompt', json.dumps({'prompt': prompt}))
            self.assertEqual((rc, context), (0, ''), prompt)

    def test_a_shortcut_word_in_the_head_fires_after_an_opener(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'Ok fix the conflict again, and we merge this time'}))
        self.assertIn('skills/change.md', context)

    def test_a_question_names_only_a_url_target(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'our todo will fix the cache read problem?'}))
        self.assertEqual((rc, context), (0, ''))
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'did you fix https://github.com/acme/acme/issues/76?'}))
        self.assertIn('skills/change.md', context)

    def test_try_names_its_skill_only_in_the_shortcut_shape(self):
        (self.root / 'skills' / 'try.md').write_text('# try\n')
        for prompt in ('try 4242 on gno', 'go in the workspace. Try 1498', 'try 1408 meet', 'boot meet',
                       'try https://github.com/acme/acme/pull/9', 'try the fix on meet', 'run the app on 1498', 'launch acme/acme#12'):
            rc, context = self.run_hook('prompt', json.dumps({'prompt': prompt}))
            self.assertIn('skills/try.md', context, prompt)
        for prompt in ('anything else? Try to deep to make that perfect', 'run the tests', 'launch the round', 'the run took 40 minutes',
                       'run it', 'try again', 'Ok I run both', 'and launch workflow', 'run a review on 4242',
                       'comments run 16 to 33 words', 'the idea to run workflows for people from outside', 'boot it',
                       'Write me a prompt so I can launch an agent on that subject'):
            rc, context = self.run_hook('prompt', json.dumps({'prompt': prompt}))
            self.assertNotIn('skills/try.md', context, prompt)

    def test_no_register_numbers_reach_the_next_prompt(self):
        transcript = self.root / 't.jsonl'
        drifted = ('The forged heading and the rule die, and the forged line does not, since the renderer '
                   'preserves the inline links by design, so a description can still print a line that reads '
                   'exactly like the one the page built, and the cost is real while the fix is not.')
        lines = [json.dumps({'type': 'user', 'message': {'content': 'why'}}),
                 json.dumps({'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': drifted}]}}),
                 json.dumps({'type': 'user', 'message': {'content': 'push'}})]
        transcript.write_text('\n'.join(lines) + '\n')
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'push', 'transcript_path': str(transcript)}))
        self.assertEqual(rc, 0)
        self.assertNotIn('articles per 100', context)
        self.assertNotIn('drifted from the register', context)

    def test_the_context_stays_under_the_hook_bound(self):
        rc, context = self.run_hook('prompt', json.dumps({'prompt': 'review fix issue report try skill gno meet'}))
        self.assertLess(len(context), 10000)

    def test_a_malformed_payload_is_quiet(self):
        rc, context = self.run_hook('prompt', 'not json')
        self.assertEqual((rc, context), (0, ''))


if __name__ == '__main__':
    unittest.main()


class PromptSections(GateCase):
    """A skill declaring prompt-sections is read as that cut, so the reader loads its moment's sections
    and not the stage sections some other moment needs."""

    FILE = ('---\nname: review\nprompt-sections: [Alpha, Gamma]\n---\n\n# Review\n\nIntro line.\n\n'
            '## Alpha\n\nkeep alpha\n\n### Alpha child\n\nkeep child\n\n'
            '## Beta\n\nDROP beta\n\n## Gamma\n\nkeep gamma\n')

    def declare(self, text=None):
        (self.root / 'skills' / 'review.md').write_text(text if text is not None else self.FILE)

    def test_resolve_returns_the_cut_and_drops_the_undeclared_section(self):
        self.declare()
        cut = gate.resolve('review')
        self.assertEqual(cut.name, 'review.md')
        self.assertIn('.skill-gate/sets', cut.as_posix())
        body = cut.read_text()
        self.assertIn('keep alpha', body)
        self.assertIn('keep child', body)      # a ### rides with its ## parent
        self.assertIn('keep gamma', body)
        self.assertNotIn('DROP beta', body)
        self.assertIn('# Review', body)        # the title and the intro survive the cut

    def test_no_declaration_resolves_to_the_file_itself(self):
        self.declare('# Review\n\n## Alpha\n\nbody\n')
        self.assertEqual(gate.resolve('review'), self.root / 'skills' / 'review.md')

    def test_a_renamed_heading_falls_back_to_the_whole_file(self):
        self.declare(self.FILE.replace('## Gamma', '## Delta'))
        self.assertEqual(gate.resolve('review'), self.root / 'skills' / 'review.md')

    def test_the_cut_refreshes_when_the_source_changes(self):
        self.declare()
        self.assertIn('keep gamma', gate.resolve('review').read_text())
        self.declare(self.FILE.replace('keep gamma', 'gamma rewritten'))
        self.assertIn('gamma rewritten', gate.resolve('review').read_text())

    def test_the_cut_records_as_a_read_of_the_skill(self):
        self.declare()
        self.assertEqual(gate.name_of(gate.resolve('review')), 'review')
        self.assertTrue(gate.record_read('review'))
        self.assertTrue(gate.is_read('review'))


class AlwaysWhole(PromptSections):
    """The skills every turn runs on are never cut, however they are declared: the harness carries them whole
    as the session opens, so a cut would record bytes the session never loaded."""

    def test_an_imported_skill_is_never_cut(self):
        (self.root / 'skills' / 'short-form.md').write_text(self.FILE)
        self.assertEqual(gate.resolve('short-form'), self.root / 'skills' / 'short-form.md')

    def test_a_claude_md_import_is_never_cut(self):
        (self.root / 'CLAUDE.md').write_text('@AGENTS.md\n@skills/writing-style.md\n')
        (self.root / 'skills' / 'writing-style.md').write_text(self.FILE)
        self.assertEqual(gate.resolve('writing-style'), self.root / 'skills' / 'writing-style.md')

    def test_a_skill_no_one_imports_still_cuts(self):
        (self.root / 'CLAUDE.md').write_text('@AGENTS.md\n')
        self.declare()
        self.assertIn('.skill-gate/sets', gate.resolve('review').as_posix())


class FencedHashIsNotAHeading(GateCase):
    """A `#` line inside a fenced block is content. Reading one as a heading ended the section at the fence and
    dropped the rest in silence, which cost skills/review.md#Overview its whole skeleton."""

    FILE = ('---\nname: review\nprompt-sections: [Alpha]\n---\n\n# Review\n\n'
            '## Alpha\n\nbefore\n\n```markdown\n# <the subject>\n## What it is for\n```\n\nafter\n\n'
            '## Beta\n\nDROP beta\n')

    def test_a_fenced_hash_does_not_end_the_section(self):
        body = gate.section(self.FILE, 'Alpha')
        self.assertIn('before', body)
        self.assertIn('after', body)          # the fence used to end it here
        self.assertIn('# <the subject>', body)
        self.assertNotIn('DROP beta', body)

    def test_the_cut_carries_the_whole_fenced_section(self):
        (self.root / 'skills' / 'review.md').write_text(self.FILE)
        body = gate.resolve('review').read_text()
        self.assertIn('after', body)
        self.assertNotIn('DROP beta', body)

    def test_a_tilde_fence_counts_too(self):
        body = gate.section(self.FILE.replace('```', '~~~'), 'Alpha')
        self.assertIn('after', body)


class IdentityRefusal(unittest.TestCase):
    def run_hook(self, command):
        out = io.StringIO()
        payload = {'tool_name': 'Bash', 'tool_input': {'command': command}}
        return gate.main(['hook-claude'], stdin=io.StringIO(json.dumps(payload)), stdout=out)

    def test_a_hand_set_identity_is_refused(self):
        self.assertEqual(self.run_hook('git -c user.name=x commit -m hi'), 2)
        self.assertEqual(self.run_hook('git commit -m hi --author="x <x@y>"'), 2)

    def test_a_message_quoting_the_words_passes(self):
        self.assertEqual(self.run_hook('./scripts/commit -m "gate: a commit that sets user.name or --author is refused" a.md'), 0)


class ModelNote(GateCase):
    def setUp(self):
        super().setUp()
        (self.root / 'skills' / 'thinking.md').write_text(
            '---\nname: thinking\neffort-set: [claude-opus-5*, claude-fable-5*]\n---\n\n# Thinking\n')

    def transcript(self, *models):
        path = self.root / 'transcript.jsonl'
        rows = [{'type': 'user', 'message': {'content': 'hi'}}]
        rows += [{'type': 'assistant', 'message': {'model': m}} for m in models]
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
        return {'transcript_path': str(path)}

    def test_model_id_drops_provider_version_and_context_suffix(self):
        self.assertEqual(gate.model_id('us.anthropic.claude-opus-5-5-v1:0'), 'claude-opus-5-5')
        self.assertEqual(gate.model_id('claude-opus-5-5[1m]'), 'claude-opus-5-5')
        self.assertEqual(gate.model_id('deepseek/deepseek-reasoner'), 'deepseek-reasoner')
        self.assertEqual(gate.model_id('claude-opus-4-5@20251101'), 'claude-opus-4-5')

    def test_payload_model_lifts_the_rules_once(self):
        note = gate.model_note({'model': 'claude-opus-5-5'})
        self.assertIn('does not apply', note)
        self.assertIsNone(gate.model_note({'model': 'claude-opus-5-5'}))

    def test_transcript_names_the_model_when_the_payload_does_not(self):
        self.assertIn('claude-fable-5-1', gate.model_note(self.transcript('deepseek-chat', 'claude-fable-5-1')))

    def test_synthetic_and_sidechain_entries_are_skipped(self):
        payload = self.transcript('claude-opus-5-5', '<synthetic>')
        with open(payload['transcript_path'], 'a') as f:
            f.write(json.dumps({'type': 'assistant', 'isSidechain': True, 'message': {'model': 'deepseek-chat'}}) + '\n')
        self.assertEqual(gate.session_model(payload), 'claude-opus-5-5')

    def test_a_model_outside_the_set_gets_no_line(self):
        self.assertIsNone(gate.model_note({'model': 'deepseek-reasoner'}))
        self.assertIsNone(gate.model_note({'model': 'claude-haiku-4-5'}))

    def test_moving_off_an_effort_set_model_restores_the_rules(self):
        gate.model_note({'model': 'claude-opus-5'})
        self.assertIn('applies again', gate.model_note({'model': 'deepseek-reasoner'}))

    def test_an_unnamed_model_keeps_the_rules(self):
        self.assertIsNone(gate.model_note({}))
        self.assertIsNone(gate.model_note({'transcript_path': str(self.root / 'missing.jsonl')}))

    def test_prompt_hook_prints_the_line(self):
        out = io.StringIO()
        gate.cmd_prompt(io.StringIO(json.dumps({'prompt': 'hello', **self.transcript('claude-opus-5-5')})), out)
        self.assertIn('does not apply', json.loads(out.getvalue())['hookSpecificOutput']['additionalContext'])
