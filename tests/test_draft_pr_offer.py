import tempfile
import unittest
from pathlib import Path

from tests import test_canonical_gantry_workflow as canonical

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"


class DraftPullRequestOfferTests(unittest.TestCase):
    def run_workflow(self, args: dict, prompt_answers: list[str], mock_gh: bool = True) -> dict:
        with tempfile.TemporaryDirectory() as tempdir:
            workflow_args = {
                **args,
                "repoRoot": str(tempdir),
                "promptAnswers": prompt_answers,
                "technicalPlanFixture": True,
                "passIntegrationGate": True,
                "acceptanceResult": {
                    "criteria": [
                        {"index": 1, "text": "crit1_text"},
                        {"index": 2, "text": "crit2_text"},
                    ],
                },
                "criticResult": {
                    "complete": True,
                    "criteria": [
                        {"index": 1, "met": True, "evidence": "ev1"},
                        {"index": 2, "met": True, "evidence": "ev2"},
                    ],
                    "gatesVerdict": "pass",
                    "gateResult": {"verdict": "pass", "requirements": []},
                },
            }
            if not mock_gh:
                workflow_args["ghVersionExitCode"] = 127
            return canonical.CanonicalGantryWorkflowTests().run_workflow("round-workflow.md", workflow_args)

    def setUp(self):
        self.args = {
            "round": 1,
            "isLastRound": True,
            "issues": [{
                "ref": "test#01",
                "path": "work/test#01.md",
                "title": "Test Issue",
                "specPath": "product/test.md",
            }],
            "models": {"implement": "test", "review": "test", "critic": "test"},
            "branch": "runs/test",
            "baseRef": "main",
            "isolate": False,
            "correctionBudget": 2,
            "skillDir": str(SKILL_DIR),
            "repoRoot": "/dummy",  # Replaced dynamically
            "policy": {"git": {"target": "main", "prefix": "runs/"}},
            "paths": {},
            "date": "2026-09-14",
        }

    def test_gh_available_and_operator_confirms(self):
        res = self.run_workflow(self.args, ["yes"], mock_gh=True)
        # Verify roadmap check and frontier check were run
        roadmap_calls = [c["command"] for c in res["commandCalls"] if "roadmap.py\" check" in c["command"]]
        self.assertGreaterEqual(len(roadmap_calls), 1)
        frontier_calls = [c["command"] for c in res["commandCalls"] if "frontier.py\" --scope all" in c["command"]]
        self.assertGreaterEqual(len(frontier_calls), 1)

        # Expecting exactly one gh pr create command
        gh_calls = [c["command"] for c in res["commandCalls"] if "gh pr create" in c["command"]]
        self.assertEqual(1, len(gh_calls))
        cmd = gh_calls[0]
        self.assertIn("--draft", cmd)
        self.assertIn("--base 'main'", cmd)
        self.assertIn("--head 'runs/test'", cmd)
        
        # Verify criteria text and evidence are correctly joined
        self.assertIn("- [x] crit1_text: ev1", cmd)
        self.assertIn("- [x] crit2_text: ev2", cmd)
        
        pr_offer = res["result"].get("prOffer")
        self.assertEqual("opened", pr_offer["status"])

    def test_gh_unavailable(self):
        res = self.run_workflow(self.args, ["yes"], mock_gh=False)
        gh_calls = [c["command"] for c in res["commandCalls"] if "gh pr create" in c["command"]]
        self.assertEqual(0, len(gh_calls))
        
        pr_offer = res["result"].get("prOffer")
        self.assertEqual("unavailable", pr_offer["status"])

    def test_gh_available_operator_refuses(self):
        res = self.run_workflow(self.args, ["no"], mock_gh=True)
        gh_calls = [c["command"] for c in res["commandCalls"] if "gh pr create" in c["command"]]
        self.assertEqual(0, len(gh_calls))
        
        pr_offer = res["result"].get("prOffer")
        self.assertEqual("declined", pr_offer["status"])

if __name__ == "__main__":
    unittest.main()
