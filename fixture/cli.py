"""Command-line entry point for the Gantry reference fixture greeting project."""
from __future__ import annotations

import sys

from greeting import greet


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: cli.py <name>", file=sys.stderr)
        return 2
    print(greet(argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
