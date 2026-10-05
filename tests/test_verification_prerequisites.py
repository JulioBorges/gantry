"""Verification prerequisites readiness, pause, and resumption tests."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents/skills/gantry/scripts"))
import common
import execution
from tests import test_canonical_gantry_workflow as canonical


class VerificationPrerequisiteUnitTests(unittest.TestCase):
    def test_prerequisite_readiness_validates_declaration_and_probe(self):
        """Operator-approved declaration is probed; non-zero returns unavailable with remedy."""
        calls = []

        def runner(cmd, **kwargs):
            calls.append(cmd)
            if "docker" in cmd and "info" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "Docker version 27.0.0", "")
            return subprocess.CompletedProcess(cmd, 1, "", "daemon not running")

        policy = {
            "prerequisites": {
                "docker": {
                    "command": "docker info",
                    "remedy": "Start the Docker daemon and check user permissions.",
                },
                "remote-auth": {
                    "command": "check-auth",
                    "remedy": "Run remote login to obtain authorization token.",
                },
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Case 1: passing probe -> verified
            res_pass = execution.probe_prerequisite(
                "docker", policy["prerequisites"]["docker"], root, runner=runner
            )
            self.assertEqual("verified", res_pass["status"])
            self.assertEqual("docker", res_pass["name"])

            # Case 2: failing probe -> unavailable with remedy
            res_fail = execution.probe_prerequisite(
                "remote-auth", policy["prerequisites"]["remote-auth"], root, runner=runner
            )
            self.assertEqual("unavailable", res_fail["status"])
            self.assertEqual("Run remote login to obtain authorization token.", res_fail["remedy"])

            # Case 3: missing command -> unavailable
            res_malformed = execution.probe_prerequisite(
                "broken", {"remedy": "fix it"}, root, runner=runner
            )
            self.assertEqual("unavailable", res_malformed["status"])
            self.assertIn("command", res_malformed["error"])

    def test_inconclusive_evidence_returns_unavailable_with_remedy(self):
        """Inconclusive or exceptional probe output yields unavailable/unknown with remedy."""
        def error_runner(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 15)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            res = execution.probe_prerequisite(
                "flaky",
                {"command": "check-flaky", "remedy": "Check network connectivity."},
                root,
                runner=error_runner,
            )
            self.assertIn(res["status"], ("unavailable", "unknown"))
            self.assertEqual("Check network connectivity.", res["remedy"])

    def test_check_issue_prerequisites_resolves_from_issue_and_policy(self):
        """Prerequisites declared in issue text and policy are resolved and checked."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / ".scratch" / "sample" / "issues"
            spec_dir.mkdir(parents=True)
            issue_file = spec_dir / "01-sample.md"
            issue_file.write_text(
                "# Sample issue\n\nType: issue\nStatus: ready-for-agent\nSlice: `sample#01`\nPrerequisites: docker\n\n## Acceptance criteria\n\n- [ ] works\n",
                encoding="utf-8",
            )

            policy = {
                "prerequisites": {
                    "docker": {
                        "command": "docker info",
                        "remedy": "Start Docker.",
                    }
                }
            }

            def fail_runner(cmd, **kwargs):
                return subprocess.CompletedProcess(cmd, 1, "", "error")

            res = execution.check_issue_prerequisites(
                "sample#01", root, policy, runner=fail_runner
            )
            self.assertFalse(res["valid"])
            self.assertEqual("sample#01", res["issue"])
            self.assertIn("docker", res["prerequisites"])
            self.assertEqual("unavailable", res["prerequisites"]["docker"]["status"])
            self.assertEqual("Start Docker.", res["prerequisites"]["docker"]["remedy"])


