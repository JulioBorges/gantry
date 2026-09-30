"""Host-only setup proposals; selected JSON adapters reuse the pack's hook fragments."""
from __future__ import annotations

import copy
import json
import shlex
import subprocess
from pathlib import Path

from execution import SUPPORTED_HARNESSES, resolve_host

PACK = Path(__file__).resolve().parent.parent
JSON_ADAPTERS = {
    'claude-code': ('.claude/settings.json', 'claude-code.settings.json'),
    'antigravity': ('.agents/hooks.json', 'antigravity.hooks.json'),
}
DECISION_EVENTS = {'PreToolUse', 'tool.execute.before'}


def read_object(text: str) -> dict:
    def unique(pairs: list) -> dict:
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate JSON object key')
            value[key] = item
        return value
    def invalid_constant(value: str) -> None:
        raise ValueError('Non-finite values are not valid configuration JSON')
    value = json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise ValueError('Configuration must contain a JSON object')
    return value


def set_member(text: str, key: str, value: object) -> str:
    """Replace one top-level value while retaining all other member bytes."""
    parsed = read_object(text)
    if key in parsed and parsed[key] == value:
        return text
    decoder = json.JSONDecoder()
    index = text.index('{') + 1
    while True:
        while text[index].isspace() or text[index] == ',':
            index += 1
        if text[index] == '}':
            break
        name, end = decoder.raw_decode(text, index)
        index = end
        while text[index].isspace() or text[index] == ':':
            index += 1
        start = index
        _, index = decoder.raw_decode(text, index)
        if name == key:
            return text[:start] + json.dumps(value, indent=2) + text[index:]
    prefix = ',' if parsed else ''
    return text[:index] + prefix + '\n  ' + json.dumps(key) + ': ' + json.dumps(value, indent=2) + '\n' + text[index:]


def set_host(text: str, host: str) -> str:
    """Patch only execution.hostHarness, including its surrounding policy bytes."""
    parsed = read_object(text)
    if 'execution' not in parsed:
        return set_member(text, 'execution', {'hostHarness': host})
    decoder = json.JSONDecoder()
    index = text.index('{') + 1
    while True:
        while text[index].isspace() or text[index] == ',':
            index += 1
        name, index = decoder.raw_decode(text, index)
        while text[index].isspace() or text[index] == ':':
            index += 1
        start = index
        _, index = decoder.raw_decode(text, index)
        if name == 'execution':
            return text[:start] + set_member(text[start:index], 'hostHarness', host) + text[index:]


