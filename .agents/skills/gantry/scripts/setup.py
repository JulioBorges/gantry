#!/usr/bin/env python3
"""Conversational setup wizard for Gantry policy and hooks."""
import argparse
import json
import os
import shutil
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
    parser.add_argument("--config-file", help="Path to JSON config file")
    args = parser.parse_args()

    if args.config_file:
        config = json.loads(Path(args.config_file).read_text(encoding="utf-8"))
    elif args.config:
        config = json.loads(args.config)
    else:
        print("Error: No config provided", file=sys.stderr)
        sys.exit(2)

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
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        content = settings_path.read_text(encoding="utf-8") if settings_path.exists() else ""
        
        new_hooks = hook_frag.get("hooks", {})
        if not content.strip():
            settings_path.write_text(json.dumps({"hooks": new_hooks}, indent=2) + "\n", encoding="utf-8")
        else:
            # Parse top level to check if hooks exists
            parsed = json.loads(content)
            if "hooks" not in parsed:
                last_brace = content.rfind('}')
                if last_brace != -1:
                    hooks_json = json.dumps({"hooks": new_hooks}, indent=2)[1:-1]
                    if not parsed:
                        new_content = content[:last_brace] + hooks_json + content[last_brace:]
                    else:
                        new_content = content[:last_brace] + "," + hooks_json + content[last_brace:]
                    settings_path.write_text(new_content, encoding="utf-8")
            else:
                import re
                match = re.search(r'"hooks"\s*:\s*\{', content)
                if match:
                    start_idx = match.end() - 1
                    brace_count = 0
                    end_idx = start_idx
                    in_string = False
                    escape = False
                    for i in range(start_idx, len(content)):
                        c = content[i]
                        if not in_string:
                            if c == '{': brace_count += 1
                            elif c == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                            elif c == '"': in_string = True
                        else:
                            if escape: escape = False
                            elif c == '\\': escape = True
                            elif c == '"': in_string = False
                    old_hooks = json.loads(content[start_idx:end_idx])
                    for k, v in new_hooks.items():
                        old_hooks[k] = v
                    lines = content[:start_idx].split('\n')
                    base_indent = len(lines[-1]) - len(lines[-1].lstrip()) if lines else 2
                    new_hooks_text = json.dumps(old_hooks, indent=2)
                    indented_new_hooks = new_hooks_text.replace('\n', '\n' + ' ' * base_indent)
                    settings_path.write_text(content[:start_idx] + indented_new_hooks + content[end_idx:], encoding="utf-8")

    # Antigravity hook wiring: when Antigravity is detected, generate or merge .agents/hooks.json
    if (repo_root / ".agents").exists() or shutil.which("agy") or os.environ.get("ANTIGRAVITY_PROJECT_DIR") or os.environ.get("GEMINI_CLI"):
        ag_hook_frag_path = Path(__file__).resolve().parents[1] / "hooks" / "antigravity.hooks.json"
        if ag_hook_frag_path.exists():
            ag_hook_frag = json.loads(ag_hook_frag_path.read_text(encoding="utf-8"))
        else:
            guard_cmd = 'python3 ".agents/skills/gantry/scripts/guard.py" PreToolUse --json'
            ag_hook_frag = {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": guard_cmd,
                                }
                            ]
                        }
                    ]
                }
            }
        agents_dir = repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        hooks_json_path = agents_dir / "hooks.json"
        if hooks_json_path.exists():
            try:
                existing_hooks = json.loads(hooks_json_path.read_text(encoding="utf-8"))
                if not isinstance(existing_hooks, dict):
                    existing_hooks = {}
            except Exception:
                existing_hooks = {}
            merged_hooks = merge_dicts(existing_hooks, ag_hook_frag)
            hooks_json_path.write_text(json.dumps(merged_hooks, indent=2) + "\n", encoding="utf-8")
        else:
            hooks_json_path.write_text(json.dumps(ag_hook_frag, indent=2) + "\n", encoding="utf-8")

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
