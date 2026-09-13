#!/usr/bin/env python3
"""Guard hook handler: protects Issue/Roadmap authority and records events.

`guard.py` is invoked by a harness hook with the event name as its one positional
argument and the harness's JSON payload on standard input. Per ADR-0003, it never
decides whether work is ready or done -- that authority stays with `roadmap.py` and
the other workflow scripts. It only blocks specific shortcuts (editing the roadmap or
an Issue's Status/checkbox fields outside `roadmap.py`, force-pushing, committing a
test-skip pattern) and records hook and subagent events into the Run log. Any payload
shape it does not recognise degrades to "record what is safely recordable, grant no
authority" -- it never denies without both a rule and a refused path, and it never
manufactures a false completion.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import runlog  # noqa: E402

DECISION_EVENTS = {"PreToolUse", "tool.execute.before"}
SUBAGENT_START_EVENTS = {"SubagentStart"}
SUBAGENT_STOP_EVENTS = {"SubagentStop"}
COMPACTION_EVENTS = {"PreCompact", "session.compacted"}

CAPABILITIES_DIR = Path(__file__).parent.parent / "capabilities"
HARNESS_BY_EVENT = {
    "PreToolUse": "claude-code",
    "PostToolUse": "claude-code",
    "SubagentStart": "claude-code",
    "SubagentStop": "claude-code",
    "PreCompact": "claude-code",
    "tool.execute.before": "opencode",
    "session.compacted": "opencode",
}
# The concepts (not literal keys -- a harness may spell them differently) a given
# event needs to be handled without guessing. Anything a concept resolves to a
# harness's declared `payload_fields` name, and is then absent from the payload
# itself, is recorded as a degradation, never a denial.
EVENT_REQUIRED_CONCEPTS = {
    "PreToolUse": ("tool_name", "tool_input"),
    "PostToolUse": ("tool_name", "tool_input"),
    "SubagentStart": ("session_id",),
    "SubagentStop": ("session_id",),
    "PreCompact": (),
    "tool.execute.before": ("tool_name", "tool_input"),
    "session.compacted": ("session_id",),
}
# Which literal `payload_fields` name each harness uses for a concept.
CONCEPT_FIELD_BY_HARNESS = {
    "claude-code": {"tool_name": "tool_name", "tool_input": "tool_input", "session_id": "session_id"},
    "opencode": {"tool_name": "tool", "tool_input": "args", "session_id": "sessionID"},
}
CONCEPT_ALIASES = {
    "tool_name": ("tool_name", "tool", "toolName"),
    "tool_input": ("tool_input", "args", "toolInput", "input"),
    "session_id": ("session_id", "sessionID", "sessionId"),
}

MODIFYING_TOOLS = {"edit", "write", "multiedit", "notebookedit", "applypatch", "patch"}
BASH_TOOLS = {"bash", "shell", "exec"}

ISSUE_FILE_RE = re.compile(r"^\d{2,}-[a-z0-9-]+\.md$")
STATUS_LINE_RE = re.compile(r"(?m)^Status:\s*(\S+)")
CHECKBOX_LINE_RE = re.compile(r"(?m)^\s*-\s\[[ xX]\]")
CHECKED_CHECKBOX_RE = re.compile(r"(?m)^\s*-\s\[[xX]\]")
PUSH_RE = re.compile(r"\bgit\b[^&|;]*\bpush\b")
FORCE_FLAG_RE = re.compile(r"(--force(-with-lease)?\b|(?:^|\s)-f\b)")
FORCE_REFSPEC_RE = re.compile(r"(?:^|\s)\+\S")
COMMIT_RE = re.compile(r"\bgit\b[^&|;]*\bcommit\b")
TEST_SKIP_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"^\s*@unittest\.skip",
        r"^\s*@pytest\.mark\.(skip|xfail)",
        r"^\s*@Disabled",
        r"^\s*(xit|xdescribe)\(",
        r"\b(it|describe|test)\.skip\(",
        r"\bt\.Skip\(",
    )
]


class Decision:
    def __init__(self, allow: bool, rule: str | None = None, path: str | None = None):
        self.allow = allow
        self.rule = rule
        self.path = path


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _first(payload: dict, keys: tuple[str, ...]) -> object:
    for key in keys:
        if isinstance(payload, dict) and key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def tool_name(payload: dict) -> str:
    value = _first(payload, ("tool_name", "tool", "toolName"))
    return str(value).strip().lower() if value else ""


def tool_input(payload: dict) -> dict:
    value = _first(payload, ("tool_input", "args", "toolInput", "input"))
    return value if isinstance(value, dict) else {}


def extract_path(payload: dict, arguments: dict) -> str | None:
    value = _first(arguments, ("file_path", "filePath", "path", "filename")) or _first(payload, ("file_path", "path"))
    return str(value) if value else None


def extract_text(arguments: dict) -> str:
    parts: list[str] = []
    for key in ("old_string", "oldString", "new_string", "newString", "content", "text"):
        value = arguments.get(key)
        if isinstance(value, str):
            parts.append(value)
    edits = arguments.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                for key in ("old_string", "oldString", "new_string", "newString"):
                    value = edit.get(key)
                    if isinstance(value, str):
                        parts.append(value)
    return "\n".join(parts)


def extract_new_text(arguments: dict) -> str:
    """The resulting text a modifying tool would write -- never the text it replaces."""
    parts: list[str] = []
    for key in ("new_string", "newString", "content", "text"):
        value = arguments.get(key)
        if isinstance(value, str):
            parts.append(value)
    edits = arguments.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                for key in ("new_string", "newString"):
                    value = edit.get(key)
                    if isinstance(value, str):
                        parts.append(value)
    return "\n".join(parts)


def is_draft_safe(new_text: str) -> bool:
    """True when the resulting content only ever declares `Status: draft` and no checked box."""
    statuses = STATUS_LINE_RE.findall(new_text)
    if any(status.lower() != "draft" for status in statuses):
        return False
    return CHECKED_CHECKBOX_RE.search(new_text) is None


def extract_command(arguments: dict) -> str | None:
    value = _first(arguments, ("command", "cmd"))
    return str(value) if value else None


def staged_diff_skip_match(cwd: Path) -> str | None:
    """Return the first staged file whose added lines introduce a test-skip pattern."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    current_file: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("+++ "):
            current_file = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            added = line[1:]
            if any(pattern.search(added) for pattern in TEST_SKIP_PATTERNS):
                return current_file
    return None


