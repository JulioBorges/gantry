#!/usr/bin/env python3
"""Validate a role result from standard input against its bundled contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
ROLES = ("requirement-critic", "planner", "plan-critic", "implementer", "reviewer", "critic", "learner")
TYPE_NAMES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "null": type(None),
}


def schema_path(role: str) -> Path:
    return SCHEMA_DIR / f"{role}.json"


def matches_type(value: Any, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPE_NAMES[name])


def validate(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        if expected_type not in TYPE_NAMES:
            return [f"{path}: unsupported schema type {expected_type!r}"]
        if not matches_type(value, expected_type):
            return [f"{path}: expected {expected_type}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}.{name}: missing required field")
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in properties:
                    errors.append(f"{path}.{name}: additional property is not allowed")
        for name, child in properties.items():
            if name in value:
                errors.extend(validate(value[name], child, f"{path}.{name}"))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(validate(item, schema["items"], f"{path}[{index}]"))
    return errors


def load_schema(role: str) -> dict[str, Any]:
    with schema_path(role).open(encoding="utf-8") as source:
        schema = json.load(source)
    if not isinstance(schema, dict):
        raise ValueError(f"schema for {role} must be an object")
    return schema


def extract_json(raw: str) -> Any:
    """Extract and parse JSON from raw string, handling markdown fences and delimiters."""
    if not raw or not raw.strip():
        raise json.JSONDecodeError("Expecting value: empty input", raw or "", 0)

    text = raw.strip()
    # 1. Try parsing directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract from markdown code fence (```json ... ``` or ``` ... ```)
    fence_pattern = re.compile(r"```+(?:json|JSON)?\s*\n([\s\S]*?)\n```+", re.MULTILINE)
    matches = fence_pattern.findall(text)
    for block in matches:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue

    fence_pattern_inline = re.compile(r"```+(?:json|JSON)?\s*([\s\S]*?)\s*```+", re.MULTILINE)
    matches_inline = fence_pattern_inline.findall(text)
    for block in matches_inline:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue

    # 3. Try outermost JSON object braces `{ ... }`
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 4. Try outermost JSON array brackets `[ ... ]`
    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = text[first_bracket : last_bracket + 1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Fallback to direct json.loads to raise original JSONDecodeError
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=ROLES, help="role contract to validate")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable validation result")
    parser.add_argument("--schema", action="store_true", help="print the selected schema")
    args = parser.parse_args()
    try:
        schema = load_schema(args.role)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"result schema error: {error}", file=sys.stderr)
        return 2
    if args.schema:
        print(json.dumps(schema))
        return 0
    try:
        raw_input = sys.stdin.read()
        result = extract_json(raw_input)
    except json.JSONDecodeError as error:
        errors = [f"$: invalid JSON: {error.msg}"]
    else:
        errors = validate(result, schema)
    payload = {"role": args.role, "valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(payload))
    elif errors:
        for error in errors:
            print(error)
    else:
        print(f"{args.role}: valid")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
