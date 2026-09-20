import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).parent.parent
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"
SCRIPTS_DIR = SKILL_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import plan
import spec
import runlog

class GantryPlanSocraticGateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        subprocess.run(["git", "init", "--quiet", str(self.repo_root)], check=True)
        # Setup basic repo files
        (self.repo_root / "CONTEXT.md").write_text("# Glossary\n\nRun: execution instance.\nIssue: unit of work.\n", encoding="utf-8")
        (self.repo_root / "PRD.md").write_text("# PRD\n\nAutomated delivery pipeline.\n", encoding="utf-8")
        adr_dir = self.repo_root / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "0001-record-architecture.md").write_text("# ADR-0001: Architecture\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_slug(self):
        self.assertEqual("webhook-support", plan.generate_slug("Add webhook support!"))
        self.assertEqual("export-csv-pipeline", plan.generate_slug("Export data to CSV in the pipeline"))
        self.assertTrue(re.match(r"^[a-z0-9][a-z0-9-]*$", plan.generate_slug("Interactive UI modal for 2026")))

    def test_explore_context(self):
        ctx = plan.explore_context(self.repo_root)
        self.assertTrue(ctx["has_context_doc"])
        self.assertTrue(ctx["has_prd"])
        self.assertIn("0001-record-architecture.md", ctx["adrs"])
        self.assertIn("Run", ctx["glossary"])

    def test_socratic_gate_interview_structure(self):
        engine = plan.SocraticGateEngine(goal="Add webhook notification delivery", repo_root=self.repo_root)
        slug = engine.slug
        self.assertEqual("webhook-notification-delivery", slug)

        phases = engine.get_interview_phases()
        phase_names = [p["name"] for p in phases]
        self.assertIn("Problem Statement & Context", phase_names)
        self.assertIn("Architectural Boundaries & Seams", phase_names)
        self.assertIn("Scope & Non-Goals", phase_names)
        self.assertIn("Verifiable Criteria & Scenarios", phase_names)

        for p in phases:
            self.assertGreater(len(p["questions"]), 0)
            for q in p["questions"]:
                self.assertIn("question", q)
                self.assertIn("recommended_answer", q)
                self.assertTrue(len(q["recommended_answer"]) > 0)

    def test_socratic_gate_runlog_telemetry(self):
        state_dir = self.repo_root / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        unit_id = "test-unit"
        run_id = "test-run"

        # Initialize run log
        runlog_path = state_dir / unit_id / "runs" / f"{run_id}.jsonl"
        runlog_path.parent.mkdir(parents=True, exist_ok=True)
        runlog_path.write_text(
            json.dumps({
                "ts": "2026-09-20T12:00:00Z",
                "run": run_id,
                "event": "run.started",
                "data": {
                    "repositoryRoot": str(self.repo_root),
                    "policyHash": "abc123",
                    "tier": "reference",
                    "staleAfterSeconds": 900
                }
            }) + "\n",
            encoding="utf-8"
        )

        engine = plan.SocraticGateEngine(
            goal="Add CSV report generation",
            repo_root=self.repo_root,
            unit_id=unit_id,
            run_id=run_id,
            state_root=state_dir
        )

        # Log pause awaiting operator
        engine.log_operator_pause("Socratic Interview")
        events = [json.loads(line) for line in runlog_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        pause_event = events[-1]
        self.assertEqual("phase.started", pause_event["event"])
        self.assertEqual(f"{engine.slug}#00", pause_event["issue"])
        self.assertEqual("Plan", pause_event["phase"])
        self.assertTrue(pause_event["data"]["operatorWaiting"])

        # Log operator answer/approval
        engine.log_operator_response()
        events = [json.loads(line) for line in runlog_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        approved_event = events[-1]
        self.assertEqual("operator.approved", approved_event["event"])
        self.assertEqual(f"{engine.slug}#00", approved_event["issue"])

    def test_spec_synthesizer_and_validation(self):
        engine = plan.SocraticGateEngine(goal="Real-time WebSocket streaming telemetry", repo_root=self.repo_root)
        spec_content = engine.synthesize_spec(
            context="Operators need real-time streaming of execution status without HTTP polling overhead.",
            architecture="Expose loopback WebSocket server endpoint on /ws and dispatch JSON event frames on runlog append.",
            constraints="Strict loopback binding (127.0.0.1 only), no external dependencies, drop connections on disconnect.",
            criteria=[
                "WebSocket endpoint responds on /ws",
                "Broadcasts runlog append events to connected clients",
                "Reconnection backoff logic handles disconnects"
            ],
            guardrails=[
                "Existing HTTP polling /api/state remains functional",
                "Loopback security constraints are preserved"
            ],
            scenarios=[
                {
                    "title": "Stream new event to WebSocket client",
                    "given": "a client connected to ws://127.0.0.1:4600/ws",
                    "when": "a runlog event is appended",
                    "then": "the event JSON frame is received by the client"
                }
            ],
            out_of_scope=[
                "Remote non-loopback connections",
                "Client-to-server bi-directional command dispatch"
            ]
        )

        spec_path = engine.write_spec(spec_content)
        self.assertTrue(spec_path.exists())

        # Validate with spec.py --check
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "spec.py"), "--check", str(spec_path), "--json"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        self.assertEqual(0, res.returncode, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        self.assertTrue(data.get("valid"), f"spec.py check failed: {res.stdout}")

class GantryPlanVerticalSlicingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        subprocess.run(["git", "init", "--quiet", str(self.repo_root)], check=True)

        # Create valid spec
        self.slug = "telemetry-stream"
        spec_dir = self.repo_root / ".scratch" / self.slug
        spec_dir.mkdir(parents=True, exist_ok=True)
        self.spec_path = spec_dir / "spec.md"
        self.spec_path.write_text("""# Spec: Telemetry Stream

Type: spec
Status: draft
Map: `ROADMAP.md` (spec 99)
Source: PRD.md §4
Created: 2026-09-20

## Blueprint

### Context

Provide live telemetry streaming for active runs.

### Architecture

Implement WebSocket server and message dispatching seam.

### Constraints

Loopback only.

## Contract

### Definition of Done

- [ ] Prefactor server socket handlers to support streaming
- [ ] Implement loopback streaming endpoint
- [ ] Add Playwright verification tests

### Regression Guardrails

- Existing endpoints remain unchanged

### Scenarios

```gherkin
Scenario: Connect to stream
  Given the server is running
  When a client connects to stream
  Then messages are received
```

## Out of Scope

- Remote streaming

## Changelog

- 2026-09-20 — Initial draft
""", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_slicing_validates_spec_before_decomposing(self):
        # Invalid spec should fail
        invalid_spec = self.repo_root / "invalid_spec.md"
        invalid_spec.write_text("# Invalid Spec\nNo sections.\n", encoding="utf-8")
        slicer = plan.SlicingEngine(invalid_spec, repo_root=self.repo_root)
        with self.assertRaises(ValueError):
            slicer.slice()

    def test_tracer_bullet_decomposition_with_prefactoring(self):
        slicer = plan.SlicingEngine(self.spec_path, repo_root=self.repo_root)
        issues = slicer.slice()

        self.assertGreaterEqual(len(issues), 2)
        # Slice 01 must be prefactoring
        slice_01 = issues[0]
        self.assertEqual(f"{self.slug}#01", slice_01["slice"])
        self.assertTrue(slice_01["is_prefactor"] or "prefactor" in slice_01["title"].lower())
        self.assertEqual([], slice_01["blocked_by"])

        # Slice 02 must depend on Slice 01
        slice_02 = issues[1]
        self.assertEqual(f"{self.slug}#02", slice_02["slice"])
        self.assertIn(f"{self.slug}#01", slice_02["blocked_by"])

        # Check issues written to disk
        written_files = slicer.write_issues(issues)
        for path in written_files:
            content = path.read_text(encoding="utf-8")
            self.assertIn("Type: issue", content)
            self.assertIn("Status: draft", content)
            self.assertIn("### Files to read", content)
            self.assertIn("## Acceptance criteria", content)
            self.assertIn("- [ ]", content)
            self.assertIn("## Blocked by", content)

    def test_context_budget_audit(self):
        slicer = plan.SlicingEngine(self.spec_path, repo_root=self.repo_root)
        issues = slicer.slice()
        budget_report = slicer.audit_budgets(issues)
        self.assertEqual(len(issues), len(budget_report))
        for item in budget_report:
            self.assertIn("slice", item)
            self.assertIn("tokens", item)
            self.assertIn("over_budget", item)
            self.assertFalse(item["over_budget"])

    def test_plan_critic_and_acyclicity(self):
        slicer = plan.SlicingEngine(self.spec_path, repo_root=self.repo_root)
        issues = slicer.slice()
        critic_result = slicer.audit_plan_critic(issues)
        self.assertTrue(critic_result["acceptable"])
        self.assertEqual([], critic_result["problems"])
        self.assertTrue(critic_result["is_dag"])

    def test_operator_quiz(self):
        slicer = plan.SlicingEngine(self.spec_path, repo_root=self.repo_root)
        issues = slicer.slice()
        quiz = slicer.generate_operator_quiz(issues)
        self.assertGreaterEqual(len(quiz), 3)
        topics = [q["topic"] for q in quiz]
        self.assertIn("granularity", topics)
        self.assertIn("dependency_order", topics)
        self.assertIn("split_merge", topics)

    def test_plan_cli_commands(self):
        # 1. Test --goal CLI
        res_goal = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "plan.py"), "--goal", "Add export report pipeline", "--json"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        self.assertEqual(0, res_goal.returncode, res_goal.stdout + res_goal.stderr)
        data_goal = json.loads(res_goal.stdout)
        self.assertIn("slug", data_goal)
        self.assertIn("phases", data_goal)

        # 2. Test --spec CLI
        res_spec = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "plan.py"), "--spec", str(self.spec_path), "--json"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        self.assertEqual(0, res_spec.returncode, res_spec.stdout + res_spec.stderr)
        data_spec = json.loads(res_spec.stdout)
        self.assertEqual(self.slug, data_spec["slug"])
        self.assertGreaterEqual(len(data_spec["issues"]), 2)
        self.assertTrue(data_spec["critic"]["acceptable"])

        # 3. Test --check-spec CLI
        res_check = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "plan.py"), "--check-spec", str(self.spec_path), "--json"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        self.assertEqual(0, res_check.returncode, res_check.stdout + res_check.stderr)
        data_check = json.loads(res_check.stdout)
        self.assertTrue(data_check.get("valid"))


class GantryPlanSkillAndDelegationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.temp_dir)
        subprocess.run(["git", "init", "--quiet", str(self.repo_root)], check=True)

        # Setup basic roadmap
        self.roadmap_path = self.repo_root / "ROADMAP.md"
        self.roadmap_path.write_text(
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
            encoding="utf-8"
        )

        # Setup valid spec
        self.slug = "sample-feature"
        spec_dir = self.repo_root / ".scratch" / self.slug
        spec_dir.mkdir(parents=True, exist_ok=True)
        self.spec_path = spec_dir / "spec.md"
        self.spec_path.write_text(f"""# Spec: Sample Feature

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 01)
Source: PRD.md §1
Created: 2026-09-20

## Blueprint

### Context

Sample feature context.

### Architecture

Sample architecture.

### Constraints

Zero external dependencies.

## Contract

### Definition of Done

- [ ] Prefactor architecture
- [ ] Implement core functionality

### Regression Guardrails

- Existing tests pass

### Scenarios

```gherkin
Scenario: Verify feature
  Given ready state
  When executed
  Then passes
```

## Out of Scope

- Remote integration

## Changelog

- 2026-09-20 — Initial
""", encoding="utf-8")

        # Slice issues in draft status
        slicer = plan.SlicingEngine(self.spec_path, repo_root=self.repo_root)
        self.issues = slicer.slice()
        self.written_files = slicer.write_issues(self.issues)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_gantry_plan_skill_registration_and_frontmatter(self):
        skill_file = REPO_ROOT / ".agents" / "skills" / "gantry-plan" / "SKILL.md"
        self.assertTrue(skill_file.exists(), "SKILL.md does not exist for gantry-plan")
        content = skill_file.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3)
        frontmatter = parts[1]
        self.assertIn("name: gantry-plan", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("argument-hint:", frontmatter)
        self.assertIn("<spec-slug | spec-path | \"free-text goal\">", frontmatter)

    def test_gantry_skill_delegation_instructions(self):
        gantry_skill = REPO_ROOT / ".agents" / "skills" / "gantry" / "SKILL.md"
        self.assertTrue(gantry_skill.exists())
        content = gantry_skill.read_text(encoding="utf-8")
        self.assertIn("gantry-plan", content)
        self.assertIn("free-text goal", content)
        self.assertIn("unplanned spec", content)

    def test_approve_plan_transitions_issues_and_updates_roadmap(self):
        # Verify initial status is draft
        for path in self.written_files:
            self.assertIn("Status: draft", path.read_text(encoding="utf-8"))

        res = plan.approve_plan(self.slug, repo_root=self.repo_root)
        self.assertTrue(res["valid"])
        self.assertEqual(len(self.issues), len(res["updated_issues"]))

        # Verify issues are now ready-for-agent
        for path in self.written_files:
            self.assertIn("Status: ready-for-agent", path.read_text(encoding="utf-8"))

        # Verify roadmap.py check passes with zero drift
        res_check = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "roadmap.py"), "check", "--json"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        self.assertEqual(0, res_check.returncode, res_check.stdout + res_check.stderr)
        data = json.loads(res_check.stdout)
        self.assertEqual([], data.get("drift", []))

    def test_approve_plan_with_telemetry_records_milestone_done(self):
        state_dir = self.repo_root / ".state"
        unit_id = "test-unit"
        run_id = "test-run"
        runlog_path = state_dir / unit_id / "runs" / f"{run_id}.jsonl"
        runlog_path.parent.mkdir(parents=True, exist_ok=True)
        runlog_path.write_text(
            json.dumps({
                "ts": "2026-09-20T12:00:00Z",
                "run": run_id,
                "event": "run.started",
                "data": {
                    "repositoryRoot": str(self.repo_root),
                    "policyHash": "abc123",
                    "tier": "reference",
                    "staleAfterSeconds": 900
                }
            }) + "\n",
            encoding="utf-8"
        )

        res = plan.approve_plan(
            self.slug,
            repo_root=self.repo_root,
            unit_id=unit_id,
            run_id=run_id,
            state_root=state_dir
        )
        self.assertTrue(res["valid"])

        events = [json.loads(line) for line in runlog_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        done_events = [e for e in events if e.get("event") == "issue.done" and e.get("issue") == f"{self.slug}#00"]
        self.assertEqual(1, len(done_events))
        self.assertEqual("Plan", done_events[0]["phase"])

    def test_approve_plan_cli_flag(self):
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "plan.py"), "--approve", self.slug, "--json"],
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
        self.assertEqual(0, res.returncode, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        self.assertTrue(data.get("valid"))
        self.assertEqual(self.slug, data.get("slug"))

    def test_standalone_vs_delegated_handoff_contract(self):
        skill_file = REPO_ROOT / ".agents" / "skills" / "gantry-plan" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("Execution Handoff", content)
        self.assertIn("Standalone Invocation", content)
        self.assertIn("Delegated Invocation", content)


if __name__ == "__main__":
    unittest.main()
