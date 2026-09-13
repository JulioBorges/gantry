#!/usr/bin/env python3
"""Draft recurring lesson candidates from recorded Run-log refutations and review findings.

The Learner reads no source other than the permitted Run-log events named on the command
line: `refutation` and `review.finding`. It never opens `AGENTS.md`, `CONTEXT.md`, a template
or the repository policy, and it never writes anything; a lesson candidate is a proposal for
the operator, not an injected change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from runlog import read_valid_events  # noqa: E402

LESSON_EVENTS = {"refutation", "review.finding"}
DEFAULT_TARGET = "AGENTS.md (Gantry section)"


def lesson_message(event: dict) -> str | None:
    data = event.get("data")
    if not isinstance(data, dict):
        return None
    message = data.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def collect_lesson_events(paths: list[Path]) -> list[dict]:
    """Read only the permitted refutation and review-finding events from the given Run logs."""
    events: list[dict] = []
    for path in paths:
        for event in read_valid_events(path):
            if event.get("event") in LESSON_EVENTS:
                events.append(event)
    return events


def draft_candidates(paths: list[Path], target: str = DEFAULT_TARGET) -> list[dict]:
    """Group recurring refutations/review findings across Issues or attempts into candidates.

    Recurrence is counted per occurrence (each matching event), not per distinct Issue: two
    refutation events sharing a message on the same Issue (e.g. two correction attempts) count
    as two occurrences, just as the same message on two different Issues does.
    """
    order: list[str] = []
    occurrences_by_message: dict[str, list[str]] = {}
    for event in collect_lesson_events(paths):
        message = lesson_message(event)
        issue = event.get("issue")
        if not message or not isinstance(issue, str):
            continue
        if message not in occurrences_by_message:
            occurrences_by_message[message] = []
            order.append(message)
        occurrences_by_message[message].append(issue)

    candidates = []
    for message in order:
        occurrences = occurrences_by_message[message]
        if len(occurrences) < 2:
            continue
        candidates.append(
            {
                "lesson": message,
                "evidence": [f"{issue}: {message}" for issue in occurrences],
                "target": target,
            }
        )
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runlog", nargs="+", help="one or more Run-log JSONL file paths")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="proposed target for every candidate")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()
    paths = [Path(value) for value in args.runlog]
    candidates = draft_candidates(paths, args.target)
    payload = {"candidates": candidates}
    if args.json:
        print(json.dumps(payload))
    elif candidates:
        for candidate in candidates:
            print(f"- {candidate['lesson']} -> {candidate['target']}")
            for item in candidate["evidence"]:
                print(f"    {item}")
    else:
        print("no recurring lesson candidates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
