#!/usr/bin/env python3
"""Public-contract tests for initial context budget estimation."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
BUDGET = SKILL_DIR / "scripts" / "budget.py"
CAPABILITIES = SKILL_DIR / "capabilities"


class ContextBudgetTests(unittest.TestCase):
    def write_issue(self, root: Path, body: str) -> Path:
        issue = root / ".scratch" / "sample" / "issues" / "01-budget.md"
        issue.parent.mkdir(parents=True)
        (root / ".scratch" / "sample" / "spec.md").write_text(
            "# Sample Spec\n",
            encoding="utf-8",
        )
        issue.write_text(
            f"""# Context budget

Type: issue
Status: draft
Slice: `sample#01`
Spec: `.scratch/sample/spec.md`

## What to build

{body}

## Acceptance criteria

- [ ] exposes the context budget

## Blocked by

- None
""",
            encoding="utf-8",
        )
        return issue

    def run_budget(self, root: Path, issue: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUDGET), str(issue), "--model", "claude-opus-4-5", "--json", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_estimate_includes_only_the_canonical_files_to_read_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            named = root / "src" / "named.txt"
            named.parent.mkdir()
            named.write_bytes(b"n" * 20)
            ignored = {
                "src/code-span-in-prose.txt",
                "src/list-prose.txt",
                "src/wrong-heading.txt",
                "src/case-variant-heading.txt",
                "src/incidental.txt",
            }
            for path in ignored:
                target = root / path
                target.write_bytes(b"x" * 100_000)
            issue = self.write_issue(
                root,
                """### Related files

- `src/wrong-heading.txt`

### Files To Read

- `src/case-variant-heading.txt`

### Files to read

- `src/named.txt`
- Read `src/list-prose.txt` before implementation.

The incidental code span `src/code-span-in-prose.txt` is not a file declaration.
Do not read `src/incidental.txt`; it is only an example.""",
            )

            result = self.run_budget(root, issue)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            paths = [entry["path"] for entry in payload["files"]]
            self.assertEqual(
                [
                    ".scratch/sample/issues/01-budget.md",
                    ".scratch/sample/spec.md",
                    "src/named.txt",
                ],
                paths,
            )
            expected_bytes = sum((root / path).stat().st_size for path in paths)
            self.assertEqual(expected_bytes, payload["bytes"])
            self.assertEqual(expected_bytes / 4, payload["estimatedTokens"])
            self.assertTrue(set(ignored).isdisjoint(paths))

    def test_policy_context_share_overrides_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            config = root / ".gantry" / "config.json"
            config.parent.mkdir()
            config.write_text('{"budget":{"contextShare":0.01}}', encoding="utf-8")
            issue = self.write_issue(root, "No additional files are required.")

            result = self.run_budget(root, issue)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(0.01, payload["contextShare"])
            self.assertEqual(payload["contextWindow"] * 0.01, payload["budgetTokens"])

    def test_capabilities_declare_known_positive_model_windows(self) -> None:
        required = {
            "tier",
            "hooks",
            "structured_output",
            "worktree_isolation",
            "per_role_model",
            "parallel_round",
            "skills_path",
            "hook_events",
            "payload_fields",
            "models",
        }
        for capability in sorted(CAPABILITIES.glob("*.json")):
            with self.subTest(capability=capability.name):
                payload = json.loads(capability.read_text(encoding="utf-8"))
                self.assertTrue(required.issubset(payload))
                self.assertTrue(payload["models"])
                self.assertFalse(
                    payload["parallel_round"] and not payload["worktree_isolation"],
                    "parallel rounds require isolated worktrees",
                )
                for model, values in payload["models"].items():
                    self.assertIsInstance(model, str)
                    self.assertEqual({"contextWindow"}, set(values))
                    self.assertIsInstance(values["contextWindow"], int)
                    self.assertGreater(values["contextWindow"], 0)

    def test_every_declared_model_window_matches_real_budget_execution(self) -> None:
        issue = REPO_ROOT / ".scratch" / "gantry-migration" / "issues" / "05-context-budget-and-capabilities.md"
        for capability in sorted(CAPABILITIES.glob("*.json")):
            declaration = json.loads(capability.read_text(encoding="utf-8"))
            for model, values in declaration["models"].items():
                with self.subTest(capability=capability.name, model=model):
                    result = subprocess.run(
                        [sys.executable, str(BUDGET), str(issue), "--model", model, "--json"],
                        cwd=REPO_ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(0, result.returncode, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(values["contextWindow"], payload["contextWindow"])

    def test_unknown_model_is_a_fail_closed_configuration_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            issue = self.write_issue(root, "No additional files are required.")

            result = subprocess.run(
                [sys.executable, str(BUDGET), str(issue), "--model", "unknown-model", "--json"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(1, result.returncode)
            payload = json.loads(result.stdout)
            self.assertIn("configuration error", payload["error"])
            self.assertNotIn("contextWindow", payload)

    def test_large_package_completes_under_one_second_and_refutes_over_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            named = root / "src" / "large.txt"
            named.parent.mkdir()
            named.write_bytes(b"x" * 200_000)
            issue = self.write_issue(
                root,
                """### Files to read

- `src/large.txt`""",
            )

            started = time.monotonic()
            result = self.run_budget(root, issue)
            elapsed = time.monotonic() - started

            self.assertLess(elapsed, 1)
            self.assertEqual(1, result.returncode)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["overBudget"])
            self.assertEqual("over_budget", payload["verdict"])
            self.assertGreater(payload["estimatedTokens"], payload["budgetTokens"])


if __name__ == "__main__":
    unittest.main()
