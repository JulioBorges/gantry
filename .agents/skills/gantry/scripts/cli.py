#!/usr/bin/env python3
"""Read the Gantry board, execute one Run, or approve it by opening a pull request."""
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


def invoke_role(
    command: Path, worktree: Path, role: str, diff_base: str, diff: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GANTRY_ROLE"] = role
    env["GANTRY_DIFF_BASE"] = diff_base
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(command), "--role", role, "--diff-base", diff_base],
        cwd=worktree, text=True, capture_output=True, check=False,
        input=None if role in {"implement", "plan"} else diff, env=env,
    )


def verdict_passed(completed: subprocess.CompletedProcess[str]) -> bool:
    if completed.returncode != 0:
        return False
    try:
        body = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False
    return isinstance(body, dict) and body.get("verdict") == "pass"


def pause(payload: dict[str, object]) -> str:
    emit(payload)
    return sys.stdin.readline().strip().lower()


def correction_budget(policy: dict) -> int:
    raw = policy.get("budget", {}).get("corrections", 2)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        return 2
    return raw


def render_branch(policy: dict, spec: str, number: int) -> str:
    return policy["git"]["issueBranch"].format(
        prefix=policy["git"]["prefix"], spec=spec, number=number,
    )


def worktree_path(root: Path, branch: str) -> Path:
    return root / ".gantry" / "worktrees" / branch.replace("/", "-")


def primary_checkout(root: Path) -> Path:
    completed = git(root, "rev-parse", "--git-common-dir")
    if completed.returncode != 0:
        return root
    path = Path(completed.stdout.strip())
    if not path.is_absolute():
        path = (root / path).resolve()
    if path.name == ".git":
        return path.parent
    if path.parent.name == "worktrees" and path.parent.parent.name == ".git":
        return path.parent.parent.parent
    return root


def tree_dirty(worktree: Path) -> bool:
    return bool(git(worktree, "status", "--porcelain").stdout.strip())


def create_worktree(root: Path, branch: str, target: str) -> Path | None:
    worktree = worktree_path(root, branch)
    if git(root, "rev-parse", "--verify", "--quiet", branch).returncode == 0 or worktree.exists():
        return None
    if git(root, "branch", branch, target).returncode != 0:
        return None
    worktree.parent.mkdir(parents=True, exist_ok=True)
    added = git(root, "worktree", "add", "--quiet", str(worktree), branch)
    if added.returncode != 0:
        git(root, "branch", "-D", branch)
        if worktree.exists():
            git(root, "worktree", "remove", "--force", str(worktree))
        return None
    return worktree


def discard_worktree(root: Path, worktree: Path, branch: str) -> None:
    git(root, "worktree", "remove", "--force", str(worktree))
    git(root, "branch", "-D", branch)


def implement_failed(worktree: Path, target: str, completed: subprocess.CompletedProcess[str]) -> bool:
    ahead = git(worktree, "rev-list", "--count", f"{target}..HEAD")
    return completed.returncode != 0 or tree_dirty(worktree) or ahead.returncode != 0 or ahead.stdout.strip() in {"", "0"}


def deliver(worktree: Path, branch: str, target: str, policy: dict, commands: dict[str, Path]) -> int:
    granted = correction_budget(policy)
    spent = 0
    first = True
    while True:
        if not first and spent >= granted:
            answer = pause({
                "event": "pause", "reason": "corrections-exhausted", "choices": ["continue", "stop"],
                "branch": branch, "worktree": str(worktree), "pushed": False,
            })
            if answer != "continue":
                emit({"event": "stopped", "branch": branch, "worktree": str(worktree), "pushed": False})
                return 1
            granted += 1
        first = False
        implement = invoke_role(commands["implement"], worktree, "implement", target, "")
        if implement_failed(worktree, target, implement):
            spent += 1
            continue
        if not run_checks(worktree, policy):
            spent += 1
            continue
        diff = git(worktree, "diff", f"{target}...HEAD").stdout
        review = invoke_role(commands["review"], worktree, "review", target, diff)
        if not verdict_passed(review):
            spent += 1
            continue
        critic = invoke_role(commands["critic"], worktree, "critic", target, diff)
        if not verdict_passed(critic):
            spent += 1
            continue
        emit({"event": "ready-for-approval", "branch": branch, "worktree": str(worktree), "pushed": False})
        return 0


def execution_context(root: Path) -> tuple[dict, str] | int:
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
    target = policy["git"]["target"]
    if git(root, "rev-parse", "--verify", "--quiet", target).returncode != 0:
        return setup_error("target-missing")
    return policy, target


def require_commands(root: Path, policy: dict, roles: tuple[str, ...]) -> dict[str, Path] | int:
    commands = {role: role_command(root, policy, role) for role in roles}
    if any(path is None for path in commands.values()):
        return setup_error("role-command-missing")
    return commands  # type: ignore[return-value]


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
    return deliver(worktree, branch, target, policy, commands)


def next_issue_number(root: Path, policy: dict, slug: str) -> int:
    directory = root / policy["artifacts"]["issues"].format(slug=slug)
    numbers = [
        int(match.group(1))
        for path in directory.glob("*.md")
        if directory.is_dir() and (match := re.match(r"^(\d{2,})-", path.name))
    ]
    return max(numbers, default=0) + 1


