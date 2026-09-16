#!/usr/bin/env python3
"""Caveman lite discovery, installation guidance, and activation resolution."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from common import repo_root, resolve_policy


def get_install_guidance(harness: str | None = None) -> str:
    """Return verified upstream skill-only installation guidance for the host harness."""
    h = (harness or "claude-code").lower()
    if "antigravity" in h or "agy" in h:
        return (
            "Clone Caveman into your Antigravity skills directory:\n"
            "  git clone https://github.com/JuliusBrussee/caveman.git ~/.gemini/config/skills/caveman\n"
            "  (or inside repository at .agents/skills/caveman)"
        )
    elif "opencode" in h:
        return (
            "Clone Caveman into your OpenCode skills directory:\n"
            "  git clone https://github.com/JuliusBrussee/caveman.git ~/.config/opencode/skills/caveman\n"
            "  (or inside repository at .agents/skills/caveman)"
        )
    elif "codex" in h:
        return (
            "Clone Caveman into your skills directory:\n"
            "  git clone https://github.com/JuliusBrussee/caveman.git .agents/skills/caveman"
        )
    else:  # Claude Code / default
        return (
            "Install Caveman skill using npx skills:\n"
            "  npx skills add caveman\n"
            "  (or git clone https://github.com/JuliusBrussee/caveman.git ~/.claude/skills/caveman)"
        )


def check_availability(harness: str | None = None, root: Path | None = None) -> dict:
    """Verify that the host harness can discover and read the Caveman skill."""
    root_path = root.resolve() if root else repo_root()
    home = Path.home()

    # Allow environment override for testing/fixtures without touching global paths
    env_override = os.environ.get("GANTRY_CAVEMAN_PATH")
    candidate_paths: list[Path] = []
    if env_override:
        p = Path(env_override)
        candidate_paths.append(p if p.name == "SKILL.md" else p / "SKILL.md")

    # In-repository skill
    candidate_paths.append(root_path / ".agents" / "skills" / "caveman" / "SKILL.md")

    h = (harness or "").lower()
    if "antigravity" in h:
        candidate_paths.extend([
            home / ".gemini" / "config" / "skills" / "caveman" / "SKILL.md",
            home / ".agents" / "skills" / "caveman" / "SKILL.md",
        ])
    elif "opencode" in h:
        candidate_paths.extend([
            home / ".config" / "opencode" / "skills" / "caveman" / "SKILL.md",
            home / ".agents" / "skills" / "caveman" / "SKILL.md",
        ])
    elif "codex" in h:
        candidate_paths.extend([
            home / ".codex" / "skills" / "caveman" / "SKILL.md",
            home / ".agents" / "skills" / "caveman" / "SKILL.md",
        ])
    else:  # Claude Code or generic
        candidate_paths.extend([
            root_path / ".claude" / "skills" / "caveman" / "SKILL.md",
            home / ".claude" / "skills" / "caveman" / "SKILL.md",
            home / ".agents" / "skills" / "caveman" / "SKILL.md",
        ])

    for candidate in candidate_paths:
        if candidate.is_file():
            try:
                candidate.read_text(encoding="utf-8")
                return {
                    "available": True,
                    "path": str(candidate.resolve()),
                    "harness": harness or "auto",
                }
            except (OSError, PermissionError) as exc:
                return {
                    "available": False,
                    "reason": f"unreadable: {exc}",
                    "path": str(candidate.resolve()),
                    "install_guidance": get_install_guidance(harness),
                }

    return {
        "available": False,
        "reason": "not_found",
        "install_guidance": get_install_guidance(harness),
    }


def resolve_activation(
    policy: dict,
    harness: str | None = None,
    root: Path | None = None,
    warned: bool = False,
) -> dict:
    """Resolve Caveman activation state and handle once-per-Run warning deduplication."""
    pref = policy.get("caveman", False)
    # Handle boolean or dict representation safely
    preference_enabled = bool(pref.get("enabled", True) if isinstance(pref, dict) else pref)

    if not preference_enabled:
        return {
            "preference": False,
            "active": False,
            "scope": "none",
            "warning": None,
            "warned": warned,
        }

    avail = check_availability(harness=harness, root=root)
    if avail["available"]:
        return {
            "preference": True,
            "active": True,
            "skill_path": avail["path"],
            "scope": "conversational_and_summaries",
            "warning": None,
            "warned": warned,
        }

    # Preference enabled, but skill unavailable
    warning = None
    new_warned = warned
    if not warned:
        guidance = avail.get("install_guidance", get_install_guidance(harness))
        warning = (
            "Warning: Caveman lite is enabled in repository policy, but the Caveman skill was not "
            "found or is unreadable in the host environment. Continuing with normal behavior.\n"
            f"{guidance}"
        )
        new_warned = True

    return {
        "preference": True,
        "active": False,
        "scope": "none",
        "warning": warning,
        "warned": new_warned,
    }


def get_coordinating_instructions(active: bool = True) -> str:
    """Return coordinating agent instructions for Caveman lite conversational scope."""
    if not active:
        return ""
    return (
        "Caveman lite is active for this Run: use concise phrasing for conversational messages and "
        "summaries. Specs, Issues, documentation, PR descriptions, Result Contracts, exact commands, "
        "exact errors, and acceptance criteria retain full detail."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="check host-harness skill discovery and readability")
    check_parser.add_argument("--harness", default="claude-code", help="host harness name")
    check_parser.add_argument("--cwd", default=".", help="repository root path")
    check_parser.add_argument("--json", action="store_true", help="output JSON")

    resolve_parser = subparsers.add_parser("resolve", help="resolve effective Caveman activation for Run")
    resolve_parser.add_argument("--harness", default="claude-code", help="host harness name")
    resolve_parser.add_argument("--cwd", default=".", help="repository root path")
    resolve_parser.add_argument("--warned", action="store_true", help="whether warning was already emitted")
    resolve_parser.add_argument("--json", action="store_true", help="output JSON")

    subparsers.add_parser("guidance", help="print installation guidance")

    args = parser.parse_args()

    if args.command == "check":
        root = Path(args.cwd).resolve()
        res = check_availability(harness=args.harness, root=root)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res["available"]:
                print(f"Caveman available: {res['path']}")
            else:
                print(f"Caveman not available: {res['reason']}")
                print(res["install_guidance"])
        return 0 if res["available"] else 1

    elif args.command == "resolve":
        root = Path(args.cwd).resolve()
        policy = resolve_policy(root)
        res = resolve_activation(policy, harness=args.harness, root=root, warned=args.warned)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Caveman preference: {res['preference']}, active: {res['active']}")
            if res["warning"]:
                print(res["warning"])
        return 0

    elif args.command == "guidance":
        print(get_install_guidance())
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