def decide(payload: dict, cwd: Path) -> Decision:
    """Evaluate one tool-invocation payload against the protected rule set."""
    if not isinstance(payload, dict):
        return Decision(True)
    name = tool_name(payload)
    arguments = tool_input(payload)
    normalized_name = re.sub(r"[^a-z]", "", name)

    if normalized_name in MODIFYING_TOOLS:
        path = extract_path(payload, arguments)
        if not path:
            return Decision(True)
        basename = Path(path).name
        if basename == "ROADMAP.md":
            return Decision(False, "roadmap-protected", path)
        if ISSUE_FILE_RE.match(basename):
            if normalized_name in {"write", "multiedit"}:
                target = Path(path)
                target = target if target.is_absolute() else cwd / target
                if not target.exists() or is_draft_safe(extract_new_text(arguments)):
                    return Decision(True)
            changed = extract_text(arguments)
            if STATUS_LINE_RE.search(changed):
                return Decision(False, "issue-status-protected", path)
            if CHECKBOX_LINE_RE.search(changed):
                return Decision(False, "issue-checkbox-protected", path)
        return Decision(True)

    if normalized_name in BASH_TOOLS:
        command = extract_command(arguments)
        if not command:
            return Decision(True)
        if PUSH_RE.search(command) and (FORCE_FLAG_RE.search(command) or FORCE_REFSPEC_RE.search(command)):
            return Decision(False, "no-force-push", command.strip()[:200])
        if COMMIT_RE.search(command):
            matched_file = staged_diff_skip_match(cwd)
            if matched_file:
                return Decision(False, "no-test-skip-commit", matched_file)
        return Decision(True)

    return Decision(True)


def resolve_run_id(payload: dict, override: str | None) -> str | None:
    candidate = override or os.environ.get("GANTRY_RUN_ID") or _first(payload, ("session_id", "sessionID", "sessionId"))
    if not candidate:
        return None
    candidate = str(candidate)
    return candidate if runlog.RUN_ID_RE.fullmatch(candidate) else None


def record(cwd: Path, state_root: str | None, run_id: str, event: dict) -> None:
    """Best-effort append; a logging failure never changes the hook's decision."""
    try:
        payload = runlog.validate_event(event)
        unit = runlog.unit_id(cwd)
        root = runlog.state_root(state_root)
        path = runlog.run_log_path(root, unit, run_id)
        if not path.exists():
            return
        runlog.append_event(path, payload)
    except (runlog.EventError, OSError, ValueError):
        return


_CAPABILITY_CACHE: dict[str, dict] = {}


