"""Public process tests for the Gantry board command."""
from __future__ import annotations

import json
import os
import signal
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


class GantryCliCorrectionsPlanAndApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.execute_case = GantryCliExecuteTests()

    def write_script(self, path: Path, body: str) -> None:
        self.execute_case.write_script(path, body)

    def git(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return self.execute_case.git(root, *args)

    def invoke(self, root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), "--cwd", str(root), *args],
            text=True, capture_output=True, check=False, input=stdin,
        )

    def events(self, result: subprocess.CompletedProcess[str]) -> list[dict]:
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]

    def set_budget(self, root: Path, corrections: int) -> None:
        policy = json.loads((root / ".gantry" / "config.json").read_text())
        policy["budget"] = {"corrections": corrections}
        (root / ".gantry" / "config.json").write_text(json.dumps(policy))

    def quiet_check(self, path: Path) -> None:
        self.write_script(path, "raise SystemExit(0)\n")

    def idempotent_implement(self, path: Path) -> None:
        self.write_script(path, """
import subprocess
from pathlib import Path
if not Path('one.txt').exists():
    Path('one.txt').write_text('one\\n')
    subprocess.check_call(['git','add','one.txt'])
    subprocess.check_call(['git','commit','-qm','one'])
""")

    def test_failed_check_and_dirty_tree_spend_corrections_without_the_next_role(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = self.execute_case.fixture(root)
            self.set_budget(root, 2)
            check_count = root / "check.count"
            review_count = root / "review.count"
            self.write_script(scripts["check"], f"""
import sys
from pathlib import Path
count = Path({str(check_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
sys.exit(1 if seen == 0 else 0)
""")
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
Path({str(review_count)!r}).write_text('ran')
print(json.dumps({{'verdict': 'pass'}}))
""")
            self.idempotent_implement(scripts["implement"])
            checked = self.invoke(root, "execute", "sample#01")
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            self.assertEqual("2", check_count.read_text())
            self.assertEqual("ran", review_count.read_text())
            self.assertEqual("ready-for-approval", self.events(checked)[-1]["event"])

            root = Path(directory) / "dirty"
            root.mkdir()
            scripts = self.execute_case.fixture(root)
            self.set_budget(root, 2)
            implement_count = root / "implement.count"
            review_count = root / "review.count"
            self.write_script(scripts["implement"], f"""
import subprocess
from pathlib import Path
count = Path({str(implement_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
if seen == 0:
    Path('dirty.txt').write_text('dirty\\n')
else:
    Path('dirty.txt').unlink(missing_ok=True)
    Path('one.txt').write_text('one\\n')
    subprocess.check_call(['git','add','one.txt'])
    subprocess.check_call(['git','commit','-qm','one'])
""")
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
Path({str(review_count)!r}).write_text('ran')
print(json.dumps({{'verdict': 'pass'}}))
""")
            dirty = self.invoke(root, "execute", "sample#01")
            self.assertEqual(0, dirty.returncode, dirty.stdout + dirty.stderr)
            self.assertEqual("2", implement_count.read_text())
            self.assertEqual("ran", review_count.read_text())
            self.assertNotIn("corrections-exhausted", dirty.stdout)

    def test_review_fail_skips_critic_and_critic_fail_repeats_both(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = self.execute_case.fixture(root)
            self.set_budget(root, 2)
            self.idempotent_implement(scripts["implement"])
            self.quiet_check(scripts["check"])
            review_count = root / "review.count"
            critic_count = root / "critic.count"
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'fail' if seen == 0 else 'pass'}}))
""")
            self.write_script(scripts["critic"], f"""
