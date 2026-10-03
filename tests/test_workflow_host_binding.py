"""Host binding at the approved canonical workflow and public CLI seams."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
                "plan": {"harness": "codex", "model": "native-custom", "effort": "medium"},
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

    def test_native_research_preserves_resolved_inheritance_and_override(self):
        from tests.test_role_execution_dispatch import execution
        with tempfile.TemporaryDirectory() as tmp:
            for issue_override in ({}, {"research": {"harness": "codex", "model": "issue-research", "effort": "high"}}):
                with self.subTest(issue_override=issue_override):
                    roles = execution.resolve_roles(
                        policy={"execution": {"roles": {"plan": {"harness": "codex", "model": "policy-plan", "effort": "low"}}}},
                        run_overrides={"plan": {"harness": "codex", "model": "run-plan", "effort": "medium"}},
                        issue_overrides=issue_override,
                    )
                    args = self.entry_args(Path(tmp), "codex")
                    roles.update({role: {"harness": "codex", "model": "local-critic"} for role in ("requirement-critic", "plan-critic")})
                    args.update(roles=roles, commandMode="real", structuredOutput=True,
                                caveman={"active": True, "skill_path": "caveman"})
                    run = self.run_workflow("plan-workflow.md", args)
                    self.assertIsNone(run["error"])
                    research = [call for call in run["calls"] if call["label"].startswith("research:")]
                    self.assertEqual(3, len(research))
                    for call in research:
                        self.assertEqual("issue-research" if issue_override else "run-plan", call["model"])
                        self.assertEqual("high" if issue_override else "medium", call["effort"])
                        self.assertEqual(roles["research"], call["selection"])
                        self.assertNotIn("schema", call)
                        self.assertIn("Caveman lite is active", call["prompt"])
                    self.assertFalse(any('result.py" --role "research"' in call["command"] for call in run["commandCalls"]))

    def test_external_research_preserves_selection_and_text_without_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.entry_args(Path(tmp), "codex")
            args.update(commandMode="real", structuredOutput=True,
                        roles={"research": {"harness": "claude-code", "model": "research-selected", "effort": "high"}},
                        caveman={"active": True},
                        dispatchResults=[{"exitCode": 0, "stdout": json.dumps(text), "stderr": ""}
                                         for text in ("codebase facts", "spec facts", "format facts")])
            run = self.run_workflow("plan-workflow.md", args)
            self.assertIsNone(run["error"])
            dispatches = [call for call in run["commandCalls"] if 'execution.py" dispatch' in call["command"]]
            self.assertEqual(3, len(dispatches))
            for call in dispatches:
                self.assertIn('--role "research"', call["command"])
                self.assertIn('"model":"research-selected"', call["command"])
                self.assertIn('"effort":"high"', call["command"])
            self.assertFalse(any(call["label"].startswith("research:") for call in run["calls"]))
            self.assertFalse(any('result.py" --role "research"' in call["command"] for call in run["commandCalls"]))
            planner = next(call for call in run["calls"] if call["label"] == "plan")
            for text in ("codebase facts", "spec facts", "format facts"):
                self.assertIn(text, planner["prompt"])
            args["dispatchResults"] = [{"exitCode": 1, "stdout": "", "stderr": "execution failed"}] * 3
            failed = self.run_workflow("plan-workflow.md", args)
            self.assertIn("Research", failed["error"] or "")
            self.assertFalse(any(call["label"] == "plan" or call["label"].startswith("research:") for call in failed["calls"]))

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

    def test_round_bounded_same_host_dispatch_preserves_issue_override(self):
        self.check_bounded_same_host_dispatch()

    def test_recorded_same_host_nonzero_exit_omits_sensitive_process_streams(self):
        self.check_bounded_same_host_dispatch(sensitive_output=True)

    def test_recorded_malformed_version_probe_omits_sensitive_output(self):
        self.check_bounded_same_host_dispatch(failure_mode='malformed-version')

    def test_recorded_exceptional_version_probe_omits_exception_text(self):
        self.check_bounded_same_host_dispatch(failure_mode='exceptional-version')

    def test_recorded_model_fallback_omits_envelope_metadata(self):
        self.check_bounded_same_host_dispatch(failure_mode='fallback')

    def check_bounded_same_host_dispatch(self, sensitive_output=False, failure_mode=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = canonical.CanonicalGantryWorkflowTests()
            helper.init_repo(root)
            issue = helper.write_issue(root, "adapter#01", "ready-for-agent")
            args = self.entry_args(root, "codex")
            args.update(commandMode="real", isolate=False, boundedRoleExecution=True,
                        issues=[{"ref": "adapter#01", "path": str(issue), "specPath": "spec.md"}],
                        roles={"implement": {"harness": "codex", "model": "run-model", "effort": "low"}},
                        issueRoles={"adapter#01": {"implementer": {"harness": "codex", "model": "issue-model", "effort": "medium"}}},
                        executionTimeout=15, runId="run-bounded-fixture", unitId="abcdef123456", stateRoot=str(root / "state"))
            before = issue.read_bytes()
            binary_dir = root / 'bin'
            binary_dir.mkdir()
            received = root / 'received-selection.json'
            binary = binary_dir / 'codex'
            stdout = 'raw stdout API_TOKEN=synthetic-fixture-secret'
            stderr = 'raw stderr Authorization: Bearer synthetic-fixture-secret'
            version = stdout if failure_mode == 'malformed-version' else 'codex 0.160.0'
            if failure_mode == 'fallback':
                body = "print(" + repr(json.dumps({'type': 'turn.started', 'model': stdout})) + ")\n"
            elif sensitive_output:
                body = f"print({stdout!r})\nprint({stderr!r}, file=sys.stderr)\nsys.exit(13)\n"
            else:
                body = "print('simulated unavailable model', file=sys.stderr)\nsys.exit(13)\n"
            binary.write_text(f"#!{sys.executable}\n" +
                "import json, sys\nfrom pathlib import Path\n" +
                f"if '--version' in sys.argv: print({version!r}); sys.exit(0)\n" +
                f"Path({str(received)!r}).write_text(json.dumps(sys.argv[1:]))\n" +
                body)
            binary.chmod(0o755)
            environment = {'PATH': str(binary_dir) + os.pathsep + os.environ['PATH']}
            if failure_mode == 'exceptional-version':
                # Inject at the same subprocess boundary used by the canonical CLI.
                (binary_dir / 'sitecustomize.py').write_text(
                    "import subprocess\n_original_run = subprocess.run\n"
                    "def probe_failure(cmd, *args, **kwargs):\n"
                    "    if isinstance(cmd, list) and cmd[:2] == ['codex', '--version']:\n"
                    f"        raise OSError({stderr!r})\n"
                    "    return _original_run(cmd, *args, **kwargs)\n"
                    "subprocess.run = probe_failure\n")
                environment['PYTHONPATH'] = str(binary_dir)
            with patch.dict(os.environ, environment):
                run = self.run_workflow("round-workflow.md", args)
            self.assertIsNone(run["error"])
            self.assertEqual("codex", run["result"]["hostResolution"]["effectiveHost"])
            dispatch = next(call["command"] for call in run["commandCalls"] if 'execution.py" dispatch' in call["command"])
            self.assertIn('"model":"issue-model"', dispatch)
            self.assertIn('"effort":"medium"', dispatch)
            self.assertIn('"harness":"codex"', dispatch)
            self.assertFalse(any(call["label"].startswith("implement:") for call in run["calls"]))
            self.assertEqual("paused", run["result"]["results"][0]["outcome"])
            self.assertEqual(before, issue.read_bytes())
            probe_failed = failure_mode in ('malformed-version', 'exceptional-version')
            if probe_failed:
                self.assertFalse(received.exists())
            else:
                invoked = json.loads(received.read_text())
                self.assertEqual('issue-model', invoked[invoked.index('--model') + 1])
                self.assertIn('model_reasoning_effort="medium"', invoked)
                self.assertIn('--json', invoked)
                self.assertNotIn('--effort', invoked)
            log = root / 'state/abcdef123456/runs/run-bounded-fixture.jsonl'
            events = [json.loads(line) for line in log.read_text().splitlines()]
            names = [event['event'] for event in events]
            self.assertEqual(1, names.count('subagent.started'))
            self.assertEqual(1, names.count('subagent.stopped'))
            self.assertEqual(0 if probe_failed else 1, names.count('role.invocation.started'))
            self.assertEqual(0 if probe_failed else 1, names.count('role.invocation.finished'))
            if not probe_failed:
                invocation = next(event for event in events if event['event']=='role.invocation.finished')
                self.assertEqual('adapter#01', invocation['issue'])
                self.assertEqual('execution-failure' if failure_mode == 'fallback' else 'nonzero-exit', invocation['data']['status'])
            if sensitive_output or failure_mode:
                recorded = log.read_text()
                for forbidden in (stdout, stderr, 'synthetic-fixture-secret', 'API_TOKEN', 'Authorization'):
                    self.assertNotIn(forbidden, recorded)
                paused = next(event for event in events if event['event'] == 'issue.paused')
                self.assertIn({'malformed-version': 'version-parse-failure', 'exceptional-version': 'version-probe-failure', 'fallback': 'model-fallback'}.get(failure_mode, 'exit 13'), paused['data']['error'])
                self.assertLess(len(paused['data']['error']), 200)

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
