#!/usr/bin/env python3
"""Reproduce public setup CLI evidence in a temporary Git repository only."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SETUP = ROOT / '.agents/skills/gantry/scripts/setup.py'


def main() -> None:
    with tempfile.TemporaryDirectory(prefix='gantry-setup-proof-') as directory:
        root = Path(directory)
        # Isolate invocation hints and Git's machine-local ignore configuration.
        environment = {'PATH': '/usr/bin:/bin', 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
        subprocess.run(['git', 'init', '-q', str(root)], env=environment, check=True)
        policy = root / '.gantry/config.json'
        policy.parent.mkdir()
        fixture = {
            'execution': {
                'hostHarness': 'antigravity',
                'roles': {'implement': {'harness': 'codex', 'model': 'custom implement', 'effort': 'medium'},
                          'critic': {'harness': 'claude-code', 'model': 'custom critic', 'effort': 'high'},
                          'learner': {'harness': 'opencode', 'model': 'custom learner'}},
                'custom': '$(touch NEVER); `touch NEVER`; "quoted"',
            },
            'hooks': {'record': ['PostToolUse'], 'deny': []},
            'caveman': True,
            'unknown': {'keep': 1},
        }
        policy.write_text(json.dumps(fixture, indent=2) + '\n')
        adapter = root / '.claude/settings.json'
        adapter.parent.mkdir()
        adapter.write_text('{\n  "user" : "unchanged",\n  "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [{"type": "command", "command": "echo user"}]}]}\n}\n')
        other = root / '.agents/hooks.json'
        other.parent.mkdir()
        other.write_bytes(b'{ "other" : "unchanged bytes" }\n')

        def invoke(title: str, arguments: list[str], answer: str = '', expected: int = 0) -> None:
            print(f'\n### {title}\n')
            print('```text')
            print('$ python3 setup.py ' + ' '.join(arguments))
            print('stdin: ' + (repr(answer) if answer else 'EOF (no approval)'))
            process = subprocess.run([sys.executable, str(SETUP), *arguments], cwd=root,
                                     env=environment, input=answer, text=True, capture_output=True)
            print(process.stdout, end='')
            if process.stderr:
                print(process.stderr.replace(str(root), '<temporary-repository>'), end='')
            print(f'Exit: {process.returncode}\n```')
            assert process.returncode == expected

        before = (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        base = ['--host-only', '--host', 'claude-code']
        invoke('Read-only preview', base)
        assert before == (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        invoke('Explicit decline', [*base, '--apply'], 'n\n', 1)
        assert before == (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        invoke('EOF cancellation', [*base, '--apply'], expected=1)
        assert before == (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        invoke('Approved host-only repair', [*base, '--apply'], 'y\n')
        expected_policy = json.loads(json.dumps(fixture))
        expected_policy['execution']['hostHarness'] = 'claude-code'
        assert expected_policy == json.loads(policy.read_bytes())
        assert before[0].replace(b'"hostHarness": "antigravity"', b'"hostHarness": "claude-code"') == policy.read_bytes()
        assert before[2] == other.read_bytes()
        assert json.loads(adapter.read_bytes())['hooks']['PreToolUse'][0]['hooks'][0]['command'] == 'echo user'
        assert not (root / 'NEVER').exists()
        first = (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        invoke('Idempotent approved repetition', [*base, '--apply'], 'yes\n')
        assert first == (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        print('\nPreservation assertions: all role/custom fields, policy bytes outside host, user command, other adapter bytes, no shell execution and repeated bytes PASS.')
        invoke('Unsupported automatic adapter wiring', ['--host-only', '--host', 'codex'])
        ignore = root / '.gitignore'
        ignore.write_text('.gantry/\n')
        invoke('Ignored policy migration proposal', [*base, '--apply'], 'y\n', 2)
        assert '.gantry/\n' == ignore.read_text()
        assert first == (policy.read_bytes(), adapter.read_bytes(), other.read_bytes())
        print('\nIgnored-policy assertions: ignore rules and all policy/adapter bytes unchanged PASS.')
        policy.unlink()
        invoke('Missing policy requires normal setup approval', [*base, '--apply'], 'y\n', 2)
        assert not policy.exists()


if __name__ == '__main__':
    main()
