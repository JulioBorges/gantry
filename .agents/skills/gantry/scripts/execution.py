#!/usr/bin/env python3
"""Role execution resolution, validation, and preflight across harnesses."""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import datetime
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).parent))

from common import repo_root, resolve_policy
import result  # noqa: E402
import runlog  # noqa: E402

SUPPORTED_HARNESSES = {"antigravity", "claude-code", "codex", "opencode"}

MIN_SUPPORTED_VERSIONS = {
    "antigravity": "1.0.0",
    "claude-code": "1.0.0",
    "opencode": "0.1.0",
    "codex": "0.1.0",
}

CLI_NAMES = {
    "antigravity": "agy",
    "claude-code": "claude",
    "opencode": "opencode",
    "codex": "codex",
}

ROLE_TO_SCHEMA = {
    "plan": "planner",
    "planner": "planner",
    "implement": "implementer",
    "implementer": "implementer",
    "review": "reviewer",
    "reviewer": "reviewer",
    "critic": "critic",
    "requirement-critic": "requirement-critic",
    "plan-critic": "plan-critic",
    "research": None,
    "learner": "learner",
}


class UnsupportedHarnessVersionError(Exception):
    """Raised when an installed harness version is below the supported threshold or invalid."""


class ModelFallbackError(Exception):
    """Raised when native or configured automatic model fallback is detected."""


class ProtocolFailureError(Exception):
    """Raised when an external role result is missing, undecodable or fails the schema contract."""


def parse_semver(version_str: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version_str)
    if not match:
        raise ValueError(f"Cannot parse version string: {version_str!r}")
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)
    return (major, minor, patch)


