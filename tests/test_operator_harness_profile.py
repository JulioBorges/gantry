"""Tests for operator harness profile outside tracked policy (spec 19, issue operator-harness-profile#01)."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SETUP = Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts/setup.py'
EXECUTION = Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts/execution.py'
COMMON = Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts/common.py'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts'))

import common
import execution
import runlog


class OperatorHarnessProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.unit_id = runlog.unit_id(self.root)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.env = {
            'HOME': str(self.home),
            'PATH': os.environ.get('PATH', ''),
            'GANTRY_STATE_ROOT': str(self.root / 'state'),
            'GANTRY_PROFILE_ROOT': str(self.home / '.gantry' / 'profiles'),
        }

        self.policy_file = self.root / '.gantry/config.json'
        self.policy_file.parent.mkdir(parents=True, exist_ok=True)
        self.initial_policy = {
            'execution': {
                'roles': {
                    'plan': {'harness': 'codex', 'model': 'gpt-6.1-sol'},
                    'implement': {'harness': 'codex', 'model': 'gpt-6.1-sol'},
                    'review': {'harness': 'codex', 'model': 'gpt-6.1-sol'},
                    'critic': {'harness': 'codex', 'model': 'gpt-6.1-sol'},
                }
            },
            'artifacts': {
                'specs': '.scratch/{slug}/spec.md',
                'issues': '.scratch/{slug}/issues',
                'adrs': 'docs/adr',
                'decisions': 'docs/adr',
                'context': 'CONTEXT.md',
                'issueTracker': 'docs/agents/issue-tracker.md',
            },
        }
        self.policy_file.write_text(json.dumps(self.initial_policy, indent=2) + '\n', encoding='utf-8')

        self.agents_file = self.root / 'AGENTS.md'
        self.agents_initial = (
            "# My Agents\n\n"
            "<!-- gantry:begin -->\n"
            "## Gantry Repository Policy\n\n"
            "This repository uses Gantry for its agentic SDLC.\n"
            "Artifacts, templates, and checks are configured in `.gantry/config.json`.\n"
            "<!-- gantry:end -->\n"
        )
        self.agents_file.write_text(self.agents_initial, encoding='utf-8')

    def run_setup(self, *args: str, answer: str = '', env: dict | None = None) -> subprocess.CompletedProcess:
        use_env = dict(self.env)
        if env:
            use_env.update(env)
        return subprocess.run(
            [sys.executable, str(SETUP), *args],
            cwd=self.root,
            input=answer,
            text=True,
            capture_output=True,
            env=use_env,
        )

    def run_execution_host(self, *args: str, env: dict | None = None) -> tuple[subprocess.CompletedProcess, dict]:
        use_env = dict(self.env)
        if env:
            use_env.update(env)
        proc = subprocess.run(
            [sys.executable, str(EXECUTION), 'host', '--cwd', str(self.root), '--json', *args],
            capture_output=True,
            text=True,
            env=use_env,
        )
        data = json.loads(proc.stdout) if proc.stdout.strip().startswith('{') else {}
        return proc, data

    def test_approved_personal_switch_writes_only_profile_and_preserves_tracked_files(self) -> None:
        policy_before = self.policy_file.read_bytes()
        agents_before = self.agents_file.read_bytes()

        # Preview first
        preview = self.run_setup('--personal', '--host', 'antigravity')
        self.assertEqual(0, preview.returncode, preview.stderr)
        self.assertIn('Execution unit:', preview.stdout)
        self.assertIn('Profile path:', preview.stdout)
        self.assertIn('Proposed profile:', preview.stdout)
        self.assertIn('antigravity', preview.stdout)
        self.assertIn('Preview only', preview.stdout)

        # Confirm no profile written yet
        expected_profile_path = self.home / '.gantry' / 'profiles' / self.unit_id / 'execution.json'
        self.assertFalse(expected_profile_path.exists())

        # Now apply with confirmation
        applied = self.run_setup('--personal', '--host', 'antigravity', '--apply', answer='y\n')
        self.assertEqual(0, applied.returncode, applied.stderr)
        self.assertIn('Applied approved personal switch', applied.stdout)

        # Profile is created with correct content
        self.assertTrue(expected_profile_path.exists())
        prof_data = json.loads(expected_profile_path.read_text(encoding='utf-8'))
        self.assertEqual({'hostHarness': 'antigravity'}, prof_data)

        # Tracked policy and AGENTS.md are byte-for-byte unchanged
        self.assertEqual(policy_before, self.policy_file.read_bytes())
        self.assertEqual(agents_before, self.agents_file.read_bytes())

    def test_two_temporary_homes_with_different_profiles_resolve_different_hosts(self) -> None:
        home_a = self.root / 'home_a'
        home_b = self.root / 'home_b'
        home_a.mkdir()
        home_b.mkdir()

        prof_a = home_a / '.gantry' / 'profiles' / self.unit_id / 'execution.json'
        prof_a.parent.mkdir(parents=True)
        prof_a.write_text(json.dumps({'hostHarness': 'antigravity'}, indent=2) + '\n')

        prof_b = home_b / '.gantry' / 'profiles' / self.unit_id / 'execution.json'
        prof_b.parent.mkdir(parents=True)
        prof_b.write_text(json.dumps({'hostHarness': 'codex'}, indent=2) + '\n')

        policy_before = self.policy_file.read_bytes()

        env_a = dict(self.env, HOME=str(home_a), GANTRY_PROFILE_ROOT=str(home_a / '.gantry' / 'profiles'))
        env_b = dict(self.env, HOME=str(home_b), GANTRY_PROFILE_ROOT=str(home_b / '.gantry' / 'profiles'))

        proc_a, data_a = self.run_execution_host(env=env_a)
        proc_b, data_b = self.run_execution_host(env=env_b)

        self.assertEqual('antigravity', data_a.get('savedPreference'))
        self.assertEqual('codex', data_b.get('savedPreference'))
        self.assertIn({'source': 'profile:execution.hostHarness', 'kind': 'preference', 'host': 'antigravity'}, data_a['sources'])
        self.assertIn({'source': 'profile:execution.hostHarness', 'kind': 'preference', 'host': 'codex'}, data_b['sources'])

        # Tracked policy remains untouched
        self.assertEqual(policy_before, self.policy_file.read_bytes())

    def test_explicit_host_outranks_profile_and_legacy_tracked_host_without_writes(self) -> None:
        # Tracked policy has legacy host codex
        policy_with_legacy = copy.deepcopy(self.initial_policy)
        policy_with_legacy['execution']['hostHarness'] = 'codex'
        self.policy_file.write_text(json.dumps(policy_with_legacy, indent=2) + '\n')
        policy_before = self.policy_file.read_bytes()

        # Profile has antigravity
        prof_path = self.home / '.gantry' / 'profiles' / self.unit_id / 'execution.json'
        prof_path.parent.mkdir(parents=True)
        prof_path.write_text(json.dumps({'hostHarness': 'antigravity'}, indent=2) + '\n')
        prof_before = prof_path.read_bytes()

        # Invocation passes --host claude-code
        proc, data = self.run_execution_host('--host', 'claude-code')
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual('resolved', data['status'])
        self.assertEqual('claude-code', data['effectiveHost'])
        self.assertEqual('antigravity', data['savedPreference'])  # Profile outranks legacy tracked
        self.assertTrue(data['mismatch'])

        # No writes to profile or tracked policy
        self.assertEqual(policy_before, self.policy_file.read_bytes())
        self.assertEqual(prof_before, prof_path.read_bytes())

    def test_role_resolution_precedence(self) -> None:
        policy = {
            'execution': {
                'roles': {
                    'plan': {'harness': 'codex', 'model': 'codex-plan'},
                    'critic': {'harness': 'codex', 'model': 'codex-critic'},
                }
            }
        }
        profile_overlay = {
            'critic': {'harness': 'claude-code', 'model': 'claude-critic'}
        }

        # 1. Base + profile overlay: critic comes from profile, plan from policy
        roles = execution.resolve_roles(policy=policy, profile_overlay=profile_overlay)
        self.assertEqual('claude-code', roles['critic']['harness'])
        self.assertEqual('claude-critic', roles['critic']['model'])
        self.assertEqual('codex', roles['plan']['harness'])
        self.assertEqual('codex-plan', roles['plan']['model'])

        # 2. Run override outranks profile overlay
        run_ov = {'critic': {'harness': 'opencode', 'model': 'run-critic'}}
        roles_run = execution.resolve_roles(policy=policy, run_overrides=run_ov, profile_overlay=profile_overlay)
        self.assertEqual('opencode', roles_run['critic']['harness'])
        self.assertEqual('run-critic', roles_run['critic']['model'])

        # 3. Issue override outranks Run override and profile overlay
        issue_ov = {'critic': {'harness': 'antigravity', 'model': 'issue-critic'}}
        roles_issue = execution.resolve_roles(policy=policy, run_overrides=run_ov, issue_overrides=issue_ov, profile_overlay=profile_overlay)
        self.assertEqual('antigravity', roles_issue['critic']['harness'])
        self.assertEqual('issue-critic', roles_issue['critic']['model'])

        # 4. Another operator without profile receives repository default
        roles_other = execution.resolve_roles(policy=policy, profile_overlay=None)
        self.assertEqual('codex', roles_other['critic']['harness'])
        self.assertEqual('codex-critic', roles_other['critic']['model'])

    def test_shared_setup_against_ignored_policy_refuses_setup(self) -> None:
        ignore_file = self.root / '.gitignore'
        ignore_file.write_text('.gantry/\n', encoding='utf-8')
        before = self.policy_file.read_bytes()

        proc = self.run_setup('--harness', 'codex')
        self.assertEqual(2, proc.returncode)
        self.assertIn('Tracked-policy migration proposal:', proc.stdout)
        self.assertIn('!.gantry/config.json', proc.stdout)
        self.assertEqual(before, self.policy_file.read_bytes())
        self.assertEqual('.gantry/\n', ignore_file.read_text())

    def test_legacy_migration_copies_to_profile_and_removes_from_tracked_policy(self) -> None:
        policy_with_legacy = copy.deepcopy(self.initial_policy)
        policy_with_legacy['execution']['hostHarness'] = 'codex'
        self.policy_file.write_text(json.dumps(policy_with_legacy, indent=2) + '\n')

        # Prior to migration, resolve_host sees codex as legacy preference
        proc_before, data_before = self.run_execution_host()
        self.assertEqual('codex', data_before.get('savedPreference'))
        self.assertIn({'source': 'policy:execution.hostHarness', 'kind': 'preference', 'host': 'codex'}, data_before['sources'])

        # Preview migration
        preview = self.run_setup('--migrate-legacy')
        self.assertEqual(0, preview.returncode, preview.stderr)
        self.assertIn('Legacy tracked host: codex', preview.stdout)
        self.assertIn('Preview only', preview.stdout)

        # Apply migration
        applied = self.run_setup('--migrate-legacy', '--apply', answer='y\n')
        self.assertEqual(0, applied.returncode, applied.stderr)
        self.assertIn('Applied approved legacy migration', applied.stdout)

        # Profile now contains codex
        prof_path = self.home / '.gantry' / 'profiles' / self.unit_id / 'execution.json'
        self.assertTrue(prof_path.exists())
        prof_data = json.loads(prof_path.read_text(encoding='utf-8'))
        self.assertEqual('codex', prof_data.get('hostHarness'))

        # Tracked policy no longer contains execution.hostHarness
        updated_policy = json.loads(self.policy_file.read_text(encoding='utf-8'))
        self.assertNotIn('hostHarness', updated_policy.get('execution', {}))

        # resolve_host now sees codex from profile
        proc_after, data_after = self.run_execution_host()
        self.assertEqual('codex', data_after.get('savedPreference'))
        self.assertIn({'source': 'profile:execution.hostHarness', 'kind': 'preference', 'host': 'codex'}, data_after['sources'])

    def test_profile_validation_rejects_credentials_and_unexpected_keys(self) -> None:
        prof_path = self.home / '.gantry' / 'profiles' / self.unit_id / 'execution.json'

        for bad in (
            {'hostHarness': 'antigravity', 'token': 'secret123'},
            {'hostHarness': 'antigravity', 'api_key': 'secret'},
            {'hostHarness': 'antigravity', 'command': 'bash -i'},
            {'hostHarness': 'invalid-host'},
            {'roles': {'critic': {'harness': 'invalid-harness', 'model': 'foo'}}},
            {'roles': {'critic': {'harness': 'codex', 'model': 'foo', 'password': 'bar'}}},
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    common.write_profile(self.root, bad, custom_profile_root=self.home / '.gantry' / 'profiles')

    def test_personal_switch_decline_eof_unsupported_and_noop(self) -> None:
        prof_path = self.home / '.gantry' / 'profiles' / self.unit_id / 'execution.json'

        # Decline
        declined = self.run_setup('--personal', '--host', 'opencode', '--apply', answer='n\n')
        self.assertEqual(1, declined.returncode)
        self.assertIn('Aborted', declined.stdout)
        self.assertFalse(prof_path.exists())

        # EOF
        eof = self.run_setup('--personal', '--host', 'opencode', '--apply', answer='')
        self.assertEqual(1, eof.returncode)
        self.assertIn('Aborted', eof.stdout)
        self.assertFalse(prof_path.exists())

        # Unsupported host
        unsupported = self.run_setup('--personal', '--host', 'invalid-harness', '--apply', answer='y\n')
        self.assertEqual(2, unsupported.returncode)
        self.assertFalse(prof_path.exists())

        # Success first
        applied = self.run_setup('--personal', '--host', 'opencode', '--apply', answer='y\n')
        self.assertEqual(0, applied.returncode)
        self.assertTrue(prof_path.exists())
        prof_bytes = prof_path.read_bytes()

        # No-op repeat
        noop = self.run_setup('--personal', '--host', 'opencode', '--apply', answer='y\n')
        self.assertEqual(0, noop.returncode)
        self.assertIn('already matches', noop.stdout)
        self.assertEqual(prof_bytes, prof_path.read_bytes())


if __name__ == '__main__':
    unittest.main()