class VerificationPrerequisiteWorkflowTests(unittest.TestCase):
    def fixture(self, root, prerequisites=None, issue_prerequisites=None):
        h = canonical.CanonicalGantryWorkflowTests()
        h.init_repo(root)
        for key, value in [("user.email", "gantry@example.test"), ("user.name", "Gantry Test")]:
            subprocess.run(["git", "config", key, value], cwd=root, check=True)
        subprocess.run(["git", "checkout", "-qb", "feat/run"], cwd=root, check=True)

        spec_dir = root / ".scratch" / "sample" / "issues"
        spec_dir.mkdir(parents=True)
        issue_file = spec_dir / "01-sample.md"
        prereq_line = f"Prerequisites: {issue_prerequisites}\n" if issue_prerequisites else ""
        issue_file.write_text(
            f"# Sample issue\n\nType: issue\nStatus: ready-for-agent\nSlice: `sample#01`\n{prereq_line}\n## Acceptance criteria\n\n- [ ] delivery file exists\n",
            encoding="utf-8",
        )

        # Issue 2: independent issue without prerequisites
        issue_file_two = spec_dir / "02-independent.md"
        issue_file_two.write_text(
            "# Independent issue\n\nType: issue\nStatus: ready-for-agent\nSlice: `sample#02`\n\n## Acceptance criteria\n\n- [ ] independent file exists\n",
            encoding="utf-8",
        )

        h.write_roadmap(root)
        (root / "Makefile").write_text("test:\n\t@true\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

        policy = {
            "git": {"target": "main", "prefix": "feat/"},
            "budget": {"corrections": 2},
            "prerequisites": prerequisites or {},
        }
        gantry_dir = root / ".gantry"
        gantry_dir.mkdir(parents=True, exist_ok=True)
        (gantry_dir / "config.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
        subprocess.run(["git", "add", ".gantry/config.json"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "policy"], cwd=root, check=True)
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

        args = dict(
            round=1,
            issues=[
                dict(ref="sample#01", path=str(issue_file.relative_to(root)), title="Sample"),
            ],
            models=dict(implement="implement", review="review", critic="critic"),
            branch="feat/run",
            baseRef=base,
            isolate=False,
            correctionBudget=2,
            skillDir=str(canonical.SKILL_DIR),
            repoRoot=str(root),
            policy=policy,
            paths={},
            commandMode="real",
            hostHarness="claude-code",
            runId="run-prereq-test",
            unitId="abcdef123456",
            stateRoot=str(root.parent / "state"),
            isLastRound=True,
            skipDashboardPrompt=True,
            implementerCommitText="delivered",
            criticResult={"criteria": h.critic_evidence(root, issue_file)},
        )
        return h, issue_file, issue_file_two, args

    def test_unavailable_prerequisite_pauses_before_implement_and_leaves_criteria_unticked(self):
        """A canonical Run with unavailable declared prerequisite pauses before role work is scheduled."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            prereqs = {
                "docker": {
                    "command": "false",  # fails
                    "remedy": "Start the Docker daemon and check user permissions.",
                }
            }
            h, issue1, issue2, args = self.fixture(root, prerequisites=prereqs, issue_prerequisites="docker")
            out = h.run_workflow("round-workflow.md", args)
            self.assertIsNone(out["error"])

            # Outcome for sample#01 is paused with verification_unavailable
            res = out["result"]["results"][0]
            self.assertEqual("paused", res["outcome"])
            self.assertEqual("verification_unavailable", res["reason"])
            self.assertEqual("Start the Docker daemon and check user permissions.", res["remedy"])

            # Authoritative issue completion criteria remain unticked
            parsed = common.parse_issue(issue1)
            self.assertEqual("ready-for-agent", parsed.status)
            self.assertFalse(all(c.checked for c in parsed.criteria))

            # Run log contains issue.paused with verification_unavailable
            events = h.read_run_log_events(Path(args["stateRoot"]), args["unitId"], args["runId"])
            paused_events = [e for e in events if e.get("event") == "issue.paused" and e.get("issue") == "sample#01"]
            self.assertEqual(1, len(paused_events))
            self.assertEqual("verification_unavailable", paused_events[0]["data"]["reason"])
            self.assertEqual("docker", paused_events[0]["data"]["prerequisite"])
            self.assertEqual("Start the Docker daemon and check user permissions.", paused_events[0]["data"]["remedy"])

            # No implement phase was started for sample#01
            implement_events = [e for e in events if e.get("event") == "phase.started" and e.get("phase") == "Implement" and e.get("issue") == "sample#01"]
            self.assertEqual(0, len(implement_events))

    def test_independent_eligible_work_continues_when_one_issue_pauses(self):
        """When an issue pauses on unavailable prerequisite, independent eligible issue completes."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            prereqs = {
                "docker": {
                    "command": "false",
                    "remedy": "Start Docker.",
                }
            }
            h, issue1, issue2, args = self.fixture(root, prerequisites=prereqs, issue_prerequisites="docker")
            # Include both issue 1 (prerequisite blocked) and issue 2 (independent)
            args["issues"] = [
                dict(ref="sample#01", path=str(issue1.relative_to(root)), title="Sample"),
                dict(ref="sample#02", path=str(issue2.relative_to(root)), title="Independent"),
            ]
            args["criticResults"] = [
                {"criteria": h.critic_evidence(root, issue2)},
            ]
            out = h.run_workflow("round-workflow.md", args)
            self.assertIsNone(out["error"])

            results = {r["ref"]: r for r in out["result"]["results"]}
            self.assertEqual("paused", results["sample#01"]["outcome"])
            self.assertEqual("verification_unavailable", results["sample#01"]["reason"])
            self.assertEqual("done", results["sample#02"]["outcome"])

            # Issue 2 is done, Issue 1 is ready-for-agent
            self.assertEqual("ready-for-agent", common.parse_issue(issue1).status)
            self.assertEqual("done", common.parse_issue(issue2).status)

    def test_verification_disappears_during_critic_pauses_without_refutation(self):
        """When verification capability fails during Critic, it pauses with verification_unavailable and NO refutation."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            prereqs = {
                "docker": {
                    "command": "true",  # Preflight passes
                    "remedy": "Restart Docker daemon.",
                }
            }
            h, issue1, issue2, args = self.fixture(root, prerequisites=prereqs, issue_prerequisites="docker")
            # Critic returns verification blocker
            args["criticResult"] = {
                "complete": False,
                "criteria": h.critic_evidence(root, issue1),
                "gatesVerdict": "fail",
                "gateResult": {
                    "verdict": "fail",
                    "verificationBlockers": [
                        {
                            "prerequisite": "docker",
                            "remedy": "Restart Docker daemon.",
                            "status": "unavailable",
                        }
                    ],
                },
                "gateFailures": ["Docker daemon stopped unexpectedly"],
                "refutations": [],  # No substantive code refutations!
                "requiredFixes": [],
                "decisionsForOperator": [],
            }
            out = h.run_workflow("round-workflow.md", args)
            self.assertIsNone(out["error"])

            res = out["result"]["results"][0]
            self.assertEqual("paused", res["outcome"])
            self.assertEqual("verification_unavailable", res["reason"])
            # Pure external pause: corrections spent is 0
            self.assertEqual(0, res["corrections"])

            # Verify NO refutation event was recorded
            events = h.read_run_log_events(Path(args["stateRoot"]), args["unitId"], args["runId"])
            refutations = [e for e in events if e.get("event") == "refutation" and e.get("issue") == "sample#01"]
            self.assertEqual(0, len(refutations))

            # issue.paused was recorded
            paused = [e for e in events if e.get("event") == "issue.paused" and e.get("issue") == "sample#01"]
            self.assertEqual(1, len(paused))
            self.assertEqual("verification_unavailable", paused[0]["data"]["reason"])

    def test_mixed_finding_retains_code_fixes_and_counts_correction_attempt(self):
        """Mixed code refutations and verification blocker: code fix is applied and counts 1 correction."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            prereqs = {
                "docker": {
                    "command": "true",
                    "remedy": "Restart Docker.",
                }
            }
            h, issue1, issue2, args = self.fixture(root, prerequisites=prereqs, issue_prerequisites="docker")
            args["implementerCommitTexts"] = ["initial\n", "corrected\n"]
            # First attempt: mixed finding (code defect + verification blocker)
            # Second attempt (after implementer fixes code): pure verification blocker -> pauses
            args["criticResults"] = [
                {
                    "complete": False,
                    "criteria": h.critic_evidence(root, issue1),
                    "gatesVerdict": "fail",
                    "gateResult": {
                        "verdict": "fail",
                        "verificationBlockers": [
                            {"prerequisite": "docker", "remedy": "Restart Docker.", "status": "unavailable"}
                        ],
                    },
                    "gateFailures": ["test failed", "docker stopped"],
                    "refutations": ["Fix error in main logic"],
                    "requiredFixes": ["Fix error in main logic"],
                    "decisionsForOperator": [],
                },
                {
                    "complete": False,
                    "criteria": h.critic_evidence(root, issue1),
                    "gatesVerdict": "fail",
                    "gateResult": {
                        "verdict": "fail",
                        "verificationBlockers": [
                            {"prerequisite": "docker", "remedy": "Restart Docker.", "status": "unavailable"}
                        ],
                    },
                    "gateFailures": ["docker stopped"],
                    "refutations": [],  # Code fix succeeded
                    "requiredFixes": [],
                    "decisionsForOperator": [],
                },
            ]
            out = h.run_workflow("round-workflow.md", args)
            self.assertIsNone(out["error"])

            res = out["result"]["results"][0]
            self.assertEqual("paused", res["outcome"])
            self.assertEqual("verification_unavailable", res["reason"])
            # Correction was counted once for the code fix attempt
            self.assertEqual(1, res["corrections"])

            # Refutation event was recorded for attempt 1
            events = h.read_run_log_events(Path(args["stateRoot"]), args["unitId"], args["runId"])
            refutations = [e for e in events if e.get("event") == "refutation" and e.get("issue") == "sample#01"]
            self.assertEqual(1, len(refutations))

    def test_resumption_with_unchanged_unavailable_evidence_stays_paused(self):
        """Resumption with unchanged unavailable prerequisite stays paused and blocks the round."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            prereqs = {
                "docker": {
                    "command": "false",  # Still failing
                    "remedy": "Start the Docker daemon.",
                }
            }
            h, issue1, issue2, args = self.fixture(root, prerequisites=prereqs, issue_prerequisites="docker")
            # Simulate prior paused state
            unit_id = args["unitId"]
            run_id = args["runId"]
            state_dir = Path(args["stateRoot"]) / unit_id / "runs"
            state_dir.mkdir(parents=True)
            log_path = state_dir / f"{run_id}.jsonl"
            log_path.write_text(
                json.dumps({"ts": "2026-10-04T00:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root), "policyHash": "123456", "tier": "reference", "staleAfterSeconds": 900, "host": {"effectiveHost": "claude-code"}}}) + "\n"
                + json.dumps({"ts": "2026-10-04T00:00:01Z", "run": run_id, "event": "round.started", "data": {"round": 1}}) + "\n"
                + json.dumps({"ts": "2026-10-04T00:00:02Z", "run": run_id, "issue": "sample#01", "phase": "Critic", "event": "issue.paused", "data": {"role": "critic", "reason": "verification_unavailable", "prerequisite": "docker", "remedy": "Start the Docker daemon."}}) + "\n"
                + json.dumps({"ts": "2026-10-04T00:00:03Z", "run": run_id, "event": "round.finished", "data": {"round": 1}}) + "\n",
                encoding="utf-8",
            )
            args["round"] = 2
            args["isFirstRound"] = False
            args["priorRun"] = {"run": run_id, "issue": "sample#01", "correctionsSpent": 0, "worktree": str(root), "branch": "feat/run"}

            out = h.run_workflow("round-workflow.md", args)
            self.assertIsNone(out["error"])
            self.assertTrue(out["result"].get("blocked") or out["result"].get("nextRoundBlocked"))
            self.assertEqual("unresolved_verification_failure", out["result"]["reason"])
            self.assertEqual("ready-for-agent", common.parse_issue(issue1).status)

    def test_resumption_with_restored_capability_verifies_and_completes(self):
        """Restoring capability allows resumption to run Critic and complete the Issue."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            prereqs = {
                "docker": {
                    "command": "true",  # Capability restored!
                    "remedy": "Start Docker.",
                }
            }
            h, issue1, issue2, args = self.fixture(root, prerequisites=prereqs, issue_prerequisites="docker")
            unit_id = args["unitId"]
            run_id = args["runId"]
            state_dir = Path(args["stateRoot"]) / unit_id / "runs"
            state_dir.mkdir(parents=True)
            log_path = state_dir / f"{run_id}.jsonl"
            log_path.write_text(
                json.dumps({"ts": "2026-10-04T00:00:00Z", "run": run_id, "event": "run.started", "data": {"repositoryRoot": str(root), "policyHash": "123456", "tier": "reference", "staleAfterSeconds": 900, "host": {"effectiveHost": "claude-code"}}}) + "\n"
                + json.dumps({"ts": "2026-10-04T00:00:01Z", "run": run_id, "event": "round.started", "data": {"round": 1}}) + "\n"
                + json.dumps({"ts": "2026-10-04T00:00:02Z", "run": run_id, "issue": "sample#01", "phase": "Critic", "event": "issue.paused", "data": {"role": "critic", "reason": "verification_unavailable", "prerequisite": "docker", "remedy": "Start Docker."}}) + "\n"
                + json.dumps({"ts": "2026-10-04T00:00:03Z", "run": run_id, "event": "round.finished", "data": {"round": 1}}) + "\n",
                encoding="utf-8",
            )
            args["round"] = 2
            args["isFirstRound"] = False
            args["priorRun"] = {"run": run_id, "issue": "sample#01", "correctionsSpent": 0, "worktree": str(root), "branch": "feat/run"}
            args["criticResult"] = {"criteria": h.critic_evidence(root, issue1)}

            out = h.run_workflow("round-workflow.md", args)
            self.assertIsNone(out["error"])
            self.assertEqual("done", out["result"]["results"][0]["outcome"])
            self.assertEqual("done", common.parse_issue(issue1).status)


if __name__ == "__main__":
    unittest.main()