def load_capability(harness: str) -> dict:
    """Read `capabilities/<harness>.json`; a missing or unreadable file means no declared fields."""
    if harness in _CAPABILITY_CACHE:
        return _CAPABILITY_CACHE[harness]
    capability: dict = {}
    try:
        parsed = json.loads((CAPABILITIES_DIR / f"{harness}.json").read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            capability = parsed
    except (OSError, json.JSONDecodeError):
        capability = {}
    _CAPABILITY_CACHE[harness] = capability
    return capability


def degradation_fields(event: str, payload: dict) -> list[str]:
    """Declared field names (per the harness's capability file) this event needs that the payload lacks.

    A concept (e.g. "tool_input") is present as soon as any of the harness's accepted
    spellings for it carries a value, so a payload shaped like another harness's (as the
    OpenCode-forwarded Claude Code shape is in `PreToolUse`-equivalent tests) is not
    penalised for using a different, still-recognised, key.
    """
    harness = HARNESS_BY_EVENT.get(event)
    concepts = EVENT_REQUIRED_CONCEPTS.get(event, ())
    if not harness or not concepts:
        return []
    declared = set(load_capability(harness).get("payload_fields", []))
    concept_field = CONCEPT_FIELD_BY_HARNESS.get(harness, {})
    missing = []
    for concept in concepts:
        field_name = concept_field.get(concept, concept)
        if field_name not in declared:
            continue
        if _first(payload, CONCEPT_ALIASES[concept]) is None:
            missing.append(field_name)
    return missing


def record_degradation(cwd: Path, args: argparse.Namespace, payload: dict, event: str, missing: list[str]) -> None:
    run_id = resolve_run_id(payload, args.run_id)
    if not run_id:
        return
    record(
        cwd,
        args.state_root,
        run_id,
        {
            "ts": now_iso(),
            "run": run_id,
            "event": "hook.degraded",
            "data": {"source": event, "missing": missing, "degraded": True},
        },
    )


def handle_decision_event(payload: dict, args: argparse.Namespace) -> Decision:
    cwd = Path(args.cwd).resolve()
    decision = decide(payload, cwd)
    if not decision.allow:
        run_id = resolve_run_id(payload, args.run_id)
        if run_id:
            record(
                cwd,
                args.state_root,
                run_id,
                {
                    "ts": now_iso(),
                    "run": run_id,
                    "event": "hook.denied",
                    "data": {"rule": decision.rule, "path": decision.path},
                },
            )
    return decision


def handle_subagent_event(payload: dict, args: argparse.Namespace, event: str) -> None:
    cwd = Path(args.cwd).resolve()
    run_id = resolve_run_id(payload if isinstance(payload, dict) else {}, args.run_id)
    if not run_id:
        return
    role = None
    if isinstance(payload, dict):
        role = _first(payload, ("role", "subagent_type", "agent_type", "subagentType", "agentType", "description"))
    record(
        cwd,
        args.state_root,
        run_id,
        {
            "ts": now_iso(),
            "run": run_id,
            "event": event,
            "data": {"role": str(role) if role else "unknown"},
        },
    )


def handle_compaction_event(payload: dict, args: argparse.Namespace) -> None:
    cwd = Path(args.cwd).resolve()
    run_id = resolve_run_id(payload if isinstance(payload, dict) else {}, args.run_id)
    if not run_id:
        return
    source = None
    if isinstance(payload, dict):
        source = _first(payload, ("trigger", "reason", "source"))
    record(
        cwd,
        args.state_root,
        run_id,
        {
            "ts": now_iso(),
            "run": run_id,
            "event": "compaction",
            "data": {"source": str(source) if source else "unknown"},
        },
    )


def read_payload() -> dict | None:
    """Parse standard input; `None` means empty, undecodable, or not a JSON object.

    A `None` payload is never recordable -- no event, degraded or otherwise, is ever
    written for it, and the hook still exits 0 (allow).
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", help="harness hook event name, e.g. PreToolUse or SubagentStop")
    parser.add_argument("--cwd", default=".", help="repository or worktree the payload applies to")
    parser.add_argument("--state-root", help="override ~/.gantry/state")
    parser.add_argument("--run-id", help="override the Run ID (defaults to $GANTRY_RUN_ID or the payload session ID)")
    parser.add_argument("--json", action="store_true", help="emit the decision as a compact JSON object")
    args = parser.parse_args()

    payload = read_payload()

    def allow() -> int:
        if args.json:
            print(json.dumps({"decision": "allow"}, separators=(",", ":")))
        else:
            print("allow")
        return 0

    if payload is None:
        # Empty, undecodable, or non-object stdin: never recorded, degraded or otherwise.
        return allow()

    cwd = Path(args.cwd).resolve()
    missing = degradation_fields(args.event, payload)
    if missing:
        record_degradation(cwd, args, payload, args.event, missing)
        return allow()

    if args.event in DECISION_EVENTS:
        decision = handle_decision_event(payload, args)
        if decision.allow:
            return allow()
        message = f"deny: {decision.rule} {decision.path}"
        if args.json:
            print(json.dumps({"decision": "deny", "rule": decision.rule, "path": decision.path}, separators=(",", ":")))
        else:
            print(message)
        print(message, file=sys.stderr)
        return 2

    if args.event in SUBAGENT_START_EVENTS:
        handle_subagent_event(payload, args, "subagent.started")
        return allow()

    if args.event in SUBAGENT_STOP_EVENTS:
        handle_subagent_event(payload, args, "subagent.stopped")
        return allow()

    if args.event in COMPACTION_EVENTS:
        handle_compaction_event(payload, args)
        return allow()

    # Unknown payload shapes degrade to recording nothing and granting no authority.
    return allow()


if __name__ == "__main__":
    sys.exit(main())
