#!/usr/bin/env python3
"""Extract or verify the acceptance criteria of one Issue."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_issues, parse_issue, repo_root, resolve_issue_arg, section  # noqa: E402


def flip(path: Path, indexes: list[int] | None, checked: bool) -> int:
    issue = parse_issue(path)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = 0
    for criterion in issue.criteria:
        if indexes is not None and criterion.index not in indexes:
            continue
        old = lines[criterion.line_no - 1]
        new = old.replace("- [ ]", "- [x]", 1) if checked else old.replace("- [x]", "- [ ]", 1).replace("- [X]", "- [ ]", 1)
        if new != old:
            lines[criterion.line_no - 1] = new
            changed += 1
    if changed:
        path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", help="spec#NN or an Issue path")
    parser.add_argument("--scratch", default=".scratch")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="require done Status and every criterion ticked")
    parser.add_argument("--tick", help="comma-separated indexes or all")
    parser.add_argument("--untick", help="comma-separated indexes or all")
    args = parser.parse_args()
    root = repo_root()
    issue = resolve_issue_arg(args.issue, root, load_issues(root / args.scratch))
    if not issue:
        print(f"issue not found: {args.issue}", file=sys.stderr)
        return 2
    for values, checked in ((args.tick, True), (args.untick, False)):
        if values:
            indexes = None if values == "all" else [int(value) for value in values.split(",") if value.strip()]
            print(f"{'ticked' if checked else 'unticked'} {flip(issue.path, indexes, checked)} criteria in {issue.path.relative_to(root)}")
            issue = parse_issue(issue.path)
    text = issue.path.read_text(encoding="utf-8")
    payload = {
        **issue.to_dict(root),
        "spec_path": str((issue.path.parent.parent / "spec.md").relative_to(root)),
        "criteria": [{"index": item.index, "text": item.text, "checked": item.checked} for item in issue.criteria],
        "what_to_build": section(text, "What to build").strip(),
        "notes": section(text, "Notes").strip(),
    }
    payload["complete"] = issue.done and bool(issue.criteria) and all(item.checked for item in issue.criteria)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{issue.ref}  {issue.title}")
        print(f"  status: {issue.status}   blocked by: {', '.join(issue.blocked_by) or 'none'}")
        for item in issue.criteria:
            print(f"  [{'x' if item.checked else ' '}] {item.index}. {item.text}")
    if args.check and not payload["complete"]:
        print(f"NOT COMPLETE: status={issue.status}, ticked={payload['criteria_checked']}/{payload['criteria_total']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
