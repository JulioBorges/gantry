#!/usr/bin/env python3
"""Public-contract tests for the canonical Gantry workflow skill."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common import parse_issue  # noqa: E402


class CanonicalGantryWorkflowTests(unittest.TestCase):
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
    if (args.testDraftPath) {{
      mkdirSync(dirname(args.testDraftPath), {{ recursive: true }});
      writeFileSync(args.testDraftPath, args.testDraftText);
      return {{
        filesWritten: [args.testDraftPath], issues: [{{ ref: 'planned#01', path: args.testDraftPath,
          title: 'Planned Issue', criteriaCount: 1, blockedBy: [] }}],
        roadmapAdditions: ['- [ ] **`planned#01`** — Planned Issue'], openDecisions: [],
      }};
    }}
    return {{ filesWritten: [], issues: [], roadmapAdditions: [], openDecisions: [] }};
  }}
  if (options.label.startsWith('critique')) {{
    if (args.planCriticRawResults && args.planCriticRawResults.length) {{
      return args.planCriticRawResults.shift();
    }}
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

    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)

    def test_result_contract_cli_rejects_missing_critic_criteria_and_accepts_large_result(self) -> None:
        missing = subprocess.run(
            [sys.executable, str(SCRIPTS / "result.py"), "--role", "critic", "--json"],
            input='{"complete": false}',
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, missing.returncode)
        self.assertIn("criteria", missing.stdout)

        valid_payload = {
            "complete": False,
            "criteria": [{"index": 1, "met": False, "evidence": "x" * 200_000}],
            "gatesVerdict": "fail",
            "gateResult": {"verdict": "fail", "checks": []},
            "gateFailures": ["a declared gate failed"],
            "refutations": ["criterion one remains unproven"],
            "requiredFixes": ["add a real proof"],
            "decisionsForOperator": [],
        }
        started = time.monotonic()
        valid = subprocess.run(
            [sys.executable, str(SCRIPTS / "result.py"), "--role", "critic", "--json"],
            input=json.dumps(valid_payload),
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        elapsed = time.monotonic() - started
        self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
        self.assertLess(elapsed, 1)

        missing_gate_verdict = subprocess.run(
            [sys.executable, str(SCRIPTS / "result.py"), "--role", "critic", "--json"],
            input=json.dumps({**valid_payload, "gateResult": {"checks": []}}),
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, missing_gate_verdict.returncode)
        self.assertIn("gateResult.verdict", missing_gate_verdict.stdout)

        invalid_verdict = subprocess.run(
            [sys.executable, str(SCRIPTS / "result.py"), "--role", "critic", "--json"],
            input=json.dumps({**valid_payload, "gatesVerdict": "green"}),
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, invalid_verdict.returncode)
        self.assertIn("gatesVerdict", invalid_verdict.stdout)

        help_result = self.run_script(REPO_ROOT, "result.py", "--help")
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertIn("usage:", help_result.stdout.lower())

    def test_result_schemas_use_the_supported_subset_for_every_role(self) -> None:
        roles = ("requirement-critic", "planner", "plan-critic", "implementer", "reviewer", "critic", "learner")
        supported = {"type", "properties", "required", "items", "enum", "additionalProperties"}
        required_fields = {
            "requirement-critic": {"blocking", "findings"},
            "planner": {"filesWritten", "issues", "roadmapAdditions", "openDecisions"},
            "plan-critic": {"acceptable", "problems", "frontierErrors"},
            "implementer": {"worktree", "branch", "commits", "summary", "testsAdded", "gatesResult", "decisions", "blockers"},
            "reviewer": {"blocking", "nonBlocking", "summary"},
            "critic": {"complete", "criteria", "gatesVerdict", "gateResult", "gateFailures", "refutations", "requiredFixes", "decisionsForOperator"},
            "learner": {"candidates"},
        }

        def validate_schema(schema: object, allow_open_object: bool = False) -> None:
            self.assertIsInstance(schema, dict)
            if schema.get("type") == "object":
                self.assertEqual(set(schema["properties"]), set(schema["required"]))
                self.assertEqual(allow_open_object, schema["additionalProperties"])
            for key, value in schema.items():
                self.assertIn(key, supported)
                if key == "properties":
                    self.assertIsInstance(value, dict)
                    for name, nested in value.items():
                        validate_schema(nested, allow_open_object=name == "gateResult")
                elif key == "items":
                    validate_schema(value)

        for role in roles:
            with self.subTest(role=role):
                path = SKILL_DIR / "schemas" / f"{role}.json"
                self.assertTrue(path.is_file())
                schema = json.loads(path.read_text(encoding="utf-8"))
                validate_schema(schema)
                self.assertEqual(required_fields[role], set(schema["required"]))
        critic = json.loads((SKILL_DIR / "schemas" / "critic.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["pass", "fail", "no_gates", "not_run"],
            critic["properties"]["gatesVerdict"]["enum"],
        )

    def test_result_contracts_reject_empty_nested_workflow_objects(self) -> None:
        invalid_results = {
            "planner": {
                "filesWritten": [],
                "issues": [{}],
                "roadmapAdditions": [],
                "openDecisions": [],
            },
            "plan-critic": {
                "acceptable": False,
                "problems": [{}],
                "frontierErrors": [],
            },
            "reviewer": {
                "blocking": [{}],
                "nonBlocking": [],
                "summary": "review completed",
            },
            "critic": {
                "complete": False,
                "criteria": [{}],
                "gatesVerdict": "fail",
                "gateFailures": [],
                "refutations": [],
                "requiredFixes": [],
                "decisionsForOperator": [],
            },
            "learner": {"candidates": [{}]},
        }
        for role, payload in invalid_results.items():
            with self.subTest(role=role):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / "result.py"), "--role", role, "--json"],
                    input=json.dumps(payload),
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn("missing required field", result.stdout)

    def test_skill_frontmatter_and_canonical_script_cli_contracts(self) -> None:
        skill = SKILL_DIR / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        for field in ("name: gantry", "description:", "argument-hint:"):
            self.assertIn(field, frontmatter)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "sample#01", "ready-for-agent")
            self.write_roadmap(root)

            for script in ("common.py", "frontier.py", "acceptance.py", "budget.py", "cleanup.py", "gates.py", "roadmap.py", "result.py", "runlog.py", "spec.py"):
                result = self.run_script(root, script, "--help")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("usage:", result.stdout.lower())

            cases = (
                ("common.py", ("--cwd", str(root), "--scope-slug", "sample", "--json"), 0),
                ("frontier.py", ("--scope", "sample", "--json"), 0),
                ("acceptance.py", (str(issue), "--json"), 0),
                ("gates.py", ("--json",), 2),
                ("roadmap.py", ("check", "--json"), 1),
            )
            for script, args, expected in cases:
                result = self.run_script(root, script, *args)
                self.assertEqual(expected, result.returncode, result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)

    def test_planning_drafts_do_not_project_until_operator_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            roadmap = self.write_roadmap(root)
            before = roadmap.read_bytes()
            draft = root / ".scratch" / "planned" / "issues" / "01-planned.md"
            spec = root / ".scratch" / "planned" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("# Planned Spec\n", encoding="utf-8")
            draft_text = """# Planned Issue

Type: issue
Status: draft
Slice: `planned#01`

## Acceptance criteria

- [ ] waits for operator approval

## Blocked by

- None
"""
            plan = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "planned", "specPath": str(root / ".scratch" / "planned" / "spec.md")},
                    "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                    "paths": {
                        "issueDir": str(draft.parent),
                        "specPath": str(root / ".scratch" / "planned" / "spec.md"),
                        "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "decisions": str(root / "docs" / "adr"),
                        "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "context": str(root / "CONTEXT.md"),
                        "adrs": str(root / "docs" / "adr"),
                    },
                    "date": "2026-09-13",
                    "testDraftPath": str(draft),
                    "testDraftText": draft_text,
                    "commandMode": "real",
                },
            )
            self.assertTrue(plan["result"]["awaitingOperatorApproval"])
            self.assertTrue(any(call["label"] == "plan" for call in plan["calls"]))
            self.assertEqual(before, roadmap.read_bytes())
            self.assertEqual("draft", parse_issue(draft).status)
            approved = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "planned", "specPath": str(root / ".scratch" / "planned" / "spec.md")},
                    "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                    "paths": {
                        "issueDir": str(draft.parent),
                        "specPath": str(root / ".scratch" / "planned" / "spec.md"),
                        "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "decisions": str(root / "docs" / "adr"),
                        "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "context": str(root / "CONTEXT.md"),
                        "adrs": str(root / "docs" / "adr"),
                    },
                    "date": "2026-09-13",
                    "testDraftPath": str(draft),
                    "testDraftText": draft_text,
                    "operatorApproved": True,
                    "commandMode": "real",
                },
            )
            self.assertFalse(approved["result"]["awaitingOperatorApproval"])
            self.assertEqual("ready-for-agent", parse_issue(draft).status)
            commands = [call["command"] for call in approved["commandCalls"]]
            approval_commands = [command for command in commands if 'roadmap.py"' in command]
            self.assertEqual(3, len(approval_commands))
            self.assertIn('roadmap.py" status planned#01 ready-for-agent', approval_commands[0])
            self.assertIn('roadmap.py" waves', approval_commands[1])
            self.assertIn('roadmap.py" check', approval_commands[2])
            self.assertTrue(any('budget.py"' in command for command in commands))
            self.assertIn('spec.py" --check', commands[0])
            self.assertIn("planned#01", roadmap.read_text(encoding="utf-8"))

    def test_planner_contract_requires_every_consumed_issue_field_and_rejects_a_pathless_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            draft = self.write_issue(root, "planned#01", "draft")
            spec = root / ".scratch" / "planned" / "spec.md"
            spec.write_text("# Planned Spec\n", encoding="utf-8")
            plan_args = {
                "target": {"kind": "spec", "slug": "planned", "specPath": str(root / ".scratch" / "planned" / "spec.md")},
                "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                "skillDir": str(SKILL_DIR),
                "repoRoot": str(root),
                "commandMode": "real",
                "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                "paths": {
                    "issueDir": str(root / ".scratch" / "planned" / "issues"),
                    "specPath": str(root / ".scratch" / "planned" / "spec.md"),
                    "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                    "decisions": str(root / "docs" / "adr"),
                    "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                    "context": str(root / "CONTEXT.md"),
                    "adrs": str(root / "docs" / "adr"),
                },
                "plannerResult": {
                    "filesWritten": [],
                    "issues": [{
                        "ref": "planned#01",
                        "title": "Pathless planned Issue",
                        "criteriaCount": 1,
                        "blockedBy": [],
                    }],
                    "roadmapAdditions": [],
                    "openDecisions": [],
                },
            }
            rejected = self.run_workflow("plan-workflow.md", plan_args)
            self.assertFalse(rejected["result"]["awaitingOperatorApproval"])
            self.assertFalse(rejected["result"]["approved"])
            self.assertEqual("planner", rejected["result"]["protocolFailure"]["role"])
            self.assertFalse(any('budget.py"' in call["command"] for call in rejected["commandCalls"]))
            self.assertFalse(any('roadmap.py"' in call["command"] for call in rejected["commandCalls"]))

            valid = self.run_workflow(
                "plan-workflow.md",
                {
                    **plan_args,
                    "plannerResult": {
                        **plan_args["plannerResult"],
                        "issues": [{
                            **plan_args["plannerResult"]["issues"][0],
                            "path": str(draft),
                        }],
                    },
                },
            )
            self.assertTrue(valid["result"]["awaitingOperatorApproval"])

    def test_plan_critic_refutes_a_real_measured_over_budget_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            draft = root / ".scratch" / "planned" / "issues" / "01-planned.md"
            spec = root / ".scratch" / "planned" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("# Planned Spec\n", encoding="utf-8")
            package = root / "src" / "over-budget.txt"
            package.parent.mkdir()
            package.write_bytes(b"x" * 200_000)
            result = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "planned", "specPath": str(spec)},
                    "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                    "paths": {
                        "issueDir": str(draft.parent),
                        "specPath": str(spec),
                        "exemplarIssue": str(draft),
                        "decisions": str(root / "docs" / "adr"),
                        "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "context": str(root / "CONTEXT.md"),
                        "adrs": str(root / "docs" / "adr"),
                    },
                    "date": "2026-09-13",
                    "testDraftPath": str(draft),
                    "testDraftText": """# Planned Issue

Type: issue
Status: draft
Slice: `planned#01`
Spec: `.scratch/planned/spec.md`

## What to build

### Files to read

- `src/over-budget.txt`

## Acceptance criteria

- [ ] remains under the initial context budget

## Blocked by

