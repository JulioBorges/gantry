#!/usr/bin/env python3
"""Conversational setup writer for Gantry policy and selected-host adapters."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from execution import SUPPORTED_HARNESSES
from common import profile_path, read_profile, write_profile, validate_profile
from runlog import unit_id
from setup_host import (adapter_proposal, confirm, host_only, ignored_policy,
                        migration_proposal, read_object, validate_policy)


def merge_dicts(base: dict, update: dict) -> dict:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_dicts(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def update_agents(repo_root: Path, host: str | None = None) -> None:
    agents_path = repo_root / "AGENTS.md"
    content = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    begin_marker = "<!-- gantry:begin -->"
    end_marker = "<!-- gantry:end -->"
    
    if host == "codex":
        new_section = (
            f"{begin_marker}\n"
            "## Gantry Repository Policy\n\n"
            "This repository uses Gantry for its agentic SDLC.\n"
            "Artifacts, templates, and checks are configured in `.gantry/config.json`.\n\n"
            "### Codex Host Orchestration & Guardrails\n\n"
            "When Codex operates as host harness or execution runner:\n"
            "- Bounded Execution: Role agents (Implementer, Reviewer, Critic) are executed via bounded sub-processes (`codex exec` or cross-harness dispatch).\n"
            "- Invariant Protection: Never hand-edit `ROADMAP.md` or issue checkboxes/status lines directly. Only `roadmap.py done` updates them after Critic acceptance.\n"
            "- Branch Isolation: Direct commits to `main` are forbidden; all work proceeds on dedicated issue branches.\n"
            "- Defense in Depth: Because Codex lacks native tool hooks, git hooks and adversarial Critic verification enforce delivery integrity and contract validation (`result.py`).\n"
            f"{end_marker}\n"
        )
    else:
        new_section = (
            f"{begin_marker}\n"
            "## Gantry Repository Policy\n\n"
            "This repository uses Gantry for its agentic SDLC.\n"
            "Artifacts, templates, and checks are configured in `.gantry/config.json`.\n"
            f"{end_marker}\n"
        )

    if begin_marker in content and end_marker in content:
        start = content.find(begin_marker)
        end = content.find(end_marker) + len(end_marker)
        if content[end:end+1] == "\n":
            end += 1
        new_content = content[:start] + new_section + content[end:]
    else:
        new_content = content + ("\n" if content and not content.endswith("\n") else "") + new_section

    agents_path.write_text(new_content, encoding="utf-8")


def codex_defaults() -> dict:
    return {'execution': {'hostHarness': 'codex', 'roles': {
        role: {'harness': 'codex', 'model': 'gpt-5.2-codex'}
        for role in ('plan', 'implement', 'review', 'critic')
    }}}


def personal_switch(root: Path, host: str | None, roles: dict | None, apply: bool) -> int:
    try:
        uid = unit_id(root)
    except Exception as exc:
        print(f"Setup error: could not resolve execution unit ID: {exc}", file=sys.stderr)
        return 2

    if host is not None and host not in SUPPORTED_HARNESSES:
        print(f"Setup error: Unsupported explicit host '{host}'; choose antigravity, claude-code, codex or opencode.", file=sys.stderr)
        return 2

    p_path = profile_path(root)
    existing = read_profile(root)
    proposed = copy.deepcopy(existing)
    if host is not None:
        proposed["hostHarness"] = host
    if roles is not None:
        proposed.setdefault("roles", {}).update(roles)

    try:
        validate_profile(proposed)
    except ValueError as exc:
        print(f"Setup error: {exc}", file=sys.stderr)
        return 2

    print(f"Execution unit: {uid}")
    print(f"Profile path: {p_path}")
    print("Proposed profile:")
    print(json.dumps(proposed, indent=2))
    print("Tracked policy (.gantry/config.json), adapter files, and AGENTS.md will remain unchanged.")

    if proposed == existing:
        print("Profile already matches proposed switch. No files changed.")
        return 0

    if not apply:
        print("Preview only. To apply, repeat with --apply and explicitly approve this switch.")
        return 0

    answer = confirm("Apply this personal switch? [y/N] ")
    if answer not in ("y", "yes"):
        print("Aborted. No files changed.")
        return 1

    write_profile(root, proposed)
    print(f"Applied approved personal switch to {p_path}.")
    return 0


def migrate_legacy(root: Path, apply: bool) -> int:
    policy_path = root / ".gantry/config.json"
    if not policy_path.exists():
        print("No .gantry/config.json found.")
        return 0
    policy = read_object(policy_path.read_text(encoding="utf-8"))
    legacy_host = policy.get("execution", {}).get("hostHarness")
    if not legacy_host:
        print("No legacy tracked execution.hostHarness found in .gantry/config.json.")
        return 0

    p_path = profile_path(root)
    prof = read_profile(root)
    proposed_profile = copy.deepcopy(prof)
    if "hostHarness" not in proposed_profile:
        proposed_profile["hostHarness"] = legacy_host

    proposed_policy = copy.deepcopy(policy)
    del proposed_policy["execution"]["hostHarness"]
    if not proposed_policy["execution"]:
        del proposed_policy["execution"]

    print(f"Legacy tracked host: {legacy_host}")
    print(f"Proposed profile ({p_path}):")
    print(json.dumps(proposed_profile, indent=2))
    print("Proposed .gantry/config.json (removing execution.hostHarness):")
    print(json.dumps(proposed_policy, indent=2))

    if not apply:
        print("Preview only. To apply, repeat with --apply and explicitly approve this migration.")
        return 0

    answer = confirm("Apply this legacy migration? [y/N] ")
    if answer not in ("y", "yes"):
        print("Aborted. No files changed.")
        return 1

    write_profile(root, proposed_profile)
    policy_path.write_text(json.dumps(proposed_policy, indent=2) + "\n", encoding="utf-8")
    print("Applied approved legacy migration.")
    return 0


def normal_setup(root: Path, args: argparse.Namespace) -> int:
    path = root / '.gantry/config.json'
    existing = read_object(path.read_text(encoding='utf-8')) if path.exists() else None
    if existing is not None:
        validate_policy(existing)
    if ignored_policy(root):
        migration_proposal()
        return 2
    if args.config_file:
        config = read_object(Path(args.config_file).read_text(encoding='utf-8'))
    elif args.config:
        config = read_object(args.config)
    elif args.harness == 'codex':
        # Legacy normal setup explicitly initializes roles only when requested.
        config = codex_defaults()
    elif args.harness:
        config = {'execution': {'hostHarness': args.harness}}
    else:
        print('Installed binaries and configuration directories are hints, not active host identity.')
        host = confirm('Choose Host Harness [antigravity/claude-code/codex/opencode], or Enter to abort: ')
        if host not in SUPPORTED_HARNESSES:
            print('Aborted. No valid explicit host selection.')
            return 2
        config = codex_defaults() if host == 'codex' else {'execution': {'hostHarness': host}}
    validate_policy(config)
    if args.harness:
        config.setdefault('execution', {})['hostHarness'] = args.harness
    host = config.get('execution', {}).get('hostHarness')
    if host is not None and host not in SUPPORTED_HARNESSES:
        raise ValueError('Unsupported explicit host')
    if host == 'codex' or args.verify_auth:
        print('Guidance: Ensure Codex CLI is authenticated via `codex login` before execution.')
        print('Testing Codex model discovery...')
        try:
            import discovery
            models = discovery.discover_codex_models(use_cache=False)
            print(f'Codex discovery verified: {len(models)} model(s) discovered.')
        except Exception as error:
            print(f'Notice: Codex discovery check: {error}')
            print('Remediation: Run `codex login` before running Gantry tasks.')
    candidates = {'overwrite': config}
    if existing is not None:
        candidates['merge'] = merge_dicts(copy.deepcopy(existing), config)
    proposals = {}
    for mode, candidate in candidates.items():
        print('Proposed .gantry/config.json:' + (f' ({mode})' if existing is not None else ''))
        print(json.dumps(candidate, indent=2))
        candidate_host = candidate.get('execution', {}).get('hostHarness')
        writes, guidance = adapter_proposal(root, candidate_host, candidate) if candidate_host else ({}, ['No selected host adapter; existing adapters remain unchanged.'])
        proposals[mode] = writes
        for message in guidance:
            print(message)
        for adapter, content in writes.items():
            print(f'Proposed adapter effects ({mode}): {adapter.relative_to(root)}')
            print(content)
        agents_host = candidate.get('execution', {}).get('hostHarness')
        print('AGENTS.md effect: update only the marked Gantry section' + (' with Codex guardrails.' if agents_host == 'codex' else '.'))
    if existing is not None:
        answer = confirm('Config exists. [M]erge, [O]verwrite, or [A]bort? ')
        mode = {'m': 'merge', 'merge': 'merge', 'o': 'overwrite', 'overwrite': 'overwrite'}.get(answer)
    else:
        mode = 'overwrite' if confirm('Write this policy? [y/N] ') in ('y', 'yes') else None
    if mode is None:
        print('Aborted. No files changed.')
        return 1
    final = candidates[mode]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8')
    for adapter, content in proposals[mode].items():
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_text(content, encoding='utf-8')
    update_agents(root, final.get('execution', {}).get('hostHarness'))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--config', help='JSON config as one structured argument')
    source.add_argument('--config-file', help='Path to JSON config file (recommended)')
    parser.add_argument('--harness', choices=sorted(SUPPORTED_HARNESSES), help='Intentional normal setup host selection')
    parser.add_argument('--verify-auth', action='store_true', help='Verify Codex discovery during normal setup')
    parser.add_argument('--host-only', action='store_true', help='Preview host-only policy and selected adapter repair without role presets')
    parser.add_argument('--personal', action='store_true', help='Personal harness and role overlay switch in machine profile')
    parser.add_argument('--migrate-legacy', action='store_true', help='Migrate legacy tracked execution.hostHarness to operator profile')
    parser.add_argument('--host', help='Operator-confirmed identity for host-only repair or personal switch')
    parser.add_argument('--roles', help='JSON string for role overrides in personal profile')
    parser.add_argument('--roles-file', help='Path to JSON file for role overrides in personal profile')
    parser.add_argument('--apply', action='store_true', help='Ask approval to apply the displayed proposal')
    args = parser.parse_args()

    if args.personal:
        if args.host_only or args.migrate_legacy or args.config or args.config_file or args.harness or args.verify_auth:
            parser.error('--personal accepts only --host, --roles, --roles-file, and --apply')
        roles = None
        if args.roles_file:
            roles = json.loads(Path(args.roles_file).read_text(encoding='utf-8'))
        elif args.roles:
            roles = json.loads(args.roles)
        try:
            return personal_switch(Path.cwd(), args.host, roles, args.apply)
        except (ValueError, OSError, UnicodeError) as error:
            print(f'Setup error: {error}. Application stopped.', file=sys.stderr)
            return 2

    if args.migrate_legacy:
        if args.host_only or args.personal or args.config or args.config_file or args.harness or args.verify_auth or args.host or args.roles or args.roles_file:
            parser.error('--migrate-legacy accepts only --apply')
        try:
            return migrate_legacy(Path.cwd(), args.apply)
        except (ValueError, OSError, UnicodeError) as error:
            print(f'Setup error: {error}. Application stopped.', file=sys.stderr)
            return 2

    if args.host_only and (args.config or args.config_file or args.harness or args.verify_auth or args.roles or args.roles_file):
        parser.error('--host-only accepts only --host and --apply; role/config updates require normal setup')
    if not args.host_only and not args.personal and (args.host or args.apply):
        parser.error('--host and --apply require --host-only or --personal')
    try:
        return host_only(Path.cwd(), args.host, args.apply) if args.host_only else normal_setup(Path.cwd(), args)
    except (ValueError, OSError, UnicodeError) as error:
        print(f'Setup error: {error}. Application stopped.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
