#!/usr/bin/env python3
"""Append and query the machine-local, append-only Gantry Run log."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EVENTS = {
    "run.started",
    "run.resumed",
    "run.cancelled",
    "run.finished",
    "round.started",
    "round.finished",
    "phase.started",
    "phase.finished",
    "subagent.started",
    "subagent.stopped",
    "compaction",
    "hook.denied",
    "policy.changed",
    "issue.done",
    "issue.blocked",
    "refutation",
    "review.finding",
}
RUN_EVENTS = {"run.started", "run.resumed", "run.cancelled", "run.finished"}
ROUND_EVENTS = {"round.started", "round.finished"}
PHASE_EVENTS = {"phase.started", "phase.finished"}
SUBAGENT_EVENTS = {"subagent.started", "subagent.stopped"}
ISSUE_EVENTS = {"issue.done", "issue.blocked", "refutation", "review.finding"}
FINISHED_EVENTS = {"run.cancelled", "run.finished"}
UNIT_ID_RE = re.compile(r"^[0-9a-f]{12}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
ISSUE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*#\d{2,}$")
PROHIBITED_KEY_TOKENS = {"command", "commands", "cmd", "diff", "diffs", "output", "outputs", "patch", "patches", "stderr", "stdout"}


class EventError(ValueError):
    """An event cannot safely be written to the Run log."""


def state_root(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else Path.home() / ".gantry" / "state"


def unit_id(cwd: Path) -> str:
    """Derive the shared execution-unit identifier for a repository worktree."""
    try:
        common_dir = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise EventError(f"could not resolve Git common directory: {error}") from error
    path = Path(common_dir)
    real_common_dir = (cwd / path).resolve() if not path.is_absolute() else path.resolve()
    return hashlib.sha256(str(real_common_dir).encode("utf-8")).hexdigest()[:12]


def require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"{name} must be a non-empty string")
    return value


def require_positive_integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise EventError(f"{name} must be a positive integer")
    return value


def validate_timestamp(value: object) -> None:
    timestamp = require_string(value, "ts")
    try:
        datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise EventError("ts must be an ISO 8601 timestamp") from error


def validate_sensitive_data(value: object, path: str = "data") -> None:
    """Reject command, output, diff, and patch fields at every nesting level."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise EventError(f"{path} keys must be strings")
            words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key)
            tokens = re.findall(r"[a-z]+", words.lower())
            if any(token in PROHIBITED_KEY_TOKENS for token in tokens):
                raise EventError(f"{path}.{key} must not be stored in the Run log")
            validate_sensitive_data(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            validate_sensitive_data(nested, f"{path}[{index}]")


def validate_secret_checks(value: object, path: str = "data") -> None:
    if isinstance(value, dict):
        if value.get("secrets") is True:
            permitted = {"secrets", "exitCode", "counts"}
            unexpected = sorted(set(value) - permitted)
            if unexpected:
                raise EventError(f"{path} for a secrets check may record only exitCode and counts")
            if "exitCode" not in value or "counts" not in value:
                raise EventError(f"{path} for a secrets check requires exitCode and counts")
            if not isinstance(value["exitCode"], int) or isinstance(value["exitCode"], bool):
                raise EventError(f"{path}.exitCode must be an integer")
            if not isinstance(value["counts"], dict):
                raise EventError(f"{path}.counts must be an object")
        for key, nested in value.items():
            validate_secret_checks(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            validate_secret_checks(nested, f"{path}[{index}]")


def validate_event(payload: object) -> dict:
    """Validate a stable event envelope before it reaches persistent state."""
    if not isinstance(payload, dict):
        raise EventError("event must be a JSON object")
    unknown = sorted(set(payload) - {"ts", "run", "event", "issue", "phase", "data"})
    if unknown:
        raise EventError(f"unknown event fields: {', '.join(unknown)}")
    for field in ("ts", "run", "event"):
        if field not in payload:
            raise EventError(f"event is missing required field: {field}")
    validate_timestamp(payload["ts"])
    run = require_string(payload["run"], "run")
    if not RUN_ID_RE.fullmatch(run):
        raise EventError("run must contain only letters, numbers, dots, colons, underscores, or hyphens")
    event = payload["event"]
    if event not in EVENTS:
        raise EventError(f"unknown event: {event!r}")
    if "issue" in payload:
        issue = require_string(payload["issue"], "issue")
        if not ISSUE_RE.fullmatch(issue):
            raise EventError("issue must be an Issue reference such as sample#01")
    if "phase" in payload:
        require_string(payload["phase"], "phase")
    data = payload.get("data")
    if data is not None and not isinstance(data, dict):
        raise EventError("data must be an object when supplied")
    validate_sensitive_data(data)
    validate_secret_checks(data)

    if event == "run.started":
        if "data" not in payload:
            raise EventError("run.started requires data")
        for field in ("repositoryRoot", "policyHash", "tier", "staleAfterSeconds"):
            if field not in data:
                raise EventError(f"run.started data is missing required field: {field}")
        require_string(data["repositoryRoot"], "data.repositoryRoot")
        require_string(data["policyHash"], "data.policyHash")
        require_string(data["tier"], "data.tier")
        require_positive_integer(data["staleAfterSeconds"], "data.staleAfterSeconds")
    elif event in ROUND_EVENTS:
        if not isinstance(data, dict) or "round" not in data:
            raise EventError(f"{event} requires data.round")
        require_positive_integer(data["round"], "data.round")
    elif event in PHASE_EVENTS:
        if "issue" not in payload or "phase" not in payload:
            raise EventError(f"{event} requires issue and phase")
    elif event in SUBAGENT_EVENTS:
        if not isinstance(data, dict) or "role" not in data:
            raise EventError(f"{event} requires data.role")
        require_string(data["role"], "data.role")
    elif event == "compaction":
        if not isinstance(data, dict) or "source" not in data:
            raise EventError("compaction requires data.source")
        require_string(data["source"], "data.source")
    elif event == "hook.denied":
        if not isinstance(data, dict) or not {"rule", "path"} <= set(data):
            raise EventError("hook.denied requires data.rule and data.path")
        require_string(data["rule"], "data.rule")
        require_string(data["path"], "data.path")
    elif event == "policy.changed":
        if not isinstance(data, dict) or "policyHash" not in data:
            raise EventError("policy.changed requires data.policyHash")
        require_string(data["policyHash"], "data.policyHash")
    elif event in ISSUE_EVENTS and "issue" not in payload:
        raise EventError(f"{event} requires issue")
    return payload


def run_log_path(root: Path, unit: str, run: str) -> Path:
    return root / unit / "runs" / f"{run}.jsonl"


def append_event(path: Path, payload: dict) -> None:
    """Append a sub-64 KB JSONL event with exactly one write system call."""
    encoded = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    if len(encoded) > 64 * 1024:
        raise EventError("event exceeds the 64 KB atomic append limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        written = os.write(descriptor, encoded)
        if written != len(encoded):
            raise EventError("could not write a complete Run log event")
    finally:
        os.close(descriptor)


def read_valid_events(path: Path) -> list[dict]:
    events: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return events
    for line in lines:
        try:
            payload = validate_event(json.loads(line))
        except (EventError, json.JSONDecodeError):
            continue
        if payload["run"] != path.stem:
            continue
        events.append(payload)
    return events


def inflight(root: Path, unit: str) -> list[dict]:
    """Derive unfinished Issue phases from valid events only."""
    result: list[dict] = []
    for path in sorted((root / unit / "runs").glob("*.jsonl")):
        events = read_valid_events(path)
        if not events or events[0]["event"] != "run.started":
            continue
        started = events[0]
        active: dict[str, dict] = {}
        finished = False
        for event in events[1:]:
            if event["event"] in FINISHED_EVENTS:
                finished = True
                continue
            if event["event"] == "phase.started":
                active[event["issue"]] = {
                    "run": event["run"],
                    "issue": event["issue"],
                    "phase": event["phase"],
                    "worktree": event.get("data", {}).get("worktree"),
                }
            elif event["event"] == "phase.finished":
                active.pop(event["issue"], None)
            elif event["event"] in {"issue.done", "issue.blocked"}:
                active.pop(event["issue"], None)
        if not finished:
            for item in active.values():
                if isinstance(item["worktree"], str) and item["worktree"]:
                    result.append(
                        {
                            **item,
                            "repositoryRoot": started["data"]["repositoryRoot"],
                            "policyHash": started["data"]["policyHash"],
                            "tier": started["data"]["tier"],
                            "staleAfterSeconds": started["data"]["staleAfterSeconds"],
                        }
                    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    unit_parser = subparsers.add_parser("unit-id", help="print the current repository execution-unit ID")
    unit_parser.add_argument("--cwd", default=".", help="repository or worktree to inspect")
    unit_parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    append_parser = subparsers.add_parser("append", help="append one JSON event from standard input")
    append_parser.add_argument("unit_id", help="twelve-hex repository execution-unit ID")
    append_parser.add_argument("run_id", nargs="?", help="optional Run ID, which must match the event")
    append_parser.add_argument("--state-root", help="override ~/.gantry/state")
    query_parser = subparsers.add_parser("inflight", help="list interrupted Issue phases")
    query_parser.add_argument("unit_id", help="twelve-hex repository execution-unit ID")
    query_parser.add_argument("--state-root", help="override ~/.gantry/state")
    query_parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    try:
        if args.command == "unit-id":
            value = unit_id(Path(args.cwd).resolve())
            payload = {"unitId": value}
            print(json.dumps(payload, sort_keys=True) if args.json else value)
            return 0
        if not UNIT_ID_RE.fullmatch(args.unit_id):
            raise EventError("unit-id must be exactly twelve lowercase hexadecimal characters")
        root = state_root(args.state_root)
        if args.command == "append":
            try:
                payload = json.loads(sys.stdin.read())
            except json.JSONDecodeError as error:
                raise EventError(f"standard input must contain one JSON event: {error.msg}") from error
            event = validate_event(payload)
            if args.run_id and event["run"] != args.run_id:
                raise EventError("positional run-id must match event.run")
            path = run_log_path(root, args.unit_id, event["run"])
            if path.exists() and event["event"] == "run.started":
                raise EventError("a Run log already starts for this run-id")
            if not path.exists() and event["event"] != "run.started":
                raise EventError("the first event of a Run must be run.started")
            append_event(path, event)
            return 0
        payload = {"unitId": args.unit_id, "inflight": inflight(root, args.unit_id)}
        print(json.dumps(payload, sort_keys=True) if args.json else "\n".join(
            f"{item['run']} {item['issue']} {item['phase']} {item['worktree']}" for item in payload["inflight"]
        ))
        return 0
    except EventError as error:
        print(f"runlog error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
