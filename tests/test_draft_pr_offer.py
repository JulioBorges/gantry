import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "gantry"

class DraftPullRequestOfferTests(unittest.TestCase):
    def run_workflow(self, args: dict, prompt_answers: list[str], mock_gh: bool = True) -> dict:
        source = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
        source = source.replace("export const meta", "const meta", 1)
        
        with tempfile.TemporaryDirectory() as tempdir:
            gh_path = Path(tempdir) / "gh"
            if mock_gh:
                gh_path.write_text("#!/bin/sh\necho gh stub called >&2\n", encoding="utf-8")
            else:
                gh_path.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
            gh_path.chmod(0o755)
            
            env = os.environ.copy()
            env["PATH"] = f"{tempdir}:{env.get('PATH', '')}"
            
            args["repoRoot"] = str(tempdir)

            driver = f"""
import {{ spawnSync }} from 'child_process';
const AsyncFunction = Object.getPrototypeOf(async function () {{}}).constructor;
const source = {json.dumps(source)};
const args = {json.dumps(args)};
const promptAnswers = {json.dumps(prompt_answers)};
const calls = [];
const commandCalls = [];
let promptIndex = 0;
const prompt = async (message) => {{
  calls.push({{ kind: 'prompt', message }});
  return promptAnswers[promptIndex++] || 'no';
}};
const agent = async (promptMsg, options) => {{
  calls.push({{ kind: 'agent', label: options.label }});
  if (options.label.startsWith('implement:')) return {{
    worktree: args.repoRoot, branch: args.branch, commits: ['test commit'],
    summary: 'stubbed rendered workflow', testsAdded: [], gatesResult: 'verdict: pass',
    decisions: [], blockers: [],
  }};
  if (options.label.startsWith('review:')) return {{ blocking: [], nonBlocking: [], summary: 'no findings' }};
  if (options.label.startsWith('critic:')) return {{
    complete: true, criteria: [
        {{ index: 1, met: true, evidence: 'ev1' }},
        {{ index: 2, met: true, evidence: 'ev2' }}
    ], gatesVerdict: 'pass', gateFailures: [],
    gateResult: {{ verdict: 'pass', requirements: [] }},
    refutations: [], requiredFixes: [], decisionsForOperator: [],
  }};
  if (options.label === 'learn') return {{ candidates: [] }};
  return null;
}};
const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd }});
  if (command.startsWith('git merge')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('python3') && command.includes('gates.py')) return {{ exitCode: 0, stdout: '{json.dumps({"verdict": "pass", "requirements": []})}' }};
  if (command.startsWith('python3') && command.includes('roadmap.py')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('python3') && command.includes('frontier.py')) return {{ exitCode: 0, stdout: '{{}}' }};
  if (command.startsWith('git add')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('git commit')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('python3') && command.includes('runlog.py')) return {{ exitCode: 0, stdout: 'dummy_unit' }};
  if (command.startsWith('python3') && command.includes('acceptance.py')) return {{ exitCode: 0, stdout: '{json.dumps({"criteria": [{"index": 1, "text": "crit1_text"}, {"index": 2, "text": "crit2_text"}]})}' }};
  if (command.startsWith('python3') && command.includes('common.py')) return {{ exitCode: 0, stdout: '{json.dumps({"issueBranch": "runs/test#01"})}' }};
  if (command.startsWith('python3') && command.includes('learner.py')) return {{ exitCode: 0, stdout: '{json.dumps({"candidates": []})}' }};
  
  if (command.startsWith('gh ')) {{
      const res = spawnSync(command, {{ shell: true, cwd: options.cwd, encoding: 'utf8' }});
      return {{ exitCode: res.status !== null ? res.status : 1, stdout: res.stdout || '', stderr: res.stderr || '' }};
  }}
  return {{ exitCode: 0, stdout: '' }};
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
const result = await new AsyncFunction('args', 'agent', 'runCommand', 'prompt', 'parallel', 'pipeline', 'phase', 'log', source)(
  args, agent, runCommand, prompt, parallel, pipeline, phase, log,
);
process.stdout.write(JSON.stringify({{ result, calls, commandCalls }}));
"""
            result = subprocess.run(
                ["node", "--input-type=module", "--eval", driver],
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if result.returncode != 0:
                print(result.stderr, file=sys.stderr)
            self.assertEqual(0, result.returncode, result.stderr)
            return json.loads(result.stdout)

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
