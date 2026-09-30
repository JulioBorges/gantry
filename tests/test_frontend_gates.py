"""Frontend completion requires an executed, declared browser-validation check."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATES = Path(__file__).resolve().parents[1] / ".agents/skills/gantry/scripts/gates.py"


class FrontendGateTests(unittest.TestCase):
    def fixture(self, root: Path, name: str = "unit", exit_code: int = 0) -> str:
        for args in (["init", "--quiet"], ["config", "user.name", "Gate Test"],
                     ["config", "user.email", "gate@example.test"]):
            subprocess.run(["git", *args], cwd=root, check=True)
        (root / ".gantry").mkdir()
        (root / ".gantry/config.json").write_text(json.dumps({"checks": [
            {"name": name, "command": f'{sys.executable} -c "raise SystemExit({exit_code})"', "mode": "absolute"}
        ]}), encoding="utf-8")
        (root / "screen.html").write_text("before", encoding="utf-8")
        self.commit(root)
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        (root / "screen.html").write_text("after", encoding="utf-8")
        self.commit(root)
        return base

    def commit(self, root: Path) -> None:
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "fixture"], cwd=root, check=True)

    def invoke(self, root: Path, base: str, *args: str) -> dict:
        result = subprocess.run([sys.executable, str(GATES), "--cwd", str(root),
                                 "--diff-base", base, "--json", *args],
                                capture_output=True, text=True, check=False)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["git"]["frontend_touched"], True)
        self.assertEqual(payload["git"]["tree_clean"], True)
        return payload

    def test_frontend_without_browser_check_keeps_requirement_and_gate_verdict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.invoke(root, self.fixture(root), "--run")
            self.assertEqual(payload["verdict"], "pass")
            self.assertEqual(len(payload["requirements"]), 1)
            self.assertIn("browser-validation", payload["requirements"][0])
            self.assertNotIn("AGENTS.md", payload["requirements"][0])
            self.assertFalse((root / "AGENTS.md").exists())

    def test_executed_passing_browser_check_clears_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self.invoke(root, self.fixture(root, "browser-validation"), "--run")
            self.assertEqual(payload["gates"][0]["status"], "pass")
            self.assertEqual(payload["verdict"], "pass")
            self.assertEqual(payload["requirements"], [])
            # Exercise the canonical workflow predicate rather than duplicating its condition.
            workflow = (GATES.parents[1] / "reference/round-workflow.md").read_text(encoding="utf-8")
            function = re.search(r"async function integrationGatePasses\(.*?\n}", workflow, re.DOTALL)
            self.assertIsNotNone(function)
            script = ("const scripts = ''; const A = {}; "
                      "async function runWorkflowCommand() { return {stdout: process.argv[1]} }\n"
                      + function.group(0) + "\nintegrationGatePasses().then(console.log)")
            accepted = subprocess.check_output(["node", "-e", script, json.dumps(payload)], text=True)
            self.assertEqual(accepted.strip(), "true")

    def test_failed_unexecuted_or_skipped_browser_check_keeps_requirement(self):
        for exit_code, args, status, verdict in (
            (1, ["--run"], "fail", "fail"),
            (0, [], "not_run", "not_run"),
            (0, ["--run", "--only", "unit"], "skipped", "pass"),
        ):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                payload = self.invoke(root, self.fixture(root, "browser-validation", exit_code), *args)
                self.assertEqual(payload["gates"][0]["status"], status)
                self.assertEqual(payload["verdict"], verdict)
                self.assertEqual(len(payload["requirements"]), 1)

    def test_differential_browser_check_cannot_clear_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.fixture(root, "browser-validation")
            config = root / ".gantry/config.json"
            policy = json.loads(config.read_text())
            policy["checks"][0].update({"mode": "differential", "command": "echo '[]'", "mapping": {
                "findings": "", "rule": "/rule", "file": "/file", "line": "/line",
                "message": "/message", "severity": "/severity"}})
            config.write_text(json.dumps(policy), encoding="utf-8")
            self.commit(root)
            payload = self.invoke(root, base, "--run")
            self.assertEqual(payload["gates"][0]["status"], "pass")
            self.assertEqual(payload["verdict"], "pass")
            self.assertEqual(len(payload["requirements"]), 1)


if __name__ == "__main__":
    unittest.main()
