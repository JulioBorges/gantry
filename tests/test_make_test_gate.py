#!/usr/bin/env python3
"""Run the real Makefile gate in a small repository, without suite recursion."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATES = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "gates.py"


class MakeTestGateTests(unittest.TestCase):
    def test_gates_detect_and_execute_the_make_test_gate(self) -> None:
        self.check_gate(failing=False)

    def test_make_test_failure_propagates_to_gate_verdict(self) -> None:
        self.check_gate(failing=True)

    def check_gate(self, *, failing: bool) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copyfile(REPO_ROOT / "Makefile", root / "Makefile")
            tests = root / "tests"
            tests.mkdir()
            shutil.copyfile(REPO_ROOT / "tests" / "__init__.py", tests / "__init__.py")
            (tests / "test_gate.py").write_text(
                "import unittest\n"
                "class GateTest(unittest.TestCase):\n"
                "    def test_make_test_gate_probe(self):\n"
                f"        self.assertEqual(2 + 2, {5 if failing else 4})\n",
                encoding="utf-8",
            )
            (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
            for args in (
                ["init", "--quiet"], ["config", "user.email", "gate@example.test"],
                ["config", "user.name", "Gate Test"], ["add", "."],
                ["-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "gate fixture"],
            ):
                subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=30)
            result = subprocess.run(
                [sys.executable, str(GATES), "--run", "--diff-base", "HEAD",
                 "--cwd", str(root), "--json"],
                cwd=root, text=True, capture_output=True, check=False, timeout=30,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(1 if failing else 0, result.returncode, result.stderr)
            self.assertEqual("fail" if failing else "pass", payload["verdict"])
            self.assertEqual([], payload["requirements"])
            self.assertEqual(1, len(payload["gates"]))
            gate = payload["gates"][0]
            self.assertEqual("test", gate["name"])
            self.assertEqual("Makefile", gate["source"])
            self.assertEqual("make test", gate["command"])
            self.assertEqual("fail" if failing else "pass", gate["status"])
            self.assertEqual(not failing, gate["exit_code"] == 0)
            self.assertIn("test_make_test_gate_probe", gate["output_tail"])
            self.assertIn("Ran 1 test", gate["output_tail"])
