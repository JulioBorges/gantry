#!/usr/bin/env python3
"""Keep ROADMAP.md and the issue files in step — deterministically.

AGENTS.md requires three edits whenever an issue is completed, and forbids ticking the roadmap for an
issue whose criteria are not all met. This script does all three edits in one pass and refuses the
unsafe ones.

  roadmap.py check [--json]                 report drift: roadmap ticks vs issue Status, wrong done/total
                                            counts, stale Progress table. Exit 1 on drift.
  roadmap.py done <spec#NN> [--dry-run]     tick every acceptance criterion, set `Status: done`, tick the
                                            roadmap checkbox, bump the spec's done/total, refresh Progress.
  roadmap.py status <spec#NN> <value>       set only the issue's Status line (e.g. in-progress, blocked,
                                            ready-for-agent). Never touches the roadmap.
  roadmap.py comment <spec#NN> "<text>"     append a dated line under `## Comments` in the issue.

`done` is only ever called after the adversarial critic returned complete=true. It is the single place
that flips the roadmap, so a green checkbox always has a verdict behind it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import Issue, load_issues, repo_root, resolve_issue_arg  # noqa: E402

ITEM_RE = re.compile(r"^(- \[)( |x|X)(\] \*\*`)([a-z0-9-]+#\d+)(`\*\*.*)$")
SPEC_HEADING_RE = re.compile(r"^(#### \d+ `)([a-z0-9-]+)(` — )(\d+)/(\d+)\s*$")
PROGRESS_ISSUES_RE = re.compile(r"^(\| Issues completed \| \*\*)(\d+) / (\d+)(\*\* \|)\s*$")
PROGRESS_SPECS_RE = re.compile(r"^(\| Specs completed \| \*\*)(\d+) / (\d+)(\*\* \|)\s*$")
STATUS_LINE_RE = re.compile(r"^Status:\s*.*$", re.MULTILINE)


def counts(issues: dict[str, Issue]) -> tuple[int, int, int, int]:
    specs: dict[str, list[Issue]] = {}
    for i in issues.values():
        specs.setdefault(i.spec, []).append(i)
    done_issues = sum(1 for i in issues.values() if i.done)
    done_specs = sum(1 for lst in specs.values() if lst and all(i.done for i in lst))
    return done_issues, len(issues), done_specs, len(specs)


def render_roadmap(text: str, issues: dict[str, Issue]) -> tuple[str, list[str]]:
    """Return the roadmap re-rendered from the issues' Status lines, plus the list of changes."""
    changes: list[str] = []
    out: list[str] = []
    per_spec_done = {}
    per_spec_total = {}
    for i in issues.values():
        per_spec_total[i.spec] = per_spec_total.get(i.spec, 0) + 1
        per_spec_done[i.spec] = per_spec_done.get(i.spec, 0) + (1 if i.done else 0)
    di, ti, ds, ts = counts(issues)

    for line in text.splitlines():
        m = ITEM_RE.match(line)
        if m:
            ref = m.group(4)
            s, n = ref.split("#")
            ref = f"{s}#{int(n):02d}"
            want = "x" if (ref in issues and issues[ref].done) else " "
            if ref not in issues:
                changes.append(f"roadmap lists {ref} but no issue file exists")
            elif m.group(2).lower() != want.strip().lower() and not (m.group(2) == " " and want == " "):
                changes.append(f"{ref}: roadmap [{m.group(2)}] -> [{want}] (issue Status: {issues[ref].status})")
            line = f"{m.group(1)}{want}{m.group(3)}{m.group(4)}{m.group(5)}"
        hm = SPEC_HEADING_RE.match(line)
        if hm:
            spec = hm.group(2)
            d, t = per_spec_done.get(spec, 0), per_spec_total.get(spec, int(hm.group(5)))
            if (int(hm.group(4)), int(hm.group(5))) != (d, t):
                changes.append(f"{spec}: heading {hm.group(4)}/{hm.group(5)} -> {d}/{t}")
            line = f"{hm.group(1)}{spec}{hm.group(3)}{d}/{t}"
        pm = PROGRESS_ISSUES_RE.match(line)
        if pm:
            if (int(pm.group(2)), int(pm.group(3))) != (di, ti):
                changes.append(f"Progress issues {pm.group(2)}/{pm.group(3)} -> {di}/{ti}")
            line = f"{pm.group(1)}{di} / {ti}{pm.group(4)}"
        sm = PROGRESS_SPECS_RE.match(line)
        if sm:
            if (int(sm.group(2)), int(sm.group(3))) != (ds, ts):
                changes.append(f"Progress specs {sm.group(2)}/{sm.group(3)} -> {ds}/{ts}")
            line = f"{sm.group(1)}{ds} / {ts}{sm.group(4)}"
        out.append(line)
    rendered = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    listed = {m.group(4) for m in (ITEM_RE.match(l) for l in text.splitlines()) if m}
    listed = {f"{r.split('#')[0]}#{int(r.split('#')[1]):02d}" for r in listed}
    for ref in issues:
        if ref not in listed:
            changes.append(f"issue {ref} exists but is not listed in the roadmap")
    return rendered, changes


