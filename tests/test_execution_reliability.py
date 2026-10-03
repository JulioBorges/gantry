"""Public adapter regressions; local parser checks use the actual installed CLI."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts'))
import execution


class ExecutionReliabilityTests(unittest.TestCase):
    def test_injected_subprocess_probe_captures_version_and_cwd(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            def runner(cmd, **kwargs):
                calls.append(kwargs)
                return subprocess.run(cmd, **kwargs)
            actual = execution.validate_harness_version('codex', runner=runner, cwd=root)
            if not shutil.which('codex'):
                self.skipTest('Codex is not installed')
            self.assertTrue(actual['valid'], actual)
            self.assertEqual(str(Path(root).resolve()), calls[0]['cwd'])
            self.assertTrue(calls[0]['capture_output'])
            self.assertEqual(actual, execution.validate_harness_version('codex', cwd=root))

    def test_installed_parser_accepts_effort_and_rejects_unsupported_option(self):
        if not shutil.which('codex'):
            self.skipTest('Codex is not installed')
        cmd = execution.build_dispatch_command('codex', 'gpt-6.1-sol', 'parser check', effort='medium')
        good = subprocess.run(cmd + ['--help'], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, good.returncode, good.stderr)
        bad = subprocess.run(cmd + ['--gantry-unsupported-option'], capture_output=True, text=True, timeout=15)
        self.assertNotEqual(0, bad.returncode)
        self.assertIn('--gantry-unsupported-option', bad.stderr)

    def test_codex_final_message_transport_and_model_claim_is_not_identity(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            contract = {'summary': 'done', 'blocking': [], 'nonBlocking': []}
            events = [{'type': 'thread.started', 'thread_id': 'example'},
                      {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps(contract)}},
                      {'type': 'turn.completed', 'usage': {}}]
            def runner(cmd, **kwargs):
                calls.append((cmd, kwargs))
                text = 'codex 0.160.0' if '--version' in cmd else '\n'.join(map(json.dumps, events))
                return subprocess.CompletedProcess(cmd, 0, text, '')
            got = execution.dispatch_role('review', 'review', root, selection={'harness': 'codex', 'model': 'gpt-6.1-sol', 'effort': 'medium'}, runner=runner)
            self.assertEqual(contract, got)
            self.assertEqual(calls[0][1]['cwd'], calls[1][1]['cwd'])
            self.assertIn('--json', calls[1][0])
            self.assertNotIn('--output-schema', calls[1][0])

    def test_truncated_stream_cannot_return_earlier_message(self):
        with tempfile.TemporaryDirectory() as root:
            def runner(cmd, **kwargs):
                text = 'codex 0.160.0' if '--version' in cmd else json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '{"summary":"partial","blocking":[],"nonBlocking":[]}'}})
                return subprocess.CompletedProcess(cmd, 0, text, '')
            with self.assertRaises(execution.ProtocolFailureError):
                execution.dispatch_role('review', 'review', root, selection={'harness': 'codex', 'model': 'gpt-6.1-sol'}, runner=runner, retry_on_invalid=False)

    def test_runner_type_error_never_reinvokes_with_unbounded_options(self):
        calls = []
        def runner(cmd, **kwargs):
            calls.append(kwargs)
            raise TypeError('runner contract error')
        self.assertFalse(execution.validate_harness_version('codex', runner=runner)['valid'])
        self.assertEqual(1, len(calls))
        self.assertIn('timeout', calls[0])

    def test_protocol_retry_is_attributable_and_does_not_log_raw_result(self):
        import runlog
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            state = root / 'state'
            path = runlog.run_log_path(state, 'abcdef123456', 'run-test')
            path.parent.mkdir(parents=True)
            path.write_text('')
            invocations = []
            def runner(cmd, **kwargs):
                if '--version' in cmd:
                    return subprocess.CompletedProcess(cmd, 0, 'codex 0.160.0', '')
                invocations.append(cmd)
                final = '{}' if len(invocations) == 1 else json.dumps({'summary': 'secret role text', 'blocking': [], 'nonBlocking': []})
                events = [{'type':'item.completed','item':{'type':'agent_message','text':final}}, {'type':'turn.completed'}]
                return subprocess.CompletedProcess(cmd, 0, '\n'.join(map(json.dumps,events)), '')
            execution.dispatch_role('review', 'secret prompt', root, selection={'harness':'codex','model':'gpt-6.1-sol','effort':'medium'}, runner=runner, run_id='run-test',unit_id='abcdef123456',state_root=str(state),issue_ref='adapter#01')
            raw = path.read_text()
            events = [json.loads(line) for line in raw.splitlines()]
            self.assertEqual(['role.invocation.started','role.invocation.finished'] * 2, [event['event'] for event in events])
            self.assertEqual([1,1,2,2], [event['data']['attempt'] for event in events])
            self.assertTrue(all(event['issue']=='adapter#01' for event in events))
            self.assertEqual('protocol-result', events[-1]['data']['retryKind'])
            self.assertIsNone(events[-1]['data']['observedSelection']['model'])
            self.assertNotIn('secret', raw)
            self.assertNotIn('result', events[-1]['data'])

    def test_timeout_cancellation_and_start_error_preserve_assigned_code(self):
        for failure in (subprocess.TimeoutExpired('codex', 1), KeyboardInterrupt(), FileNotFoundError('missing executable')):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as root:
                code = Path(root) / 'delivery.py'
                code.write_text('preserved code')
                def runner(cmd, **kwargs):
                    if '--version' in cmd:
                        return subprocess.CompletedProcess(cmd, 0, 'codex 0.160.0', '')
                    raise failure
                with self.assertRaises(execution.ExecutionFailureError):
                    execution.dispatch_role('review', 'review', root, selection={'harness':'codex','model':'gpt-6.1-sol'},runner=runner,timeout=1)
                self.assertEqual('preserved code', code.read_text())

    def test_agent_written_model_text_cannot_establish_a_fallback(self):
        with tempfile.TemporaryDirectory() as root:
            def runner(cmd, **kwargs):
                if '--version' in cmd:
                    return subprocess.CompletedProcess(cmd, 0, 'codex 0.160.0', '')
                text = 'The code contains fallback model: example-model; that is repository data.'
                events = [{'type':'item.completed','item':{'type':'agent_message','text':text}}, {'type':'turn.completed'}]
                return subprocess.CompletedProcess(cmd, 0, '\n'.join(map(json.dumps,events)), '')
            got = execution.dispatch_role('research','research',root,selection={'harness':'codex','model':'gpt-6.1-sol'},runner=runner)
            self.assertIn('repository data',got)
