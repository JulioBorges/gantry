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
HOOKS_DIR = SKILL_DIR / "hooks" / "git"

sys.path.insert(0, str(SCRIPTS))
import discovery  # noqa: E402
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


from common import parse_issue


class WorkflowTestBase(unittest.TestCase):
    def run_script(self, root: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_issue(
        self,
        root: Path,
        ref: str,
        status: str,
        blockers: list[str] | None = None,
        criteria: list[str] | None = None,
    ) -> Path:
        slug, number = ref.split("#")
        path = root / ".scratch" / slug / "issues" / f"{int(number):02d}-example.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        blocked_by = "\n".join(f"- `{blocker}` — prerequisite" for blocker in blockers or []) or "- None"
        acceptance_criteria = "\n".join(f"- [ ] {criterion}" for criterion in criteria or ["exposes a deterministic behaviour"])
        path.write_text(
            f"""# Example {ref}

Type: issue
Status: {status}
Slice: `{ref}`
Spec: `.scratch/{slug}/spec.md`
Created: 2026-09-13

## Parent

`{slug}`

## What to build

Preserve the portable workflow contract.

## Acceptance criteria

{acceptance_criteria}

## Blocked by

{blocked_by}

## Comments
""",
            encoding="utf-8",
        )
        return path

    def write_roadmap(self, root: Path) -> Path:
        roadmap = root / "ROADMAP.md"
        roadmap.write_text(
            """# Roadmap

| Metric | Value |
|---|---|
| Issues completed | **0 / 0** |
| Specs completed | **0 / 0** |
| Execution waves | **0** |

<!-- BEGIN GENERATED: spec progress -->

<!-- END GENERATED: spec progress -->

<!-- BEGIN GENERATED: issue checklist -->

<!-- END GENERATED: issue checklist -->
""",
            encoding="utf-8",
        )
        return roadmap

    def critic_evidence(self, root: Path, issue: Path) -> list[dict[str, object]]:
        accepted = self.run_script(root, "acceptance.py", str(issue), "--json")
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        return [
            {
                "index": criterion["index"],
                "met": True,
                "evidence": f"real test evidence for criterion {criterion['index']}",
            }
            for criterion in json.loads(accepted.stdout)["criteria"]
        ]

    def read_run_log_events(self, state_root: Path, unit_id: str, run_id: str) -> list[dict]:
        path = state_root / unit_id / "runs" / f"{run_id}.jsonl"
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)
        subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)

    def run_workflow(self, filename: str, args: dict) -> dict:
        source = (SKILL_DIR / "reference" / filename).read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
        source = source.replace("export const meta", "const meta", 1)
        driver = f"""
import {{ mkdirSync, writeFileSync }} from 'node:fs';
import {{ dirname }} from 'node:path';
import {{ spawnSync }} from 'node:child_process';
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {json.dumps(args)};
const calls = [];
const commandCalls = [];
let sequence = 0;
const defaultIssueWorktree = args.issueWorktree || (
  args.isolate && args.issues && args.issues[0]
    ? `${{args.repoRoot}}.gantry-${{args.issues[0].ref.replace('#', '-') }}`
    : args.repoRoot
);
const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd || args.repoRoot, sequence: sequence++ }});
  if (command.includes('/spec.py') && args.stubSpecCheck !== false) {{
    return {{ exitCode: 0, stdout: '{{"valid":true}}', stderr: '' }};
  }}
  if (args.commandMode === 'real') {{
    const completed = spawnSync(command, {{
      cwd: options.cwd || args.repoRoot, shell: true, encoding: 'utf8', input: options.input,
    }});
    return {{
      exitCode: completed.status ?? 1, stdout: completed.stdout || '',
      stderr: completed.stderr || '',
    }};
  }}
  if (args.commandResults && args.commandResults.length) return args.commandResults.shift();
  if (command.includes('/common.py')) return {{ exitCode: 0, stdout: JSON.stringify({{ issueBranch: args.issueBranch || args.branch }}) }};
  if (command === 'git branch --show-current') return {{ exitCode: 0, stdout: args.issueBranch || args.branch }};
  return {{ exitCode: 0, stdout: command.includes('/gates.py') ? '{{"verdict":"pass"}}'
    : command.includes('/spec.py') ? '{{"valid":true}}' : '' }};
}};
const agent = async (prompt, options) => {{
  calls.push({{ label: options.label, prompt, schema: options.schema, cwd: options.cwd, sequence: sequence++ }});
  if (options.label.startsWith('research:')) return 'factual research';
  if (options.label.startsWith('requirement-critic')) {{
    if (args.requirementCriticRawResults && args.requirementCriticRawResults.length) {{
      return args.requirementCriticRawResults.shift();
    }}
    if (args.requirementCriticResult) return args.requirementCriticResult;
    return {{ blocking: [], findings: [] }};
  }}
  if (options.label.startsWith('plan')) {{
    if (args.plannerRawResults && args.plannerRawResults.length) {{
      return args.plannerRawResults.shift();
    }}
    if (args.plannerResult) return args.plannerResult;
    return {{ filesWritten: [], issues: [], roadmapAdditions: [], openDecisions: [] }};
  }}
  if (options.label.startsWith('critique')) {{
    return {{ acceptable: true, problems: [], frontierErrors: [] }};
  }}
  if (options.label.startsWith('implement:')) {{
    if (args.implementerRawResults && args.implementerRawResults.length) {{
      return args.implementerRawResults.shift();
    }}
    if (args.implementerCommitText) {{
      writeFileSync(`${{options.cwd}}/delivery.txt`, args.implementerCommitText);
      const added = spawnSync('git', ['add', 'delivery.txt'], {{ cwd: options.cwd, encoding: 'utf8' }});
      const committed = spawnSync('git', ['commit', '--quiet', '-m', 'delivery'], {{ cwd: options.cwd, encoding: 'utf8' }});
      if (added.status !== 0 || committed.status !== 0) throw new Error(added.stderr || committed.stderr);
    }}
    const ref = options.label.split(':')[1];
    const assigned = (args.issueAssignments && args.issueAssignments[ref]) || {{}};
    return {{
      worktree: assigned.worktree || defaultIssueWorktree, branch: assigned.branch || args.issueBranch || args.branch,
      commits: ['test commit'],
      summary: 'workflow execution', testsAdded: [], gatesResult: 'verdict: pass',
      decisions: [], blockers: [],
    }};
  }}
  if (options.label.startsWith('review:')) return {{
    blocking: [], nonBlocking: [], summary: 'no findings',
  }};
  if (options.label.startsWith('critic:') && args.criticRawResults && args.criticRawResults.length) {{
    return args.criticRawResults.shift();
  }}
  if (options.label.startsWith('critic:')) return {{
    complete: true, criteria: [], gatesVerdict: 'pass', gateResult: {{ verdict: 'pass' }}, gateFailures: [],
    refutations: [], requiredFixes: [], decisionsForOperator: [],
    ...(args.criticResults && args.criticResults.length ? args.criticResults.shift() : (args.criticResult || {{}})),
  }};
  return null;
}};
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
const phase = () => {{}};
const log = () => {{}};
let result = null;
let error = null;
try {{
  result = await new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'runCommand', source)(
    args, agent, parallel, pipeline, phase, log, runCommand,
  );
}} catch (err) {{
  error = err && err.message ? err.message : String(err);
}}
process.stdout.write(JSON.stringify({{ result, calls, commandCalls, error }}));
"""
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", driver],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)


