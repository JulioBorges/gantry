"""Technical Plan contracts exercised through real CLI processes and Git checkouts."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import test_canonical_gantry_workflow as canonical
SCRIPTS = canonical.SCRIPTS


class TechnicalPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = canonical.CanonicalGantryWorkflowTests()
        self.fixture.init_repo(self.root)
        self.issue = self.fixture.write_issue(self.root, 'ground#01', 'ready-for-agent', criteria=['Preserve behavior', 'Verify delivery'])
        self.spec = self.root / '.scratch/ground/spec.md'
        self.spec.write_text('# Approved Spec\nPreserve behavior.\n')
        (self.root / 'source.py').write_text('def existing():\n    return True\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.identity = {'worktree': str(self.root), 'revision': self.git('rev-parse', 'HEAD'),
                         'issue': '.scratch/ground/issues/01-example.md', 'spec': '.scratch/ground/spec.md'}
        self.plan = {'input': self.identity, 'findings': [{'path': 'source.py', 'line': 1, 'behavior': 'existing returns True'}],
                     'reuse': ['Keep existing() as the behavior boundary'],
                     'changes': ['Extend existing() only if the criterion requires it'],
                     'coverage': [{'index': i, 'changes': ['source.py: existing()'], 'tests': ['Run the real workflow fixture']} for i in [1, 2]],
                     'adjustments': [], 'conflicts': []}

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def validate(self, plan):
        return subprocess.run([sys.executable, str(SCRIPTS / 'result.py'), '--role', 'technical-planner',
                               '--cwd', str(self.root), '--issue', str(self.issue), '--json'],
                              input=json.dumps(plan), text=True, capture_output=True)

    def test_public_validation_requires_grounded_source_and_complete_coverage(self):
        valid = self.validate(self.plan)
        self.assertEqual(0, valid.returncode, valid.stderr + valid.stdout)
        self.plan['findings'][0]['path'] = 'invented.py'
        invalid = self.validate(self.plan)
        self.assertEqual(1, invalid.returncode, invalid.stderr + invalid.stdout)
        self.assertIn('source', invalid.stdout)

    def test_missing_coverage_empty_evidence_and_decomposition_results_are_rejected(self):
        import copy
        for edit in ('coverage', 'empty', 'legacy', 'identity', 'line'):
            with self.subTest(edit=edit):
                plan = copy.deepcopy(self.plan)
                if edit == 'coverage': plan['coverage'].pop()
                if edit == 'empty': plan['changes'] = ['   ']
                if edit == 'legacy': plan = {'filesWritten': [], 'issues': [], 'roadmapAdditions': [], 'openDecisions': []}
                if edit == 'identity': plan['input']['worktree'] = '/other-checkout'
                if edit == 'line': plan['findings'][0]['line'] = 999
                invalid = self.validate(plan)
                self.assertEqual(1, invalid.returncode, invalid.stderr + invalid.stdout)

    def test_checkout_checkpoint_detects_committed_and_untracked_edits_and_retains_no_plan_in_git(self):
        capture = self.cli('capture')
        self.assertEqual(0, capture.returncode, capture.stderr)
        baseline = json.loads(capture.stdout)
        accepted = self.cli('accept', {'baseline': baseline, 'plan': self.plan})
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        artifact = Path(json.loads(accepted.stdout)['artifact'])
        self.assertTrue(artifact.is_file())
        self.assertFalse(artifact.is_relative_to(self.root))
        self.assertEqual(self.plan, json.loads(artifact.read_text())['plan'])
        (self.root / 'untracked.txt').write_text('unexpected planner edit')
        refused = self.cli('accept', {'baseline': baseline, 'plan': self.plan})
        self.assertEqual(1, refused.returncode, refused.stderr)
        self.assertIn('changed', refused.stdout)
        self.git('add', '.')
        self.git('commit', '-qm', 'unexpected planner commit')
        self.assertEqual(1, self.cli('accept', {'baseline': baseline, 'plan': self.plan}).returncode)

    def cli(self, action, payload=None):
        return subprocess.run([sys.executable, str(SCRIPTS / 'technical_plan.py'), action,
                               '--cwd', str(self.root), '--issue', str(self.issue),
                               '--state-root', str(self.root.parent / (self.root.name + '-state'))],
                              input=json.dumps(payload) if payload is not None else None, text=True, capture_output=True)


    def workflow(self, **extra):
        self.fixture.write_roadmap(self.root)
        (self.root / 'Makefile').write_text('test:\n\t@true\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'workflow fixture')
        args = {'round': 1, 'issues': [{'ref':'ground#01', 'path':str(self.issue.relative_to(self.root)),
                'specPath':str(self.spec.relative_to(self.root)), 'title':'Ground first implementation'}],
                'models':{'implement':'selected-model','review':'review','critic':'critic'},
                'roles':{'implement':{'harness':'claude-code','model':'selected-model','effort':'medium'}},
                'branch':self.git('branch','--show-current'), 'baseRef':'HEAD', 'isolate':False,
                'correctionBudget':0, 'skillDir':str(canonical.SKILL_DIR), 'repoRoot':str(self.root),
                'policy':{'git':{'target':'main','prefix':'gantry/'}}, 'paths':{}, 'commandMode':'real',
                'criticResult':{'criteria':self.fixture.critic_evidence(self.root,self.issue)}, **extra}
        return self.fixture.run_workflow('round-workflow.md', args)

    def test_assigned_checkout_plans_before_separate_implementer_and_independent_verification(self):
        out = self.workflow()
        self.assertIsNone(out['error'])
        self.assertEqual(['technical-plan:ground#01', 'implement:ground#01', 'review:ground#01', 'critic:ground#01#1'],
                         [call['label'] for call in out['calls']])
        plan, implement = out['calls'][:2]
        self.assertEqual(plan['cwd'], implement['cwd'])
        self.assertEqual(('selected-model','medium'), (plan['model'],plan['effort']))
        self.assertEqual(plan['selection'], implement['selection'])
        self.assertIn('Accepted Technical Plan', implement['prompt'])
        self.assertEqual('done', out['result']['results'][0]['outcome'])

    def test_missing_plan_uses_one_protocol_reask_and_never_releases_implementation(self):
        out = self.workflow(technicalPlanRawResults=[None, None])
        self.assertIsNone(out['error'])
        self.assertEqual(['technical-plan:ground#01', 'technical-plan:ground#01:retry'], [c['label'] for c in out['calls']])
        delivery = out['result']['results'][0]
        self.assertEqual(('paused', 'protocol_failure', 0), (delivery['outcome'],delivery['reason'],delivery['corrections']))

    def test_scope_conflict_waits_for_operator_without_edits(self):
        before = self.issue.read_bytes(), self.spec.read_bytes(), (self.root/'source.py').read_bytes()
        out = self.workflow(technicalPlanConflicts=['Source contract contradicts approved Spec; operator must choose'])
        self.assertIsNone(out['error'])
        self.assertEqual(['technical-plan:ground#01'], [c['label'] for c in out['calls']])
        self.assertEqual('needs_operator', out['result']['results'][0]['reason'])
        self.assertEqual(before, (self.issue.read_bytes(),self.spec.read_bytes(),(self.root/'source.py').read_bytes()))
        self.assertEqual('', self.git('status','--porcelain'))

    def test_unexpected_checkout_edit_refuses_handoff_and_preserves_evidence(self):
        out = self.workflow(technicalPlanEdit=True)
        self.assertIsNone(out['error'])
        self.assertEqual(['technical-plan:ground#01'], [c['label'] for c in out['calls']])
        delivery = out['result']['results'][0]
        self.assertEqual('checkout_changed', delivery['reason'])
        self.assertIn('universal filesystem enforcement', delivery['error'])
        self.assertEqual('planner edit', (self.root/'unexpected.txt').read_text())
