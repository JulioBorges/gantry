#!/usr/bin/env python3
"""Regression tests for portable Gantry policy and issue parsing."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "gantry" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common import parse_issue, resolve_policy  # noqa: E402


class PolicyResolutionTests(unittest.TestCase):
    def test_defaults_are_sparse_and_overlay_preserves_unsupplied_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()

            defaults = resolve_policy(root)
            self.assertEqual(".scratch/{slug}/spec.md", defaults["artifacts"]["specs"])
            self.assertEqual(".scratch/{slug}/issues", defaults["artifacts"]["issues"])
            self.assertEqual("docs/adr", defaults["artifacts"]["adrs"])
            self.assertEqual("docs/adr", defaults["artifacts"]["decisions"])
            self.assertEqual("CONTEXT.md", defaults["artifacts"]["context"])
            self.assertEqual("docs/agents/issue-tracker.md", defaults["artifacts"]["issueTracker"])
            self.assertEqual(".gantry/templates", defaults["templates"]["dir"])
            self.assertEqual({}, defaults["templates"]["headingMap"])
            self.assertEqual("main", defaults["git"]["target"])
            self.assertEqual("gantry/", defaults["git"]["prefix"])
            self.assertEqual(2, defaults["budget"]["corrections"])
            self.assertEqual(0.15, defaults["budget"]["contextShare"])
            self.assertEqual(900, defaults["dashboard"]["staleAfterSeconds"])

            config = root / ".gantry" / "config.json"
            config.parent.mkdir()
            config.write_text(
                '{"git":{"target":"trunk"},"budget":{"contextShare":0.2}}',
                encoding="utf-8",
            )
            overlay = resolve_policy(root)
            self.assertEqual("trunk", overlay["git"]["target"])
            self.assertEqual("gantry/", overlay["git"]["prefix"])
            self.assertEqual(0.2, overlay["budget"]["contextShare"])
            self.assertEqual(2, overlay["budget"]["corrections"])
            self.assertEqual(900, overlay["dashboard"]["staleAfterSeconds"])

    def test_current_issue_markdown_conventions_keep_the_same_parsed_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            issue_path = Path(temp) / ".scratch" / "sample" / "issues" / "01-parser-regression.md"
            issue_path.parent.mkdir(parents=True)
            issue_path.write_text(
                """# Parser regression

Type: issue
Status: ready-for-agent
Slice: `sample#01`

## Acceptance criteria

- [ ] preserves the first criterion
- [x] preserves the second criterion

## Blocked by

- `other#02` — required first
- `third#03` — required second
""",
                encoding="utf-8",
            )

            issue = parse_issue(issue_path)

            self.assertEqual("sample#01", issue.ref)
            self.assertEqual("ready-for-agent", issue.status)
            self.assertEqual(["preserves the first criterion", "preserves the second criterion"],
                             [criterion.text for criterion in issue.criteria])
            self.assertEqual([False, True], [criterion.checked for criterion in issue.criteria])
            self.assertEqual(["other#02", "third#03"], issue.blocked_by)

    def test_existing_issue_keeps_its_reference_status_criteria_and_blockers(self) -> None:
        issue = parse_issue(
            Path(__file__).resolve().parents[1]
            / ".scratch"
            / "gantry-migration"
            / "issues"
            / "01-portable-policy-and-legacy-loop.md"
        )

        self.assertEqual("gantry-migration#01", issue.ref)
        self.assertEqual("done", issue.status)
        self.assertEqual(5, len(issue.criteria))
        self.assertEqual([], issue.blocked_by)


if __name__ == "__main__":
    unittest.main()
