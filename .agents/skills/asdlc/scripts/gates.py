#!/usr/bin/env python3
"""Detect and run the repository's quality gates; emit a machine-readable verdict.

The adversarial critic runs this itself instead of trusting the implementer's "tests pass". It looks
for whatever the repository actually declares and runs exactly those commands — never an invented
substitute — so "runnable locally with the same commands CI uses" stays true.

Detected sources (all optional, any combination):
  package.json  scripts named lint, typecheck, format:check, test, build, pack:check (in that order),
                run through the package manager implied by the lockfile / `packageManager` field
  pyproject.toml / pytest.ini / setup.cfg   -> pytest (plus ruff check when configured)
  Makefile      targets lint, typecheck, test, build
  .pre-commit-config.yaml -> pre-commit run --all-files
  .github/workflows/*.yml -> job names are listed (cannot run here) and checked against the scripts
  .husky/, .claude/settings.json hooks -> listed for the critic's awareness

Also reports: working-tree cleanliness, files changed since --diff-base, and whether any of them look
like frontend code (AGENTS.md then requires Playwright validation before the work is complete).

  gates.py                         detect only
  gates.py --run                   detect and run; exit 0 pass, 1 any failure, 2 no gates detected
  gates.py --run --diff-base main --cwd /path/to/worktree --json
"""
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


def sh(cmd: list[str] | str, cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "CI": "1", "FORCE_COLOR": "0", "NO_COLOR": "1"})
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired as e:
        return 124, f"timed out after {timeout}s\n{(e.stdout or '')}{(e.stderr or '')}"
    except FileNotFoundError as e:
        return 127, str(e)


