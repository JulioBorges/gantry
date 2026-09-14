#!/usr/bin/env python3
"""Contracts for the optional Learner phase wired into the round-workflow Workflow script."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"


class LearnerWorkflowTests(unittest.TestCase):
    def run_round_workflow(self, args: dict) -> dict:
        source = (
            (SKILL_DIR / "reference" / "round-workflow.md")
            .read_text(encoding="utf-8")
            .split("```js\n", 1)[1]
            .split("\n```", 1)[0]
        )
        source = source.replace("export const meta", "const meta", 1)
        driver = f"""
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {json.dumps(args)};
const commandCalls = [];
const calls = [];
const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd || args.repoRoot }});
  if (command.includes('/learner.py')) {{
    return {{ exitCode: 0, stdout: JSON.stringify({{ candidates: args.extractedCandidates || [] }}), stderr: '' }};
  }}
  if (command.includes('/gates.py')) return {{ exitCode: 0, stdout: '{{"verdict":"pass"}}', stderr: '' }};
  return {{ exitCode: 0, stdout: '', stderr: '' }};
}};
const agent = async (prompt, options) => {{
  calls.push({{ label: options.label, prompt }});
  if (options.label === 'learn') return args.learnerAgentResult ?? {{ candidates: args.extractedCandidates || [] }};
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
        completed = subprocess.run(
            ["node", "--input-type=module", "--eval", driver],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def base_args(self, root: Path, **overrides: object) -> dict:
        args = {
            "round": 1,
            "issues": [],
            "models": {"implement": "implement", "review": "review", "critic": "critic"},
            "branch": "gantry/learn",
            "baseRef": "HEAD",
            "isolate": False,
            "correctionBudget": 2,
            "skillDir": str(SKILL_DIR),
            "repoRoot": str(root),
            "policy": {"git": {"target": "main", "prefix": "gantry/"}, "budget": {"corrections": 2}},
            "paths": {},
            "date": "2026-09-13",
        }
        args.update(overrides)
        return args

    def test_last_round_surfaces_recurring_candidates_from_the_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidates = [
                {
                    "lesson": "criterion 3 has no test",
                    "evidence": ["greeting#01: criterion 3 has no test", "greeting#03: criterion 3 has no test"],
                    "target": "AGENTS.md (Gantry section)",
                }
            ]

            result = self.run_round_workflow(
                self.base_args(
                    root,
                    isLastRound=True,
                    learnerRunLogs=[str(root / "run-01.jsonl")],
                    extractedCandidates=candidates,
                )
            )

            self.assertEqual(candidates, result["result"]["candidates"])
            self.assertTrue(any("/learner.py" in call["command"] for call in result["commandCalls"]))
            self.assertTrue(any(call["label"] == "learn" for call in result["calls"]))

    def test_non_last_round_never_invokes_the_learner(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            result = self.run_round_workflow(
                self.base_args(
                    root,
                    isLastRound=False,
                    learnerRunLogs=[str(root / "run-01.jsonl")],
                    extractedCandidates=[{"lesson": "x", "evidence": ["a#01: x", "a#02: x"], "target": "AGENTS.md"}],
                )
            )

            self.assertNotIn("candidates", result["result"])
            self.assertFalse(any("/learner.py" in call["command"] for call in result["commandCalls"]))
            self.assertFalse(any(call["label"] == "learn" for call in result["calls"]))

    def test_last_round_with_no_run_log_skips_the_learner(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            result = self.run_round_workflow(
                self.base_args(root, isLastRound=True, learnerRunLogs=[])
            )

            self.assertEqual([], result["result"]["candidates"])
            self.assertFalse(any("/learner.py" in call["command"] for call in result["commandCalls"]))

    def test_last_round_with_no_recurring_evidence_skips_the_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            result = self.run_round_workflow(
                self.base_args(
                    root,
                    isLastRound=True,
                    learnerRunLogs=[str(root / "run-01.jsonl")],
                    extractedCandidates=[],
                )
            )

            self.assertEqual([], result["result"]["candidates"])
            self.assertFalse(any(call["label"] == "learn" for call in result["calls"]))

    def test_skill_reports_lesson_candidates_as_operator_decisions(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("optional Learner", skill)
        self.assertIn("operator decision", skill)
        self.assertIn(
            "the workflow never writes a candidate\n  into `AGENTS.md`, `CONTEXT.md`, a template or policy on its own.",
            skill,
        )

    def test_round_workflow_documents_the_learner_phase_read_scope(self) -> None:
        round_workflow = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8")
        self.assertIn("## Learner phase (optional)", round_workflow)
        self.assertIn("never source files, `AGENTS.md`, `CONTEXT.md`, a template or", round_workflow)
        self.assertLess(
            round_workflow.index("## Learner phase (optional)"),
            round_workflow.index("## Isolation and integration"),
        )

    def test_round_workflow_documents_last_round_learner_args(self) -> None:
        round_workflow = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8")
        caller_args_section = round_workflow[: round_workflow.index("## Per-Issue roles")]
        self.assertIn("`args.isLastRound`", caller_args_section)
        self.assertIn("`args.learnerRunLogs`", caller_args_section)
        self.assertIn("`args.models.learn`", caller_args_section)
        self.assertIn("falls back to `args.models.critic`", caller_args_section)

    def test_round_workflow_declares_the_learn_phase_in_meta(self) -> None:
        round_workflow = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8")
        self.assertIn("{ title: 'Learn', detail: 'optional recurring lesson candidates for the operator' }", round_workflow)

    def test_skill_instructs_orchestrator_to_pass_learner_args(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("args.isLastRound = true", skill)
        self.assertIn("args.learnerRunLogs", skill)
        self.assertIn("~/.gantry/state/<unit-id>/runs/<run-id>.jsonl", skill)


if __name__ == "__main__":
    unittest.main()
