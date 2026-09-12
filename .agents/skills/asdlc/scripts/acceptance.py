#!/usr/bin/env python3
"""Extract or verify the acceptance criteria of one issue.

  acceptance.py <spec#NN | path/to/issue.md>            print criteria, status, blockers (add --json for JSON)
  acceptance.py <ref> --check                           exit 1 unless Status is done AND every criterion is ticked
  acceptance.py <ref> --tick 1,3 / --untick 2           flip specific criteria (1-based) in the issue file
  acceptance.py <ref> --tick all                        tick every criterion (used by roadmap.py done)

The JSON form is what the adversarial critic is handed, so the critic verifies the *file's* criteria
rather than the implementer's paraphrase of them.
"""
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
    for c in issue.criteria:
        if indexes is not None and c.index not in indexes:
            continue
        line = lines[c.line_no - 1]
        new = line.replace("- [ ]", "- [x]", 1) if checked else line.replace("- [x]", "- [ ]", 1).replace("- [X]", "- [ ]", 1)
        if new != line:
            lines[c.line_no - 1] = new
            changed += 1
    if changed:
        path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issue", help="`spec#NN` or a path to the issue file")
    ap.add_argument("--scratch", default=".scratch")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 1 unless done and fully ticked")
    ap.add_argument("--tick", help="comma-separated 1-based indexes, or 'all'")
    ap.add_argument("--untick", help="comma-separated 1-based indexes, or 'all'")
    args = ap.parse_args()

    root = repo_root()
    issues = load_issues(root / args.scratch)
    issue = resolve_issue_arg(args.issue, root, issues)
    if not issue:
        print(f"issue not found: {args.issue}", file=sys.stderr)
        return 2

    for flag, checked in ((args.tick, True), (args.untick, False)):
        if flag:
            idx = None if flag == "all" else [int(x) for x in flag.split(",") if x.strip()]
            n = flip(issue.path, idx, checked)
            print(f"{'ticked' if checked else 'unticked'} {n} criteria in {issue.path.relative_to(root)}")
            issue = parse_issue(issue.path)

    text = issue.path.read_text(encoding="utf-8")
    payload = {
        **issue.to_dict(root),
        "spec_path": str((issue.path.parent.parent / "spec.md").relative_to(root)),
        "criteria": [{"index": c.index, "text": c.text, "checked": c.checked} for c in issue.criteria],
        "what_to_build": section(text, "What to build").strip(),
        "notes": section(text, "Notes").strip(),
    }
    all_ticked = bool(issue.criteria) and all(c.checked for c in issue.criteria)
    payload["complete"] = issue.done and all_ticked

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{issue.ref}  {issue.title}")
        print(f"  status: {issue.status}   blocked by: {', '.join(issue.blocked_by) or 'none'}")
        for c in issue.criteria:
            print(f"  [{'x' if c.checked else ' '}] {c.index}. {c.text}")
        if not issue.criteria:
            print("  (no acceptance criteria found — this issue is not implementable as-is)")

    if args.check:
        if not payload["complete"]:
            print(f"NOT COMPLETE: status={issue.status}, ticked={payload['criteria_checked']}/{payload['criteria_total']}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