import json
from pathlib import Path
count = Path({str(critic_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'pass'}}))
""")
            review = self.invoke(root, "execute", "sample#01")
            self.assertEqual(0, review.returncode, review.stdout + review.stderr)
            self.assertEqual("2", review_count.read_text())
            self.assertEqual("1", critic_count.read_text())

            root = Path(directory) / "critic"
            root.mkdir()
            scripts = self.execute_case.fixture(root)
            self.set_budget(root, 2)
            self.idempotent_implement(scripts["implement"])
            self.quiet_check(scripts["check"])
            review_count = root / "review.count"
            critic_count = root / "critic.count"
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'pass'}}))
""")
            self.write_script(scripts["critic"], f"""
import json
from pathlib import Path
count = Path({str(critic_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'fail' if seen == 0 else 'pass'}}))
""")
            critic = self.invoke(root, "execute", "sample#01")
            self.assertEqual(0, critic.returncode, critic.stdout + critic.stderr)
            self.assertEqual("2", review_count.read_text())
            self.assertEqual("2", critic_count.read_text())

    def test_zero_budget_pauses_for_continue_or_stop_and_keeps_the_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "stop"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.execute_case.fixture(root)
            self.git(root, "remote", "add", "origin", str(origin))
            self.set_budget(root, 0)
            self.write_script(scripts["review"], """
import json
print(json.dumps({'verdict': 'fail'}))
""")
            stopped = self.invoke(root, "execute", "sample#01", stdin="stop\n")
            self.assertEqual(1, stopped.returncode, stopped.stdout + stopped.stderr)
            pause = self.events(stopped)[-2]
            self.assertEqual("corrections-exhausted", pause["reason"])
            self.assertEqual(["continue", "stop"], pause["choices"])
            self.assertFalse(pause["pushed"])
            self.assertEqual("stopped", self.events(stopped)[-1]["event"])
            worktree = Path(pause["worktree"])
            self.assertTrue(worktree.is_dir())
            self.assertNotEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/sample-01").returncode)

            root = Path(directory) / "continue"
            root.mkdir()
            scripts = self.execute_case.fixture(root)
            self.set_budget(root, 0)
            self.idempotent_implement(scripts["implement"])
            self.quiet_check(scripts["check"])
            review_count = root / "review.count"
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'fail' if seen == 0 else 'pass'}}))
""")
            continued = self.invoke(root, "execute", "sample#01", stdin="continue\n")
            self.assertEqual(0, continued.returncode, continued.stdout + continued.stderr)
            self.assertEqual("ready-for-approval", self.events(continued)[-1]["event"])
            self.assertFalse(self.events(continued)[-1]["pushed"])
            self.assertEqual("2", review_count.read_text())

    def test_plan_reserves_the_branch_and_rejection_or_retry_does_not_spend_a_correction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "reject"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.execute_case.fixture(root)
            self.git(root, "remote", "add", "origin", str(origin))
            plan = root / "plan-role.py"
            calls = root / "plan.count"
            self.write_script(plan, f"""
