# NOT AUDITED — AI-generated tooling. Review before executing in any privileged context.
#
# Behaviour of scripts/skill-gate.py: the refusal of a command that publishes
# without the user's slash command, and the pre-commit refusals.
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
from unittest import mock

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


    def test_other_tools_pass(self):
        rc, _ = self.run_hook({'tool_name': 'Read', 'tool_input': {'file_path': 'x'}})
        self.assertEqual(rc, 0)


class PublishWords(GateCase):
    """A publish, a push outside the standing list, a forced push and an AI marker wait for their word."""

    def turn(self, prompt, queued=()):
        """A transcript whose last turn opens on `prompt`; one opening on `/` is a slash command, recorded as the
        harness records one: `/p d` as <command-name>/p</command-name> and <command-args>d</command-args>."""
        path = self.root / 'transcript.jsonl'
        if prompt.startswith('/'):
            name, _, args = prompt.partition(' ')
            prompt = (f'<command-message>{name[1:]}</command-message>\n<command-name>{name}</command-name>\n'
                      f'<command-args>{args}</command-args>')
        rows = [{'type': 'user', 'message': {'role': 'user', 'content': 'an earlier turn: post'}},
                {'type': 'assistant', 'message': {'role': 'assistant', 'content': []}},
                {'type': 'user', 'message': {'role': 'user', 'content': prompt}, 'origin': {'kind': 'human'}},
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

    def test_a_post_waits_for_the_command_in_this_turn_only(self):
        post = 'gh pr comment 5 -R o/r -b hi'
        self.assertEqual(self.hook(post)[0], 2, 'the word in an earlier turn or in a tool result is not the word')
        self.assertEqual(self.hook(post, prompt='/post')[0], 0)
        self.assertEqual(self.hook(post, prompt='/post as ai')[0], 0, 'an argument that is no command changes nothing')
        self.assertEqual(self.hook(post, queued=['/post'])[0], 0, 'a command queued into the turn carries it')
        self.assertEqual(self.hook(post, queued=['post'])[0], 2, 'a queued word without its slash gives nothing')
        self.assertEqual(self.hook(post, prompt='ok go')[0], 2, 'a vague yes authorises nothing')

    def test_typed_prose_gives_nothing(self):
        post = 'gh pr comment 5 -R o/r -b hi'
        for prose in ('post', 'p', 'push', 'p d', 'PR 10 needs a rebase', 'Open questions', 'rai o/r#5',
                      'fix it\n/p', '<command-name>/p</command-name> in a sentence', 'see /p'):
            self.assertEqual(self.hook(post, prompt=prose)[0], 2, f'{prose!r}: typed prose is no command')

    def test_rai_carries_the_post_of_its_draft(self):
        post = './scripts/post-review.sh r/comment_m.md --as-ai'
        self.assertEqual(self.hook(post, prompt='/rai https://github.com/o/r/pull/5')[0], 0)
        self.assertEqual(self.hook('gh pr merge 5', prompt='/rai o/r#5')[0], 2, 'it carries the post alone')
        self.assertEqual(self.hook(post, prompt='/review https://github.com/o/r/pull/5')[0], 2, 'a review posts nothing')

    def test_fai_carries_the_push_and_the_replies(self):
        self.assertEqual(self.hook('gh pr comment 5 -R o/r -b hi', prompt='/fai o/r#5')[0], 0)
        self.assertEqual(self.hook('gh pr merge 5', prompt='/fai o/r#5')[0], 2, 'it merges nothing')
        self.assertEqual(self.hook('gh pr comment 5 -R o/r -b hi', prompt='fix as ai o/r#5')[0], 2, 'typed prose gives nothing')

    def test_each_command_gives_its_word_and_p_sends_it_all(self):
        post = 'gh pr comment 5 -R o/r -b hi'
        self.assertEqual(self.hook(post, prompt='/p')[0], 0, '/p sends the post it names')
        self.assertEqual(self.hook(post, prompt='/rlp')[0], 0, '/rlp sends what /p sends')
        self.assertEqual(self.hook(post, prompt='/m')[0], 2, 'merge does not post')
        self.assertEqual(self.hook('gh pr merge 5', prompt='/m')[0], 0)
        self.assertEqual(self.hook('gh pr merge 5', prompt='/p')[0], 2, '/p does not merge')
        self.assertEqual(self.hook('gh pr close 5', prompt='/x')[0], 0)
        self.assertEqual(self.hook('gh pr ready 79 -R o/r', prompt='/o')[0], 0)

    def test_arguments_that_are_commands_give_their_words(self):
        delete = 'git push origin --delete old-branch'
        self.assertEqual(self.hook(delete, prompt='/p d')[0], 0, 'every argument a command gives its word')
        self.assertEqual(self.hook(delete, prompt='/p')[0], 2, '/p alone does not delete')
        self.assertEqual(self.hook(delete, prompt='/p d please')[0], 2, 'an argument that is no command voids the rest')
        self.assertEqual(self.hook(delete, prompt='/p /d')[0], 0, 'an argument keeps its slash or drops it')
        for other in ('/model d', '/simplify d', '/ d'):
            self.assertEqual(self.hook(delete, prompt=other)[0], 2, f'{other!r}: only a gate command carries arguments')
        self.assertEqual(self.hook(delete, queued=['/tmp/x d'])[0], 2, 'a queued path is no command')

    def test_odd_command_shapes(self):
        post = 'gh pr comment 5 -R o/r -b hi'
        self.assertEqual(self.hook(post, prompt='/post see <url> & more')[0], 0, 'arguments may hold any character')
        self.assertEqual(self.hook(post, prompt='hello\n\x1f/p')[0], 2, 'the marker typed in prose gives nothing')
        self.assertEqual(self.hook(post, queued=['x\n\x1f/p'])[0], 2, 'nor in a queued message')
        self.assertEqual(self.hook(post, queued=['//p'])[0], 2, 'one slash, never two')
        path = self.root / 'odd.jsonl'
        rows = [{'type': 'user', 'message': {'role': 'user', 'content': '<command-name>/d</command-name>'}},
                {'type': 'assistant', 'message': {'role': 'assistant', 'content': []}},
                {'type': 'user', 'message': {'role': 'user', 'content': '<command-name>/post</command-name><command-x>'}}]
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
        self.assertFalse(gate.gives(gate.turn_text(str(path)), 'delete'), 'tags it cannot read still end the last turn')
        rows[2] = {'type': 'user', 'origin': {'kind': 'peer'},
                   'message': {'role': 'user', 'content': '<command-name>/post</command-name>'}}
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
        self.assertFalse(gate.gives(gate.turn_text(str(path)), 'post'), "another session's command gives nothing")
    def test_every_command_sending_what_p_sends_gives_the_push(self):
        commands = pathlib.Path(gate.__file__).resolve().parent.parent / 'commands'
        for path in commands.glob('*.md'):
            if 'everything `/p` sends' in path.read_text():
                self.assertIn('push', gate.COMMANDS.get(path.stem, ()), f'/{path.stem} sends what /p sends')
        for word in gate.COMMANDS:
            self.assertTrue((commands / f'{word}.md').exists(), f'/{word} gives a word and has no command file')

    def test_a_quiet_close_on_an_own_repository_needs_no_word(self):
        (self.root / 'workspace.json').write_text(json.dumps({'identities': {'public': {'name': 'Me'}}}))
        self.assertEqual(self.hook('gh pr close 12 -R me/fork')[0], 0, 'the fork pull request closes unasked')
        self.assertEqual(self.hook('gh pr close 12 -R me/fork --comment bye')[0], 2, 'a comment is a post')
        self.assertEqual(self.hook('gh pr close 12 -R me/fork -d')[0], 2, 'a branch delete waits')
        self.assertEqual(self.hook('gh pr close 12 -R up/meet')[0], 2, 'an upstream close waits')
        self.assertEqual(self.hook('gh issue close 3 -R me/fork')[0], 2, 'an issue close waits')

    def test_reads_dry_runs_and_an_open_pr_body_edit_pass(self):
        for cmd in ('gh pr view 5 -R o/r', 'gh api repos/o/r/pulls/5/comments --paginate',
                    "gh api graphql -f query='query{viewer{login}}'", 'gh api -X PATCH repos/o/r/pulls/5 -F body=@b.md',
                    './scripts/post-review.sh d.md --dry-run', 'git commit -m "quote gh pr comment | x"',
                    './scripts/post-fix.sh c --record-read'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)

    def test_writes_through_the_api_and_the_post_scripts_wait(self):
        for cmd in ('gh api repos/o/r/issues/1/comments -f body=x', "gh api graphql -f query='mutation{x}'",
                    './scripts/post-review.sh d.md', './scripts/post-replies o/r 5 d', 'gh issue create -R o/r -t t -b b',
                    './scripts/post-fix.sh c', './scripts/post-fix.sh c --pr-only'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)
        self.assertEqual(self.hook('gh pr merge 5', prompt='/post')[0], 2, 'a merge takes merge, not post')
        for cmd in ('gh api -X DELETE repos/o/r/issues/5/labels/class:hardfork',
                    'gh api -X DELETE repos/o/r/pulls/5/requested_reviewers -f "reviewers[]=a"'):
            self.assertEqual(self.hook(cmd, prompt='/post')[0], 0, f'taking a label off is an edit: {cmd}')
        self.assertEqual(self.hook('gh api -X DELETE repos/o/r/labels/bug', prompt='/post')[0], 2, 'deleting a label is a delete')
        self.assertEqual(self.hook('gh pr merge 5', prompt='/m')[0], 0)

    def test_an_ai_marker_is_refused_whatever_the_turn_says(self):
        rc, err = self.hook('git commit -m "fix\n\nCo-Authored-By: Claude <noreply@anthropic.com>"', prompt='/p post')
        self.assertEqual(rc, 2)
        self.assertIn('Invariant 7', err)

    def test_a_push_outside_the_standing_list_waits_for_push(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine, other = self.repo('https://github.com/me/private.git'), None
        self.assertEqual(self.hook(f'git -C {mine} push origin HEAD:main')[0], 0)
        shutil.rmtree(self.root / 'r')
        other = self.repo('https://github.com/me/public.git')
        self.assertEqual(self.hook(f'git -C {other} push origin HEAD:main')[0], 2)
        self.assertEqual(self.hook(f'git -C {other} push origin HEAD:main', prompt='/p')[0], 0)

    def test_a_forced_push_waits_for_force_even_on_a_standing_repo(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine = self.repo('https://github.com/me/private.git')
        self.assertEqual(self.hook(f'git -C {mine} push --force origin HEAD:main', prompt='/p')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push origin +HEAD:main', prompt='/p')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push --force origin HEAD:main', prompt='/pf')[0], 0)
        lease = f'git -C {mine} push --force-with-lease origin HEAD:main'
        for phrase in ('pf', '/p --force', '/p f'):
            self.assertEqual(self.hook(lease, prompt=phrase)[0], 2, f'{phrase!r}: one command per action, /pf')
        self.assertEqual(self.hook(lease, prompt='/pf')[0], 0)

    def test_a_retry_after_an_api_error_keeps_the_dead_turn_word(self):
        path = self.root / 'retry.jsonl'
        died = {'type': 'assistant', 'isApiErrorMessage': True, 'message': {'role': 'assistant', 'content': [
            {'type': 'text', 'text': "API Error: Can't reach the API server"}]}}
        replied = {'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': 'done'}]}}

        def turn(*rows):
            path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
            return gate.turn_text(str(path))

        def user(text):
            return {'type': 'user', 'message': {'role': 'user', 'content': text}}

        self.assertIn('merge 69', turn(user('merge 69'), died, user('Try again')))
        self.assertIn('merge 69', turn(user('merge 69'), died, user('Try again'), died, user('try again')))
        self.assertNotIn('merge 69', turn(user('merge 69'), replied, user('Try again')), 'a finished turn ends its word')
        self.assertNotIn('merge 69', turn(user('merge 69'), died, user('fix the test')), 'only a retry resumes it')

    def test_only_a_command_line_gives_a_word(self):
        for text in ('I want to verify before you push', 'post', '/post', 'fix it\n/m'):
            self.assertFalse(gate.gives(text, 'post') or gate.gives(text, 'merge'), text)
        self.assertTrue(gate.gives(gate.COMMAND + '/post \nall good?', 'post'), 'a question beside it keeps it')

    def test_a_question_asked_while_the_work_runs_keeps_the_word(self):
        path = self.root / 'asked.jsonl'
        replied = {'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': 'running'}]}}

        def turn(*rows):
            path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
            return gate.turn_text(str(path))

        def user(text, meta=False):
            return {'type': 'user', 'isMeta': meta, 'message': {'role': 'user', 'content': text}}

        def launched(task):
            return {'type': 'user', 'message': {'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': 't', 'content': f'Async agent launched. agentId: {task}'}]}}

        def notified(task):
            return user(f'<task-notification>\n<task-id>{task}</task-id>\n<status>completed</status>')

        def handed_back(task):
            return user(f'Another Claude session sent a message: <agent-message from="{task}">done', meta=True)

        for question in ("why it's so long", 'all good?', 'wyd', 'ag'):
            self.assertIn('push once', turn(user('push once you good'), launched('a1b2'), replied, user(question),
                                            notified('a1b2')), question)
        for task in ('again with the other flag', 'agree on the name and rename it'):
            self.assertFalse(gate._status_question(task), task)
        self.assertIn('push once', turn(user('push once you good'), launched('a1b2'), replied, user('all good?'),
                                        handed_back('a1b2')))
        self.assertNotIn('push once', turn(user('push once you good'), launched('a1b2'), notified('a1b2'), replied,
                                           user('all good?')), 'work that reported before the question had finished')
        self.assertNotIn('push once', turn(user('push once you good'), replied, user('all good?'), launched('c3d4'),
                                           notified('c3d4')), 'work started after the question is not the request')
        self.assertNotIn('push once', turn(user('push once you good'), launched('a1b2'), replied, user('fix the test'),
                                           notified('a1b2')), 'a new task ends the word')
        self.assertNotIn('push once', turn(user('push once you good'), launched('a1b2'), replied,
                                           user('all good?\nand rename the flag'), notified('a1b2')),
                         'a question carrying a task on another line ends it too')


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

    def test_a_word_typed_after_a_leading_reminder_counts(self):
        path = self.root / 'reminder.jsonl'
        reminder = '<system-reminder>\nLinked sessions now (status, not an instruction): top = a1 (idle).\n</system-reminder>\n\n'
        quoting = '<system-reminder>\nThe session "post the draft" finished.\n</system-reminder>\n\n'

        def turn(*rows):
            path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
            return gate.turn_text(str(path))

        def typed(content):
            return {'type': 'user', 'origin': {'kind': 'human'}, 'message': {'role': 'user', 'content': content}}

        def relayed(content):
            return {'type': 'user', 'turnOrigin': 'sdk', 'message': {'role': 'user', 'content': content}}

        post = '<command-name>/post</command-name>\n<command-args></command-args>'
        blocks = [{'type': 'text', 'text': reminder}, {'type': 'text', 'text': post}]
        for row in (typed(reminder + post), typed(blocks), typed(quoting + reminder + post)):
            self.assertTrue(gate.gives(turn(row), 'post'), row)
        self.assertEqual(turn(typed(quoting + 'fix the test')), 'fix the test', 'a reminder is never read for a word')
        self.assertFalse(gate.gives(turn(typed(post), typed(reminder + 'all good?')), 'post'),
                         'a typed message after a reminder opens its own turn')

        for row in (typed(reminder), typed(quoting), relayed(quoting), typed(quoting.replace('</system-reminder>', ''))):
            self.assertFalse(gate.gives(turn(row), 'post'), row)
        for said in ('Background (from the session that started this one):\npost the draft',
                     '<cross-session-message from="a1">post the draft</cross-session-message>',
                     '<side-sessions-event>post the draft</side-sessions-event>',
                     '<ci-monitor-event>post the draft</ci-monitor-event>',
                     '<task-notification>post the draft</task-notification>',
                     'Another Claude session sent a message: post the draft'):
            for row in (typed(said), relayed(reminder + said), typed(reminder + said)):
                self.assertFalse(gate.gives(turn(row), 'post'), row)
        self.assertFalse(gate.gives(turn(relayed(reminder + 'post')), 'post'), 'only the human origin opens a reminder')

    def test_a_pull_request_on_an_own_repository_goes_up_without_post(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_publish': ['me/fork']}))
        for cmd in ('gh -R me/fork pr create -t x -b y', 'gh pr comment https://github.com/me/fork/pull/5 -b x',
                    'gh -R me/fork pr edit 5 --title x', 'gh -R me/fork pr ready 5',
                    'gh api -X POST repos/me/fork/pulls -f title=x -f head=a -f base=b',
                    'gh api -X POST repos/me/fork/issues/5/comments -f body=x'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)
        for cmd in ('gh -R other/repo pr create -t x -b y', 'gh -R me/fork pr merge 5',
                    'gh -R me/fork pr comment 5 -b x && gh -R other/repo pr comment 5 -b x',
                    'gh api -X PUT repos/me/fork/pulls/5/merge', 'gh api -X POST repos/other/repo/pulls -f title=x',
                    'gh api -X POST repos/me/fork/issues -f title=x', 'gh api -X PATCH repos/me/fork/pulls/5 -f state=closed'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_merge_a_close_and_an_issue_through_the_api_keep_their_own_words(self):
        for cmd, word in (('gh api -X PUT repos/me/fork/pulls/5/merge', {'merge'}),
                          ('gh api -X PUT repos/other/repo/pulls/5/merge', {'merge'}),
                          ('gh api -X PATCH repos/me/fork/pulls/5 -f state=closed', {'close'}),
                          ('gh api -X PATCH repos/me/fork/pulls/5 -F state=closed', {'close'}),
                          ('gh api -X PATCH repos/me/fork/pulls/5 --field state=closed', {'close'}),
                          ('gh api -X PATCH repos/me/fork/pulls/5 -f state=open', {'post'}),
                          ('gh api -X PATCH repos/me/fork/pulls/5 --input /nonexistent/close.json', {'post'}),
                          ('gh api -X POST repos/me/fork/issues -f title=x', {'post'})):
            self.assertIn(word, gate.publish_words(cmd), cmd)
        body = self.root / 'close.json'
        body.write_text('{"state": "closed"}')
        self.assertIn({'close'}, gate.publish_words(f'gh api -X PATCH repos/me/fork/pulls/5 --input {body}'))

    def test_a_finished_round_goes_up_without_post_on_a_listed_repository(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_publish_review': ['up/fixes']}))
        listed, other = self.root / 'listed.md', self.root / 'other.md'
        listed.write_text('# Review: [#5](https://github.com/up/fixes/pull/5)\n')
        other.write_text('# Review: [#5](https://github.com/other/repo/pull/5)\n')
        self.assertEqual(gate.publish_words(f'./scripts/post-review.sh {listed} --as-ai'), [])
        for cmd in (f'./scripts/post-review.sh {listed}', f'./scripts/post-review.sh {other} --as-ai',
                    f'./scripts/post-review.sh {listed} --as-ai --event APPROVE',
                    f'./scripts/post-review.sh {self.root}/absent.md --as-ai'):
            self.assertEqual(gate.publish_words(cmd), [{'post', 'upload'}], cmd)

    def test_the_users_own_draft_goes_up_without_post_on_a_listed_repository(self):
        (self.root / 'workspace.json').write_text(json.dumps({
            'standing_publish_draft': ['up/fixes'], 'identities': {'public': {'name': 'me'}}}))
        pr = lambda n: {5: 'open\ttrue\tme', 6: 'open\tfalse\tme', 7: 'open\ttrue\tother'}.get(n)
        fake = lambda path, jq: pr(int(path.rsplit('/', 1)[1]))
        change = self.root / 'change'
        change.mkdir()
        (change / 'pr-body.md').write_text('Target: https://github.com/up/fixes/compare/develop...me:fixes:b\n')
        with mock.patch.object(gate, '_gh_api', fake):
            for cmd in ('gh pr create -R up/fixes --draft -t x -b y', 'gh pr comment 5 -R up/fixes -b x',
                        'gh pr comment https://github.com/up/fixes/pull/5 -b x', 'gh pr edit 5 -R up/fixes --title x',
                        'gh pr edit 5 -R up/fixes --add-label x', 'gh issue comment 5 -R up/fixes -b x',
                        'gh api -X POST repos/up/fixes/issues/5/comments -f body=x',
                        'gh api -X POST repos/up/fixes/issues/5/labels -f labels[]=x',
                        'gh api -X POST repos/up/fixes/pulls/5/comments/9/replies -f body=x',
                        'gh api -X PATCH repos/up/fixes/pulls/5 -f title=x',
                        './scripts/post-replies up/fixes 5 /tmp/replies', f'./scripts/post-fix.sh {change} --pr-only',
                        f'./scripts/post-fix.sh {change}'):
                self.assertEqual(self.hook(cmd)[0], 0, cmd)
            (change / 'issue.md').write_text('x')
            for cmd in ('gh pr create -R up/fixes -t x -b y', 'gh pr create -R other/repo --draft -t x -b y',
                        'gh pr comment 6 -R up/fixes -b x', 'gh pr comment 7 -R up/fixes -b x',
                        'gh pr comment -R up/fixes -b 5', 'gh pr comment 5 -R other/repo -b x',
                        'gh pr comment 5 -R up/fixes -b x && gh pr comment 6 -R up/fixes -b x',
                        'gh pr review 5 -R up/fixes --comment -b x', 'gh api -X POST repos/up/fixes/pulls/5/reviews -f event=COMMENT',
                        './scripts/post-review.sh d.md', 'gh pr ready 5 -R up/fixes', 'gh pr merge 5 -R up/fixes', 'gh pr close 5 -R up/fixes',
                        'gh issue create -R up/fixes -t x -b y', 'gh api -X PATCH repos/up/fixes/pulls/5 -f state=closed',
                        'gh api -X PATCH repos/up/fixes/pulls/5 -F draft=false', 'gh api -X PUT repos/up/fixes/pulls/5/merge',
                        'gh api -X POST repos/up/fixes/issues/6/comments -f body=x', './scripts/post-replies up/fixes 6 /tmp/replies',
                        f'./scripts/post-fix.sh {change}'):
                self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_failed_read_keeps_the_word_on_a_draft(self):
        (self.root / 'workspace.json').write_text(json.dumps({
            'standing_publish_draft': ['up/fixes'], 'identities': {'public': {'name': 'me'}}}))
        with mock.patch.object(gate, '_gh_api', lambda path, jq: None):
            self.assertEqual(self.hook('gh pr comment 5 -R up/fixes -b x')[0], 2)

    def test_a_listed_issues_body_goes_up_without_post(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_issue_edit': ['Up/Fixes#5']}))
        for cmd in ('gh issue edit 5 -R up/fixes --body-file b.md', 'gh issue edit 5 -R up/fixes -b x'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)
        for cmd in ('gh issue edit 6 -R up/fixes --body-file b.md', 'gh issue edit 5 -R other/repo --body-file b.md',
                    'gh issue edit 5 -R up/fixes --title x', 'gh issue edit 5 -R up/fixes --add-label x',
                    'gh issue close 5 -R up/fixes', 'gh issue comment 5 -R up/fixes -b x'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_every_change_still_waits_on_an_own_repository_that_asks_for_it(self):
        (self.root / 'workspace.json').write_text(
            json.dumps({'standing_publish': ['me/fork'], 'word_for_every_change': ['me/fork']}))
        self.assertEqual(self.hook('gh -R me/fork pr create -t x -b y')[0], 2)

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
        self.assertEqual(self.hook(both, prompt='/post')[0], 2)
        self.assertEqual(self.hook(both, prompt='/post m')[0], 0)
        self.assertEqual(self.hook(both, prompt='/post and m')[0], 2, 'an argument that is no command voids the rest')

    def test_combined_force_flags_and_mirror_are_forced(self):
        (self.root / 'workspace.json').write_text(json.dumps({'standing_push': ['me/private']}))
        mine = self.repo('https://github.com/me/private.git')
        for flag in ('-fu', '-uf', '--mirror'):
            self.assertEqual(self.hook(f'git -C {mine} push {flag} origin HEAD:main', prompt='/p')[0], 2, flag)

    def test_marker_forms_are_all_caught(self):
        for cmd in ('git commit --message="x\n\nCo-Authored-By: Claude"', 'git commit -m"Co-Authored-By: Copilot"',
                    'git commit -am "Co-Authored-By: a <noreply@anthropic.com>"',
                    'git commit -m x --trailer "Co-authored-by: dependabot[bot] <a@b>"'):
            self.assertEqual(self.hook(cmd, prompt='/p post')[0], 2, cmd)

    def test_a_human_reviewer_co_author_passes(self):
        cmd = 'git commit -m "fix\n\nCo-authored-by: Alex Doe <123+alexdoe@users.noreply.github.com>"'
        self.assertEqual(self.hook(cmd, prompt='/p post')[0], 0)


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
        heredoc = 'git commit -m "$(cat <<\'EOF\'\nfix\n\nCo-Authored-By: Claude <noreply@anthropic.com>\nEOF\n)"'
        self.assertEqual(self.hook(heredoc, prompt='/p')[0], 2)
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
        self.assertEqual(self.hook('gh api -X PUT repos/me/public/contents/a.png -f content=x', prompt='/upload')[0], 0)

    def test_a_branch_delete_waits_for_delete(self):
        mine = self.standing()
        self.assertEqual(self.hook(f'git -C {mine} push origin --delete old')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push origin :old')[0], 2)
        self.assertEqual(self.hook(f'git -C {mine} push origin :old', prompt='/d')[0], 0)

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
        self.assertEqual(self.hook('gh repo sync me/fork', prompt='/p')[0], 0)
        self.assertEqual(self.hook('gh repo sync me/fork --force', prompt='/p')[0], 2)
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

    def test_the_post_wrapper_waits_and_a_body_apply_runs_on_any_repo(self):
        # pr-body-apply refuses a pull request the user did not author, so it takes no word.
        self.assertEqual(self.hook('./scripts/post d.md')[0], 2)
        (self.root / 'workspace.json').write_text(json.dumps({'word_for_every_change': ['up/strict']}))
        (self.root / 'b.md').write_text('# PR\nTarget: https://github.com/up/strict/pull/4\n')
        (self.root / 'c.md').write_text('# PR\nTarget: https://github.com/up/loose/pull/4\n')
        self.assertEqual(self.hook('./scripts/pr-body-apply b.md')[0], 0)
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

    def test_a_graphql_variable_is_no_shell_expansion(self):
        read = ("gh api graphql -f query='query($org: String!, $first: Int = 50) { organization(login: $org) "
                "{ projectV2(number: 3) { fields(first: $first) { nodes { ... on ProjectV2Field { name } } } } } }'")
        self.assertEqual(self.hook(read)[0], 0, 'a variable left to its default is still a read')
        self.assertEqual(self.hook(read.replace('query(', 'mutation(', 1))[0], 2)
        for cmd in ('gh api graphql -f query="$OP { addComment(input: {}) { clientMutationId } }"',
                    'gh api graphql -f query="query { x } $MORE"'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_pr_edit_beyond_its_body_waits(self):
        self.assertEqual(self.hook('gh pr edit 5 -R o/r --body x')[0], 0)
        self.assertEqual(self.hook("gh pr edit 5 -R o/r --body-file - <<'MD'\nbody\nMD")[0], 0)
        for cmd in ('gh pr edit 5 -R o/r --title t', 'gh pr edit 5 -R o/r --add-label l', 'gh pr edit 5 --add-reviewer me'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_redirect_is_never_an_argument(self):
        cmd = 'git init -q --bare /tmp/rp.git && git clone -q /tmp/rp.git /tmp/rp-w 2>/dev/null && git -C /tmp/rp-w push origin HEAD'
        self.assertEqual(self.hook(cmd)[0], 0)


class PublishWordsRoundNine(PublishWordsRoundEight):
    """What the ninth check round found."""

    def test_a_quoted_body_starting_with_an_angle_keeps_its_place(self):
        for cmd in ('gh pr edit 5 -R o/r --body "<!-- template -->" --title "fix: y"', 'gh pr edit 5 -R o/r --body "> q" --base main',
                    'gh pr edit 5 -R o/r -b "<details>x</details>" --add-reviewer me'):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)
        self.assertEqual(self.hook('gh pr edit 5 -R o/r --body "<!-- template -->"')[0], 0)

    def test_the_rest_path_frees_the_body_alone(self):
        self.assertEqual(self.hook('gh api -X PATCH repos/o/r/pulls/68 -f title="fix: y"')[0], 2)
        self.assertEqual(self.hook('for n in 67 68; do gh api --method PATCH repos/o/r/pulls/$n -F body=@new_$n.md; done')[0], 0)

    def test_help_publishes_nothing(self):
        for cmd in ('./scripts/post-pr-review.py --help', './scripts/post-review.sh -h', './scripts/post --help',
                    './scripts/post-replies o/r 5 d --dry-run'):
            self.assertEqual(self.hook(cmd)[0], 0, cmd)


class PublishWordsRoundTen(PublishWordsRoundNine):
    """What the tenth check round found."""

    def test_a_script_file_or_heredoc_run_by_a_shell_is_read(self):
        other = self.repo('https://github.com/me/public.git')
        (self.root / 'p.sh').write_text(f'cd {other}\ngit push origin HEAD:x\n')
        self.assertEqual(self.hook(f'bash {self.root}/p.sh')[0], 2)
        self.assertEqual(self.hook(f"cat > {self.root}/q.sh <<'SH'\ncd {other}\ngit push origin HEAD:x\nSH\nbash {self.root}/q.sh")[0], 2)
        self.assertEqual(self.hook(f"bash <<'EOF'\ncd {other}\ngit push origin fix-x\nEOF")[0], 2)
        (self.root / 'ok.sh').write_text('echo hello\n')
        self.assertEqual(self.hook(f'bash {self.root}/ok.sh')[0], 0)
        self.assertEqual(self.hook(f'bash -n {self.root}/p.sh')[0], 0, 'a syntax check runs nothing')
        (self.root / 'scripts').mkdir(exist_ok=True)
        (self.root / 'scripts' / 'verb.sh').write_text(f'cd {other}\ngit push origin HEAD:x\n')
        self.assertEqual(self.hook(f'bash {self.root}/scripts/verb.sh')[0], 0, "the workspace's own tooling is not read")
        py = f"python3 - <<'PY'\nimport os\nos.system('git push')\nPY\nbash -n {self.root}/p.sh"
        self.assertEqual(self.hook(py)[0], 0, 'a python heredoc is not a shell script')

    def test_a_repository_in_a_variable_is_filled(self):
        (self.root / 'workspace.json').write_text(json.dumps({'word_for_every_change': ['up/strict']}))
        self.assertEqual(self.hook('R=up/strict; gh api -X PATCH repos/$R/pulls/6 -F body=@b.md')[0], 2)
        self.assertEqual(self.hook('R=up/strict; gh pr edit 6 -R "$R" --body-file b.md')[0], 2)


class PublishWordsRoundEleven(PublishWordsRoundTen):
    """What the eleventh check round found."""

    def test_shell_option_values_are_not_the_script(self):
        other = self.repo('https://github.com/me/public.git')
        (self.root / 'p.sh').write_text(f'cd {other}\ngit push origin HEAD:x\n')
        for cmd in (f'bash -euo pipefail {self.root}/p.sh', f'bash -O extglob {self.root}/p.sh',
                    f"bash -euo pipefail <<'EOF'\ncd {other}\ngit push origin x\nEOF",
                    f"bash -eo pipefail -c 'cd {other} && git push origin fix-x'"):
            self.assertEqual(self.hook(cmd)[0], 2, cmd)

    def test_a_relative_script_resolves_where_the_line_stands(self):
        other = self.repo('https://github.com/me/public.git')
        (self.root / 'sub').mkdir()
        (self.root / 'sub' / 'p.sh').write_text(f'cd {other}\ngit push origin HEAD:x\n')
        self.assertEqual(self.hook(f'cd {self.root}/sub && bash ./p.sh', cwd='/')[0], 2)

    def test_text_after_exit_is_not_shell(self):
        (self.root / 't.sh').write_text("echo ok\nexit 0\npost = read_post(readme)\ngh pr comment 5 -b x\n")
        self.assertEqual(self.hook(f'sh {self.root}/t.sh')[0], 0)

    def test_a_script_cd_ends_with_the_script(self):
        mine = self.standing()
        other = self.root / 'o2'
        subprocess.run(['git', 'init', '-q', str(other)], check=True)
        subprocess.run(['git', '-C', str(other), 'remote', 'add', 'origin', 'https://github.com/me/public.git'], check=True)
        (self.root / 'cdws.sh').write_text(f'cd {mine}\n')
        self.assertEqual(self.hook(f'cd {other} && bash {self.root}/cdws.sh && git push origin fix-x')[0], 2)

    def test_an_unreadable_path_neither_hangs_nor_crashes(self):
        fifo = self.root / 'fifo'
        os.mkfifo(fifo)
        self.assertEqual(self.hook(f'bash {fifo}')[0], 0)
        self.assertIn(self.hook('bash /tmp/a\x00b.sh; git push origin x')[0], (0, 2))


class DraftPullRequestPush(GateCase):
    """A draft pull request's branch goes up unasked on the user's own repository, and a ready one's waits for push
    where the standing word covers drafts alone; no pull request, or no answer from GitHub, keeps the standing list's."""

    turn, hook, repo = PublishWords.turn, PublishWords.hook, PublishWords.repo

    def setUp(self):
        super().setUp()
        (self.root / 'workspace.json').write_text(json.dumps({
            'identities': {'public': {'name': 'Me'}},
            'standing_push': ['me/private', 'me/fixes'], 'standing_push_draft': ['me/fixes']}))
        self.calls = []

    def github(self, draft, parent='up/gno', on=None):
        """GitHub as `gh api` answers it: True a draft, False a ready pull request, None none, 'offline' no answer;
        the pull request opens on `on`, the parent unless named."""
        def api(path, jq):
            self.calls.append(path)
            if draft == 'offline':
                return None
            if '/pulls?' not in path:
                return parent + '\n'
            return '' if draft is None or not path.startswith(f'repos/{on or parent}/') else f'{str(draft).lower()}\n'
        return mock.patch.object(gate, '_gh_api', api)

    def push(self, url, refspec='HEAD:refs/heads/docs/x', prompt='fix it'):
        shutil.rmtree(self.root / 'r', ignore_errors=True)
        return self.hook(f'git -C {self.repo(url)} push origin {refspec}', prompt=prompt)

    def test_a_draft_branch_on_an_own_fork_goes_up_unasked(self):
        with self.github(True):
            self.assertEqual(self.push('https://github.com/me/gno.git')[0], 0)
            self.assertIn('repos/up/gno/pulls?state=open&per_page=100&head=me%3Adocs%2Fx', self.calls)
            self.assertEqual(self.push('https://github.com/me/gno.git', refspec='docs/x')[0], 0)
            self.assertEqual(self.push('https://github.com/me/gno.git', refspec='--force HEAD:docs/x')[0], 2,
                             'a forced push still waits for force')

    def test_a_bare_push_asks_for_the_checked_out_branch(self):
        repo = self.repo('https://github.com/me/gno.git')
        subprocess.run(['git', '-C', repo, 'symbolic-ref', 'HEAD', 'refs/heads/docs/x'], check=True)
        with self.github(True):
            self.assertEqual(self.hook(f'git -C {repo} push -u origin')[0], 0)
        self.assertTrue(any('head=me%3Adocs%2Fx' in c for c in self.calls))

    def test_a_ready_branch_no_pull_request_or_no_answer_waits_for_push_on_an_own_fork(self):
        for state in (False, None, 'offline'):
            with self.github(state):
                self.assertEqual(self.push('https://github.com/me/gno.git')[0], 2, state)
                self.assertEqual(self.push('https://github.com/me/gno.git', prompt='/p')[0], 0, state)

    def test_a_ready_branch_waits_for_push_where_the_standing_word_covers_drafts_alone(self):
        with self.github(False, parent='up/fixes'):
            rc, err = self.push('https://github.com/me/fixes.git')
            self.assertEqual(rc, 2)
            self.assertIn('ready pull request', err)
            self.assertEqual(self.push('https://github.com/me/fixes.git', prompt='/p')[0], 0)
        for state in (True, None, 'offline'):
            with self.github(state, parent='up/fixes'):
                self.assertEqual(self.push('https://github.com/me/fixes.git')[0], 0, state)

    def test_a_full_standing_word_and_a_repository_the_user_does_not_own_ask_github_nothing(self):
        with self.github(False):
            self.assertEqual(self.push('https://github.com/me/private.git')[0], 0)
            self.assertEqual(self.push('https://github.com/up/gno.git')[0], 2)
        self.assertEqual(self.calls, [])

    def test_a_pull_request_on_the_fork_itself_counts(self):
        with self.github(True, on='me/gno'):
            self.assertEqual(self.push('https://github.com/me/gno.git')[0], 0)

    def test_a_call_that_hangs_is_no_answer(self):
        with mock.patch.object(gate.subprocess, 'run', side_effect=subprocess.TimeoutExpired('gh', 5)):
            self.assertIsNone(gate._gh_api('repos/me/gno', '.parent.full_name'))
        with mock.patch.object(gate.subprocess, 'run', side_effect=FileNotFoundError('gh')):
            self.assertIsNone(gate._gh_api('repos/me/gno', '.parent.full_name'))


class PreCommitRefusals(GateCase):
    def _repo(self):
        repo = self.root
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
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

    def test_a_gitlink_the_remote_holds_passes_once_stale_refs_are_fetched(self):
        repo = self._repo()
        env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x'}
        origin = self.root / 'origin'
        subprocess.run(['git', 'init', '-q', '-b', 'main', str(origin)], check=True)
        subprocess.run(['git', '-C', str(origin), 'commit', '-q', '--allow-empty', '-m', 'one'], check=True, env=env)
        sub = repo / 'sub'
        subprocess.run(['git', 'clone', '-q', str(origin), str(sub)], check=True)
        # the remote moves after the clone: the submodule's refs do not know the new commit yet
        subprocess.run(['git', '-C', str(origin), 'commit', '-q', '--allow-empty', '-m', 'two'], check=True, env=env)
        sha = subprocess.run(['git', '-C', str(origin), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(['git', '-C', str(repo), 'update-index', '--add', '--cacheinfo', f'160000,{sha},sub'], check=True)
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(gate.main(['pre-commit'], cwd=str(repo)), 0, err.getvalue())

    def test_a_held_gitlink_passes_from_a_linked_worktree(self):
        repo = self._repo()
        env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x'}
        subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-n', '--allow-empty', '-m', 'base'], check=True, env=env)
        wt = self.root / 'wt'
        subprocess.run(['git', '-C', str(repo), 'worktree', 'add', '-q', '--detach', str(wt)], check=True)
        sub = wt / 'sub'
        subprocess.run(['git', 'init', '-q', str(sub)], check=True)
        subprocess.run(['git', '-C', str(sub), 'commit', '-q', '--allow-empty', '-m', 'one'], check=True, env=env)
        sha = subprocess.run(['git', '-C', str(sub), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(['git', '-C', str(sub), 'update-ref', 'refs/remotes/origin/main', sha], check=True)
        subprocess.run(['git', '-C', str(wt), 'update-index', '--add', '--cacheinfo', f'160000,{sha},sub'], check=True)
        # What git hands a pre-commit hook in a linked worktree: an absolute GIT_DIR and index.
        hook_env = {'GIT_DIR': str(repo / '.git' / 'worktrees' / 'wt'),
                    'GIT_INDEX_FILE': str(repo / '.git' / 'worktrees' / 'wt' / 'index')}
        err = io.StringIO()
        with mock.patch.dict(os.environ, hook_env), redirect_stderr(err):
            rc = gate.main(['pre-commit'], cwd=str(wt))
        self.assertEqual(rc, 0, err.getvalue())


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


if __name__ == '__main__':
    unittest.main()


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


