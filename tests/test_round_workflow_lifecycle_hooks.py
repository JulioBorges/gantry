import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

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
        source = (SKILL_DIR / "reference" / "round-workflow.md").read_text(encoding="utf-8").split("```js\n", 1)[1].split("\n```", 1)[0]
        source = source.replace("export const meta", "const meta", 1)

        with tempfile.TemporaryDirectory() as tempdir:
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
    worktree: args.repoRoot, branch: args.branch, commits: ['commit 1'],
    summary: 'impl summary', testsAdded: [], gatesResult: 'verdict: pass',
    decisions: [], blockers: []
  }};
  if (options.label.startsWith('review:')) return {{ blocking: [], nonBlocking: [], summary: 'no findings' }};
  if (options.label.startsWith('critic:')) return {{
    complete: true, criteria: [
        {{ index: 1, met: true, evidence: 'ev1' }}
    ], gatesVerdict: 'pass', gateFailures: [],
    gateResult: {{ verdict: 'pass', requirements: [] }},
    refutations: [], requiredFixes: [], decisionsForOperator: [],
  }};
  if (options.label === 'learn') return {{ candidates: [] }};
  return null;
}};

let dashCheckCount = 0;
const runCommand = async (command, options = {{}}) => {{
  commandCalls.push({{ command, cwd: options.cwd }});
  if (command.includes('dashboard.py" status --json')) {{
    dashCheckCount++;
    const isRunning = dashCheckCount === 1 ? {json.dumps(dash_running)} : {json.dumps(dash_post_running)};
    return {{
      exitCode: 0,
      stdout: JSON.stringify({{
        running: isRunning,
        host: '127.0.0.1',
        port: 4600,
        pid: isRunning ? 1234 : null,
        url: isRunning ? 'http://127.0.0.1:4600' : null
      }})
    }};
  }}
  if (command.includes('dashboard.py" start --daemon')) {{
    return {{ exitCode: 0, stdout: 'Dashboard started on http://127.0.0.1:4600' }};
  }}
  if (command.includes('dashboard.py" stop')) {{
    return {{ exitCode: 0, stdout: 'Dashboard stopped.' }};
  }}
  if (command.startsWith('git merge')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('python3') && command.includes('gates.py')) return {{ exitCode: 0, stdout: '{json.dumps({"verdict": "pass", "requirements": []})}' }};
  if (command.startsWith('python3') && command.includes('roadmap.py')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('python3') && command.includes('frontier.py')) return {{ exitCode: 0, stdout: '{{}}' }};
  if (command.startsWith('git add')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('git commit')) return {{ exitCode: 0, stdout: '' }};
  if (command.startsWith('python3') && command.includes('runlog.py')) return {{ exitCode: 0, stdout: 'dummy_unit' }};
  if (command.startsWith('python3') && command.includes('acceptance.py')) return {{ exitCode: 0, stdout: '{json.dumps({"criteria": [{"index": 1, "text": "crit1_text"}]})}' }};
  if (command.startsWith('python3') && command.includes('common.py')) return {{ exitCode: 0, stdout: '{json.dumps({"issueBranch": "runs/test#01"})}' }};
  if (command.startsWith('python3') && command.includes('learner.py')) return {{ exitCode: 0, stdout: '{json.dumps({"candidates": []})}' }};
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
let result = null;
let error = null;
try {{
  result = await new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'runCommand', 'prompt', source)(
    args, agent, parallel, pipeline, phase, log, runCommand, prompt
  );
}} catch (e) {{
  error = e.message || String(e);
}}
process.stdout.write(JSON.stringify({{ result, calls, commandCalls, error }}));
"""
            res = subprocess.run(["node", "--input-type=module", "--eval", driver], text=True, capture_output=True)
            self.assertEqual(0, res.returncode, res.stderr)
            return json.loads(res.stdout)

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
