#!/usr/bin/env python3
"""Validate a Spec's structure against its effective template."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import repo_root, resolve_effective_template, resolve_heading_map  # noqa: E402

HEADING_RE = re.compile(r"^##(?!#)[ \t]+(.+?)[ \t]*$", re.MULTILINE)
SCENARIO_RE = re.compile(r"^[ \t]*Scenario:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
STEP_RE = re.compile(r"^[ \t]*(Given|When|Then|And|But)[ \t]+(.+?)[ \t]*$")
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>|YYYY-MM-DD")
FENCE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})(.*)$")


def headings(text: str) -> list[str]:
    """Return the document's level-two Markdown headings."""
    outside_fences: list[str] = []
    fenced = False
    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*(?:`{3,}|~{3,})", line):
            fenced = not fenced
        elif not fenced:
            outside_fences.append(line)
    return [f"## {match.group(1)}" for match in HEADING_RE.finditer("".join(outside_fences))]


def scenario_context(text: str) -> str:
    """Keep unfenced and Gherkin-fenced text, preserving line numbers."""
    relevant: list[str] = []
    fenced = False
    gherkin = False
    for line in text.splitlines(keepends=True):
        fence = FENCE_RE.match(line)
        if fence:
            if not fenced:
                gherkin = fence.group(1).strip().casefold() == "gherkin"
            else:
                gherkin = False
            fenced = not fenced
            relevant.append("\n" if line.endswith("\n") else "")
        elif not fenced or gherkin:
            relevant.append(line)
        else:
            relevant.append("\n" if line.endswith("\n") else "")
    return "".join(relevant)


def canonical_heading(heading: str, heading_map: dict[str, str]) -> str:
    """Translate one declared equivalent heading to its template heading."""
    if heading in heading_map:
        return heading_map[heading]
    lowered = heading.casefold()
    for alias, canonical in heading_map.items():
        if alias.casefold() == lowered:
            return canonical
    return heading


def validate_scenarios(text: str, required: bool) -> list[dict[str, object]]:
    """Check that every Scenario has ordered Given, When and Then steps."""
    text = scenario_context(text)
    matches = list(SCENARIO_RE.finditer(text))
    if required and not matches:
        return [{"line": None, "reason": "expected at least one Scenario with Given, When and Then steps"}]

    malformed: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        steps = [
            (line_number, step.group(1))
            for line_number, line in enumerate(
                text[match.end():end].splitlines(),
                text[:match.end()].count("\n") + 1,
            )
            if (step := STEP_RE.match(line))
        ]

        phase: str | None = None
        errors: list[tuple[int, str]] = []
        for line_number, kind in steps:
            if kind == "Given":
                if phase in {None, "given"}:
                    phase = "given"
                else:
                    errors.append((line_number, "Given cannot follow When or Then"))
            elif kind == "When":
                if phase == "given":
                    phase = "when"
                else:
                    errors.append((line_number, "When must follow Given and precede Then"))
            elif kind == "Then":
                if phase == "when":
                    phase = "then"
                else:
                    errors.append((line_number, "Then must follow When"))
            elif phase is None:
                errors.append((line_number, "And or But must follow Given, When or Then"))

        if phase != "then":
            errors.append((text[:match.start()].count("\n") + 1, "Scenario must end with Then steps"))
        for line_number, reason in errors:
            malformed.append(
                {
                    "line": line_number,
                    "scenario": match.group(1),
                    "reason": reason,
                }
            )
    return malformed


def validate(spec: Path, root: Path) -> dict[str, object]:
    """Produce every structural finding for one Spec."""
    template = resolve_effective_template(root, "spec")
    template_text = template.read_text(encoding="utf-8")
    text = spec.read_text(encoding="utf-8")
    required = headings(template_text)
    heading_map = resolve_heading_map(root)
    actual = headings(text)
    present: list[dict[str, str]] = []
    positions: list[tuple[str, int]] = []
    missing: list[str] = []

    for expected in required:
        match = next(
            (
                (position, heading)
                for position, heading in enumerate(actual)
                if canonical_heading(heading, heading_map).casefold() == expected.casefold()
            ),
            None,
        )
        if match is None:
            missing.append(expected)
        else:
            position, heading = match
            present.append({"expected": expected, "actual": heading})
            positions.append((expected, position))

    out_of_order: list[dict[str, str]] = []
    for (previous, previous_position), (current, current_position) in zip(positions, positions[1:]):
        if current_position < previous_position:
            out_of_order.append(
                {
                    "expected": current,
                    "found_after": previous,
                    "actual": next(item["actual"] for item in present if item["expected"] == current),
                }
            )

    template_placeholders = set(PLACEHOLDER_RE.findall(template_text))
    placeholders = [
        {"line": text[:match.start()].count("\n") + 1, "text": match.group(0)}
        for match in PLACEHOLDER_RE.finditer(text)
        if match.group(0) in template_placeholders
    ]
    malformed_scenarios = validate_scenarios(text, "Scenario:" in template_text)
    valid = not any((missing, out_of_order, placeholders, malformed_scenarios))
    return {
        "spec": str(spec),
        "template": str(template),
        "required_headings": required,
        "present": present,
        "missing": missing,
        "out_of_order": out_of_order,
        "placeholders": placeholders,
        "malformed_scenarios": malformed_scenarios,
        "valid": valid,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the supplied Spec")
    parser.add_argument("spec", nargs="?", help="Spec path")
    parser.add_argument("--cwd", default=".", help="repository or worktree containing the policy")
    parser.add_argument("--json", action="store_true", help="print machine-readable findings")
    args = parser.parse_args()
    if not args.check or not args.spec:
        parser.print_usage(sys.stderr)
        return 2

    root = repo_root(Path(args.cwd))
    spec = Path(args.spec)
    spec = spec if spec.is_absolute() else root / spec
    if not spec.is_file():
        payload = {"spec": str(spec), "error": "Spec is not a readable file"}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Spec is not a readable file: {spec}", file=sys.stderr)
        return 2

    try:
        payload = validate(spec.resolve(), root)
    except (OSError, UnicodeError, ValueError) as exc:
        payload = {"spec": str(spec), "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Spec cannot be validated: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("valid" if payload["valid"] else "invalid")
        for key in ("missing", "out_of_order", "placeholders", "malformed_scenarios"):
            for finding in payload[key]:
                print(f"{key}: {finding}")
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
