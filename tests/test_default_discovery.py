#!/usr/bin/env python3
"""Exercise default discovery in an isolated package, without suite recursion."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class DefaultUnittestDiscoveryTests(unittest.TestCase):
    def test_default_discovery_executes_a_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tests = root / "tests"
            tests.mkdir()
            # Removing the real package marker must break this test.
            shutil.copyfile(REPO_ROOT / "tests" / "__init__.py", tests / "__init__.py")
            (tests / "test_discovery.py").write_text(
                "import unittest\n"
                "class DiscoveryTest(unittest.TestCase):\n"
                "    def test_default_discovery_probe(self):\n"
                "        self.assertEqual(2 + 2, 4)\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-v"],
                cwd=root, text=True, capture_output=True, check=False, timeout=30,
            )
            output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, output)
            self.assertIn("test_default_discovery_probe", output)
            self.assertIn("Ran 1 test", output)