- None
""",
                    "commandMode": "real",
                },
            )

            critique = result["result"]["critique"]
            self.assertFalse(critique["acceptable"])
            measurement = critique["budgets"][0]
            self.assertTrue(measurement["overBudget"])
            self.assertGreater(measurement["estimatedTokens"], measurement["budgetTokens"])
            for field in ("estimatedTokens", "budgetTokens", "contextShare", "contextWindow"):
                self.assertIn(str(measurement[field]), critique["problems"][0]["problem"])
            self.assertTrue(any("/budget.py" in call["command"] for call in result["commandCalls"]))

    def test_requirement_critic_blocks_planning_on_an_ambiguous_definition_of_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_roadmap(root)
            spec = root / ".scratch" / "greeting" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text(
                """# Spec: Greeting

## Blueprint

### Context

A fixture Spec.

## Contract

### Definition of Done

- [ ] the greeting should be fast

### Scenarios

```gherkin
Scenario: greet a user
  Given a fixture Spec
  When the Requirement Critic reviews it
  Then the workflow records the outcome
```

## Out of Scope

- Nothing yet.

## Changelog

- 2026-09-13 — Initial draft.
""",
                encoding="utf-8",
            )
            check = self.run_script(root, "spec.py", "--check", str(spec), "--json")
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            self.assertTrue(json.loads(check.stdout)["valid"])
            spec_bytes_before = spec.read_bytes()
            ambiguous_item = "the greeting should be fast"
            result = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "greeting", "specPath": str(spec)},
                    "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                    "paths": {
                        "issueDir": str(root / ".scratch" / "greeting" / "issues"),
                        "specPath": str(spec),
                        "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "decisions": str(root / "docs" / "adr"),
                        "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "context": str(root / "CONTEXT.md"),
                        "adrs": str(root / "docs" / "adr"),
                    },
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "stubSpecCheck": False,
                    "requirementCriticResult": {
                        "blocking": [
                            {
                                "quote": ambiguous_item,
                                "reason": "no verifiable threshold for \"fast\"",
                            }
                        ],
                        "findings": [],
                    },
                },
            )

            self.assertEqual("requirement_review_failed", result["result"]["blocked"])
            self.assertIn(ambiguous_item, result["result"]["report"])
            self.assertIn("amend", result["result"]["report"].lower())
            self.assertIsNone(result["result"]["plan"])
            self.assertFalse(any(call["label"].startswith("research:") for call in result["calls"]))
            self.assertFalse(any(call["label"].startswith("plan") for call in result["calls"]))
            self.assertFalse(list((root / ".scratch" / "greeting" / "issues").glob("*")) if (root / ".scratch" / "greeting" / "issues").is_dir() else [])
            self.assertFalse(any("roadmap.py" in call["command"] for call in result["commandCalls"]))
            spec_check_calls = [call["command"] for call in result["commandCalls"] if "spec.py" in call["command"]]
            self.assertTrue(spec_check_calls)
            self.assertIn('spec.py" --check', spec_check_calls[0])
            self.assertEqual(spec_bytes_before, spec.read_bytes())

    def test_requirement_critic_protocol_failure_stops_planning_on_invalid_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_roadmap(root)
            spec = root / ".scratch" / "greeting" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text(
                """# Spec: Greeting

## Blueprint

### Context

A fixture Spec.

## Contract

### Definition of Done

- [ ] `greet()` returns "hello" for every call

### Scenarios

```gherkin
Scenario: greet a user
  Given a fixture Spec
  When the Requirement Critic reviews it
  Then the workflow records the outcome
```

## Out of Scope

- Nothing yet.

## Changelog

- 2026-09-13 — Initial draft.
""",
                encoding="utf-8",
            )
            check = self.run_script(root, "spec.py", "--check", str(spec), "--json")
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            self.assertTrue(json.loads(check.stdout)["valid"])
            result = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "greeting", "specPath": str(spec)},
                    "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                    "paths": {
                        "issueDir": str(root / ".scratch" / "greeting" / "issues"),
                        "specPath": str(spec),
                        "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "decisions": str(root / "docs" / "adr"),
                        "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "context": str(root / "CONTEXT.md"),
                        "adrs": str(root / "docs" / "adr"),
                    },
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "stubSpecCheck": False,
                    "structuredOutput": False,
                    "requirementCriticRawResults": [{}, {}],
                },
            )

            self.assertFalse(result["result"]["awaitingOperatorApproval"])
            self.assertFalse(result["result"]["approved"])
            self.assertEqual("requirement-critic", result["result"]["protocolFailure"]["role"])
            self.assertIsNone(result["result"]["plan"])
            self.assertFalse(any(call["label"].startswith("research:") for call in result["calls"]))
            self.assertFalse(any(call["label"].startswith("plan") for call in result["calls"]))
            self.assertFalse(any("roadmap.py" in call["command"] for call in result["commandCalls"]))

    def test_requirement_critic_allows_planning_when_the_spec_is_unambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_roadmap(root)
            spec = root / ".scratch" / "greeting" / "spec.md"
            spec.parent.mkdir(parents=True)
            spec.write_text(
                """# Spec: Greeting

## Blueprint

### Context

A fixture Spec.

## Contract

### Definition of Done

- [ ] `greet()` returns "hello" for every call

### Scenarios

```gherkin
Scenario: greet a user
  Given a fixture Spec
  When the Requirement Critic reviews it
  Then the workflow records the outcome
```

## Out of Scope

- Nothing yet.

## Changelog

