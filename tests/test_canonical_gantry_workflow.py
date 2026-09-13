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
const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd || args.repoRoot }});
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
  return {{ exitCode: 0, stdout: command.includes('/gates.py') ? '{{"verdict":"pass"}}' : '' }};
}};
const agent = async (prompt, options) => {{
  calls.push({{ label: options.label, prompt }});
  if (options.label.startsWith('research:')) return 'factual research';
  if (options.label.startsWith('plan')) {{
    if (args.plannerRawResults && args.plannerRawResults.length) {{
      return args.plannerRawResults.shift();
    }}
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
    return {{
    worktree: args.repoRoot, branch: args.issueBranch || args.branch, commits: ['test commit'],
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
const result = await new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'runCommand', source)(
  args, agent, parallel, pipeline, phase, log, runCommand,
);
process.stdout.write(JSON.stringify({{ result, calls, commandCalls }}));
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
        roles = ("planner", "plan-critic", "implementer", "reviewer", "critic", "learner")
        supported = {"type", "properties", "required", "items", "enum", "additionalProperties"}
        required_fields = {
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

            for script in ("common.py", "frontier.py", "acceptance.py", "gates.py", "roadmap.py", "result.py"):
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
                    "models": {"plan": "plan", "critic": "critic"},
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
                    "models": {"plan": "plan", "critic": "critic"},
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
            self.assertIn("planned#01", roadmap.read_text(encoding="utf-8"))

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
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            run_branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
            subprocess.run(["git", "checkout", "--quiet", "-b", "gantry/serial-issue"], cwd=root, check=True)
            (root / "delivery.txt").write_text("integrated\n", encoding="utf-8")
            subprocess.run(["git", "add", "delivery.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "delivery"], cwd=root, check=True)
            subprocess.run(["git", "checkout", "--quiet", run_branch], cwd=root, check=True)

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
                    "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 0}},
                    "paths": {},
                    "date": "2026-09-13",
                    "issueBranch": "gantry/serial-issue",
                    "commandMode": "real",
                    "criticResult": {
                        "criteria": self.critic_evidence(root, issue),
                    },
                },
            )

            self.assertEqual("done", run["result"]["results"][0]["outcome"])
            self.assertEqual("done", parse_issue(issue).status)
            commands = [call["command"] for call in run["commandCalls"]]
            self.assertEqual(9, len(commands))
            self.assertIn('result.py" --role "implementer" --json', commands[0])
            self.assertIn('result.py" --role "reviewer" --json', commands[1])
            self.assertIn('result.py" --role "critic" --json', commands[2])
            self.assertIn('acceptance.py"', commands[3])
            self.assertIn('git merge --no-ff "gantry/serial-issue"', commands[4])
            self.assertIn('gates.py" --run', commands[5])
            self.assertIn('roadmap.py" done serial#01', commands[6])
            self.assertIn('git add -- ROADMAP.md', commands[7])
            self.assertIn('git commit -m "gantry: complete serial#01"', commands[8])
            self.assertFalse(any('roadmap.py" status' in command for command in commands))

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

    def test_canonical_scripts_import_only_standard_library_or_pack_modules(self) -> None:
        allowed = {
            "__future__",
            "acceptance",
            "argparse",
            "common",
            "copy",
            "dataclasses",
            "datetime",
            "difflib",
            "json",
            "os",
            "pathlib",
            "re",
            "shutil",
            "subprocess",
            "sys",
            "tempfile",
            "typing",
        }
        self.assertEqual(
            {"acceptance.py", "common.py", "frontier.py", "gates.py", "result.py", "roadmap.py"},
            {script.name for script in SCRIPTS.glob("*.py")},
        )
        for script in sorted(SCRIPTS.glob("*.py")):
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
