#!/usr/bin/env python3
"""Public-contract tests for the canonical Gantry workflow skill."""
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

    def write_issue(self, root: Path, ref: str, status: str, blockers: list[str] | None = None) -> Path:
        slug, number = ref.split("#")
        path = root / ".scratch" / slug / "issues" / f"{int(number):02d}-example.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        blocked_by = "\n".join(f"- `{blocker}` — prerequisite" for blocker in blockers or []) or "- None"
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

- [ ] exposes a deterministic behaviour

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

    def run_workflow(self, filename: str, args: dict) -> dict:
        source = (SKILL_DIR / "reference" / filename).read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
        source = source.replace("export const meta", "const meta", 1)
        driver = f"""
import {{ mkdirSync, writeFileSync }} from 'node:fs';
import {{ dirname }} from 'node:path';
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {json.dumps(args)};
const calls = [];
const agent = async (prompt, options) => {{
  calls.push({{ label: options.label, prompt }});
  if (options.label.startsWith('research:')) return 'factual research';
  if (options.label === 'plan') {{
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
  if (options.label.startsWith('critique')) return {{
    acceptable: true, problems: [], frontierErrors: [],
  }};
  if (options.label.startsWith('implement:')) return {{
    worktree: args.repoRoot, branch: args.branch, commits: ['test commit'],
    summary: 'workflow execution', testsAdded: [], gatesResult: 'verdict: pass',
    decisions: [], blockers: [],
  }};
  if (options.label.startsWith('review:')) return {{
    blocking: [], nonBlocking: [], summary: 'no findings',
  }};
  if (options.label.startsWith('critic:')) return {{
    complete: true, criteria: [], gatesVerdict: 'pass', gateFailures: [],
    refutations: [], requiredFixes: [], decisionsForOperator: [],
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
const result = await new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', source)(
  args, agent, parallel, pipeline, phase, log,
);
process.stdout.write(JSON.stringify({{ result, calls }}));
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

            for script in ("common.py", "frontier.py", "acceptance.py", "gates.py", "roadmap.py"):
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
            approved = self.run_script(root, "roadmap.py", "status", "planned#01", "ready-for-agent")
            self.assertEqual(0, approved.returncode, approved.stderr)
            self.assertEqual(before, roadmap.read_bytes())

            projected = self.run_script(root, "roadmap.py", "waves")
            self.assertEqual(0, projected.returncode, projected.stderr)
            checked = self.run_script(root, "roadmap.py", "check", "--json")
            self.assertEqual(0, checked.returncode, checked.stderr)
            self.assertEqual([], json.loads(checked.stdout)["drift"])
            self.assertIn("planned#01", roadmap.read_text(encoding="utf-8"))

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
        ):
            self.assertIn(phrase, round_workflow)
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
        }
        self.assertEqual(
            {"acceptance.py", "common.py", "frontier.py", "gates.py", "roadmap.py"},
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
