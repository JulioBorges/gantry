#!/usr/bin/env python3
"""Tests for Caveman setup preference, discovery, and coordinating agent activation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
SETUP_SCRIPT = SCRIPTS / "setup.py"
CAVEMAN_SCRIPT = SCRIPTS / "caveman.py"

sys.path.insert(0, str(SCRIPTS))
from common import resolve_policy  # noqa: E402
import caveman  # noqa: E402


class CavemanPolicyAndSetupTests(unittest.TestCase):
    def test_default_policy_has_caveman_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            policy = resolve_policy(root)
            self.assertIn("caveman", policy)
            self.assertFalse(policy["caveman"])

    def test_setup_persists_confirmed_caveman_preference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_json = {"caveman": True}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="y\n")
            config_path = root / ".gantry" / "config.json"
            self.assertTrue(config_path.exists())
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertTrue(written.get("caveman"))

    def test_setup_merge_preserves_existing_caveman_preference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_path = gantry_dir / "config.json"
            config_path.write_text(json.dumps({"caveman": True, "git": {"target": "main"}}), encoding="utf-8")

            # Merge with new config that doesn't mention caveman
            config_json = {"git": {"prefix": "work/"}}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="m\n")
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertTrue(written.get("caveman"))
            self.assertEqual("main", written["git"]["target"])
            self.assertEqual("work/", written["git"]["prefix"])

    def test_setup_supports_explicit_disabling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_path = gantry_dir / "config.json"
            config_path.write_text(json.dumps({"caveman": True}), encoding="utf-8")

            # Merge with explicit caveman: false
            config_json = {"caveman": False}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="m\n")
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertFalse(written.get("caveman"))


class CavemanDiscoveryAndActivationTests(unittest.TestCase):
    def test_installation_guidance_for_supported_harnesses(self) -> None:
        claude_cmd = caveman.get_install_guidance("claude-code")
        self.assertIn("npx skills add caveman", claude_cmd)

        agy_cmd = caveman.get_install_guidance("antigravity")
        self.assertIn("~/.gemini/config/skills/caveman", agy_cmd)

        codex_cmd = caveman.get_install_guidance("codex")
        self.assertIn(".agents/skills/caveman", codex_cmd)

    def test_discovery_verifies_skill_readability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Not found
            res = caveman.check_availability("claude-code", root=root)
            self.assertFalse(res["available"])
            self.assertEqual("not_found", res["reason"])

            # Create mock skill file
            skill_dir = root / ".agents" / "skills" / "caveman"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("# Caveman Lite\nConcise instructions.\n", encoding="utf-8")

            res = caveman.check_availability("claude-code", root=root)
            self.assertTrue(res["available"])
            self.assertEqual(str(skill_file.resolve()), res["path"])

    def test_activation_disabled_preference_does_not_load_skill(self) -> None:
        policy = {"caveman": False}
        res = caveman.resolve_activation(policy, harness="claude-code")
        self.assertFalse(res["preference"])
        self.assertFalse(res["active"])
        self.assertIsNone(res["warning"])

    def test_activation_available_skill_activates_lite_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / ".agents" / "skills" / "caveman"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Caveman Lite\n", encoding="utf-8")

            policy = {"caveman": True}
            res = caveman.resolve_activation(policy, harness="claude-code", root=root)
            self.assertTrue(res["preference"])
            self.assertTrue(res["active"])
            self.assertIsNone(res["warning"])
            self.assertEqual("conversational_and_summaries", res["scope"])

    def test_activation_fallback_and_warning_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = {"caveman": True}

            # First check when skill is not installed: emits warning
            res1 = caveman.resolve_activation(policy, harness="claude-code", root=root, warned=False)
            self.assertTrue(res1["preference"])
            self.assertFalse(res1["active"])
            self.assertIsNotNone(res1["warning"])
            self.assertIn("Caveman lite is enabled", res1["warning"])
            self.assertTrue(res1["warned"])

            # Subsequent check in the same Run (warned=True): does NOT repeat warning
            res2 = caveman.resolve_activation(policy, harness="claude-code", root=root, warned=True)
            self.assertTrue(res2["preference"])
            self.assertFalse(res2["active"])
            self.assertIsNone(res2["warning"])
            self.assertTrue(res2["warned"])

    def test_coordinating_instructions_include_caveman_when_active(self) -> None:
        instructions = caveman.get_coordinating_instructions(active=True)
        self.assertIn("Caveman lite", instructions)
        self.assertIn("conversational messages and summaries", instructions)
        self.assertIn("retain full detail", instructions)

        inactive_instructions = caveman.get_coordinating_instructions(active=False)
        self.assertEqual("", inactive_instructions)


if __name__ == "__main__":
    unittest.main()
