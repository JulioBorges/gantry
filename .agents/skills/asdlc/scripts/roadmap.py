#!/usr/bin/env python3
"""Keep ROADMAP.md and the issue files in step — deterministically.

ROADMAP.md is a projection of the issue files: the `Status:` line of each issue is authoritative, and the
execution waves are the longest-path depth of each issue over the blocker graph (wave N is executable as
one ASDLC round once waves < N are done). This script regenerates the two generated blocks

    <!-- BEGIN GENERATED: spec progress -->  …  <!-- END GENERATED: spec progress -->
    <!-- BEGIN GENERATED: issue checklist --> …  <!-- END GENERATED: issue checklist -->

and the counters in the Progress table, and refuses the unsafe edits AGENTS.md forbids.

  roadmap.py check [--json]                 report drift between ROADMAP.md and the issue files (ticks,
                                            counts, wave placement). Exit 1 on drift.
  roadmap.py waves [--dry-run]              regenerate the generated blocks and counters (after a blocker
                                            change, a new issue, or by hand after `check` reports drift).
  roadmap.py done <spec#NN> [--dry-run]     tick every acceptance criterion, set `Status: done`, regenerate.
  roadmap.py status <spec#NN> <value>       set only the issue's Status line (in-progress, blocked, …).
  roadmap.py comment <spec#NN> "<text>"     append a dated line under `## Comments` in the issue.

`done` is only ever called after the adversarial critic returned complete=true. It is the single place
that flips a roadmap checkbox, so a green checkbox always has a verdict behind it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import Issue, issue_levels, load_issues, repo_root, resolve_issue_arg, spec_numbers  # noqa: E402

PROGRESS_ISSUES_RE = re.compile(r"^(\| Issues completed \| \*\*)(\d+) / (\d+)(\*\* \|)\s*$")
PROGRESS_SPECS_RE = re.compile(r"^(\| Specs completed \| \*\*)(\d+) / (\d+)(\*\* \|)\s*$")
PROGRESS_WAVES_RE = re.compile(r"^(\| Execution waves \| \*\*)(\d+)(\*\* \|)\s*$")
STATUS_LINE_RE = re.compile(r"^Status:\s*.*$", re.MULTILINE)
BLOCK_RE = {
    name: re.compile(rf"(<!-- BEGIN GENERATED: {name} -->\n)(.*?)(<!-- END GENERATED: {name} -->)", re.DOTALL)
    for name in ("spec progress", "issue checklist")
}


def counts(issues: dict[str, Issue]) -> tuple[int, int, int, int]:
    specs: dict[str, list[Issue]] = {}
    for i in issues.values():
        specs.setdefault(i.spec, []).append(i)
    done_issues = sum(1 for i in issues.values() if i.done)
    done_specs = sum(1 for lst in specs.values() if lst and all(i.done for i in lst))
    return done_issues, len(issues), done_specs, len(specs)


def render_spec_progress(issues: dict[str, Issue], levels: dict[str, int], numbers: dict[str, int]) -> str:
    rows = ["| # | Spec | Issues done | Waves |", "|---|---|---|---|"]
    specs = sorted({i.spec for i in issues.values()}, key=lambda s: (numbers.get(s, 99), s))
    for spec in specs:
        lst = [i for i in issues.values() if i.spec == spec]
        done = sum(1 for i in lst if i.done)
        lv = sorted(levels[i.ref] for i in lst)
        span = f"{lv[0]}" if lv[0] == lv[-1] else f"{lv[0]}–{lv[-1]}"
        rows.append(f"| {numbers.get(spec, 0):02d} | `{spec}` | {done}/{len(lst)} | {span} |")
    return "\n".join(rows) + "\n"


def render_issue_checklist(issues: dict[str, Issue], levels: dict[str, int], numbers: dict[str, int]) -> str:
    by_wave: dict[int, list[Issue]] = {}
    for ref, lv in levels.items():
        by_wave.setdefault(lv, []).append(issues[ref])
    out: list[str] = []
    for wave in sorted(by_wave):
        members = sorted(by_wave[wave], key=lambda i: (numbers.get(i.spec, 99), i.spec, i.number))
        done = sum(1 for i in members if i.done)
        out.append(f"\n### Wave {wave} — {done}/{len(members)} done\n")
        for i in members:
            box = "x" if i.done else " "
            line = f"- [{box}] **`{i.ref}`** — {i.title}"
            blockers = [b for b in i.blocked_by if b in issues]
            if not blockers:
                line += " _(no blockers)_"
            out.append(line)
            if blockers:
                out.append("  <br>↳ blocked by: " + ", ".join(blockers))
    return "\n".join(out).lstrip("\n") + "\n"


def render_roadmap(text: str, issues: dict[str, Issue], scratch: Path) -> str:
    levels = issue_levels(issues)
    numbers = spec_numbers(scratch)
    di, ti, ds, ts = counts(issues)
    waves = max(levels.values()) + 1 if levels else 0
    blocks = {
        "spec progress": render_spec_progress(issues, levels, numbers),
        "issue checklist": render_issue_checklist(issues, levels, numbers),
    }
    for name, rx in BLOCK_RE.items():
        if not rx.search(text):
            raise SystemExit(f"ROADMAP.md is missing the generated block markers for '{name}'")
        text = rx.sub(lambda m, name=name: m.group(1) + "\n" + blocks[name] + "\n" + m.group(3), text)
    lines = []
    for line in text.splitlines():
        m = PROGRESS_ISSUES_RE.match(line)
        if m:
            line = f"{m.group(1)}{di} / {ti}{m.group(4)}"
        m = PROGRESS_SPECS_RE.match(line)
        if m:
            line = f"{m.group(1)}{ds} / {ts}{m.group(4)}"
        m = PROGRESS_WAVES_RE.match(line)
        if m:
            line = f"{m.group(1)}{waves}{m.group(3)}"
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def drift(old: str, new: str, limit: int = 40) -> list[str]:
    diff = [l for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
            if (l.startswith(("+", "-")) and not l.startswith(("+++", "---")))]
    return diff[:limit] + ([f"… {len(diff) - limit} more"] if len(diff) > limit else [])


def set_status(path: Path, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not STATUS_LINE_RE.search(text):
        raise SystemExit(f"{path} has no Status: line")
    path.write_text(STATUS_LINE_RE.sub(f"Status: {value}", text, count=1), encoding="utf-8")


def append_comment(path: Path, text_line: str) -> None:
    text = path.read_text(encoding="utf-8")
    entry = f"- {dt.date.today().isoformat()} — {text_line.strip()}\n"
    if re.search(r"^## Comments\s*$", text, re.MULTILINE):
        text = text.rstrip("\n") + "\n" + entry
    else:
        text = text.rstrip("\n") + "\n\n## Comments\n\n" + entry
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "waves", "done", "status", "comment"])
    ap.add_argument("issue", nargs="?")
    ap.add_argument("value", nargs="?")
    ap.add_argument("--scratch", default=".scratch")
    ap.add_argument("--roadmap", default="ROADMAP.md")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    scratch = root / args.scratch
    roadmap_path = root / args.roadmap
    issues = load_issues(scratch)

    if args.command in ("check", "waves"):
        old = roadmap_path.read_text(encoding="utf-8")
        try:
            new = render_roadmap(old, issues, scratch)
        except ValueError as e:  # cycle
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        changes = drift(old, new)
        di, ti, ds, ts = counts(issues)
        if args.command == "waves" and not args.dry_run and changes:
            roadmap_path.write_text(new, encoding="utf-8")
        if args.json:
            print(json.dumps({"issues_done": di, "issues_total": ti, "specs_done": ds, "specs_total": ts,
                              "drift": changes, "written": args.command == "waves" and not args.dry_run and bool(changes)}, indent=2))
        else:
            print(f"issues {di}/{ti}, specs {ds}/{ts}")
            if not changes:
                print("  roadmap is in step with the issue files")
            elif args.command == "waves":
                print(f"  {'would rewrite' if args.dry_run else 'rewrote'} ROADMAP.md ({len(changes)} changed line(s))")
            else:
                for c in changes:
                    print(f"  DRIFT: {c}")
        if args.command == "check":
            return 1 if changes else 0
        return 0

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
        print(f"{issue.ref}: comment {'would be ' if args.dry_run else ''}appended")
        return 0

    # done
    if not issue.criteria:
        print(f"refusing: {issue.ref} has no acceptance criteria to satisfy", file=sys.stderr)
        return 1
    open_blockers = [b for b in issue.blocked_by if b in issues and not issues[b].done]
    if open_blockers:
        print(f"warning: {issue.ref} still has unfinished blockers: {', '.join(open_blockers)}", file=sys.stderr)
    if args.dry_run:
        issue.status = "done"
        for c in issue.criteria:
            c.checked = True
        issues[issue.ref] = issue
        old = roadmap_path.read_text(encoding="utf-8")
        for p in [f"tick {len(issue.criteria)} acceptance criteria in {issue.path.relative_to(root)}",
                  f"set Status: done in {issue.path.relative_to(root)}", *drift(old, render_roadmap(old, issues, scratch))]:
            print(f"would: {p}")
        return 0

    from acceptance import flip  # local import keeps the module standalone

    flip(issue.path, None, True)
    set_status(issue.path, "done")
    issues = load_issues(scratch)
    old = roadmap_path.read_text(encoding="utf-8")
    new = render_roadmap(old, issues, scratch)
    roadmap_path.write_text(new, encoding="utf-8")
    print(f"did: tick {len(issue.criteria)} acceptance criteria and set Status: done in {issue.path.relative_to(root)}")
    for c in drift(old, new):
        print(f"did: {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
