#!/usr/bin/env python3
"""Compute the implementation frontier and execution rounds for a scope.

Deterministic replacement for "let the model decide what to do next". Reads every issue under
.scratch/*/issues/, resolves the blocker graph, and emits the ordered rounds in which the in-scope
issues can be implemented: round k contains the issues whose blockers are all either done or in an
earlier round. Issues blocked by out-of-scope, not-done work are reported separately and never
scheduled.

Scope forms (repeatable):
  all                every issue that is not done
  <spec-slug>        every issue of one spec (e.g. release-engineering)
  <spec-slug>#NN     one issue
  wave:N             every spec listed under `### Wave N` in ROADMAP.md
  frontier           only the issues that can start right now (unblocked, not done)

Examples:
  frontier.py --scope release-engineering --json
  frontier.py --scope wave:0 --limit 4
  frontier.py --scope execution-core#01 --scope data-handling#01

Exit codes: 0 ok, 1 graph error (cycle / dangling reference), 2 empty scope.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import Issue, load_issues, normalise_ref, repo_root, roadmap_waves  # noqa: E402


def select_scope(scopes: list[str], issues: dict[str, Issue], roadmap: str) -> tuple[set[str], list[str]]:
    selected: set[str] = set()
    errors: list[str] = []
    waves = roadmap_waves(roadmap) if roadmap else {}
    specs = {i.spec for i in issues.values()}
    for raw in scopes:
        s = raw.strip()
        if s == "all":
            selected |= {r for r, i in issues.items() if not i.done}
        elif s == "frontier":
            for r, i in issues.items():
                if i.done:
                    continue
                if all(issues.get(b) and issues[b].done for b in i.blocked_by) or not i.blocked_by:
                    selected.add(r)
        elif s.startswith("wave:"):
            try:
                n = int(s.split(":", 1)[1])
            except ValueError:
                errors.append(f"bad wave scope: {raw}")
                continue
            if n not in waves:
                errors.append(f"wave {n} not found in ROADMAP.md")
                continue
            for spec in waves[n]:
                selected |= {r for r, i in issues.items() if i.spec == spec and not i.done}
        elif normalise_ref(s):
            ref = normalise_ref(s)
            if ref in issues:
                selected.add(ref)
            else:
                errors.append(f"issue not found: {ref}")
        elif s in specs:
            selected |= {r for r, i in issues.items() if i.spec == s and not i.done}
        else:
            errors.append(f"unknown scope: {raw} (not a spec slug, issue ref, wave:N, all or frontier)")
    return selected, errors


def find_cycles(nodes: set[str], issues: dict[str, Issue]) -> list[list[str]]:
    """Tarjan SCC restricted to `nodes`; returns each non-trivial component as an ordered cycle."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    out: list[list[str]] = []
    counter = [0]

    def edges(n: str) -> list[str]:
        return [b for b in issues[n].blocked_by if b in nodes]

    def strong(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in edges(v):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in edges(v):
                out.append(order_cycle(comp, issues))

    for n in sorted(nodes):
        if n not in index:
            strong(n)
    return out


def order_cycle(comp: list[str], issues: dict[str, Issue]) -> list[str]:
    """Walk one closed path through the component so the report reads as a chain."""
    members = set(comp)
    start = sorted(comp)[0]
    path = [start]
    seen = {start}
    cur = start
    while True:
        nxt = [b for b in issues[cur].blocked_by if b in members]
        if not nxt:
            break
        cur = sorted(nxt)[0]
        if cur in seen:
            return path[path.index(cur):]
        path.append(cur)
        seen.add(cur)
    return path


def schedule(selected: set[str], issues: dict[str, Issue], limit: int | None) -> tuple[list[list[str]], dict[str, list[str]], list[str]]:
    errors: list[str] = []
    for ref in sorted(selected):
        for b in issues[ref].blocked_by:
            if b not in issues:
                errors.append(f"{ref} is blocked by {b}, which does not exist")

    def satisfied_externally(ref: str) -> list[str]:
        """Blockers that cannot be satisfied in this run: out of scope (or parked) and not done."""
        return [b for b in issues[ref].blocked_by if b in issues and b not in selected and not issues[b].done]

    external_block: dict[str, list[str]] = {}
    schedulable: set[str] = set()
    for ref in selected:
        ext = satisfied_externally(ref)
        if ext:
            external_block[ref] = ext
        else:
            schedulable.add(ref)

    # Propagate: anything blocked by an externally-blocked in-scope issue is also unschedulable.
    changed = True
    while changed:
        changed = False
        for ref in list(schedulable):
            bad = [b for b in issues[ref].blocked_by if b in external_block]
            if bad:
                external_block[ref] = [f"{b} (transitively blocked)" for b in bad]
                schedulable.discard(ref)
                changed = True

    done_set = {r for r, i in issues.items() if i.done}
    placed: set[str] = set()
    rounds: list[list[str]] = []
    remaining = set(schedulable)
    while remaining:
        ready = sorted(
            r for r in remaining
            if all((b in done_set) or (b in placed) for b in issues[r].blocked_by if b in issues)
        )
        if not ready:
            for cyc in find_cycles(remaining, issues):
                errors.append("dependency cycle: " + " -> ".join(cyc + [cyc[0]]))
            break
        if limit:
            ready = ready[:limit]
        rounds.append(ready)
        placed |= set(ready)
        remaining -= set(ready)
    return rounds, external_block, errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", action="append", default=[], help="scope selector (repeatable)")
    ap.add_argument("--scratch", default=".scratch")
    ap.add_argument("--roadmap", default="ROADMAP.md")
    ap.add_argument("--limit", type=int, default=None, help="max issues per round")
    ap.add_argument("--include-parked", action="store_true", help="schedule issues whose Status is blocked / needs-operator / draft")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    scratch = root / args.scratch
    roadmap_path = root / args.roadmap
    roadmap = roadmap_path.read_text(encoding="utf-8") if roadmap_path.exists() else ""
    issues = load_issues(scratch)
    if not issues:
        print(f"no issues found under {scratch}", file=sys.stderr)
        return 2

    scopes = args.scope or ["frontier"]
    selected, errors = select_scope(scopes, issues, roadmap)
    parked = sorted(r for r in selected if issues[r].parked)
    if not args.include_parked:
        selected -= set(parked)
    rounds, external, sched_errors = schedule(selected, issues, args.limit)
    errors += sched_errors

    result = {
        "scope": scopes,
        "selected": sorted(selected),
        "already_done": sorted(r for r in selected if issues[r].done),
        "rounds": rounds,
        "externally_blocked": {k: v for k, v in sorted(external.items())},
        "parked": {r: issues[r].status for r in parked},
        "issues": {r: issues[r].to_dict(root) for r in sorted(selected)},
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"scope: {' '.join(scopes)} -> {len(selected)} issue(s), {len(rounds)} round(s)")
        for k, r in enumerate(rounds, 1):
            print(f"  round {k}:")
            for ref in r:
                print(f"    {ref}  {issues[ref].title}")
        if parked and not args.include_parked:
            print("  parked (Status blocked / needs-operator / draft — not scheduled):")
            for ref in parked:
                print(f"    {ref}  [{issues[ref].status}]")
        if external:
            print("  externally blocked (not scheduled):")
            for ref, why in external.items():
                print(f"    {ref}  <- {', '.join(why)}")
        for e in errors:
            print(f"  ERROR: {e}")
    if errors:
        return 1
    if not selected:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
