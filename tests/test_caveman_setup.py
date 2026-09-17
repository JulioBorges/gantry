#!/usr/bin/env python3
"""Tests for Caveman setup preference, discovery, and coordinating agent activation."""
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
CAVEMAN_SCRIPT = SCRIPTS / "caveman.py"

sys.path.insert(0, str(SCRIPTS))
from common import resolve_policy  # noqa: E402
import caveman  # noqa: E402


class CavemanPolicyAndSetupTests(unittest.TestCase):
    def test_default_policy_has_caveman_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            policy = resolve_policy(root)
            self.assertIn("caveman", policy)
            self.assertFalse(policy["caveman"])

    def test_setup_persists_confirmed_caveman_preference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_json = {"caveman": True}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="y\n")
            config_path = root / ".gantry" / "config.json"
            self.assertTrue(config_path.exists())
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertTrue(written.get("caveman"))

    def test_setup_merge_preserves_existing_caveman_preference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_path = gantry_dir / "config.json"
            config_path.write_text(json.dumps({"caveman": True, "git": {"target": "main"}}), encoding="utf-8")

            # Merge with new config that doesn't mention caveman
            config_json = {"git": {"prefix": "work/"}}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="m\n")
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertTrue(written.get("caveman"))
            self.assertEqual("main", written["git"]["target"])
            self.assertEqual("work/", written["git"]["prefix"])

    def test_setup_supports_explicit_disabling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_path = gantry_dir / "config.json"
            config_path.write_text(json.dumps({"caveman": True}), encoding="utf-8")

            # Merge with explicit caveman: false
            config_json = {"caveman": False}
            p = subprocess.Popen(
                [sys.executable, str(SETUP_SCRIPT), "--config", json.dumps(config_json)],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input="m\n")
            written = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertFalse(written.get("caveman"))


class CavemanDiscoveryAndActivationTests(unittest.TestCase):
    def test_installation_guidance_for_supported_harnesses(self) -> None:
        claude_cmd = caveman.get_install_guidance("claude-code")
        self.assertIn("npx skills add caveman", claude_cmd)

        agy_cmd = caveman.get_install_guidance("antigravity")
        self.assertIn("~/.gemini/config/skills/caveman", agy_cmd)

        codex_cmd = caveman.get_install_guidance("codex")
        self.assertIn(".agents/skills/caveman", codex_cmd)

    def test_discovery_verifies_skill_readability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Not found
            res = caveman.check_availability("claude-code", root=root)
            self.assertFalse(res["available"])
            self.assertEqual("not_found", res["reason"])

            # Create mock skill file
            skill_dir = root / ".agents" / "skills" / "caveman"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("# Caveman Lite\nConcise instructions.\n", encoding="utf-8")

            res = caveman.check_availability("claude-code", root=root)
            self.assertTrue(res["available"])
            self.assertEqual(str(skill_file.resolve()), res["path"])

    def test_activation_disabled_preference_does_not_load_skill(self) -> None:
        policy = {"caveman": False}
        res = caveman.resolve_activation(policy, harness="claude-code")
        self.assertFalse(res["preference"])
        self.assertFalse(res["active"])
        self.assertIsNone(res["warning"])

    def test_activation_available_skill_activates_lite_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill_dir = root / ".agents" / "skills" / "caveman"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Caveman Lite\n", encoding="utf-8")

            policy = {"caveman": True}
            res = caveman.resolve_activation(policy, harness="claude-code", root=root)
            self.assertTrue(res["preference"])
            self.assertTrue(res["active"])
            self.assertIsNone(res["warning"])
            self.assertEqual("conversational_and_summaries", res["scope"])

    def test_activation_fallback_and_warning_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            policy = {"caveman": True}

            # First check when skill is not installed: emits warning
            res1 = caveman.resolve_activation(policy, harness="claude-code", root=root, warned=False)
            self.assertTrue(res1["preference"])
            self.assertFalse(res1["active"])
            self.assertIsNotNone(res1["warning"])
            self.assertIn("Caveman lite is enabled", res1["warning"])
            self.assertTrue(res1["warned"])

            # Subsequent check in the same Run (warned=True): does NOT repeat warning
            res2 = caveman.resolve_activation(policy, harness="claude-code", root=root, warned=True)
            self.assertTrue(res2["preference"])
            self.assertFalse(res2["active"])
            self.assertIsNone(res2["warning"])
            self.assertTrue(res2["warned"])

    def test_coordinating_instructions_include_caveman_when_active(self) -> None:
        instructions = caveman.get_coordinating_instructions(active=True)
        self.assertIn("Caveman lite", instructions)
        self.assertIn("conversational messages and summaries", instructions)
        self.assertIn("retain full detail", instructions)

        inactive_instructions = caveman.get_coordinating_instructions(active=False)
        self.assertEqual("", inactive_instructions)

    def test_planning_and_round_instructions_helpers(self) -> None:
        p_inst = caveman.get_planning_instructions(active=True)
        self.assertIn("Caveman lite", p_inst)
        self.assertIn("Specs, draft Issues", p_inst)

        r_inst = caveman.get_round_instructions(active=True)
        self.assertIn("Caveman lite", r_inst)
        self.assertIn("verification evidence", r_inst)


