"""Host-only repair exercised through the public setup CLI in temporary Git repositories."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SETUP = Path(__file__).resolve().parents[1] / '.agents/skills/gantry/scripts/setup.py'


class HostSetupRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.policy = self.root / '.gantry/config.json'
        self.policy.parent.mkdir()
        self.initial = {
            'execution': {
                'hostHarness': 'antigravity',
                'roles': {
                    'plan': {'harness': 'codex', 'model': 'custom plan', 'effort': 'medium'},
                    'implement': {'harness': 'codex', 'model': 'custom implement'},
                    'review': {'harness': 'opencode', 'model': 'custom review'},
                    'critic': {'harness': 'claude-code', 'model': 'custom critic', 'effort': 'high'},
                    'research': {'harness': 'antigravity', 'model': 'custom research'},
                    'plan-critic': {'harness': 'codex', 'model': 'custom plan critic'},
                    'requirement-critic': {'harness': 'codex', 'model': 'custom requirement critic'},
                    'learner': {'harness': 'opencode', 'model': 'custom learner'},
                },
                'extension': {'literal': '$(touch NEVER); `touch NEVER` "quotes"'},
            },
            'checks': [{'name': 'test', 'command': 'echo "ok"; $(touch NEVER)'}],
            'artifacts': {'issues': 'custom/{slug}/issues'},
            'caveman': True,
            'hooks': {'record': ['PostToolUse'], 'deny': ['PreToolUse']},
            'unknown': {'keep': [1, 'two']},
        }
        self.policy.write_text(json.dumps(self.initial, indent=3) + '\n')

    def run_setup(self, *args: str, answer: str = '') -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SETUP), *args], cwd=self.root,
                              input=answer, text=True, capture_output=True)

    def test_preview_decline_and_apply_preserve_every_role_and_unrelated_field(self) -> None:
        before = self.policy.read_bytes()
        preview = self.run_setup('--host-only', '--host', 'claude-code')
        self.assertEqual(0, preview.returncode, preview.stderr)
        self.assertIn('Host diagnosis:', preview.stdout)
        self.assertIn('Proposed .gantry/config.json:', preview.stdout)
        self.assertIn('.claude/settings.json', preview.stdout)
        self.assertEqual(before, self.policy.read_bytes())
        self.assertFalse((self.root / '.claude').exists())
        for answer in ('n\n', '', 'overwrite\n'):
            declined = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer=answer)
            self.assertEqual(1, declined.returncode, declined.stderr)
            self.assertEqual(before, self.policy.read_bytes())
            self.assertFalse((self.root / '.claude').exists())
        applied = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(0, applied.returncode, applied.stderr)
        expected = json.loads(before)
        expected['execution']['hostHarness'] = 'claude-code'
        self.assertEqual(expected, json.loads(self.policy.read_bytes()))
        self.assertEqual(before.replace(b'"antigravity"', b'"claude-code"', 1), self.policy.read_bytes())
        self.assertFalse((self.root / 'AGENTS.md').exists())
        self.assertFalse((self.root / 'NEVER').exists())

    def test_ignored_policy_proposes_tracking_migration_without_changing_ignore_rules(self) -> None:
        ignore = self.root / '.gitignore'
        ignore.write_text('.gantry/\n')
        before = self.policy.read_bytes()
        preview = self.run_setup('--host-only', '--host', 'codex', '--apply', answer='y\n')
        self.assertEqual(2, preview.returncode, preview.stderr)
        self.assertIn('Tracked-policy migration proposal:', preview.stdout)
        self.assertIn('!.gantry/config.json', preview.stdout)
        self.assertIn('git add .gantry/config.json', preview.stdout)
        self.assertEqual('.gantry/\n', ignore.read_text())
        self.assertEqual(before, self.policy.read_bytes())
        self.assertFalse((self.root / '.claude').exists())

    def test_selected_adapter_preserves_user_commands_other_adapters_and_is_idempotent(self) -> None:
        claude = self.root / '.claude/settings.json'
        claude.parent.mkdir()
        owned = 'python3 "old/.agents/skills/gantry/scripts/guard.py" PreToolUse'
        user = {'type': 'command', 'command': 'python3 "mine/guard.py"; echo \"keep\"'}
        initial = {
            'permissions': {'allow': ['Read'], 'custom': 'keep'},
            'hooks': {
                'PreToolUse': [{'matcher': '*', 'timeout': 15, 'hooks': [user, {'type': 'command', 'command': owned}]}],
                'CustomEvent': [{'type': 'command', 'command': 'echo custom'}],
                'PreCompact': [{'hooks': [{'type': 'command', 'command': 'python3 "skills/gantry/scripts/guard.py" PreCompact'}]}],
            },
        }
        claude.write_text('{\n\t"permissions" : ' + json.dumps(initial['permissions']) + ',\n "hooks": ' + json.dumps(initial['hooks']) + '\n}\n')
        antigravity = self.root / '.agents/hooks.json'
        antigravity.parent.mkdir()
        antigravity.write_bytes(b'{ "other" : "bytes" }\n')
        opencode = self.root / '.opencode/opencode.json'
        opencode.parent.mkdir()
        opencode.write_bytes(b'{ "plugin" : ["user"] }\n')
        result = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='yes\n')
        self.assertEqual(0, result.returncode, result.stderr)
        final = json.loads(claude.read_bytes())
        self.assertEqual(initial['permissions'], final['permissions'])
        self.assertTrue(claude.read_bytes().startswith(b'{\n\t"permissions" : '))
        self.assertEqual([{'matcher': '*', 'timeout': 15, 'hooks': [user]}], final['hooks']['PreToolUse'][:1])
        self.assertEqual(initial['hooks']['CustomEvent'], final['hooks']['CustomEvent'])
        self.assertNotIn('PreCompact', final['hooks'])
        self.assertEqual(2, len(final['hooks']['PreToolUse']))
        self.assertEqual(1, len(final['hooks']['PostToolUse']))
        self.assertEqual(b'{ "other" : "bytes" }\n', antigravity.read_bytes())
        self.assertEqual(b'{ "plugin" : ["user"] }\n', opencode.read_bytes())
        first = (claude.read_bytes(), self.policy.read_bytes())
        repeat = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(0, repeat.returncode, repeat.stderr)
        self.assertIn('none (already matches)', repeat.stdout)
        self.assertEqual(first, (claude.read_bytes(), self.policy.read_bytes()))

    def test_empty_unrelated_events_survive_owned_repair_and_idempotent_reapplication(self) -> None:
        self.initial['hooks'] = {'record': ['PostToolUse'], 'deny': []}
        self.policy.write_text(json.dumps(self.initial))
        adapter = self.root / '.claude/settings.json'
        adapter.parent.mkdir()
        user = {'type': 'command', 'command': 'echo user-action'}
        old_post = {'type': 'command', 'command': 'python3 "old/skills/gantry/scripts/guard.py" PostToolUse'}
        adapter.write_text(json.dumps({'permissions': {'allow': ['Read']}, 'hooks': {
            'CustomEvent': [],
            'PreCompact': [],
            'SubagentStart': [{'hooks': [{'type': 'command', 'command': 'python3 "old/skills/gantry/scripts/guard.py" SubagentStart'}]}],
            'PostToolUse': [user, {'matcher': '*', 'hooks': [old_post, old_post]}],
        }}))
        applied = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(0, applied.returncode, applied.stderr)
        self.assertEqual({
            'permissions': {'allow': ['Read']},
            'hooks': {
                'CustomEvent': [],
                'PreCompact': [],
                'PostToolUse': [user, {'matcher': '*', 'hooks': [{
                    'type': 'command',
                    'command': 'python3 "${CLAUDE_PROJECT_DIR:-$PWD}/.agents/skills/gantry/scripts/guard.py" PostToolUse --cwd "${CLAUDE_PROJECT_DIR:-$PWD}" --format claude-code',
                }]}],
            },
        }, json.loads(adapter.read_bytes()))
        first = (adapter.read_bytes(), self.policy.read_bytes())
        repeated = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(0, repeated.returncode, repeated.stderr)
        self.assertIn('none (already matches)', repeated.stdout)
        self.assertEqual(first, (adapter.read_bytes(), self.policy.read_bytes()))

    def test_normal_setup_does_not_choose_adapters_from_installations_or_directories(self) -> None:
        # With no saved host selection, installed tools and directories alone
        # must not choose which adapter normal setup changes.
        self.initial['execution'].pop('hostHarness')
        self.policy.write_text(json.dumps(self.initial))
        (self.root / '.agents/skills').mkdir(parents=True)
        (self.root / '.codex').mkdir()
        result = self.run_setup('--config', '{"unknown": "new"}', answer='m\n')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse((self.root / '.claude/settings.json').exists())
        self.assertFalse((self.root / '.agents/hooks.json').exists())

    def test_malformed_policy_and_adapter_fail_before_any_write_even_overwrite(self) -> None:
        for value in ('{', '[]', '{"execution": []}', '{"execution": {"hostHarness": "unsupported"}}',
                      '{"execution": {"roles": []}}', '{"hooks": {"deny": "PreToolUse"}}',
                      '{"execution": {}, "execution": {}}'):
            with self.subTest(value=value):
                self.policy.write_text(value)
                result = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertEqual(value, self.policy.read_text())
                self.assertFalse((self.root / '.claude').exists())
                normal = self.run_setup('--config', '{}', answer='o\n')
                self.assertEqual(2, normal.returncode, normal.stdout + normal.stderr)
                self.assertEqual(value, self.policy.read_text())
        self.policy.write_text(json.dumps(self.initial))
        adapter = self.root / '.claude/settings.json'
        adapter.parent.mkdir()
        for malformed in ('{', '[]', '{"hooks": []}', '{"hooks": {"PreToolUse": {}}}'):
            with self.subTest(adapter=malformed):
                adapter.write_text(malformed)
                before = self.policy.read_bytes()
                result = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertEqual(before, self.policy.read_bytes())
                self.assertEqual(malformed, adapter.read_text())

    def test_commands_mentioning_gantry_are_not_mistaken_for_owned_entries(self) -> None:
        adapter = self.root / '.claude/settings.json'
        adapter.parent.mkdir()
        user_commands = [
            {'type': 'command', 'command': 'echo "skills/gantry/scripts/guard.py"'},
            {'type': 'command', 'command': 'python3 "skills/gantry/scripts/guard.py" PreToolUse; echo user-action'},
            {'type': 'command', 'command': 'python3 "my/guard.py" PreToolUse'},
        ]
        settings = {'hooks': {'PreToolUse': [{'matcher': 'Read', 'hooks': user_commands}]}}
        adapter.write_text(json.dumps(settings))
        result = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(0, result.returncode, result.stderr)
        final = json.loads(adapter.read_text())
        self.assertEqual(settings['hooks']['PreToolUse'][0], final['hooks']['PreToolUse'][0])
        self.assertEqual(2, len(final['hooks']['PreToolUse']))

    def test_executable_substitutions_survive_repair_and_repetition_without_execution(self) -> None:
        adapter = self.root / '.claude/settings.json'
        adapter.parent.mkdir()
        commands = [
            'python3 "skills/gantry/scripts/guard.py" PreToolUse --cwd "$(touch USER_ACTION; pwd)"',
            'python3 "skills/gantry/scripts/guard.py" PreToolUse --cwd "`touch USER_ACTION; pwd`"',
            'python3 "$(touch USER_ACTION; pwd)/skills/gantry/scripts/guard.py" PreToolUse',
            'python3 "`touch USER_ACTION; pwd`/skills/gantry/scripts/guard.py" PreToolUse',
        ]
        static_guard = {'type': 'command', 'command': 'python3 "old/.agents/skills/gantry/scripts/guard.py" PreToolUse'}
        environment_guard = {
            'type': 'command',
            'command': 'python3 "${CLAUDE_PROJECT_DIR:-$PWD}/.agents/skills/gantry/scripts/guard.py" PreToolUse --cwd "${CLAUDE_PROJECT_DIR:-$PWD}" --format claude-code',
        }
        for command in commands:
            with self.subTest(command=command):
                user = {'type': 'command', 'command': command, 'timeout': 19}
                wrapper = {'matcher': 'Read', 'timeout': 23, 'hooks': [user]}
                adapter.write_text(json.dumps({'hooks': {'PreToolUse': [
                    {**wrapper, 'hooks': [user, static_guard, environment_guard, static_guard]},
                ]}}))
                applied = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
                self.assertEqual(0, applied.returncode, applied.stderr)
                hooks = json.loads(adapter.read_bytes())['hooks']['PreToolUse']
                self.assertEqual([wrapper, {'matcher': '*', 'hooks': [environment_guard]}], hooks)
                self.assertFalse((self.root / 'USER_ACTION').exists())
                first = (adapter.read_bytes(), self.policy.read_bytes())
                repeat = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
                self.assertEqual(0, repeat.returncode, repeat.stderr)
                self.assertIn('none (already matches)', repeat.stdout)
                self.assertEqual(first, (adapter.read_bytes(), self.policy.read_bytes()))
                self.assertFalse((self.root / 'USER_ACTION').exists())

    def test_record_only_policy_does_not_silently_enable_denial_hooks(self) -> None:
        self.initial['hooks'] = {'record': ['PreToolUse', 'PostToolUse'], 'deny': []}
        self.policy.write_text(json.dumps(self.initial))
        result = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('PreToolUse requires explicit deny approval', result.stdout)
        hooks = json.loads((self.root / '.claude/settings.json').read_text())['hooks']
        self.assertNotIn('PreToolUse', hooks)
        self.assertEqual(['PostToolUse'], list(hooks))

    def test_missing_policy_and_invalid_or_unresolved_host_do_not_synthesize_setup(self) -> None:
        before = self.policy.read_bytes()
        for args in (('--host', 'made-up'), ()):
            result = self.run_setup('--host-only', *args, '--apply', answer='y\n')
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertEqual(before, self.policy.read_bytes())
            self.assertFalse((self.root / '.claude').exists())
        self.policy.unlink()
        missing = self.run_setup('--host-only', '--host', 'claude-code', '--apply', answer='y\n')
        self.assertEqual(2, missing.returncode, missing.stderr)
        self.assertIn('normal gantry-setup', missing.stdout)
        self.assertFalse(self.policy.exists())
        config_file = self.root / 'approved-policy.json'
        config_file.write_text(json.dumps(self.initial))
        declined = self.run_setup('--config-file', str(config_file), answer='n\n')
        self.assertEqual(1, declined.returncode, declined.stderr)
        self.assertFalse(self.policy.exists())
        approved = self.run_setup('--config-file', str(config_file), answer='y\n')
        self.assertEqual(0, approved.returncode, approved.stderr)
        self.assertEqual(self.initial, json.loads(self.policy.read_text()))

    def test_unsupported_adapter_has_manual_guidance_and_leaves_all_adapters_untouched(self) -> None:
        adapter = self.root / '.claude/settings.json'
        adapter.parent.mkdir()
        adapter.write_bytes(b'{ "user" : "unchanged" }\n')
        for host in ('codex', 'opencode'):
            result = self.run_setup('--host-only', '--host', host, '--apply', answer='y\n')
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('manual workflow rules and independent Critic verification', result.stdout)
            self.assertIn('no native enforcement was installed', result.stdout)
            self.assertEqual(b'{ "user" : "unchanged" }\n', adapter.read_bytes())
            self.assertFalse((self.root / '.agents/hooks.json').exists())
            self.assertFalse((self.root / '.opencode').exists())
            self.assertEqual(host, json.loads(self.policy.read_text())['execution']['hostHarness'])

    def test_structured_config_input_preserves_metacharacters_without_shell_execution(self) -> None:
        self.policy.unlink()
        config = self.root / 'config with spaces.json'
        config.write_text(json.dumps(self.initial))
        result = self.run_setup('--config-file', str(config), answer='y\n')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.initial, json.loads(self.policy.read_text()))
        self.assertFalse((self.root / 'NEVER').exists())
        before = self.policy.read_bytes()
        invalid = self.run_setup('--host-only', '--host', 'codex', '--config-file', str(config), '--apply', answer='o\n')
        self.assertEqual(2, invalid.returncode)
        self.assertEqual(before, self.policy.read_bytes())

    def test_policy_and_unrelated_adapter_bytes_keep_crlf_and_unicode_formatting(self) -> None:
        policy = b'{\r\n "execution": {"roles": {}, "hostHarness": "antigravity"},\r\n "unknown": "\\u00e9"\r\n}\r\n'
        self.policy.write_bytes(policy)
        result = self.run_setup('--host-only', '--host', 'codex', '--apply', answer='y\n')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(policy.replace(b'"antigravity"', b'"codex"'), self.policy.read_bytes())


if __name__ == '__main__':
    unittest.main()
