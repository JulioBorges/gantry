#!/usr/bin/env python3
"""Every declared hook entry invokes guard.py with its event and the payload on stdin."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS = REPO_ROOT / ".agents" / "skills" / "gantry" / "hooks"
CAPABILITIES = REPO_ROOT / ".agents" / "skills" / "gantry" / "capabilities"
RUNLOG = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "runlog.py"


def iter_commands(node: object):
    if isinstance(node, dict):
        if isinstance(node.get("command"), str):
            yield node["command"]
        for value in node.values():
            yield from iter_commands(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_commands(item)


class ClaudeCodeHookWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = json.loads((HOOKS / "claude-code.settings.json").read_text(encoding="utf-8"))
        self.capabilities = json.loads((CAPABILITIES / "claude-code.json").read_text(encoding="utf-8"))

    def test_every_declared_capability_event_is_wired_to_guard_py_with_that_event_name(self) -> None:
        for event in self.capabilities["hook_events"]:
            self.assertIn(event, self.settings["hooks"], f"{event} is declared as a capability but not wired")
            commands = list(iter_commands(self.settings["hooks"][event]))
            self.assertTrue(commands, f"{event} has no hook command")
            for command in commands:
                self.assertIn("guard.py", command)
                self.assertIn(f"guard.py\" {event}", command.replace("'", '"'))

    def test_every_wired_entry_is_a_python3_invocation_of_the_pack_guard_script(self) -> None:
        for event, entries in self.settings["hooks"].items():
            for command in iter_commands(entries):
                self.assertTrue(command.startswith("python3 "), command)
                self.assertIn("scripts/guard.py", command)


class OpenCodeHookWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is not on PATH")
        self.capabilities = json.loads((CAPABILITIES / "opencode.json").read_text(encoding="utf-8"))
        self.plugin_source = (HOOKS / "opencode.plugin.js").read_text(encoding="utf-8")

    def load_plugin(self, project_dir: Path):
        script = f"""
const plugin = require({json.dumps(str(HOOKS / "opencode.plugin.js"))});
const hooks = plugin({{ project: {{ directory: {json.dumps(str(project_dir))} }} }});
module.exports = hooks;
"""
        return script

    def run_hook(self, project_dir: Path, event: str, payload: dict, env: dict | None = None) -> subprocess.CompletedProcess[str]:
        driver = f"""
