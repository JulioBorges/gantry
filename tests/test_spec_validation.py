#!/usr/bin/env python3
"""Public-contract tests for effective-template Spec validation."""
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
SPEC = SCRIPTS / "spec.py"
sys.path.insert(0, str(SCRIPTS))

from common import resolve_effective_template  # noqa: E402


class SpecValidationTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)

    def run_spec(self, root: Path, spec: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SPEC), "--check", str(spec), "--json", *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def valid_spec(self, contract_heading: str = "Contract") -> str:
        return f"""# Spec: validated

## Blueprint

The current state is observable.

## {contract_heading}

### Scenarios

```gherkin
Scenario: Validate the effective template
  Given a repository with a Spec
  When the workflow script checks it
  Then the structural result passes
```

## Out of Scope

- No semantic review.

## Changelog

- 2026-09-13 — Added structural validation coverage.
"""

    def test_effective_template_and_heading_map_drive_missing_section_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            config = root / ".gantry" / "config.json"
            config.parent.mkdir()
            config.write_text(
                json.dumps({"templates": {"headingMap": {"## Delivery contract": "## Contract"}}}),
                encoding="utf-8",
            )
            spec = root / "spec.md"
            spec.write_text(self.valid_spec("Delivery contract").replace("\n## Changelog\n", "\n"), encoding="utf-8")

            result = self.run_spec(root, spec)

            self.assertEqual(1, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(["## Changelog"], payload["missing"])
            self.assertEqual(
                {"expected": "## Contract", "actual": "## Delivery contract"},
                payload["present"][1],
            )

    def test_repository_template_replaces_pack_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            template = root / "templates" / "spec.md"
            template.parent.mkdir()
            template.write_text(
                """# Spec: <feature>

## Purpose

<why>

## Contract

```gherkin
Scenario: <behaviour>
  Given <context>
  When <action>
  Then <outcome>
```

## Changelog

- YYYY-MM-DD — Initial draft.
""",
                encoding="utf-8",
            )
            config = root / ".gantry" / "config.json"
            config.parent.mkdir()
            config.write_text(json.dumps({"templates": {"dir": "templates"}}), encoding="utf-8")
            self.assertEqual(template.resolve(), resolve_effective_template(root, "spec"))
            spec = root / "spec.md"
            spec.write_text(
                self.valid_spec()
                .replace("## Blueprint", "## Purpose")
                .replace("## Out of Scope\n\n- No semantic review.\n\n", ""),
                encoding="utf-8",
            )

            result = self.run_spec(root, spec)

            self.assertEqual(0, result.returncode, result.stderr)

    def test_reports_every_structural_failure_and_finishes_200kb_spec_under_one_second(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            broken = root / "broken.md"
            broken.write_text(
                """# Spec: <feature>

## Contract

```gherkin
Scenario: incomplete scenario
  Given a repository
  When validation runs
```

## Blueprint

<Problem, users and current state.>

## Out of Scope

- None
""",
                encoding="utf-8",
            )

            failed = self.run_spec(root, broken)

            self.assertEqual(1, failed.returncode, failed.stderr)
            failures = json.loads(failed.stdout)
            self.assertEqual(["## Changelog"], failures["missing"])
            self.assertTrue(failures["out_of_order"])
            self.assertTrue(failures["placeholders"])
            self.assertTrue(failures["malformed_scenarios"])

            large = root / "large.md"
            large.write_text(self.valid_spec().replace("The current state is observable.", "x" * 200_000), encoding="utf-8")
            started = time.monotonic()
            passed = self.run_spec(root, large)
            elapsed = time.monotonic() - started

            self.assertEqual(0, passed.returncode, passed.stderr)
            self.assertLess(elapsed, 1)

    def test_rejects_gherkin_steps_that_regress_or_precede_their_phase(self) -> None:
        cases = {
            "given after when": (
                self.valid_spec().replace(
                    "  When the workflow script checks it",
                    "  When the workflow script checks it\n  Given a regression in setup",
                ),
                "Given cannot follow When",
                15,
            ),
            "then before when": (
                self.valid_spec().replace(
                    "  When the workflow script checks it\n  Then the structural result passes",
                    "  Then the structural result passes\n  When the workflow script checks it",
                ),
                "Then must follow When",
                14,
            ),
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            for name, (contents, reason, line) in cases.items():
                with self.subTest(name=name):
                    spec = root / f"{name}.md"
                    spec.write_text(contents, encoding="utf-8")

                    result = self.run_spec(root, spec)

                    self.assertEqual(1, result.returncode, result.stderr)
                    finding = json.loads(result.stdout)["malformed_scenarios"][0]
                    self.assertEqual(line, finding["line"])
                    self.assertIn(reason, finding["reason"])

    def test_accepts_complete_gherkin_sequences(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            spec = root / "spec.md"
            spec.write_text(
                self.valid_spec().replace(
                    "  Given a repository with a Spec\n"
                    "  When the workflow script checks it\n"
                    "  Then the structural result passes",
                    "  Given a repository with a Spec\n"
                    "  And a configured effective template\n"
                    "  But no malformed placeholders\n"
                    "  When the workflow script checks it\n"
                    "  And it reads the configured template\n"
                    "  But it does not alter the Spec\n"
                    "  Then the structural result passes\n"
                    "  And it reports no findings",
                ),
                encoding="utf-8",
            )

            result = self.run_spec(root, spec)

            self.assertEqual(0, result.returncode, result.stderr)

    def test_ignores_headings_inside_fenced_code_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            spec = root / "spec.md"
            spec.write_text(
                self.valid_spec().replace(
                    "\n## Changelog\n\n- 2026-09-13 — Added structural validation coverage.\n",
                    "\n```markdown\n## Changelog\n```\n",
                ),
                encoding="utf-8",
            )

            result = self.run_spec(root, spec)

            self.assertEqual(1, result.returncode, result.stderr)
            self.assertEqual(["## Changelog"], json.loads(result.stdout)["missing"])

    def test_ignores_scenarios_in_normal_fences_but_validates_gherkin_fences(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)

            example = root / "example.md"
            example.write_text(
                self.valid_spec().replace(
                    "\n## Out of Scope\n",
                    """\n```text
Scenario: Incomplete illustrative example
  Given an example block
  When a reader copies it
```

## Out of Scope
""",
                ),
                encoding="utf-8",
            )
            ignored = self.run_spec(root, example)

            self.assertEqual(0, ignored.returncode, ignored.stderr)
            self.assertEqual([], json.loads(ignored.stdout)["malformed_scenarios"])

            malformed = root / "malformed-gherkin.md"
            malformed.write_text(
                self.valid_spec().replace("  Then the structural result passes\n", ""),
                encoding="utf-8",
            )
            checked = self.run_spec(root, malformed)

            self.assertEqual(1, checked.returncode, checked.stderr)
            self.assertTrue(json.loads(checked.stdout)["malformed_scenarios"])

    def test_checking_a_directory_returns_json_error_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)

            result = self.run_spec(root, root)

            self.assertEqual(2, result.returncode, result.stderr)
            self.assertEqual("", result.stderr)
            self.assertIn("error", json.loads(result.stdout))

    def test_help_json_contract_and_standard_library_imports(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(SPEC), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertIn("usage:", help_result.stdout.lower())

        allowed = {"__future__", "argparse", "common", "json", "pathlib", "re", "sys"}
        source = SPEC.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SPEC))
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

    def test_plan_workflow_stops_before_planner_writes_invalid_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            invalid = root / ".scratch" / "invalid" / "spec.md"
            invalid.parent.mkdir(parents=True)
            invalid.write_text("# Spec: invalid\n\n## Blueprint\n", encoding="utf-8")
            draft = root / ".scratch" / "invalid" / "issues" / "01-draft.md"
            source = (SKILL_DIR / "reference" / "plan-workflow.md").read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
            source = source.replace("export const meta", "const meta", 1)
            driver = f"""
import {{ mkdirSync, writeFileSync }} from 'node:fs';
import {{ dirname }} from 'node:path';
import {{ spawnSync }} from 'node:child_process';
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {{
  target: {{ kind: 'spec', slug: 'invalid', specPath: {json.dumps(str(invalid))} }},
  models: {{ plan: 'plan', critic: 'critic' }}, skillDir: {json.dumps(str(SKILL_DIR))},
  repoRoot: {json.dumps(str(root))}, policy: {{ git: {{ target: 'main', prefix: 'gantry/' }} }},
  paths: {{ issueDir: {json.dumps(str(draft.parent))}, specPath: {json.dumps(str(invalid))},
    exemplarIssue: 'issue.md', decisions: 'docs/adr', issueTracker: 'tracker.md', context: 'CONTEXT.md', adrs: 'docs/adr' }},
}};
const calls = [];
const commands = [];
const runCommand = async (command, options = {{}}) => {{
  commands.push(command);
  const result = spawnSync(command, {{ cwd: options.cwd || args.repoRoot, shell: true, encoding: 'utf8' }});
  return {{ exitCode: result.status ?? 1, stdout: result.stdout || '', stderr: result.stderr || '' }};
}};
const agent = async (prompt, options) => {{
  calls.push(options.label);
  if (options.label === 'plan') {{
    mkdirSync(dirname({json.dumps(str(draft))}), {{ recursive: true }});
    writeFileSync({json.dumps(str(draft))}, 'must not exist');
  }}
  return {{ filesWritten: [], issues: [], roadmapAdditions: [], openDecisions: [] }};
}};
const parallel = async (tasks) => Promise.all(tasks.map((task) => task()));
const phase = () => {{}};
const log = () => {{}};
const result = await new AsyncFunction('args', 'agent', 'parallel', 'phase', 'log', 'runCommand', source)(
  args, agent, parallel, phase, log, runCommand,
);
process.stdout.write(JSON.stringify({{ result, calls, commands }}));
"""
            result = subprocess.run(["node", "--input-type=module", "--eval", driver], text=True, capture_output=True, check=False)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(draft.exists())
            self.assertEqual([], payload["calls"])
            self.assertIn("spec.py", payload["commands"][0])
            self.assertIn("## Contract", payload["result"]["report"])


if __name__ == "__main__":
    unittest.main()
