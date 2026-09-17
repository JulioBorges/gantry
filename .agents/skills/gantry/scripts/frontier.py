#!/usr/bin/env python3
"""Compute ready Issue rounds from authoritative Markdown execution state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import Issue, load_issues, load_policy_issues, normalise_ref, repo_root, roadmap_waves  # noqa: E402


def select_scope(scopes: list[str], issues: dict[str, Issue], roadmap: str) -> tuple[set[str], list[str]]:
    selected: set[str] = set()
    errors: list[str] = []
    waves = roadmap_waves(roadmap) if roadmap else {}
    specs = {issue.spec for issue in issues.values()}
    for raw in scopes:
        scope = raw.strip()
        if scope == "all":
            selected |= {ref for ref, issue in issues.items() if not issue.done}
        elif scope == "frontier":
            selected |= {
                ref for ref, issue in issues.items()
                if not issue.done and (
                    issue.parked
                    or not issue.blocked_by
                    or all(issues.get(blocker) and issues[blocker].done for blocker in issue.blocked_by)
                )
            }
        elif scope.startswith("wave:"):
            try:
                wave = int(scope.split(":", 1)[1])
            except ValueError:
                errors.append(f"bad wave scope: {raw}")
                continue
            if wave not in waves:
                errors.append(f"wave {wave} not found in ROADMAP.md")
            else:
                for ref in waves[wave]:
                    if ref in issues and not issues[ref].done:
                        selected.add(ref)
                    elif ref not in issues:
                        errors.append(f"ROADMAP.md wave {wave} lists {ref} but no issue file exists")
        elif normalise_ref(scope):
            ref = normalise_ref(scope)
            if ref in issues:
                selected.add(ref)
            else:
                errors.append(f"issue not found: {ref}")
        elif scope in specs:
            selected |= {ref for ref, issue in issues.items() if issue.spec == scope and not issue.done}
        else:
            errors.append(f"unknown scope: {raw} (not a spec slug, issue ref, wave:N, all or frontier)")
    return selected, errors


def find_cycles(nodes: set[str], issues: dict[str, Issue]) -> list[list[str]]:
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[list[str]] = []
    counter = 0

    def visit(ref: str) -> None:
        nonlocal counter
        index[ref] = low[ref] = counter
        counter += 1
        stack.append(ref)
        on_stack.add(ref)
        for blocker in (blocker for blocker in issues[ref].blocked_by if blocker in nodes):
            if blocker not in index:
                visit(blocker)
                low[ref] = min(low[ref], low[blocker])
            elif blocker in on_stack:
                low[ref] = min(low[ref], index[blocker])
        if low[ref] == index[ref]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == ref:
                    break
            if len(component) > 1 or ref in issues[ref].blocked_by:
                cycles.append(component)

    for ref in sorted(nodes):
        if ref not in index:
            visit(ref)
    return cycles


def validate_graph(issues: dict[str, Issue]) -> list[str]:
    """Return errors that make the authoritative Issue graph invalid."""
    errors = [
        f"{ref} is blocked by {blocker}, which does not exist"
        for ref in sorted(issues)
        for blocker in issues[ref].blocked_by
        if blocker not in issues
    ]
    for cycle in find_cycles(set(issues), issues):
        errors.append("dependency cycle: " + " -> ".join(cycle + [cycle[0]]))
    return errors


def schedule(selected: set[str], issues: dict[str, Issue], limit: int | None) -> tuple[list[list[str]], dict[str, list[str]], list[str]]:
    errors: list[str] = []
    external = {
        ref: [blocker for blocker in issues[ref].blocked_by if blocker in issues and blocker not in selected and not issues[blocker].done]
        for ref in selected
    }
    external = {ref: blockers for ref, blockers in external.items() if blockers}
    schedulable = selected - external.keys()
    changed = True
    while changed:
        changed = False
        for ref in list(schedulable):
            blocked = [blocker for blocker in issues[ref].blocked_by if blocker in external]
            if blocked:
                external[ref] = [f"{blocker} (transitively blocked)" for blocker in blocked]
                schedulable.remove(ref)
                changed = True
    done = {ref for ref, issue in issues.items() if issue.done}
    rounds: list[list[str]] = []
    placed: set[str] = set()
    remaining = set(schedulable)
    while remaining:
        ready = sorted(
            ref for ref in remaining
            if all(blocker in done or blocker in placed for blocker in issues[ref].blocked_by if blocker in issues)
        )
        if not ready:
            for cycle in find_cycles(remaining, issues):
                errors.append("dependency cycle: " + " -> ".join(cycle + [cycle[0]]))
            break
        if limit:
            ready = ready[:limit]
        rounds.append(ready)
        placed.update(ready)
        remaining.difference_update(ready)
    return rounds, external, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", action="append", default=[], help="scope selector (repeatable)")
    parser.add_argument("--scratch", help="legacy Issue root override")
    parser.add_argument("--roadmap", default="ROADMAP.md")
    parser.add_argument("--limit", type=int, default=None, help="maximum Issues per round")
    parser.add_argument("--include-parked", action="store_true", help="include blocked, needs-operator and draft Issues")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    issues = load_issues(root / args.scratch) if args.scratch else load_policy_issues(root)
    if not issues:
        location = root / args.scratch if args.scratch else "the effective artifacts.issues policy path"
        print(f"no issues found under {location}", file=sys.stderr)
        return 2
    roadmap_path = root / args.roadmap
    selected, errors = select_scope(args.scope or ["frontier"], issues, roadmap_path.read_text(encoding="utf-8") if roadmap_path.exists() else "")
    errors.extend(validate_graph(issues))
    parked = sorted(ref for ref in selected if issues[ref].parked)
    if not args.include_parked:
        selected.difference_update(parked)
    rounds, external, schedule_errors = schedule(selected, issues, args.limit)
    errors.extend(schedule_errors)
    result = {
        "scope": args.scope or ["frontier"], "selected": sorted(selected),
        "already_done": sorted(ref for ref in selected if issues[ref].done),
        "rounds": rounds, "externally_blocked": dict(sorted(external.items())),
        "parked": {ref: issues[ref].status for ref in parked},
        "issues": {ref: issues[ref].to_dict(root) for ref in sorted(selected)}, "errors": errors,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"scope: {' '.join(result['scope'])} -> {len(selected)} issue(s), {len(rounds)} round(s)")
        for number, members in enumerate(rounds, 1):
            print(f"  round {number}: {', '.join(members)}")
        for error in errors:
            print(f"  ERROR: {error}")
    if errors:
        return 1
    return 0 if selected or parked or all(i.done for i in issues.values()) else 2


if __name__ == "__main__":
    sys.exit(main())
