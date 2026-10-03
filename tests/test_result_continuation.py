"""Simulated Host coordination through the canonical workflow; Git and scripts are real."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from tests import test_canonical_gantry_workflow as canonical


class ResultContinuationTests(unittest.TestCase):
    def fixture(self, root):
        h = canonical.CanonicalGantryWorkflowTests()
        h.init_repo(root)
        for key, value in [('user.email', 'gantry@example.test'), ('user.name', 'Gantry Test')]:
            subprocess.run(['git', 'config', key, value], cwd=root, check=True)
        subprocess.run(['git', 'checkout', '-qb', 'feat/run'], cwd=root, check=True)
        issue = h.write_issue(root, 'continuation#01', 'ready-for-agent')
        h.write_roadmap(root)
        (root / 'Makefile').write_text('test:\n\t@test -f delivery.txt\n')
        subprocess.run(['git', 'add', '.'], cwd=root, check=True)
        subprocess.run(['git', 'commit', '-qm', 'base'], cwd=root, check=True)
        base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        args = dict(round=1, issues=[dict(ref='continuation#01', path=str(issue.relative_to(root)), title='Continuation')],
                    models=dict(implement='implement', review='review', critic='critic'), branch='feat/run', baseRef=base,
                    isolate=False, correctionBudget=0, skillDir=str(canonical.SKILL_DIR), repoRoot=str(root),
                    policy={'git': {'target':'main','prefix':'feat/'},'budget':{'corrections':0}}, paths={},
                    commandMode='real', hostHarness='codex', runId='run-continuation', unitId='abcdef123456',
                    stateRoot=str(root.parent / 'state'), isLastRound=True, skipDashboardPrompt=True,
                    implementerCommitText='delivered', criticResult={'criteria':h.critic_evidence(root, issue)})
        return h, issue, args

    def test_delayed_result_is_consumed_and_done_without_another_message(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'repo'
            h, issue, args = self.fixture(root)
            args.update(roleDelayMs=120, statusDuringWait=True)
            out = h.run_workflow('round-workflow.md', args)
            self.assertIsNone(out['error'])
            self.assertEqual('done', out['result']['results'][0]['outcome'])
            self.assertEqual([{'issue':'continuation#01','state':'running','delivered':False,'modelProgress':'unknown'}], out['statusReplies'])
            self.assertEqual('done', canonical.parse_issue(issue).status)
            self.assertEqual('delivered', (root/'delivery.txt').read_text())
            self.assertEqual('', subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True))
            events = h.read_run_log_events(Path(args['stateRoot']),args['unitId'],args['runId'])
            observed = [e for e in events if e['event'].startswith('role.result.') and e['data']['role']=='critic']
            self.assertEqual(['role.result.ready','role.result.consumed'],[e['event'] for e in observed])
            self.assertEqual(observed[0]['data']['invocationId'],observed[1]['data']['invocationId'])
            self.assertEqual('unknown', observed[0]['data']['modelProgress'])

    def test_interruption_reports_pending_work_and_resume_reuses_matching_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'repo'
            h, issue, args = self.fixture(root)
            args.update(roleDelayMs=100, interruptRole='critic', waitForRetainedResult=True)
            stopped = h.run_workflow('round-workflow.md', args)
            self.assertIsNone(stopped['error'])
            self.assertEqual('paused', stopped['result']['results'][0]['outcome'])
            self.assertEqual('operator_stop', stopped['result']['handoffs'][0]['reason'])
            self.assertEqual('ready-for-agent', canonical.parse_issue(issue).status)
            records = stopped['retainedResults']
            self.assertEqual({'implementer','reviewer','critic'}, {r['role'] for r in records})
            resumed = h.run_workflow('round-workflow.md', {**args, 'interruptRole':None, 'recoveredResults':records,
                'priorRun':dict(run=args['runId'], issue='continuation#01',worktree=str(root),branch='feat/run')})
            self.assertIsNone(resumed['error'])
            self.assertEqual('done', resumed['result']['results'][0]['outcome'])
            self.assertEqual([], resumed['calls'], 'No duplicate implementation, review or Critic')
            self.assertEqual(0,resumed['result']['results'][0]['corrections'])

    def test_mismatched_recovered_revision_pauses_without_code_or_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'repo'
            h, issue, args = self.fixture(root)
            args.update(roleDelayMs=50, interruptRole='critic', waitForRetainedResult=True)
            stopped = h.run_workflow('round-workflow.md',args)
            records = stopped['retainedResults']
            records[0]['revision'] = 'stale'
            resumed = h.run_workflow('round-workflow.md',{**args,'interruptRole':None,'recoveredResults':records,
                'priorRun':dict(run=args['runId'],issue='continuation#01',worktree=str(root),branch='feat/run')})
            self.assertIsNone(resumed['error'])
            self.assertEqual('paused',resumed['result']['results'][0]['outcome'])
            self.assertEqual([],resumed['calls'])
            self.assertEqual('ready-for-agent',canonical.parse_issue(issue).status)

    def test_real_configured_approval_wait_keeps_issue_unfinished_until_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            h, issue, args=self.fixture(root)
            args.update(waitGate=True, actualApprovalWait=True)
            out=h.run_workflow('round-workflow.md',args)
            self.assertIsNone(out['error'])
            self.assertEqual('done',out['result']['results'][0]['outcome'])
            events=h.read_run_log_events(Path(args['stateRoot']),args['unitId'],args['runId'])
            names=[e['event'] for e in events]
            self.assertLess(names.index('operator.waiting'),names.index('operator.approved'))
            self.assertLess(names.index('operator.approved'),names.index('issue.done'))
            self.assertTrue(out['approvalObservedUnfinished'])

    def test_delayed_accepted_delivery_integrates_real_issue_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            h, issue, args=self.fixture(root)
            args.update(isolate=True, roleDelayMs=80, issueBranch='gantry/continuation-01')
            out=h.run_workflow('round-workflow.md',args)
            self.assertIsNone(out['error'])
            self.assertEqual('done',out['result']['results'][0]['outcome'])
            delivery=out['result']['results'][0]
            self.assertEqual('gantry/continuation-01',delivery['branch'])
            merge=subprocess.check_output(['git','log','--merges','--format=%s'],cwd=root,text=True)
            self.assertIn('gantry: integrate continuation#01',merge)
            self.assertEqual('done',canonical.parse_issue(issue).status)
            self.assertEqual('delivered',(root/'delivery.txt').read_text())
            subprocess.run(['git','worktree','remove',delivery['worktree']],cwd=root,check=True)

    def test_refuted_malformed_unavailable_and_red_gate_never_complete(self):
        cases=[{'criticResult':{'complete':False,'criteria':[],'gatesVerdict':'fail','gateResult':{'verdict':'fail'},'refutations':['missing proof'],'requiredFixes':[]}},
               {'criticRawResults':[{},{}]}, {'issueExecutionUnavailable':{'continuation#01':'critic'}},
               {'implementerCommitText':'bad','integrationFails':True}]
        for case in cases:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/'repo'
                h,issue,args=self.fixture(root)
                if case.get('integrationFails'):
                    (root/'Makefile').write_text('test:\n\t@grep -q delivered delivery.txt\n')
                    subprocess.run(['git','add','Makefile'],cwd=root,check=True)
                    subprocess.run(['git','commit','-qm','gate'],cwd=root,check=True)
                    args['baseRef']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
                args.update(case,roleDelayMs=30)
                out=h.run_workflow('round-workflow.md',args)
                self.assertIsNone(out['error'])
                self.assertNotEqual('done',out['result']['results'][0]['outcome'])
                self.assertEqual('ready-for-agent',canonical.parse_issue(issue).status)
                events=h.read_run_log_events(Path(args['stateRoot']),args['unitId'],args['runId'])
                self.assertNotIn('issue.done',[e['event'] for e in events])
                if case.get('integrationFails'):
                    self.assertTrue(out['result']['nextRoundBlocked'])
                    self.assertIn('run.cancelled',[e['event'] for e in events])

    def test_late_result_observation_is_rejected_after_run_closes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            h, issue, args=self.fixture(root)
            out=h.run_workflow('round-workflow.md',args)
            retained=out['retainedResults'][-1]
            data={key:value for key,value in retained.items() if key != 'result'}
            event={'ts':'2026-10-03T00:00:00Z','run':args['runId'],'event':'role.result.ready','issue':'continuation#01','data':data}
            append=subprocess.run(['python3',str(canonical.SCRIPTS/'runlog.py'),'append',args['unitId'],args['runId'],'--state-root',args['stateRoot']],input=json.dumps(event),text=True,capture_output=True,cwd=root)
            self.assertEqual(1,append.returncode)
            self.assertIn('closed Run',append.stderr)

    def test_public_result_query_reports_unknown_for_legacy_absent_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo'
            h,issue,args=self.fixture(root)
            log=Path(args['stateRoot'])/args['unitId']/'runs'/f"{args['runId']}.jsonl"
            log.parent.mkdir(parents=True)
            log.write_text(json.dumps({'ts':'2026-10-03T00:00:00Z','run':args['runId'],'event':'run.started',
                                      'data':{'repositoryRoot':str(root),'policyHash':'fixture','tier':'supported','staleAfterSeconds':900}})+'\n')
            query=h.run_script(root,'runlog.py','results',args['unitId'],args['runId'],'--state-root',args['stateRoot'],'--json')
            self.assertEqual(0,query.returncode)
            payload=json.loads(query.stdout)
            self.assertEqual('unknown',payload['availability'])
            self.assertEqual('unknown',payload['modelProgress'])
            self.assertEqual([],payload['results'])
