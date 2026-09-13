#!/usr/bin/env python3
"""Validate a role result from standard input against its bundled contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
ROLES = ("planner", "plan-critic", "implementer", "reviewer", "critic", "learner")
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
        result = json.load(sys.stdin)
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
