"""Shared parsing helpers for the ASDLC scripts.

Conventions come from docs/agents/issue-tracker.md and AGENTS.md:
- issues live at .scratch/<spec-slug>/issues/NN-<slug>.md
- an issue reference is written `<spec-slug>#NN`
- `Status:` line near the top of the file is authoritative
- `## Blocked by` lists `- `<spec-slug>#NN` — reason` lines, or "None ..."
- `## Acceptance criteria` lists `- [ ]` / `- [x]` items
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REF_RE = re.compile(r"`?([a-z0-9][a-z0-9-]*)#(\d{2,})`?")
STATUS_RE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
SLICE_RE = re.compile(r"^Slice:\s*`?([a-z0-9-]+#\d+)`?\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^(\s*)- \[( |x|X)\]\s+(.*)$")
ISSUE_FILE_RE = re.compile(r"^(\d{2,})-[a-z0-9-]+\.md$")

DONE_STATUSES = {"done"}
# Parked issues are never scheduled: an operator has to act before they can move again.
PARKED_STATUSES = {"blocked", "needs-operator", "draft"}


def repo_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / ".git").exists():
            return candidate
    return p


def section(text: str, heading: str) -> str:
    """Return the body of `## <heading>` up to the next `## ` heading (or EOF)."""
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(r"^##\s+", rest, re.MULTILINE)
    return rest[: n.start()] if n else rest


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
            "ref": self.ref,
            "spec": self.spec,
            "number": self.number,
            "path": str(self.path.relative_to(root)),
            "title": self.title,
            "status": self.status,
            "blocked_by": self.blocked_by,
            "criteria_total": len(self.criteria),
            "criteria_checked": sum(1 for c in self.criteria if c.checked),
        }


def parse_criteria(text: str) -> list[Criterion]:
    body = section(text, "Acceptance criteria")
    if not body:
        return []
    # Map body lines back to absolute line numbers for editing.
    start_line = text[: text.index(body)].count("\n")
    out: list[Criterion] = []
    for offset, line in enumerate(body.splitlines()):
        m = CHECKBOX_RE.match(line)
        if m:
            out.append(Criterion(len(out) + 1, m.group(3).strip(), m.group(2).lower() == "x", start_line + offset + 1))
    return out


def parse_blocked_by(text: str, own_spec: str) -> list[str]:
    body = section(text, "Blocked by")
    refs: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        for spec, num in REF_RE.findall(line):
            ref = f"{spec}#{int(num):02d}"
            if ref not in refs:
                refs.append(ref)
    return refs


def parse_issue(path: Path) -> Issue:
    text = path.read_text(encoding="utf-8")
    spec = path.parent.parent.name
    m = ISSUE_FILE_RE.match(path.name)
    number = int(m.group(1)) if m else 0
    sm = SLICE_RE.search(text)
    ref = sm.group(1) if sm else f"{spec}#{number:02d}"
    # normalise NN width
    s, n = ref.split("#")
    ref = f"{s}#{int(n):02d}"
    title_m = TITLE_RE.search(text)
    status_m = STATUS_RE.search(text)
    return Issue(
        ref=ref,
        spec=s,
        number=int(n),
        path=path,
        title=title_m.group(1) if title_m else path.stem,
        status=status_m.group(1) if status_m else "unknown",
        blocked_by=parse_blocked_by(text, s),
        criteria=parse_criteria(text),
    )


def load_issues(scratch: Path) -> dict[str, Issue]:
    issues: dict[str, Issue] = {}
    for issues_dir in sorted(scratch.glob("*/issues")):
        for f in sorted(issues_dir.glob("*.md")):
            if not ISSUE_FILE_RE.match(f.name):
                continue
            issue = parse_issue(f)
            issues[issue.ref] = issue
    return issues


def normalise_ref(raw: str) -> str | None:
    m = REF_RE.fullmatch(raw.strip().strip("`"))
    if not m:
        return None
    return f"{m.group(1)}#{int(m.group(2)):02d}"


def resolve_issue_arg(arg: str, root: Path, issues: dict[str, Issue]) -> Issue | None:
    """Accept `spec#NN` or a path to an issue file."""
    ref = normalise_ref(arg)
    if ref and ref in issues:
        return issues[ref]
    p = Path(arg)
    if not p.is_absolute():
        p = root / p
    if p.exists():
        return parse_issue(p)
    return None


def roadmap_waves(roadmap_text: str) -> dict[int, list[str]]:
    """Map wave number -> issue refs listed under each `### Wave N` heading of ROADMAP.md."""
    waves: dict[int, list[str]] = {}
    current: int | None = None
    for line in roadmap_text.splitlines():
        wm = re.match(r"^###\s+Wave\s+(\d+)", line)
        if wm:
            current = int(wm.group(1))
            waves.setdefault(current, [])
            continue
        im = re.match(r"^- \[( |x|X)\] \*\*`([a-z0-9-]+#\d+)`\*\*", line)
        if im and current is not None:
            spec, num = im.group(2).split("#")
            waves[current].append(f"{spec}#{int(num):02d}")
    return waves


SPEC_NUMBER_RE = re.compile(r"\(spec\s+(\d+)")


def spec_numbers(scratch: Path) -> dict[str, int]:
    """Spec slug -> number, from the `Map: … (spec NN, …)` line of each spec.md."""
    out: dict[str, int] = {}
    for spec_md in sorted(scratch.glob("*/spec.md")):
        m = SPEC_NUMBER_RE.search(spec_md.read_text(encoding="utf-8"))
        if m:
            out[spec_md.parent.name] = int(m.group(1))
    return out


def issue_levels(issues: dict[str, Issue]) -> dict[str, int]:
    """Longest-path depth of every issue over the blocker graph. Raises on a cycle."""
    level: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(ref: str) -> int:
        if ref in level:
            return level[ref]
        if ref in visiting:
            raise ValueError(f"dependency cycle through {ref}")
        visiting.add(ref)
        blockers = [b for b in issues[ref].blocked_by if b in issues]
        level[ref] = 0 if not blockers else 1 + max(depth(b) for b in blockers)
        visiting.discard(ref)
        return level[ref]

    for ref in sorted(issues):
        depth(ref)
    return level
