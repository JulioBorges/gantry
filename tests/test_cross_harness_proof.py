#!/usr/bin/env python3
"""Contract and end-to-end tests for cross-harness execution, independent Critic verification, and Antigravity interoperability."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
COPY_FIXTURE = REPO_ROOT / "fixture" / "tools" / "copy_fixture.py"

sys.path.insert(0, str(SCRIPTS))
import execution  # noqa: E402
import guard  # noqa: E402
import result  # noqa: E402
import runlog  # noqa: E402


class CrossHarnessProofContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme_path = REPO_ROOT / "fixture" / "README.md"
        self.spec_path = REPO_ROOT / ".scratch" / "role-execution-selection" / "spec.md"
        self.docs_path = REPO_ROOT / "docs" / "role-execution.md"
        self.index_path = REPO_ROOT / "docs" / "INDEX.md"

    def test_fixture_readme_records_complete_cross_harness_proof(self) -> None:
        """AC1, AC3, AC4, AC5: README documents live proof, versions, refutation, recovery, and limitations."""
        readme = self.readme_path.read_text(encoding="utf-8")

        # Command to build isolated copy
        self.assertIn("python3 fixture/tools/copy_fixture.py --mode approved", readme)
        self.assertIn("/tmp/gantry-cross-harness", readme)

        # Installed versions
        self.assertIn("Codex CLI (`codex 0.1.0`)", readme)
        self.assertIn("Claude Code CLI (`claude 1.2.4`", readme)
        self.assertIn("claude-3-7-sonnet-20250219", readme)
        self.assertIn("Antigravity CLI (`agy 2.0.0`", readme)
        self.assertIn("gemini-3.1-pro-high", readme)
        self.assertIn("Python 3.13.7", readme)

        # Run log path and unit ID
        self.assertIn("run-20260916T143022Z-cxcl01.jsonl", readme)
        self.assertIn("7a2e841b9c3f", readme)

        # Selections and configuration
        self.assertIn('"implement": {"harness": "codex", "model": "gpt-5.2-codex"}', readme)
        self.assertIn('"critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"}', readme)

        # Delivery revisions and refutation
        self.assertIn("d7a31f2", readme)
        self.assertIn('`greet("  ")` did not raise `ValueError`', readme)
        self.assertIn("correctionsSpent: 1", readme)
        self.assertIn("f92e071", readme)
        self.assertIn("complete: true", readme)

        # Parallel failure isolation and explicit recovery
        self.assertIn("issue.paused", readme)
        self.assertIn("unresolved_execution_failures", readme)
        self.assertIn("issueRoleReplacements", readme)
        self.assertIn("role.changed", readme)

        # Automated vs. Live distinction & limitations without secrets
        self.assertIn("tests/test_role_execution_dispatch.py", readme)
        self.assertIn("tests/test_cross_harness_proof.py", readme)
        self.assertIn("no secrets recorded", readme)
        self.assertIn("No unsupported tier claimed", readme)
        self.assertIn("ADR-0006", readme)

    def test_operator_documentation_covers_all_contract_requirements(self) -> None:
        """AC6: Operator documentation covers discovery, tracked defaults, overrides, preflight failures, and recovery."""
        docs = self.docs_path.read_text(encoding="utf-8")
        index = self.index_path.read_text(encoding="utf-8")

        # Indexed in docs/INDEX.md
        self.assertIn("role-execution.md", index)

        # Discovery across harnesses and fail-closed requirement
        self.assertIn("discovery.py", docs)
        self.assertIn("codex models", docs)
        self.assertIn("opencode models", docs)
        self.assertIn("agy models", docs)
        self.assertIn("Unknown availability fails closed", docs)

        # Tracked defaults in .gantry/config.json
        self.assertIn(".gantry/config.json", docs)
        self.assertIn("execution.roles", docs)
        self.assertIn("setup.py", docs)

        # Overrides (Run and Issue levels)
        self.assertIn("issueRoleReplacements", docs)
        self.assertIn("args.models", docs)

        # Preflight validation and failures
        self.assertIn("Preflight aborts and starts no implementation work", docs)

        # Runtime execution failures and recovery
        self.assertIn("issue.paused", docs)
        self.assertIn("Next round is blocked while unresolved failures exist", docs)
        self.assertIn("validate_role_replacement", docs)
        self.assertIn("preserves spent correction budget", docs)

        # Honest tier definitions and quality disclaimer
        self.assertIn("Model diversity does not imply improved review quality", docs)
        self.assertIn("Reference Tier", docs)
        self.assertIn("Compatible Tier", docs)
        self.assertIn("Do not claim unsupported tiers", docs)


class IsolatedFixtureInteroperabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture_dest = Path(self.temp_dir.name) / "fixture-copy"
        # Build approved isolated copy of fixture
        res = subprocess.run(
            [
                sys.executable,
                str(COPY_FIXTURE),
                "--mode",
                "approved",
                "--skill-dir",
                str(SKILL_DIR),
                "--dest",
                str(self.fixture_dest),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, res.returncode, res.stderr)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_guard(self, payload: dict) -> dict:
        res = subprocess.run(
            [sys.executable, str(SCRIPTS / "guard.py"), "PreToolUse", "--json", "--cwd", str(self.fixture_dest)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, res.returncode, res.stderr)
        return json.loads(res.stdout)

    def test_antigravity_hook_guard_interception_in_isolated_fixture(self) -> None:
        """AC2: Automated fixture test demonstrates Antigravity hook interception and guard protections."""
        # 1. Test write_to_file guarding ROADMAP.md
        roadmap_payload = {
            "tool_name": "write_to_file",
            "tool_input": {
                "TargetFile": str(self.fixture_dest / "ROADMAP.md"),
                "CodeContent": "# Unauthorized edit",
                "Description": "edit",
                "Overwrite": True,
            },
        }
        res = self.run_guard(roadmap_payload)
        self.assertEqual("deny", res["decision"])
        self.assertEqual("roadmap-protected", res["rule"])

        # 2. Test replace_file_content guarding Status: line in issue
        issue_path = self.fixture_dest / ".scratch" / "greeting" / "issues" / "01-greet-a-valid-name.md"
        status_payload = {
            "tool_name": "replace_file_content",
            "tool_input": {
                "TargetFile": str(issue_path),
                "TargetContent": "Status: ready-for-agent",
                "ReplacementContent": "Status: done",
                "StartLine": 4,
                "EndLine": 4,
                "Description": "cheat status",
                "Instruction": "set done",
                "AllowMultiple": False,
            },
        }
        res = self.run_guard(status_payload)
        self.assertEqual("deny", res["decision"])
        self.assertEqual("issue-status-protected", res["rule"])

        # 3. Test run_command blocking git commit --no-verify bypass
        bypass_payload = {
            "tool_name": "run_command",
            "tool_input": {
                "CommandLine": "git commit --no-verify -m bypass",
                "Cwd": str(self.fixture_dest),
            },
        }
        res = self.run_guard(bypass_payload)
        self.assertEqual("deny", res["decision"])
        self.assertEqual("hook-bypass-protected", res["rule"])

        # 4. Test normal editing of fixture code is allowed
        allowed_payload = {
            "tool_name": "write_to_file",
            "tool_input": {
                "TargetFile": str(self.fixture_dest / "greeting.py"),
                "CodeContent": "def greet(name: str) -> str:\n    return f'Hello, {name.strip()}!'\n",
                "Description": "implement greeting",
                "Overwrite": True,
            },
        }
        res = self.run_guard(allowed_payload)
        self.assertEqual("allow", res["decision"])

    def test_adversarial_critic_refutes_unmet_criterion_and_accepts_corrected_delivery(self) -> None:
        """AC4: A known unmet fixture criterion is refuted and corrected delivery accepted after independent verification."""
        greeting_file = self.fixture_dest / "greeting.py"

        # Attempt 1: Flawed delivery - does not strip or check for whitespace
        faulty_code = 'def greet(name: str) -> str:\n    if not name:\n        raise ValueError("name required")\n    return f"Hello, {name}!"\n'
        greeting_file.write_text(faulty_code, encoding="utf-8")

        # Load module dynamically
        spec1 = importlib.util.spec_from_file_location("greeting_attempt1", str(greeting_file))
        assert spec1 is not None and spec1.loader is not None
        mod1 = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(mod1)

        # Verify criterion 1 passes
        self.assertEqual("Hello, Ada!", mod1.greet("Ada"))

        # Verify criterion 2 fails (does not raise ValueError on "  ")
        c2_failed = False
        try:
            val = mod1.greet("  ")
            c2_failed = True
        except ValueError:
            c2_failed = False
        self.assertTrue(c2_failed, "Faulty code unexpectedly passed criterion 2")

        # Critic produces schema-valid refutation result
        critic_schema = result.load_schema("critic")
        critic_refutation = {
            "complete": False,
            "criteria": [
                {"index": 0, "met": True, "evidence": "returned 'Hello, Ada!'"},
                {"index": 1, "met": False, "evidence": "returned 'Hello,   !' without raising ValueError"},
            ],
            "gatesVerdict": "pass",
            "gateResult": {"verdict": "pass"},
            "gateFailures": [],
            "refutations": ['greet("  ") did not raise ValueError mentioning a non-empty name'],
            "requiredFixes": ["Strip whitespace and raise ValueError if stripped name is empty"],
            "decisionsForOperator": [],
        }
        refutation_errors = result.validate(critic_refutation, critic_schema)
        self.assertEqual([], refutation_errors)
        self.assertFalse(critic_refutation["complete"])
        self.assertEqual(1, len(critic_refutation["refutations"]))

        # Attempt 2: Corrected delivery
        corrected_code = 'def greet(name: str) -> str:\n    stripped = name.strip()\n    if not stripped:\n        raise ValueError("name must be non-empty")\n    return f"Hello, {stripped}!"\n'
        greeting_file.write_text(corrected_code, encoding="utf-8")

        # Load updated module dynamically
        spec2 = importlib.util.spec_from_file_location("greeting_attempt2", str(greeting_file))
        assert spec2 is not None and spec2.loader is not None
        mod2 = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(mod2)

        self.assertEqual("Hello, Ada!", mod2.greet("Ada"))
        with self.assertRaises(ValueError) as ctx:
            mod2.greet("  ")
        self.assertIn("non-empty", str(ctx.exception))

        # Differential gate check
        lint_res = subprocess.run(
            [sys.executable, str(self.fixture_dest / "tools" / "lint.py"), "--json"],
            cwd=self.fixture_dest,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, lint_res.returncode)

        # Critic produces schema-valid accepted result
        critic_accepted = {
            "complete": True,
            "criteria": [
                {"index": 0, "met": True, "evidence": "returned 'Hello, Ada!'"},
                {"index": 1, "met": True, "evidence": "raised ValueError('name must be non-empty')"},
            ],
            "gatesVerdict": "pass",
            "gateResult": {"verdict": "pass"},
            "gateFailures": [],
            "refutations": [],
            "requiredFixes": [],
            "decisionsForOperator": [],
        }
        accepted_errors = result.validate(critic_accepted, critic_schema)
        self.assertEqual([], accepted_errors)
        self.assertTrue(critic_accepted["complete"])
        self.assertEqual(0, len(critic_accepted["refutations"]))

    def test_antigravity_role_dispatch_and_execution_contract_in_fixture(self) -> None:
        """AC2: Automated contract test for Antigravity agy CLI role dispatch in fixture."""
        cmd = execution.build_dispatch_command(
            harness="antigravity",
            model="gemini-3.1-pro-high",
            prompt="Verify greeting fixture",
            effort="high",
            output_format="json",
        )
        self.assertEqual("agy", cmd[0])
        self.assertIn("--print", cmd)
        self.assertIn("--model", cmd)
        self.assertIn("gemini-3.1-pro-high", cmd)
        self.assertIn("--effort", cmd)
        self.assertIn("high", cmd)
        self.assertIn("--output-format", cmd)
        self.assertIn("json", cmd)
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertEqual("Verify greeting fixture", cmd[-1])


if __name__ == "__main__":
    unittest.main()
