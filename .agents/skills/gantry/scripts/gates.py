#!/usr/bin/env python3
"""Detect and run repository quality gates, emitting a machine-readable verdict."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

FRONTEND_RE = re.compile(r"(\.(tsx|jsx|vue|svelte|css|scss|less|html)$)|(/|^)(components|pages|app|ui|views|layouts|public|styles|dashboard/src)/", re.IGNORECASE)
NODE_SCRIPT_ORDER = ["lint", "typecheck", "format:check", "test", "build", "pack:check"]
MAKE_TARGETS = ["lint", "typecheck", "test", "build"]


def sh(command: list[str] | str, cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        result = subprocess.run(command, cwd=cwd, shell=isinstance(command, str), capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "CI": "1", "FORCE_COLOR": "0", "NO_COLOR": "1"})
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        return 124, f"timed out after {timeout}s\n{error.stdout or ''}{error.stderr or ''}"
    except FileNotFoundError as error:
        return 127, str(error)


def package_manager(cwd: Path, package: dict) -> str:
    requested = str(package.get("packageManager", ""))
    for name in ("pnpm", "yarn", "bun", "npm"):
        if requested.startswith(name):
            return name
    if (cwd / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (cwd / "yarn.lock").exists():
        return "yarn"
    return "bun" if (cwd / "bun.lockb").exists() or (cwd / "bun.lock").exists() else "npm"


def detect(cwd: Path) -> dict:
    gates: list[dict] = []
    notes: list[str] = []
    package_path = cwd / "package.json"
    if package_path.exists():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            package, _ = {}, notes.append(f"package.json is not valid JSON: {error}")
        manager = package_manager(cwd, package)
        scripts = package.get("scripts", {}) or {}
        for name in NODE_SCRIPT_ORDER:
            if name in scripts:
                gates.append({"name": name, "source": "package.json", "command": f"{manager} run {name}"})
        if scripts and not any(gate["name"] == "test" for gate in gates):
            notes.append("package.json has scripts but no `test` script")
        if not (cwd / "node_modules").exists():
            notes.append("node_modules missing — install dependencies before running node gates")
    if any((cwd / name).exists() for name in ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")):
        config = (cwd / "pyproject.toml").read_text(encoding="utf-8") if (cwd / "pyproject.toml").exists() else ""
        if "ruff" in config:
            gates.append({"name": "ruff", "source": "pyproject.toml", "command": "ruff check ."})
        if "mypy" in config:
            gates.append({"name": "mypy", "source": "pyproject.toml", "command": "mypy ."})
        if "pytest" in config or (cwd / "pytest.ini").exists() or (cwd / "tests").exists():
            gates.append({"name": "pytest", "source": "pyproject.toml", "command": "pytest -q"})
    makefile = cwd / "Makefile"
    if makefile.exists():
        targets = set(re.findall(r"^([a-zA-Z0-9_.-]+):", makefile.read_text(encoding="utf-8"), re.MULTILINE))
        for name in MAKE_TARGETS:
            if name in targets and not any(gate["name"] == name for gate in gates):
                gates.append({"name": name, "source": "Makefile", "command": f"make {name}"})
    if (cwd / ".pre-commit-config.yaml").exists():
        gates.append({"name": "pre-commit", "source": ".pre-commit-config.yaml", "command": "pre-commit run --all-files"})
    hooks: list[str] = []
    if (cwd / ".husky").is_dir():
        hooks.extend(f".husky/{path.name}" for path in (cwd / ".husky").iterdir() if path.is_file() and not path.name.startswith("_"))
    for name in (".claude/settings.json", ".claude/settings.local.json"):
        path = cwd / name
        if path.exists():
            try:
                hooks.extend(f"{name}: {event} x{len(entries)}" for event, entries in (json.loads(path.read_text(encoding="utf-8")).get("hooks") or {}).items())
            except json.JSONDecodeError:
                notes.append(f"{name} is not valid JSON")
    ci: list[dict] = []
    workflows = cwd / ".github" / "workflows"
    if workflows.is_dir():
        for workflow in sorted(workflows.glob("*.y*ml")):
            text = workflow.read_text(encoding="utf-8")
            jobs: list[str] = []
            marker = re.search(r"^jobs:\s*$", text, re.MULTILINE)
            if marker:
                for line in text[marker.end():].splitlines():
                    if line and not line.startswith((" ", "\t", "#")):
                        break
                    match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
                    if match:
                        jobs.append(match.group(1))
            commands = [item.strip() for item in re.findall(r"^\s*(?:-\s*)?run:\s*(.+)$", text, re.MULTILINE)]
            ci.append({"workflow": str(workflow.relative_to(cwd)), "jobs": jobs, "run_steps": commands})
        declared = {gate["name"] for gate in gates}
        package_scripts = set()
        if package_path.exists():
            try:
                package_scripts = set((json.loads(package_path.read_text(encoding="utf-8")).get("scripts") or {}).keys())
            except json.JSONDecodeError:
                pass
        for workflow in ci:
            for job in workflow["jobs"]:
                if job in NODE_SCRIPT_ORDER and job not in declared:
                    notes.append(f"CI job `{job}` in {workflow['workflow']} has no matching package script")
            for command in workflow["run_steps"]:
                match = re.match(r"^(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?([A-Za-z0-9:_-]+)", command)
                if match and package_scripts and match.group(1) not in package_scripts and match.group(1) not in {"install", "ci", "test"}:
                    notes.append(f"CI runs `{command}` in {workflow['workflow']} but package.json has no `{match.group(1)}` script — CI and local commands have diverged")
    return {"gates": gates, "ci": ci, "hooks": hooks, "notes": notes}


def git_facts(cwd: Path, diff_base: str | None) -> dict:
    facts = {"is_git": (cwd / ".git").exists() or shutil.which("git") is not None}
    code, output = sh(["git", "status", "--porcelain"], cwd, 30)
    facts["tree_clean"] = code == 0 and not output.strip()
    facts["dirty_files"] = [line[3:] for line in output.splitlines()] if code == 0 else []
    code, output = sh(["git", "branch", "--show-current"], cwd, 30)
    facts["branch"] = output.strip() if code == 0 else None
    changed: list[str] = []
    if diff_base:
        code, output = sh(["git", "diff", "--name-only", f"{diff_base}...HEAD"], cwd, 60)
        if code:
            code, output = sh(["git", "diff", "--name-only", diff_base, "HEAD"], cwd, 60)
        changed = [line for line in output.splitlines() if line.strip()] if code == 0 else []
        facts.update({"diff_base": diff_base, "diff_error": None if code == 0 else output.strip()[:500]})
    facts["changed_files"] = changed
    facts["frontend_touched"] = any(FRONTEND_RE.search(path) for path in changed)
    return facts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="repository or worktree to inspect")
    parser.add_argument("--run", action="store_true", help="execute detected gates")
    parser.add_argument("--diff-base", help="Git ref to diff against")
    parser.add_argument("--timeout", type=int, default=900, help="seconds per gate")
    parser.add_argument("--only", help="comma-separated gate names")
    parser.add_argument("--tail", type=int, default=60, help="output lines per gate")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    cwd = Path(args.cwd).resolve()
    result = detect(cwd)
    result.update({"cwd": str(cwd), "git": git_facts(cwd, args.diff_base)})
    only = {item.strip() for item in args.only.split(",")} if args.only else None
    failures = 0
    for gate in result["gates"]:
        if only and gate["name"] not in only:
            gate["status"] = "skipped"
        elif not args.run:
            gate["status"] = "not_run"
        else:
            code, output = sh(gate["command"], cwd, args.timeout)
            gate.update({"exit_code": code, "output_tail": "\n".join(output.splitlines()[-args.tail:]), "status": "pass" if code == 0 else "fail"})
            failures += code != 0
    result["verdict"] = "no_gates" if not result["gates"] else ("not_run" if not args.run else ("fail" if failures else "pass"))
    result["requirements"] = []
    if result["git"]["frontend_touched"]:
        result["requirements"].append("frontend files changed: AGENTS.md requires Playwright validation before completion")
    if not result["git"]["tree_clean"]:
        result["requirements"].append("working tree is dirty: uncommitted changes are not part of the delivery")
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"cwd: {cwd}  branch: {result['git'].get('branch')}  tree_clean: {result['git']['tree_clean']}")
        for gate in result["gates"]:
            print(f"  [{gate['status']}] {gate['name']}: {gate['command']}")
        print(f"verdict: {result['verdict']}")
    return {"pass": 0, "fail": 1, "no_gates": 2, "not_run": 0}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
