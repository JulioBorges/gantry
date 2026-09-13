#!/usr/bin/env python3
"""Build a deterministic, isolated copy of the Gantry reference fixture.

Produces an independent Git repository at ``--dest`` with a baseline commit and
a pack-visible local Gantry-skill installation copied from ``--skill-dir``.
``--mode unplanned`` omits every Issue file; ``--mode approved`` includes the
fixture's three ``ready-for-agent`` greeting Issues. Never modifies the source
fixture or the skill directory it reads from.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_RELATIVE_PATHS = {Path("tools") / "copy_fixture.py"}
ISSUES_RELATIVE_DIR = Path(".scratch") / "greeting" / "issues"
BASELINE_DATE = "2000-01-01T00:00:00Z"
GENERATED_ARTIFACT_NAMES = {"__pycache__", ".pytest_cache", ".git"}
GENERATED_ARTIFACT_SUFFIXES = (".pyc", ".pyo", ".pyd")


def _is_generated_artifact(relative: Path) -> bool:
    if set(relative.parts) & GENERATED_ARTIFACT_NAMES:
        return True
    return relative.suffix in GENERATED_ARTIFACT_SUFFIXES


def copy_fixture_content(dest: Path, mode: str) -> None:
    """Copy the reusable fixture tree into ``dest``, mode-gating the Issues."""
    for source in sorted(FIXTURE_ROOT.rglob("*")):
        if source.is_dir():
            continue
        relative = source.relative_to(FIXTURE_ROOT)
        if relative in EXCLUDED_RELATIVE_PATHS:
            continue
        if _is_generated_artifact(relative):
            continue
        if mode == "unplanned" and ISSUES_RELATIVE_DIR in relative.parents:
            continue
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def install_skill(dest: Path, skill_dir: Path) -> None:
    """Copy the canonical Gantry skill into ``dest`` and make it pack-visible."""
    skill_name = skill_dir.name
    installed = dest / ".agents" / "skills" / skill_name
    installed.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        skill_dir,
        installed,
        ignore=shutil.ignore_patterns("__pycache__", "*.py[cod]", ".pytest_cache", ".git"),
    )
    claude_skills = dest / ".claude" / "skills"
    claude_skills.parent.mkdir(parents=True, exist_ok=True)
    claude_skills.symlink_to(Path("..") / ".agents" / "skills", target_is_directory=True)


def git(dest: Path, *args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True, text=True, env=env)


def init_baseline_commit(dest: Path) -> None:
    git(dest, "init", "--quiet")
    git(dest, "config", "user.email", "fixture@gantry.local")
    git(dest, "config", "user.name", "Gantry Fixture")
    git(dest, "config", "commit.gpgsign", "false")
    git(dest, "add", "-A")
    commit_env = {
        "GIT_AUTHOR_NAME": "Gantry Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@gantry.local",
        "GIT_AUTHOR_DATE": BASELINE_DATE,
        "GIT_COMMITTER_NAME": "Gantry Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@gantry.local",
        "GIT_COMMITTER_DATE": BASELINE_DATE,
    }
    git(dest, "commit", "--quiet", "-m", "chore: fixture baseline", env={**os.environ, **commit_env})


def build(mode: str, skill_dir: Path, dest: Path) -> None:
    if mode not in {"unplanned", "approved"}:
        raise ValueError("mode must be unplanned or approved")
    if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
        raise ValueError(f"--skill-dir {skill_dir} must be a Gantry skill directory containing SKILL.md")
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.iterdir()):
        raise ValueError(f"--dest {dest} must be an empty directory")

    copy_fixture_content(dest, mode)
    install_skill(dest, skill_dir)
    init_baseline_commit(dest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["unplanned", "approved"])
    parser.add_argument("--skill-dir", required=True, type=Path, help="canonical Gantry skill directory to install")
    parser.add_argument("--dest", required=True, type=Path, help="empty directory to build the isolated copy in")
    args = parser.parse_args()

    try:
        build(args.mode, args.skill_dir.resolve(), args.dest.resolve())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"copy_fixture: {error}", file=sys.stderr)
        return 1
    print(f"built {args.mode} fixture copy at {args.dest.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
