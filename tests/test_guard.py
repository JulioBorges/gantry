#!/usr/bin/env python3
"""Contracts for the guard hook handler: protect, record, degrade -- never decide."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts"
GUARD = SCRIPTS / "guard.py"
RUNLOG = SCRIPTS / "runlog.py"


class GuardHookTests(unittest.TestCase):
    def run_guard(self, root: Path, *args: str, payload: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GUARD), *args],
            cwd=root,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def run_runlog(self, root: Path, *args: str, event: dict | None = None) -> subprocess.CompletedProcess[str]:
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
        subprocess.run(["git", "config", "user.email", "guard@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Guard Test"], cwd=root, check=True)
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)

    def unit_id(self, root: Path) -> str:
        return json.loads(self.run_runlog(root, "unit-id", "--cwd", str(root), "--json").stdout)["unitId"]

    def seed_run(self, root: Path, state: Path, run: str = "run-01") -> str:
        unit = self.unit_id(root)
        started = {
            "ts": "2026-09-13T12:00:00Z",
            "run": run,
            "event": "run.started",
            "data": {"repositoryRoot": str(root), "policyHash": "abc123", "tier": "reference", "staleAfterSeconds": 900},
        }
        accepted = self.run_runlog(root, "append", unit, "--state-root", str(state), event=started)
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        return run

    # -- ROADMAP.md / Status protection ---------------------------------------------------

    def test_denies_editing_roadmap_and_allows_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            edit_payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {"file_path": "ROADMAP.md", "old_string": "- gantry-migration#09", "new_string": "- [x] gantry-migration#09"},
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=edit_payload)
            self.assertEqual(2, denied.returncode)
            lines = [line for line in denied.stdout.splitlines() if line]
            self.assertEqual(1, len(lines))
            self.assertIn("roadmap-protected", lines[0])
            self.assertIn("ROADMAP.md", lines[0])

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            denials = [event for event in events if event["event"] == "hook.denied"]
            self.assertEqual(1, len(denials))
            self.assertEqual("roadmap-protected", denials[0]["data"]["rule"])
            self.assertEqual("ROADMAP.md", denials[0]["data"]["path"])

            read_payload = {"session_id": "sess-1", "tool_name": "Read", "tool_input": {"file_path": "ROADMAP.md"}}
            allowed = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=read_payload)
            self.assertEqual(0, allowed.returncode)
            self.assertEqual("allow", allowed.stdout.strip())

    def test_denies_editing_an_issue_status_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/09-guard.md",
                    "old_string": "Status: ready-for-agent",
                    "new_string": "Status: done",
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode)
            lines = [line for line in denied.stdout.splitlines() if line]
            self.assertEqual(1, len(lines))
            self.assertIn("issue-status-protected", lines[0])
            self.assertIn("09-guard.md", lines[0])

    # -- checkbox protection ---------------------------------------------------------------

    def test_denies_editing_an_issue_acceptance_checkbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/09-guard.md",
                    "old_string": "- [ ] Some criterion",
                    "new_string": "- [x] Some criterion",
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode)
            lines = [line for line in denied.stdout.splitlines() if line]
            self.assertEqual(1, len(lines))
            self.assertIn("issue-checkbox-protected", lines[0])

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "hook.denied"]))

    # -- subagent + degradation --------------------------------------------------------------

    def test_subagent_stop_appends_event_and_malformed_payload_still_degrades_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            good = self.run_guard(
                root,
                "SubagentStop",
                "--state-root",
                str(state),
                "--run-id",
                run,
                payload={"session_id": "sess-1", "subagent_type": "implementer"},
            )
            self.assertEqual(0, good.returncode)

            malformed = self.run_guard(root, "SubagentStop", "--state-root", str(state), "--run-id", run, payload={"unexpected": True})
            self.assertEqual(0, malformed.returncode)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            stopped = [event for event in events if event["event"] == "subagent.stopped"]
            self.assertEqual(2, len(stopped))
            self.assertEqual("implementer", stopped[0]["data"]["role"])
            self.assertEqual("unknown", stopped[1]["data"]["role"])

            # No run context available at all: never crashes, never fabricates completion.
            no_run_context = subprocess.run(
                [sys.executable, str(GUARD), "SubagentStop", "--state-root", str(state)],
                cwd=root,
                input=json.dumps({"nothing": "useful"}),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, no_run_context.returncode)

    # -- force push and test-skip commit -----------------------------------------------------

    def test_denies_force_push_and_test_skip_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            push_payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}
            denied_push = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=push_payload)
            self.assertEqual(2, denied_push.returncode)
            self.assertIn("no-force-push", denied_push.stdout)

            safe_push = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git push origin main"}}
            allowed_push = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=safe_push)
            self.assertEqual(0, allowed_push.returncode)

            (root / "app_test.py").write_text("import unittest\n\nclass T(unittest.TestCase):\n    @unittest.skip('later')\n    def test_x(self):\n        pass\n", encoding="utf-8")
            subprocess.run(["git", "add", "app_test.py"], cwd=root, check=True)
            commit_payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git commit -m 'add test'"}}
            denied_commit = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=commit_payload)
            self.assertEqual(2, denied_commit.returncode)
            self.assertIn("no-test-skip-commit", denied_commit.stdout)
            self.assertIn("app_test.py", denied_commit.stdout)

            subprocess.run(["git", "reset"], cwd=root, check=True)
            (root / "app_test.py").write_text("import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n", encoding="utf-8")
            subprocess.run(["git", "add", "app_test.py"], cwd=root, check=True)
            allowed_commit = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=commit_payload)
            self.assertEqual(0, allowed_commit.returncode)

    def test_allows_committing_guards_own_source_despite_skip_pattern_literals(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            (root / "guard.py").write_bytes(GUARD.read_bytes())
            (root / "test_guard.py").write_bytes((REPO_ROOT / "tests" / "test_guard.py").read_bytes())
            subprocess.run(["git", "add", "guard.py", "test_guard.py"], cwd=root, check=True)

            commit_payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git commit -m 'copy guard sources'"}}
            allowed = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=commit_payload)
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)

    def test_denies_push_with_a_leading_plus_refspec(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            plus_refspec_payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git push origin +main"}}
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=plus_refspec_payload)
            self.assertEqual(2, denied.returncode)
            self.assertIn("no-force-push", denied.stdout)

    # -- performance --------------------------------------------------------------------------

    def test_answers_a_one_megabyte_payload_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            payload = {"session_id": "sess-1", "tool_name": "Read", "tool_input": {"file_path": "big.txt", "content": "x" * (1024 * 1024)}}
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    # -- unknown / non-decision events never grant authority ----------------------------------

    def test_unknown_event_and_precompact_degrade_without_granting_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            unknown = self.run_guard(root, "SomeFutureEvent", "--state-root", str(state), "--run-id", run, payload={"anything": 1})
            self.assertEqual(0, unknown.returncode)

            compaction = self.run_guard(root, "PreCompact", "--state-root", str(state), "--run-id", run, payload={"trigger": "auto"})
            self.assertEqual(0, compaction.returncode)
            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "compaction"]))
            self.assertEqual("auto", [event for event in events if event["event"] == "compaction"][0]["data"]["source"])


if __name__ == "__main__":
    unittest.main()
