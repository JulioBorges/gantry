#!/usr/bin/env python3
"""Wait for operator approval after Critic verification before starting Integrate."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import threading
import time
from pathlib import Path

from runlog import ISSUE_RE, RUN_ID_RE, UNIT_ID_RE, append_event, read_marker, resolve_hook_run, run_log_path, state_root as default_state_root, unit_id as derive_unit_id


class WaitGateError(ValueError):
    """The gate check cannot execute safely with the provided arguments."""


def approval_marker_path(root: Path, unit: str, issue: str) -> Path:
    return root / unit / "approvals" / f"{issue}.json"


def read_approval_marker(root: Path, unit: str, issue: str) -> dict | None:
    path = approval_marker_path(root, unit, issue)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("issue") == issue:
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None


def write_approval_marker(root: Path, unit: str, run: str, issue: str, source: str = "terminal") -> Path:
    path = approval_marker_path(root, unit, issue)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "unit": unit,
        "run": run,
        "issue": issue,
        "approvedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Record operator.approved in Run log if run log exists
    log_path = run_log_path(root, unit, run)
    if log_path.exists():
        try:
            append_event(
                log_path,
                {
                    "ts": payload["approvedAt"],
                    "run": run,
                    "event": "operator.approved",
                    "issue": issue,
                    "data": {"approvedAt": payload["approvedAt"], "source": source},
                },
            )
        except Exception:
            pass
    return path


def wait_for_gate(
    root: Path,
    unit: str,
    run: str,
    issue: str,
    timeout: float | None = None,
    poll_interval: float = 0.2,
    prompt: bool = True,
) -> int:
    start_time = time.time()
    marker = read_approval_marker(root, unit, issue)
    if marker:
        print(json.dumps({"approved": True, "issue": issue, "source": marker.get("source", "marker"), "approvedAt": marker.get("approvedAt")}))
        return 0

    user_input: list[str] = []
    if prompt and sys.stdin.isatty():
        sys.stderr.write(f"\n[GANTRY GATE] Issue {issue} passed Critic verification.\n")
        sys.stderr.write("Press [Enter] or type 'y' to approve and proceed to Integrate (or approve in Dashboard UI): ")
        sys.stderr.flush()

        def _reader() -> None:
            try:
                line = sys.stdin.readline()
                user_input.append(line.strip().lower())
            except Exception:
                pass

        t = threading.Thread(target=_reader, daemon=True)
        t.start()

    while True:
        # 1. Check approval marker
        marker = read_approval_marker(root, unit, issue)
        if marker:
            print(json.dumps({"approved": True, "issue": issue, "source": marker.get("source", "marker"), "approvedAt": marker.get("approvedAt")}))
            return 0

        # 2. Check terminal stdin if available
        if user_input:
            line = user_input[0]
            if line in ("", "y", "yes", "approve", "ok", "1"):
                write_approval_marker(root, unit, run, issue, source="terminal")
                print(json.dumps({"approved": True, "issue": issue, "source": "terminal"}))
                return 0

        if timeout is not None and timeout > 0:
            if (time.time() - start_time) >= timeout:
                sys.stderr.write(f"\n[GANTRY GATE] Timeout waiting for operator approval for {issue}.\n")
                return 1

        time.sleep(poll_interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", nargs="?", help="Issue reference e.g. sample#01")
    parser.add_argument("--issue", dest="opt_issue", help="Issue reference")
    parser.add_argument("--unit", help="Execution unit ID")
    parser.add_argument("--run", help="Run ID")
    parser.add_argument("--state-root", help="State root directory")
    parser.add_argument("--cwd", default=".", help="Current working directory")
    parser.add_argument("--poll-interval", type=float, default=0.2, help="Poll interval in seconds")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    parser.add_argument("--check", action="store_true", help="Check approval status non-blocking and exit")
    parser.add_argument("--approve", action="store_true", help="Approve gate immediately and exit")
    args = parser.parse_args(argv)

    issue = args.issue or args.opt_issue
    if not issue or not ISSUE_RE.fullmatch(issue):
        print(f"wait-gate error: valid issue reference required (e.g. sample#01), got {issue!r}", file=sys.stderr)
        return 2

    cwd = Path(args.cwd).resolve()
    root = Path(args.state_root).expanduser().resolve() if args.state_root else default_state_root(None)

    unit = args.unit
    if not unit:
        try:
            unit = derive_unit_id(cwd)
        except Exception:
            unit = "000000000000"
    if not UNIT_ID_RE.fullmatch(unit):
        print(f"wait-gate error: invalid unit id {unit!r}", file=sys.stderr)
        return 2

    run = args.run
    if not run:
        env_run, _ = resolve_hook_run(cwd)
        run = env_run or "run-default"
    if not RUN_ID_RE.fullmatch(run):
        print(f"wait-gate error: invalid run id {run!r}", file=sys.stderr)
        return 2

    if args.approve:
        write_approval_marker(root, unit, run, issue, source="terminal")
        print(json.dumps({"approved": True, "issue": issue, "source": "terminal"}))
        return 0

    if args.check:
        marker = read_approval_marker(root, unit, issue)
        if marker:
            print(json.dumps({"approved": True, "issue": issue, "source": marker.get("source", "marker"), "approvedAt": marker.get("approvedAt")}))
            return 0
        return 1

    return wait_for_gate(root, unit, run, issue, timeout=args.timeout, poll_interval=args.poll_interval)


if __name__ == "__main__":
    sys.exit(main())
