#!/usr/bin/env python3
"""Smoke coverage for the portable legacy planning and round paths."""
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

from common import parse_issue, resolve_policy, resolve_workflow_paths  # noqa: E402


class LegacyWorkflowSmokeTests(unittest.TestCase):
    def test_no_policy_repository_stops_at_planning_approval_and_no_ready_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            subprocess.run(["git", "init", "--quiet", str(root)], check=True)
            spec_path = root / ".scratch" / "portable" / "spec.md"
            spec_path.parent.mkdir(parents=True)
            spec_path.write_text("# Portable spec\n", encoding="utf-8")

            policy = resolve_policy(root)
            paths = resolve_workflow_paths(root, "portable")
            self.assertEqual(root / ".scratch" / "portable" / "issues", paths["issueDir"])
            self.assertEqual(root / "CONTEXT.md", paths["context"])
            self.assertEqual(root / "docs" / "adr", paths["adrs"])
            self.assertEqual(root / "docs" / "agents" / "issue-tracker.md", paths["issueTracker"])
            self.assertFalse((root / ".gantry" / "config.json").exists())

            plan_args = {
                "target": {"kind": "spec", "slug": "portable", "specPath": str(paths["specPath"])},
                "models": {"plan": "test-plan", "critic": "test-critic"},
                "skillDir": str(SKILL_DIR),
                "repoRoot": str(root),
                "policy": policy,
                "paths": {name: str(path) for name, path in paths.items()},
                "date": "2026-09-13",
            }
            plan_result = self.run_workflow(
                "plan-workflow.md",
                plan_args,
                research_format=self.frontier_json(root, "portable", include_parked=False),
            )
            self.assertTrue(plan_result["result"]["critique"]["acceptable"])
            self.assertEqual([], plan_result["result"]["plan"]["issues"])
            plan_prompt = self.prompt_for(plan_result["calls"], "plan")
            self.assertIn(str(paths["issueDir"]), plan_prompt)
            self.assertIn(str(paths["issueTracker"]), plan_prompt)
            self.assertIn('"selected":[]', plan_prompt)
            self.assertFalse(paths["issueDir"].exists(), "the planning workflow must stop for approval")

            issue_path = root / ".scratch" / "portable" / "issues" / "01-portable-loop.md"
            blocker_path = root / ".scratch" / "portable" / "issues" / "00-parser-prerequisite.md"
            issue_path.parent.mkdir(parents=True)
            blocker_path.write_text(
                """# Parser prerequisite

Type: issue
Status: done
Slice: `portable#00`

## Acceptance criteria

- [x] provide a completed blocker

## Blocked by

- None
""",
                encoding="utf-8",
            )
            issue_path.write_text(
                """# Portable loop

Type: issue
Status: draft
Slice: `portable#01`

## Acceptance criteria

- [ ] preserve the first parser criterion
- [x] preserve the second parser criterion

## Blocked by

- `portable#00` — prerequisite parsed from Markdown
""",
                encoding="utf-8",
            )

            issue = parse_issue(issue_path)
            self.assertEqual("portable#01", issue.ref)
            self.assertEqual("draft", issue.status)
            self.assertEqual(
                ["preserve the first parser criterion", "preserve the second parser criterion"],
                [item.text for item in issue.criteria],
            )
            self.assertEqual(["portable#00"], issue.blocked_by)

            parsed_issue = self.acceptance_json(root, issue_path)
            self.assertEqual(".scratch/portable/issues/01-portable-loop.md", parsed_issue["path"])
            self.assertTrue(parsed_issue["path"].endswith(issue_path.name))
            self.assertEqual("draft", parsed_issue["status"])
            self.assertEqual("portable#01", parsed_issue["ref"])
            self.assertEqual(
                ["preserve the first parser criterion", "preserve the second parser criterion"],
                [item["text"] for item in parsed_issue["criteria"]],
            )
            self.assertEqual(["portable#00"], parsed_issue["blocked_by"])

            frontier = self.frontier_json(root, "portable", include_parked=True)
            self.assertEqual(["portable#01"], frontier["selected"])
            self.assertEqual("draft", frontier["issues"]["portable#01"]["status"])
            self.assertEqual(2, frontier["issues"]["portable#01"]["criteria_total"])
            self.assertEqual(["portable#00"], frontier["issues"]["portable#01"]["blocked_by"])

            plan_with_parser = self.run_workflow(
                "plan-workflow.md",
                plan_args,
                research_format={"frontier": frontier, "issues": [parsed_issue]},
            )
            parser_prompt = self.prompt_for(plan_with_parser["calls"], "plan")
            for field in ("path", "status", "ref", "criteria", "blocked_by"):
                self.assertIn(
                    json.dumps(parsed_issue[field], separators=(",", ":")),
                    parser_prompt,
                    f"planning must receive parser {field}",
                )

            round_args = {
                "round": 1,
                "models": {"implement": "test-implement", "review": "test-review", "critic": "test-critic"},
                "branch": "gantry/portable",
                "baseRef": "HEAD",
                "isolate": False,
                "correctionBudget": 2,
                "skillDir": str(SKILL_DIR),
                "repoRoot": str(root),
                "policy": policy,
                "paths": {name: str(path) for name, path in paths.items()},
                "date": "2026-09-13",
            }
            no_ready_frontier = self.frontier_json(root, "portable", include_parked=False)
            self.assertEqual({"portable#01": "draft"}, no_ready_frontier["parked"])
            round_args["issues"] = self.round_issues(no_ready_frontier, [parsed_issue])
            self.assertEqual([], round_args["issues"])
            round_result = self.run_workflow("round-workflow.md", round_args)
            self.assertEqual([], round_result["result"]["results"])
            self.assertEqual([], round_result["calls"])

            # Reuse the parser output selected by the public frontier rather
            # than constructing a round issue by hand.
            round_args["issues"] = self.round_issues(frontier, [parsed_issue])
            rendered_round = self.run_workflow("round-workflow.md", round_args)
            implement_prompt = self.prompt_for(rendered_round["calls"], "implement:portable#01")
            self.assertIn(str(paths["context"]), implement_prompt)
            self.assertIn(str(paths["adrs"]), implement_prompt)
            self.assertIn(parsed_issue["ref"], implement_prompt)
            self.assertIn(parsed_issue["path"], implement_prompt)
            critic_prompt = self.prompt_for(rendered_round["calls"], "critic:portable#01#1")
            self.assertIn(
                f"acceptance.py {root}/{parsed_issue['path']} --json",
                critic_prompt,
            )

    def test_workflows_render_configured_paths_from_args(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            subprocess.run(["git", "init", "--quiet", str(root)], check=True)
            config_path = root / ".gantry" / "config.json"
            config_path.parent.mkdir()
            config_path.write_text(
                json.dumps({
                    "artifacts": {
                        "specs": "product/{slug}.md",
                        "issues": "work/{slug}",
                        "decisions": "decisions",
                        "adrs": "architecture",
                        "context": "domain.md",
                        "issueTracker": "guides/issues.md",
                    },
                    "git": {"prefix": "runs/"},
                }),
                encoding="utf-8",
            )
            paths = resolve_workflow_paths(root, "portable")
            policy = resolve_policy(root)
            plan_args = {
                "target": {"kind": "spec", "slug": "portable", "specPath": str(paths["specPath"])},
                "models": {"plan": "test-plan", "critic": "test-critic"},
                "skillDir": str(SKILL_DIR),
                "repoRoot": str(root),
                "policy": policy,
                "paths": {name: str(path) for name, path in paths.items()},
                "date": "2026-09-13",
            }
            plan_result = self.run_workflow("plan-workflow.md", plan_args, research_format={"selected": []})
            codebase_prompt = self.prompt_for(plan_result["calls"], "research:codebase")
            plan_prompt = self.prompt_for(plan_result["calls"], "plan")
            self.assertIn(str(paths["context"]), codebase_prompt)
            self.assertIn(str(paths["adrs"]), codebase_prompt)
            self.assertIn(str(paths["issueTracker"]), plan_prompt)
            self.assertIn("runs/", plan_prompt)

            round_args = {
                "round": 1,
                "issues": [{
                    "ref": "portable#01",
                    "path": "work/portable/01-portable.md",
                    "title": "Portable loop",
                    "specPath": "product/portable.md",
                }],
                "models": {"implement": "test-implement", "review": "test-review", "critic": "test-critic"},
                "branch": "runs/portable",
                "baseRef": "HEAD",
                "isolate": False,
                "correctionBudget": 2,
                "skillDir": str(SKILL_DIR),
                "repoRoot": str(root),
                "policy": policy,
                "paths": {name: str(path) for name, path in paths.items()},
                "date": "2026-09-13",
            }
            round_result = self.run_workflow("round-workflow.md", round_args)
            implement_prompt = self.prompt_for(round_result["calls"], "implement:portable#01")
            self.assertIn(str(paths["context"]), implement_prompt)
            self.assertIn(str(paths["adrs"]), implement_prompt)
            self.assertIn("runs/", implement_prompt)

    def frontier_json(self, root: Path, scope: str, *, include_parked: bool) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "frontier.py"),
                "--scope",
                scope,
                "--json",
                *(["--include-parked"] if include_parked else []),
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 2:
            return json.loads(result.stdout) if result.stdout else {"selected": [], "rounds": []}
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def acceptance_json(self, root: Path, issue_path: Path) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "acceptance.py"), str(issue_path), "--json"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def round_issues(self, frontier: dict, parsed_issues: list[dict]) -> list[dict]:
        parsed_by_ref = {issue["ref"]: issue for issue in parsed_issues}
        selected = [ref for round_refs in frontier["rounds"] for ref in round_refs]
        return [
            {
                "ref": parsed_by_ref[ref]["ref"],
                "path": parsed_by_ref[ref]["path"],
                "title": parsed_by_ref[ref]["title"],
                "specPath": parsed_by_ref[ref]["spec_path"],
            }
            for ref in selected
            if ref in parsed_by_ref
        ]

    def run_workflow(self, filename: str, args: dict, research_format: dict | None = None) -> dict:
        source = (SKILL_DIR / "reference" / filename).read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
        source = source.replace("export const meta", "const meta", 1)
        driver = f"""
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {json.dumps(args)};
const researchFormat = {json.dumps(research_format)};
const calls = [];
const commandCalls = [];
const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd || args.repoRoot }});
  if (command.includes('/spec.py')) return {{ exitCode: 0, stdout: '{{"valid":true}}', stderr: '' }};
  if (command.includes('/result.py')) return {{ exitCode: 0, stdout: '{{"valid":true}}', stderr: '' }};
  if (command.includes('/common.py')) return {{ exitCode: 0, stdout: JSON.stringify({{ issueBranch: args.issueBranch || args.branch }}) }};
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
  return {{ exitCode: 0, stdout: '' }};
}};
const prompt = async () => 'no';
const agent = async (promptText, options) => {{
  calls.push({{ prompt: promptText, label: options.label }});
  if (options.label.startsWith('requirement-critic')) return {{ blocking: [], findings: [] }};
  if (options.label === 'plan') return {{ filesWritten: [], issues: [], roadmapAdditions: [], openDecisions: [] }};
  if (options.label.startsWith('critique')) return {{ acceptable: true, problems: [], frontierErrors: [] }};
  if (options.label === 'research:format') return JSON.stringify(researchFormat);
  if (options.label.startsWith('research:')) return 'research brief';
  if (options.label.startsWith('implement:')) return {{
    worktree: args.repoRoot, branch: args.branch, commits: ['test commit'],
    summary: 'stubbed rendered workflow', testsAdded: [], gatesResult: 'verdict: pass',
    decisions: [], blockers: [],
  }};
  if (options.label.startsWith('review:')) return {{ blocking: [], nonBlocking: [], summary: 'no findings' }};
  if (options.label.startsWith('critic:')) return {{
    complete: true,
    criteria: [{{ index: 1, text: 'criterion', met: true, evidence: 'ok' }}],
    gatesVerdict: 'pass', gateResult: {{ verdict: 'pass' }}, gateFailures: [],
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
let result = null;
let error = null;
try {{
  result = await new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'runCommand', 'prompt', source)(
    args, agent, parallel, pipeline, phase, log, runCommand, prompt,
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
        data = json.loads(result.stdout)
        if data.get("error"):
            self.fail(f"workflow threw error: {data['error']}")
        return data

    def prompt_for(self, calls: list[dict], label: str) -> str:
        for call in calls:
            if call["label"] == label:
                return call["prompt"]
        self.fail(f"workflow did not invoke {label}")

    def test_asdlc_retired_and_harness_skills_resolve_canonical_pack(self) -> None:
        self.assertFalse((REPO_ROOT / ".agents" / "skills" / "asdlc").exists())
        skills = [
            REPO_ROOT / ".agents" / "skills" / "gantry",
            REPO_ROOT / ".agents" / "skills" / "gantry-setup",
            REPO_ROOT / ".agents" / "skills" / "gantry-dashboard",
        ]
        for skill in skills:
            self.assertTrue(skill.is_dir())
            skill_md = skill / "SKILL.md"
            self.assertTrue(skill_md.is_file())
            text = skill_md.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            frontmatter = text.split("---", 2)[1]
            self.assertIn(f"name: {skill.name}", frontmatter)
            self.assertIn("description:", frontmatter)

        for harness in (".claude", ".cursor", ".opencode", ".gemini"):
            harness_skills = REPO_ROOT / harness / "skills"
            self.assertTrue(harness_skills.exists(), f"missing {harness}/skills")
            names = sorted([item.name for item in harness_skills.iterdir() if not item.name.startswith(".")])
            self.assertEqual(["gantry", "gantry-dashboard", "gantry-setup"], names)
            for name in names:
                target = harness_skills / name
                self.assertTrue(target.is_dir())
                self.assertTrue((target / "SKILL.md").is_file())

    def test_workflow_templates_receive_paths_in_args_without_repository_literals(self) -> None:
        prohibited = ("gantry-v4", "slice-index", "the Gantry repository")
        for skill_dir in sorted(REPO_ROOT.glob(".agents/skills/gantry*")):
            for path in sorted(skill_dir.rglob("*")):
                if path.is_file() and not path.name.endswith((".pyc", ".pyo", ".pyd")):
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    self.assertFalse(
                        any(literal in text for literal in prohibited),
                        f"{path.relative_to(REPO_ROOT)} contains a prohibited literal",
                    )

    def test_no_policy_smoke_runs_canonical_workflow_on_this_repository(self) -> None:
        self.assertFalse((REPO_ROOT / ".gantry" / "config.json").exists())

        policy = resolve_policy(REPO_ROOT)
        self.assertEqual(".scratch/{slug}/spec.md", policy["artifacts"]["specs"])
        self.assertEqual(".scratch/{slug}/issues", policy["artifacts"]["issues"])
        self.assertEqual("docs/adr", policy["artifacts"]["adrs"])
        self.assertEqual("docs/adr", policy["artifacts"]["decisions"])
        self.assertEqual("CONTEXT.md", policy["artifacts"]["context"])
        self.assertEqual("docs/agents/issue-tracker.md", policy["artifacts"]["issueTracker"])
        self.assertEqual("main", policy["git"]["target"])
        self.assertEqual("gantry/", policy["git"]["prefix"])

        paths = resolve_workflow_paths(REPO_ROOT, "gantry-migration")
        self.assertEqual(REPO_ROOT / ".scratch" / "gantry-migration" / "issues", paths["issueDir"])
        self.assertEqual(REPO_ROOT / "CONTEXT.md", paths["context"])
        self.assertEqual(REPO_ROOT / "docs" / "adr", paths["adrs"])
        self.assertEqual(REPO_ROOT / "docs" / "agents" / "issue-tracker.md", paths["issueTracker"])

        frontier = self.frontier_json(REPO_ROOT, "gantry-migration", include_parked=False)
        issue_path = REPO_ROOT / ".scratch" / "gantry-migration" / "issues" / "18-retire-asdlc-and-switch-harness-links.md"
        parsed_issue = self.acceptance_json(REPO_ROOT, issue_path)
        self.assertEqual("gantry-migration#18", parsed_issue["ref"])
        if parsed_issue["status"] == "ready-for-agent":
            self.assertIn("gantry-migration#18", frontier["selected"])
        else:
            self.assertEqual("done", parsed_issue["status"])

        round_args = {
            "round": 6,
            "models": {"implement": "test-implement", "review": "test-review", "critic": "test-critic"},
            "branch": "gantry/wave-6",
            "baseRef": "51b4d6d",
            "isolate": False,
            "correctionBudget": 2,
            "skillDir": str(SKILL_DIR),
            "repoRoot": str(REPO_ROOT),
            "policy": policy,
            "paths": {name: str(path) for name, path in paths.items()},
            "date": "2026-09-14",
            "issues": [parsed_issue],
        }
        round_result = self.run_workflow("round-workflow.md", round_args)
        self.assertEqual(1, len(round_result["result"]["results"]))
        self.assertEqual("gantry-migration#18", round_result["result"]["results"][0]["ref"])
        self.assertEqual("done", round_result["result"]["results"][0]["outcome"])

        implement_prompt = self.prompt_for(round_result["calls"], "implement:gantry-migration#18")
        self.assertIn(str(paths["context"]), implement_prompt)
        self.assertIn(str(paths["adrs"]), implement_prompt)
        self.assertIn("gantry-migration#18", implement_prompt)

        critic_prompt = self.prompt_for(round_result["calls"], "critic:gantry-migration#18#1")
        self.assertIn(f"acceptance.py {REPO_ROOT}/{parsed_issue['path']} --json", critic_prompt)

    def test_scripts_import_only_standard_library_or_pack_modules(self) -> None:
        allowed = {
            "__future__",
            "acceptance",
            "argparse",
            "common",
            "copy",
            "dataclasses",
            "datetime",
            "difflib",
            "execution",
            "hashlib",
            "http",
            "json",
            "os",
            "pathlib",
            "re",
            "result",
            "runlog",
            "shlex",
            "shutil",
            "skipscan",
            "socket",
            "spec",
            "subprocess",
            "sys",
            "tempfile",
            "threading",
            "time",
            "typing",
            "urllib",
        }
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