- 2026-09-13 — Initial draft.
""",
                encoding="utf-8",
            )
            check = self.run_script(root, "spec.py", "--check", str(spec), "--json")
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            self.assertTrue(json.loads(check.stdout)["valid"])
            spec_bytes_before = spec.read_bytes()
            result = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "greeting", "specPath": str(spec)},
                    "models": {"plan": "claude-opus-4-5", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                    "paths": {
                        "issueDir": str(root / ".scratch" / "greeting" / "issues"),
                        "specPath": str(spec),
                        "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "decisions": str(root / "docs" / "adr"),
                        "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                        "context": str(root / "CONTEXT.md"),
                        "adrs": str(root / "docs" / "adr"),
                    },
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "stubSpecCheck": False,
                    "requirementCriticResult": {"blocking": [], "findings": []},
                },
            )

            self.assertNotIn("blocked", result["result"])
            self.assertTrue(any(call["label"].startswith("research:") for call in result["calls"]))
            self.assertTrue(any(call["label"] == "plan" for call in result["calls"]))
            self.assertEqual(
                1,
                sum(1 for call in result["calls"] if call["label"].startswith("requirement-critic")),
            )
            requirement_critic_index = next(
                index for index, call in enumerate(result["calls"]) if call["label"].startswith("requirement-critic")
            )
            research_index = next(
                index for index, call in enumerate(result["calls"]) if call["label"].startswith("research:")
            )
            self.assertLess(requirement_critic_index, research_index)
            spec_check_calls = [call for call in result["commandCalls"] if "spec.py" in call["command"]]
            self.assertTrue(spec_check_calls)
            self.assertIn('spec.py" --check', spec_check_calls[0]["command"])
            requirement_critic_call = next(
                call for call in result["calls"] if call["label"].startswith("requirement-critic")
            )
            self.assertLess(spec_check_calls[0]["sequence"], requirement_critic_call["sequence"])
            self.assertEqual(spec_bytes_before, spec.read_bytes())

    def test_round_never_raises_the_two_correction_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "ceiling#01", "ready-for-agent")
            self.write_roadmap(root)
            refutation = {
                "complete": False,
                "criteria": [],
                "gatesVerdict": "fail",
                "gateFailures": ["the criterion is not proven"],
                "refutations": ["the criterion is not proven"],
                "requiredFixes": ["add real evidence"],
                "decisionsForOperator": [],
            }

            result = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "ceiling#01", "path": str(issue.relative_to(root)), "title": "Ceiling", "specPath": ".scratch/ceiling/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/ceiling",
                    "baseRef": "HEAD",
                    "isolate": False,
                    "correctionBudget": 10,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 10}},
                    "paths": {},
                    "date": "2026-09-13",
                    "criticResults": [refutation, refutation, refutation],
                },
            )

            delivery = result["result"]["results"][0]
            self.assertEqual("refuted", delivery["outcome"])
            self.assertEqual(2, delivery["corrections"])
            labels = [call["label"] for call in result["calls"]]
            self.assertEqual(3, sum(label.startswith("critic:") for label in labels))
            self.assertEqual(3, sum(label.startswith("implement:") for label in labels))

    def test_round_rejects_critic_completion_without_a_passing_gate(self) -> None:
        cases = ("fail", "no_gates")
        for gates_verdict in cases:
            with self.subTest(gates_verdict=gates_verdict), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.init_repo(root)
                issue = self.write_issue(root, "gates#01", "ready-for-agent")
                self.write_roadmap(root)

                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "gates#01", "path": str(issue.relative_to(root)), "title": "Gate issue", "specPath": ".scratch/gates/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/gates",
                        "baseRef": "HEAD",
                        "isolate": False,
                        "correctionBudget": 0,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 0}},
                        "paths": {},
                        "date": "2026-09-13",
                        "criticResult": {
                            "complete": True, "criteria": self.critic_evidence(root, issue), "gatesVerdict": gates_verdict,
                            "gateResult": {"verdict": gates_verdict}, "gateFailures": ["real gate evidence failed"],
                            "refutations": ["gate evidence is not green"], "requiredFixes": ["make the declared gate pass"],
                            "decisionsForOperator": [],
                        },
                    },
                )

                self.assertEqual("refuted", run["result"]["results"][0]["outcome"])
                self.assertFalse(any('gates.py" --run' in call["command"] for call in run["commandCalls"]))
                self.assertFalse(any('roadmap.py" done' in call["command"] for call in run["commandCalls"]))
                self.assertEqual("ready-for-agent", parse_issue(issue).status)

    def test_round_rejects_missing_or_invalid_critic_evidence_without_state_change(self) -> None:
        cases = {
            "empty": [],
            "partial": [{"index": 1, "met": True, "evidence": "proves the behaviour"}],
            "duplicate": [
                {"index": 1, "met": True, "evidence": "first proof"},
                {"index": 1, "met": True, "evidence": "duplicate proof"},
            ],
            "blank-evidence": [{"index": 1, "met": True, "evidence": "   "}],
            "unmet": [
                {"index": 1, "met": False, "evidence": "the behaviour remains unproven"},
                {"index": 2, "met": True, "evidence": "the second behaviour is proven"},
            ],
        }
        for name, criteria in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.init_repo(root)
                issue = self.write_issue(
                    root,
                    "evidence#01",
                    "ready-for-agent",
                    criteria=["exposes the first behaviour", "exposes the second behaviour"],
                )
                roadmap = self.write_roadmap(root)
                before_issue = issue.read_bytes()
                before_roadmap = roadmap.read_bytes()

                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "evidence#01", "path": str(issue.relative_to(root)), "title": "Evidence issue", "specPath": ".scratch/evidence/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/evidence",
                        "baseRef": "HEAD",
                        "isolate": False,
                        "correctionBudget": 0,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 0}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "criticResult": {
                            "complete": True, "criteria": criteria, "gatesVerdict": "pass",
                            "gateResult": {"verdict": "pass"}, "gateFailures": [],
                            "refutations": [], "requiredFixes": [], "decisionsForOperator": [],
                        },
                    },
                )

                self.assertEqual("refuted", run["result"]["results"][0]["outcome"])
                self.assertEqual(before_issue, issue.read_bytes())
                self.assertEqual(before_roadmap, roadmap.read_bytes())
                commands = [call["command"] for call in run["commandCalls"]]
                self.assertTrue(any('acceptance.py"' in command for command in commands))
                self.assertFalse(any('gates.py" --run' in command for command in commands))
                self.assertFalse(any('roadmap.py" done' in command for command in commands))

    def test_round_reasks_invalid_critic_result_once_without_consuming_budget_or_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "protocol#01", "ready-for-agent")
            roadmap = self.write_roadmap(root)
            before_issue = issue.read_bytes()
            before_roadmap = roadmap.read_bytes()

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "protocol#01", "path": str(issue.relative_to(root)), "title": "Protocol failure", "specPath": ".scratch/protocol/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/protocol",
                    "baseRef": "HEAD",
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "structuredOutput": False,
                    "commandMode": "real",
                    "criticRawResults": [
                        {"complete": False},
                        {"complete": False},
                    ],
                },
            )

            delivery = run["result"]["results"][0]
            self.assertEqual("critic_failed", delivery["outcome"])
            self.assertEqual(0, delivery["corrections"])
            self.assertEqual(before_issue, issue.read_bytes())
            self.assertEqual(before_roadmap, roadmap.read_bytes())
            critic_calls = [call for call in run["calls"] if call["label"].startswith("critic:")]
            self.assertEqual(["critic:protocol#01#1", "critic:protocol#01#1:retry"], [call["label"] for call in critic_calls])
            self.assertFalse(any(call["label"].startswith("implement:protocol#01") for call in run["calls"][1:]))
            self.assertFalse(any('roadmap.py" done' in call["command"] for call in run["commandCalls"]))

    def test_round_stops_on_invalid_correction_implementer_without_spending_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "implementer-protocol#01", "ready-for-agent")
            roadmap = self.write_roadmap(root)
            before_issue = issue.read_bytes()
            before_roadmap = roadmap.read_bytes()

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{
                        "ref": "implementer-protocol#01",
                        "path": str(issue.relative_to(root)),
                        "title": "Implementer protocol failure",
                        "specPath": ".scratch/implementer-protocol/spec.md",
                    }],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/implementer-protocol",
                    "baseRef": "HEAD",
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "structuredOutput": False,
                    "commandMode": "real",
                    "criticRawResults": [{
                        "complete": False,
                        "criteria": self.critic_evidence(root, issue),
                        "gatesVerdict": "fail",
                        "gateResult": {"verdict": "fail"},
                        "gateFailures": ["the gate is red"],
                        "refutations": ["criterion needs a correction"],
                        "requiredFixes": ["make the criterion pass"],
                        "decisionsForOperator": [],
                    }],
                    "implementerRawResults": [
                        {
                            "worktree": root.as_posix(),
                            "branch": "gantry/implementer-protocol",
                            "commits": ["initial implementation"],
                            "summary": "initial implementation completed",
                            "testsAdded": [],
                            "gatesResult": "verdict: pass",
                            "decisions": [],
                            "blockers": [],
                        },
                        {"worktree": root.as_posix()},
                        {"worktree": root.as_posix()},
                    ],
                },
            )

            delivery = run["result"]["results"][0]
            self.assertEqual("implementer_failed", delivery["outcome"])
            self.assertEqual(0, delivery["corrections"])
            self.assertEqual(before_issue, issue.read_bytes())
            self.assertEqual(before_roadmap, roadmap.read_bytes())
            labels = [call["label"] for call in run["calls"]]
            self.assertEqual(
                [
                    "implement:implementer-protocol#01",
                    "review:implementer-protocol#01",
                    "critic:implementer-protocol#01#1",
                    "implement:implementer-protocol#01",
                    "implement:implementer-protocol#01:retry",
                ],
                labels,
            )
            self.assertFalse(any(label.startswith("critic:implementer-protocol#01#2") for label in labels))
            self.assertFalse(any('roadmap.py" done' in call["command"] for call in run["commandCalls"]))

    def test_plan_reports_protocol_failure_instead_of_awaiting_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_roadmap(root)
            base_args = {
                "target": {"kind": "spec", "slug": "planned", "specPath": str(root / ".scratch" / "planned" / "spec.md")},
                "models": {"plan": "plan", "critic": "critic"},
                "skillDir": str(SKILL_DIR),
                "repoRoot": str(root),
                "policy": {"git": {"target": "main", "prefix": "gantry/"}},
                "paths": {
                    "issueDir": str(root / ".scratch" / "planned" / "issues"),
                    "specPath": str(root / ".scratch" / "planned" / "spec.md"),
                    "exemplarIssue": str(root / "docs" / "agents" / "issue-tracker.md"),
                    "decisions": str(root / "docs" / "adr"),
                    "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                    "context": str(root / "CONTEXT.md"),
                    "adrs": str(root / "docs" / "adr"),
                },
                "date": "2026-09-13",
                "structuredOutput": False,
                "commandMode": "real",
            }
            cases = {
                "planner": {"plannerRawResults": [{}, {}]},
                "plan-critic": {"planCriticRawResults": [{}, {}]},
            }
            for role, raw_results in cases.items():
                with self.subTest(role=role):
                    run = self.run_workflow("plan-workflow.md", {**base_args, **raw_results})
                    result = run["result"]
                    self.assertFalse(result["awaitingOperatorApproval"])
                    self.assertFalse(result["approved"])
                    self.assertEqual(role, result["protocolFailure"]["role"])
                    self.assertFalse(any("roadmap.py" in call["command"] for call in run["commandCalls"]))

    def test_round_stops_without_state_change_when_integration_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "integration-fail#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@false\n", encoding="utf-8")

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "integration-fail#01", "path": str(issue.relative_to(root)), "title": "Integration gate", "specPath": ".scratch/integration-fail/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/integration-fail",
                    "baseRef": "HEAD",
                    "isolate": False,
                    "correctionBudget": 0,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 0}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                    },
                },
            )

            self.assertEqual("integration_failed", run["result"]["results"][0]["outcome"])
            self.assertEqual("ready-for-agent", parse_issue(issue).status)
            self.assertEqual(5, len(run["commandCalls"]))
            self.assertIn('result.py" --role "implementer" --json', run["commandCalls"][0]["command"])
            self.assertIn('result.py" --role "reviewer" --json', run["commandCalls"][1]["command"])
            self.assertIn('result.py" --role "critic" --json', run["commandCalls"][2]["command"])
            self.assertIn('acceptance.py"', run["commandCalls"][3]["command"])
            self.assertIn('gates.py" --run', run["commandCalls"][4]["command"])

    def test_round_serially_integrates_then_gates_then_marks_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "serial#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            (root / "base.txt").write_text("base\n", encoding="utf-8")
            policy_path = root / ".gantry" / "config.json"
            policy_path.parent.mkdir()
            policy_path.write_text(
                '{"git":{"issueBranch":"issues/{spec}/{number:02d}"}}',
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            run_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            issue_branch = "issues/serial/01"
            issue_worktree = Path(f"{root}.gantry-serial-01")

            try:
                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "serial#01", "path": str(issue.relative_to(root)), "title": "Serial integration", "specPath": ".scratch/serial/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": run_branch,
                        "baseRef": base_ref,
                        "isolate": True,
                        "correctionBudget": 0,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/", "issueBranch": "issues/{spec}/{number:02d}"}, "budget": {"corrections": 0}},
                        "paths": {},
                        "date": "2026-09-13",
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "implementerCommitText": "integrated\n",
                        "commandMode": "real",
                        "criticResult": {
                            "criteria": self.critic_evidence(root, issue),
                        },
                    },
                )

                self.assertEqual("done", run["result"]["results"][0]["outcome"])
                self.assertEqual("done", parse_issue(issue).status)
                self.assertEqual("integrated\n", (root / "delivery.txt").read_text(encoding="utf-8"))
                commands = [call["command"] for call in run["commandCalls"]]
                self.assertEqual(12, len(commands))
                self.assertIn('common.py" --cwd', commands[0])
                self.assertIn("--issue", commands[0])
                self.assertIn(f"git worktree add --quiet -b '{issue_branch}'", commands[1])
                self.assertEqual("git branch --show-current", commands[2])
                self.assertIn('result.py" --role "implementer" --json', commands[3])
                self.assertIn('result.py" --role "reviewer" --json', commands[4])
                self.assertIn('result.py" --role "critic" --json', commands[5])
                self.assertIn('acceptance.py"', commands[6])
                self.assertIn(f'git merge --no-ff "{issue_branch}"', commands[7])
                self.assertIn('gates.py" --run', commands[8])
                self.assertIn('roadmap.py" done serial#01', commands[9])
                self.assertIn('git add -- ROADMAP.md', commands[10])
                self.assertIn('git commit -m "gantry: complete serial#01"', commands[11])
                self.assertFalse(any('roadmap.py" status' in command for command in commands))
                self.assertEqual(
                    [str(issue_worktree)] * 3,
                    [call["cwd"] for call in run["calls"] if call["label"].split(":", 1)[0] in {"implement", "review", "critic"}],
                )
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def test_round_workflow_records_the_recorded_run_lifecycle_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "lifecycle#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "abababababab"
            run_id = "run-lifecycle-1"

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 3,
                    "issues": [{"ref": "lifecycle#01", "path": str(issue.relative_to(root)), "title": "Lifecycle", "specPath": ".scratch/lifecycle/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/lifecycle",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "isLastRound": True,
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                    },
                },
            )

            self.assertEqual("done", run["result"]["results"][0]["outcome"])
            events = self.read_run_log_events(state_root, unit_id, run_id)
            sequence = [(event["event"], event.get("issue"), event.get("phase")) for event in events]
            self.assertEqual(
                [
                    ("run.started", None, None),
                    ("round.started", None, None),
                    ("phase.started", "lifecycle#01", "Implement"),
                    ("subagent.started", "lifecycle#01", "Implement"),
                    ("subagent.stopped", "lifecycle#01", "Implement"),
                    ("phase.finished", "lifecycle#01", "Implement"),
                    ("phase.started", "lifecycle#01", "Review"),
                    ("subagent.started", "lifecycle#01", "Review"),
                    ("subagent.stopped", "lifecycle#01", "Review"),
                    ("phase.finished", "lifecycle#01", "Review"),
                    ("review.finding", "lifecycle#01", "Review"),
                    ("phase.started", "lifecycle#01", "Critic"),
                    ("subagent.started", "lifecycle#01", "Critic"),
                    ("subagent.stopped", "lifecycle#01", "Critic"),
                    ("phase.finished", "lifecycle#01", "Critic"),
                    ("issue.done", "lifecycle#01", None),
                    ("round.finished", None, None),
                    ("run.finished", None, None),
                ],
                sequence,
            )
            started = events[0]
            self.assertEqual(str(root), started["data"]["repositoryRoot"])
            self.assertEqual("reference", started["data"]["tier"])
            self.assertEqual(900, started["data"]["staleAfterSeconds"])
            self.assertTrue(started["data"]["policyHash"])
            done_event = next(event for event in events if event["event"] == "issue.done")
            self.assertEqual(str(root), done_event["data"]["worktree"])
            round_started = next(event for event in events if event["event"] == "round.started")
            self.assertEqual(3, round_started["data"]["round"])

            # `subagent.stopped` must carry the validated role result payload itself, not just tag the
            # event with the phase/issue it belongs to.
            implement_stopped = next(
                event for event in events
                if event["event"] == "subagent.stopped" and event["phase"] == "Implement"
            )
            self.assertEqual("implementer", implement_stopped["data"]["role"])
            implement_result = implement_stopped["data"]["result"]
            self.assertEqual(str(root), implement_result["worktree"])
            self.assertEqual("gantry/lifecycle", implement_result["branch"])
            self.assertEqual(["test commit"], implement_result["commits"])
            self.assertEqual("workflow execution", implement_result["summary"])

    def test_round_workflow_marks_the_worktree_with_the_run_before_any_agent_and_clears_it_at_the_end(self) -> None:
        """The marker is what makes a git hook's `hook.denied` recording a guarantee."""
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "marked#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "cdcdcdcdcdcd"
            run_id = "run-marked-1"
            marker = root / ".git" / "gantry" / "current-run.json"

            def invoke(is_first_round: bool, is_last_round: bool, round_number: int) -> dict:
                return self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": round_number,
                        "issues": [{"ref": "marked#01", "path": str(issue.relative_to(root)), "title": "Marked", "specPath": ".scratch/marked/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/marked",
                        "baseRef": base_ref,
                        "isolate": False,
                        "correctionBudget": 2,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                        "paths": {},
                        "date": "2026-09-14",
                        "commandMode": "real",
                        "runId": run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "isFirstRound": is_first_round,
                        "isLastRound": is_last_round,
                        "criticResult": {"criteria": self.critic_evidence(root, issue)},
                    },
                )

            first = invoke(True, False, 1)
            self.assertIsNone(first["error"], first["error"])
            mark_calls = [call for call in first["commandCalls"] if "runlog.py" in call["command"] and " mark " in call["command"]]
            self.assertTrue(mark_calls, first["commandCalls"])
            self.assertIn(str(root), mark_calls[0]["command"])
            self.assertIn(run_id, mark_calls[0]["command"])
            implement_call = next(call for call in first["calls"] if call["label"].startswith("implement:"))
            self.assertLess(mark_calls[0]["sequence"], implement_call["sequence"], "the worktree is marked before any agent works in it")

            self.assertTrue(marker.is_file(), "a Run that continues into another round keeps its marker")
            self.assertEqual(run_id, json.loads(marker.read_text(encoding="utf-8"))["run"])

            last = invoke(False, True, 2)
            self.assertIsNone(last["error"], last["error"])
            self.assertFalse(marker.exists(), "the marker is cleared when the Run ends")

    def test_round_workflow_marks_the_issue_worktree_of_an_isolated_round(self) -> None:
        """An isolated round works in `<repoRoot>.gantry-<spec>-<nn>`, not the repository root.

        That worktree is where the Implementer's `git` runs, so it is the worktree whose own git
        directory must carry the current-Run marker before any agent starts -- otherwise a
        `pre-commit`/`pre-push` denial there resolves no Run and the `hook.denied` guarantee is
        empty for exactly the case isolation is used for.
        """
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "isomark#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            policy_path = root / ".gantry" / "config.json"
            policy_path.parent.mkdir()
            policy_path.write_text('{"git":{"issueBranch":"issues/{spec}/{number:02d}"}}', encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True,
            ).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "efefefefefef"
            run_id = "run-isomark-1"
            issue_branch = "issues/isomark/01"
            issue_worktree = Path(f"{root}.gantry-isomark-01")

            def invoke(is_first_round: bool, is_last_round: bool, round_number: int, prior_run: dict | None) -> dict:
                return self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": round_number,
                        "issues": [{"ref": "isomark#01", "path": str(issue.relative_to(root)), "title": "Isolated marker", "specPath": ".scratch/isomark/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/isomark",
                        "baseRef": base_ref,
                        "isolate": True,
                        "correctionBudget": 0,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/", "issueBranch": "issues/{spec}/{number:02d}"}, "budget": {"corrections": 0}},
                        "paths": {},
                        "date": "2026-09-14",
                        "commandMode": "real",
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "runId": run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "isFirstRound": is_first_round,
                        "isLastRound": is_last_round,
                        **({"priorRun": prior_run} if prior_run else {}),
                        # Refuted, so the Issue keeps its worktree into the next round instead of
                        # being merged and completed.
                        "criticResult": {
                            "complete": False,
                            "refutations": ["criterion one is unproven"],
                            "requiredFixes": ["prove criterion one"],
                        },
                    },
                )

            try:
                first = invoke(True, False, 1, None)
                self.assertIsNone(first["error"], first["error"])
                self.assertEqual("refuted", first["result"]["results"][0]["outcome"])

                worktree_git_dir = Path(
                    subprocess.run(
                        ["git", "rev-parse", "--git-dir"],
                        cwd=issue_worktree,
                        text=True,
                        capture_output=True,
                        check=True,
                    ).stdout.strip()
                )
                self.assertNotEqual(root / ".git", worktree_git_dir, "git keys a git directory per worktree")
                marker = worktree_git_dir / "gantry" / "current-run.json"

                mark_calls = [
                    call for call in first["commandCalls"]
                    if "runlog.py" in call["command"] and f"mark '{run_id}' --cwd '{issue_worktree}'" in call["command"]
                ]
                self.assertTrue(mark_calls, first["commandCalls"])
                implement_call = next(call for call in first["calls"] if call["label"].startswith("implement:"))
                self.assertEqual(str(issue_worktree), implement_call["cwd"])
                self.assertLess(
                    mark_calls[0]["sequence"],
                    implement_call["sequence"],
                    "the Issue worktree is marked before any agent works in it",
                )

                self.assertTrue(marker.is_file(), f"{marker} should carry the Run between rounds")
                self.assertEqual(run_id, json.loads(marker.read_text(encoding="utf-8"))["run"])

                last = invoke(
                    False, True, 2,
                    {"issue": "isomark#01", "worktree": str(issue_worktree), "branch": issue_branch, "correctionsSpent": 0},
                )
                self.assertIsNone(last["error"], last["error"])
                self.assertFalse(marker.exists(), "the Issue worktree's marker is cleared when the Run ends")
                self.assertFalse((root / ".git" / "gantry" / "current-run.json").exists())
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def test_round_workflow_unmarks_every_worktree_of_the_run_not_only_this_invocations(self) -> None:
        """An Issue finished in an earlier round is absent from the last one.

        Each round is a separate invocation of this Workflow with its own memory, so the set of
        worktrees *this* invocation marked is not the set of worktrees the Run marked. Clearing
        only the former leaves a stale marker naming a finished Run in the Issue's worktree, and
        the next hook denial there records into a Run that is already over. The Run end must
        enumerate the clone's worktrees and clear every marker that names this Run.
        """
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "isodrop#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            policy_path = root / ".gantry" / "config.json"
            policy_path.parent.mkdir()
            policy_path.write_text('{"git":{"issueBranch":"issues/{spec}/{number:02d}"}}', encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True,
            ).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "dadadadadada"
            run_id = "run-isodrop-1"
            issue_worktree = Path(f"{root}.gantry-isodrop-01")

            def invoke(round_number: int, issues: list[dict], is_first: bool, is_last: bool) -> dict:
                return self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": round_number,
                        "issues": issues,
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/isodrop",
                        "baseRef": base_ref,
                        "isolate": True,
                        "correctionBudget": 0,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/", "issueBranch": "issues/{spec}/{number:02d}"}, "budget": {"corrections": 0}},
                        "paths": {},
                        "date": "2026-09-14",
                        "commandMode": "real",
                        "issueBranch": "issues/isodrop/01",
                        "issueWorktree": str(issue_worktree),
                        "runId": run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "isFirstRound": is_first,
                        "isLastRound": is_last,
                        "criticResult": {
                            "complete": False,
                            "refutations": ["criterion one is unproven"],
                            "requiredFixes": ["prove criterion one"],
                        },
                    },
                )

            try:
                first = invoke(
                    1,
                    [{"ref": "isodrop#01", "path": str(issue.relative_to(root)), "title": "Dropped", "specPath": ".scratch/isodrop/spec.md"}],
                    True,
                    False,
                )
                self.assertIsNone(first["error"], first["error"])

                worktree_git_dir = Path(
                    subprocess.run(
                        ["git", "rev-parse", "--git-dir"],
                        cwd=issue_worktree, text=True, capture_output=True, check=True,
                    ).stdout.strip()
                )
                marker = worktree_git_dir / "gantry" / "current-run.json"
                self.assertTrue(marker.is_file(), f"{marker} should carry the Run after round 1")

                # Round 2 is the Run's last and carries no Issue at all: isodrop#01 was already
                # dealt with, so this invocation never marks its worktree and cannot remember it.
                last = invoke(2, [], False, True)
                self.assertIsNone(last["error"], last["error"])

                self.assertFalse(
                    marker.exists(),
                    "a worktree marked by an earlier round of this Run must still be unmarked at the Run's end",
                )
                self.assertFalse((root / ".git" / "gantry" / "current-run.json").exists())
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def test_round_workflow_records_the_learner_phase_before_run_finished(self) -> None:
        # The optional Learner phase, when it actually runs, must be recorded exactly like every other
        # phase (phase.started / subagent.started / subagent.stopped / phase.finished) and must be
        # recorded strictly between round.finished and run.finished, so run.finished stays the Run log's
        # last event and no subagent runs after the Run's own recorded completion.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "learnround#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True,
            ).stdout.strip()

            # A prior Run log containing the same refutation evidence text on two different Issues, so
            # `learner.py` extracts exactly one recurring lesson candidate from it.
            state_root = Path(state_dir)
            prior_log = state_root / "fixtures" / "prior-run.jsonl"
            prior_log.parent.mkdir(parents=True, exist_ok=True)
            prior_events = [
                {
                    "ts": "2026-09-13T00:00:00Z", "run": "prior-run", "event": "refutation",
                    "issue": "priorx#01", "phase": "Critic", "data": {"message": "criterion 3 has no test"},
                },
                {
                    "ts": "2026-09-13T00:05:00Z", "run": "prior-run", "event": "refutation",
                    "issue": "priorx#02", "phase": "Critic", "data": {"message": "criterion 3 has no test"},
                },
            ]
            prior_log.write_text(
                "\n".join(json.dumps(event) for event in prior_events) + "\n", encoding="utf-8",
            )

            unit_id = "efefefefefef"
            run_id = "run-learnround-1"

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "learnround#01", "path": str(issue.relative_to(root)), "title": "Learn round", "specPath": ".scratch/learnround/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/learnround",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-14",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "isLastRound": True,
                    "learnerRunLogs": [str(prior_log)],
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                    },
                },
            )

            self.assertIsNone(run["error"], run["error"])
            self.assertEqual("done", run["result"]["results"][0]["outcome"])
            self.assertTrue(run["result"]["candidates"])

            events = self.read_run_log_events(state_root, unit_id, run_id)
            names = [event["event"] for event in events]

            # run.finished is emitted exactly once and is the very last event in the log.
            self.assertEqual(1, names.count("run.finished"))
            self.assertEqual("run.finished", names[-1])

            round_finished_index = names.index("round.finished")
            run_finished_index = names.index("run.finished")

            learn_phase_events = [
                event for event in events
                if event.get("phase") == "Learn"
            ]
            learn_event_names = [event["event"] for event in learn_phase_events]
            self.assertEqual(
                ["phase.started", "subagent.started", "subagent.stopped", "phase.finished"],
                learn_event_names,
            )
            for event in learn_phase_events:
                # Every phase.started/phase.finished event requires an `issue` per runlog.py's own
                # rule; the Learn phase is not scoped to one Issue, so it uses the reserved,
                # non-Issue reference documented in round-workflow.md.
                self.assertEqual("learn#00", event["issue"])

            learn_indexes = [events.index(event) for event in learn_phase_events]
            self.assertTrue(all(round_finished_index < index < run_finished_index for index in learn_indexes))

            subagent_started = next(event for event in learn_phase_events if event["event"] == "subagent.started")
            self.assertEqual("learner", subagent_started["data"]["role"])
            subagent_stopped = next(event for event in learn_phase_events if event["event"] == "subagent.stopped")
            self.assertEqual("learner", subagent_stopped["data"]["role"])
            self.assertIn("result", subagent_stopped["data"])
            self.assertTrue(subagent_stopped["data"]["result"]["candidates"])

    def test_round_workflow_projects_a_real_gates_json_critic_verdict_before_recording_it(self) -> None:
        # A real Critic runs `gates.py --run --diff-base <baseRef> --json` and returns that payload
        # unchanged in `gateResult`, per its own prompt contract. `gates.py --json`'s real shape carries
        # `gates[{name, source, command, exit_code, output_tail, status}]` — command and output data the
        # Run log must never store (spec.md line 25; `runlog.py`'s own `command`/`output` rejection).
        # Recording that payload unprojected would make `runlog.py append` fail loudly on every genuinely
        # gate-green Critic pass, not only on disallowed data. This proves the round still completes.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "realgate#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True,
            ).stdout.strip()

            real_gates_json = self.run_script(root, "gates.py", "--run", "--diff-base", base_ref, "--cwd", str(root), "--json")
            self.assertEqual(0, real_gates_json.returncode, real_gates_json.stderr)
            real_gate_result = json.loads(real_gates_json.stdout)
            self.assertEqual("pass", real_gate_result["verdict"])
            self.assertTrue(real_gate_result["gates"])
            self.assertIn("command", real_gate_result["gates"][0])
            self.assertIn("output_tail", real_gate_result["gates"][0])

            state_root = Path(state_dir)
            unit_id = "cdcdcdcdcdcd"
            run_id = "run-realgate-1"

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "realgate#01", "path": str(issue.relative_to(root)), "title": "Real gate", "specPath": ".scratch/realgate/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/realgate",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "isLastRound": True,
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                        "gatesVerdict": real_gate_result["verdict"],
                        "gateResult": real_gate_result,
                    },
                },
            )

            self.assertIsNone(run["error"], run["error"])
            self.assertEqual("done", run["result"]["results"][0]["outcome"])

            events = self.read_run_log_events(state_root, unit_id, run_id)
            critic_stopped = [
                event for event in events
                if event["event"] == "subagent.stopped" and event["phase"] == "Critic"
            ]
            self.assertEqual(1, len(critic_stopped))
            recorded_gate_result = critic_stopped[0]["data"]["result"]["gateResult"]
            self.assertEqual({"verdict", "requirements"}, set(recorded_gate_result.keys()))
            self.assertEqual("pass", recorded_gate_result["verdict"])
            self.assertEqual(real_gate_result["requirements"], recorded_gate_result["requirements"])

            raw_lines = (state_root / unit_id / "runs" / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertTrue(raw_lines)
            for line in raw_lines:
                keys = set()

                def collect_keys(value: object) -> None:
                    if isinstance(value, dict):
                        keys.update(value.keys())
                        for nested in value.values():
                            collect_keys(nested)
                    elif isinstance(value, list):
                        for nested in value:
                            collect_keys(nested)

                collect_keys(json.loads(line))
                self.assertNotIn("command", keys, line)
                self.assertNotIn("output", keys, line)
                self.assertNotIn("output_tail", keys, line)

    def test_round_workflow_emits_run_started_and_run_finished_exactly_once_across_two_rounds(self) -> None:
        # A Run spans multiple rounds of the same round-workflow.md invocation sharing one runId/unitId.
        # `run.started` must open the Run exactly once (on the first round) and `run.finished` must close
        # it exactly once, only after the last round — never once per round-workflow invocation.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue_one = self.write_issue(root, "tworound#01", "ready-for-agent")
            issue_two = self.write_issue(root, "tworound#02", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "aaaaaaaaaaaa"
            run_id = "run-tworound-1"

            round_one = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "tworound#01", "path": str(issue_one.relative_to(root)), "title": "Two round one", "specPath": ".scratch/tworound/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/tworound",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "isLastRound": False,
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue_one),
                    },
                },
            )
            self.assertEqual("done", round_one["result"]["results"][0]["outcome"])

            round_two = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 2,
                    "issues": [{"ref": "tworound#02", "path": str(issue_two.relative_to(root)), "title": "Two round two", "specPath": ".scratch/tworound/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/tworound",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "isFirstRound": False,
                    "isLastRound": True,
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue_two),
                    },
                },
            )
            self.assertEqual("done", round_two["result"]["results"][0]["outcome"])

            events = self.read_run_log_events(state_root, unit_id, run_id)
            names = [event["event"] for event in events]
            self.assertEqual(1, names.count("run.started"))
            self.assertEqual(2, names.count("round.started"))
            self.assertEqual(2, names.count("round.finished"))
            self.assertEqual(1, names.count("run.finished"))
            round_started_rounds = [event["data"]["round"] for event in events if event["event"] == "round.started"]
            self.assertEqual([1, 2], round_started_rounds)
            # `run.finished` is the very last event, emitted only once both rounds (and their own
            # round.finished) have already been recorded.
            self.assertEqual("run.finished", names[-1])
            self.assertEqual("round.finished", names[-2])

    def test_round_workflow_resume_with_changed_policy_emits_policy_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "policydrift#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "efefefefefef"
            run_id = "run-policydrift-2"

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "policydrift#01", "path": str(issue.relative_to(root)), "title": "Policy drift", "specPath": ".scratch/policydrift/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/policydrift",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "priorRun": {
                        "run": "run-policydrift-1",
                        "worktree": str(root),
                        "branch": "gantry/policydrift",
                        "issue": "policydrift#01",
                        "correctionsSpent": 0,
                        "policyHash": "deadbeef",
                    },
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                    },
                },
            )

            self.assertEqual("done", run["result"]["results"][0]["outcome"])
            events = self.read_run_log_events(state_root, unit_id, run_id)
            sequence = [event["event"] for event in events]
            self.assertEqual(
                ["run.started", "run.resumed", "policy.changed", "round.started"],
                sequence[:4],
            )
            started = events[0]
            changed = next(event for event in events if event["event"] == "policy.changed")
            self.assertEqual(started["data"]["policyHash"], changed["data"]["policyHash"])
            self.assertNotEqual("deadbeef", changed["data"]["policyHash"])

    def test_round_workflow_resume_emits_run_resumed_and_preserves_worktree_and_corrections(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "resume#01", "ready-for-agent")
            roadmap = self.write_roadmap(root)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            before_issue = issue.read_bytes()
            before_roadmap = roadmap.read_bytes()

            issue_branch = "gantry/resume-01"
            issue_worktree = Path(f"{root}.gantry-resume-01")
            subprocess.run(["git", "worktree", "add", "--quiet", "-b", issue_branch, str(issue_worktree), "HEAD"], cwd=root, check=True)

            state_root = Path(state_dir)
            unit_id = "cdcdcdcdcdcd"
            run_id = "run-resume-2"

            try:
                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "resume#01", "path": str(issue.relative_to(root)), "title": "Resume", "specPath": ".scratch/resume/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/resume",
                        "baseRef": "HEAD",
                        "isolate": True,
                        "correctionBudget": 1,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 1}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "runId": run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "priorRun": {
                            "run": "run-resume-1",
                            "worktree": str(issue_worktree),
                            "branch": issue_branch,
                            "issue": "resume#01",
                            "correctionsSpent": 1,
                        },
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "criticResult": {
                            "complete": False,
                            "criteria": [],
                            "gatesVerdict": "fail",
                            "gateResult": {"verdict": "fail"},
                            "gateFailures": ["still not proven"],
                            "refutations": ["criterion one remains unproven"],
                            "requiredFixes": ["add real evidence"],
                            "decisionsForOperator": [],
                        },
                    },
                )

                delivery = run["result"]["results"][0]
                self.assertEqual("refuted", delivery["outcome"])
                self.assertEqual(1, delivery["corrections"])
                self.assertFalse(any("worktree add" in call["command"] for call in run["commandCalls"]))
                self.assertEqual(before_issue, issue.read_bytes())
                self.assertEqual(before_roadmap, roadmap.read_bytes())
                self.assertTrue(issue_worktree.is_dir())

                events = self.read_run_log_events(state_root, unit_id, run_id)
                self.assertEqual("run.started", events[0]["event"])
                resumed = next(event for event in events if event["event"] == "run.resumed")
                self.assertEqual("run-resume-1", resumed["data"]["priorRun"])
                self.assertEqual(str(issue_worktree), resumed["data"]["worktree"])
                refutation = next(event for event in events if event["event"] == "refutation")
                self.assertEqual("resume#01", refutation["issue"])
                self.assertEqual(["criterion one remains unproven"], refutation["data"]["refutations"])
                blocked = next(event for event in events if event["event"] == "issue.blocked")
                self.assertEqual("resume#01", blocked["issue"])
                self.assertEqual(str(issue_worktree), blocked["data"]["worktree"])
                self.assertEqual(1, blocked["data"]["corrections"])
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def append_runlog_event(self, state_root: Path, unit_id: str, run_id: str, event: dict[str, object]) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "runlog.py"), "append", unit_id, run_id, "--state-root", str(state_root)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_runlog_inflight_reports_interrupted_review_and_critic_phases_with_worktree(self) -> None:
        # Covers feedback item 4: `reference/round-workflow.md` now records `worktree` in the Review and
        # Critic `phase.started` data, so a Run interrupted mid-Review or mid-Critic (not just
        # mid-Implement) still surfaces in `runlog.py inflight --json` with its worktree.
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            unit_id = "aaaaaaaaaaaa"

            review_run_id = "run-inflight-review"
            self.append_runlog_event(state_root, unit_id, review_run_id, {
                "ts": "2026-09-13T10:00:00Z", "run": review_run_id, "event": "run.started",
                "data": {"repositoryRoot": "/tmp/repo", "policyHash": "policyhash", "tier": "reference", "staleAfterSeconds": 900},
            })
            self.append_runlog_event(state_root, unit_id, review_run_id, {
                "ts": "2026-09-13T10:01:00Z", "run": review_run_id, "event": "phase.started",
                "issue": "inflight#01", "phase": "Review", "data": {"worktree": "/tmp/repo.gantry-inflight-01"},
            })
            # Interrupted mid-Review: no phase.finished, run.cancelled, or run.finished.

            critic_run_id = "run-inflight-critic"
            self.append_runlog_event(state_root, unit_id, critic_run_id, {
                "ts": "2026-09-13T10:02:00Z", "run": critic_run_id, "event": "run.started",
                "data": {"repositoryRoot": "/tmp/repo", "policyHash": "policyhash", "tier": "reference", "staleAfterSeconds": 900},
            })
            self.append_runlog_event(state_root, unit_id, critic_run_id, {
                "ts": "2026-09-13T10:03:00Z", "run": critic_run_id, "event": "phase.started",
                "issue": "inflight#02", "phase": "Critic", "data": {"attempt": 1, "worktree": "/tmp/repo.gantry-inflight-02"},
            })
            # Interrupted mid-Critic: no phase.finished, run.cancelled, or run.finished.

            inflight = subprocess.run(
                [sys.executable, str(SCRIPTS / "runlog.py"), "inflight", unit_id, "--state-root", str(state_root), "--json"],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, inflight.returncode, inflight.stderr)
            payload = json.loads(inflight.stdout)
            matches = {entry["issue"]: entry for entry in payload["inflight"]}
            self.assertEqual({"inflight#01", "inflight#02"}, set(matches))
            self.assertEqual("Review", matches["inflight#01"]["phase"])
            self.assertEqual("/tmp/repo.gantry-inflight-01", matches["inflight#01"]["worktree"])
            self.assertEqual("Critic", matches["inflight#02"]["phase"])
            self.assertEqual("/tmp/repo.gantry-inflight-02", matches["inflight#02"]["worktree"])

    def test_preflight_derives_corrections_spent_from_inflight_refutations_and_resumes_at_the_ceiling(self) -> None:
        # Covers SKILL.md's documented derivation rule: `runlog.py inflight` reports only `run`, `issue`,
        # `phase` and `worktree` (plus Run-level metadata) — never `correctionsSpent` or `branch` — so this
        # proves preflight must derive `correctionsSpent` by invoking the shipped `runlog.py corrections
        # <unitId> <runId> <issue> --json` query (this Run's `run.resumed.data.correctionsSpent`, if any,
        # plus every `refutation` for the matched Issue that is later followed by a `phase.started`
        # `Implement` event, i.e. a refutation whose correction pass actually started), and that `branch`
        # may be omitted because `reference/round-workflow.md`'s `implementationLocation` derives it itself.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "resumeq#01", "ready-for-agent")
            self.write_roadmap(root)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            before_issue = issue.read_bytes()

            issue_branch = "gantry/resumeq-01"
            issue_worktree = Path(f"{root}.gantry-resumeq-01")
            subprocess.run(["git", "worktree", "add", "--quiet", "-b", issue_branch, str(issue_worktree), "HEAD"], cwd=root, check=True)

            state_root = Path(state_dir)
            unit_id = "abcabcabcabc"
            prior_run_id = "run-priorq-1"
            now_run_id = "run-priorq-2"

            try:
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:00:00Z", "run": prior_run_id, "event": "run.started",
                    "data": {
                        "repositoryRoot": str(root), "policyHash": "priorpolicyhash",
                        "tier": "reference", "staleAfterSeconds": 900,
                    },
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:01:00Z", "run": prior_run_id, "event": "phase.started",
                    "issue": "resumeq#01", "phase": "Implement",
                    "data": {"worktree": str(issue_worktree)},
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:02:00Z", "run": prior_run_id, "event": "refutation",
                    "issue": "resumeq#01", "phase": "Critic",
                    "data": {"attempt": 1, "refutations": ["first refutation"]},
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:02:30Z", "run": prior_run_id, "event": "phase.started",
                    "issue": "resumeq#01", "phase": "Implement",
                    "data": {"worktree": str(issue_worktree)},
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:03:00Z", "run": prior_run_id, "event": "refutation",
                    "issue": "resumeq#01", "phase": "Critic",
                    "data": {"attempt": 2, "refutations": ["second refutation"]},
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:03:30Z", "run": prior_run_id, "event": "phase.started",
                    "issue": "resumeq#01", "phase": "Implement",
                    "data": {"worktree": str(issue_worktree)},
                })
                # No phase.finished or run.finished: this Run is genuinely interrupted mid-Implement,
                # in the middle of the correction pass started after the second refutation.

                inflight = subprocess.run(
                    [sys.executable, str(SCRIPTS / "runlog.py"), "inflight", unit_id, "--state-root", str(state_root), "--json"],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(0, inflight.returncode, inflight.stderr)
                payload = json.loads(inflight.stdout)
                self.assertEqual(1, len(payload["inflight"]))
                match = payload["inflight"][0]
                self.assertEqual("resumeq#01", match["issue"])
                self.assertEqual(str(issue_worktree), match["worktree"])
                # `runlog.py inflight` never reports correctionsSpent or branch: preflight must derive them.
                self.assertNotIn("correctionsSpent", match)
                self.assertNotIn("branch", match)

                # Invoke the shipped `runlog.py corrections` query (SKILL.md's documented preflight
                # step) against the match's own Run log, rather than a test-local derivation helper.
                corrections_spent = self.run_corrections_command(state_root, unit_id, match["run"], match["issue"])
                self.assertEqual(2, corrections_spent)

                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "resumeq#01", "path": str(issue.relative_to(root)), "title": "Resume derivation", "specPath": ".scratch/resumeq/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/resumeq",
                        "baseRef": "HEAD",
                        "isolate": True,
                        "correctionBudget": 2,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "runId": now_run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "priorRun": {
                            "run": match["run"],
                            "worktree": match["worktree"],
                            "issue": match["issue"],
                            "correctionsSpent": corrections_spent,
                            "policyHash": match["policyHash"],
                        },
                        "criticResult": {
                            "complete": False,
                            "criteria": [],
                            "gatesVerdict": "fail",
                            "gateResult": {"verdict": "fail"},
                            "gateFailures": ["still not proven"],
                            "refutations": ["criterion one remains unproven"],
                            "requiredFixes": ["add real evidence"],
                            "decisionsForOperator": [],
                        },
                    },
                )

                delivery = run["result"]["results"][0]
                self.assertEqual("refuted", delivery["outcome"])
                self.assertEqual(2, delivery["corrections"])
                # The ceiling was already spent: only the initial Implementer call happens, never a
                # correction pass, and the Critic is consulted exactly once before the Run blocks.
                implement_calls = [call for call in run["calls"] if call["label"].startswith("implement:")]
                self.assertEqual(1, len(implement_calls))
                critic_calls = [call for call in run["calls"] if call["label"].startswith("critic:")]
                self.assertEqual(1, len(critic_calls))
                self.assertEqual(str(issue_worktree), implement_calls[0]["cwd"])

                events = self.read_run_log_events(state_root, unit_id, now_run_id)
                self.assertEqual("run.started", events[0]["event"])
                resumed = next(event for event in events if event["event"] == "run.resumed")
                self.assertEqual(prior_run_id, resumed["data"]["priorRun"])
                self.assertEqual(str(issue_worktree), resumed["data"]["worktree"])
                blocked = next(event for event in events if event["event"] == "issue.blocked")
                self.assertEqual("resumeq#01", blocked["issue"])
                self.assertEqual(str(issue_worktree), blocked["data"]["worktree"])
                self.assertEqual(2, blocked["data"]["corrections"])

                # Status authority stays in the Issue file: a refuted, ceiling-spent Issue keeps
                # `Status: ready-for-agent`, so `frontier.py` still reports it as workable.
                self.assertEqual(before_issue, issue.read_bytes())
                frontier = subprocess.run(
                    [sys.executable, str(SCRIPTS / "frontier.py"), "--scope", "resumeq#01",
                     "--scratch", ".scratch", "--json"],
                    cwd=root, text=True, capture_output=True, check=False,
                )
                self.assertEqual(0, frontier.returncode, frontier.stderr)
                frontier_payload = json.loads(frontier.stdout)
                self.assertIn(["resumeq#01"], frontier_payload["rounds"])
                self.assertEqual({}, frontier_payload["parked"])
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def test_gantry_greeting_offers_and_resumes_a_fixture_interrupted_run_in_its_worktree(self) -> None:
        # Covers AC1 with the real `fixture/` tree from gantry-migration#16 (not a synthetic stand-in):
        # a Run interrupted while `greeting#02` was in the Implement phase in worktree W, having already
        # burned one real correction attempt (a refutation followed by a later Implement phase.started),
        # causes the next `gantry greeting` invocation to offer continuation in W via `runlog.py inflight`.
        # `runlog.py corrections` derives `1` from that prior log; choosing to continue appends
        # `run.resumed` with the prior Run id, W and `correctionsSpent: 1`, and the resumed round spends
        # only its one remaining correction attempt (out of budget 2) before `issue.blocked` records
        # `data.corrections == 2`, worktree W preserved and `greeting#02` still `Status: ready-for-agent`.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp) / "fixture-copy"
            build = subprocess.run(
                [sys.executable, str(REPO_ROOT / "fixture" / "tools" / "copy_fixture.py"),
                 "--mode", "approved", "--skill-dir", str(SKILL_DIR), "--dest", str(root)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, build.returncode, build.stderr)

            issue = root / ".scratch" / "greeting" / "issues" / "02-greeting-cli.md"
            before_issue = issue.read_bytes()

            issue_branch = "gantry/greeting-02"
            issue_worktree = Path(f"{root}.gantry-greeting-02")
            subprocess.run(["git", "worktree", "add", "--quiet", "-b", issue_branch, str(issue_worktree), "HEAD"], cwd=root, check=True)

            state_root = Path(state_dir)
            unit_id = "112233445566"
            prior_run_id = "run-greeting-prior"
            now_run_id = "run-greeting-now"

            try:
                # A genuinely interrupted Run: greeting#02 reached the Implement phase in worktree W and
                # nothing else — no phase.finished, run.cancelled, or run.finished.
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:00:00Z", "run": prior_run_id, "event": "run.started",
                    "data": {"repositoryRoot": str(root), "policyHash": "greetingpolicy", "tier": "reference", "staleAfterSeconds": 900},
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:01:00Z", "run": prior_run_id, "event": "phase.started",
                    "issue": "greeting#02", "phase": "Implement", "data": {"worktree": str(issue_worktree)},
                })
                # ...and it already burned one correction attempt: a real refutation followed by a
                # later Implement phase.started, so `runlog.py corrections` derives `1`, not `0`.
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:02:00Z", "run": prior_run_id, "event": "refutation",
                    "issue": "greeting#02", "phase": "Critic", "data": {"attempt": 1, "refutations": ["prior refutation"]},
                })
                self.append_runlog_event(state_root, unit_id, prior_run_id, {
                    "ts": "2026-09-13T09:03:00Z", "run": prior_run_id, "event": "phase.started",
                    "issue": "greeting#02", "phase": "Implement", "data": {"worktree": str(issue_worktree)},
                })

                # The next `gantry greeting` invocation queries `runlog.py inflight` and offers W.
                inflight = subprocess.run(
                    [sys.executable, str(SCRIPTS / "runlog.py"), "inflight", unit_id, "--state-root", str(state_root), "--json"],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(0, inflight.returncode, inflight.stderr)
                payload = json.loads(inflight.stdout)
                self.assertEqual(1, len(payload["inflight"]))
                match = payload["inflight"][0]
                self.assertEqual("greeting#02", match["issue"])
                self.assertEqual("Implement", match["phase"])
                self.assertEqual(str(issue_worktree), match["worktree"])

                corrections_spent = self.run_corrections_command(state_root, unit_id, match["run"], match["issue"])
                self.assertEqual(1, corrections_spent)

                # Choosing to continue in W resumes round-workflow. The Critic refutes, so this proves
                # `greeting#02` stays `ready-for-agent` while the Run records the continuation.
                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "greeting#02", "path": str(issue.relative_to(root)), "title": "Greeting CLI", "specPath": ".scratch/greeting/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/greeting",
                        "baseRef": "HEAD",
                        "isolate": True,
                        "correctionBudget": 2,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "runId": now_run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "priorRun": {
                            "run": match["run"], "worktree": match["worktree"], "issue": match["issue"],
                            "correctionsSpent": corrections_spent, "policyHash": match["policyHash"],
                        },
                        "criticResult": {
                            "complete": False, "criteria": [], "gatesVerdict": "fail",
                            "gateResult": {"verdict": "fail"}, "gateFailures": ["still not proven"],
                            "refutations": ["cli.py prints to stderr"], "requiredFixes": ["fix cli.py"],
                            "decisionsForOperator": [],
                        },
                    },
                )

                delivery = run["result"]["results"][0]
                self.assertEqual("refuted", delivery["outcome"])
                self.assertEqual(str(issue_worktree), delivery["worktree"])
                # Only the one remaining correction attempt (budget 2 minus the 1 already spent) is
                # available: the resumed round spends it and then blocks at the ceiling.
                self.assertEqual(2, delivery["corrections"])

                events = self.read_run_log_events(state_root, unit_id, now_run_id)
                self.assertEqual("run.started", events[0]["event"])
                resumed = next(event for event in events if event["event"] == "run.resumed")
                self.assertEqual(prior_run_id, resumed["data"]["priorRun"])
                self.assertEqual(str(issue_worktree), resumed["data"]["worktree"])
                self.assertEqual("greeting#02", resumed["data"]["issue"])
                self.assertEqual(1, resumed["data"]["correctionsSpent"])
                refutation = next(event for event in events if event["event"] == "refutation")
                self.assertIn("cli.py prints to stderr", refutation["data"]["refutations"])
                blocked = next(event for event in events if event["event"] == "issue.blocked")
                self.assertEqual("greeting#02", blocked["issue"])
                self.assertEqual(str(issue_worktree), blocked["data"]["worktree"])
                self.assertEqual(2, blocked["data"]["corrections"])

                # Status authority stays in the Issue file: greeting#02 keeps Status: ready-for-agent
                # until the Critic accepts it, and `frontier.py` still reports it as workable.
                self.assertEqual(before_issue, issue.read_bytes())
                self.assertIn(b"Status: ready-for-agent", issue.read_bytes())
                frontier = subprocess.run(
                    [sys.executable, str(SCRIPTS / "frontier.py"), "--scope", "greeting",
                     "--scratch", ".scratch", "--json"],
                    cwd=root, text=True, capture_output=True, check=False,
                )
                self.assertEqual(0, frontier.returncode, frontier.stderr)
                frontier_payload = json.loads(frontier.stdout)
                self.assertIn("greeting#02", [ref for round_ in frontier_payload["rounds"] for ref in round_])
                self.assertEqual({}, frontier_payload["parked"])
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def run_corrections_command(self, state_root: Path, unit_id: str, run_id: str, issue_ref: str) -> int:
        """Invoke the shipped `runlog.py corrections` query preflight must call (SKILL.md's rule)."""
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "runlog.py"), "corrections", unit_id, run_id, issue_ref,
             "--state-root", str(state_root), "--json"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)["correctionsSpent"]

    def test_append_run_event_fails_loudly_when_runlog_rejects_a_prohibited_key(self) -> None:
        # Covers feedback item 2: `appendRunEvent` must check the exit code of `runlog.py append` and
        # fail loudly instead of silently discarding a rejected event. `projectCriticResult` narrows a
        # recorded Critic verdict's `gateResult` to only `verdict` and `requirements`, deliberately
        # dropping any other `gateResult` field (such as a real gates.py run's `gates[]` or a stray
        # `diff`) so a genuine gate-green Critic pass can still be recorded. `requirements` itself passes
        # through unchanged, so a prohibited key nested inside it (not a sibling `gateResult` field, which
        # the projection now strips before it ever reaches `runlog.py`) still reaches `runlog.py`'s own
        # prohibited-key check and must still surface as a thrown error, not a silently missing line.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "recordfail#01", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            state_root = Path(state_dir)
            unit_id = "abcdefabcdef"
            run_id = "run-recordfail-1"

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "recordfail#01", "path": str(issue.relative_to(root)), "title": "Record failure", "specPath": ".scratch/recordfail/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/recordfail",
                    "baseRef": base_ref,
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "commandMode": "real",
                    "runId": run_id,
                    "unitId": unit_id,
                    "stateRoot": str(state_root),
                    "tier": "reference",
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                        # `gateResult` permits additionalProperties, so this passes result.py's schema.
                        # `projectCriticResult` keeps `requirements` unchanged, so a prohibited key nested
                        # inside one of its entries still reaches `runlog.py`'s own prohibited-key check
                        # at every nesting level, even though a sibling `gateResult` field (like a bare
                        # `diff`) would now be dropped by the projection before ever reaching `runlog.py`.
                        "gateResult": {"verdict": "pass", "requirements": [{"command": "leaked command"}]},
                    },
                },
            )

            self.assertIsNone(run["result"])
            self.assertIsNotNone(run["error"])
            self.assertIn("workflow command failed", run["error"])
            self.assertIn("runlog.py", run["error"])

            # The rejected event never reaches the log: no subagent.stopped line for the Critic
            # phase exists, even though the phase.started/subagent.started pair that preceded it do.
            events = self.read_run_log_events(state_root, unit_id, run_id)
            self.assertIn("run.started", [event["event"] for event in events])
            critic_events = [event for event in events if event.get("phase") == "Critic"]
            self.assertIn("phase.started", [event["event"] for event in critic_events])
            self.assertIn("subagent.started", [event["event"] for event in critic_events])
            self.assertNotIn("subagent.stopped", [event["event"] for event in critic_events])

    def test_round_workflow_chained_resume_accumulates_corrections_spent_across_runs(self) -> None:
        # Covers feedback item 3: a chain of three Runs, each resuming the last, where the documented
        # derivation rule (`run.resumed.data.correctionsSpent` plus refutations that actually started a
        # correction pass) must be applied fresh to each Run's own log and carried forward explicitly.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "chained#01", "ready-for-agent")
            self.write_roadmap(root)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)

            issue_branch = "gantry/chained-01"
            issue_worktree = Path(f"{root}.gantry-chained-01")
            subprocess.run(["git", "worktree", "add", "--quiet", "-b", issue_branch, str(issue_worktree), "HEAD"], cwd=root, check=True)

            state_root = Path(state_dir)
            unit_id = "fefefefefefe"

            try:
                # Run1: a genuinely interrupted Run with one refutation that already started a
                # correction pass (a later `phase.started` Implement for the same Issue).
                run1_id = "run-chained-1"
                self.append_runlog_event(state_root, unit_id, run1_id, {
                    "ts": "2026-09-13T09:00:00Z", "run": run1_id, "event": "run.started",
                    "data": {"repositoryRoot": str(root), "policyHash": "policy1", "tier": "reference", "staleAfterSeconds": 900},
                })
                self.append_runlog_event(state_root, unit_id, run1_id, {
                    "ts": "2026-09-13T09:01:00Z", "run": run1_id, "event": "phase.started",
                    "issue": "chained#01", "phase": "Implement", "data": {"worktree": str(issue_worktree)},
                })
                self.append_runlog_event(state_root, unit_id, run1_id, {
                    "ts": "2026-09-13T09:02:00Z", "run": run1_id, "event": "refutation",
                    "issue": "chained#01", "phase": "Critic", "data": {"attempt": 1, "refutations": ["first refutation"]},
                })
                self.append_runlog_event(state_root, unit_id, run1_id, {
                    "ts": "2026-09-13T09:03:00Z", "run": run1_id, "event": "phase.started",
                    "issue": "chained#01", "phase": "Implement", "data": {"worktree": str(issue_worktree)},
                })
                # No phase.finished, run.cancelled, or run.finished: Run1 is interrupted mid-correction.

                run1_corrections = self.run_corrections_command(state_root, unit_id, run1_id, "chained#01")
                self.assertEqual(1, run1_corrections)

                # Run2 resumes Run1, carrying the derived correctionsSpent forward explicitly, and its
                # Critic refutes twice before the correction ceiling (budget 2) is reached.
                run2_id = "run-chained-2"
                run2 = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "chained#01", "path": str(issue.relative_to(root)), "title": "Chained", "specPath": ".scratch/chained/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/chained",
                        "baseRef": "HEAD",
                        "isolate": True,
                        "correctionBudget": 2,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "runId": run2_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "priorRun": {
                            "run": run1_id,
                            "worktree": str(issue_worktree),
                            "issue": "chained#01",
                            "correctionsSpent": run1_corrections,
                            "policyHash": "policy1",
                        },
                        "criticResults": [
                            {
                                "complete": False, "criteria": [], "gatesVerdict": "fail",
                                "gateResult": {"verdict": "fail"}, "gateFailures": ["still not proven"],
                                "refutations": ["second refutation"], "requiredFixes": ["add real evidence"],
                                "decisionsForOperator": [],
                            },
                            {
                                "complete": False, "criteria": [], "gatesVerdict": "fail",
                                "gateResult": {"verdict": "fail"}, "gateFailures": ["still not proven"],
                                "refutations": ["third refutation"], "requiredFixes": ["add more evidence"],
                                "decisionsForOperator": [],
                            },
                        ],
                    },
                )

                delivery2 = run2["result"]["results"][0]
                self.assertEqual("refuted", delivery2["outcome"])
                self.assertEqual(2, delivery2["corrections"])
                critic_calls_run2 = [call for call in run2["calls"] if call["label"].startswith("critic:")]
                self.assertEqual(2, len(critic_calls_run2))

                run2_events = self.read_run_log_events(state_root, unit_id, run2_id)
                resumed2 = next(event for event in run2_events if event["event"] == "run.resumed")
                self.assertEqual(1, resumed2["data"]["correctionsSpent"])
                self.assertEqual(run1_id, resumed2["data"]["priorRun"])
                self.assertEqual("chained#01", resumed2["data"]["issue"])

                run2_corrections = self.run_corrections_command(state_root, unit_id, run2_id, "chained#01")
                self.assertEqual(2, run2_corrections)
                blocked2 = next(event for event in run2_events if event["event"] == "issue.blocked")
                self.assertEqual(2, blocked2["data"]["corrections"])

                # Run3 resumes Run2 with the derived ceiling already spent: zero correction passes,
                # exactly one initial Implement call and one Critic call, then the Issue blocks again.
                run3_id = "run-chained-3"
                run3 = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [{"ref": "chained#01", "path": str(issue.relative_to(root)), "title": "Chained", "specPath": ".scratch/chained/spec.md"}],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": "gantry/chained",
                        "baseRef": "HEAD",
                        "isolate": True,
                        "correctionBudget": 2,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "runId": run3_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "issueBranch": issue_branch,
                        "issueWorktree": str(issue_worktree),
                        "priorRun": {
                            "run": run2_id,
                            "worktree": str(issue_worktree),
                            "issue": "chained#01",
                            "correctionsSpent": run2_corrections,
                            "policyHash": "policy1",
                        },
                        "criticResult": {
                            "complete": False, "criteria": [], "gatesVerdict": "fail",
                            "gateResult": {"verdict": "fail"}, "gateFailures": ["still not proven"],
                            "refutations": ["fourth refutation"], "requiredFixes": ["add even more evidence"],
                            "decisionsForOperator": [],
                        },
                    },
                )

                delivery3 = run3["result"]["results"][0]
                self.assertEqual("refuted", delivery3["outcome"])
                self.assertEqual(2, delivery3["corrections"])
                implement_calls_run3 = [call for call in run3["calls"] if call["label"].startswith("implement:")]
                critic_calls_run3 = [call for call in run3["calls"] if call["label"].startswith("critic:")]
                self.assertEqual(1, len(implement_calls_run3))
                self.assertEqual(1, len(critic_calls_run3))

                run3_events = self.read_run_log_events(state_root, unit_id, run3_id)
                blocked3 = next(event for event in run3_events if event["event"] == "issue.blocked")
                self.assertEqual(2, blocked3["data"]["corrections"])
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(issue_worktree)], cwd=root, check=False)

    def test_round_workflow_isolated_multi_issue_round_stops_the_run_on_a_red_post_merge_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as state_dir:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue_one = self.write_issue(root, "multi#01", "ready-for-agent")
            issue_two = self.write_issue(root, "multi#02", "ready-for-agent")
            self.write_roadmap(root)
            (root / "Makefile").write_text(
                "test:\n"
                "\t@n=$$(( $$(cat .gatecount 2>/dev/null || echo 0) + 1 )); echo $$n > .gatecount; test $$n -lt 2\n",
                encoding="utf-8",
            )
            (root / ".gitignore").write_text(".gatecount\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            run_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

            worktree_one = Path(f"{root}.gantry-multi-01")
            worktree_two = Path(f"{root}.gantry-multi-02")
            state_root = Path(state_dir)
            unit_id = "efefefefefef"
            run_id = "run-multi-3"

            try:
                run = self.run_workflow(
                    "round-workflow.md",
                    {
                        "round": 1,
                        "issues": [
                            {"ref": "multi#01", "path": str(issue_one.relative_to(root)), "title": "Multi one", "specPath": ".scratch/multi/spec.md"},
                            {"ref": "multi#02", "path": str(issue_two.relative_to(root)), "title": "Multi two", "specPath": ".scratch/multi/spec.md"},
                        ],
                        "models": {"implement": "implement", "review": "review", "critic": "critic"},
                        "branch": run_branch,
                        "baseRef": base_ref,
                        "isolate": True,
                        "correctionBudget": 0,
                        "skillDir": str(SKILL_DIR),
                        "repoRoot": str(root),
                        "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 0}},
                        "paths": {},
                        "date": "2026-09-13",
                        "commandMode": "real",
                        "runId": run_id,
                        "unitId": unit_id,
                        "stateRoot": str(state_root),
                        "tier": "reference",
                        "implementerCommitText": "integrated\n",
                        "issueAssignments": {
                            "multi#01": {"worktree": str(worktree_one), "branch": "gantry/multi-01"},
                            "multi#02": {"worktree": str(worktree_two), "branch": "gantry/multi-02"},
                        },
                        "criticResults": [
                            {"criteria": self.critic_evidence(root, issue_one)},
                            {"criteria": self.critic_evidence(root, issue_two)},
                        ],
                    },
                )

                outcomes = {result["ref"]: result["outcome"] for result in run["result"]["results"]}
                self.assertEqual("done", outcomes["multi#01"])
                self.assertEqual("integration_failed", outcomes["multi#02"])
                self.assertEqual("done", parse_issue(issue_one).status)
                self.assertEqual("ready-for-agent", parse_issue(issue_two).status)
                commands = [call["command"] for call in run["commandCalls"]]
                self.assertEqual(1, sum('roadmap.py" done' in command for command in commands))
                self.assertIn('roadmap.py" done multi#01', "\n".join(commands))

                events = self.read_run_log_events(state_root, unit_id, run_id)
                self.assertEqual(["multi#01"], [event["issue"] for event in events if event["event"] == "issue.done"])
                self.assertEqual([], [event for event in events if event["event"] == "issue.blocked"])
                cancelled = next(event for event in events if event["event"] == "run.cancelled")
                self.assertEqual("multi#02", cancelled["issue"])
                self.assertEqual("integration_gate_failed", cancelled["data"]["reason"])
                self.assertNotIn("run.finished", [event["event"] for event in events])

                # Serial integration: exactly one `--no-ff` merge and one gate run per Issue, in Issue
                # order, and merges/gates never run again after the red post-merge gate stops the Run.
                merge_indexes = [
                    index for index, call in enumerate(run["commandCalls"])
                    if "git merge --no-ff" in call["command"]
                ]
                gate_indexes = [
                    index for index, call in enumerate(run["commandCalls"])
                    if 'gates.py" --run' in call["command"]
                ]
                self.assertEqual(2, len(merge_indexes))
                self.assertEqual(2, len(gate_indexes))
                self.assertIn('gantry/multi-01', run["commandCalls"][merge_indexes[0]]["command"])
                self.assertIn('gantry/multi-02', run["commandCalls"][merge_indexes[1]]["command"])
                merge_one, merge_two = merge_indexes
                gate_one, gate_two = gate_indexes
                self.assertLess(merge_one, gate_one)
                self.assertLess(gate_one, merge_two)
                self.assertLess(merge_two, gate_two)
                # No further merge or gate command runs after the red post-merge gate stops the Run.
                after_red_gate = run["commandCalls"][gate_two + 1:]
                self.assertFalse(any("git merge --no-ff" in call["command"] for call in after_red_gate))
                self.assertFalse(any('gates.py" --run' in call["command"] for call in after_red_gate))
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree_one)], cwd=root, check=False)
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree_two)], cwd=root, check=False)

    def test_roadmap_check_reports_drift_from_issue_files_not_from_the_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "drift#01", "ready-for-agent")
            self.write_roadmap(root)

            state_root = root / "state"
            unit_id = "010101010101"
            run_id = "run-drift-1"
            append = subprocess.run(
                [sys.executable, str(SCRIPTS / "runlog.py"), "append", unit_id, run_id, "--state-root", str(state_root)],
                input=json.dumps({
                    "ts": "2026-09-13T00:00:00Z", "run": run_id, "event": "run.started",
                    "data": {"repositoryRoot": str(root), "policyHash": "deadbeef", "tier": "reference", "staleAfterSeconds": 900},
                }),
                cwd=root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, append.returncode, append.stderr)
            append_done = subprocess.run(
                [sys.executable, str(SCRIPTS / "runlog.py"), "append", unit_id, run_id, "--state-root", str(state_root)],
                input=json.dumps({"ts": "2026-09-13T00:01:00Z", "run": run_id, "event": "issue.done", "issue": "drift#01"}),
                cwd=root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, append_done.returncode, append_done.stderr)

            # Hand-tick the roadmap without going through roadmap.py or the Issue's own Status line.
            roadmap_path = root / "ROADMAP.md"
            roadmap_path.write_text(
                roadmap_path.read_text(encoding="utf-8").replace(
                    "<!-- BEGIN GENERATED: issue checklist -->",
                    "<!-- BEGIN GENERATED: issue checklist -->\n- [x] **`drift#01`** — Example",
                ),
                encoding="utf-8",
            )

            check = self.run_script(root, "roadmap.py", "check", "--json")
            self.assertEqual(1, check.returncode, check.stdout + check.stderr)
            payload = json.loads(check.stdout)
            self.assertTrue(payload.get("drift") or payload.get("mismatches") or payload.get("issues"))
            self.assertEqual("ready-for-agent", parse_issue(issue).status)

    def test_round_workflow_keeps_protected_rules_in_prompts_with_no_hooks_configured(self) -> None:
        # docs/adr/0003-scripts-decide-hooks-guard-and-record.md: scripts, not hooks, decide and record —
        # hooks are an optional, harness-specific guard. `run_workflow`'s driver supplies no `hooks` at
        # all, so this proves the protected-rules text lives in the prompts themselves (and in Critic
        # verification) rather than depending on any hook to enforce it.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            subprocess.run(["git", "config", "user.email", "gantry@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Gantry Test"], cwd=root, check=True)
            issue = self.write_issue(root, "nohooks#01", "ready-for-agent")
            roadmap = self.write_roadmap(root)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            before_issue = issue.read_bytes()
            before_roadmap = roadmap.read_bytes()

            run = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "nohooks#01", "path": str(issue.relative_to(root)), "title": "No hooks", "specPath": ".scratch/nohooks/spec.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/nohooks",
                    "baseRef": "HEAD",
                    "isolate": False,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
                    "paths": {},
                    "date": "2026-09-13",
                    "criticResult": {
                        "complete": False,
                        "criteria": [],
                        "gatesVerdict": "fail",
                        "gateResult": {"verdict": "fail"},
                        "gateFailures": ["not proven"],
                        "refutations": ["criterion one remains unproven"],
                        "requiredFixes": ["add real evidence"],
                        "decisionsForOperator": [],
                    },
                },
            )

            implement_calls = [call for call in run["calls"] if call["label"].startswith("implement:")]
            critic_calls = [call for call in run["calls"] if call["label"].startswith("critic:")]
            self.assertTrue(implement_calls)
            self.assertTrue(critic_calls)
            for call in implement_calls:
                self.assertIn("Never edit ROADMAP.md, Status, or criteria checkboxes", call["prompt"])
            for call in critic_calls:
                self.assertIn("never trust the Implementer", call["prompt"])
                self.assertIn("must never be raised", call["prompt"])

            self.assertEqual(before_issue, issue.read_bytes())
            self.assertEqual(before_roadmap, roadmap.read_bytes())

    def test_frontier_rejects_invalid_graphs_and_uses_authoritative_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_issue(root, "chain#01", "done")
            self.write_issue(root, "chain#02", "ready-for-agent", ["chain#01"])
            self.write_issue(root, "chain#03", "ready-for-agent", ["chain#02"])
            self.write_issue(root, "chain#04", "draft")
            self.write_issue(root, "chain#05", "blocked")
            self.write_issue(root, "chain#06", "needs-operator")
            valid = self.run_script(root, "frontier.py", "--scope", "chain", "--json")
            self.assertEqual(0, valid.returncode, valid.stderr)
            payload = json.loads(valid.stdout)
            self.assertEqual([["chain#02"], ["chain#03"]], payload["rounds"])
            self.assertEqual(
                {"chain#04": "draft", "chain#05": "blocked", "chain#06": "needs-operator"},
                payload["parked"],
            )

            self.write_issue(root, "cycle#01", "ready-for-agent", ["cycle#02"])
            self.write_issue(root, "cycle#02", "ready-for-agent", ["cycle#01"])
            cyclic = self.run_script(root, "frontier.py", "--scope", "cycle", "--json")
            self.assertEqual(1, cyclic.returncode)
            self.assertTrue(json.loads(cyclic.stdout)["errors"])

            self.write_issue(root, "dangling#01", "ready-for-agent", ["missing#01"])
            dangling = self.run_script(root, "frontier.py", "--scope", "dangling", "--json")
            self.assertEqual(1, dangling.returncode)
            self.assertIn("does not exist", "\n".join(json.loads(dangling.stdout)["errors"]))

    def test_frontier_validates_parked_issue_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_issue(root, "parked#01", "draft", ["parked#02"])
            self.write_issue(root, "parked#02", "needs-operator", ["parked#01"])
            result = self.run_script(root, "frontier.py", "--scope", "frontier", "--json")

            self.assertEqual(1, result.returncode)
            self.assertIn("dependency cycle", "\n".join(json.loads(result.stdout)["errors"]))

    def test_frontier_reports_parked_issues_before_readiness_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            self.write_issue(root, "waiting#01", "ready-for-agent", ["waiting#02"])
            self.write_issue(root, "waiting#02", "draft", ["waiting#03"])
            self.write_issue(root, "waiting#03", "blocked", ["waiting#04"])
            self.write_issue(root, "waiting#04", "needs-operator")

            result = self.run_script(root, "frontier.py", "--scope", "frontier", "--json")

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(
                {
                    "waiting#02": "draft",
                    "waiting#03": "blocked",
                    "waiting#04": "needs-operator",
                },
                payload["parked"],
            )
            self.assertEqual([], payload["rounds"])

    def test_acceptance_cli_is_read_only_and_roadmap_done_is_state_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue = self.write_issue(root, "state#01", "ready-for-agent")
            roadmap = self.write_roadmap(root)
            before_issue = issue.read_bytes()
            before_roadmap = roadmap.read_bytes()

            mutable = self.run_script(root, "acceptance.py", "state#01", "--tick", "all")

            self.assertEqual(2, mutable.returncode)
            self.assertEqual(before_issue, issue.read_bytes())
            self.assertEqual(before_roadmap, roadmap.read_bytes())

            done = self.run_script(root, "roadmap.py", "done", "state#01")

            self.assertEqual(0, done.returncode, done.stderr)
            parsed = parse_issue(issue)
            self.assertTrue(parsed.done)
            self.assertTrue(all(criterion.checked for criterion in parsed.criteria))
            self.assertIn("state#01", roadmap.read_text(encoding="utf-8"))

    def test_custom_artifact_policy_drives_frontier_roadmap_and_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            config = root / ".gantry" / "config.json"
            config.parent.mkdir()
            policy = {
                "artifacts": {"specs": "product/{slug}.md", "issues": "work/{slug}"},
                "git": {"target": "main", "prefix": "gantry/"},
                "budget": {"corrections": 2},
            }
            config.write_text(
                json.dumps(policy),
                encoding="utf-8",
            )
            spec = root / "product" / "portable.md"
            spec.parent.mkdir()
            spec.write_text("# Portable Spec\n", encoding="utf-8")
            issue = root / "work" / "portable" / "01-portable.md"
            issue.parent.mkdir(parents=True)
            issue.write_text(
                """# Portable issue

Type: issue
Status: ready-for-agent
Slice: `portable#01`

## Acceptance criteria

- [ ] executes through the effective artifact policy

## Blocked by

- None
""",
                encoding="utf-8",
            )
            roadmap = self.write_roadmap(root)

            frontier = self.run_script(root, "frontier.py", "--scope", "portable", "--json")
            accepted = self.run_script(root, "acceptance.py", "portable#01", "--json")
            waves = self.run_script(root, "roadmap.py", "waves", "--json")
            checked = self.run_script(root, "roadmap.py", "check", "--json")

            self.assertEqual(0, frontier.returncode, frontier.stderr)
            self.assertEqual("work/portable/01-portable.md", json.loads(frontier.stdout)["issues"]["portable#01"]["path"])
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertEqual("product/portable.md", json.loads(accepted.stdout)["spec_path"])
            self.assertEqual(0, waves.returncode, waves.stderr)
            self.assertEqual(0, checked.returncode, checked.stderr)
            self.assertIn("portable#01", roadmap.read_text(encoding="utf-8"))

            paths = {
                "issueDir": str(root / "work" / "portable"),
                "specPath": str(spec),
                "exemplarIssue": str(issue),
                "decisions": str(root / "docs" / "adr"),
                "issueTracker": str(root / "docs" / "agents" / "issue-tracker.md"),
                "context": str(root / "CONTEXT.md"),
                "adrs": str(root / "docs" / "adr"),
            }
            plan = self.run_workflow(
                "plan-workflow.md",
                {
                    "target": {"kind": "spec", "slug": "portable", "specPath": str(spec)},
                    "models": {"plan": "plan", "critic": "critic"},
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": policy,
                    "paths": paths,
                    "date": "2026-09-13",
                },
            )
            round_result = self.run_workflow(
                "round-workflow.md",
                {
                    "round": 1,
                    "issues": [{"ref": "portable#01", "path": "work/portable/01-portable.md", "title": "Portable issue", "specPath": "product/portable.md"}],
                    "models": {"implement": "implement", "review": "review", "critic": "critic"},
                    "branch": "gantry/portable",
                    "baseRef": "HEAD",
                    "isolate": True,
                    "correctionBudget": 2,
                    "skillDir": str(SKILL_DIR),
                    "repoRoot": str(root),
                    "policy": policy,
                    "paths": paths,
                    "date": "2026-09-13",
                },
            )
            self.assertTrue(any(call["label"] == "plan" for call in plan["calls"]))
            self.assertTrue(any(call["label"] == "critic:portable#01#1" for call in round_result["calls"]))

    def test_templates_and_canonical_parser_keep_legacy_issue_state(self) -> None:
        required = {
            "spec.md": ("# Spec:", "## Blueprint", "## Contract", "## Out of Scope", "## Changelog"),
            "prd.md": ("# Product Requirements", "## 1. Problem", "## 2. Principles", "## 3. Scope"),
            "issue.md": (
                "Type: issue",
                "Status: draft",
                "Slice:",
                "Spec:",
                "Created:",
                "## Parent",
                "## What to build",
                "## Acceptance criteria",
                "## Blocked by",
                "## Comments",
            ),
        }
        for name, headings in required.items():
            text = (SKILL_DIR / "templates" / name).read_text(encoding="utf-8")
            for heading in headings:
                self.assertIn(heading, text, name)
        issue_template = (SKILL_DIR / "templates" / "issue.md").read_text(encoding="utf-8")
        self.assertIn("### Files to read", issue_template)
        self.assertIn("- `<repository-relative-path>`", issue_template)
        plan_workflow = (SKILL_DIR / "reference" / "plan-workflow.md").read_text(encoding="utf-8")
        self.assertIn("### Files to read", plan_workflow)
        self.assertIn("repository-relative paths", plan_workflow)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            issue_path = root / ".scratch" / "legacy" / "issues" / "07-existing-format.md"
            issue_path.parent.mkdir(parents=True)
            issue_path.write_text(
                """# Existing legacy Issue

Type: issue
Status: ready-for-agent
Slice: `legacy#07`

## Acceptance criteria

- [ ] preserves the persisted execution state

## Blocked by

- `other#02` — an existing dependency
""",
                encoding="utf-8",
            )
            before = issue_path.read_bytes()
            issue = parse_issue(issue_path)
            self.assertEqual("legacy#07", issue.ref)
            self.assertEqual("ready-for-agent", issue.status)
            self.assertEqual(["other#02"], issue.blocked_by)
            self.assertEqual(["preserves the persisted execution state"], [criterion.text for criterion in issue.criteria])
            parsed = self.run_script(root, "acceptance.py", str(issue_path), "--json")
            self.assertEqual(0, parsed.returncode, parsed.stderr)
            self.assertEqual("ready-for-agent", json.loads(parsed.stdout)["status"])
            self.assertEqual(before, issue_path.read_bytes())

    def test_workflow_templates_preserve_canonical_phase_boundaries(self) -> None:
        plan = (SKILL_DIR / "reference" / "plan-workflow.md").read_text(encoding="utf-8")
        self.assertIn("Status: draft", plan)
        self.assertRegex(plan, r"stop for explicit operator\s+approval")
        self.assertIn("never write `ROADMAP.md`", plan)
        self.assertLess(plan.index("Status: draft"), plan.index("stop for explicit operator"))
        self.assertLess(plan.index("status <ref> ready-for-agent"), plan.index("roadmap.py\" waves"))
        self.assertLess(plan.index("roadmap.py\" waves"), plan.index("roadmap.py\" check"))

        round_workflow = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8")
        for phrase in (
            "red → green TDD",
            "standards:",
            "Spec:",
            "fresh adversarial Critic",
            "own worktree and branch",
            "one at a time with `git merge --no-ff`",
            "result.py",
            "--schema",
        ):
            self.assertIn(phrase, round_workflow)
        self.assertNotIn("const IMPL_SCHEMA", round_workflow)
        self.assertNotIn("const REVIEW_SCHEMA", round_workflow)
        self.assertNotIn("const CRITIC_SCHEMA", round_workflow)
        self.assertIn("result.py", plan)
        self.assertIn("--schema", plan)
        self.assertNotIn("const PLAN_SCHEMA", plan)
        self.assertNotIn("const CRITIQUE_SCHEMA", plan)
        self.assertEqual(1, round_workflow.count("roadmap.py done <ref>"))
        self.assertLess(round_workflow.index("**Implementer:**"), round_workflow.index("**Reviewer:**"))
        self.assertLess(round_workflow.index("**Reviewer:**"), round_workflow.index("**Critic:**"))
        self.assertLess(round_workflow.index("**Critic:**"), round_workflow.index("## Isolation and integration"))

    def test_spec_changelog_records_the_canonical_workflow_in_english(self) -> None:
        spec = (REPO_ROOT / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        self.assertIn(
            "2026-09-13 — Added the canonical harness-neutral Gantry workflow skill, "
            "default templates and portable legacy script contracts with regression coverage.",
            spec,
        )
        self.assertIn(
            "Wired the canonical `SKILL.md` preflight and `round-workflow.md` execution to the Run log",
            spec,
        )
        for phrase in (
            "run.started",
            "run.resumed",
            "preserved worktree",
            "spent correction attempts retained",
        ):
            self.assertIn(phrase, spec)

    def test_canonical_scripts_import_only_standard_library_or_pack_modules(self) -> None:
        allowed = {
            "__future__",
            "acceptance",
            "argparse",
            "caveman",
            "common",
            "copy",
            "dataclasses",
            "datetime",
            "difflib",
            "discovery",
            "hashlib",
            "http",
            "json",
            "os",
            "pathlib",
            "re",
            "runlog",
            "shlex",
            "shutil",
            "skipscan",
            "subprocess",
            "sys",
            "tempfile",
            "threading",
            "time",
            "typing",
        }
        self.assertEqual(
            {"acceptance.py", "budget.py", "caveman.py", "cleanup.py", "common.py", "dashboard.py", "discovery.py", "frontier.py", "gates.py", "guard.py", "learner.py", "result.py", "roadmap.py", "runlog.py", "setup.py", "spec.py"},
            {script.name for script in SCRIPTS.glob("*.py")},
        )
        git_hooks = SKILL_DIR / "hooks" / "git"
        for script in sorted([*SCRIPTS.glob("*.py"), git_hooks / "pre-commit", git_hooks / "pre-push", git_hooks / "skipscan.py"]):
            tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
            imported = {
                alias.name.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imported |= {
                node.module.split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            self.assertLessEqual(imported, allowed, f"{script.name}: {sorted(imported - allowed)}")


if __name__ == "__main__":
    unittest.main()