class RoleExecutionRecoveryAndPauseContractTests(WorkflowTestBase):
    def test_two_issue_workflow_pauses_failed_execution_preserves_worktree_and_integrates_accepted_issue(self) -> None:
        """A two-Issue workflow pauses one failed execution, preserves its worktree, and allows the independent accepted Issue to integrate."""
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue_one = self.write_issue(root, "rec#01", "ready-for-agent")
            issue_two = self.write_issue(root, "rec#02", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            run_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            worktree_one = Path(f"{root}.gantry-rec-01")
            worktree_two = Path(f"{root}.gantry-rec-02")
            state_root = Path(state_dir)
            unit_id = "123456abcdef"
            run_id = "run-recovery-1"

            try:
                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [
                            {"ref": "rec#01", "path": str(issue_one.relative_to(root)), "title": "Recovery one", "specPath": ".scratch/rec/spec.md"},
                            {"ref": "rec#02", "path": str(issue_two.relative_to(root)), "title": "Recovery two", "specPath": ".scratch/rec/spec.md"},
                        ],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "recordRoleSelection": True,
                        "branch": run_branch,
                        "baseRef": base_ref,
                        "isolate": True,
                        "correctionBudget": 2,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                        "paths": {},
                        "date": "2026-09-16",
                        "commandMode": "real",
                        "runId": run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "implementerCommitText": "integrated\n",
                        "issueAssignments": {
                            "rec#01": {"worktree": str(worktree_one), "branch": "gantry/rec-01"},
                            "rec#02": {"worktree": str(worktree_two), "branch": "gantry/rec-02"},
                        },
                        "issueExecutionUnavailable": {
                            "rec#02": "critic",
                        },
                        "criticResults": [
                            {"criteria": self.critic_evidence(root, issue_one)},
                        ],
                    },
                )

                self.assertIsNone(run["error"], run["error"])
                outcomes = {res["ref"]: res["outcome"] for res in run["result"]["results"]}
                # Independent accepted Issue integrates
                self.assertEqual("done", outcomes["rec#01"])
                self.assertEqual("done", parse_issue(issue_one).status)
                # Failed execution pauses and preserves worktree
                self.assertEqual("paused", outcomes["rec#02"])
                self.assertEqual("ready-for-agent", parse_issue(issue_two).status)
                self.assertTrue(worktree_two.is_dir(), "Failed execution worktree must be preserved")

                # Authoritative completion in ROADMAP.md
                roadmap_text = (root / "ROADMAP.md").read_text(encoding="utf-8")
                self.assertIn("- [x] **`rec#01`**", roadmap_text)
                self.assertIn("- [ ] **`rec#02`**", roadmap_text)

                # Next round is blocked
                self.assertTrue(run["result"]["nextRoundBlocked"])

                # Run log events
                events = self.read_run_log_events(state_root, unit_id, run_id)
                done_events = [e for e in events if e.get("event") == "issue.done"]
                self.assertEqual(1, len(done_events))
                self.assertEqual("rec#01", done_events[0]["issue"])

                paused_events = [e for e in events if e.get("event") == "issue.paused"]
                self.assertEqual(1, len(paused_events))
                self.assertEqual("rec#02", paused_events[0]["issue"])
                self.assertEqual("critic", paused_events[0]["data"]["role"])
                self.assertEqual("execution_unavailable", paused_events[0]["data"]["reason"])

                # Selection event was recorded
                sel_events = [e for e in events if e.get("event") == "role.selected"]
                self.assertTrue(len(sel_events) > 0)
                rec2_critic_sel = next(e for e in sel_events if e.get("issue") == "rec#02" and e["data"]["role"] == "critic")
                self.assertEqual("critic", rec2_critic_sel["data"]["role"])
                self.assertIn("effective", rec2_critic_sel["data"])

            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree_one)], cwd=root, check=False)
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree_two)], cwd=root, check=False)

    def test_workflow_blocks_next_round_until_explicit_recovery_without_fallback(self) -> None:
        """The workflow blocks the next round until explicit recovery; no automatic fallback or automatic retry substitutes a selection."""
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            issue_two = self.write_issue(root, "rec#02", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            run_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "123456abcdef"
            run_id = "run-recovery-2"
            log_dir = state_root / unit_id / "runs"
            log_dir.mkdir(parents=True)
            log_path = log_dir / f"{run_id}.jsonl"
            # Simulate prior round with paused issue
            log_path.write_text(
                json.dumps({"ts": "2026-09-16T00:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root), "policyHash": "12345678", "tier": "reference", "staleAfterSeconds": 900}}) + "\n"
                + json.dumps({"ts": "2026-09-16T00:00:01Z", "run": run_id, "event": "round.started", "data": {"round": 1}}) + "\n"
                + json.dumps({"ts": "2026-09-16T00:00:02Z", "run": run_id, "event": "issue.paused", "issue": "rec#02", "data": {"role": "critic", "reason": "execution_unavailable"}}) + "\n"
                + json.dumps({"ts": "2026-09-16T00:00:03Z", "run": run_id, "event": "round.finished", "data": {"round": 1}}) + "\n",
                encoding="utf-8",
            )

            # Round 2 invoked without explicit recovery
            round2 = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 2,
                    "isFirstRound": False,
                    "issues": [
                        {"ref": "rec#02", "path": str(issue_two.relative_to(root)), "title": "Recovery two", "specPath": ".scratch/rec/spec.md"},
                    ],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": run_branch,
                    "baseRef": base_ref,
                    "isolate": True,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-16",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                },
            )

            self.assertIsNone(round2["error"])
            self.assertTrue(round2["result"]["blocked"])
            self.assertTrue(round2["result"]["nextRoundBlocked"])
            self.assertEqual("unresolved_execution_failure", round2["result"]["reason"])
            # Verify no agents were called and no fallback occurred
            self.assertEqual(0, len(round2["calls"]))

    def test_issue_role_replacement_validated_and_logged_without_altering_defaults_and_preserves_spent_budget(self) -> None:
        """Issue-role replacement is validated and logged, does not alter saved defaults or active agents, and preserves spent correction budget."""
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "rec#02", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")

            # Setup repository defaults in tracked .gantry/config.json
            gantry_dir = root / ".gantry"
            gantry_dir.mkdir()
            config_file = gantry_dir / "config.json"
            initial_config = {
                "execution": {
                    "roles": {
                        "critic": {"harness": "codex", "model": "gpt-5.2-codex"},
                    }
                }
            }
            config_file.write_text(json.dumps(initial_config, indent=2), encoding="utf-8")

            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            run_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "123456abcdef"
            run_id = "run-recovery-3"
            log_dir = state_root / unit_id / "runs"
            log_dir.mkdir(parents=True)
            log_path = log_dir / f"{run_id}.jsonl"
            log_path.write_text(
                json.dumps({"ts": "2026-09-16T00:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root), "policyHash": "12345678", "tier": "reference", "staleAfterSeconds": 900}}) + "\n"
                + json.dumps({"ts": "2026-09-16T00:00:01Z", "run": run_id, "event": "round.started", "data": {"round": 1}}) + "\n"
                + json.dumps({"ts": "2026-09-16T00:00:02Z", "run": run_id, "event": "issue.paused", "issue": "rec#02", "data": {"role": "critic", "reason": "execution_unavailable"}}) + "\n"
                + json.dumps({"ts": "2026-09-16T00:00:03Z", "run": run_id, "event": "round.finished", "data": {"round": 1}}) + "\n",
                encoding="utf-8",
            )

            # 1. Invalid replacement is rejected
            invalid_run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 2,
                    "isFirstRound": False,
                    "issues": [
                        {"ref": "rec#02", "path": str(issue.relative_to(root)), "title": "Recovery two", "specPath": ".scratch/rec/spec.md"},
                    ],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": run_branch,
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-16",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "issueRoleReplacements": {
                        "rec#02": {
                            "critic": {"harness": "unsupported_harness", "model": "m1"},
                        },
                    },
                },
            )
            self.assertTrue(invalid_run["result"]["blocked"])
            self.assertEqual("invalid_role_replacement", invalid_run["result"]["reason"])

            # 2. Valid replacement proceeds, logs role.changed, preserves spent corrections and saved defaults
            valid_run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 2,
                    "isFirstRound": False,
                    "isLastRound": True,
                    "issues": [
                        {"ref": "rec#02", "path": str(issue.relative_to(root)), "title": "Recovery two", "specPath": ".scratch/rec/spec.md"},
                    ],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": run_branch,
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-16",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "priorRun": {
                        "run": run_id,
                        "issue": "rec#02",
                        "worktree": str(root),
                        "branch": run_branch,
                        "correctionsSpent": 1,
                    },
                    "issueRoleReplacements": {
                        "rec#02": {
                            "critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
                        },
                    },
                    "criticResult": {
                        "complete": True,
                        "criteria": self.critic_evidence(root, issue),
                        "gatesVerdict": "pass",
                        "gateResult": {"verdict": "pass", "requirements": []},
                    },
                },
            )

            self.assertIsNone(valid_run["error"], valid_run["error"])
            self.assertEqual("done", valid_run["result"]["results"][0]["outcome"])

            # Verify saved defaults in .gantry/config.json were NOT mutated
            self.assertEqual(initial_config, json.loads(config_file.read_text(encoding="utf-8")))

            # Verify role.changed was logged
            events = self.read_run_log_events(state_root, unit_id, run_id)
            role_changed = next(e for e in events if e.get("event") == "role.changed")
            self.assertEqual("rec#02", role_changed["issue"])
            self.assertEqual("critic", role_changed["data"]["role"])
            self.assertEqual("claude-code", role_changed["data"]["effective"]["harness"])
            self.assertEqual("claude-3-7-sonnet-20250219", role_changed["data"]["effective"]["model"])

            # Verify spent budget was preserved (started at 1, so outcome carries corrections=1)
            self.assertEqual(1, valid_run["result"]["results"][0]["corrections"])

    def test_runlog_selection_and_change_events_contain_identity_and_evidence_without_secrets(self) -> None:
        """Run Log selection and change events contain Issue/role identity and selection evidence without secrets or raw command output."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_id = "run-events-1"
            unit_id = "112233445566"
            log_dir = root / unit_id / "runs"
            log_dir.mkdir(parents=True)
            log_path = log_dir / f"{run_id}.jsonl"

            # Valid role.selected event
            valid_sel = {
                "ts": "2026-09-16T12:00:00Z",
                "run": run_id,
                "event": "role.selected",
                "issue": "sample#01",
                "data": {
                    "role": "critic",
                    "issue": "sample#01",
                    "requested": {"harness": "antigravity", "model": "gemini-3.1-pro-high", "effort": "high"},
                    "effective": {"harness": "antigravity", "model": "gemini-3.1-pro-high", "effort": "high"},
                    "evidence": {"source": "issue_override"},
                },
            }
            validated_sel = runlog.validate_event(valid_sel)
            self.assertEqual("sample#01", validated_sel["issue"])
            self.assertEqual("critic", validated_sel["data"]["role"])
            runlog.append_event(log_path, validated_sel)

            # Valid role.changed event
            valid_chg = {
                "ts": "2026-09-16T12:05:00Z",
                "run": run_id,
                "event": "role.changed",
                "issue": "sample#01",
                "data": {
                    "role": "critic",
                    "issue": "sample#01",
                    "previous": {"harness": "codex", "model": "gpt-5.2-codex"},
                    "requested": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                    "effective": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                    "evidence": {"source": "explicit_recovery"},
                },
            }
            validated_chg = runlog.validate_event(valid_chg)
            self.assertEqual("sample#01", validated_chg["issue"])
            self.assertEqual("critic", validated_chg["data"]["role"])
            runlog.append_event(log_path, validated_chg)

            # Rejection of prohibited tokens (command, output, diff, secrets)
            bad_events = [
                {
                    "ts": "2026-09-16T12:00:00Z",
                    "run": run_id,
                    "event": "role.selected",
                    "issue": "sample#01",
                    "data": {
                        "role": "critic",
                        "requested": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "effective": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "command": "agy --print",  # prohibited!
                    },
                },
                {
                    "ts": "2026-09-16T12:00:00Z",
                    "run": run_id,
                    "event": "role.selected",
                    "issue": "sample#01",
                    "data": {
                        "role": "critic",
                        "requested": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "effective": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "output": "raw output from cli",  # prohibited!
                    },
                },
                {
                    "ts": "2026-09-16T12:00:00Z",
                    "run": run_id,
                    "event": "role.changed",
                    "issue": "sample#01",
                    "data": {
                        "role": "critic",
                        "requested": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "effective": {"harness": "antigravity", "model": "gemini-3.8-flash-medium"},
                        "diff": "patch content",  # prohibited!
                    },
                },
            ]
            for bad in bad_events:
                with self.assertRaises(runlog.EventError):
                    runlog.validate_event(bad)

    def test_codex_capability_declares_supported_tier_and_context_windows(self) -> None:
        """AC1: capabilities/codex.json declares tier: supported, per_role_model: true, and model context windows."""
        cap_file = SKILL_DIR / "capabilities" / "codex.json"
        self.assertTrue(cap_file.exists(), "capabilities/codex.json must exist")
        cap = json.loads(cap_file.read_text(encoding="utf-8"))
        self.assertEqual("supported", cap.get("tier"))
        self.assertTrue(cap.get("per_role_model"))
        models = cap.get("models", {})
        self.assertIn("gpt-5.2-codex", models)
        self.assertEqual(272000, models["gpt-5.2-codex"]["contextWindow"])

    def test_codex_discovery_extracts_version_and_enumerates_models_with_caching_and_error_handling(self) -> None:
        """AC2: discovery.py discovers codex CLI, extracts version, and parses codex models output with caching."""
        discovery.clear_discovery_cache()

        class MockCodexRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                if "--version" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, stdout="codex-cli 0.154.0\n", stderr="")
                elif "models" in cmd:
                    raw_models = "gpt-5.2-codex   GPT-5.2 Codex (Default)\ngpt-5-codex     GPT-5 Codex\n"
                    return subprocess.CompletedProcess(cmd, 0, stdout=raw_models, stderr="")
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown command")

        runner = MockCodexRunner()
        version = discovery.get_codex_version(runner=runner)
        self.assertEqual("0.154.0", version)

        models = discovery.discover_codex_models(runner=runner, use_cache=False)
        model_ids = [m["id"] for m in models]
        self.assertIn("gpt-5.2-codex", model_ids)
        self.assertIn("gpt-5-codex", model_ids)
        gpt52 = next(m for m in models if m["id"] == "gpt-5.2-codex")
        self.assertEqual(272000, gpt52.get("contextWindow"))

        # Discovery error when codex CLI not found
        with patch("shutil.which", return_value=None):
            with self.assertRaises(discovery.DiscoveryError) as ctx:
                discovery.discover_codex_models(runner=None)
            self.assertIn("codex cli not found in path", str(ctx.exception).lower())

        # Discovery error when codex models fails
        class FailingModelsRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="API connection refused")

        with self.assertRaises(discovery.DiscoveryError) as ctx:
            discovery.discover_codex_models(runner=FailingModelsRunner(), use_cache=False)
        self.assertIn("codex models returned exit code 1", str(ctx.exception))

    def test_codex_preflight_validation_succeeds_when_authenticated_fails_with_remediation(self) -> None:
        """AC3: execution.preflight_validate() succeeds when authenticated and fails with 'codex login' remediation when unauthenticated or missing."""
        policy = {
            "execution": {
                "roles": {
                    "implement": {"harness": "codex", "model": "gpt-5.2-codex"},
                    "critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"},
                }
            }
        }

        # 1. Successful authentication
        class AuthenticatedRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                if cmd[0] == "codex":
                    if "--version" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="0.154.0\n", stderr="")
                    elif "login" in cmd and "status" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="Logged in using ChatGPT\n", stderr="")
                if "--version" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, stdout="1.2.4\n", stderr="")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        res = execution.preflight_validate(policy=policy, check_auth=True, runner=AuthenticatedRunner())
        self.assertTrue(res["valid"], f"Expected preflight to succeed: {res.get('errors')}")

        # 2. Unauthenticated codex returns error with 'codex login'
        class UnauthenticatedRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                if cmd[0] == "codex":
                    if "--version" in cmd:
                        return subprocess.CompletedProcess(cmd, 0, stdout="0.154.0\n", stderr="")
                    elif "login" in cmd and "status" in cmd:
                        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Not logged in")
                if "--version" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, stdout="1.2.4\n", stderr="")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        res_unauth = execution.preflight_validate(policy=policy, check_auth=True, runner=UnauthenticatedRunner())
        self.assertFalse(res_unauth["valid"])
        self.assertTrue(any("codex login" in err for err in res_unauth["errors"]), f"Errors should mention 'codex login': {res_unauth['errors']}")

        # 3. Missing codex binary returns actionable remediation
        with patch("shutil.which", return_value=None):
            res_missing = execution.preflight_validate(policy=policy, check_auth=True, runner=None)
            self.assertFalse(res_missing["valid"])
            self.assertTrue(any("codex" in err.lower() and "not found on path" in err.lower() for err in res_missing["errors"]), f"Errors should mention binary on PATH: {res_missing['errors']}")

    def test_existing_harnesses_preflight_and_discovery_have_no_regression(self) -> None:
        """AC4: Existing harnesses (antigravity, claude-code, opencode) remain valid without regression."""
        for harness, model in [
            ("antigravity", "gemini-3.8-flash-medium"),
            ("claude-code", "claude-3-7-sonnet-20250219"),
            ("opencode", "claude-3-7-sonnet-20250219"),
        ]:
            policy = {"execution": {"roles": {"plan": {"harness": harness, "model": model}}}}
            res = execution.preflight_validate(policy=policy, check_auth=False)
            self.assertTrue(res["valid"], f"Preflight failed for {harness}: {res.get('errors')}")


class CodexHostOrchestrationAndDispatchTests(unittest.TestCase):
    def test_codex_build_dispatch_command_with_and_without_effort(self) -> None:
        """AC2: build_dispatch_command handles codex exec with and without reasoning effort."""
        cmd_standard = execution.build_dispatch_command("codex", "gpt-5.2-codex", "Implement feature")
        self.assertEqual(["codex", "exec", "Implement feature", "--model", "gpt-5.2-codex"], cmd_standard)

        cmd_effort = execution.build_dispatch_command("codex", "gpt-5.2-codex", "Implement feature", effort="high")
        self.assertEqual(["codex", "exec", "Implement feature", "--model", "gpt-5.2-codex", "--effort", "high"], cmd_effort)

    def test_bounded_dispatch_timeout_and_error_isolation(self) -> None:
        """AC2: execution runners isolate timeouts and subprocess errors as ExecutionFailureError."""
        # 1. Timeout isolation
        class TimeoutRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                if "--version" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, stdout="0.154.0\n", stderr="")
                raise subprocess.TimeoutExpired(cmd, timeout=kwargs.get("timeout", 5))

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            with self.assertRaises(execution.ExecutionFailureError) as ctx:
                execution.dispatch_role(
                    role="implementer",
                    prompt="implement",
                    cwd=cwd,
                    selection={"harness": "codex", "model": "gpt-5.2-codex"},
                    runner=TimeoutRunner(),
                    timeout=5,
                )
            self.assertIn("timed out after 5", str(ctx.exception))

        # 2. Non-zero exit code error isolation
        class FailingRunner:
            def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                if "--version" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, stdout="0.154.0\n", stderr="")
                return subprocess.CompletedProcess(cmd, 127, stdout="", stderr="command terminated abnormally")

        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            with self.assertRaises(execution.ExecutionFailureError) as ctx:
                execution.dispatch_role(
                    role="implementer",
                    prompt="implement",
                    cwd=cwd,
                    selection={"harness": "codex", "model": "gpt-5.2-codex"},
                    runner=FailingRunner(),
                )
            self.assertIn("exit 127", str(ctx.exception))
            self.assertIn("command terminated abnormally", str(ctx.exception))

        # 3. CLI help accepts --timeout
        cli_check = subprocess.run(
            [sys.executable, str(EXECUTION_SCRIPT), "dispatch", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cli_check.returncode)
        self.assertIn("--timeout", cli_check.stdout)

    def test_robust_result_contract_parsing_markdown_and_delimiters(self) -> None:
        """AC3: Role results returned from codex exec conform to result.py contracts, with robust parsing for markdown and JSON delimiters."""
        valid_implementer_dict = {
            "worktree": "/mock/worktree",
            "branch": "feat-1",
            "commits": ["sha1"],
            "summary": "Implemented feature cleanly",
            "testsAdded": ["tests/test_feat.py"],
            "gatesResult": "pass",
            "decisions": [],
            "blockers": [],
        }

        # Case A: Plain JSON
        plain_json = json.dumps(valid_implementer_dict)
        res_plain = execution.parse_and_validate_result("implementer", plain_json)
        self.assertEqual("Implemented feature cleanly", res_plain["summary"])

        # Case B: Standard markdown code fence ```json ... ```
        fenced_json = f"```json\n{json.dumps(valid_implementer_dict, indent=2)}\n```"
        res_fenced = execution.parse_and_validate_result("implementer", fenced_json)
        self.assertEqual("Implemented feature cleanly", res_fenced["summary"])

        # Case C: Uppercase ```JSON ... ``` with commentary before and after
        messy_output = (
            "I have finished executing the implementer role.\n\n"
            f"```JSON\n{json.dumps(valid_implementer_dict, indent=2)}\n```\n\n"
            "All unit tests and differential gates are passing."
        )
        res_messy = execution.parse_and_validate_result("implementer", messy_output)
        self.assertEqual("Implemented feature cleanly", res_messy["summary"])

        # Case D: 4 backticks ````json ... ````
        quad_backticks = f"````json\n{json.dumps(valid_implementer_dict)}\n````"
        res_quad = execution.parse_and_validate_result("implementer", quad_backticks)
        self.assertEqual("Implemented feature cleanly", res_quad["summary"])

        # Case E: Embedded JSON object surrounded by conversational text without fences
        embedded_prose = f"The resulting contract is: {json.dumps(valid_implementer_dict)} - verified."
        res_embedded = execution.parse_and_validate_result("implementer", embedded_prose)
        self.assertEqual("Implemented feature cleanly", res_embedded["summary"])

        # Case F: CLI test with piped input containing markdown code fences
        cli_proc = subprocess.run(
            [sys.executable, str(RESULT_SCRIPT), "--role", "implementer", "--json"],
            input=messy_output,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cli_proc.returncode, cli_proc.stderr)
        cli_result = json.loads(cli_proc.stdout)
        self.assertTrue(cli_result["valid"])

    def test_simulated_codex_host_run_with_cross_harness_critic_and_invariant_defense(self) -> None:
        """AC4: Simulated Codex host run with cross-harness Critic; verifies refusal when prompt invariants or git hooks are violated."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # Initialize git repo
            subprocess.run(["git", "init", "--quiet", "--initial-branch=main"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "codex@host.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Codex Host"], cwd=root, check=True)
            subprocess.run(["git", "config", "core.hooksPath", str(HOOKS_DIR)], cwd=root, check=True)

            # Seed runlog
            run_id = "run-20260920T150000Z-codex"
            unit_id = runlog.unit_id(root)
            state_root = root / "state"
            state_root.mkdir()
            log_dir = state_root / unit_id / "runs"
            log_dir.mkdir(parents=True)
            log_path = log_dir / f"{run_id}.jsonl"
            log_path.write_text(
                json.dumps({"ts": "2026-09-20T15:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root)}}) + "\n",
                encoding="utf-8",
            )

            # Mark worktree
            subprocess.run([sys.executable, str(SCRIPTS / "runlog.py"), "mark", run_id, "--cwd", str(root), "--state-root", str(state_root)], cwd=root, check=True)

            # Commit initial baseline
            (root / "README.md").write_text("# Initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "initial commit"], cwd=root, check=True)

            # 1. Test Git Hook Invariant Defense: Reject test-skip
            # An implementer attempting to commit a test-skip (e.g. it.skip or test.skip) is blocked by git pre-commit hook
            (root / "test_sample.js").write_text("describe('sample', () => { it.skip('skipped test', () => {}); });\n", encoding="utf-8")
            subprocess.run(["git", "add", "test_sample.js"], cwd=root, check=True)
            proc_commit = subprocess.run(
                ["git", "commit", "-m", "commit with test skip"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc_commit.returncode)
            self.assertIn("deny", proc_commit.stderr.lower())

            # Reset staging
            subprocess.run(["git", "reset", "--hard", "--quiet", "HEAD"], cwd=root, check=True)

            # 2. Test Adversarial Cross-Harness Critic Refusal:
            # Implementer returns incomplete work claiming complete=true without gates pass
            fraudulent_critic_summary = {
                "complete": True,
                "gatesVerdict": "pass",
                "gateResult": {"verdict": "fail", "requirements": ["unresolved compilation error"]},
                "gateFailures": ["make: syntax error"],
                "criteria": [{"index": 1, "met": True, "evidence": "claimed passing without test"}],
                "refutations": [],
                "requiredFixes": [],
                "decisionsForOperator": [],
            }
            with self.assertRaises(execution.ProtocolFailureError) as ctx:
                execution.verify_critic_result(fraudulent_critic_summary)
            self.assertIn("gateResult verdict is 'fail'", str(ctx.exception))

            # 3. Test Adversarial Cross-Harness Critic Verification: Valid delivery accepted
            valid_critic_verdict = {
                "complete": True,
                "gatesVerdict": "pass",
                "gateResult": {"verdict": "pass", "requirements": []},
                "gateFailures": [],
                "criteria": [
                    {"index": 1, "met": True, "evidence": "Verified all tests passed in test_role_execution_dispatch.py"},
                    {"index": 2, "met": True, "evidence": "Verified preflight validation passes for Codex"},
                ],
                "refutations": [],
                "requiredFixes": [],
                "decisionsForOperator": [],
            }
            # verify_critic_result passes without raising
            execution.verify_critic_result(valid_critic_verdict)


if __name__ == "__main__":
    unittest.main()

