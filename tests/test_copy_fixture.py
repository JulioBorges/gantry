#!/usr/bin/env python3
"""Contracts for the reference fixture's deterministic isolated-copy builder."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "fixture"
COPY_FIXTURE = FIXTURE / "tools" / "copy_fixture.py"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
GATES = SKILL_DIR / "scripts" / "gates.py"
SPEC_PY = SKILL_DIR / "scripts" / "spec.py"

sys.path.insert(0, str(SKILL_DIR / "scripts"))
from runlog import unit_id  # noqa: E402


def run_copy_fixture(mode: str, dest: Path, skill_dir: Path = SKILL_DIR) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(COPY_FIXTURE), "--mode", mode, "--skill-dir", str(skill_dir), "--dest", str(dest)],
        text=True,
        capture_output=True,
        check=False,
    )


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True).stdout.strip()


def tree_digest(root: Path) -> dict[str, str]:
    digest = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            digest[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


class CopyFixtureUnplannedModeTests(unittest.TestCase):
    def test_produces_an_isolated_repository_with_a_baseline_commit_and_no_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "dest"
            dest.mkdir()
            result = run_copy_fixture("unplanned", dest)
            self.assertEqual(result.returncode, 0, result.stderr)

            self.assertTrue((dest / ".git").is_dir())
            self.assertEqual(git(dest, "rev-list", "--count", "HEAD"), "1")
            self.assertEqual(git(dest, "status", "--porcelain"), "")

            issues_dir = dest / ".scratch" / "greeting" / "issues"
            issue_files = list(issues_dir.glob("*.md")) if issues_dir.is_dir() else []
            self.assertEqual(issue_files, [])

            spec = dest / ".scratch" / "greeting" / "spec.md"
            self.assertTrue(spec.is_file())
            check = subprocess.run(
                [sys.executable, str(SPEC_PY), "--check", str(spec), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertTrue(json.loads(check.stdout)["valid"])

            self.assertFalse((dest / ".gantry" / "runs").exists())


class CopyFixtureApprovedModeTests(unittest.TestCase):
    def test_produces_three_ready_for_agent_legacy_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "dest"
            dest.mkdir()
            result = run_copy_fixture("approved", dest)
            self.assertEqual(result.returncode, 0, result.stderr)

            self.assertTrue((dest / ".git").is_dir())
            self.assertEqual(git(dest, "rev-list", "--count", "HEAD"), "1")

            issues_dir = dest / ".scratch" / "greeting" / "issues"
            issue_files = sorted(issues_dir.glob("*.md"))
            self.assertEqual(len(issue_files), 3)
            for path in issue_files:
                text = path.read_text(encoding="utf-8")
                self.assertRegex(text, re.compile(r"^Status:\s*ready-for-agent\s*$", re.MULTILINE), msg=path.name)
                self.assertRegex(text, re.compile(r"^Slice:\s*`greeting#\d{2}`\s*$", re.MULTILINE))
                self.assertIn("## Acceptance criteria", text)
                self.assertIn("## Blocked by", text)


class CopyFixtureSkillInstallationTests(unittest.TestCase):
    def test_skill_is_pack_visible_and_copies_stay_independent_of_each_other_and_the_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            first.mkdir()
            second.mkdir()

            self.assertEqual(run_copy_fixture("unplanned", first).returncode, 0)
            self.assertEqual(run_copy_fixture("approved", second).returncode, 0)

            for dest in (first, second):
                installed_skill_md = dest / ".agents" / "skills" / "gantry" / "SKILL.md"
                self.assertTrue(installed_skill_md.is_file())
                self.assertEqual(installed_skill_md.read_text(), (SKILL_DIR / "SKILL.md").read_text())

                visible_skill_md = dest / ".claude" / "skills" / "gantry" / "SKILL.md"
                self.assertTrue(visible_skill_md.is_file())
                self.assertTrue((dest / ".claude" / "skills").is_symlink())

            source_unit = unit_id(REPO_ROOT)
            first_unit = unit_id(first)
            second_unit = unit_id(second)
            self.assertEqual(len({source_unit, first_unit, second_unit}), 3)

            def common_dir(root: Path) -> Path:
                raw = Path(git(root, "rev-parse", "--git-common-dir"))
                return raw.resolve() if raw.is_absolute() else (root / raw).resolve()

            first_common = common_dir(first)
            second_common = common_dir(second)
            self.assertNotEqual(first_common, second_common)
            self.assertTrue(first_common.is_relative_to(first.resolve()))
            self.assertTrue(second_common.is_relative_to(second.resolve()))


class CopyFixtureRunnableChecksTests(unittest.TestCase):
    def test_generated_copy_carries_a_runnable_absolute_and_differential_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "dest"
            dest.mkdir()
            self.assertEqual(run_copy_fixture("approved", dest).returncode, 0)

            pytest_check = subprocess.run(["pytest", "-q"], cwd=dest, text=True, capture_output=True, check=False)
            self.assertEqual(pytest_check.returncode, 0, pytest_check.stdout + pytest_check.stderr)

            base = git(dest, "rev-parse", "HEAD")
            gate_check = subprocess.run(
                [sys.executable, str(GATES), "--run", "--diff-base", base, "--cwd", str(dest), "--json"],
                cwd=dest,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(gate_check.returncode, 0, gate_check.stdout + gate_check.stderr)
            payload = json.loads(gate_check.stdout)
            self.assertEqual(payload["verdict"], "pass")
            names = {gate["name"] for gate in payload["gates"]}
            self.assertEqual(names, {"pytest", "lint"})
            lint_gate = next(gate for gate in payload["gates"] if gate["name"] == "lint")
            self.assertEqual(lint_gate["status"], "pass")
            self.assertEqual(lint_gate["new"], [])
            self.assertEqual(lint_gate["aggravated"], [])


class CopyFixtureLeavesSourceUntouchedTests(unittest.TestCase):
    def test_neither_mode_modifies_the_source_fixture_or_the_canonical_skill_directory(self) -> None:
        before_fixture = tree_digest(FIXTURE)
        before_skill = tree_digest(SKILL_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            unplanned = Path(tmp) / "unplanned"
            approved = Path(tmp) / "approved"
            unplanned.mkdir()
            approved.mkdir()
            self.assertEqual(run_copy_fixture("unplanned", unplanned).returncode, 0)
            self.assertEqual(run_copy_fixture("approved", approved).returncode, 0)

        self.assertEqual(tree_digest(FIXTURE), before_fixture)
        self.assertEqual(tree_digest(SKILL_DIR), before_skill)
