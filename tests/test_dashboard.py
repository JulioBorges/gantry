#!/usr/bin/env python3
"""Behavioral tests for the read-only, loopback-only multi-Run dashboard."""
from __future__ import annotations

import ast
import datetime
import io
import json
import socket
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

    def test_compaction_signal_and_operator_waiting_reach_reduced_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log_c = root / "unit-cccccccccccc" / "runs" / "run-c.jsonl"
            write_event(log_c, started_event("run-c", 900, iso(50), "/repo/C"))
            write_event(log_c, {
                "ts": iso(40), "run": "run-c", "event": "phase.started",
                "issue": "sample#05", "phase": "Review",
                "data": {"worktree": "/wt/c1", "branch": "gantry/sample-05", "operatorWaiting": True},
            })
            write_event(log_c, {
                "ts": iso(20), "run": "run-c", "event": "compaction", "data": {"source": "auto"},
            })

            runs = dashboard.collect_runs(root)
            by_unit = {run["unitId"]: run for run in runs}
            run_c = by_unit["unit-cccccccccccc"]

            self.assertIsNotNone(run_c["compactionAt"])
            issue_c = run_c["issues"][0]
            self.assertTrue(issue_c["operatorWaiting"])

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

    def test_collect_projects_and_issue_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log_a = root / "unit-alpha" / "runs" / "run-a.jsonl"
            write_event(log_a, started_event("run-a", 900, iso(50), "/repo/AlphaProject"))
            write_event(log_a, {
                "ts": iso(40), "run": "run-a", "event": "phase.started",
                "issue": "alpha#01", "phase": "Implement", "data": {},
            })

            log_b = root / "unit-beta" / "runs" / "run-b.jsonl"
            write_event(log_b, started_event("run-b", 900, iso(50), "/repo/BetaProject"))
            write_event(log_b, {
                "ts": iso(30), "run": "run-b", "event": "phase.started",
                "issue": "beta#01", "phase": "Review", "data": {},
            })

            (root / "unit-gamma").mkdir(parents=True, exist_ok=True)

            runs = dashboard.collect_runs(root)
            projects = dashboard.collect_projects(root, runs)

            by_unit_runs = {run["unitId"]: run for run in runs}
            issue_a = by_unit_runs["unit-alpha"]["issues"][0]
            self.assertEqual("AlphaProject", issue_a["project"])
            self.assertEqual("unit-alpha", issue_a["unitId"])
            self.assertEqual("run-a", issue_a["run"])

            projects_by_id = {p["unitId"]: p for p in projects}
            self.assertIn("unit-alpha", projects_by_id)
            self.assertEqual("AlphaProject", projects_by_id["unit-alpha"]["name"])
            self.assertEqual("/repo/AlphaProject", projects_by_id["unit-alpha"]["repositoryRoot"])

            self.assertIn("unit-beta", projects_by_id)
            self.assertEqual("BetaProject", projects_by_id["unit-beta"]["name"])

            self.assertIn("unit-gamma", projects_by_id)
            self.assertEqual("unit-gamma", projects_by_id["unit-gamma"]["name"])

    def test_timer_freezes_on_done_and_tracks_phase_durations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "unit-freeze000001" / "runs" / "run-freeze.jsonl"
            t_plan_start = iso(200)
            t_plan_end = iso(150)
            t_impl_start = iso(150)
            t_impl_end = iso(90)
            t_rev_start = iso(90)
            t_rev_end = iso(70)
            t_crit_start = iso(70)
            t_crit_end = iso(40)
            t_int_start = iso(40)
            t_done = iso(10)

            write_event(log, started_event("run-freeze", 900, t_plan_start, "/repo/freeze"))
            write_event(log, {"ts": t_plan_start, "run": "run-freeze", "event": "phase.started", "issue": "sample#01", "phase": "Plan", "data": {}})
            write_event(log, {"ts": t_plan_end, "run": "run-freeze", "event": "phase.finished", "issue": "sample#01", "phase": "Plan", "data": {}})
            write_event(log, {"ts": t_impl_start, "run": "run-freeze", "event": "phase.started", "issue": "sample#01", "phase": "Implement", "data": {}})
            write_event(log, {"ts": t_impl_end, "run": "run-freeze", "event": "phase.finished", "issue": "sample#01", "phase": "Implement", "data": {}})
            write_event(log, {"ts": t_rev_start, "run": "run-freeze", "event": "phase.started", "issue": "sample#01", "phase": "Review", "data": {}})
            write_event(log, {"ts": t_rev_end, "run": "run-freeze", "event": "phase.finished", "issue": "sample#01", "phase": "Review", "data": {}})
            write_event(log, {"ts": t_crit_start, "run": "run-freeze", "event": "phase.started", "issue": "sample#01", "phase": "Critic", "data": {}})
            write_event(log, {"ts": t_crit_end, "run": "run-freeze", "event": "phase.finished", "issue": "sample#01", "phase": "Critic", "data": {}})
            write_event(log, {"ts": t_int_start, "run": "run-freeze", "event": "phase.started", "issue": "sample#01", "phase": "Integrate", "data": {}})
            write_event(log, {"ts": t_done, "run": "run-freeze", "event": "issue.done", "issue": "sample#01", "data": {"strategy": "branch-merge"}})

            now = time.time()
            runs = dashboard.collect_runs(root, now=now)
            issue = runs[0]["issues"][0]

            self.assertEqual("Done", issue["column"])
            self.assertEqual(t_done, issue["completedAt"])
            self.assertEqual(190, issue["totalCycleSeconds"])
            self.assertEqual(50, issue["phaseDurations"]["Plan"])
            self.assertEqual(60, issue["phaseDurations"]["Implement"])
            self.assertEqual(20, issue["phaseDurations"]["Review"])
            self.assertEqual(30, issue["phaseDurations"]["Critic"])
            self.assertEqual(30, issue["phaseDurations"]["Integrate"])
            self.assertEqual(30, issue["elapsedPhaseSeconds"])

            # Verify that advancing now does NOT increment totalCycleSeconds or elapsedPhaseSeconds
            future_runs = dashboard.collect_runs(root, now=now + 86400)
            future_issue = future_runs[0]["issues"][0]
            self.assertEqual(190, future_issue["totalCycleSeconds"])
            self.assertEqual(30, future_issue["elapsedPhaseSeconds"])
            self.assertEqual(t_done, future_issue["completedAt"])

    def test_in_progress_issue_increments_timer_with_now(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "unit-prog00000001" / "runs" / "run-prog.jsonl"
            t_start = iso(100)
            write_event(log, started_event("run-prog", 900, t_start, "/repo/prog"))
            write_event(log, {"ts": t_start, "run": "run-prog", "event": "phase.started", "issue": "sample#02", "phase": "Implement", "data": {}})

            base_now = time.time()
            runs_1 = dashboard.collect_runs(root, now=base_now)
            issue_1 = runs_1[0]["issues"][0]
            self.assertIsNone(issue_1["completedAt"])
            self.assertGreaterEqual(issue_1["totalCycleSeconds"], 99)
            self.assertGreaterEqual(issue_1["phaseDurations"]["Implement"], 99)

            runs_2 = dashboard.collect_runs(root, now=base_now + 50)
            issue_2 = runs_2[0]["issues"][0]
            self.assertEqual(issue_1["totalCycleSeconds"] + 50, issue_2["totalCycleSeconds"])
            self.assertEqual(issue_1["phaseDurations"]["Implement"] + 50, issue_2["phaseDurations"]["Implement"])

    def test_planning_milestone_telemetry_in_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "unit-plan0000001" / "runs" / "run-plan.jsonl"
            t_plan_start = iso(100)
            t_approved = iso(60)
            t_done = iso(20)

            write_event(log, started_event("run-plan", 900, t_plan_start, "/repo/plan"))
            write_event(log, {
                "ts": t_plan_start,
                "run": "run-plan",
                "event": "phase.started",
                "issue": "my-feature#00",
                "phase": "Plan",
                "data": {"operatorWaiting": True},
            })

            # Check dashboard placing my-feature#00 in Plan with Awaiting Operator
            runs = dashboard.collect_runs(root, now=time.time())
            issue = runs[0]["issues"][0]
            self.assertEqual("Plan", issue["column"])
            self.assertTrue(issue["operatorWaiting"])
            self.assertEqual("Awaiting Operator", issue["liveActivity"])

            # Log operator.approved
            write_event(log, {
                "ts": t_approved,
                "run": "run-plan",
                "event": "operator.approved",
                "issue": "my-feature#00",
                "data": {"source": "interview"},
            })
            runs2 = dashboard.collect_runs(root, now=time.time())
            issue2 = runs2[0]["issues"][0]
            self.assertFalse(issue2["operatorWaiting"])
            self.assertNotEqual("Awaiting Operator", issue2.get("liveActivity"))

            # Log issue.done
            write_event(log, {
                "ts": t_done,
                "run": "run-plan",
                "event": "issue.done",
                "issue": "my-feature#00",
                "data": {"strategy": "branch-merge"},
            })
            runs3 = dashboard.collect_runs(root, now=time.time())
            issue3 = runs3[0]["issues"][0]
            self.assertEqual("Done", issue3["column"])
            self.assertFalse(issue3["operatorWaiting"])
            self.assertEqual(t_done, issue3["completedAt"])
            self.assertEqual(80, issue3["totalCycleSeconds"])


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

    def post(self, path: str, data: bytes = b"{}") -> tuple[int, bytes]:
        try:
            request = urllib.request.Request(
                f"{self.base_url}{path}",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
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

    def test_api_state_exposes_projects_metadata_and_columns(self) -> None:
        log_path = self.state_root / "unit-proj0001" / "runs" / "run-p1.jsonl"
        write_event(log_path, started_event("run-p1", 900, iso(10), "/repo/MyProject"))
        write_event(log_path, {
            "ts": iso(5), "run": "run-p1", "event": "phase.started",
            "issue": "proj#01", "phase": "Ready", "data": {},
        })

        status, body = self.get("/api/state")
        self.assertEqual(200, status)
        payload = json.loads(body)
        self.assertIn("columns", payload)
        self.assertIn("runs", payload)
        self.assertIn("projects", payload)
        self.assertEqual(1, len(payload["projects"]))
        self.assertEqual("MyProject", payload["projects"][0]["name"])
        self.assertEqual("unit-proj0001", payload["projects"][0]["unitId"])
        self.assertEqual("MyProject", payload["runs"][0]["issues"][0]["project"])

    def test_transcript_endpoint_and_live_activity_from_harness(self) -> None:
        unit = "unit-trans0001"
        run = "run-trans"
        issue = "issue#02"
        log_path = self.state_root / unit / "runs" / f"{run}.jsonl"
        write_event(log_path, started_event(run, 900, iso(20), "/repo/trans"))

        # Setup transcript file in ~/.gantry/state/<unit>/transcripts/<run>/<issue>/transcript.jsonl
        transcript_dir = self.state_root / unit / "transcripts" / run / issue
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_file = transcript_dir / "transcript.jsonl"
        with transcript_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"step_index": 0, "type": "USER_INPUT", "content": "Start work"}) + "\n")
            f.write(json.dumps({"step_index": 1, "type": "PLANNER_RESPONSE", "thinking": "Analyzing requirements carefully...", "tool_calls": [{"name": "run_command", "args": {"CommandLine": "git status"}}]}) + "\n")
            f.write(json.dumps({"step_index": 2, "type": "GENERIC", "content": "git diff content\n+added line\n-removed line"}) + "\n")

        # Query state to check live activity derived from latest step
        write_event(log_path, {
            "ts": iso(10), "run": run, "event": "phase.started",
            "issue": issue, "phase": "Implement", "data": {},
        })

        quoted_issue = urllib.parse.quote(issue, safe="")
        status, body = self.get(f"/api/runs/{unit}/{run}/issues/{quoted_issue}/transcript")
        self.assertEqual(200, status)
        data = json.loads(body)
        self.assertIn("steps", data)
        self.assertEqual(3, len(data["steps"]))
        self.assertEqual("Analyzing requirements carefully...", data["steps"][1]["thinking"])
        self.assertEqual("run_command", data["steps"][1]["tool_calls"][0]["name"])

        # Check /api/state reflects live activity badge
        status, body = self.get("/api/state")
        self.assertEqual(200, status)
        state_data = json.loads(body)
        matched_issue = state_data["runs"][0]["issues"][0]
        self.assertEqual("Tool: run_command", matched_issue.get("liveActivity"))

    def test_transcript_endpoint_returns_empty_when_missing(self) -> None:
        quoted_issue = urllib.parse.quote("none#01", safe="")
        status, body = self.get(f"/api/runs/unit-none/run-none/issues/{quoted_issue}/transcript")
        self.assertEqual(200, status)
        data = json.loads(body)
        self.assertEqual({"steps": []}, data)

    def test_post_approve_creates_marker_and_appends_runlog(self) -> None:
        unit = "111122223333"
        run = "run-appr-01"
        issue = "sample#01"
        log_path = self.state_root / unit / "runs" / f"{run}.jsonl"
        write_event(log_path, started_event(run, 900, iso(30), "/repo/appr"))
        write_event(log_path, {
            "ts": iso(20), "run": run, "event": "phase.started",
            "issue": issue, "phase": "Critic", "data": {"operatorWaiting": True},
        })

        status, body = self.post(f"/api/runs/{unit}/{run}/issues/{urllib.parse.quote(issue, safe='')}/approve")
        self.assertEqual(200, status)
        data = json.loads(body)
        self.assertEqual("ok", data.get("status"))
        self.assertTrue(data.get("approved"))

        # Verify marker file
        marker_file = self.state_root / unit / "approvals" / f"{issue}.json"
        self.assertTrue(marker_file.exists())
        marker_data = json.loads(marker_file.read_text(encoding="utf-8"))
        self.assertEqual(issue, marker_data.get("issue"))
        self.assertEqual("dashboard", marker_data.get("source"))

        # Verify operator.approved event in run log
        lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        events = [line["event"] for line in lines]
        self.assertIn("operator.approved", events)

        # Verify state endpoint reflects approval
        status, body = self.get("/api/state")
        self.assertEqual(200, status)
        state_data = json.loads(body)
        matched_issue = state_data["runs"][0]["issues"][0]
        self.assertFalse(matched_issue.get("operatorWaiting", False))
        self.assertTrue(matched_issue.get("operatorApproved", False))

    def test_post_approve_rejects_invalid_identifiers(self) -> None:
        # Invalid unit
        status, _ = self.post(f"/api/runs/bad-unit/run-01/issues/{urllib.parse.quote('sample#01', safe='')}/approve")
        self.assertEqual(400, status)

        # Invalid issue
        status, _ = self.post(f"/api/runs/111122223333/run-01/issues/{urllib.parse.quote('bad-issue', safe='')}/approve")
        self.assertEqual(400, status)

    def test_gates_endpoint_returns_structured_verdicts(self) -> None:
        unit = "unit-gate000001"
        run = "run-gate-01"
        issue = "sample#02"
        log_path = self.state_root / unit / "runs" / f"{run}.jsonl"
        write_event(log_path, started_event(run, 900, iso(50), "/repo/gate"))

        # Persist structured artifacts under ~/.gantry/state/<unit>/artifacts/<run>/<issue>/gate-<phase>.json
        artifacts_dir = self.state_root / unit / "artifacts" / run / issue
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "gate-plan.json").write_text(json.dumps({
            "verdict": "accepted",
            "criteria": ["Criterion 1", "Criterion 2"],
            "scope": ["Slice 1"],
        }), encoding="utf-8")
        (artifacts_dir / "gate-critic.json").write_text(json.dumps({
            "complete": True,
            "verdict": "complete",
            "criteria": ["Criterion 1", "Criterion 2"],
            "evidence": ["Tests green", "Build clean"],
        }), encoding="utf-8")

        quoted_issue = urllib.parse.quote(issue, safe="")
        status, body = self.get(f"/api/runs/{unit}/{run}/issues/{quoted_issue}/gates")
        self.assertEqual(200, status)
        data = json.loads(body)
        self.assertIn("gates", data)
        self.assertIn("plan", data["gates"])
        self.assertEqual("accepted", data["gates"]["plan"]["verdict"])
        self.assertIn("critic", data["gates"])
        self.assertTrue(data["gates"]["critic"]["complete"])

    def test_gates_endpoint_returns_integrate_strategy_from_done_event(self) -> None:
        unit = "unit-gate-int01"
        run = "run-gate-int01"
        issue = "sample#09"
        log_path = self.state_root / unit / "runs" / f"{run}.jsonl"
        write_event(log_path, started_event(run, 900, iso(50), "/repo/gate-int"))
        write_event(log_path, {
            "ts": iso(10), "run": run, "event": "issue.done", "issue": issue,
            "data": {"worktree": "/wt/int", "strategy": "pull-request"},
        })

        quoted_issue = urllib.parse.quote(issue, safe="")
        status, body = self.get(f"/api/runs/{unit}/{run}/issues/{quoted_issue}/gates")
        self.assertEqual(200, status)
        data = json.loads(body)
        self.assertIn("integrate", data["gates"])
        self.assertEqual("merged", data["gates"]["integrate"]["verdict"])
        self.assertEqual("pull-request", data["gates"]["integrate"]["strategy"])

    def test_history_html_served(self) -> None:
        status, body = self.get("/history.html")
        self.assertEqual(200, status)
        self.assertIn("GANTRY", body.decode("utf-8"))
        self.assertIn("HISTORY", body.decode("utf-8"))

        status, body = self.get("/history")
        self.assertEqual(200, status)

    def test_post_shutdown_triggers_graceful_shutdown(self) -> None:
        status, body = self.post("/api/shutdown")
        self.assertEqual(200, status)
        data = json.loads(body)
        self.assertEqual("shutting_down", data.get("status"))
        self.thread.join(timeout=3)
        self.assertFalse(self.thread.is_alive())

    def test_post_shutdown_rejects_non_loopback(self) -> None:
        handler_class = dashboard.make_handler(self.state_root)
        dummy = handler_class.__new__(handler_class)
        dummy.client_address = ("192.168.1.100", 54321)
        dummy.send_response = lambda code: setattr(dummy, "status_sent", code)
        dummy.send_header = lambda *a: None
        dummy.end_headers = lambda: None
        dummy.wfile = io.BytesIO()
        self.assertFalse(dummy._check_loopback())
        self.assertEqual(403, getattr(dummy, "status_sent", None))


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
                "__future__", "argparse", "datetime", "http", "json", "os", "pathlib",
                "re", "runlog", "socket", "subprocess", "sys", "threading", "time", "urllib",
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
                "__future__", "ast", "dashboard", "datetime", "io", "json", "socket", "subprocess",
                "sys", "tempfile", "threading", "time", "unittest", "urllib", "pathlib",
            },
        )

    def test_status_reports_not_running_when_inactive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_cli("status", "--port", "4820", "--state-root", str(temp), "--json")
            self.assertEqual(0, result.returncode)
            data = json.loads(result.stdout)
            self.assertFalse(data["running"])
            self.assertIsNone(data["pid"])
            self.assertEqual(4820, data["port"])

    def test_status_cleans_up_stale_pid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_file = root / "dashboard.json"
            state_file.write_text(json.dumps({
                "running": True,
                "host": "127.0.0.1",
                "port": 4821,
                "pid": 99999999,
                "stateRoot": str(root),
            }))
            self.assertTrue(state_file.exists())
            result = self.run_cli("status", "--port", "4821", "--state-root", str(temp), "--json")
            self.assertEqual(0, result.returncode)
            data = json.loads(result.stdout)
            self.assertFalse(data["running"])
            self.assertFalse(state_file.exists())

    def test_start_daemon_fails_when_port_occupied_by_alien_process(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        alien_port = sock.getsockname()[1]
        try:
            with tempfile.TemporaryDirectory() as temp:
                result = self.run_cli("start", "--daemon", "--port", str(alien_port), "--state-root", str(temp))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("alien process", result.stderr)
        finally:
            sock.close()

    def test_daemon_start_status_and_stop_lifecycle(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        free_port = sock.getsockname()[1]
        sock.close()

        with tempfile.TemporaryDirectory() as temp:
            # 1. Start daemon
            start_res = self.run_cli("start", "--daemon", "--port", str(free_port), "--state-root", str(temp), "--json")
            self.assertEqual(0, start_res.returncode, start_res.stderr)
            start_data = json.loads(start_res.stdout)
            self.assertTrue(start_data["running"])
            pid = start_data["pid"]
            self.assertIsInstance(pid, int)

            # 2. Check status
            status_res = self.run_cli("status", "--port", str(free_port), "--state-root", str(temp), "--json")
            self.assertEqual(0, status_res.returncode)
            status_data = json.loads(status_res.stdout)
            self.assertTrue(status_data["running"])
            self.assertEqual(pid, status_data["pid"])

            # 3. Stop daemon
            stop_res = self.run_cli("stop", "--port", str(free_port), "--state-root", str(temp), "--json")
            self.assertEqual(0, stop_res.returncode)
            stop_data = json.loads(stop_res.stdout)
            self.assertTrue(stop_data["stopped"])

            # 4. Check status after stop
            status_after = self.run_cli("status", "--port", str(free_port), "--state-root", str(temp), "--json")
            self.assertEqual(0, status_after.returncode)
            self.assertFalse(json.loads(status_after.stdout)["running"])

    def test_wait_gate_script(self) -> None:
        wait_gate_script = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "wait_gate.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unit = "112233445566"
            run = "run-wait-01"
            issue = "sample#01"

            # Check without marker exits 1
            res_check_fail = subprocess.run(
                [sys.executable, str(wait_gate_script), "--issue", issue, "--unit", unit, "--run", run, "--state-root", str(root), "--check"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(1, res_check_fail.returncode)

            # Approve via CLI
            res_approve = subprocess.run(
                [sys.executable, str(wait_gate_script), "--issue", issue, "--unit", unit, "--run", run, "--state-root", str(root), "--approve"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, res_approve.returncode)
            self.assertIn('"approved": true', res_approve.stdout.lower())

            # Check with marker exits 0
            res_check_ok = subprocess.run(
                [sys.executable, str(wait_gate_script), "--issue", issue, "--unit", unit, "--run", run, "--state-root", str(root), "--check"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, res_check_ok.returncode)


if __name__ == "__main__":
    unittest.main()