import os, subprocess
from pathlib import Path
count = Path({str(calls)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
Path({str(root / 'plan-branch.txt')!r}).write_text(subprocess.check_output(['git','branch','--show-current'], text=True))
spec = Path(os.environ['GANTRY_SPEC_PATH'])
issue = Path(os.environ['GANTRY_ISSUE_PATH'])
spec.parent.mkdir(parents=True, exist_ok=True)
issue.parent.mkdir(parents=True, exist_ok=True)
spec.write_text('# Fresh\\n')
issue.write_text('# Planned\\n\\nType: issue\\nStatus: ready-for-agent\\nSlice: `fresh#01`\\n\\n## Acceptance criteria\\n\\n- [ ] Ship it.\\n\\n## Blocked by\\n\\nNone\\n')
subprocess.check_call(['git','add', spec.as_posix(), issue.as_posix()])
subprocess.check_call(['git','commit','-qm','plan'])
""")
            policy = json.loads((root / ".gantry" / "config.json").read_text())
            policy["execution"]["roles"]["plan"] = {"harness": "claude-code", "model": "fixture", "command": str(plan)}
            policy["budget"] = {"corrections": 0}
            (root / ".gantry" / "config.json").write_text(json.dumps(policy))
            rejected = self.invoke(root, "execute", "fresh", stdin="reject\n")
            self.assertEqual(1, rejected.returncode, rejected.stdout + rejected.stderr)
            self.assertEqual("plan-approval", self.events(rejected)[-2]["reason"])
            self.assertEqual("rejected", self.events(rejected)[-1]["event"])
            self.assertEqual("gantry/fresh-01\n", (root / "plan-branch.txt").read_text())
            self.assertFalse((root / ".gantry" / "worktrees" / "gantry-fresh-01").exists())
            self.assertEqual("", self.git(root, "branch", "--list", "gantry/fresh-01").stdout)
            self.assertNotEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/fresh-01").returncode)
            self.assertNotIn("corrections-exhausted", rejected.stdout)

            root = Path(directory) / "retry"
            root.mkdir()
            scripts = self.execute_case.fixture(root)
            plan = root / "plan-role.py"
            calls = root / "plan.count"
            self.write_script(plan, f"""
import os, subprocess, sys
from pathlib import Path
count = Path({str(calls)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
dirty = Path('dirty.txt')
if seen < 2:
    dirty.write_text('still dirty\\n')
    raise SystemExit(0)
dirty.unlink(missing_ok=True)
spec = Path(os.environ['GANTRY_SPEC_PATH'])
issue = Path(os.environ['GANTRY_ISSUE_PATH'])
spec.parent.mkdir(parents=True, exist_ok=True)
issue.parent.mkdir(parents=True, exist_ok=True)
spec.write_text('# Fresh\\n')
issue.write_text('# Planned\\n\\nType: issue\\nStatus: ready-for-agent\\nSlice: `fresh#01`\\n\\n## Acceptance criteria\\n\\n- [ ] Ship it.\\n\\n## Blocked by\\n\\nNone\\n')
subprocess.check_call(['git','add','-A'])
subprocess.check_call(['git','commit','-qm','plan'])
""")
            policy = json.loads((root / ".gantry" / "config.json").read_text())
            policy["execution"]["roles"]["plan"] = {"harness": "claude-code", "model": "fixture", "command": str(plan)}
            policy["budget"] = {"corrections": 0}
            (root / ".gantry" / "config.json").write_text(json.dumps(policy))
            retried = self.invoke(root, "execute", "fresh", stdin="try-again\napprove\n")
            self.assertEqual(0, retried.returncode, retried.stdout + retried.stderr)
            reasons = [event.get("reason") for event in self.events(retried)]
            self.assertEqual(["plan-dirty", "plan-approval"], [reason for reason in reasons if reason])
            self.assertNotIn("corrections-exhausted", retried.stdout)
            self.assertEqual("3", calls.read_text())
            worktree = Path(self.events(retried)[-1]["worktree"])
            self.assertEqual("gantry/fresh-01", self.git(worktree, "branch", "--show-current").stdout.strip())
            self.assertTrue((worktree / ".scratch" / "fresh" / "spec.md").is_file())
            self.assertTrue((worktree / ".scratch" / "fresh" / "issues" / "01-fresh.md").is_file())

    def test_approval_commits_done_state_on_the_branch_and_a_repeat_only_opens_the_pr(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.execute_case.fixture(root, target="trunk")
            self.quiet_check(scripts["check"])
            self.write_script(scripts["review"], "import json\nprint(json.dumps({'verdict':'pass'}))\n")
            self.write_script(scripts["critic"], "import json\nprint(json.dumps({'verdict':'pass'}))\n")
            roadmap = root / "ROADMAP.md"
            roadmap.write_text("""# Roadmap

| Metric | Value |
|---|---|
| Issues completed | **0 / 0** |
| Specs completed | **0 / 0** |
| Execution waves | **0** |

<!-- BEGIN GENERATED: spec progress -->

<!-- END GENERATED: spec progress -->

<!-- BEGIN GENERATED: issue checklist -->

<!-- END GENERATED: issue checklist -->
""", encoding="utf-8")
            self.git(root, "add", "ROADMAP.md")
            self.git(root, "commit", "-qm", "roadmap")
            self.git(root, "remote", "add", "origin", str(origin))
            self.git(root, "push", "-q", "origin", "trunk")
            gh_log = root / "gh.log"
            gh = root / "gh"
            self.write_script(gh, f"""
import json, sys
from pathlib import Path
Path({str(gh_log)!r}).write_text(Path({str(gh_log)!r}).read_text() + json.dumps(sys.argv) + '\\n' if Path({str(gh_log)!r}).exists() else json.dumps(sys.argv) + '\\n')
print('https://example.test/pr/1')
""")
            prepared = self.invoke(root, "execute", "sample#01")
            self.assertEqual(0, prepared.returncode, prepared.stdout + prepared.stderr)
            self.assertFalse(self.events(prepared)[-1]["pushed"])
            self.assertNotEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/sample-01").returncode)
            target_before = self.git(origin, "rev-parse", "trunk").stdout.strip()
            worktree = Path(self.events(prepared)[-1]["worktree"])
            before = self.git(worktree, "rev-parse", "HEAD").stdout.strip()
            env = os.environ.copy()
            env["PATH"] = f"{root}{os.pathsep}{env.get('PATH', '')}"
            approved = subprocess.run(
                ["node", str(COMMAND), "approve", "sample#01", "--cwd", str(root)],
                text=True, capture_output=True, check=False, env=env,
            )
            self.assertEqual(0, approved.returncode, approved.stdout + approved.stderr)
            event = json.loads(approved.stdout.strip().splitlines()[-1])
            self.assertEqual("pull-request", event["event"])
            self.assertTrue(event["pushed"])
            self.assertTrue(event["createdCommit"])
            self.assertEqual("trunk", event["target"])
            self.assertEqual("gantry: close sample#01", self.git(worktree, "log", "-1", "--format=%s").stdout.strip())
            self.assertEqual(before, self.git(worktree, "rev-parse", "HEAD^").stdout.strip())
            self.assertIn("Status: done", (worktree / ".scratch" / "sample" / "issues" / "01-ready.md").read_text())
            self.assertIn("[x]", (worktree / "ROADMAP.md").read_text())
            self.assertIn("Status: ready-for-agent", (root / ".scratch" / "sample" / "issues" / "01-ready.md").read_text())
            self.assertEqual(target_before, self.git(origin, "rev-parse", "trunk").stdout.strip())
            self.assertEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/sample-01").returncode)
            closed = self.git(worktree, "rev-parse", "HEAD").stdout.strip()
            repeated = subprocess.run(
                ["node", str(COMMAND), "approve", "sample#01", "--cwd", str(root)],
                text=True, capture_output=True, check=False, env=env,
            )
            self.assertEqual(0, repeated.returncode, repeated.stdout + repeated.stderr)
            self.assertEqual(closed, self.git(worktree, "rev-parse", "HEAD").stdout.strip())
            self.assertFalse(json.loads(repeated.stdout.strip().splitlines()[-1])["createdCommit"])
            self.assertEqual(2, len(gh_log.read_text().splitlines()))
            self.assertEqual(target_before, self.git(origin, "rev-parse", "trunk").stdout.strip())


class GantryCliInterruptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = GantryCliCorrectionsPlanAndApprovalTests()
        self.case.setUp()

    def write_script(self, path: Path, body: str) -> None:
        self.case.write_script(path, body)

    def git(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return self.case.git(root, *args)

    def invoke(self, root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return self.case.invoke(root, *args, stdin=stdin)

    def events(self, result: subprocess.CompletedProcess[str]) -> list[dict]:
        return self.case.events(result)

    def failing_review(self, root: Path, scripts: dict[str, Path]) -> Path:
        count = root / "implement.count"
        self.write_script(scripts["implement"], f"""
import subprocess
from pathlib import Path
count = Path({str(count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
if not Path('one.txt').exists():
    Path('one.txt').write_text('one\\n')
    subprocess.check_call(['git','add','one.txt'])
    subprocess.check_call(['git','commit','-qm','one'])
""")
        self.case.quiet_check(scripts["check"])
        self.write_script(scripts["review"], """
import json
print(json.dumps({'verdict': 'fail'}))
""")
        return count

    def test_stop_keeps_the_worktree_branch_and_local_commits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.case.execute_case.fixture(root)
            self.git(root, "remote", "add", "origin", str(origin))
            self.case.set_budget(root, 0)
            self.failing_review(root, scripts)
            stopped = self.invoke(root, "execute", "sample#01", stdin="stop\n")
            self.assertEqual(1, stopped.returncode, stopped.stdout + stopped.stderr)
            self.assertEqual("stopped", self.events(stopped)[-1]["event"])
            worktree = Path(self.events(stopped)[-1]["worktree"])
            self.assertTrue(worktree.is_dir())
            self.assertEqual("gantry/sample-01", self.git(worktree, "branch", "--show-current").stdout.strip())
            self.assertEqual(["one"], self.git(worktree, "log", "--format=%s", "trunk..HEAD").stdout.splitlines())
            self.assertNotEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/sample-01").returncode)

    def test_resume_at_zero_budget_reopens_the_pause_without_calling_implement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "pause"
            root.mkdir()
            scripts = self.case.execute_case.fixture(root)
            self.case.set_budget(root, 0)
            count = self.failing_review(root, scripts)
            stopped = self.invoke(root, "execute", "sample#01", stdin="stop\n")
            self.assertEqual(1, stopped.returncode, stopped.stdout + stopped.stderr)
            self.assertEqual("1", count.read_text())
            resumed = self.invoke(root, "resume", "sample#01", stdin="stop\n")
            self.assertEqual(1, resumed.returncode, resumed.stdout + resumed.stderr)
            self.assertEqual("corrections-exhausted", self.events(resumed)[0]["reason"])
            self.assertEqual(["continue", "stop"], self.events(resumed)[0]["choices"])
            self.assertEqual(self.events(stopped)[-1]["worktree"], self.events(resumed)[0]["worktree"])
            self.assertEqual("stopped", self.events(resumed)[-1]["event"])
            self.assertEqual("1", count.read_text())

            root = Path(directory) / "continue"
            root.mkdir()
            scripts = self.case.execute_case.fixture(root)
            self.case.set_budget(root, 0)
            count = root / "implement.count"
            self.write_script(scripts["implement"], f"""
import subprocess
from pathlib import Path
count = Path({str(count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
if not Path('one.txt').exists():
    Path('one.txt').write_text('one\\n')
    subprocess.check_call(['git','add','one.txt'])
    subprocess.check_call(['git','commit','-qm','one'])
""")
            self.case.quiet_check(scripts["check"])
            review_count = root / "review.count"
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'fail' if seen == 0 else 'pass'}}))
""")
            stopped = self.invoke(root, "execute", "sample#01", stdin="stop\n")
            self.assertEqual("1", count.read_text())
            continued = self.invoke(root, "resume", "sample#01", stdin="continue\n")
            self.assertEqual(0, continued.returncode, continued.stdout + continued.stderr)
            self.assertEqual("corrections-exhausted", self.events(continued)[0]["reason"])
            self.assertEqual("ready-for-approval", self.events(continued)[-1]["event"])
            self.assertFalse(self.events(continued)[-1]["pushed"])
            self.assertEqual("2", count.read_text())
            self.assertEqual(self.events(stopped)[-1]["worktree"], self.events(continued)[-1]["worktree"])

    def test_resume_continues_the_unfinished_role_with_the_remaining_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = self.case.execute_case.fixture(root)
            self.case.set_budget(root, 2)
            implement_count = root / "implement.count"
            review_count = root / "review.count"
            critic_count = root / "critic.count"
            check_count = root / "check.count"
            self.write_script(scripts["check"], f"""
from pathlib import Path
count = Path({str(check_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
if seen:
    raise SystemExit(1)
""")
            self.write_script(scripts["implement"], f"""
import subprocess
from pathlib import Path
count = Path({str(implement_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
if not Path('one.txt').exists():
    Path('one.txt').write_text('one\\n')
    subprocess.check_call(['git','add','one.txt'])
    subprocess.check_call(['git','commit','-qm','one'])
""")
            self.write_script(scripts["review"], f"""
import os, signal
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
os.kill(os.getppid(), signal.SIGTERM)
raise SystemExit(1)
""")
            self.write_script(scripts["critic"], f"""
import json
from pathlib import Path
Path({str(critic_count)!r}).write_text('1')
print(json.dumps({{'verdict': 'pass'}}))
""")
            interrupted = self.invoke(root, "execute", "sample#01")
            self.assertNotEqual(0, interrupted.returncode)
            self.assertEqual("1", implement_count.read_text())
            self.assertEqual("1", review_count.read_text())
            self.assertFalse(critic_count.exists())
            worktree = root / ".gantry" / "worktrees" / "gantry-sample-01"
            self.assertTrue(worktree.is_dir())
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'pass'}}))
""")
            resumed = self.invoke(root, "resume", "sample#01")
            self.assertEqual(0, resumed.returncode, resumed.stdout + resumed.stderr)
            self.assertEqual("1", implement_count.read_text())
            self.assertEqual("1", check_count.read_text())
            self.assertEqual("2", review_count.read_text())
            self.assertEqual("1", critic_count.read_text())
            self.assertEqual("ready-for-approval", self.events(resumed)[-1]["event"])
            self.assertEqual(str(worktree), self.events(resumed)[-1]["worktree"])
            self.assertEqual("", self.git(root, "branch", "--list", "gantry/sample-02").stdout)

    def test_resume_does_not_redo_plan_or_reserve_another_number(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.case.execute_case.fixture(root)
            plan = root / "plan-role.py"
            calls = root / "plan.count"
            self.write_script(plan, f"""
import os, subprocess
from pathlib import Path
count = Path({str(calls)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
spec = Path(os.environ['GANTRY_SPEC_PATH'])
issue = Path(os.environ['GANTRY_ISSUE_PATH'])
spec.parent.mkdir(parents=True, exist_ok=True)
issue.parent.mkdir(parents=True, exist_ok=True)
spec.write_text('# Fresh\\n')
issue.write_text('# Planned\\n\\nType: issue\\nStatus: ready-for-agent\\nSlice: `fresh#01`\\n\\n## Acceptance criteria\\n\\n- [ ] Ship it.\\n\\n## Blocked by\\n\\nNone\\n')
subprocess.check_call(['git','add', spec.as_posix(), issue.as_posix()])
subprocess.check_call(['git','commit','-qm','plan'])
""")
            policy = json.loads((root / ".gantry" / "config.json").read_text())
            policy["execution"]["roles"]["plan"] = {"harness": "claude-code", "model": "fixture", "command": str(plan)}
            (root / ".gantry" / "config.json").write_text(json.dumps(policy))
            proc = subprocess.Popen(
                [sys.executable, str(CLI), "--cwd", str(root), "execute", "fresh"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                assert proc.stdout is not None
                for line in proc.stdout:
                    if "plan-approval" in line:
                        break
                proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
            finally:
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    if stream:
                        stream.close()
            self.assertEqual("1", calls.read_text())
            worktree = root / ".gantry" / "worktrees" / "gantry-fresh-01"
            self.assertTrue((worktree / ".scratch" / "fresh" / "spec.md").is_file())
            self.assertTrue((worktree / ".scratch" / "fresh" / "issues" / "01-fresh.md").is_file())
            resumed = self.invoke(root, "resume", "fresh#01", stdin="approve\n")
            self.assertEqual(0, resumed.returncode, resumed.stdout + resumed.stderr)
            self.assertEqual("1", calls.read_text())
            self.assertEqual("plan-approval", self.events(resumed)[0]["reason"])
            self.assertEqual("ready-for-approval", self.events(resumed)[-1]["event"])
            self.assertEqual("gantry/fresh-01", self.git(worktree, "branch", "--show-current").stdout.strip())
            self.assertEqual("", self.git(root, "branch", "--list", "gantry/fresh-02").stdout)
            self.assertFalse((worktree / ".scratch" / "fresh" / "issues" / "02-fresh.md").exists())

    def test_discard_deletes_the_local_worktree_and_branch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.case.execute_case.fixture(root)
            self.git(root, "remote", "add", "origin", str(origin))
            self.case.set_budget(root, 0)
            self.failing_review(root, scripts)
            stopped = self.invoke(root, "execute", "sample#01", stdin="stop\n")
            worktree = Path(self.events(stopped)[-1]["worktree"])
            self.assertTrue(worktree.is_dir())
            discarded = self.invoke(root, "discard", "sample#01")
            self.assertEqual(0, discarded.returncode, discarded.stdout + discarded.stderr)
            self.assertEqual("discarded", self.events(discarded)[-1]["event"])
            self.assertFalse(self.events(discarded)[-1]["pushed"])
            self.assertFalse(worktree.exists())
            self.assertEqual("", self.git(root, "branch", "--list", "gantry/sample-01").stdout)
            self.assertNotEqual(0, self.git(origin, "rev-parse", "--verify", "gantry/sample-01").returncode)
            missing = self.invoke(root, "resume", "sample#01")
            self.assertNotEqual(0, missing.returncode)
            self.assertEqual("run-missing", json.loads(missing.stdout)["error"]["reason"])

    def test_resume_of_a_ready_run_does_not_call_an_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            origin = Path(directory) / "origin.git"
            root.mkdir()
            subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
            scripts = self.case.execute_case.fixture(root, target="trunk")
            self.case.quiet_check(scripts["check"])
            implement_count = root / "implement.count"
            review_count = root / "review.count"
            critic_count = root / "critic.count"
            self.write_script(scripts["implement"], f"""
import subprocess
from pathlib import Path
count = Path({str(implement_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
if not Path('one.txt').exists():
    Path('one.txt').write_text('one\\n')
    subprocess.check_call(['git','add','one.txt'])
    subprocess.check_call(['git','commit','-qm','one'])
""")
            self.write_script(scripts["review"], f"""
import json
from pathlib import Path
count = Path({str(review_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'pass'}}))
""")
            self.write_script(scripts["critic"], f"""
import json
from pathlib import Path
count = Path({str(critic_count)!r})
seen = int(count.read_text()) if count.exists() else 0
count.write_text(str(seen + 1))
print(json.dumps({{'verdict': 'pass'}}))
""")
            roadmap = root / "ROADMAP.md"
            roadmap.write_text("""# Roadmap

| Metric | Value |
|---|---|
| Issues completed | **0 / 0** |
| Specs completed | **0 / 0** |
| Execution waves | **0** |

<!-- BEGIN GENERATED: spec progress -->

<!-- END GENERATED: spec progress -->

<!-- BEGIN GENERATED: issue checklist -->

<!-- END GENERATED: issue checklist -->
""", encoding="utf-8")
            self.git(root, "add", "ROADMAP.md")
            self.git(root, "commit", "-qm", "roadmap")
            self.git(root, "remote", "add", "origin", str(origin))
            self.git(root, "push", "-q", "origin", "trunk")
            gh = root / "gh"
            self.write_script(gh, """
print('https://example.test/pr/1')
""")
            prepared = self.invoke(root, "execute", "sample#01")
            self.assertEqual(0, prepared.returncode, prepared.stdout + prepared.stderr)
            resumed = subprocess.run(
                ["node", str(COMMAND), "resume", "sample#01", "--cwd", str(root)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, resumed.returncode, resumed.stdout + resumed.stderr)
            self.assertNotIn("Unknown command", resumed.stderr)
            self.assertEqual("ready-for-approval", self.events(resumed)[-1]["event"])
            self.assertFalse(self.events(resumed)[-1]["pushed"])
            self.assertEqual("1", implement_count.read_text())
            self.assertEqual("1", review_count.read_text())
            self.assertEqual("1", critic_count.read_text())
            env = os.environ.copy()
            env["PATH"] = f"{root}{os.pathsep}{env.get('PATH', '')}"
            approved = subprocess.run(
                ["node", str(COMMAND), "approve", "sample#01", "--cwd", str(root)],
                text=True, capture_output=True, check=False, env=env,
            )
            self.assertEqual(0, approved.returncode, approved.stdout + approved.stderr)
            self.assertEqual("pull-request", json.loads(approved.stdout.strip().splitlines()[-1])["event"])
            self.assertEqual("1", implement_count.read_text())

