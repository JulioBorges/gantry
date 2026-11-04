"""Regression for planning entry in a repository that predates Gantry (Issue gantry-harness#27)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import re
import unittest

REPO_ROOT = Path(__file__).parent.parent
SKILLS = REPO_ROOT / ".agents" / "skills"
PLAN_SKILL = SKILLS / "gantry-plan" / "SKILL.md"
GANTRY_SKILL = SKILLS / "gantry" / "SKILL.md"
SCRIPTS_DIR = SKILLS / "gantry" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import execution  # noqa: E402


def host_gate_block(skill: Path) -> str:
    text = skill.read_text(encoding="utf-8")
    start = text.index("<!-- host-gate-protocol:start -->")
    end = text.index("<!-- host-gate-protocol:end -->")
    return text[start:end]


class GantryPlanExistingProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo = self.temp_dir / "legacy-app"
        self.home = self.temp_dir / "home"
        self.home.mkdir()
        self.env = {**os.environ, "HOME": str(self.home), "GANTRY_PROFILE_ROOT": str(self.home / "profiles")}
        for name in ("CODEX_THREAD_ID", "CODEX_HOME", "CLAUDECODE", "CLAUDE_CODE_SESSION_ID",
                     "OPENCODE_SESSION_ID", "ANTIGRAVITY_SESSION_ID"):
            self.env.pop(name, None)
        git = ["git", "-c", "user.email=t@example.com", "-c", "user.name=t"]
        subprocess.run(["git", "init", "--quiet", str(self.repo)], check=True)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "app.py").write_text("print('legacy')\n", encoding="utf-8")
        (self.repo / "README.md").write_text("# Legacy app\n", encoding="utf-8")
        subprocess.run(git + ["add", "."], cwd=self.repo, check=True)
        subprocess.run(git + ["commit", "--quiet", "-m", "legacy"], cwd=self.repo, check=True)
        # The pack arrives later, with no .gantry/, CONTEXT.md, PRD.md, docs/adr or .scratch.
        for skill in ("gantry", "gantry-plan"):
            shutil.copytree(SKILLS / skill, self.repo / ".agents" / "skills" / skill,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.scripts = self.repo / ".agents" / "skills" / "gantry" / "scripts"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_script(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], cwd=self.repo, env=self.env,
                              capture_output=True, text=True, timeout=60)

    def test_host_preflight_without_selection_is_unknown_with_actionable_diagnostic(self):
        res = self.run_script(self.scripts / "execution.py", "host", "--require-resolved", "--json", "--cwd", self.repo)
        self.assertEqual(1, res.returncode, res.stderr)
        data = json.loads(res.stdout)
        # Installed harness CLIs are hints only; several of them make the result ambiguous.
        self.assertIn(data["status"], {"unknown", "ambiguous"})
        self.assertTrue(any("--host" in line for line in data["diagnostics"]))

    def test_confirmed_host_resolves_and_free_text_plan_starts_in_existing_project(self):
        host = self.run_script(self.scripts / "execution.py", "host", "--require-resolved", "--json",
                               "--cwd", self.repo, "--host", "codex")
        self.assertEqual(0, host.returncode, host.stdout + host.stderr)
        data = json.loads(host.stdout)
        self.assertEqual("resolved", data["status"])
        self.assertIn("capabilities", data)

        plan = self.run_script(self.scripts / "plan.py", "--goal", "chatbot quote with multiple items and options", "--json")
        self.assertEqual(0, plan.returncode, plan.stdout + plan.stderr)
        interview = json.loads(plan.stdout)
        self.assertTrue(interview["slug"])
        self.assertEqual(4, len(interview["phases"]))

    def test_unsupported_host_is_invalid_with_message(self):
        res = self.run_script(self.scripts / "execution.py", "host", "--require-resolved", "--json",
                              "--cwd", self.repo, "--host", "cursor")
        self.assertEqual(1, res.returncode)
        data = json.loads(res.stdout)
        self.assertEqual("invalid", data["status"])
        self.assertIn("Unsupported explicit host", " ".join(data["diagnostics"]))

    def test_host_gate_protocol_is_identical_in_gantry_and_gantry_plan(self):
        canonical = host_gate_block(GANTRY_SKILL)
        self.assertEqual(canonical, host_gate_block(PLAN_SKILL),
                         "gantry-plan must carry the same host gate protocol block as gantry/SKILL.md")

    def test_host_gate_protocol_covers_every_status(self):
        flat = " ".join(host_gate_block(GANTRY_SKILL).split())
        self.assertIn("`unknown` or `ambiguous`: ask the operator", flat)
        self.assertIn("`--host` comes only from that explicit operator confirmation", flat)
        self.assertIn("never guess or assume the host", flat)
        self.assertIn("No operator can answer", flat)
        self.assertIn("the same channels `wait_gate.py` accepts", flat)
        self.assertIn("`invalid`", flat)
        self.assertIn("Never stop silently", flat)
        self.assertNotIn("Ovis", flat)

    def test_resume_follows_the_host_gate_protocol(self):
        flat = " ".join(GANTRY_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("any role work, following the host gate protocol above", flat)

    def test_skill_host_list_matches_supported_harnesses(self):
        flat = " ".join(host_gate_block(GANTRY_SKILL).split())
        match = re.search(r"that `execution\.py` supports \(([^)]*)\)", flat)
        self.assertIsNotNone(match, "host list not found in the host gate protocol")
        listed = set(re.findall(r"`([^`]+)`", match.group(1)))
        self.assertEqual(set(execution.SUPPORTED_HARNESSES), listed)

    def test_hints_never_select_host_without_explicit_flag(self):
        # Saved preference and environment hints are present; without --host nothing selects a host.
        (self.repo / ".gantry").mkdir()
        (self.repo / ".gantry" / "config.json").write_text(
            json.dumps({"execution": {"hostHarness": "codex"}}), encoding="utf-8")
        self.env["CODEX_THREAD_ID"] = "hint-only"
        res = subprocess.run([sys.executable, str(self.scripts / "execution.py"), "host", "--require-resolved",
                              "--json", "--cwd", str(self.repo)], cwd=self.repo, env=self.env,
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        self.assertEqual(1, res.returncode, res.stderr)
        data = json.loads(res.stdout)
        self.assertIn(data["status"], {"unknown", "ambiguous"})
        self.assertIsNone(data["effectiveHost"])
        self.assertNotIn("capabilities", data)
        self.assertTrue(data["diagnostics"])

    def test_host_gate_is_the_first_section_of_gantry_plan(self):
        """The host gate must be read before any other step of /gantry-plan (gantry-harness#27).

        Agents act on the first instructions they read, so the gate is the first `##` section and comes
        before the entry modes. This checks section order instead of a line count.
        """
        headings = [line for line in PLAN_SKILL.read_text(encoding="utf-8").splitlines() if line.startswith("## ")]
        self.assertEqual("## Resolve the invocation host first", headings[0])
        self.assertLess(headings.index("## Resolve the invocation host first"), headings.index("## Dual Entry Modes"))

    def test_plan_skill_reports_failures_and_accepts_repo_without_gantry_history(self):
        flat = " ".join(PLAN_SKILL.read_text(encoding="utf-8").split())
        self.assertIn("## Failure reporting and optional context", flat)
        self.assertIn("without Gantry history", flat)
        self.assertNotIn("Unknown, ambiguous or unsupported identity stops planning entry", flat)


if __name__ == "__main__":
    unittest.main()
