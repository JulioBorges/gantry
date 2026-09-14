#!/usr/bin/env python3
"""End-to-end contracts for the append-only Gantry Run log."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNLOG = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "runlog.py"


class RunLogTests(unittest.TestCase):
    def run_script(
        self,
        root: Path,
        *args: str,
        event: dict[str, object] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RUNLOG), *args],
            cwd=root,
            input=json.dumps(event) if event is not None else None,
            text=True,
            capture_output=True,
            check=False,
        )

    def init_repository(self, root: Path) -> None:
        subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "runlog@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Run Log Test"], cwd=root, check=True)
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)

    def started(self, run: str = "run-01") -> dict[str, object]:
        return {
            "ts": "2026-09-13T12:00:00Z",
            "run": run,
            "event": "run.started",
            "data": {
                "repositoryRoot": "/repository",
                "policyHash": "abc123",
                "tier": "supported",
                "staleAfterSeconds": 60,
            },
        }

    def test_append_persists_a_valid_start_event_unchanged_and_rejects_invalid_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            started = self.started()

            accepted = self.run_script(root, "append", unit, "--state-root", str(state), event=started)
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            path = state / unit / "runs" / "run-01.jsonl"
            self.assertEqual([started], [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()])

            malformed = self.run_script(root, "append", unit, "--state-root", str(state), event={"event": "run.started"})
            unknown = self.run_script(
                root,
                "append",
                unit,
                "--state-root",
                str(state),
                event={**self.started("run-02"), "event": "not.a.lifecycle.event"},
            )
            self.assertEqual(1, malformed.returncode)
            self.assertEqual(1, unknown.returncode)

    def test_worktrees_share_unit_and_inflight_reports_only_unfinished_issue_phase_and_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "clone"
            root.mkdir()
            self.init_repository(root)
            linked = Path(temp) / "linked"
            subprocess.run(["git", "worktree", "add", "--quiet", str(linked)], cwd=root, check=True)
            try:
                root_unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
                linked_unit = json.loads(self.run_script(linked, "unit-id", "--cwd", str(linked), "--json").stdout)["unitId"]
                self.assertEqual(root_unit, linked_unit)
                state = Path(temp) / "state"
                for event in (
                    self.started("interrupted"),
                    {
                        "ts": "2026-09-13T12:01:00Z",
                        "run": "interrupted",
                        "event": "phase.started",
                        "issue": "sample#02",
                        "phase": "Implement",
                        "data": {"worktree": str(linked)},
                    },
                    self.started("finished"),
                    {"ts": "2026-09-13T12:02:00Z", "run": "finished", "event": "run.finished", "data": {}},
                ):
                    appended = self.run_script(root, "append", root_unit, "--state-root", str(state), event=event)
                    self.assertEqual(0, appended.returncode, appended.stderr)

                result = self.run_script(root, "inflight", root_unit, "--state-root", str(state), "--json")

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(1, len(json.loads(result.stdout)["inflight"]))
                current = json.loads(result.stdout)["inflight"][0]
                self.assertEqual("interrupted", current["run"])
                self.assertEqual("sample#02", current["issue"])
                self.assertEqual("Implement", current["phase"])
                self.assertEqual(str(linked), current["worktree"])
            finally:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(linked)],
                    cwd=root,
                    capture_output=True,
                    check=False,
                )

    def test_inflight_preserves_each_issue_when_one_concurrent_phase_finishes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]

            for event in (
                self.started("parallel"),
                {
                    "ts": "2026-09-13T12:01:00Z",
                    "run": "parallel",
                    "event": "phase.started",
                    "issue": "sample#01",
                    "phase": "Implement",
                    "data": {"worktree": "/worktrees/sample-01"},
                },
                {
                    "ts": "2026-09-13T12:01:01Z",
                    "run": "parallel",
                    "event": "phase.started",
                    "issue": "sample#02",
                    "phase": "Implement",
                    "data": {"worktree": "/worktrees/sample-02"},
                },
                {
                    "ts": "2026-09-13T12:02:00Z",
                    "run": "parallel",
                    "event": "phase.finished",
                    "issue": "sample#02",
                    "phase": "Implement",
                    "data": {},
                },
            ):
                appended = self.run_script(root, "append", unit, "--state-root", str(state), event=event)
                self.assertEqual(0, appended.returncode, appended.stderr)

            result = self.run_script(root, "inflight", unit, "--state-root", str(state), "--json")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                [
                    {
                        "run": "parallel",
                        "issue": "sample#01",
                        "phase": "Implement",
                        "worktree": "/worktrees/sample-01",
                        "repositoryRoot": "/repository",
                        "policyHash": "abc123",
                        "tier": "supported",
                        "staleAfterSeconds": 60,
                    }
                ],
                json.loads(result.stdout)["inflight"],
            )

    def test_concurrent_single_write_append_keeps_jsonl_parseable_and_protects_prohibited_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            first = self.run_script(root, "append", unit, "--state-root", str(state), event=self.started("concurrent"))
            self.assertEqual(0, first.returncode, first.stderr)
            events = [
                {
                    "ts": f"2026-09-13T12:00:{index:02d}Z",
                    "run": "concurrent",
                    "event": "round.started",
                    "data": {"round": index},
                }
                for index in range(1, 17)
            ]
            processes = [
                subprocess.Popen(
                    [sys.executable, str(RUNLOG), "append", unit, "--state-root", str(state)],
                    cwd=root,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in events
            ]
            for process, event in zip(processes, events):
                stdout, stderr = process.communicate(json.dumps(event))
                self.assertEqual(0, process.returncode, stdout + stderr)
            path = state / unit / "runs" / "concurrent.jsonl"
            self.assertEqual(17, len(path.read_text(encoding="utf-8").splitlines()))
            for line in path.read_text(encoding="utf-8").splitlines():
                self.assertIsInstance(json.loads(line), dict)

            prohibited = self.run_script(
                root,
                "append",
                unit,
                "--state-root",
                str(state),
                event={**self.started("prohibited"), "data": {**self.started("prohibited")["data"], "diff": "secret patch"}},
            )
            secret_output = self.run_script(
                root,
                "append",
                unit,
                "--state-root",
                str(state),
                event={
                    **self.started("secret-output"),
                    "data": {
                        **self.started("secret-output")["data"],
                        "check": {"secrets": True, "exitCode": 1, "counts": {"failed": 1}, "output": "do not persist"},
                    },
                },
            )
            self.assertEqual(1, prohibited.returncode)
            self.assertEqual(1, secret_output.returncode)

    def test_secrets_check_persists_only_exit_code_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            rejected = self.run_script(
                root,
                "append",
                unit,
                "--state-root",
                str(state),
                event={
                    **self.started("secret-name"),
                    "data": {
                        **self.started("secret-name")["data"],
                        "check": {"secrets": True, "name": "secret-scan", "exitCode": 0, "counts": {"passed": 1}},
                    },
                },
            )

            self.assertEqual(1, rejected.returncode)
            self.assertIn("only exitCode and counts", rejected.stderr)
            self.assertFalse((state / unit / "runs" / "secret-name.jsonl").exists())

    def test_rejects_sensitive_key_variants_without_rejecting_permitted_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            permitted = self.run_script(
                root,
                "append",
                unit,
                "--state-root",
                str(state),
                event={
                    **self.started("permitted"),
                    "data": {
                        **self.started("permitted")["data"],
                        "dispatch": "lifecycle event",
                        "check": {"name": "test", "exitCode": 0, "counts": {"passed": 1}},
                    },
                },
            )
            self.assertEqual(0, permitted.returncode, permitted.stderr)

            for index, key in enumerate(
                ("unifiedDiff", "checkOutput", "commandLine", "commands", "patchText", "stderrOutput"),
                start=1,
            ):
                with self.subTest(key=key):
                    rejected = self.run_script(
                        root,
                        "append",
                        unit,
                        "--state-root",
                        str(state),
                        event={
                            **self.started(f"sensitive-{index}"),
                            "data": {
                                **self.started(f"sensitive-{index}")["data"],
                                "nested": {key: "must not persist"},
                            },
                        },
                    )
                    self.assertEqual(1, rejected.returncode)
                    self.assertIn(key, rejected.stderr)
                    self.assertFalse((state / unit / "runs" / f"sensitive-{index}.jsonl").exists())

    def test_sub_64_kb_append_uses_exactly_one_write_system_call(self) -> None:
        specification = importlib.util.spec_from_file_location("gantry_runlog", RUNLOG)
        self.assertIsNotNone(specification)
        module = importlib.util.module_from_spec(specification)
        self.assertIsNotNone(specification.loader)
        specification.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "run.jsonl"
            real_write = module.os.write
            with mock.patch.object(module.os, "write", wraps=real_write) as write:
                module.append_event(path, {"event": "run.started", "payload": "x" * 64_000})
            self.assertEqual(1, write.call_count)
            self.assertLessEqual(path.stat().st_size, 64 * 1024)

    def test_policy_changes_do_not_mutate_run_snapshots_and_help_and_json_queries_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            for event in (
                self.started("snapshot"),
                {
                    "ts": "2026-09-13T12:00:30Z",
                    "run": "snapshot",
                    "event": "phase.started",
                    "issue": "sample#01",
                    "phase": "Review",
                    "data": {"worktree": str(root)},
                },
                {
                    "ts": "2026-09-13T12:01:00Z",
                    "run": "snapshot",
                    "event": "policy.changed",
                    "data": {"policyHash": "def456"},
                },
            ):
                appended = self.run_script(root, "append", unit, "--state-root", str(state), event=event)
                self.assertEqual(0, appended.returncode, appended.stderr)

            path = state / unit / "runs" / "snapshot.jsonl"
            path.write_text(
                path.read_text(encoding="utf-8")
                + json.dumps({
                    "ts": "2026-09-13T12:01:30Z",
                    "run": "other-run",
                    "event": "phase.started",
                    "issue": "sample#99",
                    "phase": "Critic",
                    "data": {"worktree": str(root)},
                })
                + "\n",
                encoding="utf-8",
            )
            result = self.run_script(root, "inflight", unit, "--state-root", str(state), "--json")
            self.assertEqual(0, result.returncode, result.stderr)
            run = json.loads(result.stdout)["inflight"][0]
            self.assertEqual("snapshot", run["run"])
            self.assertEqual(60, run["staleAfterSeconds"])
            self.assertEqual("abc123", run["policyHash"])
            help_result = self.run_script(root, "--help")
            self.assertEqual(0, help_result.returncode, help_result.stderr)
            self.assertIn("usage:", help_result.stdout.lower())

    def test_hook_degraded_requires_source_missing_list_and_degraded_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            started = self.started()
            self.assertEqual(0, self.run_script(root, "append", unit, "--state-root", str(state), event=started).returncode)

            degraded = {
                "ts": "2026-09-13T12:00:30Z",
                "run": "run-01",
                "event": "hook.degraded",
                "data": {"source": "PreToolUse", "missing": ["tool_input"], "degraded": True},
            }
            accepted = self.run_script(root, "append", unit, "--state-root", str(state), event=degraded)
            self.assertEqual(0, accepted.returncode, accepted.stderr)

            missing_fields = {**degraded, "data": {"source": "PreToolUse"}}
            rejected = self.run_script(root, "append", unit, "--state-root", str(state), event=missing_fields)
            self.assertEqual(1, rejected.returncode)

            not_degraded = {**degraded, "data": {"source": "PreToolUse", "missing": ["tool_input"], "degraded": False}}
            rejected_flag = self.run_script(root, "append", unit, "--state-root", str(state), event=not_degraded)
            self.assertEqual(1, rejected_flag.returncode)

    def test_every_runlog_event_is_named_in_the_spec_blueprint_run_log_bullet(self) -> None:
        specification = importlib.util.spec_from_file_location("gantry_runlog", RUNLOG)
        self.assertIsNotNone(specification)
        module = importlib.util.module_from_spec(specification)
        self.assertIsNotNone(specification.loader)
        specification.loader.exec_module(module)

        spec_path = REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md"
        spec_text = spec_path.read_text(encoding="utf-8")
        run_log_bullet = next(
            line for line in spec_text.splitlines() if line.startswith("- **Run log:**")
        )
        for event in module.EVENTS:
            self.assertIn(
                f"`{event}`",
                run_log_bullet,
                f"runlog.EVENTS names {event!r} but the spec's Run log bullet does not list it",
            )

    def test_corrections_derives_spent_count_from_started_correction_passes_only(self) -> None:
        # A shipped query, not prose or test-local code: `runlog.py corrections` applies the
        # documented derivation rule (prior `run.resumed.data.correctionsSpent`, plus only the
        # refutations that a later `phase.started` Implement event proves actually started a
        # correction pass) directly to one Run's own event log.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            run_id = "corrections-run"
            for event in (
                self.started(run_id),
                {
                    "ts": "2026-09-13T12:00:10Z", "run": run_id, "event": "run.resumed",
                    "data": {"priorRun": "run-before", "worktree": str(root), "issue": "sample#01", "correctionsSpent": 1},
                },
                {
                    "ts": "2026-09-13T12:01:00Z", "run": run_id, "event": "phase.started",
                    "issue": "sample#01", "phase": "Implement", "data": {"worktree": str(root)},
                },
                {
                    "ts": "2026-09-13T12:02:00Z", "run": run_id, "event": "refutation",
                    "issue": "sample#01", "phase": "Critic", "data": {"attempt": 2, "refutations": ["still wrong"]},
                },
                {
                    "ts": "2026-09-13T12:03:00Z", "run": run_id, "event": "phase.started",
                    "issue": "sample#01", "phase": "Implement", "data": {"worktree": str(root)},
                },
                # A refutation for a different Issue must never count toward sample#01.
                {
                    "ts": "2026-09-13T12:04:00Z", "run": run_id, "event": "refutation",
                    "issue": "sample#99", "phase": "Critic", "data": {"attempt": 1, "refutations": ["unrelated"]},
                },
                {
                    "ts": "2026-09-13T12:05:00Z", "run": run_id, "event": "phase.started",
                    "issue": "sample#99", "phase": "Implement", "data": {"worktree": str(root)},
                },
            ):
                appended = self.run_script(root, "append", unit, "--state-root", str(state), event=event)
                self.assertEqual(0, appended.returncode, appended.stderr)

            result = self.run_script(root, "corrections", unit, run_id, "sample#01", "--state-root", str(state), "--json")
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(unit, payload["unitId"])
            self.assertEqual(run_id, payload["runId"])
            self.assertEqual("sample#01", payload["issue"])
            # 1 (resumed base) + 1 (the sample#01 refutation followed by a real correction pass) = 2.
            self.assertEqual(2, payload["correctionsSpent"])

            plain = self.run_script(root, "corrections", unit, run_id, "sample#01", "--state-root", str(state))
            self.assertEqual(0, plain.returncode, plain.stderr)
            self.assertEqual("2", plain.stdout.strip())

            other_issue = self.run_script(root, "corrections", unit, run_id, "sample#99", "--state-root", str(state), "--json")
            self.assertEqual(0, other_issue.returncode, other_issue.stderr)
            # The `run.resumed` base (1) names `sample#01` in `data.issue`, so it is Issue-scoped and
            # must never lend itself to sample#99: only sample#99's own refutation followed by a real
            # correction pass counts, giving 0 (base, withheld) + 1 = 1.
            self.assertEqual(1, json.loads(other_issue.stdout)["correctionsSpent"])

    def test_corrections_resumed_base_only_applies_to_the_resumed_issue(self) -> None:
        # A single Run log resumed for Issue A (base 2) must never lend that base to Issue B, even
        # when B has its own started correction pass in the same log, and an unrelated Issue C that
        # never appears in the log must derive 0.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]
            run_id = "per-issue-base-run"
            for event in (
                self.started(run_id),
                {
                    "ts": "2026-09-13T12:00:10Z", "run": run_id, "event": "run.resumed",
                    "data": {"priorRun": "run-before", "worktree": str(root), "issue": "issue-a#01", "correctionsSpent": 2},
                },
                {
                    "ts": "2026-09-13T12:01:00Z", "run": run_id, "event": "phase.started",
                    "issue": "issue-b#01", "phase": "Implement", "data": {"worktree": str(root)},
                },
                {
                    "ts": "2026-09-13T12:02:00Z", "run": run_id, "event": "refutation",
                    "issue": "issue-b#01", "phase": "Critic", "data": {"attempt": 1, "refutations": ["b needs work"]},
                },
                {
                    "ts": "2026-09-13T12:03:00Z", "run": run_id, "event": "phase.started",
                    "issue": "issue-b#01", "phase": "Implement", "data": {"worktree": str(root)},
                },
            ):
                appended = self.run_script(root, "append", unit, "--state-root", str(state), event=event)
                self.assertEqual(0, appended.returncode, appended.stderr)

            issue_a = self.run_script(root, "corrections", unit, run_id, "issue-a#01", "--state-root", str(state), "--json")
            self.assertEqual(0, issue_a.returncode, issue_a.stderr)
            # Base 2 (resumed for issue-a#01, no started corrections of its own in this log) + 0 = 2.
            self.assertEqual(2, json.loads(issue_a.stdout)["correctionsSpent"])

            issue_b = self.run_script(root, "corrections", unit, run_id, "issue-b#01", "--state-root", str(state), "--json")
            self.assertEqual(0, issue_b.returncode, issue_b.stderr)
            # Base withheld (resumed names issue-a#01, not issue-b#01) + 1 (issue-b#01's own started
            # correction pass) = 1.
            self.assertEqual(1, json.loads(issue_b.stdout)["correctionsSpent"])

            issue_c = self.run_script(root, "corrections", unit, run_id, "issue-c#01", "--state-root", str(state), "--json")
            self.assertEqual(0, issue_c.returncode, issue_c.stderr)
            # issue-c#01 never appears in this log at all: base withheld, no started corrections, 0.
            self.assertEqual(0, json.loads(issue_c.stdout)["correctionsSpent"])

    def test_corrections_rejects_unknown_run_or_malformed_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            unit = json.loads(self.run_script(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]

            missing_run = self.run_script(root, "corrections", unit, "no-such-run", "sample#01", "--state-root", str(state), "--json")
            self.assertEqual(1, missing_run.returncode)
            self.assertIn("no Run log for no-such-run", missing_run.stderr)

            bad_issue = self.run_script(root, "corrections", unit, "no-such-run", "not-an-issue", "--state-root", str(state), "--json")
            self.assertEqual(1, bad_issue.returncode)
            self.assertIn("issue", bad_issue.stderr.lower())


if __name__ == "__main__":
    unittest.main()
