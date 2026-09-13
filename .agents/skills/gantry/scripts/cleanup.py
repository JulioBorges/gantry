#!/usr/bin/env python3
"""Print or execute an explicit cleanup plan for merged done Issue worktrees."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_policy_issues, repo_root, resolve_policy  # noqa: E402


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run Git in the repository and retain output for a caller-facing error."""
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def git_output(root: Path, *args: str) -> str:
    result = git(root, *args)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())
    return result.stdout


def current_branch(root: Path) -> str:
    branch = git_output(root, "branch", "--show-current").strip()
    if not branch:
        raise ValueError("cleanup requires a checked-out run branch; use --run-branch from a branch checkout")
    return branch


def worktrees(root: Path) -> dict[str, str]:
    """Map checked-out local branches to their registered worktree paths."""
    result: dict[str, str] = {}
    path: str | None = None
    for line in git_output(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line.removeprefix("worktree ")
        elif line.startswith("branch refs/heads/") and path:
            result[line.removeprefix("branch refs/heads/")] = path
        elif not line:
            path = None
    return result


def branch_exists(root: Path, branch: str) -> bool:
    return git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0


def merged_into_run(root: Path, branch: str, run_branch: str) -> bool:
    return git(root, "merge-base", "--is-ancestor", branch, run_branch).returncode == 0


def cleanup_plan(root: Path, run_branch: str) -> dict:
    """Plan cleanup only for done Issue branches merged into the run branch."""
    policy = resolve_policy(root)
    checked_out = worktrees(root)
    candidates: list[tuple[str, str]] = []
    for issue in load_policy_issues(root).values():
        branch = f"{policy['git']['prefix']}{issue.spec}-{issue.number:02d}"
        if issue.done and branch != run_branch and branch_exists(root, branch) and merged_into_run(root, branch, run_branch):
            candidates.append((issue.ref, branch))

    branches = [{"issue": ref, "name": branch} for ref, branch in sorted(candidates)]
    planned_worktrees = [
        {"issue": ref, "path": checked_out[branch], "branch": branch}
        for ref, branch in sorted(candidates)
        if branch in checked_out
    ]
    return {
        "run_branch": run_branch,
        "worktrees": planned_worktrees,
        "branches": branches,
    }


def execute_plan(root: Path, plan: dict) -> tuple[dict[str, list[str]], list[str]]:
    """Remove the exact worktrees then branches listed in a freshly-built plan."""
    removed = {"worktrees": [], "branches": []}
    errors: list[str] = []
    for item in plan["worktrees"]:
        result = git(root, "worktree", "remove", "--", item["path"])
        if result.returncode:
            errors.append(f"could not remove worktree {item['path']}: {(result.stderr or result.stdout).strip()}")
        else:
            removed["worktrees"].append(item["path"])
    if errors:
        return removed, errors
    for item in plan["branches"]:
        result = git(root, "branch", "-d", "--", item["name"])
        if result.returncode:
            errors.append(f"could not remove branch {item['name']}: {(result.stderr or result.stdout).strip()}")
        else:
            removed["branches"].append(item["name"])
    return removed, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--plan", action="store_true", help="print the read-only cleanup plan (default)")
    action.add_argument("--yes", action="store_true", help="remove exactly the worktrees and branches in the plan")
    parser.add_argument("--run-branch", help="run branch used to determine whether Issue branches are merged")
    parser.add_argument("--cwd", default=".", help="repository or worktree to inspect")
    parser.add_argument("--json", action="store_true", help="emit the cleanup plan as JSON")
    args = parser.parse_args()

    root = repo_root(Path(args.cwd))
    try:
        run_branch = args.run_branch or current_branch(root)
        plan = cleanup_plan(root, run_branch)
    except ValueError as error:
        payload = {"error": str(error)}
        print(json.dumps(payload, indent=2) if args.json else f"ERROR: {payload['error']}", file=sys.stderr)
        return 1

    if args.yes:
        removed, errors = execute_plan(root, plan)
        plan["removed"] = removed
        if errors:
            plan["errors"] = errors
    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        print(f"run branch: {plan['run_branch']}")
        for item in plan["worktrees"]:
            print(f"worktree: {item['path']} ({item['branch']}, {item['issue']})")
        for item in plan["branches"]:
            print(f"branch: {item['name']} ({item['issue']})")
        if not plan["worktrees"] and not plan["branches"]:
            print("nothing eligible for cleanup")
        if args.yes:
            for path in plan["removed"]["worktrees"]:
                print(f"removed worktree: {path}")
            for branch in plan["removed"]["branches"]:
                print(f"removed branch: {branch}")
        for error in plan.get("errors", []):
            print(f"ERROR: {error}", file=sys.stderr)
    if plan.get("errors"):
        return 1
    return 0 if plan["worktrees"] or plan["branches"] else 2


if __name__ == "__main__":
    sys.exit(main())
