import tempfile
import unittest
from pathlib import Path

from tests import test_canonical_gantry_workflow as canonical

REPO_ROOT = Path(__file__).parent.parent
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"


class RoundWorkflowLifecycleHooksTests(unittest.TestCase):
    def setUp(self):
        self.args = {
            "round": 1,
            "issues": [
                {
                    "ref": "test#01",
                    "title": "Test Issue",
                    "path": ".scratch/test/issues/01-test.md",
                    "criteria": [{"index": 1, "text": "crit1"}],
                    "blocked_by": []
                }
            ],
            "models": {"implement": "mock-impl", "review": "mock-rev", "critic": "mock-crit"},
            "branch": "runs/test",
            "baseRef": "main",
            "isolate": False,
            "correctionBudget": 2,
            "skillDir": str(SKILL_DIR),
            "repoRoot": "/dummy",
            "policy": {"git": {"target": "main", "prefix": "runs/"}},
            "paths": {},
            "date": "2026-09-20",
        }

    def run_workflow(self, args: dict, prompt_answers: list[str], dash_running: bool = False, dash_post_running: bool = False) -> dict:
        with tempfile.TemporaryDirectory() as tempdir:
            workflow_args = {
                **args,
                "repoRoot": str(tempdir),
                "promptAnswers": prompt_answers,
                "technicalPlanFixture": True,
                "stubDashboard": True,
                "dashboardFirstRunning": dash_running,
                "dashboardLaterRunning": dash_post_running,
                "recordPromptCalls": True,
                "passIntegrationGate": True,
                "criticResult": {
                    "complete": True,
                    "criteria": [{"index": 1, "met": True, "evidence": "ev1"}],
                    "gatesVerdict": "pass",
                    "gateResult": {"verdict": "pass", "requirements": []},
                },
            }
            return canonical.CanonicalGantryWorkflowTests().run_workflow("round-workflow.md", workflow_args)

    def test_pre_implementation_hook_prompts_and_starts_when_approved(self):
        out = self.run_workflow(self.args, prompt_answers=["yes", "no"], dash_running=False, dash_post_running=False)
        self.assertIsNone(out.get("error"))

        # Check prompt was presented
        prompts = [c["message"] for c in out["calls"] if c.get("kind") == "prompt"]
        self.assertTrue(any("start it in the background" in p for p in prompts))

        # Check dashboard.py start --daemon was executed
        start_cmds = [c["command"] for c in out["commandCalls"] if "dashboard.py\" start --daemon" in c["command"]]
        self.assertEqual(1, len(start_cmds))

    def test_pre_implementation_hook_declined(self):
        out = self.run_workflow(self.args, prompt_answers=["no", "no"], dash_running=False, dash_post_running=False)
        self.assertIsNone(out.get("error"))

        prompts = [c["message"] for c in out["calls"] if c.get("kind") == "prompt"]
        self.assertTrue(any("start it in the background" in p for p in prompts))

        # Start should not have been called
        start_cmds = [c["command"] for c in out["commandCalls"] if "dashboard.py\" start --daemon" in c["command"]]
        self.assertEqual(0, len(start_cmds))

    def test_pre_implementation_hook_already_active_does_not_prompt(self):
        out = self.run_workflow(self.args, prompt_answers=["no"], dash_running=True, dash_post_running=False)
        self.assertIsNone(out.get("error"))

        prompts = [c["message"] for c in out["calls"] if c.get("kind") == "prompt"]
        self.assertFalse(any("start it in the background" in p for p in prompts))

        start_cmds = [c["command"] for c in out["commandCalls"] if "dashboard.py\" start --daemon" in c["command"]]
        self.assertEqual(0, len(start_cmds))

    def test_post_integration_hook_prompts_and_stops_when_approved(self):
        out = self.run_workflow(self.args, prompt_answers=["yes"], dash_running=True, dash_post_running=True)
        self.assertIsNone(out.get("error"))

        prompts = [c["message"] for c in out["calls"] if c.get("kind") == "prompt"]
        self.assertTrue(any("shut down the background dashboard server" in p for p in prompts))

        stop_cmds = [c["command"] for c in out["commandCalls"] if "dashboard.py\" stop" in c["command"]]
        self.assertEqual(1, len(stop_cmds))

    def test_documentation_reflects_lifecycle_and_daemon_subcommands(self):
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        dash_skill_text = (SKILL_DIR.parent / "gantry-dashboard" / "SKILL.md").read_text(encoding="utf-8")
        round_wf_text = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8")

        for subcmd in ("start --daemon", "status", "stop"):
            self.assertIn(subcmd, skill_text)
            self.assertIn(subcmd, dash_skill_text)
            self.assertIn(subcmd, round_wf_text)

if __name__ == "__main__":
    unittest.main()
