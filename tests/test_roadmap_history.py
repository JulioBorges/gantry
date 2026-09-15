"""Completed delivery waves remain stable as the approved backlog grows."""
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/gantry/scripts"
sys.path.insert(0, str(SCRIPTS))

from common import Issue  # noqa: E402
from frontier import select_scope  # noqa: E402
from roadmap import delivery_levels, render_roadmap  # noqa: E402


def issue(ref, status="ready-for-agent", blockers=()):
    spec, number = ref.split("#")
    return Issue(ref, spec, int(number), Path(ref), ref, status, list(blockers))


def roadmap(checklist):
    return (
        "| Issues completed | **0 / 0** |\n"
        "| Specs completed | **0 / 0** |\n"
        "| Execution waves | **0** |\n"
        "<!-- BEGIN GENERATED: spec progress -->\n\n<!-- END GENERATED: spec progress -->\n"
        "<!-- BEGIN GENERATED: issue checklist -->\n" + checklist
        + "\n<!-- END GENERATED: issue checklist -->\n"
    )


class RoadmapHistoryTests(unittest.TestCase):
    def test_completed_waves_preserved_and_new_dependency_chain_appended(self):
        issues = {entry.ref: entry for entry in [
            issue("old#01", "done"), issue("old#02", "done", ["old#01"]),
            issue("new#01", blockers=["old#01"]),
            issue("new#02", blockers=["new#01"]), issue("new#03", blockers=["new#01"]),
        ]}
        text = roadmap("### Wave 0 — 1/1 done\n- [x] **`old#01`**\n"
                       "### Wave 1 — 1/1 done\n- [x] **`old#02`**\n")
        rendered = render_roadmap(text, issues, Path.cwd())
        self.assertEqual({"old#01": 0, "old#02": 1, "new#01": 2,
                          "new#02": 3, "new#03": 3}, delivery_levels(rendered, issues))
        self.assertIn("| Execution waves | **4** |", rendered)
        self.assertEqual(rendered, render_roadmap(rendered, issues, Path.cwd()))
        selected, errors = select_scope(["wave:3"], issues, rendered)
        self.assertEqual({"new#02", "new#03"}, selected)
        self.assertEqual([], errors)
        issues["new#01"].status = "done"
        completed = render_roadmap(rendered, issues, Path.cwd())
        self.assertEqual(2, delivery_levels(completed, issues)["new#01"])
        issues["later#01"] = issue("later#01")
        self.assertEqual(3, delivery_levels(completed, issues)["later#01"])

    def test_stale_checkboxes_do_not_freeze_incomplete_wave(self):
        issues = {"old#01": issue("old#01", "done"), "new#01": issue("new#01")}
        text = roadmap("### Wave 0 — 1/1 done\n- [x] **`old#01`**\n"
                       "### Wave 0 — 1/1 done\n- [x] **`new#01`**\n")
        self.assertEqual({"old#01": 0, "new#01": 1}, delivery_levels(text, issues))

    def test_initial_generation_uses_dependency_depth(self):
        issues = {"a#01": issue("a#01"), "a#02": issue("a#02", blockers=["a#01"])}
        self.assertEqual({"a#01": 0, "a#02": 1}, delivery_levels(roadmap(""), issues))

    def test_cycles_and_backward_historical_dependencies_are_rejected(self):
        issues = {"a#01": issue("a#01", "done"), "a#02": issue("a#02", "done", ["a#01"])}
        text = roadmap("### Wave 1\n- [x] **`a#01`**\n### Wave 0\n- [x] **`a#02`**\n")
        with self.assertRaisesRegex(ValueError, "conflict"):
            delivery_levels(text, issues)
        issues["a#01"].blocked_by = ["a#02"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            delivery_levels(text, issues)