def execute_plan(root: Path, slug: str) -> int:
    prepared = execution_context(root)
    if isinstance(prepared, int):
        return prepared
    policy, target = prepared
    spec = artifact_path(root, "specs", slug)
    issue_dir = root / policy["artifacts"]["issues"].format(slug=slug)
    if spec.is_file() or any(issue_dir.glob("*.md")):
        return setup_error("spec-or-issue-exists")
    commands = require_commands(root, policy, ("plan", "implement", "review", "critic"))
    if isinstance(commands, int):
        return commands
    number = next_issue_number(root, policy, slug)
    branch = render_branch(policy, slug, number)
    if git(root, "rev-parse", "--verify", "--quiet", branch).returncode == 0 or worktree_path(root, branch).exists():
        return setup_error("branch-exists")
    worktree = create_worktree(root, branch, target)
    if worktree is None:
        return setup_error("worktree-create-failed")
    emit({"event": "worktree", "branch": branch, "worktree": str(worktree), "pushed": False})
    spec_path = policy["artifacts"]["specs"].format(slug=slug)
    issue_path = policy["artifacts"]["issues"].format(slug=slug).rstrip("/") + f"/{number:02d}-{slug}.md"
    plan_env = {
        "GANTRY_SLUG": slug,
        "GANTRY_ISSUE_NUMBER": f"{number:02d}",
        "GANTRY_SPEC_PATH": spec_path,
        "GANTRY_ISSUE_PATH": issue_path,
    }

    def call_plan() -> subprocess.CompletedProcess[str]:
        return invoke_role(commands["plan"], worktree, "plan", target, "", plan_env)

    def plan_ready(completed: subprocess.CompletedProcess[str]) -> bool:
        return completed.returncode == 0 and not tree_dirty(worktree)

    completed = call_plan()
    if not plan_ready(completed):
        completed = call_plan()
    while not plan_ready(completed):
        answer = pause({
            "event": "pause", "reason": "plan-dirty", "choices": ["try-again", "reject"],
            "branch": branch, "worktree": str(worktree), "pushed": False,
        })
        if answer != "try-again":
            discard_worktree(root, worktree, branch)
            emit({"event": "rejected", "branch": branch, "pushed": False})
            return 1
        completed = call_plan()
    answer = pause({
        "event": "pause", "reason": "plan-approval", "choices": ["approve", "reject"],
        "branch": branch, "worktree": str(worktree), "pushed": False,
    })
    if answer != "approve":
        discard_worktree(root, worktree, branch)
        emit({"event": "rejected", "branch": branch, "pushed": False})
        return 1
    return deliver(worktree, branch, target, policy, commands)


def issue_status(path: Path) -> str:
    match = re.search(r"^Status:\s*(.+?)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else ""


def approve_issue(root: Path, ref: str) -> int:
    checkout = primary_checkout(root)
    if not (checkout / ".git").exists():
        return setup_error("not-a-repository")
    if not (checkout / ".agents" / "skills" / "gantry").is_dir():
        emit({"error": {"code": "pack-unreadable", "repository": str(checkout)}})
        return 2
    try:
        policy = resolve_policy(checkout)
    except ValueError as error:
        return setup_error(f"policy-invalid: {error}")
    key = normalise_ref(ref) if ref else None
    if key is None:
        return setup_error("issue-missing")
    spec, number_text = key.split("#")
    branch = render_branch(policy, spec, int(number_text))
    worktree = worktree_path(checkout, branch)
    if not worktree.exists():
        return setup_error("worktree-missing")
    if tree_dirty(worktree):
        return setup_error("worktree-dirty")
    issues = load_policy_issues(worktree, policy)
    issue = issues.get(key)
    if issue is None:
        return setup_error("issue-missing")
    target = policy["git"]["target"]
    before = git(worktree, "rev-parse", "HEAD").stdout.strip()
    created = False
    if issue.status != "done":
        roadmap = Path(__file__).resolve().parent / "roadmap.py"
        closed = subprocess.run(
            [sys.executable, str(roadmap), "done", key],
            cwd=worktree, text=True, capture_output=True, check=False,
        )
        if closed.returncode != 0:
            return setup_error("close-failed")
        relative = issue.path.relative_to(worktree).as_posix()
        if git(worktree, "add", "--", "ROADMAP.md", relative).returncode != 0:
            return setup_error("close-failed")
        if git(worktree, "commit", "-qm", f"gantry: close {key}").returncode != 0:
            return setup_error("close-failed")
        created = git(worktree, "rev-parse", "HEAD").stdout.strip() != before
    if "origin" not in git(worktree, "remote").stdout.split():
        return setup_error("remote-missing")
    pushed = git(worktree, "push", "-u", "origin", f"HEAD:refs/heads/{branch}")
    if pushed.returncode != 0:
        return setup_error("push-failed")
    title = issue.title
    body = f"Close {key}.\n\nThe closing commit marks the Issue and the roadmap done.\n"
    pull = subprocess.run(
        ["gh", "pr", "create", "--base", target, "--head", branch, "--title", title, "--body", body],
        cwd=worktree, text=True, capture_output=True, check=False,
    )
    if pull.returncode != 0:
        return setup_error("pull-request-failed")
    emit({
        "event": "pull-request", "branch": branch, "target": target, "worktree": str(worktree),
        "pushed": True, "createdCommit": created, "url": pull.stdout.strip(),
    })
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="repository to inspect")
    parser.add_argument("command", choices=("board", "issues", "specs", "frontier", "execute", "approve"), nargs="?", default="board")
    parser.add_argument("issue", nargs="?")
    args = parser.parse_args(argv)
    root = repo_root(Path(args.cwd))
    if args.command == "execute":
        if not args.issue:
            return setup_error("issue-missing")
        if "#" not in args.issue:
            return execute_plan(root, args.issue)
        return execute_issue(root, args.issue)
    if args.command == "approve":
        if not args.issue:
            return setup_error("issue-missing")
        return approve_issue(root, args.issue)
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
