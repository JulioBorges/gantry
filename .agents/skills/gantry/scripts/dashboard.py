#!/usr/bin/env python3
"""Serve a read-only, loopback-only, multi-Run kanban dashboard.

The dashboard never writes to an Issue, a policy, a Run log, a branch or a worktree: every
HTTP endpoint is a GET that renders data already produced by ``runlog.py``. Staleness is
always derived from the ``staleAfterSeconds`` snapshot recorded on each Run's ``run.started``
event, never from the current policy or a mutable dashboard action.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from runlog import read_valid_events
from runlog import state_root as default_state_root

COLUMNS = ["Ready", "Plan", "Implement", "Review", "Critic", "Integrate", "Done", "Blocked"]
STATIC_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "static"
STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.js": "app.js",
    "/style.css": "style.css",
}
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}
IGNORED_FOR_ACTIVITY = {"policy.changed"}


class DashboardError(ValueError):
    """The dashboard cannot serve safely with the requested configuration."""


def require_loopback_host(host: str) -> str:
    """Refuse to bind anywhere but the local loopback address."""
    if host != "127.0.0.1":
        raise DashboardError(f"dashboard must bind 127.0.0.1 only, refusing host {host!r}")
    return host


def _parse_ts(value: str) -> float:
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def build_run(unit_id: str, events: list[dict], now: float) -> dict:
    """Reduce one Run's valid event stream into swimlane and Issue-column state."""
    started = events[0]
    data = started["data"]
    stale_after = data["staleAfterSeconds"]

    activity_events = [event for event in events if event["event"] not in IGNORED_FOR_ACTIVITY]
    last_activity_ts = _parse_ts(activity_events[-1]["ts"]) if activity_events else _parse_ts(started["ts"])

    repo_root = data.get("repositoryRoot", "")
    project_name = Path(repo_root).name if repo_root else unit_id

    issues: dict[str, dict] = {}
    compaction_at = None
    for event in events[1:]:
        name = event["event"]
        if name == "compaction":
            compaction_at = event["ts"]
            continue
        issue = event.get("issue")
        if issue is None:
            continue
        state = issues.setdefault(
            issue,
            {
                "issue": issue,
                "column": "Ready",
                "branch": None,
                "worktree": None,
                "models": {},
                "correctionBudget": None,
                "phaseStartedAt": None,
                "operatorWaiting": False,
                "project": project_name,
                "unitId": unit_id,
                "run": started["run"],
                "repositoryRoot": repo_root,
            },
        )
        edata = event.get("data") or {}
        if name == "phase.started":
            state["column"] = event["phase"]
            state["phaseStartedAt"] = event["ts"]
            if "branch" in edata:
                state["branch"] = edata["branch"]
            if "worktree" in edata:
                state["worktree"] = edata["worktree"]
            if "models" in edata:
                state["models"] = dict(edata["models"])
            if "correctionBudget" in edata:
                state["correctionBudget"] = edata["correctionBudget"]
            state["operatorWaiting"] = bool(edata.get("operatorWaiting", False))
        elif name == "subagent.started":
            role = edata.get("role")
            if role:
                state["models"][role] = edata.get("model")
        elif name == "issue.done":
            state["column"] = "Done"
        elif name == "issue.blocked":
            state["column"] = "Blocked"

    for state in issues.values():
        if state["phaseStartedAt"] is not None:
            state["elapsedPhaseSeconds"] = max(0, int(now - _parse_ts(state["phaseStartedAt"])))
        else:
            state["elapsedPhaseSeconds"] = None

    return {
        "unitId": unit_id,
        "run": started["run"],
        "repositoryRoot": data["repositoryRoot"],
        "tier": data["tier"],
        "staleAfterSeconds": stale_after,
        "lastActivityAt": activity_events[-1]["ts"] if activity_events else started["ts"],
        "stale": (now - last_activity_ts) >= stale_after,
        "compactionAt": compaction_at,
        "issues": sorted(issues.values(), key=lambda item: item["issue"]),
    }


def collect_projects(root: Path, runs: list[dict] | None = None) -> list[dict]:
    """Collect project metadata across all execution units."""
    if runs is None:
        runs = collect_runs(root)
    projects_by_unit: dict[str, dict] = {}
    for run in runs:
        unit_id = run["unitId"]
        repo_root = run.get("repositoryRoot", "")
        name = Path(repo_root).name if repo_root else unit_id
        if unit_id not in projects_by_unit:
            projects_by_unit[unit_id] = {
                "unitId": unit_id,
                "name": name,
                "repositoryRoot": repo_root,
            }
    if root.exists():
        for unit_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            if unit_dir.name not in projects_by_unit:
                projects_by_unit[unit_dir.name] = {
                    "unitId": unit_dir.name,
                    "name": unit_dir.name,
                    "repositoryRoot": "",
                }
    return sorted(projects_by_unit.values(), key=lambda p: p["name"].lower())


def collect_runs(root: Path, now: float | None = None) -> list[dict]:
    """Read every Run log under every execution unit's state root."""
    now = time.time() if now is None else now
    runs: list[dict] = []
    if not root.exists():
        return runs
    for unit_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        runs_dir = unit_dir / "runs"
        if not runs_dir.exists():
            continue
        for log_path in sorted(runs_dir.glob("*.jsonl")):
            events = read_valid_events(log_path)
            if not events or events[0]["event"] != "run.started":
                continue
            runs.append(build_run(unit_dir.name, events, now))
    return runs


def make_handler(state_root: Path) -> type[BaseHTTPRequestHandler]:
    class DashboardRequestHandler(BaseHTTPRequestHandler):
        server_version = "GantryDashboard/1"

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - stdlib signature
            pass

        def _send_json(self, status: int, payload: object) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, filename: str) -> None:
            path = STATIC_DIR / filename
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", MIME_TYPES.get(path.suffix, "application/octet-stream"))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_not_found(self) -> None:
            body = b"not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - stdlib method name
            path = self.path.split("?", 1)[0]
            if path == "/api/state":
                runs = collect_runs(state_root)
                projects = collect_projects(state_root, runs)
                self._send_json(200, {"columns": COLUMNS, "runs": runs, "projects": projects})
                return
            filename = STATIC_FILES.get(path)
            if filename is not None:
                self._send_static(filename)
                return
            self._send_not_found()

    return DashboardRequestHandler


def create_server(host: str, port: int, state_root: Path) -> ThreadingHTTPServer:
    """Build a validated, loopback-only HTTP server for the dashboard."""
    require_loopback_host(host)
    handler = make_handler(state_root)
    server = ThreadingHTTPServer((host, port), handler)
    return server


def serve(host: str, port: int, state_root: Path) -> None:
    server = create_server(host, port, state_root)
    print(json.dumps({"host": host, "port": server.server_port, "stateRoot": str(state_root)}))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve_parser = subparsers.add_parser("serve", help="serve the read-only kanban dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="must be 127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=4600, help="TCP port, 0 for an ephemeral port")
    serve_parser.add_argument("--state-root", help="override ~/.gantry/state")
    args = parser.parse_args(argv)

    if args.command == "serve":
        state_root = Path(args.state_root).expanduser().resolve() if args.state_root else default_state_root(None)
        try:
            serve(args.host, args.port, state_root)
        except DashboardError as error:
            print(f"dashboard error: {error}", file=sys.stderr)
            return 1
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
