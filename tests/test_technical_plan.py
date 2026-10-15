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
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
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
        if self.git('status','--porcelain'):
            self.git('commit', '-qm', 'workflow fixture')
        args = {'round': 1, 'issues': [{'ref':'ground#01', 'path':str(self.issue.relative_to(self.root)),
                'specPath':str(self.spec.relative_to(self.root)), 'title':'Ground first implementation'}],
                'models':{'implement':'selected-model','review':'review','critic':'critic'},
                'roles':{'implement':{'harness':'claude-code','model':'selected-model','effort':'medium'}},
                'branch':self.git('branch','--show-current'), 'baseRef':'HEAD', 'isolate':False,
                'correctionBudget':0, 'skillDir':str(canonical.SKILL_DIR), 'repoRoot':str(self.root),
                'stateRoot':str(self.root.parent/'state'), 'policy':{'git':{'target':'main','prefix':'gantry/'}}, 'paths':{}, 'commandMode':'real',
                'technicalPlanSource':'source.py', 'criticResult':{'criteria':self.fixture.critic_evidence(self.root,self.issue)}, **extra}
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

    def test_bounded_dispatch_uses_implement_identity_and_read_only_codex_process(self):
        import os
        binary_dir = self.root / 'bin'
        binary_dir.mkdir()
        binary = binary_dir / 'codex'
        binary.write_text(f'#!{sys.executable}\n' + '''import json, sys
from pathlib import Path
if '--version' in sys.argv:
    print('codex 99.0.0')
else:
    Path('invocation.json').write_text(json.dumps(sys.argv))
    plan = json.loads(Path('response.json').read_text())
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps(plan)}}))
    print(json.dumps({'type':'turn.completed'}))
''')
        binary.chmod(0o755)
        (self.root/'response.json').write_text(json.dumps(self.plan))
        command = [sys.executable, str(SCRIPTS/'execution.py'), 'dispatch', '--role','technical-planner',
                   '--cwd',str(self.root), '--selection',json.dumps({'harness':'codex','model':'chosen-model','effort':'medium'})]
        completed = subprocess.run(command, input='Inspect without editing', text=True, capture_output=True,
                                   env={**os.environ, 'PATH':str(binary_dir)+os.pathsep+os.environ['PATH']})
        self.assertEqual(0,completed.returncode,completed.stderr)
        invocation = json.loads((self.root/'invocation.json').read_text())
        self.assertEqual('chosen-model',invocation[invocation.index('--model')+1])
        self.assertIn('model_reasoning_effort="medium"',invocation)
        self.assertEqual('read-only',invocation[invocation.index('--sandbox')+1])
        self.assertEqual(self.plan,json.loads(completed.stdout))


    def test_two_assigned_issue_chains_advance_without_a_planning_barrier(self):
        second = self.fixture.write_issue(self.root, 'ground#02', 'ready-for-agent', criteria=['Independent delivery'])
        assignments = {f'ground#{i:02d}':{'worktree':f'{self.root}.gantry-ground-{i:02d}', 'branch':f'gantry/ground-{i:02d}'} for i in [1,2]}
        issues = [{'ref':f'ground#{i:02d}', 'path':str(path.relative_to(self.root)),
                   'specPath':str(self.spec.relative_to(self.root)), 'title':'Independent Issue'} for i,path in [(1,self.issue),(2,second)]]
        out = self.workflow(issues=issues, isolate=True, interleavePlans=True, issueAssignments=assignments)
        self.assertIsNone(out['error'])
        labels = [c['label'] for c in out['calls']]
        self.assertLess(labels.index('technical-plan:ground#02'), labels.index('implement:ground#01'))
        self.assertLess(labels.index('implement:ground#01'), labels.index('implement:ground#02'))
        for ref, assigned in assignments.items():
            chain = [c for c in out['calls'] if c['label'] in [f'technical-plan:{ref}',f'implement:{ref}']]
            self.assertEqual([assigned['worktree']]*2, [c['cwd'] for c in chain])
        self.assertTrue(all(any(c['label'].startswith(f'critic:{ref}') for c in out['calls']) for ref in assignments))


    def test_invalid_grounding_cannot_bypass_native_structured_output(self):
        for defect in ['source', 'coverage']:
            with self.subTest(defect=defect):
                out = self.workflow(technicalPlanDefect=defect, structuredOutput=True)
                self.assertIsNone(out['error'])
                self.assertEqual(['technical-plan:ground#01','technical-plan:ground#01:retry'], [c['label'] for c in out['calls']])
                self.assertEqual('protocol_failure', out['result']['results'][0]['reason'])

    def test_checkpoint_observes_approved_inputs_even_when_tracker_files_are_ignored(self):
        (self.root/'.gitignore').write_text('.scratch/\n')
        self.git('rm','--cached','-r','.scratch')
        self.git('add','.gitignore')
        self.git('commit','-qm','machine-local tracker fixture')
        self.plan['input']['revision'] = self.git('rev-parse','HEAD')
        baseline = json.loads(self.cli('capture').stdout)
        self.spec.write_text('# Unexpected change to approved scope\n')
        refused = self.cli('accept', {'baseline':baseline,'plan':self.plan})
        self.assertEqual(1,refused.returncode,refused.stdout)
        self.assertIn('changed',refused.stdout)

    def test_planning_execution_failure_preserves_override_and_spends_no_correction(self):
        selection = {'harness':'claude-code','model':'issue-selected-model','effort':'medium'}
        unit = subprocess.check_output([sys.executable,str(SCRIPTS/'runlog.py'),'unit-id','--cwd',str(self.root)],text=True).strip()
        out = self.workflow(issueRoles={'ground#01':{'implementer':selection}}, runId='planning-failure', unitId=unit,
                            technicalPlanRawResults=[{'executionUnavailable':True,'error':'Selected execution unavailable'}])
        self.assertIsNone(out['error'])
        self.assertEqual([selection], [c['selection'] for c in out['calls']])
        delivery = out['result']['results'][0]
        self.assertEqual(('paused','execution_unavailable','technical-planner',0),
                         (delivery['outcome'],delivery['reason'],delivery['role'],delivery['corrections']))
        self.assertEqual('',self.git('status','--porcelain'))
        events = self.fixture.read_run_log_events(self.root.parent/'state',unit,'planning-failure')
        self.assertFalse(any(e['event']=='refutation' or e.get('phase')=='Implement' for e in events))
        selected = next(e['data'] for e in events if e['event']=='role.selected')
        self.assertEqual(selection,selected['effective'])

    def test_accepted_plan_is_retained_outside_sanitized_run_events(self):
        unit = subprocess.check_output([sys.executable,str(SCRIPTS/'runlog.py'),'unit-id','--cwd',str(self.root)],text=True).strip()
        out = self.workflow(runId='retained-plan',unitId=unit)
        self.assertIsNone(out['error'])
        events = self.fixture.read_run_log_events(self.root.parent/'state',unit,'retained-plan')
        text = json.dumps(events)
        self.assertNotIn('existing() returns True',text)
        plans = list((self.root.parent/'state'/unit/'technical-plans').glob('*.json'))
        self.assertEqual(1,len(plans))
        retained = json.loads(plans[0].read_text())
        self.assertEqual('source.py',retained['plan']['findings'][0]['path'])
        self.assertEqual('done',out['result']['results'][0]['outcome'])


    def test_pending_resume_correction_is_not_spent_when_planning_refuses_handoff(self):
        self.git('branch', '-m', 'gantry/ground-01')
        unit = subprocess.check_output([sys.executable, str(SCRIPTS/'runlog.py'), 'unit-id',
                                       '--cwd', str(self.root)], text=True).strip()
        state = self.root.parent/'state'
        cases = [
            ('checkout_changed', {'technicalPlanEdit': True}),
            ('protocol_failure', {'technicalPlanRawResults': [None, None]}),
            ('execution_unavailable', {'technicalPlanRawResults': [
                {'executionUnavailable': True, 'error': 'Selected execution unavailable'}]}),
            ('needs_operator', {'technicalPlanConflicts': ['Approved contract conflicts with source']}),
        ]
        for reason, options in cases:
            with self.subTest(reason=reason):
                run = 'resume-plan-' + reason
                events = [
                    {'event': 'run.started', 'data': {'repositoryRoot': str(self.root),
                        'policyHash': 'deadbeef', 'tier': 'reference', 'staleAfterSeconds': 900,
                        'host': {'effectiveHost': 'claude-code'}}},
                    {'event': 'refutation', 'issue': 'ground#01', 'data': {}},
                    {'event': 'phase.started', 'issue': 'ground#01', 'phase': 'Implement',
                     'data': {'worktree': str(self.root)}},
                    {'event': 'refutation', 'issue': 'ground#01', 'data': {}},
                ]
                for event in events:
                    self.fixture.append_runlog_event(state, unit, run, {'ts': '2026-09-13T09:00:00Z', 'run': run, **event})
                out = self.workflow(runId=run, unitId=unit, correctionBudget=2,
                    priorRun={'run': run, 'issue': 'ground#01', 'worktree': str(self.root),
                              'branch': self.git('branch', '--show-current')}, **options)
                self.assertIsNone(out['error'])
                delivery = out['result']['results'][0]
                self.assertEqual(('paused', reason, 1),
                    (delivery['outcome'], delivery['reason'], delivery['corrections']))
                self.assertEqual(1, self.fixture.run_corrections_command(state, unit, run, 'ground#01'))
                self.assertFalse(any(c['label'].startswith('implement:') for c in out['calls']))
                recorded = self.fixture.read_run_log_events(state, unit, run)
                self.assertEqual(1, sum(e['event'] == 'phase.started' and e.get('phase') == 'Implement'
                                        for e in recorded))
                (self.root/'unexpected.txt').unlink(missing_ok=True)

    def test_recovered_delivery_cannot_advance_when_review_fix_planning_fails(self):
        self.git('branch','-m','gantry/ground-01')
        unit = subprocess.check_output([sys.executable,str(SCRIPTS/'runlog.py'),'unit-id','--cwd',str(self.root)],text=True).strip()
        stopped = self.workflow(runId='review-fix-plan',unitId=unit,interruptRole='implementer',waitForRetainedResult=True)
        self.assertEqual('paused',stopped['result']['results'][0]['outcome'])
        resumed = self.workflow(runId='review-fix-plan',unitId=unit,
            recoveredResults=stopped['retainedResults'],
            priorRun={'run':'review-fix-plan','issue':'ground#01','worktree':str(self.root),'branch':self.git('branch','--show-current')},
            reviewerResult={'blocking':[{'finding':'Missing proof','fix':'Add real verification'}],'nonBlocking':[],'summary':'Requires fix'},
            technicalPlanRawResults=[None,None])
        self.assertIsNone(resumed['error'])
        self.assertEqual(['review:ground#01','technical-plan:ground#01','technical-plan:ground#01:retry'], [c['label'] for c in resumed['calls']])
        self.assertEqual(('paused','protocol_failure',0), tuple(resumed['result']['results'][0][key] for key in ['outcome','reason','corrections']))
        self.assertEqual(['test commit'], resumed['result']['results'][0]['commits'])
        self.assertTrue(resumed['result']['results'][0]['reviewFix'])

    def test_native_structured_output_does_not_bypass_external_critic_validation(self):
        out = self.workflow(structuredOutput=True,
            roles={'implement':{'harness':'claude-code','model':'selected-model','effort':'medium'},
                   'critic':{'harness':'codex','model':'external-critic'}},
            dispatchResults=[{'exitCode':0,'stdout':'{}','stderr':''}])
        self.assertIsNone(out['error'])
        self.assertEqual('critic_failed',out['result']['results'][0]['outcome'])
        self.assertIn('Status: ready-for-agent',self.issue.read_text())
