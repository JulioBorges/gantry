#!/usr/bin/env python3
"""Behavioral tests for explicit Issue worktree cleanup."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLEANUP = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "cleanup.py"


class CleanupPlanTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout.strip()

    def run_cleanup(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLEANUP), *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_issue(self, root: Path, number: int, status: str) -> None:
        path = root / ".scratch" / "sample" / "issues" / f"{number:02d}-example.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"""# Sample {number:02d}

Type: issue
Status: {status}
Slice: `sample#{number:02d}`

## Acceptance criteria

- [ ] proves cleanup ownership

## Blocked by

- None
""",
            encoding="utf-8",
        )

    def add_issue_worktree(self, root: Path, number: int) -> tuple[str, Path]:
        branch = f"gantry/sample-{number:02d}"
        path = root.parent / f"sample-{number:02d}"
        self.git(root, "worktree", "add", "--quiet", "-b", branch, str(path), "gantry/sample-run")
        (path / f"{number:02d}.txt").write_text(f"{number}\n", encoding="utf-8")
        self.git(path, "add", ".")
        self.git(path, "commit", "--quiet", "-m", f"issue {number:02d}")
        return branch, path

    def setUp_fixture(self, root: Path) -> dict[str, object]:
        self.git(root, "init", "--quiet")
        self.git(root, "config", "user.email", "gantry@example.test")
        self.git(root, "config", "user.name", "Gantry Test")
        for number, status in (
            (1, "done"),
            (2, "draft"),
            (3, "blocked"),
            (4, "done"),
            (5, "unknown"),
        ):
            self.write_issue(root, number, status)
        (root / "README.md").write_text("fixture\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "--quiet", "-m", "fixture")
        self.git(root, "branch", "-M", "main")
        self.git(root, "checkout", "--quiet", "-b", "gantry/sample-run")

        worktrees = {}
        for number in range(1, 6):
            branch, path = self.add_issue_worktree(root, number)
            worktrees[number] = (branch, path)

        done_branch, _ = worktrees[1]
        self.git(root, "merge", "--no-ff", "--quiet", done_branch, "-m", "merge done issue")
        unrelated = root.parent / "unrelated"
        self.git(root, "worktree", "add", "--quiet", "-b", "topic/unrelated", str(unrelated), "gantry/sample-run")
        return {"worktrees": worktrees, "unrelated": unrelated}

    def test_plan_lists_only_done_merged_issue_worktree_and_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            fixture = self.setUp_fixture(root)
            expected_branch, expected_path = fixture["worktrees"][1]
            before_worktrees = self.git(root, "worktree", "list", "--porcelain")

            result = self.run_cleanup(root, "--plan", "--json")

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual("gantry/sample-run", plan["run_branch"])
            self.assertEqual(
                [{"issue": "sample#01", "path": str(expected_path.resolve()), "branch": expected_branch}],
                plan["worktrees"],
            )
            self.assertEqual(
                [{"issue": "sample#01", "name": expected_branch}],
                plan["branches"],
            )
            self.assertTrue(expected_path.exists())
            self.assertEqual(before_worktrees, self.git(root, "worktree", "list", "--porcelain"))
            self.assertTrue((fixture["unrelated"]).exists())

    def test_yes_removes_exactly_the_planned_clean_worktree_and_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            fixture = self.setUp_fixture(root)
            branch, path = fixture["worktrees"][1]
            plan_result = self.run_cleanup(root, "--plan", "--json")
            self.assertEqual(0, plan_result.returncode, plan_result.stderr)
            plan = json.loads(plan_result.stdout)

            result = self.run_cleanup(root, "--yes", "--json")

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            executed = json.loads(result.stdout)
            self.assertEqual(plan["worktrees"], executed["worktrees"])
            self.assertEqual(plan["branches"], executed["branches"])
            self.assertEqual([str(path.resolve())], executed["removed"]["worktrees"])
            self.assertEqual([branch], executed["removed"]["branches"])
            self.assertFalse(path.exists())
            missing_branch = subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", branch],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, missing_branch.returncode)
            for number in (2, 3, 4, 5):
                protected_branch, protected_path = fixture["worktrees"][number]
                self.assertTrue(protected_path.exists())
                self.git(root, "rev-parse", "--verify", protected_branch)
            self.assertTrue(fixture["unrelated"].exists())
            self.git(root, "rev-parse", "--verify", "topic/unrelated")

    def test_help_and_implementation_use_standard_library_only(self) -> None:
        result = self.run_cleanup(REPO_ROOT, "--help")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage:", result.stdout.lower())
        tree = ast.parse(CLEANUP.read_text(encoding="utf-8"), filename=str(CLEANUP))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports |= {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertLessEqual(
            imports,
            {"__future__", "argparse", "json", "pathlib", "subprocess", "sys", "common"},
        )

    def test_workflow_prints_a_plan_and_never_executes_cleanup_automatically(self) -> None:
        skill = (REPO_ROOT / ".agents" / "skills" / "gantry" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn('cleanup.py --plan --json', skill)
        self.assertIn("explicit Cleanup Authorization", skill)
        self.assertIn("never executes `cleanup.py --yes`", skill)


if __name__ == "__main__":
    unittest.main()