def approved_events(policy: dict) -> set[str]:
    hooks = policy.get('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError('hooks must be an object')
    for key in ('record', 'deny'):
        if not isinstance(hooks.get(key, []), list) or any(not isinstance(event, str) for event in hooks.get(key, [])):
            raise ValueError(f'hooks.{key} must be an event-name array')
    # The existing guard has no record-only mode for a decision event. Never
    # install denial-capable wiring on a recording-only approval.
    return (set(hooks.get('record', [])) - DECISION_EVENTS) | set(hooks.get('deny', []))


def validate_policy(policy: dict) -> None:
    execution = policy.get('execution', {})
    if not isinstance(execution, dict):
        raise ValueError('execution must be an object')
    host = execution.get('hostHarness')
    if host is not None and (not isinstance(host, str) or host not in SUPPORTED_HARNESSES):
        raise ValueError('Unsupported saved host')
    roles = execution.get('roles', {})
    if not isinstance(roles, dict) or any(not isinstance(role, dict) for role in roles.values()):
        raise ValueError('execution.roles must map roles to objects')
    approved_events(policy)


def owned_command(entry: dict) -> bool:
    command = entry.get('command')
    if entry.get('type') != 'command' or not isinstance(command, str):
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False
    if len(tokens) < 3 or Path(tokens[0]).name != 'python3':
        return False
    script = tokens[1]
    if script != 'skills/gantry/scripts/guard.py' and not script.endswith('/skills/gantry/scripts/guard.py'):
        return False
    # Only the standalone Gantry invocation is ours. Compound user actions and
    # mentions in echo commands must survive repair.
    if any(token in (';', '&&', '||', '|', '&', '<', '>') for token in tokens):
        return False
    if tokens[2] not in ('PreToolUse', 'PostToolUse', 'SubagentStart', 'SubagentStop', 'PreCompact',
                         'tool.execute.before', 'session.compacted'):
        return False
    options = tokens[3:]
    while options:
        option = options.pop(0)
        if option == '--json':
            continue
        if option == '--cwd' and options:
            options.pop(0)
            continue
        return False
    return True


def without_owned(entries: list) -> list:
    kept = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Hook entries must be objects')
        if owned_command(entry):
            continue
        if 'hooks' not in entry:
            kept.append(entry)
            continue
        nested = entry['hooks']
        if not isinstance(nested, list):
            raise ValueError('Nested hooks must be an array')
        remaining = without_owned(nested)
        if remaining:
            kept.append({**entry, 'hooks': remaining})
        elif not nested:
            kept.append(entry)
    return kept


def adapter_proposal(root: Path, host: str, policy: dict) -> tuple[dict[Path, str], list[str]]:
    capabilities = read_object((PACK / 'capabilities' / f'{host}.json').read_text())
    events = approved_events(policy)
    diagnostics = [f'{event} requires explicit deny approval; recording-only selection cannot install the existing denial-capable guard.'
                   for event in sorted(set(policy.get('hooks', {}).get('record', [])) & DECISION_EVENTS - set(policy.get('hooks', {}).get('deny', [])))]
    if not capabilities.get('hooks') or host not in JSON_ADAPTERS:
        return {}, diagnostics + [f'{host}: no verified automatic setup wiring for this adapter. Use manual workflow rules and independent Critic verification; no native enforcement was installed.']
    relative, fragment = JSON_ADAPTERS[host]
    path = root / relative
    content = path.read_bytes().decode('utf-8') if path.exists() else '{}\n'
    current = read_object(content)
    hooks = copy.deepcopy(current.get('hooks', {}))
    if not isinstance(hooks, dict):
        raise ValueError('Adapter hooks must be an object')
    desired = read_object((PACK / 'hooks' / fragment).read_text())['hooks']
    allowed = events & set(capabilities['hook_events'])
    for event in list(hooks):
        if not isinstance(hooks[event], list):
            raise ValueError('Adapter hook events must contain arrays')
        hooks[event] = without_owned(hooks[event])
        if not hooks[event]:
            del hooks[event]
    for event, entries in desired.items():
        if event in allowed:
            hooks.setdefault(event, []).extend(entries)
    diagnostics.append(f'{host}: selected adapter {relative}; approved wired events: {", ".join(sorted(allowed)) or "none"}. Existing capability declaration only; wiring is not live hook proof.')
    unsupported = events - set(capabilities['hook_events'])
    if unsupported:
        diagnostics.append('Unsupported hook selections require manual guidance: ' + ', '.join(sorted(unsupported)))
    if current.get('hooks', {}) == hooks:
        return {}, diagnostics
    return {path: set_member(content, 'hooks', hooks)}, diagnostics


def confirm(prompt: str) -> str:
    try:
        return input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return ''


def ignored_policy(root: Path) -> bool:
    check = subprocess.run(['git', 'check-ignore', '--no-index', '-q', '--', '.gantry/config.json'],
                           cwd=root, capture_output=True, text=True)
    if check.returncode not in (0, 1):
        # Normal setup also supports repositories not yet initialized by Git.
        if not (root / '.git').exists():
            return False
        raise ValueError('Could not inspect repository policy ignore rules')
    return check.returncode == 0


def migration_proposal() -> None:
    print('Tracked-policy migration proposal:')
    print('Review the effective ignore rules. For repository ignore rules, append these exceptions to .gitignore:')
    print('!.gantry/\n.gantry/*\n!.gantry/config.json')
    print('If policy is still ignored, inspect repository, .git/info/exclude and global rules and repair the effective rule explicitly.')
    print('Then verify with git check-ignore .gantry/config.json and stage with git add .gantry/config.json.')
    print('Keep credentials and transient state outside tracked policy. No ignore rules or policy were changed.')


def host_only(root: Path, host: str | None, apply: bool) -> int:
    diagnosis = resolve_host(root=root, explicit_host=host)
    print('Host diagnosis:')
    print(json.dumps(diagnosis, indent=2))
    if diagnosis['status'] != 'resolved':
        print('Host repair requires a valid explicit --host selection. No files changed.')
        return 2
    path = root / '.gantry/config.json'
    if not path.exists():
        print('Missing repository policy. Use normal gantry-setup with --config-file and approve the full policy before host-only repair. No policy was synthesized.')
        return 2
    if ignored_policy(root):
        migration_proposal()
        return 2
    before = path.read_bytes().decode('utf-8')
    policy = read_object(before)
    validate_policy(policy)
    proposed = set_host(before, diagnosis['effectiveHost'])
    writes, diagnostics = adapter_proposal(root, diagnosis['effectiveHost'], policy)
    if proposed != before:
        writes[path] = proposed
    print('Proposed .gantry/config.json:')
    print(proposed)
    for diagnostic in diagnostics:
        print(diagnostic)
    print('Proposed adapter effects:')
    for adapter, content in writes.items():
        if adapter != path:
            print(adapter.relative_to(root))
            print(content)
    print('Files to change: ' + (', '.join(str(file.relative_to(root)) for file in writes) or 'none (already matches)'))
    print('All role selections and unrelated policy are preserved. AGENTS.md is unchanged.')
    if not apply:
        print('Preview only. To apply, repeat with --apply and explicitly approve this proposal.')
        return 0
    if confirm('Apply this host-only proposal? [y/N] ') not in ('y', 'yes'):
        print('Aborted. No files changed.')
        return 1
    for file, content in writes.items():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding='utf-8')
    print('Applied approved host-only proposal.')
    return 0
