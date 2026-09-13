#!/usr/bin/env python3
"""Smoke coverage for the portable legacy planning and round paths."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "asdlc"
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common import parse_issue, resolve_policy  # noqa: E402


class LegacyWorkflowSmokeTests(unittest.TestCase):
    def test_no_policy_repository_stops_at_planning_approval_and_no_ready_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            issue_path = root / ".scratch" / "portable" / "issues" / "01-portable-loop.md"
            issue_path.parent.mkdir(parents=True)
            issue_path.write_text(
                """# Portable loop

Type: issue
Status: draft
Slice: `portable#01`

## Acceptance criteria

- [ ] preserve the existing parser

## Blocked by

- None
""",
                encoding="utf-8",
            )
            policy = resolve_policy(root)
            self.assertEqual(".scratch/{slug}/issues", policy["artifacts"]["issues"])
            self.assertFalse((root / ".gantry" / "config.json").exists())

            issue = parse_issue(issue_path)
            self.assertEqual("portable#01", issue.ref)
            self.assertEqual("draft", issue.status)
            self.assertEqual(["preserve the existing parser"], [item.text for item in issue.criteria])
            self.assertEqual([], issue.blocked_by)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "frontier.py"),
                    "--scope",
                    "portable",
                    "--json",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertEqual([], json.loads(result.stdout)["selected"])

        plan = (SKILL_DIR / "reference" / "plan-workflow.md").read_text(encoding="utf-8")
        round_workflow = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8")
        self.assertIn("planning approval", plan.lower())
        self.assertIn("A.policy", plan)
        self.assertIn("A.paths.issueDir", plan)
        self.assertIn("A.policy", round_workflow)
        self.assertIn("paths.decisions", round_workflow)

    def test_workflow_templates_receive_paths_in_args_without_repository_literals(self) -> None:
        prohibited = ("gantry-v4", "slice-index", "the Gantry repository")
        for path in (
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "reference" / "plan-workflow.md",
            SKILL_DIR / "reference" / "round-workflow.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertFalse(
                any(literal in text for literal in prohibited),
                f"{path.relative_to(REPO_ROOT)} contains a repository-specific literal",
            )

    def test_scripts_import_only_standard_library_or_pack_modules(self) -> None:
        allowed = {
            "__future__",
            "acceptance",
            "argparse",
            "common",
            "copy",
            "dataclasses",
            "datetime",
            "difflib",
            "json",
            "os",
            "pathlib",
            "re",
            "shutil",
            "subprocess",
            "sys",
        }
        for script in sorted(SCRIPTS.glob("*.py")):
            tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
            imported = {
                alias.name.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imported |= {
                node.module.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            self.assertLessEqual(imported, allowed, f"{script.name}: {sorted(imported - allowed)}")


if __name__ == "__main__":
    unittest.main()
