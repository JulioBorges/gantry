#!/usr/bin/env python3
"""Role execution resolution, validation, and preflight across harnesses."""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).parent))

from common import repo_root, resolve_policy

SUPPORTED_HARNESSES = {"antigravity", "claude-code", "codex", "opencode"}

BASE_ROLES = ("plan", "implement", "review", "critic")
DERIVED_ROLES = {
    "requirement-critic": "critic",
    "plan-critic": "critic",
    "research": "plan",
    "learner": "critic",
}
ALL_ROLES = (*BASE_ROLES, *DERIVED_ROLES.keys())


def validate_effort(
    model_id: str,
    effort: str | None,
    supported_efforts: list[str] | None = None,
) -> dict[str, Any]:
    """Validate that the requested reasoning effort is supported by the model."""
    if not effort:
        return {"valid": True}
    if not supported_efforts:
        return {
            "valid": False,
            "error": f"Model {model_id} does not declare supported reasoning effort values.",
        }
    normalized_supported = [e.lower() for e in supported_efforts]
    if effort.lower() not in normalized_supported:
        return {
            "valid": False,
            "error": f"Unsupported effort value {effort!r} for model {model_id}. Supported: {supported_efforts}",
        }
    return {"valid": True}

HARNESS_DEFAULT_MODELS = {
    "antigravity": "gemini-3.8-flash-medium",
    "claude-code": "claude-3-7-sonnet-20250219",
    "codex": "gpt-5.2-codex",
    "opencode": "claude-3-7-sonnet-20250219",
}

ENVIRONMENT_DEFAULTS = {
    "plan": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
    "implement": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
    "review": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
    "critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
}


def _fill_defaults(selection: dict[str, Any]) -> dict[str, Any]:
    res = copy.deepcopy(selection)
    harness = res.get("harness", "claude-code")
    res["harness"] = harness
    if "model" not in res or not res["model"]:
        res["model"] = HARNESS_DEFAULT_MODELS.get(harness, "claude-3-7-sonnet-20250219")
    return res


