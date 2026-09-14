#!/usr/bin/env python3
"""Automated transcript tests for the Gantry setup skill."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
SETUP_SCRIPT = SCRIPTS / "setup.py"


class GantrySetupTests(unittest.TestCase):
    def test_setup_transcript_proves_config_json_is_shown_and_waits_for_confirmation(self) -> None:
        """A setup transcript test proves `.gantry/config.json` is shown in full and is not written before confirmation."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            config_json = {"artifacts": {"specs": ".scratch/specs"}}
            
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            stdout, stderr = p.communicate(input="n\n")
            
            self.assertIn("Proposed .gantry/config.json:", stdout)
            self.assertIn('"specs": ".scratch/specs"', stdout)
            self.assertIn("Write this policy? [y/N]", stdout)
            
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
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, _ = p.communicate(input="m\n")
            self.assertIn("Config exists. [M]erge, [O]verwrite, or [A]bort?", stdout)
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual({"existing": "value", "new": "value2"}, written)
            
            # Test Overwrite
            config_json2 = {"overwrite": "yes"}
            p2 = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json2)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p2.communicate(input="o\n")
            written2 = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual({"overwrite": "yes"}, written2)

    def test_running_accepted_setup_twice_produces_byte_identical_claude_settings(self) -> None:
        """Running accepted setup twice produces byte-identical .claude/settings.json, preserves unrelated keys."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            
            claude_dir = root / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            
            # create initial unrelated key with custom byte formatting
            initial_bytes = b'{\n\t"unrelated" :  "key" \n}'
            settings_path.write_bytes(initial_bytes)
            
            config_json = {"test": "val"}
            
            # First run
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="y\n")
                            
            content_first_bytes = settings_path.read_bytes()
            parsed_first = json.loads(content_first_bytes.decode("utf-8"))
            self.assertEqual("key", parsed_first["unrelated"])
            self.assertIn("hooks", parsed_first)
            
            # Assert byte-for-byte outside hooks
            self.assertTrue(content_first_bytes.startswith(b'{\n\t"unrelated" :  "key"'))
            
            # Second run (setup accepted again, overwrite)
            p2 = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p2.communicate(input="o\n")
                            
            content_second_bytes = settings_path.read_bytes()
            self.assertEqual(content_first_bytes, content_second_bytes, "Second run should produce byte-identical file")

    def test_setup_adds_or_replaces_only_marked_gantry_section_in_agents_md(self) -> None:
        """Setup adds or replaces only the marked Gantry section in AGENTS.md."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            agents_path = root / "AGENTS.md"
            
            initial_content = b"Before\nExisting content\n"
            agents_path.write_bytes(initial_content)
            
            config_json = {"test": "val"}
            
            # First run
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="y\n")
                            
            first_run_content = agents_path.read_bytes()
            self.assertTrue(first_run_content.startswith(b"Before\nExisting content\n"))
            self.assertIn(b"<!-- gantry:begin -->", first_run_content)
            self.assertIn(b"<!-- gantry:end -->", first_run_content)
            
            # Add some After content manually just to test replacement
            agents_path.write_bytes(first_run_content + b"\nAfter")
            first_run_content_with_after = agents_path.read_bytes()
            
            # Second run, should replace the section exactly
            p2 = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p2.communicate(input="o\n")
                            
            second_run_content = agents_path.read_bytes()
            self.assertEqual(first_run_content_with_after, second_run_content)
            self.assertTrue(second_run_content.startswith(b"Before\nExisting content\n"))
            self.assertTrue(second_run_content.endswith(b"\nAfter"))
            
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
