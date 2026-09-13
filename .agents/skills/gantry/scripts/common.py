"""Shared parsing and policy helpers for the Gantry workflow scripts."""
from __future__ import annotations

import copy
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_POLICY = {
    "artifacts": {
        "specs": ".scratch/{slug}/spec.md",
        "issues": ".scratch/{slug}/issues",
        "adrs": "docs/adr",
        "decisions": "docs/adr",
        "context": "CONTEXT.md",
        "issueTracker": "docs/agents/issue-tracker.md",
    },
    "templates": {"dir": ".gantry/templates", "headingMap": {}},
    "checks": [],
    "git": {"target": "main", "prefix": "gantry/"},
    "hooks": {"record": [], "deny": []},
    "budget": {"corrections": 2, "contextShare": 0.15},
    "dashboard": {"staleAfterSeconds": 900},
}

REF_RE = re.compile(r"`?([a-z0-9][a-z0-9-]*)#(\d{2,})`?")
STATUS_RE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
SLICE_RE = re.compile(r"^Slice:\s*`?([a-z0-9-]+#\d+)`?\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^(\s*)- \[( |x|X)\]\s+(.*)$")
ISSUE_FILE_RE = re.compile(r"^(\d{2,})-[a-z0-9-]+\.md$")
DONE_STATUSES = {"done"}
PARKED_STATUSES = {"blocked", "needs-operator", "draft"}


def repo_root(start: Path | None = None) -> Path:
    """Find the enclosing repository, including linked worktrees."""
    path = (start or Path.cwd()).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return candidate
    return path


