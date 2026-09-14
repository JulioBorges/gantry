#!/usr/bin/env python3
"""Shared test-skip detection for the tracked git hooks.

`pre-commit` scans what a commit is about to write (`git diff --cached`); `pre-push` scans
what a push is about to publish (the diff between the remote tip and the local tip). Both
ask the same question -- does this content *introduce* a line matching a test-skip pattern
-- so the patterns and the diff reader live here once rather than twice.

This module is a helper next to the hooks, not a hook: `core.hooksPath` only ever executes
files whose name is a git hook name, so git never runs it.
"""
from __future__ import annotations

import re
import subprocess

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
# git's own empty-tree object: the base for a first commit that has no parent.
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run git in the hook's own environment, so `GIT_INDEX_FILE` and friends are honoured."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def added_skip_file(diff: str) -> str | None:
    """The first file in a unified diff whose *added* lines introduce a test-skip pattern."""
    current_file: str | None = None
    for line in diff.splitlines():
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


def staged_skip_match() -> str | None:
    """The first staged file introducing a test-skip pattern, whatever put it in the index."""
    result = git("diff", "--cached", "--unified=0")
    if result.returncode != 0:
        return None
    return added_skip_file(result.stdout)


def push_base(local_sha: str, remote_sha: str, remote_name: str, zero_shas: set[str]) -> str | None:
    """The commit a pushed ref update should be compared against, or `None` when there is none.

    For an existing remote ref that is the remote's own tip. For a ref the remote does not
    have yet, it is the parent of the oldest commit this push actually adds (every commit
    already reachable from another ref of the same remote is excluded), so history the
    remote already carries is never rescanned; a root commit is compared against git's
    empty tree.
    """
    if remote_sha not in zero_shas:
        return remote_sha
    listed = git("rev-list", local_sha, "--not", f"--remotes={remote_name}")
    if listed.returncode != 0:
        return None
    commits = listed.stdout.split()
    if not commits:
        return None
    oldest = commits[-1]
    parent = git("rev-parse", "--verify", "--quiet", f"{oldest}^")
    return parent.stdout.strip() if parent.returncode == 0 and parent.stdout.strip() else EMPTY_TREE


def range_skip_match(base: str, tip: str) -> str | None:
    """The first file a push introduces a test-skip pattern in, between `base` and `tip`."""
    result = git("diff", "--unified=0", base, tip)
    if result.returncode != 0:
        return None
    return added_skip_file(result.stdout)
