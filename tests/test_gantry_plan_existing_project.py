"""Regression for planning entry in a repository that predates Gantry (Issue gantry-harness#27)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).parent.parent
SKILLS = REPO_ROOT / ".agents" / "skills"
PLAN_SKILL = SKILLS / "gantry-plan" / "SKILL.md"


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

    def test_skill_turns_unknown_host_into_operator_question_not_silent_stop(self):
        content = PLAN_SKILL.read_text(encoding="utf-8")
        section = content[content.index("## Resolve the invocation host first"):content.index("## Dual Entry Modes")]
        self.assertIn("ask the operator which Host Harness", section)
        self.assertIn("--host <host>", section)
        self.assertIn("Never stop silently", section)
        self.assertIn("next step", section)
        self.assertIn("without Gantry history", section)
        self.assertNotIn("Unknown, ambiguous or unsupported\nidentity stops planning entry", content)

    def test_host_gate_is_inside_the_first_120_lines(self):
        lines = PLAN_SKILL.read_text(encoding="utf-8").splitlines()
        head = "\n".join(lines[:120])
        self.assertIn("Never stop silently", head)
        self.assertIn("ask the operator which Host Harness", head)


if __name__ == "__main__":
    unittest.main()
