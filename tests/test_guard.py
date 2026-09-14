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

    def test_denies_editing_roadmap_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            for variant in ("roadmap.md", "Roadmap.md"):
                with self.subTest(variant=variant):
                    edit_payload = {
                        "session_id": "sess-1",
                        "tool_name": "Edit",
                        "tool_input": {
                            "file_path": variant,
                            "old_string": "- gantry-migration#09",
                            "new_string": "- [x] gantry-migration#09",
                        },
                    }
                    denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=edit_payload)
                    self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
                    lines = [line for line in denied.stdout.splitlines() if line]
                    self.assertEqual(1, len(lines))
                    self.assertIn("roadmap-protected", lines[0])
                    self.assertIn(variant, lines[0])

                    write_payload = {
                        "session_id": "sess-1",
                        "tool_name": "Write",
                        "tool_input": {"file_path": variant, "content": "# Roadmap\n"},
                    }
                    denied_write = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=write_payload)
                    self.assertEqual(2, denied_write.returncode, denied_write.stdout + denied_write.stderr)
                    self.assertIn("roadmap-protected", denied_write.stdout)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            denials = [event for event in events if event["event"] == "hook.denied" and event["data"]["rule"] == "roadmap-protected"]
            self.assertEqual(4, len(denials))

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

    # -- replace_all must be honored, not silently treated as a single replacement ----------

    def test_denies_single_edit_replace_all_whose_later_occurrence_is_the_status_value(self) -> None:
        """The first textual occurrence of old_string sits outside the Status line, but with
        replace_all:true the real tool would rewrite every occurrence -- including the later
        one that IS the Status value. Guard must simulate the full replacement, not just the
        first hit, to catch this."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "## Notes\n\nready-for-agent needs another pass\n\nStatus: ready-for-agent\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "old_string": "ready-for-agent",
                    "new_string": "done",
                    "replace_all": True,
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            lines = [line for line in denied.stdout.splitlines() if line]
            self.assertEqual(1, len(lines))
            self.assertIn("issue-status-protected", lines[0])
            self.assertIn("10-new.md", lines[0])

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "hook.denied"]))

    def test_denies_multiedit_second_edit_replace_all_whose_occurrence_is_the_status_value(self) -> None:
        """The first edit plants the token elsewhere in the file; the second edit then
        replace_all's it, including the Status line -- guard must chain both edits and
        honor replace_all on the second one."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "## Notes\n\nplaceholder note\n\nStatus: ready-for-agent\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "MultiEdit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "edits": [
                        {"old_string": "placeholder note", "new_string": "ready-for-agent still pending"},
                        {"old_string": "ready-for-agent", "new_string": "done", "replace_all": True},
                    ],
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("issue-status-protected", denied.stdout)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "hook.denied"]))

    def test_denies_multiedit_second_edit_replace_all_whose_occurrence_is_a_checkbox_line(self) -> None:
        """Same shape as the Status case, but for '[ ]' -> '[x]' via a chained replace_all edit."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "## Notes\n\nplaceholder note\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "MultiEdit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "edits": [
                        {"old_string": "placeholder note", "new_string": "[ ] still pending"},
                        {"old_string": "[ ]", "new_string": "[x]", "replace_all": True},
                    ],
                },
            }
            denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("issue-checkbox-protected", denied.stdout)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len([event for event in events if event["event"] == "hook.denied"]))

    def test_allows_replace_all_edit_that_touches_neither_status_nor_checkbox_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Notes\n\nold note, old note again\n",
                encoding="utf-8",
            )

            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "old_string": "old note",
                    "new_string": "new note",
                    "replace_all": True,
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

    # -- Bash: only rule is the hook-disabling substring check --------------------------------

    def test_allows_ordinary_bash_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            for command in (
                "git status",
                "git push --force origin main",
                "git commit -am 'skip the world'",
                "npm test",
                "python3 -m pytest",
                "ls -la && echo done",
            ):
                with self.subTest(command=command):
                    payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": command}}
                    allowed = self.run_guard(root, "PreToolUse", payload=payload)
                    self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)
                    self.assertEqual("allow", allowed.stdout.strip())

    def test_denies_bash_commands_that_would_disable_the_git_hooks_layer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)

            for command in (
                "git commit --no-verify -m x",
                "git config core.hooksPath /tmp/evil && git push",
                "git --git-dir=/tmp/other.git push",
                "GIT_DIR=/tmp/other.git git push",
            ):
                with self.subTest(command=command):
                    payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": command}}
                    denied = self.run_guard(root, "PreToolUse", "--state-root", str(state), "--run-id", run, payload=payload)
                    self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
                    lines = [line for line in denied.stdout.splitlines() if line]
                    self.assertEqual(1, len(lines))
                    self.assertIn("hook-bypass-protected", lines[0])

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            denials = [event for event in events if event["event"] == "hook.denied" and event["data"]["rule"] == "hook-bypass-protected"]
            self.assertEqual(4, len(denials))

    def test_denies_the_documented_case_and_env_spellings_of_disabling_the_git_hook_layer(self) -> None:
        """git config keys are case-insensitive, and GIT_CONFIG_* env vars set them without `-c`."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            for command in (
                "git -c core.hookspath=/dev/null commit -m x",
                "git -c CORE.HOOKSPATH=/dev/null commit -m x",
                "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hookspath GIT_CONFIG_VALUE_0=/dev/null git commit -m x",
                "GIT_CONFIG_PARAMETERS=\"'core.hooksPath=/dev/null'\" git commit -m x",
                "GIT_CONFIG=/tmp/other.config git commit -m x",
            ):
                with self.subTest(command=command):
                    payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": command}}
                    denied = self.run_guard(root, "PreToolUse", payload=payload)
                    self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
                    self.assertIn("hook-bypass-protected", denied.stdout)

    def test_still_allows_commands_that_merely_look_like_the_disabling_spellings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            for command in (
                "git config --list",
                "echo GIT_CONFIGURATION",
                "grep -rn 'hooks path' docs/",
                "head -n 20 README.md",
            ):
                with self.subTest(command=command):
                    payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": command}}
                    allowed = self.run_guard(root, "PreToolUse", payload=payload)
                    self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)
                    self.assertEqual("allow", allowed.stdout.strip())

    # -- performance --------------------------------------------------------------------------

    def test_answers_a_one_megabyte_bash_command_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            command = "git " * (1024 * 1024 // 4)
            payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": command}}
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_answers_a_one_megabyte_bash_command_carrying_a_disabling_token_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            command = ("x" * (1024 * 1024)) + " --no-verify"
            payload = {"session_id": "sess-1", "tool_name": "Bash", "tool_input": {"command": command}}
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertIn("hook-bypass-protected", result.stdout)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_answers_editing_an_existing_issue_with_a_half_megabyte_whitespace_new_string_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)

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
                    # Keeps the checkbox line itself untouched (old_string == new_string prefix)
                    # and only appends whitespace-only lines after it, so the resulting text
                    # carries the same acceptance-criteria checkboxes as the original -- this
                    # exercises CHECKBOX_FULL_LINE_RE over 0.5 MB without changing the decision.
                    "old_string": "Some criterion\n",
                    "new_string": "Some criterion\n" + " \n" * 500_000,
                },
            }
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_answers_editing_an_existing_issue_with_a_one_megabyte_absent_old_string_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)
            issue_path = issues_dir / "10-new.md"
            issue_path.write_text(
                "Type: issue\nStatus: ready-for-agent\n\n## Acceptance criteria\n\n- [ ] Some criterion\n",
                encoding="utf-8",
            )

            # The old_string is not present in the file, so apply_edits() returns None and
            # decide() falls back to the coarse extract_text()/CHECKBOX_LINE_RE check over the
            # raw old_string + new_string text -- which must still be linear at 1 MB.
            payload = {
                "session_id": "sess-1",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/10-new.md",
                    "old_string": " \n" * (1024 * 1024 // 2),
                    "new_string": "unchanged",
                },
            }
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_answers_writing_over_an_existing_issue_with_a_one_megabyte_whitespace_content_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)

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
                    "content": " \n" * (1024 * 1024 // 2),
                },
            }
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_answers_writing_a_new_issue_with_a_one_megabyte_whitespace_content_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)

            issues_dir = root / ".scratch" / "sample" / "issues"
            issues_dir.mkdir(parents=True)

            # The target Issue does not exist yet, so decide() takes the is_draft_safe() path,
            # which must also stay linear over 1 MB of whitespace-only content.
            payload = {
                "session_id": "sess-1",
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".scratch/sample/issues/11-new.md",
                    "content": " \n" * (1024 * 1024 // 2),
                },
            }
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_answers_editing_an_existing_issue_with_a_one_megabyte_newline_only_new_string_in_under_200ms(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)

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
                    "old_string": "Some criterion\n",
                    "new_string": "Some criterion\n" + "\n" * (1024 * 1024),
                },
            }
            start = time.monotonic()
            result = self.run_guard(root, "PreToolUse", payload=payload)
            elapsed = time.monotonic() - start
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertLess(elapsed, 0.2, f"guard.py took {elapsed:.3f}s")

    def test_denial_is_recorded_from_the_worktree_marker_without_a_run_id_or_session(self) -> None:
        """The same guarantee the git hooks have: a marked worktree records its denials."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            state = root / "state"
            run = self.seed_run(root, state)
            marked = self.run_runlog(root, "mark", run, "--cwd", str(root), "--state-root", str(state))
            self.assertEqual(0, marked.returncode, marked.stderr)

            environment = {key: value for key, value in os.environ.items() if not key.startswith("GANTRY_")}
            denied = subprocess.run(
                [sys.executable, str(GUARD), "PreToolUse"],
                cwd=root,
                input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "ROADMAP.md", "old_string": "a", "new_string": "b"}}),
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(2, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("roadmap-protected", denied.stdout)

            unit = self.unit_id(root)
            events = [json.loads(line) for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()]
            denials = [event for event in events if event["event"] == "hook.denied"]
            self.assertEqual(1, len(denials))
            self.assertEqual("roadmap-protected", denials[0]["data"]["rule"])

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
