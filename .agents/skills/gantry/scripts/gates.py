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
import tempfile
from pathlib import Path

from common import resolve_policy

FRONTEND_RE = re.compile(r"(\.(tsx|jsx|vue|svelte|css|scss|less|html)$)|(/|^)(components|pages|app|ui|views|layouts|public|styles|dashboard/src)/", re.IGNORECASE)
NODE_SCRIPT_ORDER = ["lint", "typecheck", "format:check", "test", "build", "pack:check"]
MAKE_TARGETS = ["lint", "typecheck", "test", "build"]
MAPPING_FIELDS = ("findings", "rule", "file", "line", "message", "severity")
SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}


def sh(command: list[str] | str, cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        result = subprocess.run(command, cwd=cwd, shell=isinstance(command, str), capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "CI": "1", "FORCE_COLOR": "0", "NO_COLOR": "1"})
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        return 124, f"timed out after {timeout}s\n{error.stdout or ''}{error.stderr or ''}"
    except FileNotFoundError as error:
        return 127, str(error)


def pointer_parts(pointer: object) -> list[str]:
    """Parse one RFC 6901 JSON Pointer, rejecting malformed escape sequences."""
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError("must be an RFC 6901 JSON Pointer")
    parts: list[str] = []
    for raw_part in pointer[1:].split("/") if pointer else []:
        part: list[str] = []
        index = 0
        while index < len(raw_part):
            if raw_part[index] != "~":
                part.append(raw_part[index])
                index += 1
                continue
            if index + 1 == len(raw_part) or raw_part[index + 1] not in "01":
                raise ValueError(f"has an invalid RFC 6901 escape in {pointer!r}")
            part.append("~" if raw_part[index + 1] == "0" else "/")
            index += 2
        parts.append("".join(part))
    return parts


def resolve_pointer(document: object, pointer: object) -> object:
    """Resolve an RFC 6901 pointer against JSON data."""
    current = document
    for part in pointer_parts(pointer):
        if isinstance(current, dict):
            if part not in current:
                raise ValueError(f"does not resolve {pointer!r}")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit() or (len(part) > 1 and part.startswith("0")):
                raise ValueError(f"does not resolve {pointer!r}")
            index = int(part)
            if index >= len(current):
                raise ValueError(f"does not resolve {pointer!r}")
            current = current[index]
        else:
            raise ValueError(f"does not resolve {pointer!r}")
    return current


def scalar(document: object, pointer: object, name: str) -> object:
    value = resolve_pointer(document, pointer)
    if value is None or isinstance(value, (dict, list)):
        raise ValueError(f"{name} must resolve to one scalar")
    return value


