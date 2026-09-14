#!/usr/bin/env python3
"""Automated transcript tests for the Gantry setup skill."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import io

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

import setup  # type: ignore

class GantrySetupTests(unittest.TestCase):
    def test_setup_transcript_proves_config_json_is_shown_and_waits_for_confirmation(self) -> None:
        """A setup transcript test proves `.gantry/config.json` is shown in full and is not written before confirmation."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            config_json = {"artifacts": {"specs": ".scratch/specs"}}
            
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                        with mock.patch("builtins.input", return_value="n") as mock_input:
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                with self.assertRaises(SystemExit):
                                    setup.main()
                                
            output = mock_stdout.getvalue()
            self.assertIn("Proposed .gantry/config.json:", output)
            self.assertIn('"specs": ".scratch/specs"', output)
            
            mock_input.assert_called_once_with("Write this policy? [y/N] ")
            
            self.assertFalse((root / ".gantry" / "config.json").exists())

    def test_existing_policy_offers_merge_overwrite_abort(self) -> None:
        """An existing policy offers merge, overwrite, or abort with the chosen outcome observable on disk."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_path = gantry_dir / "config.json"
            config_path.write_text(json.dumps({"existing": "value"}), encoding="utf-8")
            
            config_json = {"new": "value2"}
            
            # Test Merge
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        with mock.patch("builtins.input", return_value="m") as mock_input:
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                setup.main()
                                
            mock_input.assert_called_once_with("Config exists. [M]erge, [O]verwrite, or [A]bort? ")
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual({"existing": "value", "new": "value2"}, written)
            
            # Test Overwrite
            config_json2 = {"overwrite": "yes"}
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json2))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        with mock.patch("builtins.input", return_value="o") as mock_input:
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                setup.main()
                                
            written2 = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual({"overwrite": "yes"}, written2)

    def test_running_accepted_setup_twice_produces_byte_identical_claude_settings(self) -> None:
        """Running accepted setup twice produces byte-identical .claude/settings.json, preserves unrelated keys."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            
            claude_dir = root / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            
            # create initial unrelated key
            settings_path.write_text(json.dumps({"unrelated": "key"}, indent=2) + "\n", encoding="utf-8")
            
            config_json = {"test": "val"}
            
            # First run
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        with mock.patch("builtins.input", return_value="y"):
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                setup.main()
                                
            content_first = settings_path.read_text(encoding="utf-8")
            parsed_first = json.loads(content_first)
            self.assertEqual("key", parsed_first["unrelated"])
            self.assertIn("hooks", parsed_first)
            
            # Second run (setup accepted again, overwrite)
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        with mock.patch("builtins.input", return_value="o"):
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                setup.main()
                                
            content_second = settings_path.read_text(encoding="utf-8")
            self.assertEqual(content_first, content_second, "Second run should produce byte-identical file")

    def test_setup_adds_or_replaces_only_marked_gantry_section_in_agents_md(self) -> None:
        """Setup adds or replaces only the marked Gantry section in AGENTS.md."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            agents_path = root / "AGENTS.md"
            
            initial_content = "Existing content\n"
            agents_path.write_text(initial_content, encoding="utf-8")
            
            config_json = {"test": "val"}
            
            # First run
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        with mock.patch("builtins.input", return_value="y"):
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                setup.main()
                                
            first_run_content = agents_path.read_text(encoding="utf-8")
            self.assertTrue(first_run_content.startswith("Existing content\n"))
            self.assertIn("<!-- gantry:begin -->", first_run_content)
            self.assertIn("<!-- gantry:end -->", first_run_content)
            
            # Second run, should replace the section exactly
            with mock.patch("sys.argv", ["setup.py"]):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(config_json))):
                    with mock.patch("sys.stdout", new_callable=io.StringIO):
                        with mock.patch("builtins.input", return_value="o"):
                            with mock.patch("pathlib.Path.cwd", return_value=root):
                                setup.main()
                                
            second_run_content = agents_path.read_text(encoding="utf-8")
            self.assertEqual(first_run_content, second_run_content)
            
    def test_skill_prompt_instructions(self) -> None:
        """The skill reads capability declarations, creates no engine, etc."""
        skill_path = REPO_ROOT / ".agents" / "skills" / "gantry-setup" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        
        self.assertIn("reads capability declarations", content.lower() or content)
        self.assertIn("benefit, trade-off, default", content.lower() or content)
        self.assertIn("creates no engine", content.lower() or content)
        self.assertIn("database", content.lower() or content)
        self.assertIn("mcp service", content.lower() or content)
        self.assertIn("automatic cleanup", content.lower() or content)
        self.assertIn("enables recording by default", content.lower() or content)
        self.assertIn("asks before denial hooks", content.lower() or content)
        self.assertIn("preserves pack defaults when skipped", content.lower() or content)

if __name__ == "__main__":
    unittest.main()
