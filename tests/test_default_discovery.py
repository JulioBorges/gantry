#!/usr/bin/env python3
"""Regression coverage for the repository's default unittest command."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_ENV = "_GANTRY_DEFAULT_DISCOVERY_PROBE"


if os.environ.get(PROBE_ENV):

    class DefaultDiscoveryProbe(unittest.TestCase):
        def test_default_discovery_probe(self) -> None:
            self.assertTrue(True)


else:

    class DefaultUnittestDiscoveryTests(unittest.TestCase):
        def test_default_discovery_executes_a_test(self) -> None:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-v"],
                cwd=REPO_ROOT,
                env={**os.environ, PROBE_ENV: "1"},
                text=True,
                capture_output=True,
                check=False,
            )

            output = result.stdout + result.stderr
            self.assertEqual(0, result.returncode, output)
            self.assertIn("test_default_discovery_probe", output)


if __name__ == "__main__":
    unittest.main()
