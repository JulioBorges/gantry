"""Read-only Host Harness diagnosis at the public subprocess boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts/execution.py'


class HostResolutionCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {'HOME': str(self.root / 'home'), 'PATH': '', 'GANTRY_STATE_ROOT': str(self.root / 'state')}
        self.policy = self.root / '.gantry/config.json'
        self.policy.parent.mkdir()
        self.policy.write_text('{"execution":{"hostHarness":"antigravity","roles":{"critic":{"harness":"claude-code","model":"custom"}}}}\n')
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def diagnose(self, *args):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        proc = subprocess.run([sys.executable, str(SCRIPT), 'host', '--cwd', str(self.root), '--json', *args], env=self.env, capture_output=True, text=True)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        return proc, json.loads(proc.stdout)

    def test_explicit_supported_host_reports_stale_preference_without_writes(self):
        for host in ('claude-code', 'codex', 'opencode', 'antigravity'):
            with self.subTest(host=host):
                proc, data = self.diagnose('--host', host)
                self.assertEqual(0, proc.returncode, proc.stderr)
                self.assertEqual('resolved', data['status'])
                self.assertEqual(host, data['effectiveHost'])
                self.assertEqual('antigravity', data['savedPreference'])
                self.assertEqual(host != 'antigravity', data['mismatch'])
                self.assertIn({'source': 'invocation:explicit-selection', 'kind': 'explicit', 'host': host}, data['sources'])

    def test_absent_and_saved_only_signals_do_not_resolve(self):
        proc, data = self.diagnose()
        self.assertEqual(0, proc.returncode)
        self.assertEqual('unknown', data['status'])
        self.assertIsNone(data['effectiveHost'])
        self.assertEqual('antigravity', data['savedPreference'])
        self.policy.unlink()
        proc, data = self.diagnose()
        self.assertEqual('unknown', data['status'])
        self.assertIsNone(data['savedPreference'])

    def test_inherited_environment_and_installations_are_only_sanitized_hints(self):
        binary_dir = self.root / 'bin'
        binary_dir.mkdir()
        binary = binary_dir / 'codex'
        binary.write_text('#!/bin/sh\necho secret-command-output\n')
        binary.chmod(0o755)
        self.env['PATH'] = str(binary_dir)
        self.env['CODEX_THREAD_ID'] = 'secret-thread-token'
        (self.root / '.agents/skills').mkdir(parents=True)
        proc, data = self.diagnose()
        self.assertEqual(0, proc.returncode)
        self.assertEqual('unknown', data['status'])
        self.assertIsNone(data['effectiveHost'])
        self.assertIn({'source': 'environment:CODEX_THREAD_ID', 'kind': 'hint', 'host': 'codex'}, data['sources'])
        self.assertIn({'source': 'installation:codex', 'kind': 'hint', 'host': 'codex'}, data['sources'])
        self.assertIn({'source': 'directory:.agents/skills', 'kind': 'hint', 'host': None}, data['sources'])
        self.assertNotIn('secret-', proc.stdout + proc.stderr)

    def test_conflicting_inherited_hints_require_explicit_choice(self):
        self.env.update(CODEX_THREAD_ID='secret-codex', CLAUDECODE='secret-claude')
        proc, data = self.diagnose()
        self.assertEqual(0, proc.returncode)
        self.assertEqual('ambiguous', data['status'])
        self.assertIsNone(data['effectiveHost'])
        self.assertNotIn('secret-', proc.stdout + proc.stderr)
        proc, data = self.diagnose('--host', 'opencode')
        self.assertEqual('resolved', data['status'])
        self.assertEqual('opencode', data['effectiveHost'])

    def test_unsupported_selection_is_invalid_and_sanitized(self):
        proc, data = self.diagnose('--host', 'secret-unsupported-token')
        self.assertEqual(1, proc.returncode)
        self.assertEqual('invalid', data['status'])
        self.assertIsNone(data['effectiveHost'])
        self.assertNotIn('secret-', proc.stdout + proc.stderr)

    def test_malformed_policy_is_invalid_even_with_explicit_selection(self):
        for policy_bytes in (b'{broken secret-policy-token', b'[]', b'{"execution":[]}', b'{"execution":{"hostHarness":"secret-invalid-host"}}', b'\xff'):
            with self.subTest(policy=policy_bytes):
                self.policy.write_bytes(policy_bytes)
                proc, data = self.diagnose('--host', 'codex')
                self.assertEqual(1, proc.returncode)
                self.assertEqual('invalid', data['status'])
                self.assertIsNone(data['effectiveHost'])
                self.assertIsNone(data['savedPreference'])
                self.assertNotIn('secret-', proc.stdout + proc.stderr)
                self.assertIn('No fallback', ' '.join(data['diagnostics']))

    def test_existing_adapters_and_machine_state_remain_unchanged(self):
        for relative, contents in (('.claude/settings.json', b'{"hooks":{"custom":"keep"}}'), ('.agents/hooks.json', b'{"custom":"keep"}'), ('home/.gantry/state/unit/runs/run.jsonl', b'{"event":"keep"}\n')):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        proc, data = self.diagnose('--host', 'claude-code')
        self.assertEqual(0, proc.returncode)
        self.assertEqual('resolved', data['status'])

    def test_each_inherited_hint_alone_never_proves_invocation(self):
        for name in ('CODEX_THREAD_ID', 'CODEX_HOME', 'CLAUDECODE', 'CLAUDE_CODE_SESSION_ID', 'OPENCODE_SESSION_ID', 'ANTIGRAVITY_SESSION_ID'):
            with self.subTest(name=name):
                self.env[name] = 'secret-inherited-token'
                proc, data = self.diagnose()
                self.assertEqual(0, proc.returncode)
                self.assertEqual('unknown', data['status'])
                self.assertIsNone(data['effectiveHost'])
                self.assertNotIn('secret-', proc.stdout + proc.stderr)
                del self.env[name]

    def test_binary_and_directory_presence_alone_do_not_resolve(self):
        self.policy.unlink()
        binary_dir = self.root / 'bin'
        binary_dir.mkdir()
        self.env['PATH'] = str(binary_dir)
        for binary_name in ('agy', 'claude', 'codex', 'opencode'):
            with self.subTest(binary=binary_name):
                binary = binary_dir / binary_name
                binary.write_text('#!/bin/sh\nexit 99\n')
                binary.chmod(0o755)
                proc, data = self.diagnose()
                self.assertEqual(0, proc.returncode)
                self.assertEqual('unknown', data['status'])
                self.assertIsNone(data['effectiveHost'])
                binary.unlink()
        for directory in ('.agents/skills', '.claude/skills', '.opencode/skills', '.gemini/skills'):
            (self.root / directory).mkdir(parents=True)
        proc, data = self.diagnose()
        self.assertEqual('unknown', data['status'])
        self.assertIsNone(data['effectiveHost'])