const hooks = require({json.dumps(str(HOOKS / "opencode.plugin.js"))})({{ project: {{ directory: {json.dumps(str(project_dir))} }} }});
hooks[{json.dumps(event)}]({json.dumps(payload)}, {{}}).then(
  () => {{ console.log("resolved"); process.exit(0); }},
  (error) => {{ console.log("rejected: " + error.message); process.exit(1); }}
);
"""
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
            handle.write(driver)
            driver_path = handle.name
        try:
            return subprocess.run(
                [shutil.which("node"), driver_path], capture_output=True, text=True, check=False, env=env,
            )
        finally:
            Path(driver_path).unlink(missing_ok=True)

    def test_every_declared_capability_event_appears_as_a_named_hook_forwarding_to_guard_py(self) -> None:
        for event in self.capabilities["hook_events"]:
            self.assertIn(json.dumps(event), self.plugin_source.replace("'", '"'))
        self.assertIn("guard.py", self.plugin_source)
        self.assertIn("input: JSON.stringify", self.plugin_source)

    def test_tool_execute_before_denies_a_roadmap_edit_and_allows_a_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp)
            denied = self.run_hook(
                project_dir,
                "tool.execute.before",
                {"tool_name": "Edit", "tool_input": {"file_path": "ROADMAP.md", "old_string": "a", "new_string": "b"}},
            )
            self.assertEqual(1, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("rejected", denied.stdout)
            self.assertIn("roadmap-protected", denied.stdout)

            allowed = self.run_hook(
                project_dir,
                "tool.execute.before",
                {"tool_name": "Read", "tool_input": {"file_path": "ROADMAP.md"}},
            )
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)
            self.assertIn("resolved", allowed.stdout)

    def test_tool_execute_before_uses_opencodes_own_declared_payload_fields(self) -> None:
        """Proven against the plugin's own capability payload_fields: `tool`, `args`, `sessionID`."""
        self.assertEqual(["tool", "args", "sessionID"], self.capabilities["payload_fields"])
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp)
            denied = self.run_hook(
                project_dir,
                "tool.execute.before",
                {
                    "tool": "edit",
                    "sessionID": "sess-opencode-1",
                    "args": {"filePath": "ROADMAP.md", "oldString": "a", "newString": "b"},
                },
            )
            self.assertEqual(1, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("rejected", denied.stdout)
            self.assertIn("roadmap-protected", denied.stdout)

            allowed = self.run_hook(
                project_dir,
                "tool.execute.before",
                {"tool": "read", "args": {"filePath": "ROADMAP.md"}},
            )
            self.assertEqual(0, allowed.returncode, allowed.stdout + allowed.stderr)
            self.assertIn("resolved", allowed.stdout)

    def test_a_real_opencode_payload_records_into_the_marked_run_not_its_own_session_id(self) -> None:
        """OpenCode's `sessionID` is a session, not a Gantry Run: the marker must win over it.

        The plugin passes no `--run-id` and OpenCode exports no `GANTRY_*` variable, so the
        worktree's current-Run marker is the only thing that can name the Run -- resolving the
        session ID first would key the lookup to a Run log that never exists and drop the denial.
        """
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp)
            state = project_dir / "state"
            run = "run-opencode-1"
            subprocess.run(["git", "init", "--quiet"], cwd=project_dir, check=True)
            subprocess.run(["git", "config", "user.email", "guard@example.test"], cwd=project_dir, check=True)
            subprocess.run(["git", "config", "user.name", "Guard Test"], cwd=project_dir, check=True)
            (project_dir / "tracked.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=project_dir, check=True)

            unit = json.loads(
                subprocess.run(
                    [sys.executable, str(RUNLOG), "unit-id", "--cwd", str(project_dir), "--json"],
                    cwd=project_dir, text=True, capture_output=True, check=True,
                ).stdout
            )["unitId"]
            started = {
                "ts": "2026-09-14T12:00:00Z",
                "run": run,
                "event": "run.started",
                "data": {"repositoryRoot": str(project_dir), "policyHash": "abc123", "tier": "supported", "staleAfterSeconds": 900},
            }
            subprocess.run(
                [sys.executable, str(RUNLOG), "append", unit, "--state-root", str(state)],
                cwd=project_dir, input=json.dumps(started), text=True, capture_output=True, check=True,
            )
            subprocess.run(
                [sys.executable, str(RUNLOG), "mark", run, "--cwd", str(project_dir), "--state-root", str(state)],
                cwd=project_dir, text=True, capture_output=True, check=True,
            )

            environment = {key: value for key, value in os.environ.items() if not key.startswith("GANTRY_")}
            denied = self.run_hook(
                project_dir,
                "tool.execute.before",
                {
                    "tool": "edit",
                    "sessionID": "ses_8f1c2b7e3a4d4e5f8b901c2d3e4f5a6b",
                    "args": {"filePath": "ROADMAP.md", "oldString": "a", "newString": "b"},
                },
                env=environment,
            )
            self.assertEqual(1, denied.returncode, denied.stdout + denied.stderr)
            self.assertIn("roadmap-protected", denied.stdout)

            events = [
                json.loads(line)
                for line in (state / unit / "runs" / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            denials = [event for event in events if event["event"] == "hook.denied"]
            self.assertEqual(1, len(denials), events)
            self.assertEqual("roadmap-protected", denials[0]["data"]["rule"])
            self.assertEqual(run, denials[0]["run"])


class CodexHookWiringTests(unittest.TestCase):
    def test_placeholder_file_exists_and_grants_no_authority(self) -> None:
        payload = json.loads((HOOKS / "codex.hooks.json").read_text(encoding="utf-8"))
        capabilities = json.loads((CAPABILITIES / "codex.json").read_text(encoding="utf-8"))
        self.assertEqual([], capabilities["hook_events"])
        self.assertEqual({}, payload["hooks"])


class NoHooksFallbackTests(unittest.TestCase):
    """Every rule guard.py enforces must also be a stated, Critic-checked prompt rule."""

    def setUp(self) -> None:
        self.round_workflow = (REPO_ROOT / ".agents" / "skills" / "gantry" / "reference" / "round-workflow.md").read_text(encoding="utf-8")

    def test_implementer_prompt_states_every_protected_rule(self) -> None:
        self.assertIn(
            "Never edit ROADMAP.md, Status, or criteria checkboxes. Never force-push, and never skip, disable\n"
            "or weaken a test. Never bypass the repository git hooks: no \\`--no-verify\\` in any abbreviation\n"
            "(e.g. \\`--no-veri\\`) or \\`-n\\`, no \\`core.hooksPath\\` override in any spelling, no\n"
            "\\`--git-dir\\`/\\`GIT_DIR=\\`, no \\`GIT_CONFIG_*\\`.",
            self.round_workflow,
        )

    def test_critic_prompt_checks_every_protected_rule(self) -> None:
        self.assertIn("Status/checkbox/ROADMAP edits", self.round_workflow)
        self.assertIn("skipped,\ndisabled or mock-replaced tests", self.round_workflow)
        self.assertIn("forced rewrite", self.round_workflow)
        self.assertIn(
            "So is any commit or push made with \\`--no-verify\\` in any abbreviation (e.g.\n"
            "\\`--no-veri\\`) or \\`-n\\`, or under a \\`core.hooksPath\\`/\\`--git-dir\\`/\\`GIT_DIR=\\`/\\`GIT_CONFIG_*\\`\n"
            "override, and any test-skip pattern that reached HEAD despite the hooks.",
            self.round_workflow,
        )


class SpecChangelogTests(unittest.TestCase):
    def test_spec_changelog_records_the_guard_hook_wiring_in_english(self) -> None:
        spec = (REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        self.assertIn(
            "Added the guard hook handler and its Claude Code, OpenCode and Codex wiring, "
            "protecting the roadmap and Issue Status/checkbox fields, force-pushes and "
            "test-skip commits, and recording hook and subagent events into the Run log.",
            spec,
        )

    def test_spec_and_adr_state_the_recording_guarantee_not_a_best_effort(self) -> None:
        spec = (REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        adr = (REPO_ROOT / "docs" / "adr" / "0005-git-hooks-enforce-git-rules.md").read_text(encoding="utf-8")
        self.assertIn(
            "the same denial is always written to the run log as `hook.denied` when it happens inside a Run",
            spec,
        )
        self.assertIn("Made `hook.denied` recording a guarantee", spec)
        self.assertIn("Recording is guaranteed, not best-effort", adr)
        self.assertNotIn("Recording is therefore best-effort", adr)

    def test_documents_state_the_marker_resolution_order_and_the_worktree_enumerated_unmark(self) -> None:
        """The shipped resolution order and the Run-end unmark must be the documented ones."""
        spec = (REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        adr = (REPO_ROOT / "docs" / "adr" / "0005-git-hooks-enforce-git-rules.md").read_text(encoding="utf-8")
        skill = (REPO_ROOT / ".agents" / "skills" / "gantry" / "SKILL.md").read_text(encoding="utf-8")
        workflow = (REPO_ROOT / ".agents" / "skills" / "gantry" / "reference" / "round-workflow.md").read_text(encoding="utf-8")
        order = (
            "`GANTRY_RUN_ID` when the caller exports it, then the marker, and a harness session ID "
            "only when nothing else names a Run and its Run log already exists"
        )
        unmark = (
            "the Run's end enumerates `git worktree list --porcelain` and clears every marker naming "
            "that Run, so a worktree marked by an earlier round is never left behind"
        )
        for document, name in ((spec, "spec.md"), (adr, "ADR-0005"), (skill, "SKILL.md"), (workflow, "round-workflow.md")):
            # Prose in these files is hard-wrapped at different widths, so the sentence is asserted
            # against the document with its line wrapping collapsed -- exact wording, any wrapping.
            unwrapped = " ".join(document.split())
            self.assertIn(order, unwrapped, f"{name} must state the resolution order")
            self.assertIn(unmark, unwrapped, f"{name} must state the worktree-enumerated unmark")
        self.assertIn(
            "2026-09-14 — Corrected the Run resolution order a hook records through, and the Run-end unmark.",
            " ".join(spec.split()),
            "the Spec Changelog records this behaviour change in the same merge",
        )

    def test_spec_and_adr_name_the_no_verify_abbreviation_the_guard_actually_matches(self) -> None:
        """The documented rule must be the implemented one: `--no-veri`, not `--no-verify`."""
        spec = (REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        adr = (REPO_ROOT / "docs" / "adr" / "0005-git-hooks-enforce-git-rules.md").read_text(encoding="utf-8")
        hook_wiring = next(line for line in spec.splitlines() if line.startswith("- **Hook wiring:**"))
        self.assertIn("`--no-veri` (any `--no-verify` abbreviation)", hook_wiring)
        self.assertIn("`--no-veri` (any `--no-verify` abbreviation)", adr)
        self.assertIn(
            "2026-09-14 — Widened the guard's hook-disabling substring rule from `--no-verify` to "
            "`--no-veri`",
            spec,
        )


if __name__ == "__main__":
    unittest.main()
