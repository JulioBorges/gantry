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


class GantryCliExecuteTests(unittest.TestCase):
    def write_script(self, path: Path, body: str) -> None:
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(0o755)

    def git(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)

    def fixture(self, root: Path, *, spec: bool = True, commands: bool = True, target: str = "trunk") -> dict[str, Path]:
        subprocess.run(["git", "init", "-q", "-b", target, str(root)], check=True)
        self.git(root, "config", "user.email", "gantry@example.test")
        self.git(root, "config", "user.name", "Gantry Test")
        (root / ".agents" / "skills" / "gantry").mkdir(parents=True)
        scripts = {
            "implement": root / "implement-role.py",
            "review": root / "review-role.py",
            "critic": root / "critic-role.py",
            "check": root / "check-role.py",
        }
        if commands:
            self.write_script(scripts["implement"], """
import subprocess
from pathlib import Path
Path('one.txt').write_text('one\\n')
subprocess.check_call(['git','add','one.txt'])
subprocess.check_call(['git','commit','-qm','one'])
Path('two.txt').write_text('two\\n')
subprocess.check_call(['git','add','two.txt'])
subprocess.check_call(['git','commit','-qm','two'])
""")
            self.write_script(scripts["review"], """
import json, os, sys
from pathlib import Path
Path('review-diff.txt').write_text(sys.stdin.read())
Path('review-base.txt').write_text(os.environ['GANTRY_DIFF_BASE'])
print(json.dumps({'verdict':'pass'}))
""")
            self.write_script(scripts["critic"], """
import json, os, sys
from pathlib import Path
Path('critic-diff.txt').write_text(sys.stdin.read())
Path('critic-base.txt').write_text(os.environ['GANTRY_DIFF_BASE'])
print(json.dumps({'verdict':'pass'}))
""")
            self.write_script(scripts["check"], """
from pathlib import Path
Path('checked.txt').write_text('yes\\n')
""")
        (root / ".gantry").mkdir()
        (root / ".gantry" / "config.json").write_text(json.dumps({
            "git": {"target": target, "prefix": "gantry/", "issueBranch": "{prefix}{spec}-{number:02d}"},
            "checks": [str(scripts["check"])] if commands else [],
            "execution": {"roles": {
                role: {"harness": "claude-code", "model": "fixture-model", "command": str(scripts[role])}
                for role in ("implement", "review", "critic")
            }} if commands else {},
        }), encoding="utf-8")
        issue_dir = root / ".scratch" / "sample" / "issues"
        issue_dir.mkdir(parents=True)
        if spec:
            (root / ".scratch" / "sample" / "spec.md").write_text("# Sample\n", encoding="utf-8")
        (issue_dir / "01-ready.md").write_text("""# Ready work

Type: issue
Status: ready-for-agent
Slice: `sample#01`

## Acceptance criteria

- [ ] Deliver the change.

## Blocked by

None
""", encoding="utf-8")
        (issue_dir / "02-blocked.md").write_text("""# Blocked work

Type: issue
Status: ready-for-agent
Slice: `sample#02`

## Acceptance criteria

- [ ] Wait.

## Blocked by

- `sample#01`
""", encoding="utf-8")
        (root / "README.md").write_text("base\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-qm", "base")
        return scripts

    def execute(self, root: Path, ref: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CLI), "--cwd", str(root), "execute", ref],
                              text=True, capture_output=True, check=False)

    def test_invalid_setup_creates_no_branch_or_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, spec=False)
            before = self.git(root, "branch", "--list").stdout
            result = self.execute(root, "sample#01")
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertEqual("spec-missing", json.loads(result.stdout)["error"]["reason"])
            self.assertEqual(before, self.git(root, "branch", "--list").stdout)
            self.assertFalse((root / ".gantry" / "worktrees").exists())

    def test_open_blocker_creates_no_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            result = self.execute(root, "sample#02")
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertEqual(["sample#01"], json.loads(result.stdout)["error"]["openBlockers"])
            self.assertEqual("", self.git(root, "branch", "--list", "gantry/sample-02").stdout)
            self.assertFalse((root / ".gantry" / "worktrees").exists())

    def test_happy_path_commits_in_the_worktree_and_does_not_push(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.fixture(root, target="trunk")
            self.git(root, "remote", "add", "origin", str(origin))
            result = subprocess.run(
                ["node", str(COMMAND), "execute", "sample#01", "--cwd", str(root)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            events = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual("ready-for-approval", events[-1]["event"])
            self.assertFalse(events[-1]["pushed"])
            worktree = Path(events[-1]["worktree"])
            self.assertEqual("gantry/sample-01", self.git(worktree, "branch", "--show-current").stdout.strip())
            subjects = self.git(worktree, "log", "--format=%s", "trunk..HEAD").stdout.splitlines()
            self.assertEqual(["two", "one"], subjects)
            self.assertIn("one.txt", (worktree / "review-diff.txt").read_text())
            self.assertIn("two.txt", (worktree / "critic-diff.txt").read_text())
            self.assertEqual("trunk", (worktree / "review-base.txt").read_text())
            self.assertEqual("trunk", (worktree / "critic-base.txt").read_text())
            self.assertEqual("yes\n", (worktree / "checked.txt").read_text())
            self.assertNotEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/sample-01").returncode)
            self.assertTrue(scripts["review"].is_file())

    def test_configured_role_command_is_the_one_that_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            replacement = root / "replacement-review.py"
            self.write_script(replacement, """
import json, sys
from pathlib import Path
Path('replacement-ran.txt').write_text(sys.stdin.read())
print(json.dumps({'verdict':'pass'}))
""")
            policy = json.loads((root / ".gantry" / "config.json").read_text())
            policy["execution"]["roles"]["review"]["command"] = str(replacement)
            (root / ".gantry" / "config.json").write_text(json.dumps(policy))
            self.git(root, "add", ".gantry/config.json")
            self.git(root, "commit", "-qm", "replace review command")
            result = self.execute(root, "sample#01")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            worktree = root / ".gantry" / "worktrees" / "gantry-sample-01"
            self.assertTrue((worktree / "replacement-ran.txt").is_file())
            self.assertFalse((worktree / "review-diff.txt").exists())

