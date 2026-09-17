#!/usr/bin/env python3
"""Contract tests for cross-harness role execution dispatch, guard normalization, and verification."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
EXECUTION_SCRIPT = SCRIPTS / "execution.py"
GUARD_SCRIPT = SCRIPTS / "guard.py"
RESULT_SCRIPT = SCRIPTS / "result.py"

sys.path.insert(0, str(SCRIPTS))
import execution  # noqa: E402
import guard  # noqa: E402
import result  # noqa: E402
import runlog  # noqa: E402


class RoleExecutionDispatchContractTests(unittest.TestCase):
    def test_every_role_and_derived_role_can_select_independent_harness_model_effort(self) -> None:
        """Exercise all base and derived roles with independent harness/model/effort selections."""
        selections = {
            "plan": {"harness": "antigravity", "model": "gemini-3.8-flash-medium", "effort": "medium"},
            "implement": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
            "review": {"harness": "codex", "model": "gpt-5.2-codex"},
            "critic": {"harness": "antigravity", "model": "gemini-3.1-pro-high", "effort": "high"},
            "requirement-critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
            "plan-critic": {"harness": "opencode", "model": "claude-3-7-sonnet-20250219"},
            "research": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
            "learner": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
        }
        resolved = execution.resolve_roles(policy={"execution": {"roles": selections}})
        for role, sel in selections.items():
            self.assertEqual(sel["harness"], resolved[role]["harness"], f"Harness mismatch for {role}")
            self.assertEqual(sel["model"], resolved[role]["model"], f"Model mismatch for {role}")
            if "effort" in sel:
                self.assertEqual(sel["effort"], resolved[role]["effort"], f"Effort mismatch for {role}")

    def test_build_dispatch_command_antigravity_agy_cli(self) -> None:
        """Verify Antigravity agy command construction with effort, json output, and skip permissions."""
        cmd = execution.build_dispatch_command(
            harness="antigravity",
            model="gemini-3.1-pro-high",
            prompt="Implement greeting",
            effort="high",
            output_format="json",
        )
        self.assertEqual(
            ["agy", "--print", "--model", "gemini-3.1-pro-high", "--effort", "high", "--output-format", "json", "--dangerously-skip-permissions", "Implement greeting"],
            cmd,
        )

    def test_build_dispatch_command_other_harnesses(self) -> None:
        """Verify command construction across Claude Code, OpenCode, and Codex."""
        claude_cmd = execution.build_dispatch_command("claude-code", "claude-3-7-sonnet-20250219", "Review code")
        self.assertIn("claude", claude_cmd)
        self.assertIn("-p", claude_cmd)
        self.assertIn("claude-3-7-sonnet-20250219", claude_cmd)

        opencode_cmd = execution.build_dispatch_command("opencode", "claude-3-7-sonnet-20250219", "Review code")
        self.assertEqual(["opencode", "run", "Review code", "--model", "claude-3-7-sonnet-20250219"], opencode_cmd)

        codex_cmd = execution.build_dispatch_command("codex", "gpt-5.2-codex", "Plan spec")
        self.assertEqual(["codex", "exec", "Plan spec", "--model", "gpt-5.2-codex"], codex_cmd)

    def test_dispatch_role_executes_in_canonical_assigned_working_directory(self) -> None:
        """Verify dispatch_role executes in the assigned working directory."""
        with tempfile.TemporaryDirectory() as temp:
            worktree = Path(temp) / "worktree"
            worktree.mkdir()
            executed_cwd = []

            class MockRunner:
                def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                    if "--version" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="1.2.4\n", stderr="")
                    executed_cwd.append(kwargs.get("cwd"))
                    # Return valid implementer JSON result
                    valid_output = json.dumps({
                        "worktree": str(worktree),
                        "branch": "feature-1",
                        "commits": ["c1"],
                        "summary": "done",
                        "testsAdded": ["t1"],
                        "gatesResult": "pass",
                        "decisions": [],
                        "blockers": [],
                    })
                    return subprocess.CompletedProcess(cmd, 0, stdout=valid_output, stderr="")

            res = execution.dispatch_role(
                role="implementer",
                prompt="implement",
                cwd=worktree,
                selection={"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                runner=MockRunner(),
            )
            self.assertEqual(str(worktree.resolve()), executed_cwd[0])
            self.assertEqual(str(worktree), res["worktree"])

    def test_unsupported_harness_version_is_explicitly_rejected(self) -> None:
        """Installed versions below minimum supported version are rejected with explicit error."""
        class OldVersionRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                # Old agy version 0.9.0
                return subprocess.CompletedProcess(cmd, 0, stdout="0.9.0\n", stderr="")

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            with self.assertRaises(execution.UnsupportedHarnessVersionError) as ctx:
                execution.dispatch_role(
                    role="plan",
                    prompt="plan",
                    cwd=cwd,
                    selection={"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                    runner=OldVersionRunner(),
                )
            self.assertIn("Unsupported installed version 0.9.0", str(ctx.exception))
            self.assertIn("Minimum supported is 1.0.0", str(ctx.exception))

    def test_selection_identity_honestly_recorded_and_fallback_rejected(self) -> None:
        """Verify selection identity is recorded in Run log and model fallback is detected and rejected."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
            run_id = "run-20260916T000000Z-123456"
            unit_id = runlog.unit_id(root)
            state_root = root / "state"
            state_root.mkdir()
            log_dir = state_root / unit_id / "runs"
            log_dir.mkdir(parents=True)
            log_path = log_dir / f"{run_id}.jsonl"
            # Seed log with run.started
            log_path.write_text(
                json.dumps({"ts": "2026-09-16T00:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root)}}) + "\n",
                encoding="utf-8",
            )

            # 1. Honest recording on successful dispatch
            class HonestRunner:
                def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                    if "--version" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="1.2.4\n", stderr="")
                    valid_output = json.dumps({
                        "worktree": str(root),
                        "branch": "b1",
                        "commits": [],
                        "summary": "done",
                        "testsAdded": [],
                        "gatesResult": "pass",
                        "decisions": [],
                        "blockers": [],
                    })
                    return subprocess.CompletedProcess(cmd, 0, stdout=valid_output, stderr="")

            execution.dispatch_role(
                role="implementer",
                prompt="implement",
                cwd=root,
                selection={"harness": "antigravity", "model": "gemini-3.1-pro-high", "effort": "high"},
                runner=HonestRunner(),
                run_id=run_id,
                unit_id=unit_id,
                state_root=str(state_root),
            )

            events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            start_event = next(e for e in events if e.get("event") == "subagent.started")
            self.assertEqual("antigravity", start_event["data"]["harness"])
            self.assertEqual("gemini-3.1-pro-high", start_event["data"]["model"])
            self.assertEqual("high", start_event["data"]["effort"])

            # 2. Rejection of automatic model fallback
            class FallbackRunner:
                def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                    if "--version" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="1.2.4\n", stderr="")
                    fallback_output = json.dumps({
                        "model": "gemini-3.8-flash-low",  # substituted model!
                        "worktree": str(root),
                        "branch": "b1",
                        "commits": [],
                        "summary": "fallback occurred",
                        "testsAdded": [],
                        "gatesResult": "pass",
                        "decisions": [],
                        "blockers": [],
                    })
                    return subprocess.CompletedProcess(cmd, 0, stdout=fallback_output, stderr="")

            with self.assertRaises(execution.ModelFallbackError) as ctx:
                execution.dispatch_role(
                    role="implementer",
                    prompt="implement",
                    cwd=root,
                    selection={"harness": "antigravity", "model": "gemini-3.1-pro-high"},
                    runner=FallbackRunner(),
                )
            self.assertIn("Automatic model fallback detected", str(ctx.exception))

    def test_result_contract_validation_and_protocol_failure_semantics(self) -> None:
        """Invalid schema output triggers protocol failure with retry; failure if retry also invalid."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []

            class BadOutputRunner:
                def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                    if "--version" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="1.2.4\n", stderr="")
                    calls.append(cmd)
                    # Missing required fields for reviewer contract (summary, blocking, nonBlocking)
                    invalid_output = json.dumps({"only_summary": "invalid"})
                    return subprocess.CompletedProcess(cmd, 0, stdout=invalid_output, stderr="")

            with self.assertRaises(execution.ProtocolFailureError) as ctx:
                execution.dispatch_role(
                    role="reviewer",
                    prompt="review",
                    cwd=root,
                    selection={"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                    runner=BadOutputRunner(),
                    retry_on_invalid=True,
                )
            self.assertIn("schema validation failed for reviewer", str(ctx.exception))
            # Verify one retry was attempted
            self.assertEqual(2, len(calls))

    def test_critic_invocation_verifies_revision_and_fails_visibly_on_permission_or_tool_limits(self) -> None:
        """Critic cannot accept a summary without running gates/criteria, and fails visibly on permission errors."""
        # 1. Permission limitation fails visibly
        critic_perm_error = {
            "complete": False,
            "permission_error": True,
            "error": "Tool execution permission denied for git and gates.py",
        }
        with self.assertRaises(RuntimeError) as ctx:
            execution.verify_critic_result(critic_perm_error)
        self.assertIn("Critic execution failed visibly", str(ctx.exception))
        self.assertIn("permission denied", str(ctx.exception))

        # 2. Complete=True without gatesResult is rejected
        critic_summary_only = {
            "complete": True,
            "summary": "Everything looks good to me without running gates",
            "criteria": [{"index": 1, "met": True, "evidence": "good"}],
        }
        with self.assertRaises(execution.ProtocolFailureError) as ctx:
            execution.verify_critic_result(critic_summary_only)
        self.assertIn("without required gateResult", str(ctx.exception))

        # 3. Complete=True with failing gates is rejected
        critic_failed_gate = {
            "complete": True,
            "gateResult": {"verdict": "fail", "requirements": ["lint error"]},
            "criteria": [{"index": 1, "met": True, "evidence": "good"}],
        }
        with self.assertRaises(execution.ProtocolFailureError) as ctx:
            execution.verify_critic_result(critic_failed_gate)
        self.assertIn("gateResult verdict is 'fail'", str(ctx.exception))

        # 4. Valid Critic result passes
        critic_valid = {
            "complete": True,
            "gatesVerdict": "pass",
            "gateResult": {"verdict": "pass", "requirements": []},
            "gateFailures": [],
            "criteria": [{"index": 1, "met": True, "evidence": "Verified greeting returns expected string with pytest -q"}],
            "refutations": [],
            "requiredFixes": [],
            "decisionsForOperator": [],
        }
        # Should not raise
        execution.verify_critic_result(critic_valid)


class AntigravityGuardSubagentAndToolTests(unittest.TestCase):
    def test_guard_normalizes_invoke_subagent_and_records_runlog_events(self) -> None:
        """guard.py handles invoke_subagent tool calls and records subagent.started and stopped."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
            run_id = "run-20260916T000000Z-111111"
            unit_id = runlog.unit_id(root)
            state_root = root / "state"
            state_root.mkdir()
            log_dir = state_root / unit_id / "runs"
            log_dir.mkdir(parents=True)
            log_path = log_dir / f"{run_id}.jsonl"
            log_path.write_text(
                json.dumps({"ts": "2026-09-16T00:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root)}}) + "\n",
                encoding="utf-8",
            )

            # 1. PreToolUse for invoke_subagent records subagent.started and returns allow exit 0
            payload_start = {
                "tool_name": "invoke_subagent",
                "tool_input": {
                    "Subagents": [
                        {
                            "Role": "Requirement Critic",
                            "TypeName": "research",
                            "Prompt": "Assess spec ambiguity",
                        }
                    ]
                },
            }
            p1 = subprocess.run(
                [
                    sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json",
                    "--cwd", str(root), "--run-id", run_id,
                    "--state-root", str(state_root),
                ],
                input=json.dumps(payload_start),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p1.returncode)
            res1 = json.loads(p1.stdout)
            self.assertEqual("allow", res1["decision"])

            # 2. PostToolUse for invoke_subagent records subagent.stopped and returns allow exit 0
            p2 = subprocess.run(
                [
                    sys.executable, str(GUARD_SCRIPT), "PostToolUse", "--json",
                    "--cwd", str(root), "--run-id", run_id,
                    "--state-root", str(state_root),
                ],
                input=json.dumps(payload_start),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p2.returncode)
            res2 = json.loads(p2.stdout)
            self.assertEqual("allow", res2["decision"])

            events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            start_event = next(e for e in events if e.get("event") == "subagent.started")
            self.assertEqual("Requirement Critic", start_event["data"]["role"])
            stop_event = next(e for e in events if e.get("event") == "subagent.stopped")
            self.assertEqual("Requirement Critic", stop_event["data"]["role"])

    def test_guard_normalizes_antigravity_cwd_in_run_command(self) -> None:
        """guard.py extracts Cwd from Antigravity tool_input to resolve effective worktree."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            worktree = root / "isolated-worktree"
            worktree.mkdir()
            issue_file = worktree / "01-sample.md"
            issue_file.write_text("Type: issue\nStatus: ready-for-agent\n", encoding="utf-8")

            # run_command specifying Cwd
            payload = {
                "tool_name": "run_command",
                "tool_input": {
                    "CommandLine": "git commit --no-verify -m 'skip'",
                    "Cwd": str(worktree),
                },
            }
            p = subprocess.run(
                [sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json", "--cwd", str(root)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p.returncode)
            res = json.loads(p.stdout)
            self.assertEqual("deny", res["decision"])
            self.assertEqual("hook-bypass-protected", res["rule"])


if __name__ == "__main__":
    unittest.main()