def validate_harness_version(
    harness: str,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    cli_name = CLI_NAMES.get(harness, harness)
    try:
        if runner:
            try:
                proc = runner([cli_name, "--version"])
            except TypeError:
                proc = runner([cli_name, "--version"], capture_output=True, text=True, check=False)
        else:
            proc = subprocess.run([cli_name, "--version"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return {
                "valid": False,
                "version": None,
                "error": f"Harness CLI {cli_name} authentication/execution validation failed: return code {proc.returncode}",
            }
        stdout = (proc.stdout or "").strip() or (proc.stderr or "").strip()
        version_tuple = parse_semver(stdout)
        min_ver_str = MIN_SUPPORTED_VERSIONS.get(harness, "0.0.0")
        min_tuple = parse_semver(min_ver_str)
        if version_tuple < min_tuple:
            ver_formatted = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
            return {
                "valid": False,
                "version": ver_formatted,
                "error": f"Unsupported installed version {ver_formatted} for {harness}. Minimum supported is {min_ver_str}.",
            }
        ver_formatted = f"{version_tuple[0]}.{version_tuple[1]}.{version_tuple[2]}"
        return {"valid": True, "version": ver_formatted}
    except Exception as exc:
        return {
            "valid": False,
            "version": None,
            "error": f"Harness CLI {cli_name} version check failed: {exc}",
        }


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

HARNESS_SUPPORTED_EFFORTS = {
    "antigravity": ["low", "medium", "high"],
    "codex": ["low", "medium", "high"],
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
        if supported_efforts is None:
            supported_efforts = HARNESS_SUPPORTED_EFFORTS.get(harness)
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
        ver_check = validate_harness_version(harness, runner=runner)
        if not ver_check["valid"]:
            return {
                "valid": False,
                "role": role,
                "error": ver_check["error"],
            }

    return {"valid": True, "role": role}


def build_dispatch_command(
    harness: str,
    model: str,
    prompt: str,
    effort: str | None = None,
    output_format: str = "json",
) -> list[str]:
    """Build the bounded native CLI dispatch command for a role invocation."""
    h = (harness or "").lower()
    if h == "antigravity":
        cmd = ["agy", "--print", "--model", model]
        if effort:
            cmd.extend(["--effort", effort])
        cmd.extend(["--output-format", output_format, "--dangerously-skip-permissions", prompt])
        return cmd
    elif h == "claude-code":
        return ["claude", "-p", prompt, "--model", model, "--dangerously-skip-permissions"]
    elif h == "opencode":
        return ["opencode", "run", prompt, "--model", model]
    elif h == "codex":
        return ["codex", "exec", prompt, "--model", model]
    else:
        raise ValueError(f"Unsupported harness: {harness}")


def check_model_fallback(requested_model: str, output_data: dict[str, Any] | str) -> None:
    """Detect if the harness silently replaced the requested model with a fallback model."""
    if isinstance(output_data, str):
        if "fallback" in output_data.lower() and "model" in output_data.lower():
            fb_match = re.search(r"falling back to (\S+)|fallback model:?\s*(\S+)", output_data, re.IGNORECASE)
            if fb_match:
                reported = fb_match.group(1) or fb_match.group(2)
                raise ModelFallbackError(
                    f"Automatic model fallback detected: requested {requested_model!r} but fell back to {reported!r}"
                )
        try:
            parsed = json.loads(output_data)
            if isinstance(parsed, dict):
                output_data = parsed
        except Exception:
            pass

    if isinstance(output_data, dict):
        reported = output_data.get("model") or output_data.get("effective_model") or output_data.get("actual_model")
        if reported and str(reported).strip().lower() != requested_model.strip().lower():
            raise ModelFallbackError(
                f"Automatic model fallback detected: requested {requested_model!r} but harness used {reported!r}"
            )
        if output_data.get("fallback_occurred") or output_data.get("model_fallback"):
            raise ModelFallbackError(
                f"Automatic model fallback detected for model {requested_model!r}"
            )


def parse_and_validate_result(
    role: str,
    raw_output: str,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse output and validate against the Result Contract; protocol failure on error."""
    if not raw_output or not raw_output.strip():
        raise ProtocolFailureError(f"Protocol failure: empty output returned for role {role}")

    text = raw_output.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProtocolFailureError(f"Protocol failure: invalid JSON output for role {role}: {exc}") from exc

    if not isinstance(data, dict):
        raise ProtocolFailureError(f"Protocol failure: expected JSON object for role {role}, got {type(data).__name__}")

    schema_role = ROLE_TO_SCHEMA.get(role, role)
    if schema_role:
        if schema is None:
            try:
                schema = result.load_schema(schema_role)
            except Exception as exc:
                raise ProtocolFailureError(f"Protocol failure: failed to load schema for {schema_role}: {exc}") from exc
        errors = result.validate(data, schema)
        if errors:
            raise ProtocolFailureError(f"Protocol failure: schema validation failed for {role}: {errors}")

    return data


def verify_critic_result(critic_result: dict[str, Any]) -> None:
    """Verify that Critic independently verified criteria and gates without accepting a summary.

    Permission or tool limitations must fail visibly rather than accepting a summary.
    """
    if not isinstance(critic_result, dict):
        raise ProtocolFailureError("Critic result must be a JSON object")

    if critic_result.get("permission_error") or critic_result.get("tool_limitation"):
        err = critic_result.get("error") or "Critic encountered permission or tool limitation"
        raise RuntimeError(f"Critic execution failed visibly: {err}")

    if critic_result.get("complete") is True:
        gate_result = critic_result.get("gateResult")
        if not gate_result or not isinstance(gate_result, dict):
            raise ProtocolFailureError("Critic claimed complete=true without required gateResult")
        if gate_result.get("verdict") != "pass":
            raise ProtocolFailureError(f"Critic claimed complete=true but gateResult verdict is {gate_result.get('verdict')!r}")

        criteria = critic_result.get("criteria")
        if not isinstance(criteria, list) or len(criteria) == 0:
            raise ProtocolFailureError("Critic claimed complete=true with empty criteria list")
        for c in criteria:
            if not isinstance(c, dict) or not c.get("met") or not str(c.get("evidence", "")).strip():
                raise ProtocolFailureError(f"Critic claimed complete=true but criterion lacks verified evidence: {c}")


def dispatch_role(
    role: str,
    prompt: str,
    cwd: Path | str,
    selection: dict[str, Any] | None = None,
    policy: dict | None = None,
    run_overrides: dict | None = None,
    issue_overrides: dict | None = None,
    environment_defaults: dict | None = None,
    runner: Callable[..., Any] | None = None,
    run_id: str | None = None,
    unit_id: str | None = None,
    state_root: str | None = None,
    retry_on_invalid: bool = True,
) -> dict[str, Any]:
    """Execute a bounded role invocation in the selected native harness."""
    cwd_path = Path(cwd).resolve()
    if not cwd_path.is_dir():
        raise ValueError(f"Working directory {cwd_path} does not exist")

    eff_selection = selection or resolve_single_role(
        role,
        policy=policy,
        run_overrides=run_overrides,
        issue_overrides=issue_overrides,
        environment_defaults=environment_defaults,
    )
    harness = eff_selection.get("harness", "")
    model = eff_selection.get("model", "")
    effort = eff_selection.get("effort")

    ver_check = validate_harness_version(harness, runner=runner)
    if not ver_check["valid"]:
        raise UnsupportedHarnessVersionError(ver_check["error"])

    eff_val = validate_selection(eff_selection, role=role, root=cwd_path, check_auth=False)
    if not eff_val["valid"]:
        raise ValueError(eff_val["error"])

    if run_id and unit_id:
        try:
            root = runlog.state_root(state_root)
            log_path = runlog.run_log_path(root, unit_id, run_id)
            if log_path.exists():
                event_data = {
                    "role": role,
                    "harness": harness,
                    "model": model,
                    "cwd": str(cwd_path),
                }
                if effort:
                    event_data["effort"] = effort
                runlog.append_event(
                    log_path,
                    runlog.validate_event({
                        "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "run": run_id,
                        "event": "subagent.started",
                        "data": event_data,
                    }),
                )
        except Exception:
            pass

    cmd = build_dispatch_command(harness, model, prompt, effort=effort)
    run_fn = runner or subprocess.run
    proc = run_fn(cmd, cwd=str(cwd_path), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or (proc.stdout or "").strip()
        raise RuntimeError(f"Harness {harness} execution failed (exit {proc.returncode}): {err}")

    check_model_fallback(model, proc.stdout)

    try:
        data = parse_and_validate_result(role, proc.stdout)
        if role in ("critic", "requirement-critic", "plan-critic"):
            verify_critic_result(data)
    except ProtocolFailureError as exc:
        if retry_on_invalid:
            retry_prompt = f"{prompt}\n\nYour prior result was invalid: {exc}\nReturn the complete {role} result contract."
            retry_cmd = build_dispatch_command(harness, model, retry_prompt, effort=effort)
            proc2 = run_fn(retry_cmd, cwd=str(cwd_path), capture_output=True, text=True, check=False)
            if proc2.returncode != 0:
                raise RuntimeError(f"Harness {harness} retry failed (exit {proc2.returncode}): {(proc2.stderr or '').strip()}")
            check_model_fallback(model, proc2.stdout)
            data = parse_and_validate_result(role, proc2.stdout)
            if role in ("critic", "requirement-critic", "plan-critic"):
                verify_critic_result(data)
        else:
            raise

    if run_id and unit_id:
        try:
            root = runlog.state_root(state_root)
            log_path = runlog.run_log_path(root, unit_id, run_id)
            if log_path.exists():
                event_data = {
                    "role": role,
                    "harness": harness,
                    "model": model,
                    "result": data,
                }
                if effort:
                    event_data["effort"] = effort
                runlog.append_event(
                    log_path,
                    runlog.validate_event({
                        "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "run": run_id,
                        "event": "subagent.stopped",
                        "data": event_data,
                    }),
                )
        except Exception:
            pass

    return data


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


def validate_role_replacement(
    role: str,
    selection: dict[str, Any],
    issue_ref: str,
    root: Path | None = None,
    check_auth: bool = False,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Validate an explicit role replacement for an Issue without mutating defaults."""
    if not isinstance(selection, dict):
        return {"valid": False, "error": "Replacement selection must be an object"}
    val = validate_selection(selection, role=role, root=root, check_auth=check_auth, runner=runner)
    if not val["valid"]:
        return {"valid": False, "error": val["error"]}
    return {
        "valid": True,
        "role": role,
        "issue": issue_ref,
        "selection": selection,
    }


def check_unresolved_failures(
    unit_id: str,
    run_id: str,
    state_root_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Derive unresolved paused executions from the Run log.

    An issue execution is paused if an `issue.paused` event was recorded.
    It is considered resolved if a later `role.changed` event was recorded for that same issue and role.
    """
    root = runlog.state_root(str(state_root_path) if state_root_path else None)
    log_path = runlog.run_log_path(root, unit_id, run_id)
    if not log_path.is_file():
        return []

    events = runlog.read_valid_events(log_path)
    paused_map: dict[tuple[str, str], dict[str, Any]] = {}

    for event in events:
        ev_type = event.get("event")
        issue = event.get("issue")
        data = event.get("data", {})
        if ev_type == "issue.paused" and issue:
            role = data.get("role", "critic")
            paused_map[(issue, role)] = {
                "issue": issue,
                "role": role,
                "worktree": data.get("worktree"),
                "reason": data.get("reason", "execution_unavailable"),
                "error": data.get("error", "execution unavailable"),
            }
        elif ev_type == "role.changed" and issue:
            role = data.get("role", "critic")
            paused_map.pop((issue, role), None)
        elif ev_type in ("issue.done", "issue.blocked") and issue:
            for key in list(paused_map.keys()):
                if key[0] == issue:
                    paused_map.pop(key, None)

    return list(paused_map.values())


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

    dispatch_parser = subparsers.add_parser("dispatch", help="dispatch bounded role invocation")
    dispatch_parser.add_argument("--role", required=True, help="role to execute")
    dispatch_parser.add_argument("--prompt", help="prompt text (or via stdin)")
    dispatch_parser.add_argument("--cwd", default=".", help="working directory")
    dispatch_parser.add_argument("--selection", help="JSON selection object with harness, model, effort")
    dispatch_parser.add_argument("--run-overrides", help="JSON string of run-level overrides")
    dispatch_parser.add_argument("--issue-overrides", help="JSON string of issue-level overrides")
    dispatch_parser.add_argument("--run-id", help="Run ID for logging")
    dispatch_parser.add_argument("--unit-id", help="Unit ID for logging")
    dispatch_parser.add_argument("--state-root", help="State root directory")
    dispatch_parser.add_argument("--json", action="store_true", help="output JSON")

    failures_parser = subparsers.add_parser("unresolved-failures", help="check for unresolved paused executions")
    failures_parser.add_argument("unit_id", help="repository unit ID")
    failures_parser.add_argument("run_id", help="run ID")
    failures_parser.add_argument("--state-root", help="override state root")
    failures_parser.add_argument("--json", action="store_true", help="output JSON")

    validate_rep_parser = subparsers.add_parser("validate-replacement", help="validate role replacement")
    validate_rep_parser.add_argument("--issue", required=True, help="issue ref")
    validate_rep_parser.add_argument("--role", required=True, help="role name")
    validate_rep_parser.add_argument("--selection", required=True, help="selection JSON")
    validate_rep_parser.add_argument("--cwd", default=".", help="repository root path")
    validate_rep_parser.add_argument("--json", action="store_true", help="output JSON")

    args = parser.parse_args()
    root = Path(args.cwd).resolve() if getattr(args, "cwd", None) else Path(".").resolve()
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

    elif args.command == "dispatch":
        prompt = args.prompt
        if not prompt:
            prompt = sys.stdin.read()
        selection = json.loads(args.selection) if getattr(args, "selection", None) else None
        try:
            res = dispatch_role(
                role=args.role,
                prompt=prompt,
                cwd=root,
                selection=selection,
                policy=policy,
                run_overrides=run_ov,
                issue_overrides=issue_ov,
                run_id=getattr(args, "run_id", None),
                unit_id=getattr(args, "unit_id", None),
                state_root=getattr(args, "state_root", None),
            )
            print(json.dumps(res, indent=2))
            return 0
        except ProtocolFailureError as exc:
            print(f"protocol failure: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"execution failure: {exc}", file=sys.stderr)
            return 1

    elif args.command == "unresolved-failures":
        failures = check_unresolved_failures(
            unit_id=args.unit_id,
            run_id=args.run_id,
            state_root_path=getattr(args, "state_root", None),
        )
        if args.json:
            print(json.dumps(failures, indent=2))
        else:
            print(f"Unresolved failures: {len(failures)}")
            for f in failures:
                print(f"  - {f['issue']} ({f['role']}): {f['reason']}")
        return 0

    elif args.command == "validate-replacement":
        sel = json.loads(args.selection)
        res = validate_role_replacement(
            role=args.role,
            selection=sel,
            issue_ref=args.issue,
            root=root,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("Valid" if res["valid"] else f"Invalid: {res.get('error')}")
        return 0 if res["valid"] else 1

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
