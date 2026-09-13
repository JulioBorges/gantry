#!/usr/bin/env python3
"""End-to-end contracts for declared absolute and differential gates."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATES = REPO_ROOT / ".agents" / "skills" / "gantry" / "scripts" / "gates.py"
MAPPING = {
    "findings": "/result~1data/findings",
    "rule": "/rule~1id",
    "file": "/path",
    "line": "/line",
    "message": "/message~0text",
    "severity": "/severity",
}


class DifferentialGateTests(unittest.TestCase):
    def run_gate(self, root: Path, base: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GATES), "--run", "--diff-base", base, "--cwd", str(root), "--json", *extra],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def init_repository(self, root: Path, findings: list[dict[str, object]]) -> str:
        subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "gate@example.test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Gate Test"], cwd=root, check=True)
        (root / ".gantry").mkdir()
        (root / "tools").mkdir()
        (root / "src").mkdir()
        (root / "src" / "greeting.py").write_text("print('hello')\n", encoding="utf-8")
        (root / ".gantry" / "config.json").write_text(
            json.dumps(
                {
                    "checks": [
                        {"name": "unit", "command": "python3 tools/unit.py", "mode": "absolute"},
                        {
                            "name": "lint",
                            "command": "python3 tools/lint.py",
                            "mode": "differential",
                            "mapping": MAPPING,
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        (root / "tools" / "unit.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        (root / "tools" / "lint.py").write_text(
            """import json
from pathlib import Path

payload = json.loads(Path("findings.json").read_text(encoding="utf-8"))
print(json.dumps({"result/data": {"findings": payload}}))
""",
            encoding="utf-8",
        )
        self.write_findings(root, findings)
        self.commit(root, "base")
        return self.git(root, "rev-parse", "HEAD")

    def write_findings(self, root: Path, findings: list[dict[str, object]]) -> None:
        rendered = [
            {key: str(root / value.removeprefix("$ROOT/")) if isinstance(value, str) and value.startswith("$ROOT/") else value
             for key, value in finding.items()}
            for finding in findings
        ]
        (root / "findings.json").write_text(json.dumps(rendered), encoding="utf-8")

    def commit(self, root: Path, message: str) -> None:
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", message], cwd=root, check=True)

    def git(self, root: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

    def finding(
        self, rule: str, path: str, message: str, severity: str, line: int = 1
    ) -> dict[str, object]:
        return {
            "rule/id": rule,
            "path": path,
            "line": line,
            "message~text": message,
            "severity": severity,
        }

    def run_scenario(
        self, base_findings: list[dict[str, object]], delivery_findings: list[dict[str, object]]
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        base = self.init_repository(root, base_findings)
        self.write_findings(root, delivery_findings)
        self.commit(root, "delivery")
        result = self.run_gate(root, base)
        return result, json.loads(result.stdout)

    def test_new_and_aggravated_findings_fail_while_resolved_and_preexisting_remain_visible(self) -> None:
        base = [
            self.finding("old", "src/greeting.py", "kept", "warning"),
            self.finding("aggravated", "src/greeting.py", "worse", "warning"),
            self.finding("resolved", "src/greeting.py", "fixed", "info"),
        ]
        delivery = [
            self.finding("old", "$ROOT/src/greeting.py", "kept", "info"),
            self.finding("aggravated", "src/greeting.py", "worse", "error"),
            self.finding("new", "src/greeting.py", "added", "warning"),
        ]
        result, payload = self.run_scenario(base, delivery)

        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual("fail", payload["verdict"])
        lint = next(gate for gate in payload["gates"] if gate["name"] == "lint")
        self.assertEqual("src/greeting.py", lint["preexisting"][0]["file"])
        self.assertEqual(["aggravated"], [item["rule"] for item in lint["aggravated"]])
        self.assertEqual(["new"], [item["rule"] for item in lint["new"]])
        self.assertEqual(["resolved"], [item["rule"] for item in lint["resolved"]])

    def test_same_or_lower_severity_and_resolved_findings_pass(self) -> None:
        result, payload = self.run_scenario(
            [
                self.finding("old", "src/greeting.py", "kept", "warning"),
                self.finding("resolved", "src/greeting.py", "fixed", "info"),
            ],
            [self.finding("old", "src/greeting.py", "kept", "info")],
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("pass", payload["verdict"])
        lint = next(gate for gate in payload["gates"] if gate["name"] == "lint")
        self.assertEqual(["old"], [item["rule"] for item in lint["preexisting"]])
        self.assertEqual(["resolved"], [item["rule"] for item in lint["resolved"]])

    def test_declared_absolute_check_uses_its_exit_code(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        base = self.init_repository(root, [])
        (root / "tools" / "unit.py").write_text("raise SystemExit(9)\n", encoding="utf-8")
        self.commit(root, "failing absolute check")

        result = self.run_gate(root, base)
        payload = json.loads(result.stdout)

        self.assertEqual(1, result.returncode, result.stderr)
        unit = next(gate for gate in payload["gates"] if gate["name"] == "unit")
        self.assertEqual({"exit_code": 9, "status": "fail"}, {key: unit[key] for key in ("exit_code", "status")})

    def test_invalid_pointers_and_severities_fail_the_declared_gate(self) -> None:
        for mapping, findings in (
            ({**MAPPING, "rule": "/bad~2escape"}, [self.finding("old", "src/greeting.py", "kept", "warning")]),
            ({**MAPPING, "severity": "/missing"}, [self.finding("old", "src/greeting.py", "kept", "warning")]),
            (MAPPING, [self.finding("old", "src/greeting.py", "kept", "fatal")]),
        ):
            with self.subTest(mapping=mapping, findings=findings):
                temp = tempfile.TemporaryDirectory()
                self.addCleanup(temp.cleanup)
                root = Path(temp.name)
                base = self.init_repository(root, [])
                config = json.loads((root / ".gantry" / "config.json").read_text(encoding="utf-8"))
                config["checks"][1]["mapping"] = mapping
                (root / ".gantry" / "config.json").write_text(json.dumps(config), encoding="utf-8")
                self.write_findings(root, findings)
                self.commit(root, "invalid delivery")

                result = self.run_gate(root, base)
                payload = json.loads(result.stdout)

                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual("fail", payload["verdict"])
                lint = next(gate for gate in payload["gates"] if gate["name"] == "lint")
                self.assertTrue(lint["invalid"])

    def test_duplicate_normalized_identity_names_the_source_and_identity(self) -> None:
        duplicate = [
            self.finding("dup", "src/greeting.py", "same", "warning"),
            self.finding("dup", "./src/greeting.py", "same", "error"),
        ]
        for base_findings, delivery_findings, source in (
            (duplicate, [], "base"),
            ([], duplicate, "delivery"),
        ):
            with self.subTest(source=source):
                result, payload = self.run_scenario(base_findings, delivery_findings)
                lint = next(gate for gate in payload["gates"] if gate["name"] == "lint")

                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual("fail", payload["verdict"])
                self.assertEqual(source, lint["invalid"][0]["source"])
                self.assertEqual(
                    {"rule": "dup", "file": "src/greeting.py", "message": "same"},
                    lint["invalid"][0]["identity"],
                )


if __name__ == "__main__":
    unittest.main()
