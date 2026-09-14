#!/usr/bin/env python3
"""Conversational setup wizard for Gantry policy and hooks."""
import argparse
import json
import sys
from pathlib import Path

def merge_dicts(base: dict, update: dict) -> dict:
    for k, v in update.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            merge_dicts(base[k], v)
        else:
            base[k] = v
    return base

def main() -> None:
    parser = argparse.ArgumentParser(description="Gantry Setup config writer")
    parser.add_argument("--config", help="JSON config string")
    args = parser.parse_args()

    if args.config:
        config = json.loads(args.config)
    else:
        config_text = sys.stdin.read().strip()
        if not config_text:
            print("Error: No config provided", file=sys.stderr)
            sys.exit(2)
        config = json.loads(config_text)

    print("Proposed .gantry/config.json:")
    print(json.dumps(config, indent=2))

    repo_root = Path.cwd()
    gantry_dir = repo_root / ".gantry"
    config_path = gantry_dir / "config.json"

    if config_path.exists():
        choice = input("Config exists. [M]erge, [O]verwrite, or [A]bort? ").strip().lower()
        if choice.startswith('a'):
            print("Aborted.")
            sys.exit(1)
        elif choice.startswith('o'):
            final_config = config
        elif choice.startswith('m'):
            existing = json.loads(config_path.read_text(encoding="utf-8"))
            final_config = merge_dicts(existing, config)
        else:
            print("Invalid choice, aborted.")
            sys.exit(1)
    else:
        choice = input("Write this policy? [y/N] ").strip().lower()
        if not choice.startswith('y'):
            print("Aborted.")
            sys.exit(1)
        final_config = config

    gantry_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(final_config, indent=2) + "\n", encoding="utf-8")

    hook_frag_path = Path(__file__).resolve().parents[1] / "hooks" / "claude-code.settings.json"
    if hook_frag_path.exists():
        hook_frag = json.loads(hook_frag_path.read_text(encoding="utf-8"))
        settings_path = repo_root / ".claude" / "settings.json"
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        else:
            settings = {}
            settings_path.parent.mkdir(parents=True, exist_ok=True)

        if "hooks" not in settings:
            settings["hooks"] = {}
        for k, v in hook_frag.get("hooks", {}).items():
            settings["hooks"][k] = v

        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    agents_path = repo_root / "AGENTS.md"
    content = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    begin_marker = "<!-- gantry:begin -->"
    end_marker = "<!-- gantry:end -->"
    
    new_section = (
        f"{begin_marker}\n"
        "## Gantry Repository Policy\n\n"
        "This repository uses Gantry for its agentic SDLC.\n"
        "Artifacts, templates, and checks are configured in `.gantry/config.json`.\n"
        f"{end_marker}\n"
    )

    if begin_marker in content and end_marker in content:
        start = content.find(begin_marker)
        end = content.find(end_marker) + len(end_marker)
        if content[end:end+1] == "\n":
            end += 1
        new_content = content[:start] + new_section + content[end:]
    else:
        new_content = content + ("\n" if content and not content.endswith("\n") else "") + new_section

    agents_path.write_text(new_content, encoding="utf-8")

if __name__ == "__main__":
    main()
