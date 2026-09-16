#!/usr/bin/env python3
"""Runtime model and effort discovery across supported harnesses."""
from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SUPPORTED_HARNESSES = {"antigravity", "claude-code", "codex", "opencode"}
PROGRESS_CHAR_RE = re.compile(r"^[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏\s\r\x1b\[0-9;]*Fetching available models\.\.\.", re.MULTILINE)
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


class DiscoveryError(Exception):
    """Raised when runtime model or effort discovery cannot be established."""


def clean_ansi(text: str) -> str:
    """Remove ANSI escape sequences and carriage returns."""
    return ANSI_ESCAPE_RE.sub("", text).replace("\r", "")


def parse_agy_models_output(
    raw_output: str,
    metadata_lookup: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Parse stdout from `agy models` into a structured list of model dicts without inventing windows."""
    cleaned = clean_ansi(raw_output)
    models: list[dict[str, Any]] = []
    seen: set[str] = set()

    for line in cleaned.splitlines():
        line = line.strip()
        if not line or line.startswith("Fetching available models") or line.startswith("Usage:"):
            continue
        parts = line.split(None, 1)
        if not parts:
            continue
        model_id = parts[0].strip()
        display_name = parts[1].strip() if len(parts) > 1 else model_id

        if model_id in seen:
            continue
        seen.add(model_id)

        entry: dict[str, Any] = {
            "id": model_id,
            "name": display_name,
        }

        # Attach verified context metadata or effort if declared/verified
        if metadata_lookup and model_id in metadata_lookup:
            meta = metadata_lookup[model_id]
            if isinstance(meta, dict):
                if "contextWindow" in meta:
                    entry["contextWindow"] = meta["contextWindow"]
                if "supportedEfforts" in meta:
                    entry["supportedEfforts"] = meta["supportedEfforts"]
                if "effort" in meta:
                    entry["effort"] = meta["effort"]

        models.append(entry)

    return models


def fetch_paginated_catalog(fetcher: Callable[[str | None], dict[str, Any]]) -> list[dict[str, Any]]:
    """Fetch all pages from a paginated catalog source."""
    all_models: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        res = fetcher(page_token)
        models = res.get("models", [])
        all_models.extend(models)
        page_token = res.get("next_page_token") or res.get("nextPageToken")
        if not page_token:
            break

    return all_models


def discover_antigravity_models(runner: Callable[..., subprocess.CompletedProcess[str]] | None = None) -> list[dict[str, Any]]:
    """Discover executable models via `agy models`."""
    agy_path = shutil.which("agy")
    if not agy_path:
        raise DiscoveryError("Missing discovery: agy CLI not found in PATH")

    run_cmd = runner or subprocess.run
    try:
        proc = run_cmd([agy_path, "models"], capture_output=True, text=True, check=False)
    except OSError as exc:
        raise DiscoveryError(f"Missing discovery: failed to run agy models: {exc}") from exc

    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip()
        raise DiscoveryError(f"Missing discovery: agy models returned exit code {proc.returncode}: {err}")

    cap_file = Path(__file__).resolve().parents[1] / "capabilities" / "antigravity.json"
    metadata_lookup = {}
    if cap_file.exists():
        try:
            metadata_lookup = json.loads(cap_file.read_text(encoding="utf-8")).get("models", {})
        except Exception:
            pass

    models = parse_agy_models_output(proc.stdout, metadata_lookup=metadata_lookup)
    if not models:
        raise DiscoveryError("Missing discovery: agy models returned an empty model list")
    return models


def discover_models(harness: str, runner: Callable[..., Any] | None = None) -> list[dict[str, Any]]:
    """Discover executable models for the given harness; fail closed on missing discovery."""
    h = (harness or "").lower()
    if h not in SUPPORTED_HARNESSES:
        raise DiscoveryError(f"Missing discovery: unsupported harness {harness!r}. Supported: {sorted(SUPPORTED_HARNESSES)}")

    if h == "antigravity":
        return discover_antigravity_models(runner=runner)
    elif h == "claude-code":
        claude_path = shutil.which("claude")
        if not claude_path:
            raise DiscoveryError("Missing discovery: claude CLI not found in PATH")
        cap_file = Path(__file__).resolve().parents[1] / "capabilities" / "claude-code.json"
        if cap_file.exists():
            cap = json.loads(cap_file.read_text(encoding="utf-8"))
            return [{"id": m, "contextWindow": d["contextWindow"]} for m, d in cap.get("models", {}).items()]
        raise DiscoveryError("Missing discovery: claude capability declaration missing")
    elif h == "opencode":
        opencode_path = shutil.which("opencode")
        if not opencode_path:
            raise DiscoveryError("Missing discovery: opencode CLI not found in PATH")
        cap_file = Path(__file__).resolve().parents[1] / "capabilities" / "opencode.json"
        if cap_file.exists():
            cap = json.loads(cap_file.read_text(encoding="utf-8"))
            return [{"id": m, "contextWindow": d["contextWindow"]} for m, d in cap.get("models", {}).items()]
        raise DiscoveryError("Missing discovery: opencode capability declaration missing")
    elif h == "codex":
        codex_path = shutil.which("codex")
        if not codex_path:
            raise DiscoveryError("Missing discovery: codex CLI not found in PATH")
        cap_file = Path(__file__).resolve().parents[1] / "capabilities" / "codex.json"
        if cap_file.exists():
            cap = json.loads(cap_file.read_text(encoding="utf-8"))
            return [{"id": m, "contextWindow": d["contextWindow"]} for m, d in cap.get("models", {}).items()]
        raise DiscoveryError("Missing discovery: codex capability declaration missing")

    raise DiscoveryError(f"Missing discovery: unhandled harness {harness}")


def sanitize_no_credentials(data: Any) -> Any:
    """Recursively scrub credential keys from dictionary."""
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(secret in k_lower for secret in ("token", "secret", "password", "api_key", "auth")):
                continue
            cleaned[k] = sanitize_no_credentials(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_no_credentials(item) for item in data]
    return data


def create_catalog_entry(
    harness: str,
    models: list[dict[str, Any]],
    provider: str = "",
    account: str = "",
    source_command: str = "",
) -> dict[str, Any]:
    """Create a catalog entry with provenance, freshness, and no credentials."""
    entry = {
        "harness": harness,
        "provider": provider,
        "account": account,
        "models": models,
        "provenance": {
            "source": source_command or f"{harness} discovery",
            "discovered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "freshness_seconds": 3600,
        },
    }
    return sanitize_no_credentials(entry)


def is_catalog_valid(
    catalog: dict[str, Any],
    current_provider: str = "",
    current_account: str = "",
) -> bool:
    """Check whether a catalog entry is valid for the current provider and account."""
    if not isinstance(catalog, dict) or "models" not in catalog:
        return False
    if current_provider and catalog.get("provider") != current_provider:
        return False
    if current_account and catalog.get("account") != current_account:
        return False
    return True


def validate_effort(
    model_id: str,
    effort: str | None,
    supported_efforts: list[str] | None = None,
) -> dict[str, Any]:
    """Validate that the requested reasoning effort is supported by the model."""
    if not effort:
        return {"valid": True}
    if not supported_efforts:
        return {
            "valid": False,
            "error": f"Model {model_id} does not declare supported reasoning effort values.",
        }
    normalized_supported = [e.lower() for e in supported_efforts]
    if effort.lower() not in normalized_supported:
        return {
            "valid": False,
            "error": f"Unsupported effort value {effort!r} for model {model_id}. Supported: {supported_efforts}",
        }
    return {"valid": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", default="antigravity", help="harness to discover models for")
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()

    try:
        models = discover_models(args.harness)
        catalog = create_catalog_entry(
            harness=args.harness,
            models=models,
            source_command=f"gantry discovery --harness {args.harness}",
        )
        if args.json:
            print(json.dumps(catalog, indent=2))
        else:
            print(f"Discovered {len(models)} model(s) for {args.harness}:")
            for m in models:
                eff = f" (effort: {m['effort']})" if "effort" in m else ""
                print(f"  - {m['id']}: window={m.get('contextWindow')}{eff}")
        return 0
    except DiscoveryError as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
