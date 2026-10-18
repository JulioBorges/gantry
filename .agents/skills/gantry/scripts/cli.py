#!/usr/bin/env python3
"""Read the Gantry board without creating a Run or mutating a repository."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import load_policy_issues, repo_root, resolve_policy


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="repository to inspect")
    parser.add_argument("command", choices=("board", "issues", "specs", "frontier"), nargs="?", default="board")
    args = parser.parse_args(argv)
    root = repo_root(Path(args.cwd))
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