def resolve_single_role(
    role: str,
    policy: dict | None = None,
    run_overrides: dict | None = None,
    issue_overrides: dict | None = None,
    environment_defaults: dict | None = None,
) -> dict[str, Any]:
    """Resolve the effective execution selection for a single role.

    Resolution order:
    1. Issue-role override
    2. Run-role override
    3. Repository role default (policy["execution"]["roles"])
    4. Explicitly confirmed environment default

    Derived roles inherit from their parent role at each level unless explicitly set.
    """
    parent = DERIVED_ROLES.get(role)

    # 1. Issue-role override
    if issue_overrides:
        if role in issue_overrides:
            return _fill_defaults(issue_overrides[role])
        if parent and parent in issue_overrides:
            return _fill_defaults(issue_overrides[parent])

    # 2. Run-role override
    if run_overrides:
        if role in run_overrides:
            return _fill_defaults(run_overrides[role])
        if parent and parent in run_overrides:
            return _fill_defaults(run_overrides[parent])

    # 3. Repository role default
    roles_policy = (policy or {}).get("execution", {}).get("roles", {})
    if role in roles_policy:
        return _fill_defaults(roles_policy[role])
    if parent and parent in roles_policy:
        return _fill_defaults(roles_policy[parent])

    # 4. Environment default
    env_defs = environment_defaults or ENVIRONMENT_DEFAULTS
    if role in env_defs:
        return _fill_defaults(env_defs[role])
    if parent and parent in env_defs:
        return _fill_defaults(env_defs[parent])

    return _fill_defaults(ENVIRONMENT_DEFAULTS.get("plan", {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"}))


def resolve_roles(
    policy: dict | None = None,
    run_overrides: dict | None = None,
    issue_overrides: dict | None = None,
    environment_defaults: dict | None = None,
) -> dict[str, dict[str, Any]]:
    """Resolve all execution roles."""
    return {
        r: resolve_single_role(
            r,
            policy=policy,
            run_overrides=run_overrides,
            issue_overrides=issue_overrides,
            environment_defaults=environment_defaults,
        )
        for r in ALL_ROLES
    }


def assess_model_strength(roles: dict[str, dict[str, Any]]) -> list[str]:
    """Model strength guidance is advisory; returns non-blocking observations."""
    notes = []
    plan_model = roles.get("plan", {}).get("model", "")
    critic_model = roles.get("critic", {}).get("model", "")
    impl_model = roles.get("implement", {}).get("model", "")

    plan_harness = roles.get("plan", {}).get("harness", "")
    critic_harness = roles.get("critic", {}).get("harness", "")
    impl_harness = roles.get("implement", {}).get("harness", "")

    if critic_harness and impl_harness and critic_harness != impl_harness:
        notes.append(f"Advisory: Critic uses external harness {critic_harness!r} differing from Implementer {impl_harness!r}.")
    if "flash" in critic_model.lower() and "pro" in impl_model.lower():
        notes.append(f"Advisory: Critic model {critic_model!r} may have lower reasoning capacity than Implementer {impl_model!r}.")
    return notes


def validate_selection(
    selection: dict[str, Any],
    role: str = "unknown",
    root: Path | None = None,
    check_auth: bool = True,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Validate a single role execution selection."""
    harness = selection.get("harness", "")
    if harness not in SUPPORTED_HARNESSES:
        return {
            "valid": False,
            "role": role,
            "error": f"Unsupported harness {harness!r} for role {role}. Supported: {sorted(SUPPORTED_HARNESSES)}",
        }

    model = selection.get("model", "")
    if not model:
        return {
            "valid": False,
            "role": role,
            "error": f"No model specified for role {role} on harness {harness}.",
        }

    effort = selection.get("effort")
    if effort:
        cap_file = Path(__file__).resolve().parents[1] / "capabilities" / f"{harness}.json"
        supported_efforts = None
        if cap_file.exists():
            try:
                cap_data = json.loads(cap_file.read_text(encoding="utf-8"))
                model_meta = cap_data.get("models", {}).get(model, {})
                supported_efforts = model_meta.get("supportedEfforts")
            except Exception:
                pass
        eff_check = validate_effort(model, effort, supported_efforts=supported_efforts)
        if not eff_check["valid"]:
            return {
                "valid": False,
                "role": role,
                "error": eff_check.get("error", f"Invalid effort {effort} for model {model}"),
            }

    if root is not None and not root.is_dir():
        return {
            "valid": False,
            "role": role,
            "error": f"Working directory {root} does not exist",
        }

    if check_auth:
        cli_name = "agy" if harness == "antigravity" else "claude" if harness == "claude-code" else harness
        if runner:
            try:
                proc = runner([cli_name, "--version"])
                if proc.returncode != 0:
                    return {
                        "valid": False,
                        "role": role,
                        "error": f"Harness CLI {cli_name} authentication/execution validation failed: return code {proc.returncode}",
                    }
            except Exception as exc:
                return {
                    "valid": False,
                    "role": role,
                    "error": f"Harness CLI {cli_name} execution check failed: {exc}",
                }

    return {"valid": True, "role": role}


def preflight_validate(
    policy: dict | None = None,
    run_overrides: dict | None = None,
    issue_overrides: dict | None = None,
    environment_defaults: dict | None = None,
    root: Path | None = None,
    check_auth: bool = True,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Preflight check: resolve effective selections and validate all roles."""
    roles = resolve_roles(
        policy=policy,
        run_overrides=run_overrides,
        issue_overrides=issue_overrides,
        environment_defaults=environment_defaults,
    )
    errors = []
    for r, sel in roles.items():
        val = validate_selection(sel, role=r, root=root, check_auth=check_auth, runner=runner)
        if not val["valid"]:
            errors.append(val["error"])

    guidance = assess_model_strength(roles)
    valid = len(errors) == 0

    return {
        "valid": valid,
        "roles": roles,
        "errors": errors,
        "guidance": guidance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    resolve_parser = subparsers.add_parser("resolve", help="resolve effective role executions")
    resolve_parser.add_argument("--role", help="specific role to resolve")
    resolve_parser.add_argument("--run-overrides", help="JSON string of run-level overrides")
    resolve_parser.add_argument("--issue-overrides", help="JSON string of issue-level overrides")
    resolve_parser.add_argument("--cwd", default=".", help="repository root path")
    resolve_parser.add_argument("--json", action="store_true", help="output JSON")

    preflight_parser = subparsers.add_parser("preflight", help="run preflight validation across roles")
    preflight_parser.add_argument("--run-overrides", help="JSON string of run-level overrides")
    preflight_parser.add_argument("--issue-overrides", help="JSON string of issue-level overrides")
    preflight_parser.add_argument("--cwd", default=".", help="repository root path")
    preflight_parser.add_argument("--json", action="store_true", help="output JSON")

    args = parser.parse_args()
    root = Path(args.cwd).resolve()
    policy = resolve_policy(root)

    run_ov = json.loads(args.run_overrides) if getattr(args, "run_overrides", None) else None
    issue_ov = json.loads(args.issue_overrides) if getattr(args, "issue_overrides", None) else None

    if args.command == "resolve":
        if args.role:
            res = resolve_single_role(args.role, policy=policy, run_overrides=run_ov, issue_overrides=issue_ov)
        else:
            res = resolve_roles(policy=policy, run_overrides=run_ov, issue_overrides=issue_ov)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(res)
        return 0

    elif args.command == "preflight":
        res = preflight_validate(policy=policy, run_overrides=run_ov, issue_overrides=issue_ov, root=root)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res["valid"]:
                print("Preflight validation passed.")
                for g in res["guidance"]:
                    print(f"  {g}")
            else:
                print("Preflight validation FAILED:")
                for err in res["errors"]:
                    print(f"  - {err}", file=sys.stderr)
        return 0 if res["valid"] else 1

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
