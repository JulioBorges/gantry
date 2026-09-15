#!/usr/bin/env python3
"""Contract tests for the reference-tier end-to-end proof."""
import os
import unittest
from pathlib import Path

class ReferenceTierProofTests(unittest.TestCase):
    def test_proof_records_the_unplanned_and_approved_execution_properties(self) -> None:
        readme = (Path(__file__).parents[1] / "fixture" / "README.md").read_text(encoding="utf-8")
        
        # Exact commands
        self.assertIn("python3 fixture/tools/copy_fixture.py --mode unplanned", readme)
        self.assertIn("python3 fixture/tools/copy_fixture.py --mode approved", readme)
        
        # Tier and Run-log paths
        self.assertIn("reference", readme)
        self.assertIn("run-20260914T214531Z-19a5fb.jsonl", readme)
        self.assertIn("run-20260914T214012Z-plan12.jsonl", readme)
        self.assertIn("ee61815efea9", readme)
        self.assertIn("bc054eb612dc", readme)
        self.assertIn("- [x]", readme)
        
        # Planning-stop observation
        self.assertIn("planning-approval stop", readme)
        self.assertIn("Status: draft", readme)
        self.assertIn("unchanged", readme)
        
        # Approved copy mutation
        self.assertIn("mutating roadmap through `roadmap.py` after Critic acceptance", readme)
        
        # Draft PR body
        self.assertIn("`greet()` already existed", readme)
        self.assertIn("added subprocess tests", readme)
        
        # Spec changelog
        spec = (Path(__file__).parents[1] / ".scratch" / "gantry-migration" / "spec.md").read_text(encoding="utf-8")
        self.assertIn("no engine, database, MCP service", spec)
        self.assertIn("reference tier", spec)

if __name__ == "__main__":
    unittest.main()
