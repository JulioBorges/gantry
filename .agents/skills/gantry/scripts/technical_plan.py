"""Ground a dedicated Technical Plan in its assigned Issue checkout."""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from common import artifact_path, parse_issue, resolve_policy


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
    import os
    identity = input_identity(root, issue_path)
    files = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root).split(b'\0')
    # Approved input files remain protected even with a machine-local ignored tracker.
    files.extend(os.fsencode(identity[key]) for key in ('issue', 'spec'))
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
    return {'input': identity, 'branch': git(root, 'branch', '--show-current'),
            'files': contents, 'index': git(root, 'diff', '--cached', '--binary', '--no-ext-diff')}


def _digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def standing_hashes(root: Path) -> dict[str, str | None]:
    """Content of configured context and standing-decision files, not every commit."""
    policy = resolve_policy(root)
    found: dict[str, str | None] = {}
    context = policy['artifacts']['context']
    found[context] = _digest(root / context)
    decisions = root / policy['artifacts']['adrs']
    if decisions.is_dir():
        for path in sorted(item for item in decisions.rglob('*') if item.is_file()):
            found[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        found[policy['artifacts']['adrs']] = _digest(decisions)
    return found


def contract_fingerprint(root: Path, issue_path: Path) -> dict:
    issue = parse_issue(issue_path)
    spec = artifact_path(root, 'specs', issue.spec)
    return {
        'criteria': [criterion.text for criterion in issue.criteria],
        'blockedBy': list(issue.blocked_by),
        'spec': _digest(spec),
    }


def source_hashes(root: Path, plan: dict) -> dict[str, str | None]:
    hashes = {}
    for finding in plan.get('findings') or []:
        relative = finding.get('path')
        if isinstance(relative, str) and relative not in hashes:
            hashes[relative] = _digest(root / relative)
    return hashes


def freshness(root: Path, issue_path: Path, plan: dict) -> dict:
    identity = input_identity(root, issue_path)
    return {
        'worktree': identity['worktree'],
        'issue': identity['issue'],
        'spec': identity['spec'],
        'revision': identity['revision'],
        'contract': contract_fingerprint(root, issue_path),
        'sources': source_hashes(root, plan),
        'standing': standing_hashes(root),
    }


def artifact_file(directory: Path, issue_ref: str) -> Path:
    safe = re.sub(r'[^A-Za-z0-9._-]+', '-', issue_ref)
    return directory / f'{safe}.json'


def plans_directory(root: Path, state_root: Path | None):
    import runlog
    directory = runlog.state_root(state_root) / runlog.unit_id(root) / 'technical-plans'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    return directory


def evaluate_retained(root: Path, issue_path: Path, state_root: Path | None) -> dict:
    """Decide reuse, targeted refresh, or an operator stop. Never return another checkout's plan."""
    import json
    root = root.resolve()
    issue = parse_issue(issue_path)
    path = artifact_file(plans_directory(root, state_root), issue.ref)
    if not path.is_file():
        return {'action': 'absent'}
    try:
        retained = json.loads(path.read_text(encoding='utf-8'))
        plan = retained['plan']
        recorded = retained['freshness']
    except (OSError, ValueError, KeyError, TypeError):
        return {'action': 'corrupt'}
    try:
        identity = input_identity(root, issue_path)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        return {'action': 'corrupt', 'error': str(error)}
    if recorded.get('worktree') != identity['worktree'] or recorded.get('issue') != identity['issue'] or recorded.get('spec') != identity['spec']:
        return {'action': 'mismatch', 'reason': 'artifact identity does not match this Issue checkout'}
    current_contract = contract_fingerprint(root, issue_path)
    if current_contract != recorded.get('contract'):
        return {
            'action': 'operator',
            'reason': 'approved_contract_changed',
            'error': 'Approved contract or dependency changed; operator decision required before replanning',
        }
    current_sources = source_hashes(root, plan)
    stale = sorted(relative for relative, digest in (recorded.get('sources') or {}).items() if current_sources.get(relative) != digest)
    standing_changed = recorded.get('standing') != standing_hashes(root)
    if stale or standing_changed:
        return {'action': 'refresh', 'plan': plan, 'staleSources': stale, 'standingChanged': standing_changed}
    return {'action': 'reuse', 'plan': plan}


def main() -> int:
    import argparse
    import json
    import sys
    import result
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['capture', 'accept', 'evaluate'])
    parser.add_argument('--cwd', required=True, type=Path)
    parser.add_argument('--issue', required=True, type=Path)
    parser.add_argument('--state-root', type=Path)
    args = parser.parse_args()
    root = args.cwd.resolve()
    issue = root / args.issue
    try:
        if args.action == 'evaluate':
            print(json.dumps(evaluate_retained(root, issue, args.state_root)))
            return 0
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
        directory = plans_directory(root, args.state_root)
        destination = artifact_file(directory, parse_issue(issue).ref)
        destination.write_text(json.dumps({'baseline': observed, 'plan': plan, 'freshness': freshness(root, issue, plan)}), encoding='utf-8')
        print(json.dumps({'artifact': str(destination), 'accepted': not plan['conflicts'], 'conflicts': plan['conflicts']}))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(json.dumps({'accepted': False, 'reason': 'checkout_changed' if 'changed the assigned checkout' in str(error) else 'protocol_failure', 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
