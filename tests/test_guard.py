#!/usr/bin/env python3
"""Contracts for the guard hook handler: protect, record, degrade -- never decide."""
from __future__ import annotations

import json
import os
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

    # -- Issue creation exemption -----------------------------------------------------------

    def test_allows_writing_a_new_draft_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            draft_content = "Type: issue\nStatus: draft\n\n## Acceptance criteria\n\n- [ ] Some criterion\n"
            payload = {
                "session_id": "sess-1",
                "tool_name": "Write",
                "tool_input": {"file_path": ".scratch/sample/issues/10-new.md", "content": draft_content},
            }
            allowed = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)

    def test_denies_writing_over_an_existing_issue_that_changes_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text("Type: issue\nStatus: draft\n\n## Acceptance criteria\n\n- [ ] Some criterion\n", encoding="utf-8")

            payload = {
                "session_id": "sess-1",
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "content": "Type: issue\nStatus: ready-for-agent\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode)
            self.assertIn("issue-status-protected", denied.stdout)

    def test_denies_writing_draft_status_over_an_existing_ready_for_agent_issue(self) -> None:
        """The draft-content exemption is for *creating* an Issue, never for downgrading one."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "content": "Type: issue\nStatus: draft\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode)
            self.assertIn("issue-status-protected", denied.stdout)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "hook.denied"]))

    def test_denies_multiedit_unchecking_an_existing_issue_acceptance_checkbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Acceptance criteria\n\n- [x] Some criterion\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "MultiEdit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "edits": [{"old_string": "- [x] Some criterion", "new_string": "- [ ] Some criterion"}],
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode)
            self.assertIn("issue-checkbox-protected", denied.stdout)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "hook.denied"]))

    def test_denies_value_only_status_edit_on_an_existing_issue(self) -> None:
        """old_string/new_string that never spell 'Status:' must still be caught by comparing the file."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "old_string": "ready-for-agent",
                    "new_string": "done",
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("issue-status-protected", denied.stdout)
            self.assertIn("10-new.md", denied.stdout)

    def test_denies_value_only_checkbox_edit_on_an_existing_issue(self) -> None:
        """old_string/new_string missing the leading '- ' scaffolding must still be caught."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "old_string": "[ ] Some criterion",
                    "new_string": "[x] Some criterion",
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("issue-checkbox-protected", denied.stdout)

    def test_allows_a_value_only_edit_that_does_not_touch_status_or_checkboxes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Comments\n\nold note\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "old_string": "old note",
                    "new_string": "new note",
                },
            }
            allowed = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)

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

            capability_incomplete = self.run_guard(root, "SubagentStop", "--state-root", str(state), "--run-id", run, payload={"unexpected": True})
            self.assertEqual(0, capability_incomplete.returncode)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            stopped = [event for event in events if event["event"] == "subagent.stopped"]
            # Capability-incomplete payload never fabricates a plain subagent.stopped completion.
            self.assertEqual(1, len(stopped))
            self.assertEqual("implementer", stopped[0]["data"]["role"])
            degraded = [event for event in events if event["event"] == "hook.degraded"]
            self.assertEqual(1, len(degraded))
            self.assertEqual("SubagentStop", degraded[0]["data"]["source"])
            self.assertIn("session_id", degraded[0]["data"]["missing"])
            self.assertIs(True, degraded[0]["data"]["degraded"])

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

    def test_undecodable_stdin_with_a_resolvable_run_id_records_one_degraded_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            def events(unit: str) -> list[dict]:
                path = state / unit / "runs" / f"{run}.jsonl"
                return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

            unit = self.unit_id(root)

            for stdin_text, harness_event in (
                ("[1, 2, 3]", "SubagentStop"),
                ("not json at all", "SubagentStart"),
                ("", "PreCompact"),
                ('"just a string"', "SubagentStop"),
            ):
                before = len(events(unit))
                result = subprocess.run(
                    [sys.executable, str(GUARD), harness_event, "--state-root", str(state), "--run-id", run],
                    cwd=root,
                    input=stdin_text,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                after = events(unit)
                self.assertEqual(before + 1, len(after))
                self.assertEqual("hook.degraded", after[-1]["event"])
                self.assertEqual(harness_event, after[-1]["data"]["source"])
                self.assertEqual(["payload"], after[-1]["data"]["missing"])
                self.assertIs(True, after[-1]["data"]["degraded"])

    def test_undecodable_stdin_without_a_run_id_or_env_records_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            def event_count(unit: str) -> int:
                path = state / unit / "runs" / f"{run}.jsonl"
                return len(path.read_text(encoding="utf-8").splitlines())

            unit = self.unit_id(root)
            before = event_count(unit)

            env = {key: value for key, value in os.environ.items() if key != "GANTRY_RUN_ID"}
            for stdin_text, harness_event in (
                ("[1, 2, 3]", "SubagentStop"),
                ("not json at all", "SubagentStart"),
                ("", "PreCompact"),
                ('"just a string"', "SubagentStop"),
            ):
                result = subprocess.run(
                    [sys.executable, str(GUARD), harness_event, "--state-root", str(state)],
                    cwd=root,
                    input=stdin_text,
                    text=True,
                    capture_output=True,
                    check=False,
                    env=env,
                )
                self.assertEqual(0, result.returncode, result.stderr)

            self.assertEqual(before, event_count(unit))

    def test_pretooluse_missing_required_fields_is_recorded_as_degraded_and_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            payload = {"tool_name": "Edit"}
            result = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(0, result.returncode)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            degraded = [event for event in events if event["event"] == "hook.degraded"]
            self.assertEqual(1, len(degraded))
            self.assertEqual("PreToolUse", degraded[0]["data"]["source"])
            self.assertIn("tool_input", degraded[0]["data"]["missing"])

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

    def test_denies_git_add_then_commit_of_an_unstaged_skip_file(self) -> None:
        """'git add <file> && git commit' must be checked against the working tree, not just the index."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            (root / "app_test.py").write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    @unittest.skip('later')\n    def test_x(self):\n        pass\n",
                encoding="utf-8",
            )
            # Deliberately never actually run `git add`: guard.py must not trust the index alone.
            payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git add app_test.py && git commit -m x"}}
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("no-test-skip-commit", denied.stdout)
            self.assertIn("app_test.py", denied.stdout)

    def test_allows_git_add_then_commit_of_a_clean_unstaged_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            (root / "app_test.py").write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n",
                encoding="utf-8",
            )
            payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git add app_test.py && git commit -m x"}}
            allowed = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)

    def test_denies_commit_dash_a_of_a_tracked_but_unstaged_skip_edit(self) -> None:
        """'git commit -am' must be checked against unstaged tracked changes too, not just --cached."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            test_file = root / "app_test.py"
            test_file.write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "app_test.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "add test"], cwd=root, check=True)

            # Now modify the tracked file without staging the change.
            test_file.write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    @unittest.skip('later')\n    def test_x(self):\n        pass\n",
                encoding="utf-8",
            )
            payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git commit -am x"}}
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("no-test-skip-commit", denied.stdout)
            self.assertIn("app_test.py", denied.stdout)

    def test_allows_commit_dash_a_of_a_clean_tracked_unstaged_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            test_file = root / "app_test.py"
            test_file.write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "app_test.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "add test"], cwd=root, check=True)

            test_file.write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n    def test_y(self):\n        pass\n",
                encoding="utf-8",
            )
            payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": "git commit -am x"}}
            allowed = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)

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

    def test_uses_payload_cwd_over_dash_dash_cwd_to_find_a_staged_test_skip_pattern(self) -> None:
        """A payload naming its own cwd (a worktree) must be checked there, not at --cwd."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "harness-cwd"
            root.mkdir()
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            worktree = Path(temp) / "payload-worktree"
            worktree.mkdir()
            self.init_repository(worktree)
            (worktree / "app_test.py").write_text(
                "import unittest\n\nclass T(unittest.TestCase):\n    @unittest.skip('later')\n    def test_x(self):\n        pass\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "app_test.py"], cwd=worktree, check=True)

            commit_payload = {
                "session_id": "sess-1",
                "cwd": str(worktree),
                "tool_name": "Bash",
                "tool_input": {"command": "git commit -m 'add test'"},
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=commit_payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("no-test-skip-commit", denied.stdout)
            self.assertIn("app_test.py", denied.stdout)

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
