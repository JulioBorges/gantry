#!/usr/bin/env python3
"""Contracts for the deterministic Learner extraction of recurring lesson candidates."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS = SKILL_DIR / "scripts"
LEARNER = SCRIPTS / "learner.py"
RESULT = SCRIPTS / "result.py"


class LearnerTests(unittest.TestCase):
    def write_run_log(self, root: Path, name: str, events: list[dict]) -> Path:
        path = root / name
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        return path

    def run_learner(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LEARNER), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def event(self, event: str, issue: str, message: str) -> dict:
        return {
            "ts": "2026-09-13T12:00:00Z",
            "run": "run-01",
            "event": event,
            "issue": issue,
            "phase": "Critic",
            "data": {"message": message},
        }

    def test_recurring_refutation_across_issues_yields_exactly_one_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = self.write_run_log(
                root,
                "run-01.jsonl",
                [
                    self.event("refutation", "greeting#01", "criterion 3 has no test"),
                    self.event("review.finding", "greeting#02", "cli.py prints to stderr"),
                    self.event("refutation", "greeting#03", "criterion 3 has no test"),
                ],
            )

            result = self.run_learner(str(log), "--json")

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(1, len(payload["candidates"]))
            candidate = payload["candidates"][0]
            self.assertEqual("criterion 3 has no test", candidate["lesson"])
            self.assertEqual(2, len(candidate["evidence"]))
            self.assertTrue(any("greeting#01" in item for item in candidate["evidence"]))
            self.assertTrue(any("greeting#03" in item for item in candidate["evidence"]))
            self.assertTrue(candidate["target"])

    def test_result_validates_against_learner_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = self.write_run_log(
                root,
                "run-01.jsonl",
                [
                    self.event("refutation", "greeting#01", "criterion 3 has no test"),
                    self.event("refutation", "greeting#03", "criterion 3 has no test"),
                ],
            )
            extracted = self.run_learner(str(log), "--json")
            self.assertEqual(0, extracted.returncode, extracted.stderr)

            validated = subprocess.run(
                [sys.executable, str(RESULT), "--role", "learner", "--json"],
                input=extracted.stdout,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, validated.returncode, validated.stdout)
            self.assertTrue(json.loads(validated.stdout)["valid"])

    def test_reads_only_permitted_run_log_events_and_leaves_other_files_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = self.write_run_log(
                root,
                "run-01.jsonl",
                [
                    self.event("refutation", "greeting#01", "criterion 3 has no test"),
                    self.event("refutation", "greeting#03", "criterion 3 has no test"),
                    # Non-lesson events must never influence extraction.
                    {"ts": "2026-09-13T12:00:00Z", "run": "run-01", "event": "run.started",
                     "data": {"repositoryRoot": "/x", "policyHash": "h", "tier": "reference", "staleAfterSeconds": 900}},
                ],
            )
            agents_md = root / "AGENTS.md"
            context_md = root / "CONTEXT.md"
            template = root / "templates" / "issue.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            policy = root / ".gantry" / "config.json"
            policy.parent.mkdir(parents=True, exist_ok=True)
            agents_md.write_text("original agents\n", encoding="utf-8")
            context_md.write_text("original context\n", encoding="utf-8")
            template.write_text("original template\n", encoding="utf-8")
            policy.write_text('{"original": true}\n', encoding="utf-8")

            result = self.run_learner(str(log), "--json")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("original agents\n", agents_md.read_text(encoding="utf-8"))
            self.assertEqual("original context\n", context_md.read_text(encoding="utf-8"))
            self.assertEqual("original template\n", template.read_text(encoding="utf-8"))
            self.assertEqual('{"original": true}\n', policy.read_text(encoding="utf-8"))
            self.assertEqual(1, len(json.loads(result.stdout)["candidates"]))

    def test_single_occurrence_produces_no_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = self.write_run_log(
                root,
                "run-01.jsonl",
                [self.event("review.finding", "greeting#02", "cli.py prints to stderr")],
            )

            result = self.run_learner(str(log), "--json")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual([], json.loads(result.stdout)["candidates"])

    def test_help_json_contract_and_standard_library_imports(self) -> None:
        help_result = self.run_learner("--help")
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertIn("usage:", help_result.stdout.lower())

        allowed = {"__future__", "argparse", "json", "pathlib", "runlog", "sys"}
        source = LEARNER.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(LEARNER))
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
        self.assertLessEqual(imported, allowed)


if __name__ == "__main__":
    unittest.main()