def set_status(path: Path, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not STATUS_LINE_RE.search(text):
        raise SystemExit(f"{path} has no Status: line")
    path.write_text(STATUS_LINE_RE.sub(f"Status: {value}", text, count=1), encoding="utf-8")


def append_comment(path: Path, text_line: str) -> None:
    text = path.read_text(encoding="utf-8")
    stamp = dt.date.today().isoformat()
    entry = f"- {stamp} — {text_line.strip()}\n"
    if re.search(r"^## Comments\s*$", text, re.MULTILINE):
        text = text.rstrip("\n") + "\n" + entry
    else:
        text = text.rstrip("\n") + "\n\n## Comments\n\n" + entry
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "done", "status", "comment"])
    ap.add_argument("issue", nargs="?")
    ap.add_argument("value", nargs="?")
    ap.add_argument("--scratch", default=".scratch")
    ap.add_argument("--roadmap", default="ROADMAP.md")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    roadmap_path = root / args.roadmap
    issues = load_issues(root / args.scratch)

    if args.command == "check":
        text = roadmap_path.read_text(encoding="utf-8")
        _, changes = render_roadmap(text, issues)
        di, ti, ds, ts = counts(issues)
        if args.json:
            print(json.dumps({"issues_done": di, "issues_total": ti, "specs_done": ds, "specs_total": ts, "drift": changes}, indent=2))
        else:
            print(f"issues {di}/{ti}, specs {ds}/{ts}")
            for c in changes:
                print(f"  DRIFT: {c}")
            if not changes:
                print("  roadmap is in step with the issue files")
        return 1 if changes else 0

    if not args.issue:
        ap.error(f"{args.command} needs an issue reference")
    issue = resolve_issue_arg(args.issue, root, issues)
    if not issue:
        print(f"issue not found: {args.issue}", file=sys.stderr)
        return 2

    if args.command == "status":
        if not args.value:
            ap.error("status needs a value")
        if args.value.lower() == "done":
            print("refusing: use `roadmap.py done` so the roadmap is updated in the same change", file=sys.stderr)
            return 1
        if not args.dry_run:
            set_status(issue.path, args.value)
        print(f"{issue.ref}: Status -> {args.value}")
        return 0

    if args.command == "comment":
        if not args.value:
            ap.error("comment needs text")
        if not args.dry_run:
            append_comment(issue.path, args.value)
        print(f"{issue.ref}: comment {'would be' if args.dry_run else ''} appended".replace("  ", " "))
        return 0

    # done
    if not issue.criteria:
        print(f"refusing: {issue.ref} has no acceptance criteria to satisfy", file=sys.stderr)
        return 1
    plan = [f"tick {len(issue.criteria)} acceptance criteria in {issue.path.relative_to(root)}",
            f"set Status: done in {issue.path.relative_to(root)}"]
    if args.dry_run:
        # simulate
        issue.status = "done"
        for c in issue.criteria:
            c.checked = True
        issues[issue.ref] = issue
        _, changes = render_roadmap(roadmap_path.read_text(encoding="utf-8"), issues)
        for p in plan + changes:
            print(f"would: {p}")
        return 0

    from acceptance import flip  # local import keeps the module standalone

    flip(issue.path, None, True)
    set_status(issue.path, "done")
    issues = load_issues(root / args.scratch)
    text = roadmap_path.read_text(encoding="utf-8")
    rendered, changes = render_roadmap(text, issues)
    roadmap_path.write_text(rendered, encoding="utf-8")
    for p in plan + changes:
        print(f"did: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
