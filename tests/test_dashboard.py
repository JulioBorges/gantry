#!/usr/bin/env python3
"""Behavioral tests for the read-only, loopback-only multi-Run dashboard."""
from __future__ import annotations

import ast
import datetime
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_SCRIPT = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "dashboard.py"
STATIC_DIR = REPO_ROOT / ".agents" / "skills" / "gantry" / "dashboard" / "static"

sys.path.insert(0, str(DASHBOARD_SCRIPT.parent))
import dashboard  # noqa: E402


def iso(seconds_ago: float) -> str:
    when = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds_ago)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_event(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def started_event(run: str, stale_after: int, ts: str, repository_root: str = "/repo/A") -> dict:
    return {
        "ts": ts,
        "run": run,
        "event": "run.started",
        "data": {
            "repositoryRoot": repository_root,
            "policyHash": "hash-1",
            "tier": "supported",
            "staleAfterSeconds": stale_after,
        },
    }


class DashboardHelperTests(unittest.TestCase):
    def test_require_loopback_host_accepts_only_127_0_0_1(self) -> None:
        self.assertEqual("127.0.0.1", dashboard.require_loopback_host("127.0.0.1"))
        for host in ("0.0.0.0", "localhost", "::1", "192.168.1.5"):
            with self.assertRaises(dashboard.DashboardError):
                dashboard.require_loopback_host(host)

    def test_collect_runs_places_issues_in_correct_phase_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log_a = root / "unit-aaaaaaaaaaaa" / "runs" / "run-a.jsonl"
            write_event(log_a, started_event("run-a", 900, iso(50), "/repo/A"))
            write_event(log_a, {
                "ts": iso(40), "run": "run-a", "event": "phase.started",
                "issue": "sample#01", "phase": "Plan",
                "data": {"worktree": "/wt/a1", "branch": "gantry/sample-01", "models": {"planner": "model-x"}},
            })

            log_b = root / "unit-bbbbbbbbbbbb" / "runs" / "run-b.jsonl"
            write_event(log_b, started_event("run-b", 900, iso(50), "/repo/B"))
            write_event(log_b, {
                "ts": iso(30), "run": "run-b", "event": "phase.started",
                "issue": "sample#02", "phase": "Critic",
                "data": {"worktree": "/wt/b2", "branch": "gantry/sample-02",
                         "correctionBudget": {"used": 1, "ceiling": 2}},
            })
            write_event(log_b, {
                "ts": iso(10), "run": "run-b", "event": "issue.done", "issue": "sample#03",
            })
            write_event(log_b, {
                "ts": iso(5), "run": "run-b", "event": "issue.blocked", "issue": "sample#04",
            })

            runs = dashboard.collect_runs(root)
            by_unit = {run["unitId"]: run for run in runs}

            issue_a = by_unit["unit-aaaaaaaaaaaa"]["issues"][0]
            self.assertEqual("Plan", issue_a["column"])
            self.assertEqual("/repo/A", by_unit["unit-aaaaaaaaaaaa"]["repositoryRoot"])
            self.assertEqual("/wt/a1", issue_a["worktree"])
            self.assertEqual("gantry/sample-01", issue_a["branch"])
            self.assertEqual({"planner": "model-x"}, issue_a["models"])
            self.assertIsInstance(issue_a["elapsedPhaseSeconds"], int)
            self.assertGreaterEqual(issue_a["elapsedPhaseSeconds"], 39)

            issues_b = {item["issue"]: item for item in by_unit["unit-bbbbbbbbbbbb"]["issues"]}
            self.assertEqual("Critic", issues_b["sample#02"]["column"])
            self.assertEqual({"used": 1, "ceiling": 2}, issues_b["sample#02"]["correctionBudget"])
            self.assertEqual("Done", issues_b["sample#03"]["column"])
            self.assertEqual("Blocked", issues_b["sample#04"]["column"])

    def test_staleness_uses_run_started_snapshot_and_ignores_policy_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stale_log = root / "unit-stale000001" / "runs" / "run-stale.jsonl"
            write_event(stale_log, started_event("run-stale", 60, iso(120), "/repo/stale"))
            write_event(stale_log, {
                "ts": iso(120), "run": "run-stale", "event": "phase.started",
                "issue": "sample#01", "phase": "Critic", "data": {},
            })

            fresh_log = root / "unit-fresh000001" / "runs" / "run-fresh.jsonl"
            write_event(fresh_log, started_event("run-fresh", 900, iso(120), "/repo/fresh"))
            write_event(fresh_log, {
                "ts": iso(120), "run": "run-fresh", "event": "phase.started",
                "issue": "sample#02", "phase": "Critic", "data": {},
            })

            runs = dashboard.collect_runs(root)
            by_unit = {run["unitId"]: run for run in runs}
            self.assertTrue(by_unit["unit-stale000001"]["stale"])
            self.assertFalse(by_unit["unit-fresh000001"]["stale"])

            # A later policy.changed event must not change either Run's stale result.
            write_event(stale_log, {
                "ts": iso(0), "run": "run-stale", "event": "policy.changed",
                "data": {"policyHash": "hash-2"},
            })
            write_event(fresh_log, {
                "ts": iso(0), "run": "run-fresh", "event": "policy.changed",
                "data": {"policyHash": "hash-2"},
            })

            runs = dashboard.collect_runs(root)
            by_unit = {run["unitId"]: run for run in runs}
            self.assertTrue(by_unit["unit-stale000001"]["stale"])
            self.assertFalse(by_unit["unit-fresh000001"]["stale"])


class DashboardHttpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state_root = Path(self.temp.name)
        self.server = dashboard.create_server("127.0.0.1", 0, self.state_root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def get(self, path: str) -> tuple[int, bytes]:
        try:
            with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def test_binds_loopback_only(self) -> None:
        self.assertEqual("127.0.0.1", self.server.server_address[0])
        with self.assertRaises(dashboard.DashboardError):
            dashboard.create_server("0.0.0.0", 0, self.state_root)

    def test_serves_only_pack_owned_zero_external_asset_files(self) -> None:
        status, body = self.get("/")
        self.assertEqual(200, status)
        text = body.decode("utf-8")
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)

        status, _ = self.get("/app.js")
        self.assertEqual(200, status)
        status, _ = self.get("/style.css")
        self.assertEqual(200, status)

        status, _ = self.get("/../../etc/passwd")
        self.assertEqual(404, status)
        status, _ = self.get("/nonexistent.txt")
        self.assertEqual(404, status)

    def test_no_endpoint_mutates_state(self) -> None:
        log_path = self.state_root / "unit-readonly0001" / "runs" / "run-ro.jsonl"
        write_event(log_path, started_event("run-ro", 900, iso(10), "/repo/ro"))
        before = log_path.read_text(encoding="utf-8")

        request = urllib.request.Request(f"{self.base_url}/api/state", method="POST", data=b"{}")
        try:
            urllib.request.urlopen(request, timeout=5)
            self.fail("POST to /api/state should be refused")
        except urllib.error.HTTPError as error:
            self.assertIn(error.code, (405, 501))

        after = log_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_reflects_an_appended_run_log_event_within_two_seconds(self) -> None:
        log_path = self.state_root / "unit-live00000001" / "runs" / "run-live.jsonl"
        write_event(log_path, started_event("run-live", 900, iso(5), "/repo/live"))

        status, body = self.get("/api/state")
        self.assertEqual(200, status)
        payload = json.loads(body)
        self.assertEqual([], payload["runs"][0]["issues"])

        write_event(log_path, {
            "ts": iso(0), "run": "run-live", "event": "phase.started",
            "issue": "sample#09", "phase": "Implement", "data": {},
        })

        deadline = time.time() + 2
        seen = False
        while time.time() < deadline:
            status, body = self.get("/api/state")
            payload = json.loads(body)
            if payload["runs"][0]["issues"]:
                seen = True
                break
            time.sleep(0.1)
        self.assertTrue(seen, "the dashboard did not reflect the appended event within two seconds")


class DashboardCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(DASHBOARD_SCRIPT), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    def test_help(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("usage:", result.stdout.lower())

    def test_cli_rejects_a_non_loopback_bind_request(self) -> None:
        result = self.run_cli("serve", "--host", "0.0.0.0", "--port", "0")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("127.0.0.1", result.stderr)

    def test_help_and_implementation_use_standard_library_only(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(0, result.returncode, result.stderr)

        tree = ast.parse(DASHBOARD_SCRIPT.read_text(encoding="utf-8"), filename=str(DASHBOARD_SCRIPT))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports |= {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertLessEqual(
            imports,
            {
                "__future__", "argparse", "datetime", "http", "json", "pathlib",
                "runlog", "sys", "threading", "time", "urllib",
            },
        )

    def test_dashboard_test_module_itself_uses_standard_library_only(self) -> None:
        this_file = Path(__file__).resolve()
        tree = ast.parse(this_file.read_text(encoding="utf-8"), filename=str(this_file))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports |= {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertLessEqual(
            imports,
            {
                "__future__", "ast", "dashboard", "datetime", "json", "subprocess",
                "sys", "tempfile", "threading", "time", "unittest", "urllib", "pathlib",
            },
        )


if __name__ == "__main__":
    unittest.main()
