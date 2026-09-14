#!/usr/bin/env python3
"""Every declared hook entry invokes guard.py with its event and the payload on stdin."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS = REPO_ROOT / ".agents" / "skills" / "gantry" / "hooks"
CAPABILITIES = REPO_ROOT / ".agents" / "skills" / "gantry" / "capabilities"


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

    def run_hook(self, project_dir: Path, event: str, payload: dict) -> subprocess.CompletedProcess[str]:
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
            return subprocess.run([shutil.which("node"), driver_path], capture_output=True, text=True, check=False)
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
        self.assertIn("Never edit ROADMAP.md, Status, or criteria checkboxes.", self.round_workflow)
        self.assertIn("Never force-push, and never skip, disable\nor weaken a test.", self.round_workflow)

    def test_critic_prompt_checks_every_protected_rule(self) -> None:
        self.assertIn("Status/checkbox/ROADMAP edits", self.round_workflow)
        self.assertIn("skipped,\ndisabled or mock-replaced tests", self.round_workflow)
        self.assertIn("forced rewrite", self.round_workflow)


class SpecChangelogTests(unittest.TestCase):
    def test_spec_changelog_records_the_guard_hook_wiring_in_english(self) -> None:
        spec = (REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        self.assertIn(
            "Added the guard hook handler and its Claude Code, OpenCode and Codex wiring, "
            "protecting the roadmap and Issue Status/checkbox fields, force-pushes and "
            "test-skip commits, and recording hook and subagent events into the Run log.",
            spec,
        )


if __name__ == "__main__":
    unittest.main()
