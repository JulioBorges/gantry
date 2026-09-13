#!/usr/bin/env python3
"""A tiny standard-library linter emitting JSON findings for the Gantry fixture.

Flags lines longer than 88 characters in the fixture's own Python source files.
Used as the fixture's differential quality gate, declared in .gantry/config.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_LINE_LENGTH = 88
SOURCE_FILES = ("greeting.py", "cli.py")


def find_long_lines(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for name in SOURCE_FILES:
        path = root / name
        if not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if len(line) > MAX_LINE_LENGTH:
                findings.append(
                    {
                        "rule": "line-too-long",
                        "file": name,
                        "line": line_number,
                        "message": f"line exceeds {MAX_LINE_LENGTH} characters",
                        "severity": "warning",
                    }
                )
    return findings


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    findings = find_long_lines(root)
    print(json.dumps({"findings": findings}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