def detect_package_manager(cwd: Path, pkg: dict) -> str:
    pm = str(pkg.get("packageManager", ""))
    for name in ("pnpm", "yarn", "bun", "npm"):
        if pm.startswith(name):
            return name
    if (cwd / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (cwd / "yarn.lock").exists():
        return "yarn"
    if (cwd / "bun.lockb").exists() or (cwd / "bun.lock").exists():
        return "bun"
    return "npm"


def detect(cwd: Path) -> dict:
    gates: list[dict] = []
    notes: list[str] = []

    pkg_path = cwd / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            pkg = {}
            notes.append(f"package.json is not valid JSON: {e}")
        pm = detect_package_manager(cwd, pkg)
        scripts = pkg.get("scripts", {}) or {}
        for name in NODE_SCRIPT_ORDER:
            if name in scripts:
                gates.append({"name": name, "source": "package.json", "command": f"{pm} run {name}"})
        if not any(g["name"] == "test" for g in gates) and scripts:
            notes.append("package.json has scripts but no `test` script")
        if not (cwd / "node_modules").exists():
            notes.append("node_modules missing — install dependencies before running node gates")

    if any((cwd / f).exists() for f in ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")):
        py_text = (cwd / "pyproject.toml").read_text(encoding="utf-8") if (cwd / "pyproject.toml").exists() else ""
        if "ruff" in py_text:
            gates.append({"name": "ruff", "source": "pyproject.toml", "command": "ruff check ."})
        if "mypy" in py_text:
            gates.append({"name": "mypy", "source": "pyproject.toml", "command": "mypy ."})
        if "pytest" in py_text or (cwd / "pytest.ini").exists() or (cwd / "tests").exists():
            gates.append({"name": "pytest", "source": "pyproject.toml", "command": "pytest -q"})

    mk = cwd / "Makefile"
    if mk.exists():
        targets = set(re.findall(r"^([a-zA-Z0-9_.-]+):", mk.read_text(encoding="utf-8"), re.MULTILINE))
        for t in MAKE_TARGETS:
            if t in targets and not any(g["name"] == t for g in gates):
                gates.append({"name": t, "source": "Makefile", "command": f"make {t}"})

    if (cwd / ".pre-commit-config.yaml").exists():
        gates.append({"name": "pre-commit", "source": ".pre-commit-config.yaml", "command": "pre-commit run --all-files"})

    hooks: list[str] = []
    if (cwd / ".husky").is_dir():
        hooks += [f".husky/{p.name}" for p in (cwd / ".husky").iterdir() if p.is_file() and not p.name.startswith("_")]
    for settings in (".claude/settings.json", ".claude/settings.local.json"):
        sp = cwd / settings
        if sp.exists():
            try:
                data = json.loads(sp.read_text(encoding="utf-8"))
                for event, entries in (data.get("hooks") or {}).items():
                    hooks.append(f"{settings}: {event} x{len(entries)}")
            except json.JSONDecodeError:
                notes.append(f"{settings} is not valid JSON")

    ci_jobs: list[dict] = []
    wf_dir = cwd / ".github" / "workflows"
    if wf_dir.is_dir():
        for wf in sorted(wf_dir.glob("*.y*ml")):
            text = wf.read_text(encoding="utf-8")
            jobs_m = re.search(r"^jobs:\s*$", text, re.MULTILINE)
            names: list[str] = []
            if jobs_m:
                for line in text[jobs_m.end():].splitlines():
                    if line and not line.startswith((" ", "\t", "#")):
                        break
                    m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
                    if m:
                        names.append(m.group(1))
            run_cmds = [c.strip() for c in re.findall(r"^\s*(?:-\s*)?run:\s*(.+)$", text, re.MULTILINE)]
            ci_jobs.append({"workflow": str(wf.relative_to(cwd)), "jobs": names, "run_steps": run_cmds})
        declared = {g["name"] for g in gates}
        pkg_scripts = set()
        if pkg_path.exists():
            try:
                pkg_scripts = set((json.loads(pkg_path.read_text(encoding="utf-8")).get("scripts") or {}).keys())
            except json.JSONDecodeError:
                pass
        for wf in ci_jobs:
            for job in wf["jobs"]:
                if job in NODE_SCRIPT_ORDER and job not in declared:
                    notes.append(f"CI job `{job}` in {wf['workflow']} has no matching package script")
            for step in wf["run_steps"]:
                m = re.match(r"^(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?([A-Za-z0-9:_-]+)", step.strip())
                if m and pkg_scripts and m.group(1) not in pkg_scripts and m.group(1) not in {"install", "ci", "test"}:
                    notes.append(f"CI runs `{step.strip()}` in {wf['workflow']} but package.json has no `{m.group(1)}` script — CI and local commands have diverged")

    return {"gates": gates, "ci": ci_jobs, "hooks": hooks, "notes": notes}


def git_facts(cwd: Path, diff_base: str | None) -> dict:
    facts: dict = {"is_git": (cwd / ".git").exists() or shutil.which("git") is not None}
    code, out = sh(["git", "status", "--porcelain"], cwd, 30)
    facts["tree_clean"] = code == 0 and out.strip() == ""
    facts["dirty_files"] = [l[3:] for l in out.splitlines()] if code == 0 else []
    code, out = sh(["git", "branch", "--show-current"], cwd, 30)
    facts["branch"] = out.strip() if code == 0 else None
    changed: list[str] = []
    if diff_base:
        code, out = sh(["git", "diff", "--name-only", f"{diff_base}...HEAD"], cwd, 60)
        if code != 0:
            code, out = sh(["git", "diff", "--name-only", diff_base, "HEAD"], cwd, 60)
        changed = [l for l in out.splitlines() if l.strip()] if code == 0 else []
        facts["diff_base"] = diff_base
        facts["diff_error"] = None if code == 0 else out.strip()[:500]
    facts["changed_files"] = changed
    facts["frontend_touched"] = any(FRONTEND_RE.search(f) for f in changed)
    return facts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cwd", default=".", help="repository or worktree to inspect")
    ap.add_argument("--run", action="store_true", help="execute the detected gates")
    ap.add_argument("--diff-base", default=None, help="ref to diff HEAD against (e.g. main)")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per gate command")
    ap.add_argument("--only", default=None, help="comma-separated gate names to run")
    ap.add_argument("--tail", type=int, default=60, help="output lines kept per gate")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cwd = Path(args.cwd).resolve()
    result = detect(cwd)
    result["cwd"] = str(cwd)
    result["git"] = git_facts(cwd, args.diff_base)

    only = {s.strip() for s in args.only.split(",")} if args.only else None
    failures = 0
    ran = 0
    for g in result["gates"]:
        if only and g["name"] not in only:
            g["status"] = "skipped"
            continue
        if not args.run:
            g["status"] = "not_run"
            continue
        code, out = sh(g["command"], cwd, args.timeout)
        lines = out.splitlines()
        g["exit_code"] = code
        g["output_tail"] = "\n".join(lines[-args.tail:])
        g["status"] = "pass" if code == 0 else "fail"
        ran += 1
        failures += 1 if code else 0

    if not result["gates"]:
        verdict = "no_gates"
    elif not args.run:
        verdict = "not_run"
    else:
        verdict = "fail" if failures else "pass"
    result["verdict"] = verdict
    result["requirements"] = []
    if result["git"]["frontend_touched"]:
        result["requirements"].append("frontend files changed: AGENTS.md requires Playwright validation before completion")
    if not result["git"]["tree_clean"]:
        result["requirements"].append("working tree is dirty: uncommitted changes are not part of the delivery")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"cwd: {cwd}  branch: {result['git'].get('branch')}  tree_clean: {result['git']['tree_clean']}")
        if not result["gates"]:
            print("no gates detected (no package.json scripts, pyproject, Makefile targets or pre-commit config)")
        for g in result["gates"]:
            print(f"  [{g.get('status')}] {g['name']}: {g['command']}" + (f" (exit {g['exit_code']})" if g.get("exit_code") else ""))
            if g.get("status") == "fail":
                print("      " + "\n      ".join(g["output_tail"].splitlines()[-15:]))
        for wf in result["ci"]:
            print(f"  ci {wf['workflow']}: jobs={', '.join(wf['jobs']) or '-'}")
        for h in result["hooks"]:
            print(f"  hook {h}")
        for n in result["notes"]:
            print(f"  note: {n}")
        for r in result["requirements"]:
            print(f"  REQUIRED: {r}")
        if args.diff_base:
            print(f"  changed since {args.diff_base}: {len(result['git']['changed_files'])} file(s), frontend_touched={result['git']['frontend_touched']}")
        print(f"verdict: {verdict}")

    return {"pass": 0, "fail": 1, "no_gates": 2, "not_run": 0}[verdict]


if __name__ == "__main__":
    sys.exit(main())
