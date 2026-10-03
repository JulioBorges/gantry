"""Bounded selected-profile evidence. No account capabilities are inferred from catalogs."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil

DIMENSIONS = ('compatibility', 'authentication', 'modelEffort', 'transport', 'permissions')


VERIFIED_SOURCES = {
    'compatibility': 'bounded-version-and-parser-probes',
    'authentication': 'bounded-login-status',
    'modelEffort': 'bounded-selected-profile-probe',
    'transport': 'completed-codex-jsonl-probe',
    'permissions': 'operator-selection',
}
MODEL_IDENTITY = 'requested arguments; effective model/effort unobserved'
REMEDY = 'Select an explicitly approved profile or authorize a bounded read-only probe; no fallback was used.'


def valid_evidence(value):
    """Validate the complete sanitized success contract before trusting evidence."""
    if (not isinstance(value, dict) or set(value) != {'valid', 'status', 'dimensions', 'remedy', 'reused', 'error'}
            or value['valid'] is not True or value['status'] != 'verified'
            or value['error'] is not None or value['remedy'] != REMEDY
            or not isinstance(value['reused'], bool)):
        return False
    dimensions = value['dimensions']
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        return False
    for name, source in VERIFIED_SOURCES.items():
        expected = {'status': 'verified', 'source': source}
        if name == 'modelEffort':
            expected['identity'] = MODEL_IDENTITY
        if dimensions[name] != expected:
            return False
    return True


def identity(selection, root, policy):
    """Fingerprint observable local identity without reading credential values.

    API-key environments and absent auth files cannot establish authentication identity.
    They may be probed but never reused. File metadata is conservative: any rewrite
    invalidates evidence, including a credential refresh with the same account.
    """
    if selection.get('harness') != 'codex' or any(os.environ.get(k) for k in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'CODEX_SANDBOX_NETWORK_DISABLED')):
        return None
    cli = shutil.which('codex')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    try:
        def stamp(path):
            p = Path(path).resolve()
            s = p.stat()
            return [str(p), s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]
        material = [stamp(cli), stamp(auth), str(Path(root).resolve()), selection, policy,
                    hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    hashlib.sha256(Path(__file__).with_name('execution.py').read_bytes()).hexdigest()]
        # Native configuration may alter providers, permissions or model routing.
        config = auth.with_name('config.toml')
        material.append(stamp(config) if config.exists() else None)
        capability = Path(__file__).parent.parent / 'capabilities' / 'codex.json'
        material.append(stamp(capability))
        for directory in [Path(root).resolve(), *Path(root).resolve().parents]:
            local = directory / '.codex' / 'config.toml'
            material.append(stamp(local) if local.exists() else None)
        return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
    except (OSError, TypeError, ValueError):
        return None


def check(selection, *, root, policy=None, runner=None, authorize_probe=False, cache=None, run_id=None):
    import execution
    dimensions = {name: {'status': 'unknown', 'source': 'not-checked'} for name in DIMENSIONS}
    remedy = REMEDY
    out = {'valid': False, 'status': 'unknown', 'dimensions': dimensions, 'remedy': remedy, 'reused': False}
    if not isinstance(selection, dict):
        out.update(status='unavailable', error='Execution selection must be an object.')
        return out
    structural = execution.validate_selection(selection, root=root, check_auth=False)
    if not structural['valid']:
        out.update(status='unavailable', error=structural['error'])
        dimensions['compatibility'] = {'status': 'unavailable', 'source': 'selection-validation'}
        return out
    key = identity(selection, root, policy)
    scope = (run_id, key)
    if run_id and key and cache is not None and scope in cache:
        if valid_evidence(cache[scope]):
            got = copy.deepcopy(cache[scope])
            got['reused'] = True
            return got
        del cache[scope]
    version = execution.validate_harness_version(selection['harness'], runner=runner, cwd=root)
    dimensions['compatibility'] = {'status': 'verified' if version['valid'] else 'unavailable', 'source': 'bounded-version-probe'}
    if not version['valid']:
        out.update(status='unavailable', error=version['error'])
        return out
    if selection['harness'] != 'codex':
        out['error'] = 'Unknown safe selected-profile probe for this adapter; select a supported replacement.'
        return out
    auth = execution.validate_codex_auth(runner=runner, cwd=root)
    dimensions['authentication'] = {'status': 'verified' if auth['valid'] else 'unavailable', 'source': 'bounded-login-status'}
    if not auth['valid']:
        out.update(status='unavailable', error='Authentication unavailable; run codex login explicitly and repeat preflight.')
        return out
    permission = selection.get('sandbox')
    dimensions['permissions'] = {'status': 'verified' if permission in ('read-only', 'workspace-write') else 'unavailable', 'source': 'operator-selection'}
    if dimensions['permissions']['status'] != 'verified':
        out.update(status='unavailable', error='Missing approved sandbox: select read-only or workspace-write explicitly.')
        return out
    if selection.get('transport', 'codex-jsonl') != 'codex-jsonl':
        dimensions['transport'] = {'status': 'unavailable', 'source': 'adapter-contract'}
        out.update(status='unavailable', error='Unsupported result transport; select codex-jsonl explicitly.')
        return out
    syntax_cmd = execution.build_dispatch_command('codex', selection['model'], 'parser check', effort=selection.get('effort'))
    syntax_cmd.extend(['--sandbox', 'read-only', '--config', 'approval_policy="never"', '--help'])
    try:
        syntax = execution.run_captured(syntax_cmd, runner=runner, cwd=root, timeout=15)
        if syntax.returncode:
            raise ValueError('unsupported syntax')
    except (Exception, KeyboardInterrupt):
        dimensions['compatibility'] = {'status': 'unavailable', 'source': 'bounded-parser-probe'}
        out.update(status='unavailable', error='Unsupported or unverifiable selected-profile syntax; select a supported adapter explicitly.')
        return out
    dimensions['compatibility'] = {'status': 'verified', 'source': 'bounded-version-and-parser-probes'}
    if not authorize_probe:
        out['error'] = 'Selected model/effort remains unknown; authorize a bounded non-editing probe.'
        return out
    token = 'GANTRY_PREFLIGHT_OK'
    cmd = execution.build_dispatch_command('codex', selection['model'], f'Do not use tools. Reply exactly {token}.', effort=selection.get('effort'))
    cmd.extend(['--sandbox', 'read-only', '--config', 'approval_policy="never"'])
    try:
        proc = execution.run_captured(cmd, runner=runner, cwd=root, timeout=45)
        if proc.returncode:
            out.update(status='unavailable', error='Selected-profile probe refused; select an available replacement or repair authentication explicitly.')
            dimensions['modelEffort'] = {'status': 'unavailable', 'source': 'bounded-selected-profile-probe'}
            return out
        final = execution.codex_final_result(proc.stdout, selection['model'])
        if final.strip() != token:
            raise ValueError('invalid probe final')
    except (Exception, KeyboardInterrupt):
        out['error'] = 'Selected-profile probe timed out, failed or returned invalid evidence; pause and repeat explicitly.'
        return out
    dimensions['modelEffort'] = {'status': 'verified', 'source': 'bounded-selected-profile-probe', 'identity': MODEL_IDENTITY}
    dimensions['transport'] = {'status': 'verified', 'source': 'completed-codex-jsonl-probe'}
    out.update(valid=True, status='verified', error=None)
    if run_id and key and cache is not None:
        cache[scope] = copy.deepcopy(out)
    return out
