"""Host binding at the approved canonical workflow and public CLI seams."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import test_canonical_gantry_workflow as canonical

SKILL_DIR = canonical.SKILL_DIR


class WorkflowHostBindingTests(unittest.TestCase):
    run_workflow = canonical.CanonicalGantryWorkflowTests.run_workflow

    def entry_args(self, root, host):
        return dict(skillDir=str(SKILL_DIR), repoRoot=str(root), hostHarness=host,
                    policy={"budget": {"corrections": 0}, "git": {"target": "main"}}, paths={}, models={"plan": "custom", "critic": "custom"},
                    target={"kind": "goal", "goal": "example", "slug": "example"},
                    round=1, issues=[], branch="feat/example", baseRef="HEAD", isolate=True)

    def test_both_entries_stop_before_commands_or_agents_when_host_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            for filename in ("plan-workflow.md", "round-workflow.md"):
                for host in (None, "unsupported"):
                    with self.subTest(filename=filename, host=host):
                        run = self.run_workflow(filename, self.entry_args(Path(tmp), host))
                        self.assertIn("Host Harness", run["error"] or "")
                        self.assertEqual([], run["calls"])
                        self.assertEqual([], run["commandCalls"])
                        self.assertEqual(1, len(run["hostCalls"]))

    def test_selected_host_capabilities_win_over_stale_policy_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = root / ".gantry/config.json"
            policy.parent.mkdir()
            policy.write_text('{"execution":{"hostHarness":"antigravity","roles":{"critic":{"harness":"claude-code","model":"custom","effort":"high"}}},"custom":{"keep":true}}')
            before = policy.read_bytes()
            for filename in ("plan-workflow.md", "round-workflow.md"):
                run = self.run_workflow(filename, self.entry_args(root, "claude-code"))
                self.assertIsNone(run["error"])
                host = run["result"]["hostResolution"]
                self.assertEqual("claude-code", host["effectiveHost"])
                self.assertEqual("antigravity", host["savedPreference"])
                self.assertTrue(host["mismatch"])
                self.assertTrue(host["capabilities"]["hooks"])
                self.assertEqual(before, policy.read_bytes())
                self.assertEqual(1, len(run["hostCalls"]))

    def test_codex_host_routes_external_critic_and_native_selected_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gantry").mkdir()
            (root / ".gantry/config.json").write_text('{"execution":{"hostHarness":"antigravity"}}')
            args = self.entry_args(root, "codex")
            args.update(commandMode="real", roles={
                "planner": {"harness": "codex", "model": "native-custom", "effort": "medium"},
                "plan-critic": {"harness": "claude-code", "model": "external-custom", "effort": "high"}},
                dispatchResults=[{"exitCode": 0, "stdout": '{"acceptable":true,"problems":[],"frontierErrors":[]}', "stderr": ""}])
            run = self.run_workflow("plan-workflow.md", args)
            self.assertIsNone(run["error"])
            self.assertTrue(run["result"]["awaitingOperatorApproval"])
            native = next(call for call in run["calls"] if call["label"] == "plan")
            self.assertEqual("native-custom", native["model"])
            self.assertEqual("medium", native["effort"])
            self.assertFalse(any(call["label"] == "critique" for call in run["calls"]))
            dispatch = next(call["command"] for call in run["commandCalls"] if 'execution.py" dispatch' in call["command"])
            self.assertIn('"model":"external-custom"', dispatch)
            self.assertIn('"effort":"high"', dispatch)
            args["dispatchResults"] = [{"exitCode": 0, "stdout": '{}', "stderr": ""}]
            run = self.run_workflow("plan-workflow.md", args)
            self.assertEqual("plan-critic", run["result"]["protocolFailure"]["role"])

    def test_round_external_critic_contract_and_issue_override_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = canonical.CanonicalGantryWorkflowTests()
            helper.init_repo(root)
            issue = helper.write_issue(root, "binding#01", "ready-for-agent")
            args = self.entry_args(root, "codex")
            args.update(commandMode="real", isolate=False,
                        issues=[{"ref": "binding#01", "path": str(issue), "specPath": "spec.md"}],
                        models={"implement": "legacy", "review": "legacy", "critic": "legacy"},
                        roles={"implement": {"harness": "codex", "model": "run-model", "effort": "low"}},
                        issueRoles={"binding#01": {
                            "implementer": {"harness": "codex", "model": "issue-model", "effort": "medium"},
                            "critic": {"harness": "claude-code", "model": "external-custom", "effort": "high"}}},
                        dispatchResults=[{"exitCode": 0, "stdout": '{}', "stderr": ""}])
            before = issue.read_bytes()
            run = self.run_workflow("round-workflow.md", args)
            self.assertIsNone(run["error"])
            self.assertEqual("critic_failed", run["result"]["results"][0]["outcome"])
            implementer = next(call for call in run["calls"] if call["label"].startswith("implement:"))
            self.assertEqual("issue-model", implementer["model"])
            self.assertEqual("medium", implementer["effort"])
            self.assertEqual(before, issue.read_bytes())
            self.assertFalse(any(call["label"].startswith("critic:") for call in run["calls"]))
            self.assertTrue(any('result.py" --role "critic" --json' in call["command"] for call in run["commandCalls"]))

    def test_concurrent_new_runs_record_their_own_sanitized_host_and_capability_tier(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            def invoke(index, host):
                root = Path(tmp) / str(index)
                root.mkdir()
                canonical.CanonicalGantryWorkflowTests().init_repo(root)
                args = self.entry_args(root, host)
                args.update(commandMode="real", unitId="abcdef123456", runId=f"run-{index}", stateRoot=str(state), tier="false-tier")
                run = self.run_workflow("round-workflow.md", args)
                self.assertIsNone(run["error"])
                events = [json.loads(line) for line in (state / "abcdef123456/runs" / f"run-{index}.jsonl").read_text().splitlines()]
                return events[0]["data"]
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(invoke, 1, "codex")
                second = executor.submit(invoke, 2, "claude-code")
                codex, claude = first.result(), second.result()
            self.assertEqual("codex", codex["host"]["effectiveHost"])
            self.assertEqual("claude-code", claude["host"]["effectiveHost"])
            self.assertEqual("supported", codex["tier"])
            self.assertNotEqual("false-tier", claude["tier"])
            for record in (codex, claude):
                self.assertEqual([{"source": "invocation:explicit-selection", "kind": "explicit", "host": record["host"]["effectiveHost"]}], record["host"]["sources"])
