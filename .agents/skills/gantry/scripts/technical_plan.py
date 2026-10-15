"""Ground a dedicated Technical Plan in its assigned Issue checkout."""
from __future__ import annotations

import subprocess
from pathlib import Path

from common import artifact_path, parse_issue


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def input_identity(root: Path, issue_path: Path) -> dict:
    root = root.resolve()
    issue = parse_issue(issue_path)
    spec = artifact_path(root, 'specs', issue.spec)
    if not spec.is_file():
        raise ValueError('Technical Plan requires the approved Spec file')
    return {'worktree': str(root), 'revision': git(root, 'rev-parse', 'HEAD'),
            'issue': str(issue.path.relative_to(root)), 'spec': str(spec.relative_to(root))}


def validate_plan(plan: dict, root: Path, issue_path: Path) -> list[str]:
    """Structural evidence is necessary; semantic conflict detection remains agent work."""
    errors = []
    try:
        if plan['input'] != input_identity(root, issue_path):
            errors.append('Technical Plan input identity does not match assigned checkout')
        issue = parse_issue(issue_path)
        expected = [criterion.index for criterion in issue.criteria]
        indexes = [item['index'] for item in plan['coverage']]
        if not expected or sorted(indexes) != expected:
            errors.append('Technical Plan coverage must map every criterion exactly once')
        for finding in plan['findings']:
            path = (root / finding['path']).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                errors.append('Technical Plan source reference does not exist inside assigned checkout')
            elif not 1 <= finding['line'] <= len(path.read_text(encoding='utf-8').splitlines()):
                errors.append('Technical Plan source line does not exist')
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        errors.append(f'Technical Plan inputs unavailable: {error}')
    return errors


def capture(root: Path, issue_path: Path) -> dict:
    """Observe checkout contents, index and identity; this is detection, not a sandbox."""
    import hashlib
    import os
    files = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root).split(b'\0')
    contents = {}
    for raw in files:
        if not raw:
            continue
        relative = os.fsdecode(raw)
        path = root / relative
        if path.is_symlink():
            data = os.fsencode(os.readlink(path))
        elif path.is_file():
            data = path.read_bytes()
        else:
            data = b'<missing>'
        contents[relative] = [hashlib.sha256(data).hexdigest(), path.lstat().st_mode if path.exists() or path.is_symlink() else None]
    return {'input': input_identity(root, issue_path), 'branch': git(root, 'branch', '--show-current'),
            'files': contents, 'index': git(root, 'diff', '--cached', '--binary', '--no-ext-diff')}


def main() -> int:
    import argparse
    import json
    import sys
    import tempfile
    import result
    import runlog
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['capture', 'accept'])
    parser.add_argument('--cwd', required=True, type=Path)
    parser.add_argument('--issue', required=True, type=Path)
    parser.add_argument('--state-root', type=Path)
    args = parser.parse_args()
    root = args.cwd.resolve()
    issue = root / args.issue
    try:
        observed = capture(root, issue)
        if args.action == 'capture':
            print(json.dumps(observed))
            return 0
        payload = json.load(sys.stdin)
        if observed != payload['baseline']:
            raise ValueError('Technical planning changed the assigned checkout; handoff refused. Changes preserved. Read-only instructions and post-call observation do not establish universal filesystem enforcement.')
        plan = payload['plan']
        errors = result.validate(plan, result.load_schema('technical-planner'))
        if not errors:
            errors = validate_plan(plan, root, issue)
        if errors:
            raise ValueError('; '.join(errors))
        directory = runlog.state_root(args.state_root) / runlog.unit_id(root) / 'technical-plans'
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory, suffix='.json', delete=False) as artifact:
            json.dump({'baseline': observed, 'plan': plan}, artifact)
        print(json.dumps({'artifact': artifact.name, 'accepted': not plan['conflicts'], 'conflicts': plan['conflicts']}))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(json.dumps({'accepted': False, 'reason': 'checkout_changed' if 'changed the assigned checkout' in str(error) else 'protocol_failure', 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