def normalise_file(value: object, root: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("file must resolve to a non-empty string")
    root = root.resolve()
    candidate = Path(value)
    candidate = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError as error:
        raise ValueError(f"file {value!r} is outside the repository root") from error


def validate_mapping(mapping: object) -> dict:
    if not isinstance(mapping, dict):
        raise ValueError("differential checks require a mapping object")
    missing = [field for field in MAPPING_FIELDS if field not in mapping]
    if missing:
        raise ValueError(f"mapping is missing {', '.join(missing)}")
    for field in MAPPING_FIELDS:
        pointer_parts(mapping[field])
    return mapping


def parse_findings(output: str, mapping: dict, root: Path, source: str) -> list[dict]:
    try:
        document = json.loads(output)
    except json.JSONDecodeError as error:
        raise ValueError(f"{source} command did not emit JSON: {error.msg}") from error
    findings = resolve_pointer(document, mapping["findings"])
    if not isinstance(findings, list):
        raise ValueError("findings must resolve to an array")
    parsed: list[dict] = []
    for index, finding in enumerate(findings):
        values = {field: scalar(finding, mapping[field], field) for field in MAPPING_FIELDS[1:]}
        if not isinstance(values["rule"], str) or not values["rule"]:
            raise ValueError(f"finding {index} rule must be a non-empty string")
        if not isinstance(values["message"], str) or not values["message"]:
            raise ValueError(f"finding {index} message must be a non-empty string")
        if values["severity"] not in SEVERITY_ORDER:
            raise ValueError(f"finding {index} severity must be info, warning or error")
        parsed.append(
            {
                "rule": values["rule"],
                "file": normalise_file(values["file"], root),
                "line": values["line"],
                "message": values["message"],
                "severity": values["severity"],
            }
        )
    return parsed


def index_findings(findings: list[dict], source: str) -> tuple[dict[tuple[str, str, str], dict], list[dict]]:
    indexed: dict[tuple[str, str, str], dict] = {}
    invalid: list[dict] = []
    for finding in findings:
        identity = (finding["rule"], finding["file"], finding["message"])
        if identity in indexed:
            invalid.append(
                {
                    "source": source,
                    "identity": {"rule": identity[0], "file": identity[1], "message": identity[2]},
                }
            )
        else:
            indexed[identity] = finding
    return indexed, invalid


def differential_gate(gate: dict, cwd: Path, diff_base: str | None, timeout: int) -> dict:
    gate = dict(gate)
    gate.update({"new": [], "aggravated": [], "resolved": [], "preexisting": [], "invalid": []})
    try:
        mapping = validate_mapping(gate.get("mapping"))
    except ValueError as error:
        gate["invalid"].append({"source": "config", "error": str(error)})
        gate["status"] = "fail"
        return gate
    if not diff_base:
        gate["invalid"].append({"source": "config", "error": "differential checks require --diff-base"})
        gate["status"] = "fail"
        return gate

    base_root = Path(tempfile.mkdtemp(prefix="gantry-gates-"))
    try:
        code, output = sh(["git", "worktree", "add", "--detach", "--quiet", str(base_root), diff_base], cwd, timeout)
        if code:
            gate["invalid"].append({"source": "base", "error": f"could not create base worktree: {output.strip()}"})
            gate["status"] = "fail"
            return gate
        base_code, base_output = sh(gate["command"], base_root, timeout)
        delivery_code, delivery_output = sh(gate["command"], cwd, timeout)
        gate["base_exit_code"] = base_code
        gate["delivery_exit_code"] = delivery_code
        try:
            base_findings = parse_findings(base_output, mapping, base_root, "base")
        except ValueError as error:
            gate["invalid"].append({"source": "base", "error": str(error)})
            gate["status"] = "fail"
            return gate
        try:
            delivery_findings = parse_findings(delivery_output, mapping, cwd, "delivery")
        except ValueError as error:
            gate["invalid"].append({"source": "delivery", "error": str(error)})
            gate["status"] = "fail"
            return gate

        base_index, base_invalid = index_findings(base_findings, "base")
        delivery_index, delivery_invalid = index_findings(delivery_findings, "delivery")
        gate["invalid"].extend(base_invalid + delivery_invalid)
        if gate["invalid"]:
            gate["status"] = "fail"
            return gate
        for identity in sorted(base_index.keys() | delivery_index.keys()):
            base_finding = base_index.get(identity)
            delivery_finding = delivery_index.get(identity)
            if base_finding is None:
                gate["new"].append(delivery_finding)
            elif delivery_finding is None:
                gate["resolved"].append(base_finding)
            elif SEVERITY_ORDER[delivery_finding["severity"]] > SEVERITY_ORDER[base_finding["severity"]]:
                gate["aggravated"].append(delivery_finding)
            else:
                gate["preexisting"].append(delivery_finding)
        gate["status"] = "fail" if gate["new"] or gate["aggravated"] else "pass"
        return gate
    finally:
        sh(["git", "worktree", "remove", "--force", str(base_root)], cwd, timeout)
        shutil.rmtree(base_root, ignore_errors=True)


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


def declared_or_detected(cwd: Path) -> dict:
    policy = resolve_policy(cwd)
    checks = policy.get("checks", [])
    if not checks:
        return detect(cwd)
    if not isinstance(checks, list):
        return {"gates": [{"name": "policy", "invalid": [{"source": "config", "error": "checks must be a list"}]}],
                "ci": [], "hooks": [], "notes": []}
    gates: list[dict] = []
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            gates.append({"name": f"check-{index + 1}", "invalid": [{"source": "config", "error": "check must be an object"}]})
            continue
        gate = dict(check)
        gate["source"] = ".gantry/config.json"
        if not isinstance(gate.get("name"), str) or not gate["name"]:
            gate["name"] = f"check-{index + 1}"
            gate["invalid"] = [{"source": "config", "error": "check name must be a non-empty string"}]
        elif not isinstance(gate.get("command"), str) or not gate["command"]:
            gate["invalid"] = [{"source": "config", "error": "check command must be a non-empty string"}]
        elif gate.get("mode") not in {"absolute", "differential"}:
            gate["invalid"] = [{"source": "config", "error": "check mode must be absolute or differential"}]
        gates.append(gate)
    return {"gates": gates, "ci": [], "hooks": [], "notes": []}


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
    try:
        result = declared_or_detected(cwd)
    except ValueError as error:
        result = {"gates": [{"name": "policy", "invalid": [{"source": "config", "error": str(error)}]}],
                  "ci": [], "hooks": [], "notes": []}
    result.update({"cwd": str(cwd), "git": git_facts(cwd, args.diff_base)})
    only = {item.strip() for item in args.only.split(",")} if args.only else None
    failures = 0
    for index, gate in enumerate(result["gates"]):
        if only and gate["name"] not in only:
            gate["status"] = "skipped"
        elif not args.run:
            gate["status"] = "not_run"
        elif gate.get("invalid"):
            gate["status"] = "fail"
            failures += 1
        elif gate.get("mode") == "differential":
            gate = differential_gate(gate, cwd, args.diff_base, args.timeout)
            result["gates"][index] = gate
            failures += gate["status"] == "fail"
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
