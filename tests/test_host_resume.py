"""Host resumption at the public CLI and canonical workflow seams (simulated)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests import test_runlog as runlog_tests
from tests import test_canonical_gantry_workflow as canonical
SKILL_DIR = canonical.SKILL_DIR

EXECUTION = SKILL_DIR / 'scripts/execution.py'


class HostResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.state = Path(self.temp.name) / 'state'
        self.helper = runlog_tests.RunLogTests()
        self.helper.init_repository(self.root)
        self.unit = json.loads(self.helper.run_script(self.root, 'unit-id', '--cwd', str(self.root), '--json').stdout)['unitId']

    def append(self, event):
        result = self.helper.run_script(self.root, 'append', self.unit, '--state-root', str(self.state), event=event)
        self.assertEqual(0, result.returncode, result.stderr)

    def start(self, run='existing', host='claude-code'):
        event = self.helper.started(run)
        if host:
            event['data']['host'] = {'effectiveHost': host}
        self.append(event)

    def diagnose(self, host='codex', run='existing'):
        before = {str(p): p.read_bytes() for p in self.state.rglob('*') if p.is_file()}
        command = [sys.executable, str(EXECUTION), 'host', '--require-resolved', '--json', '--cwd', str(self.root), '--run-id', run, '--state-root', str(self.state)]
        if host:
            command += ['--host', host]
        result = subprocess.run(command, capture_output=True, text=True, env={**os.environ, 'CODEX_THREAD_ID': 'secret-hint', 'CLAUDECODE': 'secret-hint'})
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.state.rglob('*') if p.is_file()})
        return result, json.loads(result.stdout)

    def test_existing_run_comparison_is_read_only_and_never_resolves_invocation(self):
        self.start()
        result, data = self.diagnose()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({'runId': 'existing', 'previousHost': 'claude-code', 'effectiveHost': 'codex', 'decision': 'transition-required'}, data['resume'])
        result, data = self.diagnose('claude-code')
        self.assertEqual('unchanged', data['resume']['decision'])
        for host in (None, 'unsupported'):
            result, data = self.diagnose(host)
            self.assertEqual(1, result.returncode)
            self.assertIsNone(data['effectiveHost'])
            self.assertNotIn('secret-hint', result.stdout)

    def test_run_isolation_and_older_metadata_require_establishment(self):
        self.start(host=None)
        self.start('another', 'codex')
        result, data = self.diagnose()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('establishment-required', data['resume']['decision'])
        self.assertIsNone(data['resume']['previousHost'])
        result, data = self.diagnose(run='absent')
        self.assertEqual(1, result.returncode)
        self.assertEqual('invalid', data['status'])

    def test_transition_log_rejects_raw_provenance_and_wrong_previous_host(self):
        self.start()
        transition = {'oldHost': 'claude-code', 'newHost': 'codex', 'confirmationSource': 'invocation:operator-approved', 'tier': 'supported'}
        for altered in ({**transition, 'confirmationSource': 'secret-transcript'}, {**transition, 'oldHost': 'opencode'}, {**transition, 'raw': 'secret-transcript'}):
            result = self.helper.run_script(self.root, 'append', self.unit, '--state-root', str(self.state), event={'ts': '2026-10-01T00:00:00Z', 'run': 'existing', 'event': 'run.resumed', 'data': {'hostTransition': altered}})
            self.assertEqual(1, result.returncode)
        self.append({'ts': '2026-10-01T00:00:00Z', 'run': 'existing', 'event': 'run.resumed', 'data': {'hostTransition': transition}})
        result, data = self.diagnose()
        self.assertEqual('unchanged', data['resume']['decision'])
        self.assertEqual('codex', data['resume']['previousHost'])

    def workflow_args(self):
        helper = canonical.CanonicalGantryWorkflowTests()
        issue = helper.write_issue(self.root, 'resume#01', 'ready-for-agent')
        helper.write_roadmap(self.root)
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', 'commit', '-qm', 'fixture'], cwd=self.root, check=True)
        worktree = Path(self.temp.name) / 'issue'
        subprocess.run(['git', 'worktree', 'add', '-qb', 'gantry/resume-01', str(worktree)], cwd=self.root, check=True)
        self.start()
        self.append({'ts': '2026-10-01T00:00:00Z', 'run': 'existing', 'event': 'refutation', 'issue': 'resume#01', 'data': {}})
        self.append({'ts': '2026-10-01T00:00:01Z', 'run': 'existing', 'event': 'phase.started', 'issue': 'resume#01', 'phase': 'Implement', 'data': {'worktree': str(worktree)}})
        return dict(skillDir=str(SKILL_DIR), repoRoot=str(self.root), hostHarness='codex', runId='existing', unitId=self.unit,
                    stateRoot=str(self.state), round=2, isFirstRound=False, issues=[{'ref': 'resume#01', 'path': str(issue.relative_to(self.root)), 'title': 'Resume'}],
                    priorRun={'run': 'existing', 'issue': 'resume#01', 'worktree': str(worktree), 'branch': 'gantry/resume-01', 'correctionsSpent': 0},
                    branch='gantry/resume', baseRef='HEAD', isolate=True, correctionBudget=1, paths={},
                    models={'implement': 'custom-impl', 'review': 'custom-review', 'critic': 'custom-critic'},
                    roles={role: {'harness': 'codex', 'model': 'custom-' + role, 'effort': 'medium'} for role in ('implement', 'review', 'critic')},
                    policy={'git': {'prefix': 'gantry/', 'target': 'main'}, 'budget': {'corrections': 1}}, commandMode='real',
                    issueWorktree=str(worktree), issueBranch='gantry/resume-01', criticResult={'complete': False, 'refutations': ['still unproven'], 'requiredFixes': ['prove criterion']})

    def test_workflow_decline_is_read_only_and_approval_reuses_assignment_and_budget(self):
        args = self.workflow_args()
        before = {str(p): p.read_bytes() for p in Path(self.temp.name).rglob('*') if p.is_file()}
        helper = canonical.CanonicalGantryWorkflowTests()
        declined = helper.run_workflow('round-workflow.md', {**args, 'promptAnswers': ['no']})
        self.assertIn('declined', declined['error'])
        self.assertEqual([], declined['calls'])
        self.assertEqual([], declined['commandCalls'])
        self.assertIn('claude-code → codex', declined['prompts'][0])
        self.assertEqual(before, {str(p): p.read_bytes() for p in Path(self.temp.name).rglob('*') if p.is_file()})
        approved = helper.run_workflow('round-workflow.md', {**args, 'promptAnswers': ['yes']})
        self.assertIsNone(approved['error'], approved['error'])
        self.assertEqual('existing', approved['result']['runId'])
        self.assertEqual(1, approved['result']['results'][0]['corrections'])
        implementers = [c for c in approved['calls'] if c['label'].startswith('implement:')]
        self.assertEqual(1, len(implementers))
        self.assertEqual(args['issueWorktree'], implementers[0]['cwd'])
        self.assertEqual('custom-implement', implementers[0]['model'])
        self.assertFalse(any('worktree add' in c['command'] for c in approved['commandCalls']))
        events = [json.loads(line) for line in (self.state / self.unit / 'runs/existing.jsonl').read_text().splitlines()]
        self.assertEqual(1, sum(e['event'] == 'run.started' for e in events))
        transition = next(e['data']['hostTransition'] for e in events if e['event'] == 'run.resumed')
        self.assertEqual({'oldHost': 'claude-code', 'newHost': 'codex', 'confirmationSource': 'invocation:operator-approved', 'tier': 'supported'}, transition)
        spent = self.helper.run_script(self.root, 'corrections', self.unit, 'existing', 'resume#01', '--state-root', str(self.state), '--json')
        self.assertEqual(1, json.loads(spent.stdout)['correctionsSpent'])
        self.assertEqual(['existing.jsonl'], [p.name for p in (self.state / self.unit / 'runs').glob('*')])

    def test_workflow_unresolved_host_and_older_establishment_fail_closed(self):
        args = self.workflow_args()
        helper = canonical.CanonicalGantryWorkflowTests()
        for host in (None, 'unsupported'):
            result = helper.run_workflow('round-workflow.md', {**args, 'hostHarness': host, 'promptAnswers': ['yes']})
            self.assertIn('Host Harness', result['error'])
            self.assertEqual([], result['calls'])
            self.assertEqual([], result['commandCalls'])
        self.start('older', None)
        prior = {**args['priorRun'], 'run': 'older'}
        declined = helper.run_workflow('round-workflow.md', {**args, 'priorRun': prior, 'promptAnswers': ['no']})
        self.assertIn('unrecorded host → codex', declined['prompts'][0])
        self.assertEqual([], declined['calls'])
        approved = helper.run_workflow('round-workflow.md', {**args, 'priorRun': prior, 'promptAnswers': ['yes']})
        self.assertIsNone(approved['error'], approved['error'])
        result, data = self.diagnose(run='older')
        self.assertEqual('codex', data['resume']['previousHost'])
        result, data = self.diagnose(run='existing')
        self.assertEqual('claude-code', data['resume']['previousHost'])

    def test_linked_worktrees_share_unit_but_keep_run_host_metadata_isolated(self):
        self.start()
        self.start('parallel', 'opencode')
        linked = Path(self.temp.name) / 'parallel'
        subprocess.run(['git', 'worktree', 'add', '-qb', 'parallel', str(linked)], cwd=self.root, check=True)
        for root, run in ((self.root, 'existing'), (linked, 'parallel')):
            proc = self.helper.run_script(root, 'mark', run, '--cwd', str(root), '--state-root', str(self.state))
            self.assertEqual(0, proc.returncode, proc.stderr)
        self.append({'ts': '2026-10-01T00:00:00Z', 'run': 'existing', 'event': 'run.resumed', 'data': {'hostTransition': {'oldHost': 'claude-code', 'newHost': 'codex', 'confirmationSource': 'invocation:operator-approved', 'tier': 'supported'}}})
        original = self.root
        self.root = linked
        try:
            result, data = self.diagnose('opencode', 'parallel')
            self.assertEqual('unchanged', data['resume']['decision'])
            result, data = self.diagnose(None, 'parallel')
            self.assertEqual(1, result.returncode)
            self.assertIsNone(data['effectiveHost'])
        finally:
            self.root = original
        self.assertEqual('codex', self.diagnose()[1]['resume']['previousHost'])

    def test_resume_of_unstarted_correction_spends_budget_and_exhaustion_stops_work(self):
        args = self.workflow_args()
        args['roles'] = {role: {**selection, 'harness': 'claude-code'} for role, selection in args['roles'].items()}
        self.append({'ts': '2026-10-01T00:00:03Z', 'run': 'existing', 'event': 'refutation', 'issue': 'resume#01', 'data': {}})
        helper = canonical.CanonicalGantryWorkflowTests()
        exhausted = helper.run_workflow('round-workflow.md', {**args, 'hostHarness': 'claude-code'})
        self.assertIn('correction budget', exhausted['error'] or '')
        self.assertEqual([], exhausted['calls'])
        self.assertEqual([], exhausted['commandCalls'])
        allowed = helper.run_workflow('round-workflow.md', {**args, 'hostHarness': 'claude-code', 'correctionBudget': 2})
        self.assertIsNone(allowed['error'], allowed['error'])
        self.assertEqual(2, allowed['result']['results'][0]['corrections'])
        spent = self.helper.run_script(self.root, 'corrections', self.unit, 'existing', 'resume#01', '--state-root', str(self.state), '--json')
        self.assertEqual(2, json.loads(spent.stdout)['correctionsSpent'])

    def test_transition_rebinds_routing_without_changing_external_critic_selection(self):
        args = self.workflow_args()
        args['roles']['critic'] = {'harness': 'claude-code', 'model': 'external-custom', 'effort': 'high'}
        args['dispatchResults'] = [{'exitCode': 0, 'stdout': json.dumps({'complete': False, 'criteria': [], 'gatesVerdict': 'fail', 'gateResult': {'verdict': 'fail'}, 'gateFailures': ['unproven'], 'refutations': ['unproven'], 'requiredFixes': ['prove it'], 'decisionsForOperator': []}), 'stderr': ''}]
        result = canonical.CanonicalGantryWorkflowTests().run_workflow('round-workflow.md', {**args, 'promptAnswers': ['yes']})
        self.assertIsNone(result['error'], result['error'])
        self.assertEqual('supported', result['result']['hostResolution']['capabilities']['tier'])
        self.assertFalse(any(c['label'].startswith('critic:') for c in result['calls']))
        dispatch = next(c['command'] for c in result['commandCalls'] if 'execution.py" dispatch ' in c['command'])
        self.assertIn('"harness":"claude-code"', dispatch)
        self.assertIn('"model":"external-custom"', dispatch)
        self.assertIn('"effort":"high"', dispatch)
        events = [json.loads(line) for line in (self.state / self.unit / 'runs/existing.jsonl').read_text().splitlines()]
        selected = next(e['data']['effective'] for e in events if e['event'] == 'role.selected' and e['data']['role'] == 'critic')
        self.assertEqual(args['roles']['critic'], selected)
