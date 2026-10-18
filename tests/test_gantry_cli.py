"""Public process tests for the Gantry board command."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "cli.py"
COMMAND = REPO_ROOT / "bin" / "gantry.mjs"


class GantryCliBoardTests(unittest.TestCase):
    def write_fixture(self, root: Path, *, with_pack: bool = True) -> None:
        (root / ".gantry").mkdir()
        (root / ".gantry" / "config.json").write_text(json.dumps({
            "artifacts": {
                "specs": ".delivery/{slug}/specification.md",
                "issues": ".delivery/{slug}/work-items",
            },
        }), encoding="utf-8")
        if with_pack:
            (root / ".agents" / "skills" / "gantry").mkdir(parents=True)
        issue_dir = root / ".delivery" / "sample" / "work-items"
        issue_dir.mkdir(parents=True)
        (root / ".delivery" / "sample" / "specification.md").write_text(
            "# Sample Spec\nMap: `ROADMAP.md` (spec 01)\n", encoding="utf-8")
        (issue_dir / "01-ready.md").write_text("""# Ready work

Type: issue
Status: ready-for-agent
Slice: `sample#01`

## Acceptance criteria

- [ ] The board works.

## Blocked by

None
""", encoding="utf-8")
        (issue_dir / "02-blocked.md").write_text("""# Blocked work

Type: issue
Status: ready-for-agent
Slice: `sample#02`

## Acceptance criteria

- [ ] The board reports its blocker.

## Blocked by

- `sample#01`
""", encoding="utf-8")

    def run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), "--cwd", str(root), *args],
            text=True, capture_output=True, check=False,
        )

    def test_board_uses_policy_paths_and_marks_open_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)

            result = self.run_cli(root, "board")

        self.assertEqual(0, result.returncode, result.stderr)
        board = json.loads(result.stdout)
        self.assertEqual(["sample"], [spec["slug"] for spec in board["specs"]])
        self.assertFalse(board["specs"][0]["executable"])
        issues = {issue["ref"]: issue for issue in board["issues"]}
        self.assertFalse(issues["sample#01"]["frontierBlocked"])
        self.assertTrue(issues["sample#02"]["frontierBlocked"])
        self.assertEqual(["sample#01"], issues["sample#02"]["openBlockers"])
        self.assertEqual(["sample#01"], board["frontier"])

    def test_pack_unavailable_is_a_structured_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root, with_pack=False)

            result = self.run_cli(root, "board")

        self.assertEqual(2, result.returncode)
        self.assertEqual("pack-unreadable", json.loads(result.stdout)["error"]["code"])

    def test_public_command_delegates_to_the_board(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root)
            result = subprocess.run(
                ["node", str(COMMAND), "frontier", "--cwd", str(root)],
                text=True, capture_output=True, check=False,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["sample#01"], json.loads(result.stdout)["frontier"])

