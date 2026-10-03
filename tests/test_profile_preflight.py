"""Readiness is proof of the selected profile, not a declaration or login."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts'))
import execution


class ProfilePreflightTests(unittest.TestCase):
    selection = {'harness': 'codex', 'model': 'gpt-6.1-sol', 'effort': 'medium', 'sandbox': 'read-only'}

    def test_version_and_login_cannot_prove_selected_model(self):
        calls = []
        def runner(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, 'codex 0.160.0' if '--version' in cmd else 'Logged in', '')
        with tempfile.TemporaryDirectory() as root:
            res = execution.preflight_validate(run_overrides={r:self.selection for r in execution.BASE_ROLES}, root=Path(root), runner=runner)
        self.assertFalse(res['valid'])
        self.assertEqual('unknown', res['checks']['plan']['dimensions']['modelEffort']['status'])
        self.assertFalse(any('exec' in cmd and '--help' not in cmd for cmd in calls))

    def test_authorized_probe_is_bounded_non_editing_and_reused_only_in_run(self):
        from unittest.mock import patch
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            cli=root/'codex'; cli.write_text('binary'); cli.chmod(0o755)
            (root/'auth.json').write_text('credential deliberately never read')
            calls=[]
            def runner(cmd, **kwargs):
                calls.append((cmd,kwargs))
                if '--version' in cmd: text='codex 0.160.0'
                elif 'login' in cmd: text='Logged in'
                else: text='\n'.join(map(json.dumps,[{'type':'item.completed','item':{'type':'agent_message','text':'GANTRY_PREFLIGHT_OK'}},{'type':'turn.completed'}]))
                return subprocess.CompletedProcess(cmd,0,text,'')
            with patch.dict(os.environ, {'PATH':str(root), 'CODEX_HOME':str(root), 'OPENAI_API_KEY':'', 'CODEX_API_KEY':''}):
                cache={}
                opts=dict(run_overrides={r:self.selection for r in execution.BASE_ROLES},root=root,runner=runner,authorize_probe=True,cache=cache,run_id='run-one')
                got=execution.preflight_validate(**opts)
                self.assertTrue(got['valid'], got)
                self.assertEqual(1,len([c for c,k in calls if 'exec' in c and '--help' not in c]))
                cmd, kw=next((c,k) for c,k in calls if 'exec' in c and '--help' not in c)
                self.assertEqual('read-only',cmd[cmd.index('--sandbox')+1])
                self.assertEqual(45,kw['timeout'])
                execution.preflight_validate(**opts)
                self.assertEqual(4,len(calls))
                execution.preflight_validate(**{**opts,'run_id':'run-two'})
                self.assertEqual(8,len(calls))
                (root/'auth.json').write_text('changed account credential')
                execution.preflight_validate(**opts)
                self.assertEqual(12,len(calls))
                self.assertNotIn('credential',repr(cache))

    def test_cli_single_selection_requires_approved_permissions(self):
        proc=subprocess.run([sys.executable,str(Path(execution.__file__)),'preflight','--selection',json.dumps({**self.selection,'sandbox':None}),'--json'],capture_output=True,text=True,timeout=20)
        self.assertEqual(1,proc.returncode)
        got=json.loads(proc.stdout)
        self.assertEqual('unavailable',got['dimensions']['permissions']['status'])

    def test_canonical_entries_refuse_before_native_or_external_agents(self):
        from tests.test_workflow_host_binding import WorkflowHostBindingTests
        fixture=WorkflowHostBindingTests()
        with tempfile.TemporaryDirectory() as tmp:
            args=fixture.entry_args(Path(tmp),'codex')
            args['preflightResult']={'valid':False,'status':'unknown','remedy':'Select a replacement explicitly'}
            for filename in ('plan-workflow.md','round-workflow.md'):
                if filename=='round-workflow.md':
                    args['issues']=[{'ref':'example#01','path':'example.md','spec':'example'}]
                got=fixture.run_workflow(filename,args)
                self.assertIn('preflight',json.dumps(got).lower())
                self.assertEqual([],got['calls'])

    def test_canonical_failures_preserve_actionable_sanitized_diagnosis(self):
        import profile_preflight
        from tests.test_workflow_host_binding import WorkflowHostBindingTests
        fixture = WorkflowHostBindingTests()
        cases = (
            ('authentication', self.selection, True),
            ('transport', {**self.selection, 'transport': 'unsupported'}, False),
            ('permissions', {**self.selection, 'sandbox': None}, False),
            ('modelEffort', self.selection, False),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for dimension, selection, auth_failure in cases:
                def runner(cmd, **kwargs):
                    if 'login' in cmd and auth_failure:
                        return subprocess.CompletedProcess(cmd, 1, 'RAW_AUTH_STREAM', 'RAW_STDERR')
                    text = 'codex 0.160.0' if '--version' in cmd else 'Logged in'
                    return subprocess.CompletedProcess(cmd, 0, text, 'RAW_STDERR')
                diagnosis = profile_preflight.check(selection, root=root, runner=runner)
                self.assertFalse(diagnosis['valid'])
                self.assertEqual('unknown' if dimension == 'modelEffort' else 'unavailable',
                                 diagnosis['dimensions'][dimension]['status'])
                # Extra transport fields must not enter the operator-facing failure.
                diagnosis['stdout'] = 'RAW_STDOUT'
                diagnosis['stderr'] = 'RAW_STDERR'
                for filename in ('plan-workflow.md', 'round-workflow.md'):
                    with self.subTest(dimension=dimension, workflow=filename):
                        args = fixture.entry_args(root, 'codex')
                        args['preflightResult'] = diagnosis
                        if filename == 'round-workflow.md':
                            args['issues'] = [{'ref': 'example#01', 'path': 'example.md', 'spec': 'example'}]
                        got = fixture.run_workflow(filename, args)
                        self.assertEqual([], got['calls'])
                        if filename == 'plan-workflow.md':
                            message = got['error']
                        else:
                            paused = got['result']['results'][0]
                            self.assertEqual('paused', paused['outcome'])
                            self.assertTrue(got['result']['nextRoundBlocked'])
                            message = paused['error']
                        preserved = json.loads(message.split('Execution preflight failed: ', 1)[1])
                        self.assertEqual(diagnosis['status'], preserved['status'])
                        self.assertEqual(diagnosis['dimensions'], preserved['dimensions'])
                        self.assertEqual(diagnosis['error'], preserved['error'])
                        self.assertEqual(diagnosis['remedy'], preserved['remedy'])
                        self.assertNotIn('RAW_', message)

    def test_canonical_malformed_preflight_uses_fixed_safe_fallback(self):
        from tests.test_workflow_host_binding import WorkflowHostBindingTests
        fixture = WorkflowHostBindingTests()
        fallback = ('Execution preflight refused or unknown; explicit profile recovery required. '
                    'Select a replacement or authorize a bounded read-only probe explicitly.')
        malformed = (
            ['RAW_STREAM'],
            {'valid': False, 'status': 'RAW_STREAM', 'error': 'RAW_ERROR'},
            {'valid': False, 'status': 'unknown', 'dimensions': [], 'error': 'RAW_ERROR', 'remedy': 'RAW_REMEDY'},
            {'valid': False, 'status': 'unknown', 'dimensions': {}, 'error': 'RAW_ERROR', 'remedy': 'RAW_REMEDY'},
        )
        with tempfile.TemporaryDirectory() as tmp:
            for diagnosis in malformed:
                for filename in ('plan-workflow.md', 'round-workflow.md'):
                    with self.subTest(diagnosis=diagnosis, workflow=filename):
                        args = fixture.entry_args(Path(tmp), 'codex')
                        args['preflightResult'] = diagnosis
                        if filename == 'round-workflow.md':
                            args['issues'] = [{'ref': 'example#01', 'path': 'example.md', 'spec': 'example'}]
                        got = fixture.run_workflow(filename, args)
                        message = (got['error'] if filename == 'plan-workflow.md'
                                   else got['result']['results'][0]['error'])
                        self.assertEqual(fallback, message)
                        self.assertEqual([], got['calls'])

    def test_success_evidence_validation_rejects_incomplete_or_unverified_contracts(self):
        import copy
        import profile_preflight
        from tests.preflight_fixture import VERIFIED_PREFLIGHT
        self.assertTrue(profile_preflight.valid_evidence(VERIFIED_PREFLIGHT))
        invalid = self.invalid_success_evidence()
        for value in invalid:
            with self.subTest(value=value):
                self.assertFalse(profile_preflight.valid_evidence(value))
                with tempfile.TemporaryDirectory() as tmp:
                    from unittest.mock import patch
                    cache = {('run-test', 'a' * 64): copy.deepcopy(value)}
                    calls = []
                    def runner(cmd, **kwargs):
                        calls.append(cmd)
                        return subprocess.CompletedProcess(cmd, 1, 'RAW_STDOUT', 'RAW_STDERR')
                    with patch.object(profile_preflight, 'identity', return_value='a' * 64):
                        got = profile_preflight.check(self.selection, root=Path(tmp), runner=runner,
                                                      cache=cache, run_id='run-test')
                    self.assertFalse(got['valid'])
                    self.assertFalse(got['reused'])
                    self.assertEqual({}, cache)
                    self.assertTrue(calls)
                    self.assertNotIn('RAW_', json.dumps(got))

    @staticmethod
    def invalid_success_evidence():
        import copy
        from tests.preflight_fixture import VERIFIED_PREFLIGHT
        invalid = [{'valid': True}, {**VERIFIED_PREFLIGHT, 'dimensions': None}]
        for field in ('status', 'dimensions', 'error', 'remedy', 'reused'):
            value = copy.deepcopy(VERIFIED_PREFLIGHT)
            del value[field]
            invalid.append(value)
        for name in VERIFIED_PREFLIGHT['dimensions']:
            for status in ('unknown', 'unavailable'):
                value = copy.deepcopy(VERIFIED_PREFLIGHT)
                value['dimensions'][name]['status'] = status
                invalid.append(value)
            value = copy.deepcopy(VERIFIED_PREFLIGHT)
            del value['dimensions'][name]
            invalid.append(value)
        for replacement in (None, [], {'status': 'verified', 'source': 'untrusted'}):
            value = copy.deepcopy(VERIFIED_PREFLIGHT)
            value['dimensions']['authentication'] = replacement
            invalid.append(value)
        for field, replacement in (('status', 'unknown'), ('status', 'unavailable'),
                                   ('reused', 'yes'), ('error', 'RAW_ERROR'), ('stdout', 'RAW_STREAM')):
            invalid.append({**copy.deepcopy(VERIFIED_PREFLIGHT), field: replacement})
        value = copy.deepcopy(VERIFIED_PREFLIGHT)
        value['dimensions']['modelEffort']['identity'] = 'untrusted'
        invalid.append(value)
        return invalid

    def test_canonical_success_claims_require_all_verified_dimensions_and_provenance(self):
        from tests.test_workflow_host_binding import WorkflowHostBindingTests
        fixture = WorkflowHostBindingTests()
        with tempfile.TemporaryDirectory() as tmp:
            for value in self.invalid_success_evidence():
                for filename in ('plan-workflow.md', 'round-workflow.md'):
                    with self.subTest(value=value, workflow=filename):
                        args = fixture.entry_args(Path(tmp), 'codex')
                        args['preflightResult'] = value
                        if filename == 'round-workflow.md':
                            args['issues'] = [{'ref': 'example#01', 'path': 'example.md', 'spec': 'example'}]
                        got = fixture.run_workflow(filename, args)
                        self.assertEqual([], got['calls'])
                        message = (got['error'] if filename == 'plan-workflow.md'
                                   else got['result']['results'][0]['error'])
                        self.assertTrue(message.startswith('Execution preflight refused or unknown;'))
                        self.assertNotIn('RAW_', message)
                        if filename == 'round-workflow.md':
                            self.assertEqual('paused', got['result']['results'][0]['outcome'])
                            self.assertTrue(got['result']['nextRoundBlocked'])

    def test_public_cli_rejects_persisted_invalid_success_and_requires_fresh_probe(self):
        import copy
        import os
        import profile_preflight
        from tests.preflight_fixture import VERIFIED_PREFLIGHT
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = root / 'codex'
            cli.write_text('#!' + sys.executable + '\n' + '''import sys,json
from pathlib import Path
root=Path(__file__).parent
args=sys.argv[1:]
if '--version' in args: print('codex 0.160.0')
elif 'login' in args: print('Logged in')
elif '--help' in args: print('usage')
else:
 p=root/'counter'; p.write_text(str(int(p.read_text())+1) if p.exists() else '1')
 if (root/'fail').exists():
  print('RAW_FAILURE',file=sys.stderr); sys.exit(1)
 print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'GANTRY_PREFLIGHT_OK'}}))
 print(json.dumps({'type':'turn.completed'}))
''')
            cli.chmod(0o755)
            (root / 'auth.json').write_text('never read')
            state = root / 'state'
            log = state / 'abcdef123456' / 'runs' / 'run-invalid.jsonl'
            log.parent.mkdir(parents=True)
            log.write_text(json.dumps({'ts': '2026-10-03T00:00:00Z', 'run': 'run-invalid',
                'event': 'run.started', 'data': {'repositoryRoot': str(root), 'policyHash': 'test',
                'tier': 'compatible', 'staleAfterSeconds': 1800}}) + '\n')
            env = {**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                   'CODEX_HOME': str(root), 'OPENAI_API_KEY': '', 'CODEX_API_KEY': ''}
            cmd = [sys.executable, str(Path(execution.__file__)), 'preflight', '--selection',
                   json.dumps(self.selection), '--run-id', 'run-invalid', '--unit-id', 'abcdef123456',
                   '--state-root', str(state), '--cwd', str(root), '--json']
            def invoke(authorized=False):
                proc = subprocess.run(cmd + (['--authorize-probe'] if authorized else []),
                                      env=env, capture_output=True, text=True, timeout=20)
                return proc, json.loads(proc.stdout)
            proc, got = invoke(True)
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertTrue(profile_preflight.valid_evidence(got))
            cache_path = log.with_suffix('.preflight.json')
            key = next(iter(json.loads(cache_path.read_text())))
            (root / 'fail').touch()
            for value in self.invalid_success_evidence():
                with self.subTest(value=value):
                    cache_path.write_text(json.dumps({key: value}))
                    proc, got = invoke()
                    self.assertEqual(1, proc.returncode)
                    self.assertFalse(got['valid'])
                    self.assertFalse(got['reused'])
                    self.assertEqual('unknown', got['dimensions']['modelEffort']['status'])
                    self.assertEqual({}, json.loads(cache_path.read_text()))
                    cache_path.write_text(json.dumps({key: value}))
                    proc, got = invoke(True)
                    self.assertEqual(1, proc.returncode)
                    self.assertFalse(got['valid'])
                    self.assertFalse(got['reused'])
                    self.assertNotIn('RAW_', proc.stdout)
                    self.assertEqual({}, json.loads(cache_path.read_text()))
            # Rejected evidence can be replaced only by a fresh authorized successful probe.
            (root / 'fail').unlink()
            cache_path.write_text(json.dumps({key: {'valid': True}}))
            proc, got = invoke(True)
            self.assertEqual(0, proc.returncode)
            self.assertFalse(got['reused'])
            self.assertTrue(profile_preflight.valid_evidence(got))
            proc, got = invoke()
            self.assertEqual(0, proc.returncode)
            self.assertTrue(got['reused'])

    def test_unsupported_selected_syntax_stops_before_execution_probe(self):
        calls=[]
        def runner(cmd, **kwargs):
            calls.append(cmd)
            if '--help' in cmd: return subprocess.CompletedProcess(cmd,2,'','sensitive unsupported syntax')
            text='codex 0.160.0' if '--version' in cmd else 'Logged in'
            return subprocess.CompletedProcess(cmd,0,text,'')
        with tempfile.TemporaryDirectory() as root:
            import profile_preflight
            got=profile_preflight.check(self.selection,root=Path(root),runner=runner,authorize_probe=True)
        self.assertEqual('unavailable',got['dimensions']['compatibility']['status'])
        self.assertFalse(any('exec' in c and '--help' not in c for c in calls))
        self.assertNotIn('sensitive',json.dumps(got))

    def test_failed_probes_never_enter_reusable_evidence(self):
        import profile_preflight
        for failure in ('timeout','invalid','auth','refused','fallback'):
            calls=[]
            def runner(cmd, **kwargs):
                calls.append((cmd,kwargs))
                if '--version' in cmd: text='codex 0.160.0'
                elif '--help' in cmd: text='usage'
                elif 'login' in cmd:
                    return subprocess.CompletedProcess(cmd,1 if failure=='auth' else 0,'Logged in','sensitive authentication detail')
                elif failure=='timeout': raise subprocess.TimeoutExpired(cmd,45,output='sensitive timeout')
                elif failure=='refused': return subprocess.CompletedProcess(cmd,1,'','sensitive refusal')
                elif failure=='fallback': text=json.dumps({'type':'turn.completed','model':'sensitive-fallback-model'})
                else: text='invalid sensitive stream'
                return subprocess.CompletedProcess(cmd,0,text,'')
            with tempfile.TemporaryDirectory() as root:
                cache={}
                for attempt in range(2):
                    got=profile_preflight.check(self.selection,root=Path(root),runner=runner,authorize_probe=True,cache=cache,run_id='run-test')
                    self.assertFalse(got['valid'])
                    self.assertNotIn('sensitive',json.dumps(got))
                self.assertEqual({},cache)
                self.assertTrue(all(k['timeout'] in (15,45) for c,k in calls))

    def test_profile_and_local_identity_changes_invalidate_evidence(self):
        import profile_preflight
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); cli=root/'codex'; cli.write_text('binary'); cli.chmod(0o755)
            (root/'auth.json').write_text('never read')
            (root/'config.toml').write_text('initial config')
            with patch.dict(os.environ,{'PATH':str(root),'CODEX_HOME':str(root),'OPENAI_API_KEY':'','CODEX_API_KEY':''}):
                original=profile_preflight.identity(self.selection,root,{'policy':1})
                self.assertIsNotNone(original)
                for field,value in (('model','different'),('effort','high'),('sandbox','workspace-write'),('transport','other')):
                    self.assertNotEqual(original,profile_preflight.identity({**self.selection,field:value},root,{'policy':1}))
                self.assertNotEqual(original,profile_preflight.identity(self.selection,root,{'policy':2}))
                self.assertNotEqual(original,profile_preflight.identity(self.selection,root.parent,{'policy':1}))
                (root/'config.toml').write_text('new permission/provider config')
                self.assertNotEqual(original,profile_preflight.identity(self.selection,root,{'policy':1}))
                next_key=profile_preflight.identity(self.selection,root,{'policy':1})
                cli.write_text('different binary')
                self.assertNotEqual(next_key,profile_preflight.identity(self.selection,root,{'policy':1}))
                (root/'auth.json').unlink()
                self.assertIsNone(profile_preflight.identity(self.selection,root,{'policy':1}))

    def test_ready_workflow_preflights_exact_resolved_selection_before_agent(self):
        from tests.test_workflow_host_binding import WorkflowHostBindingTests
        fixture=WorkflowHostBindingTests()
        with tempfile.TemporaryDirectory() as tmp:
            args=fixture.entry_args(Path(tmp),'codex')
            args['roles']={r:self.selection for r in execution.ALL_ROLES}
            got=fixture.run_workflow('plan-workflow.md',args)
            self.assertIsNone(got['error'])
            self.assertTrue(got['calls'])
            self.assertTrue(got['preflightCalls'])
            self.assertLess(got['preflightCalls'][0]['sequence'],got['calls'][0]['sequence'])
            import shlex
            command=shlex.split(got['preflightCalls'][0]['command'])
            profile=json.loads(command[command.index('--selection')+1])
            self.assertEqual(self.selection,profile)
            self.assertNotIn('--authorize-probe',got['preflightCalls'][0]['command'])
            args['authorizePreflightProbe']=True
            approved=fixture.run_workflow('plan-workflow.md',args)
            self.assertIn('--authorize-probe',approved['preflightCalls'][0]['command'])

    def test_public_cli_reuses_existing_run_evidence_across_processes(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); cli=root/'codex'
            cli.write_text('#!'+sys.executable+'\n'+'''import sys,json
from pathlib import Path
args=sys.argv[1:]
if '--version' in args: print('codex 0.160.0')
elif 'login' in args: print('Logged in')
elif '--help' in args: print('usage')
else:
 p=Path(__file__).with_name('counter'); p.write_text(str(int(p.read_text())+1) if p.exists() else '1')
 print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'GANTRY_PREFLIGHT_OK'}}))
 print(json.dumps({'type':'turn.completed'}))
''');cli.chmod(0o755)
            (root/'auth.json').write_text('not read')
            state=root/'state'; log=state/'abcdef123456'/'runs'/'run-cli.jsonl';log.parent.mkdir(parents=True)
            log.write_text(json.dumps({'ts':'2026-10-03T00:00:00Z','run':'run-cli','event':'run.started','data':{'repositoryRoot':str(root),'policyHash':'test','tier':'compatible','staleAfterSeconds':1800}})+'\n')
            env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'CODEX_HOME':str(root),'OPENAI_API_KEY':'','CODEX_API_KEY':''}
            cmd=[sys.executable,str(Path(execution.__file__)),'preflight','--selection',json.dumps(self.selection),'--authorize-probe','--run-id','run-cli','--unit-id','abcdef123456','--state-root',str(state),'--cwd',str(root),'--json']
            for attempt in range(2):
                proc=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=20)
                self.assertEqual(0,proc.returncode,proc.stderr)
                got=json.loads(proc.stdout);self.assertTrue(got['valid'])
                self.assertEqual(attempt==1,got['reused'])
            self.assertEqual('1',(root/'counter').read_text())
            self.assertNotIn('not read',log.with_suffix('.preflight.json').read_text())