def run_workflow_with_recorder(workflow_file: str, args: dict, fail_initial_role: str | None = None) -> dict:
    source = (SKILL_DIR / "reference" / workflow_file).read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
    source = source.replace("export const meta", "const meta", 1)
    driver = f"""
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {json.dumps(args)};
const failRole = {json.dumps(fail_initial_role)};
const calls = [];
const commandCalls = [];
let initialFailed = false;

const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd || args.repoRoot }});
  if (command.includes('/spec.py')) return {{ exitCode: 0, stdout: '{{"valid":true}}', stderr: '' }};
  if (command.includes('/result.py')) return {{ exitCode: 0, stdout: '{{"valid":true}}', stderr: '' }};
  if (command.includes('/common.py')) return {{ exitCode: 0, stdout: JSON.stringify({{ issueBranch: args.issueBranch || args.branch }}) }};
  if (command.includes('/budget.py')) return {{ exitCode: 0, stdout: JSON.stringify({{ issue: "p#01", estimatedTokens: 100, contextWindow: 1000, contextShare: 0.15, budgetTokens: 150, overBudget: false }}) }};
  if (command === 'git branch --show-current') return {{ exitCode: 0, stdout: args.issueBranch || args.branch }};
  if (command.includes('/acceptance.py')) {{
    return {{
      exitCode: 0,
      stdout: JSON.stringify({{
        complete: true,
        criteria: [{{ index: 1, text: 'criterion', checked: false }}],
      }}),
    }};
  }}
  if (command.includes('/gates.py')) return {{ exitCode: 0, stdout: JSON.stringify({{ verdict: 'pass', requirements: [] }}) }};
  if (command.includes('/roadmap.py')) return {{ exitCode: 0, stdout: '{{"verdict":"pass"}}' }};
  if (command.includes('/runlog.py')) return {{ exitCode: 0, stdout: '' }};
  if (command.includes('/learner.py')) return {{ exitCode: 0, stdout: JSON.stringify({{ candidates: [{{ recurringEvidence: 'ev', target: 'CONTEXT.md', count: 2 }}] }}) }};
  return {{ exitCode: 0, stdout: '' }};
}};

const log = (msg) => {{}};
const prompt = async () => 'no';
const phase = (name) => {{}};
const parallel = async (tasks) => Promise.all(tasks.map((task) => task()));
const pipeline = async (items, ...steps) => {{
  const results = [];
  for (const item of items) {{
    let value = await steps[0](item);
    for (const step of steps.slice(1)) value = await step(value, item);
    results.push(value);
  }}
  return results;
}};

const agent = async (promptText, options) => {{
  calls.push({{ prompt: promptText, label: options.label, options }});
  if (failRole && options.label.startsWith(failRole) && !initialFailed) {{
    initialFailed = true;
    return null; // triggers retry
  }}
  if (options.label.startsWith('requirement-critic')) return {{ blocking: [], findings: [] }};
  if (options.label.startsWith('plan')) return {{ filesWritten: [], issues: [{{ ref: 'p#01', path: 'issues/01.md', title: 'Issue 1', criteriaCount: 1, blockedBy: [] }}], roadmapAdditions: [], openDecisions: [] }};
  if (options.label.startsWith('critique')) return {{ acceptable: true, problems: [], frontierErrors: [] }};
  if (options.label.startsWith('research:format')) return JSON.stringify({{ selected: [] }});
  if (options.label.startsWith('research:')) return 'factual research';
  if (options.label.startsWith('implement:')) return {{
    worktree: args.repoRoot, branch: args.branch, commits: ['commit 1'],
    summary: 'implemented vertical slice', testsAdded: ['test_one'], gatesResult: 'verdict: pass',
    decisions: [], blockers: [],
  }};
  if (options.label.startsWith('review:')) return {{ blocking: [], nonBlocking: [], summary: 'no findings' }};
  if (options.label.startsWith('critic:')) return {{
    complete: true,
    criteria: [{{ index: 1, text: 'criterion', met: true, evidence: 'passed' }}],
    gatesVerdict: 'pass', gateResult: {{ verdict: 'pass' }}, gateFailures: [],
    refutations: [], requiredFixes: [], decisionsForOperator: [],
  }};
  if (options.label === 'learn') return {{ candidates: [] }};
  return null;
}};

const fn = new AsyncFunction('args', 'runCommand', 'agent', 'parallel', 'pipeline', 'log', 'prompt', 'phase', source);
fn(args, runCommand, agent, parallel, pipeline, log, prompt, phase).then(
  (result) => {{
    console.log(JSON.stringify({{ result, calls }}));
    process.exit(0);
  }},
  (err) => {{
    console.error(err);
    process.exit(1);
  }}
);
"""
    proc = subprocess.run(
        ["node", "-e", driver],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


class PlanningWorkflowCavemanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_args = {
            "target": {"kind": "spec", "slug": "test-spec", "specPath": ".scratch/test-spec/spec.md"},
            "models": {"plan": "claude-opus-4-5", "critic": "claude-opus-4-5"},
            "skillDir": str(SKILL_DIR),
            "repoRoot": "/fake/repo",
            "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
            "paths": {
                "issueDir": ".scratch/test-spec/issues",
                "specPath": ".scratch/test-spec/spec.md",
                "exemplarIssue": "docs/agents/issue-tracker.md",
                "decisions": "docs/adr",
                "issueTracker": "docs/agents/issue-tracker.md",
                "context": "CONTEXT.md",
                "adrs": "docs/adr",
            },
        }

    def test_planning_workflow_propagates_caveman_to_all_planning_agents(self) -> None:
        caveman_arg = {
            "preference": True,
            "active": True,
            "skill_path": "/fake/skills/caveman/SKILL.md",
            "scope": "conversational_and_summaries",
        }
        args = {**self.base_args, "caveman": caveman_arg}
        out = run_workflow_with_recorder("plan-workflow.md", args)
        calls = out["calls"]

        labels = [c["label"] for c in calls]
        self.assertIn("requirement-critic", labels)
        self.assertIn("research:codebase", labels)
        self.assertIn("research:spec", labels)
        self.assertIn("research:format", labels)
        self.assertIn("plan", labels)
        self.assertIn("critique", labels)

        for c in calls:
            self.assertIn("Caveman lite is active", c["prompt"], f"{c['label']} missing Caveman lite instruction")
            self.assertTrue(c["options"].get("caveman"), f"{c['label']} missing caveman: true in options")
            self.assertIn("/fake/skills/caveman/SKILL.md", c["options"].get("skills", []), f"{c['label']} missing skill_path in options")

    def test_planning_workflow_propagates_to_retries(self) -> None:
        caveman_arg = {
            "preference": True,
            "active": True,
            "skill_path": "/fake/skills/caveman/SKILL.md",
            "scope": "conversational_and_summaries",
        }
        args = {**self.base_args, "caveman": caveman_arg}
        out = run_workflow_with_recorder("plan-workflow.md", args, fail_initial_role="plan")
        calls = out["calls"]
        retry_call = next((c for c in calls if c["label"] == "plan:retry"), None)
        self.assertIsNotNone(retry_call)
        self.assertIn("Caveman lite is active", retry_call["prompt"])
        self.assertTrue(retry_call["options"].get("caveman"))
        self.assertIn("/fake/skills/caveman/SKILL.md", retry_call["options"].get("skills", []))

    def test_planning_workflow_normal_behavior_when_disabled(self) -> None:
        caveman_arg = {
            "preference": False,
            "active": False,
            "scope": "none",
        }
        args = {**self.base_args, "caveman": caveman_arg}
        out = run_workflow_with_recorder("plan-workflow.md", args)
        calls = out["calls"]
        for c in calls:
            self.assertNotIn("Caveman lite is active", c["prompt"])
            self.assertFalse(c["options"].get("caveman", False))

    def test_planning_workflow_unavailable_uses_normal_behavior_and_does_not_block(self) -> None:
        caveman_arg = {
            "preference": True,
            "active": False,
            "warning": "Caveman unavailable warning",
            "warned": False,
        }
        args = {**self.base_args, "caveman": caveman_arg}
        out = run_workflow_with_recorder("plan-workflow.md", args)
        self.assertIsNotNone(out["result"]["plan"])
        for c in out["calls"]:
            self.assertNotIn("Caveman lite is active", c["prompt"])


class RoundWorkflowCavemanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_args = {
            "round": 1,
            "date": "2026-09-15",
            "branch": "gantry/work",
            "baseRef": "main",
            "isolate": False,
            "issues": [{"ref": "p#01", "path": ".scratch/test-spec/issues/01.md"}],
            "models": {"implement": "claude-opus-4-5", "review": "claude-opus-4-5", "critic": "claude-opus-4-5", "learn": "claude-opus-4-5"},
            "skillDir": str(SKILL_DIR),
            "repoRoot": "/fake/repo",
            "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
            "paths": {
                "issueDir": ".scratch/test-spec/issues",
                "specPath": ".scratch/test-spec/spec.md",
                "exemplarIssue": "docs/agents/issue-tracker.md",
                "decisions": "docs/adr",
                "issueTracker": "docs/agents/issue-tracker.md",
                "context": "CONTEXT.md",
                "adrs": "docs/adr",
            },
            "isFirstRound": True,
            "isLastRound": True,
            "learnerRunLogs": ["/fake/runlog.jsonl"],
        }

    def test_round_workflow_propagates_caveman_to_all_round_agents(self) -> None:
        caveman_arg = {
            "preference": True,
            "active": True,
            "skill_path": "/fake/skills/caveman/SKILL.md",
            "scope": "conversational_and_summaries",
        }
        args = {**self.base_args, "caveman": caveman_arg}
        out = run_workflow_with_recorder("round-workflow.md", args)
        calls = out["calls"]

        labels = [c["label"] for c in calls]
        self.assertIn("implement:p#01", labels)
        self.assertIn("review:p#01", labels)
        self.assertTrue(any(l.startswith("critic:p#01") for l in labels))
        self.assertIn("learn", labels)

        for c in calls:
            self.assertIn("Caveman lite is active", c["prompt"], f"{c['label']} missing Caveman lite instruction")
            self.assertTrue(c["options"].get("caveman"), f"{c['label']} missing caveman: true in options")
            self.assertIn("/fake/skills/caveman/SKILL.md", c["options"].get("skills", []), f"{c['label']} missing skill_path in options")

    def test_round_workflow_propagates_to_retries(self) -> None:
        caveman_arg = {
            "preference": True,
            "active": True,
            "skill_path": "/fake/skills/caveman/SKILL.md",
            "scope": "conversational_and_summaries",
        }
        args = {**self.base_args, "caveman": caveman_arg}
        out = run_workflow_with_recorder("round-workflow.md", args, fail_initial_role="critic:")
        calls = out["calls"]
        retry_call = next((c for c in calls if c["label"].startswith("critic:p#01") and c["label"].endswith(":retry")), None)
        self.assertIsNotNone(retry_call)
        self.assertIn("Caveman lite is active", retry_call["prompt"])
        self.assertTrue(retry_call["options"].get("caveman"))
        self.assertIn("/fake/skills/caveman/SKILL.md", retry_call["options"].get("skills", []))

    def test_round_workflow_warning_state_persists_across_rounds(self) -> None:
        # Round 1 has unavailable skill and emits warning
        caveman_round1 = {
            "preference": True,
            "active": False,
            "warning": "Warning: Caveman lite unavailable",
            "warned": False,
        }
        args1 = {**self.base_args, "caveman": caveman_round1, "isLastRound": False}
        out1 = run_workflow_with_recorder("round-workflow.md", args1)
        res_caveman = out1["result"]["caveman"]
        self.assertTrue(res_caveman["warned"])

        # Round 2 uses persisted warned state, so no repeated warning is emitted
        res_caveman["warning"] = None
        args2 = {**self.base_args, "caveman": res_caveman, "round": 2, "isFirstRound": False, "isLastRound": True}
        out2 = run_workflow_with_recorder("round-workflow.md", args2)
        self.assertIsNone(out2["result"]["caveman"].get("warning"))


if __name__ == "__main__":
    unittest.main()

