#!/usr/bin/env python3
"""Contracts for the tracked git hooks: pre-push refuses non-fast-forward updates,
pre-commit refuses a test-skip commit, both name their rule and path, and both
record hook.denied -- per docs/adr/0005-git-hooks-enforce-git-rules.md."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GANTRY = REPO_ROOT / ".agents" / "skills" / "gantry"
HOOKS_DIR = GANTRY / "hooks" / "git"
RUNLOG = GANTRY / "scripts" / "runlog.py"


def git(*args: str, cwd: Path, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )


class GitHookFixtureMixin:
    def init_repository(self, root: Path, *, initial_branch: str = "main") -> None:
        git("init", "--quiet", f"--initial-branch={initial_branch}", cwd=root)
        git("config", "user.email", "hook@example.test", cwd=root)
        git("config", "user.name", "Hook Test", cwd=root)
        git("config", "core.hooksPath", str(HOOKS_DIR), cwd=root)

    def commit(self, root: Path, name: str, content: str, message: str = "commit") -> None:
        (root / name).write_text(content, encoding="utf-8")
        git("add", name, cwd=root)
        git("commit", "--quiet", "-m", message, cwd=root)

    def unit_id(self, root: Path) -> str:
        return json.loads(
            subprocess.run(
                [sys.executable, str(RUNLOG), "unit-id", "--cwd", str(root), "--json"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )["unitId"]

    def seed_run(self, root: Path, state: Path, run: str = "run-01") -> str:
        unit = self.unit_id(root)
        started = {
            "ts": "2026-09-14T12:00:00Z",
            "run": run,
            "event": "run.started",
            "data": {"repositoryRoot": str(root), "policyHash": "abc123", "tier": "reference", "staleAfterSeconds": 900},
        }
        result = subprocess.run(
            [sys.executable, str(RUNLOG), "append", unit, "--state-root", str(state)],
            cwd=root,
            input=json.dumps(started),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return run

    def assert_single_denial_line(self, result: subprocess.CompletedProcess[str], *expected: str) -> None:
        """The hook prints its denial exactly once, on stderr only -- never duplicated onto stdout."""
        stdout_lines = [line for line in result.stdout.splitlines() if line.startswith("deny:")]
        stderr_lines = [line for line in result.stderr.splitlines() if line.startswith("deny:")]
        self.assertEqual(0, len(stdout_lines), result.stdout)
        self.assertEqual(1, len(stderr_lines), result.stderr)
        for substring in expected:
            self.assertIn(substring, stderr_lines[0])

    def mark_run(self, root: Path, state: Path, run: str) -> None:
        """Mark this worktree as executing `run`, the way the round workflow does before any agent works in it."""
        result = subprocess.run(
            [sys.executable, str(RUNLOG), "mark", run, "--cwd", str(root), "--state-root", str(state)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def env_without_gantry_variables(self) -> dict[str, str]:
        """A child environment carrying no Run ID and no state root -- what a real `git` subprocess inherits."""
        env = {key: value for key, value in os.environ.items() if not key.startswith("GANTRY_")}
        return env

    def denied_events(self, root: Path, state: Path, run: str) -> list[dict]:
        unit = self.unit_id(root)
        log_path = state / unit / "runs" / f"{run}.jsonl"
        events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        return [event for event in events if event["event"] == "hook.denied"]


class PrePushHookTests(GitHookFixtureMixin, unittest.TestCase):
    def make_remote_and_local(self, temp: Path) -> tuple[Path, Path]:
        remote = temp / "remote.git"
        remote.mkdir()
        git("init", "--quiet", "--bare", cwd=remote)
        local = temp / "local"
        local.mkdir()
        self.init_repository(local)
        git("remote", "add", "origin", str(remote), cwd=local)
        return remote, local

    def push(self, local: Path, *args: str, env: dict[str, str] | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
        full_env = dict(os.environ)
        if env:
            full_env.update(env)
        return subprocess.run(
            ["git", "push", *args],
            cwd=local,
            capture_output=True,
            text=True,
            check=check,
            env=full_env,
        )

    def test_accepts_a_fast_forward_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            remote, local = self.make_remote_and_local(Path(temp))
            self.commit(local, "a.txt", "base\n")
            first = self.push(local, "origin", "HEAD:refs/heads/main")
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)

            self.commit(local, "a.txt", "base\nmore\n", "second")
            second = self.push(local, "origin", "HEAD:refs/heads/main")
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)

    def diverge(self, local: Path, marker: str) -> None:
        """Rewrite the current commit's content, producing a new SHA with the same
        parent as before -- a sibling of whatever the remote already has, which is
        exactly what a non-fast-forward update is."""
        (local / "a.txt").write_text(f"base\ndiverged-{marker}\n", encoding="utf-8")
        git("add", "a.txt", cwd=local)
        git("commit", "--quiet", "--amend", "-m", f"diverged-{marker}", cwd=local)

    def test_rejects_non_fast_forward_pushes_spelled_every_which_way(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            remote, local = self.make_remote_and_local(Path(temp))
            self.commit(local, "a.txt", "base\n")
            first = self.push(local, "-u", "origin", "HEAD:refs/heads/main")
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)

            for flags in (["--force"], ["-f"], ["-uf"], ["--force-with-lease"], ["+HEAD:refs/heads/main"]):
                with self.subTest(flags=flags):
                    self.diverge(local, "-".join(flags))
                    if flags[0].startswith("+"):
                        result = self.push(local, "origin", flags[0])
                    else:
                        result = self.push(local, *flags, "origin", "HEAD:refs/heads/main")
                    self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assert_single_denial_line(result, "no-force-push")
                    # Reset local history back to what the remote actually has, so the
                    # next spelling in the matrix starts from a clean fast-forward point.
                    git("reset", "--quiet", "--hard", "origin/main", cwd=local, check=False)

            self.diverge(local, "mirror")
            mirror = self.push(local, "--mirror", "origin")
            self.assertNotEqual(0, mirror.returncode, mirror.stdout + mirror.stderr)
            self.assert_single_denial_line(mirror, "no-force-push")

    def test_denial_appends_hook_denied_naming_rule_and_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            remote, local = self.make_remote_and_local(temp_path)
            state = temp_path / "state"
            run = self.seed_run(local, state)

            self.commit(local, "a.txt", "base\n")
            first = self.push(local, "origin", "HEAD:refs/heads/main", env={"GANTRY_RUN_ID": run, "GANTRY_STATE_ROOT": str(state)})
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)

            (local / "a.txt").write_text("base\ndiverged\n", encoding="utf-8")
            git("add", "a.txt", cwd=local)
            git("commit", "--quiet", "--amend", "-m", "diverged", cwd=local)
            denied = self.push(
                local,
                "--force",
                "origin",
                "HEAD:refs/heads/main",
                env={"GANTRY_RUN_ID": run, "GANTRY_STATE_ROOT": str(state)},
            )
            self.assertNotEqual(0, denied.returncode, denied.stdout + denied.stderr)

            events = self.denied_events(local, state, run)
            self.assertEqual(1, len(events))
            self.assertEqual("no-force-push", events[0]["data"]["rule"])
            self.assertIn("main", events[0]["data"]["path"])

    def test_denial_is_recorded_without_the_caller_exporting_a_run_id(self) -> None:
        """Recording is guaranteed, not best-effort: the hook resolves the Run from the worktree's marker."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            remote, local = self.make_remote_and_local(temp_path)
            state = temp_path / "state"
            run = self.seed_run(local, state)
            self.mark_run(local, state, run)
            env = self.env_without_gantry_variables()

            self.commit(local, "a.txt", "base\n")
            first = self.push(local, "origin", "HEAD:refs/heads/main", env=env)
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)

            (local / "a.txt").write_text("base\ndiverged\n", encoding="utf-8")
            git("add", "a.txt", cwd=local)
            git("commit", "--quiet", "--amend", "-m", "diverged", cwd=local)
            denied = subprocess.run(
                ["git", "push", "--force", "origin", "HEAD:refs/heads/main"],
                cwd=local,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertNotEqual(0, denied.returncode, denied.stdout + denied.stderr)
            self.assert_single_denial_line(denied, "no-force-push")

            events = self.denied_events(local, state, run)
            self.assertEqual(1, len(events))
            self.assertEqual("no-force-push", events[0]["data"]["rule"])


class PreCommitHookTests(GitHookFixtureMixin, unittest.TestCase):
    CLEAN_TEST = "import unittest\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n"
    SKIPPED_TEST = (
        "import unittest\n\nclass T(unittest.TestCase):\n    @unittest.skip('later')\n    def test_x(self):\n        pass\n"
    )

    def test_accepts_a_clean_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            self.commit(root, "app_test.py", self.CLEAN_TEST)
            # commit() already asserts nothing; a raised CalledProcessError would fail the test.

    def test_rejects_a_skip_committed_via_dash_a(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            result = git("commit", "-am", "skip", cwd=root, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assert_single_denial_line(result, "no-test-skip-commit", "app_test.py")

    def test_rejects_a_skip_committed_via_pathspec(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            result = git("commit", "-m", "skip", "--", "app_test.py", cwd=root, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assert_single_denial_line(result, "no-test-skip-commit")

    def test_rejects_a_skip_committed_via_include(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            result = git("commit", "-m", "skip", "--include", "app_test.py", cwd=root, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assert_single_denial_line(result, "no-test-skip-commit")

    def test_rejects_a_skip_committed_via_dash_i(self) -> None:
        """AC4 names `-i` literally, alongside the `--include` spelling above."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            result = git("commit", "-m", "skip", "-i", "app_test.py", cwd=root, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assert_single_denial_line(result, "no-test-skip-commit")

    def test_rejects_a_skip_committed_via_git_stage_then_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repository(root)
            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            git("stage", "app_test.py", cwd=root)
            result = git("commit", "-m", "skip", cwd=root, check=False)
            self.assertNotEqual(0, result.returncode)
            self.assert_single_denial_line(result, "no-test-skip-commit")

    def test_denial_appends_hook_denied_naming_rule_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            root = temp_path / "repo"
            root.mkdir()
            self.init_repository(root)
            state = temp_path / "state"
            run = self.seed_run(root, state)

            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            git("add", "app_test.py", cwd=root)
            env = dict(os.environ)
            env["GANTRY_RUN_ID"] = run
            env["GANTRY_STATE_ROOT"] = str(state)
            result = git("commit", "-m", "skip", cwd=root, check=False, env=env)
            self.assertNotEqual(0, result.returncode)

            events = self.denied_events(root, state, run)
            self.assertEqual(1, len(events))
            self.assertEqual("no-test-skip-commit", events[0]["data"]["rule"])
            self.assertEqual("app_test.py", events[0]["data"]["path"])

    def test_denial_is_recorded_without_the_caller_exporting_a_run_id(self) -> None:
        """Recording is guaranteed, not best-effort: the hook resolves the Run from the worktree's marker."""
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            root = temp_path / "repo"
            root.mkdir()
            self.init_repository(root)
            state = temp_path / "state"
            run = self.seed_run(root, state)
            self.mark_run(root, state, run)
            env = self.env_without_gantry_variables()

            self.commit(root, "app_test.py", self.CLEAN_TEST)
            (root / "app_test.py").write_text(self.SKIPPED_TEST, encoding="utf-8")
            git("add", "app_test.py", cwd=root, env=env)
            result = git("commit", "-m", "skip", cwd=root, check=False, env=env)
            self.assertNotEqual(0, result.returncode)
            self.assert_single_denial_line(result, "no-test-skip-commit", "app_test.py")

            events = self.denied_events(root, state, run)
            self.assertEqual(1, len(events))
            self.assertEqual("no-test-skip-commit", events[0]["data"]["rule"])
            self.assertEqual("app_test.py", events[0]["data"]["path"])


if __name__ == "__main__":
    unittest.main()
