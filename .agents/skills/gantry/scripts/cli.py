#!/usr/bin/env python3
"""Read the Gantry board, or execute one existing Issue, without pushing."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from common import artifact_path, issue_branch, load_policy_issues, normalise_ref, repo_root, resolve_policy


def specs(root: Path, policy: dict) -> list[dict[str, object]]:
    template = policy["artifacts"]["specs"]
    matcher = re.compile(
        "^" + re.escape(template).replace(re.escape("{slug}"), r"(?P<slug>[^/]+)") + "$"
    )
    entries: list[dict[str, object]] = []
    for path in sorted(root.glob(template.format(slug="*"))):
        match = matcher.match(path.relative_to(root).as_posix())
        if match and path.is_file():
            entries.append({
                "slug": match.group("slug"),
                "path": path.relative_to(root).as_posix(),
                "executable": False,
            })
    return entries


def board(root: Path) -> dict[str, object]:
    policy = resolve_policy(root)
    issues = load_policy_issues(root, policy)
    records = []
    frontier = []
    for issue in sorted(issues.values(), key=lambda entry: (entry.spec, entry.number)):
        open_blockers = [
            blocker for blocker in issue.blocked_by
            if blocker not in issues or not issues[blocker].done
        ]
        blocked = bool(open_blockers)
        if not issue.done and not issue.parked and not blocked:
            frontier.append(issue.ref)
        records.append({
            "ref": issue.ref,
            "spec": issue.spec,
            "number": issue.number,
            "title": issue.title,
            "status": issue.status,
            "path": issue.path.relative_to(root).as_posix(),
            "frontierBlocked": blocked,
            "openBlockers": open_blockers,
        })
    return {"issues": records, "specs": specs(root, policy), "frontier": frontier}


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True), flush=True)


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)


def role_command(root: Path, policy: dict, role: str) -> Path | None:
    configured = policy.get("execution", {}).get("roles", {}).get(role, {}).get("command")
    if not isinstance(configured, str) or not configured.strip():
        return None
    path = Path(configured)
    if not path.is_absolute():
        path = root / path
    if path.is_file() and os.access(path, os.X_OK):
        return path
    return None


def check_commands(policy: dict) -> str | None:
    checks = policy.get("checks") or []
    if not isinstance(checks, list):
        return "checks-invalid"
    for check in checks:
        command = check if isinstance(check, str) else check.get("command") if isinstance(check, dict) else None
        if not isinstance(command, str) or not command.strip():
            return "checks-invalid"
    return None


def setup_error(reason: str) -> int:
    emit({"error": {"code": "setup-invalid", "reason": reason}})
    return 2


def run_checks(worktree: Path, policy: dict) -> bool:
    for check in policy.get("checks") or []:
        command = check if isinstance(check, str) else check["command"]
        completed = subprocess.run(command, cwd=worktree, shell=True, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            return False
    return True


def invoke_role(command: Path, worktree: Path, role: str, diff_base: str, diff: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GANTRY_ROLE"] = role
    env["GANTRY_DIFF_BASE"] = diff_base
    return subprocess.run(
        [str(command), "--role", role, "--diff-base", diff_base],
        cwd=worktree, text=True, capture_output=True, check=False,
        input=None if role == "implement" else diff, env=env,
    )


def verdict_passed(completed: subprocess.CompletedProcess[str]) -> bool:
    if completed.returncode != 0:
        return False
    try:
        body = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False
    return isinstance(body, dict) and body.get("verdict") == "pass"


def execute_issue(root: Path, ref: str) -> int:
    if not (root / ".git").exists():
        return setup_error("not-a-repository")
    if not (root / ".agents" / "skills" / "gantry").is_dir():
        emit({"error": {"code": "pack-unreadable", "repository": str(root)}})
        return 2
    try:
        policy = resolve_policy(root)
    except ValueError as error:
        return setup_error(f"policy-invalid: {error}")
    if check_commands(policy):
        return setup_error("checks-invalid")
    key = normalise_ref(ref) if ref else None
    issues = load_policy_issues(root, policy)
    issue = issues.get(key) if key else None
    if issue is None:
        return setup_error("issue-missing")
    spec = artifact_path(root, "specs", issue.spec)
    if not spec.is_file():
        return setup_error("spec-missing")
    commands = {role: role_command(root, policy, role) for role in ("implement", "review", "critic")}
    if any(path is None for path in commands.values()):
        return setup_error("role-command-missing")
    target = policy["git"]["target"]
    if git(root, "rev-parse", "--verify", "--quiet", target).returncode != 0:
        return setup_error("target-missing")
    branch = issue_branch(policy, issue)
    worktree = root / ".gantry" / "worktrees" / branch.replace("/", "-")
    if git(root, "rev-parse", "--verify", "--quiet", branch).returncode == 0 or worktree.exists():
        return setup_error("branch-exists")
    open_blockers = [blocker for blocker in issue.blocked_by if blocker not in issues or not issues[blocker].done]
    if open_blockers:
        emit({"error": {"code": "open-blocker", "openBlockers": open_blockers}})
        return 1
    if git(root, "branch", branch, target).returncode != 0:
        return setup_error("branch-create-failed")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    added = git(root, "worktree", "add", "--quiet", str(worktree), branch)
    if added.returncode != 0:
        git(root, "branch", "-D", branch)
        if worktree.exists():
            git(root, "worktree", "remove", "--force", str(worktree))
        return setup_error("worktree-create-failed")
    emit({"event": "worktree", "branch": branch, "worktree": str(worktree), "pushed": False})
    implement = invoke_role(commands["implement"], worktree, "implement", target, "")
    status = git(worktree, "status", "--porcelain")
    ahead = git(worktree, "rev-list", "--count", f"{target}..HEAD")
    if implement.returncode != 0 or status.stdout.strip() or ahead.returncode != 0 or ahead.stdout.strip() in {"", "0"}:
        emit({"error": {"code": "implement-failed", "pushed": False}})
        return 1
    if not run_checks(worktree, policy):
        emit({"error": {"code": "check-failed", "pushed": False}})
        return 1
    diff = git(worktree, "diff", f"{target}...HEAD").stdout
    review = invoke_role(commands["review"], worktree, "review", target, diff)
    if not verdict_passed(review):
        emit({"error": {"code": "review-failed", "pushed": False}})
        return 1
    critic = invoke_role(commands["critic"], worktree, "critic", target, diff)
    if not verdict_passed(critic):
        emit({"error": {"code": "critic-failed", "pushed": False}})
        return 1
    emit({"event": "ready-for-approval", "branch": branch, "worktree": str(worktree), "pushed": False})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="repository to inspect")
    parser.add_argument("command", choices=("board", "issues", "specs", "frontier", "execute"), nargs="?", default="board")
    parser.add_argument("issue", nargs="?")
    args = parser.parse_args(argv)
    root = repo_root(Path(args.cwd))
    if args.command == "execute":
        if not args.issue:
            return setup_error("issue-missing")
        return execute_issue(root, args.issue)
    pack = root / ".agents" / "skills" / "gantry"
    if not pack.is_dir():
        print(json.dumps({"error": {"code": "pack-unreadable", "repository": str(root)}}))
        return 2
    result = board(root)
    if args.command == "issues":
        result = {"issues": result["issues"]}
    elif args.command == "specs":
        result = {"specs": result["specs"]}
    elif args.command == "frontier":
        result = {"frontier": result["frontier"]}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
