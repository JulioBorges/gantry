#!/usr/bin/env python3
"""Tests for role execution defaults, preflight validation, Antigravity hooks and tool guards."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
SETUP_SCRIPT = SCRIPTS / "setup.py"
EXECUTION_SCRIPT = SCRIPTS / "execution.py"
GUARD_SCRIPT = SCRIPTS / "guard.py"

sys.path.insert(0, str(SCRIPTS))
import execution  # noqa: E402
import guard  # noqa: E402


class RoleExecutionSetupAndPolicyTests(unittest.TestCase):
    def test_setup_preview_and_merge_persists_execution_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Create existing policy with caveman and git
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_path = gantry_dir / "config.json"
            config_path.write_text(
                json.dumps({"caveman": True, "git": {"target": "main"}}),
                encoding="utf-8",
            )

            # Proposed config adds execution.roles
            config_json = {
                "execution": {
                    "roles": {
                        "plan": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
                    }
                }
            }

            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, _ = p.communicate(input="m\n")
            self.assertIn("Proposed .gantry/config.json:", stdout)
            self.assertIn('"gemini-3.8-flash-medium"', stdout)

            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertTrue(written.get("caveman"))
            self.assertEqual("main", written["git"]["target"])
            self.assertIn("execution", written)
            self.assertIn("roles", written["execution"])
            self.assertEqual("antigravity", written["execution"]["roles"]["plan"]["harness"])
            self.assertEqual("claude-code", written["execution"]["roles"]["critic"]["harness"])

    def test_setup_configures_agents_hooks_json_when_antigravity_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".agents").mkdir()

            config_json = {"execution": {"roles": {"plan": {"harness": "antigravity"}}}}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="y\n")

            hooks_path = root / ".agents" / "hooks.json"
            self.assertTrue(hooks_path.exists())
            hooks_data = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertIn("hooks", hooks_data)
            self.assertIn("PreToolUse", hooks_data["hooks"])
            hook_entries = hooks_data["hooks"]["PreToolUse"]
            self.assertTrue(any("guard.py\" PreToolUse --json" in h["command"] for entry in hook_entries for h in entry.get("hooks", [])))

    def test_setup_merges_existing_agents_hooks_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agents_dir = root / ".agents"
            agents_dir.mkdir()
            hooks_path = agents_dir / "hooks.json"
            hooks_path.write_text(
                json.dumps({"hooks": {"PostToolUse": [{"type": "command", "command": "echo post"}]}}),
                encoding="utf-8",
            )

            config_json = {"test": "val"}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="y\n")

            merged = json.loads(hooks_path.read_text(encoding="utf-8"))
            self.assertIn("PostToolUse", merged["hooks"])
            self.assertIn("PreToolUse", merged["hooks"])


class GitIgnorePolicyTests(unittest.TestCase):
    def test_canonical_root_policy_is_trackable_while_transient_state_and_secrets_are_ignored(self) -> None:
        res = subprocess.run(
            ["git", "check-ignore", "-v", ".gantry/config.json", ".gantry/state.json", ".gantry/secret.key"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        lines = res.stdout.splitlines()
        # .gantry/config.json must have negative pattern !.gantry/config.json
        config_line = next((l for l in lines if ".gantry/config.json" in l), "")
        self.assertIn("!.gantry/config.json", config_line)

        # transient state and secrets must be ignored
        state_line = next((l for l in lines if ".gantry/state.json" in l), "")
        self.assertIn(".gantry/*", state_line)
        secret_line = next((l for l in lines if ".gantry/secret.key" in l), "")
        self.assertIn(".gantry/*", secret_line)


class RoleExecutionPreflightTests(unittest.TestCase):
    def test_precedence_issue_override_wins_over_run_and_policy(self) -> None:
        policy = {
            "execution": {
                "roles": {
                    "critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
                }
            }
        }
        run_overrides = {
            "critic": {"harness": "codex", "model": "gpt-5.2-codex"},
        }
        issue_overrides = {
            "critic": {"harness": "antigravity", "model": "gemini-3.1-pro-high"},
        }

        # Issue override wins
        res = execution.resolve_single_role(
            "critic",
            policy=policy,
            run_overrides=run_overrides,
            issue_overrides=issue_overrides,
        )
        self.assertEqual("antigravity", res["harness"])
        self.assertEqual("gemini-3.1-pro-high", res["model"])

        # Without issue override, Run override wins
        res2 = execution.resolve_single_role(
            "critic",
            policy=policy,
            run_overrides=run_overrides,
            issue_overrides={},
        )
        self.assertEqual("codex", res2["harness"])
        self.assertEqual("gpt-5.2-codex", res2["model"])

        # Without run override, policy wins
        res3 = execution.resolve_single_role(
            "critic",
            policy=policy,
            run_overrides={},
            issue_overrides={},
        )
        self.assertEqual("claude-code", res3["harness"])
        self.assertEqual("claude-3-7-sonnet-20250219", res3["model"])

        # Without policy, environment default wins
        res4 = execution.resolve_single_role(
            "critic",
            policy={},
            run_overrides={},
            issue_overrides={},
        )
        self.assertEqual("claude-code", res4["harness"])

    def test_derived_role_inheritance(self) -> None:
        policy = {
            "execution": {
                "roles": {
                    "critic": {"harness": "antigravity", "model": "gemini-3.1-pro-high"},
                    "plan": {"harness": "codex", "model": "gpt-5.2-codex"},
                }
            }
        }

        roles = execution.resolve_roles(policy=policy)
        # requirement-critic, plan-critic, learner inherit from critic
        self.assertEqual("antigravity", roles["requirement-critic"]["harness"])
        self.assertEqual("gemini-3.1-pro-high", roles["requirement-critic"]["model"])
        self.assertEqual("antigravity", roles["plan-critic"]["harness"])
        self.assertEqual("antigravity", roles["learner"]["harness"])

        # research inherits from plan
        self.assertEqual("codex", roles["research"]["harness"])
        self.assertEqual("gpt-5.2-codex", roles["research"]["model"])

        # Explicit learner override does not change critic
        policy_with_learner = {
            "execution": {
                "roles": {
                    "critic": {"harness": "antigravity", "model": "gemini-3.1-pro-high"},
                    "learner": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
                }
            }
        }
        roles2 = execution.resolve_roles(policy=policy_with_learner)
        self.assertEqual("antigravity", roles2["critic"]["harness"])
        self.assertEqual("claude-code", roles2["learner"]["harness"])

    def test_preflight_starts_no_implementation_when_auth_or_validation_fails(self) -> None:
        policy = {
            "execution": {
                "roles": {
                    "implement": {"harness": "invalid-harness", "model": "some-model"},
                }
            }
        }
        res = execution.preflight_validate(policy=policy, check_auth=False)
        self.assertFalse(res["valid"])
        self.assertTrue(any("Unsupported harness" in err for err in res["errors"]))

        # Failing auth runner
        class FailingRunner:
            def __call__(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="auth error")

        res2 = execution.preflight_validate(
            policy={"execution": {"roles": {"plan": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"}}}},
            check_auth=True,
            runner=FailingRunner(),
        )
        self.assertFalse(res2["valid"])
        self.assertTrue(any("authentication/execution validation failed" in err for err in res2["errors"]))

    def test_model_strength_guidance_is_advisory_only(self) -> None:
        policy = {
            "execution": {
                "roles": {
                    "implement": {"harness": "codex", "model": "gemini-3.1-pro-high"},
                    "critic": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                }
            }
        }
        res = execution.preflight_validate(policy=policy, check_auth=False)
        # Advisory notes should be present
        self.assertTrue(any("Advisory:" in g for g in res["guidance"]))
        # But valid is still True (not blocked by guessed ranking)
        self.assertTrue(res["valid"])


class AntigravityGuardNormalizationTests(unittest.TestCase):
    def test_run_command_normalization_and_protection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Denied: git hook bypass via run_command
            payload = {
                "tool_name": "run_command",
                "tool_input": {"CommandLine": "git commit -m 'skip' --no-verify", "Cwd": str(root)},
            }
            p = subprocess.run(
                [sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json", "--cwd", str(root)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p.returncode, p.stdout + p.stderr)
            res = json.loads(p.stdout)
            self.assertEqual("deny", res["decision"])
            self.assertEqual("hook-bypass-protected", res["rule"])

            # Allowed: normal command
            payload_ok = {
                "tool_name": "run_command",
                "tool_input": {"CommandLine": "pytest tests/", "Cwd": str(root)},
            }
            p_ok = subprocess.run(
                [sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json", "--cwd", str(root)],
                input=json.dumps(payload_ok),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p_ok.returncode)
            res_ok = json.loads(p_ok.stdout)
            self.assertEqual("allow", res_ok["decision"])

    def test_write_to_file_and_replace_file_content_protections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Roadmap protected on write_to_file
            p_rm = subprocess.run(
                [sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json", "--cwd", str(root)],
                input=json.dumps({
                    "tool_name": "write_to_file",
                    "tool_input": {"TargetFile": str(root / "ROADMAP.md"), "CodeContent": "# New roadmap"},
                }),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p_rm.returncode)
            res_rm = json.loads(p_rm.stdout)
            self.assertEqual("deny", res_rm["decision"])
            self.assertEqual("roadmap-protected", res_rm["rule"])

            # Issue status protected on replace_file_content
            issue_path = root / "01-sample.md"
            issue_path.write_text("Type: issue\nStatus: ready-for-agent\n- [ ] criterion\n", encoding="utf-8")

            p_issue = subprocess.run(
                [sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json", "--cwd", str(root)],
                input=json.dumps({
                    "tool_name": "replace_file_content",
                    "tool_input": {
                        "TargetFile": str(issue_path),
                        "TargetContent": "Status: ready-for-agent",
                        "ReplacementContent": "Status: done",
                    },
                }),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p_issue.returncode)
            res_issue = json.loads(p_issue.stdout)
            self.assertEqual("deny", res_issue["decision"])
            self.assertEqual("issue-status-protected", res_issue["rule"])

            # Issue checkbox protected on replace_file_content
            p_box = subprocess.run(
                [sys.executable, str(GUARD_SCRIPT), "PreToolUse", "--json", "--cwd", str(root)],
                input=json.dumps({
                    "tool_name": "replace_file_content",
                    "tool_input": {
                        "TargetFile": str(issue_path),
                        "TargetContent": "- [ ] criterion",
                        "ReplacementContent": "- [x] criterion",
                    },
                }),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, p_box.returncode)
            res_box = json.loads(p_box.stdout)
            self.assertEqual("deny", res_box["decision"])
            self.assertEqual("issue-checkbox-protected", res_box["rule"])


if __name__ == "__main__":
    unittest.main()
