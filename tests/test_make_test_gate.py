#!/usr/bin/env python3
"""Integration coverage for the repository's declared test gate."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATES = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "gates.py"
PROBE_ENV = "_GANTRY_MAKE_TEST_GATE_PROBE"


if os.environ.get(PROBE_ENV):

    class MakeTestGateProbe(unittest.TestCase):
        def test_make_test_gate_probe(self) -> None:
            self.assertTrue(True)

else:

    class MakeTestGateTests(unittest.TestCase):
        def test_gates_detect_and_execute_the_make_test_gate(self) -> None:
            result = subprocess.run(
                [
                    sys.executable,
                    str(GATES),
                    "--run",
                    "--diff-base",
                    "b8d7146908a26e7f68fc4a8dda2e97e05e7f1492",
                    "--cwd",
                    str(REPO_ROOT),
                    "--json",
                ],
                cwd=REPO_ROOT,
                env={**os.environ, PROBE_ENV: "1"},
                text=True,
                capture_output=True,
                check=False,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("pass", payload["verdict"])
            self.assertEqual(
                [{"name": "test", "source": "Makefile", "command": "make test", "exit_code": 0,
                  "output_tail": payload["gates"][0]["output_tail"], "status": "pass"}],
                payload["gates"],
            )
            self.assertIn("test_make_test_gate_probe", payload["gates"][0]["output_tail"])


if __name__ == "__main__":
    unittest.main()