def _merge_policy(base: dict, overlay: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        result[key] = _merge_policy(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else copy.deepcopy(value)
    return result


def resolve_policy(root: Path | None = None) -> dict:
    """Overlay optional repository policy onto portable pack defaults."""
    root = repo_root(root)
    path = root / ".gantry" / "config.json"
    if not path.exists():
        return copy.deepcopy(DEFAULT_POLICY)
    try:
        overlay = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(overlay, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return _merge_policy(DEFAULT_POLICY, overlay)


def resolve_workflow_paths(root: Path, slug: str) -> dict[str, Path]:
    """Render the effective policy's repository paths for a workflow run."""
    root = repo_root(root)
    artifacts = resolve_policy(root)["artifacts"]

    def render(name: str) -> Path:
        return root / artifacts[name].format(slug=slug)

    issue_dir = render("issues")
    existing = sorted(issue_dir.glob("*.md"))
    return {
        "specPath": render("specs"),
        "issueDir": issue_dir,
        "exemplarIssue": existing[0] if existing else render("issueTracker"),
        "decisions": render("decisions"),
        "issueTracker": render("issueTracker"),
        "context": render("context"),
        "adrs": render("adrs"),
    }


def section(text: str, heading: str) -> str:
    """Return a level-two Markdown section body."""
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    rest = text[match.end():]
    next_heading = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[:next_heading.start()] if next_heading else rest


@dataclass
class Criterion:
    index: int
    text: str
    checked: bool
    line_no: int


@dataclass
class Issue:
    ref: str
    spec: str
    number: int
    path: Path
    title: str
    status: str
    blocked_by: list[str] = field(default_factory=list)
    criteria: list[Criterion] = field(default_factory=list)

    @property
    def done(self) -> bool:
        return self.status.lower() in DONE_STATUSES

    @property
    def parked(self) -> bool:
        return self.status.lower() in PARKED_STATUSES

    def to_dict(self, root: Path) -> dict:
        return {
            "ref": self.ref, "spec": self.spec, "number": self.number,
            "path": str(self.path.relative_to(root)), "title": self.title,
            "status": self.status, "blocked_by": self.blocked_by,
            "criteria_total": len(self.criteria),
            "criteria_checked": sum(criterion.checked for criterion in self.criteria),
        }


def parse_criteria(text: str) -> list[Criterion]:
    body = section(text, "Acceptance criteria")
    if not body:
        return []
    start_line = text[:text.index(body)].count("\n")
    criteria: list[Criterion] = []
    for offset, line in enumerate(body.splitlines()):
        match = CHECKBOX_RE.match(line)
        if match:
            criteria.append(Criterion(len(criteria) + 1, match.group(3).strip(), match.group(2).lower() == "x", start_line + offset + 1))
    return criteria


def parse_blocked_by(text: str, own_spec: str) -> list[str]:
    refs: list[str] = []
    for line in section(text, "Blocked by").splitlines():
        if line.strip().startswith("-"):
            for spec, number in REF_RE.findall(line):
                ref = f"{spec}#{int(number):02d}"
                if ref not in refs:
                    refs.append(ref)
    return refs


def parse_issue(path: Path) -> Issue:
    path = path.resolve()
    text = path.read_text(encoding="utf-8")
    spec = path.parent.parent.name
    file_match = ISSUE_FILE_RE.match(path.name)
    number = int(file_match.group(1)) if file_match else 0
    ref_match = SLICE_RE.search(text)
    raw_ref = ref_match.group(1) if ref_match else f"{spec}#{number:02d}"
    ref_spec, raw_number = raw_ref.split("#")
    ref = f"{ref_spec}#{int(raw_number):02d}"
    title = TITLE_RE.search(text)
    status = STATUS_RE.search(text)
    return Issue(ref, ref_spec, int(raw_number), path, title.group(1) if title else path.stem,
                 status.group(1) if status else "unknown", parse_blocked_by(text, ref_spec), parse_criteria(text))


def load_issues(scratch: Path) -> dict[str, Issue]:
    issues: dict[str, Issue] = {}
    for directory in sorted(scratch.glob("*/issues")):
        for path in sorted(directory.glob("*.md")):
            if ISSUE_FILE_RE.match(path.name):
                issue = parse_issue(path)
                issues[issue.ref] = issue
    return issues


def normalise_ref(raw: str) -> str | None:
    match = REF_RE.fullmatch(raw.strip().strip("`"))
    return f"{match.group(1)}#{int(match.group(2)):02d}" if match else None


def resolve_issue_arg(arg: str, root: Path, issues: dict[str, Issue]) -> Issue | None:
    ref = normalise_ref(arg)
    if ref and ref in issues:
        return issues[ref]
    path = Path(arg)
    path = path if path.is_absolute() else root / path
    return parse_issue(path) if path.exists() else None


def roadmap_waves(roadmap_text: str) -> dict[int, list[str]]:
    waves: dict[int, list[str]] = {}
    current: int | None = None
    for line in roadmap_text.splitlines():
        match = re.match(r"^###\s+Wave\s+(\d+)", line)
        if match:
            current = int(match.group(1))
            waves.setdefault(current, [])
            continue
        item = re.match(r"^- \[( |x|X)\] \*\*`([a-z0-9-]+#\d+)`\*\*", line)
        if item and current is not None:
            spec, number = item.group(2).split("#")
            waves[current].append(f"{spec}#{int(number):02d}")
    return waves


def spec_numbers(scratch: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for spec in sorted(scratch.glob("*/spec.md")):
        match = re.search(r"\(spec\s+(\d+)", spec.read_text(encoding="utf-8"))
        if match:
            result[spec.parent.name] = int(match.group(1))
    return result


def issue_levels(issues: dict[str, Issue]) -> dict[str, int]:
    levels: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(ref: str) -> int:
        if ref in levels:
            return levels[ref]
        if ref in visiting:
            raise ValueError(f"dependency cycle through {ref}")
        visiting.add(ref)
        blockers = [blocker for blocker in issues[ref].blocked_by if blocker in issues]
        levels[ref] = 0 if not blockers else 1 + max(depth(blocker) for blocker in blockers)
        visiting.remove(ref)
        return levels[ref]

    for reference in sorted(issues):
        depth(reference)
    return levels


def main() -> int:
    """Print the portable policy and rendered workflow paths."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--cwd", default=".", help="repository or worktree to inspect")
    parser.add_argument("--scope-slug", default="sample", help="slug used to render artifact paths")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = repo_root(Path(args.cwd))
    paths = resolve_workflow_paths(root, args.scope_slug)
    payload = {
        "repo_root": str(root),
        "policy": resolve_policy(root),
        "paths": {name: str(path) for name, path in paths.items()},
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"repo_root: {payload['repo_root']}")
        for name, path in payload["paths"].items():
            print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
