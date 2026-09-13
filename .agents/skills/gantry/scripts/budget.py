#!/usr/bin/env python3
"""Estimate an Issue's initial context package against a declared model window."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import artifact_path, parse_issue, repo_root, resolve_policy, section

FILES_TO_READ_HEADING_RE = re.compile(r"^###\s+Files to read\s*$", re.MULTILINE)
LISTED_FILE_RE = re.compile(r"^\s*-\s+`([^`\r\n]+)`\s*$")


class ConfigurationError(ValueError):
    """A policy, capability, or model declaration cannot be used safely."""


def relative_file(root: Path, value: str) -> Path | None:
    """Resolve an explicitly named repository-relative regular file."""
    candidate = Path(value.strip())
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        return None
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if path.is_file() else None


def explicitly_listed_files(issue_path: Path, root: Path) -> list[Path]:
    """Return files listed exactly under ``### Files to read`` in What to build."""
    text = issue_path.read_text(encoding="utf-8")
    what_to_build = section(text, "What to build")
    heading = FILES_TO_READ_HEADING_RE.search(what_to_build)
    if heading is None:
        return []
    listing = what_to_build[heading.end():]
    next_heading = re.search(r"^#{1,3}\s+", listing, re.MULTILINE)
    if next_heading:
        listing = listing[:next_heading.start()]
    paths: dict[Path, None] = {}
    for line in listing.splitlines():
        match = LISTED_FILE_RE.fullmatch(line)
        path = relative_file(root, match.group(1)) if match else None
        if path is not None:
            paths[path] = None
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def declared_models(capabilities_dir: Path) -> dict[str, tuple[str, int]]:
    """Return model IDs and windows from the shipped capability declarations."""
    models: dict[str, tuple[str, int]] = {}
    for path in sorted(capabilities_dir.glob("*.json")):
        try:
            capability = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"{path} is not valid JSON: {exc}") from exc
        declared = capability.get("models")
        if not isinstance(declared, dict):
            raise ConfigurationError(f"{path} must declare a models object")
        for model, details in declared.items():
            window = details.get("contextWindow") if isinstance(details, dict) else None
            if not isinstance(model, str) or not isinstance(window, int) or isinstance(window, bool) or window <= 0:
                raise ConfigurationError(f"{path} has an invalid contextWindow for {model!r}")
            if set(details) != {"contextWindow"}:
                raise ConfigurationError(f"{path} must map {model!r} only to contextWindow")
            if model in models:
                raise ConfigurationError(f"model {model!r} is declared by more than one capability")
            models[model] = (path.stem, window)
    if not models:
        raise ConfigurationError(f"no capability declarations found in {capabilities_dir}")
    return models


def estimate(issue_path: Path, model: str, root: Path, capabilities_dir: Path) -> dict:
    """Build the deterministic initial-package estimate for one Issue."""
    issue = parse_issue(issue_path)
    spec_path = artifact_path(root, "specs", issue.spec).resolve()
    if not spec_path.is_file():
        raise ConfigurationError(f"parent Spec does not exist: {spec_path.relative_to(root)}")
    models = declared_models(capabilities_dir)
    if model not in models:
        raise ConfigurationError(f"unknown model ID: {model!r}")
    policy = resolve_policy(root)
    share = policy.get("budget", {}).get("contextShare")
    if not isinstance(share, (int, float)) or isinstance(share, bool) or not 0 < share <= 1:
        raise ConfigurationError("budget.contextShare must be a number greater than 0 and at most 1")

    paths: dict[Path, None] = {issue_path.resolve(): None, spec_path: None}
    for path in explicitly_listed_files(issue_path, root):
        paths[path] = None
    ordered = [issue_path.resolve(), spec_path]
    ordered.extend(sorted((path for path in paths if path not in {issue_path.resolve(), spec_path}),
                          key=lambda path: path.relative_to(root).as_posix()))
    files = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size}
        for path in ordered
    ]
    byte_count = sum(entry["bytes"] for entry in files)
    harness, window = models[model]
    estimated_tokens = byte_count / 4
    budget_tokens = window * share
    over_budget = estimated_tokens > budget_tokens
    return {
        "issue": issue.path.relative_to(root).as_posix(),
        "spec": spec_path.relative_to(root).as_posix(),
        "model": model,
        "harness": harness,
        "files": files,
        "bytes": byte_count,
        "estimatedTokens": estimated_tokens,
        "contextWindow": window,
        "contextShare": share,
        "budgetTokens": budget_tokens,
        "overBudget": over_budget,
        "verdict": "over_budget" if over_budget else "within_budget",
    }


def emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    if "error" in payload:
        print(f"configuration error: {payload['error']}")
        return
    print(f"estimated tokens: {payload['estimatedTokens']}")
    print(f"context window: {payload['contextWindow']}")
    print(f"context share: {payload['contextShare']}")
    print(f"budget tokens: {payload['budgetTokens']}")
    print(f"verdict: {payload['verdict']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", help="Issue path")
    parser.add_argument("--model", required=True, help="exact model ID declared by a capability")
    parser.add_argument("--cwd", default=".", help="repository or worktree to inspect")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    issue_path = Path(args.issue).resolve()
    root = repo_root(Path(args.cwd))
    if not issue_path.is_file():
        emit({"error": f"configuration error: Issue does not exist: {issue_path}"}, args.json)
        return 1
    capabilities = Path(__file__).resolve().parents[1] / "capabilities"
    try:
        payload = estimate(issue_path, args.model, root, capabilities)
    except (ConfigurationError, ValueError) as exc:
        emit({"error": f"configuration error: {exc}"}, args.json)
        return 1
    emit(payload, args.json)
    return 1 if payload["overBudget"] else 0


if __name__ == "__main__":
    sys.exit(main())
