#!/usr/bin/env python3
"""Gantry Plan: Socratic Gate planning engine and tracer-bullet vertical slicing.

Dual entry modes:
1. Free-text goal: Socratic Gate interview -> repo context exploration -> spec synthesis.
2. Existing spec: Structural validation -> tracer-bullet vertical slicing -> budget audit -> Plan Critic -> operator quiz.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# Support direct execution and relative import
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import common
import spec
import runlog


def generate_slug(goal: str) -> str:
    """Generate a clean URL/file-friendly slug from a free-text goal."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", goal).strip().lower()
    slug = re.sub(r"[\s_]+", "-", cleaned)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "feature"
    stop_words = {"a", "an", "the", "for", "to", "in", "of", "and", "with", "add", "create", "implement", "build", "data"}
    words = [w for w in slug.split("-") if w not in stop_words]
    if not words:
        words = slug.split("-")
    return "-".join(words[:5])


def explore_context(repo_root: Path) -> dict:
    """Survey repository context to ground Socratic questions and architecture."""
    context_doc = repo_root / "CONTEXT.md"
    prd_doc = repo_root / "PRD.md"
    adr_dir = repo_root / "docs" / "adr"

    glossary = {}
    if context_doc.exists():
        text = context_doc.read_text(encoding="utf-8")
        for match in re.finditer(r"^([A-Za-z0-9_-]+):\s*(.+)$", text, re.MULTILINE):
            glossary[match.group(1)] = match.group(2).strip()

    adrs = []
    if adr_dir.exists():
        adrs = sorted([f.name for f in adr_dir.glob("*.md")])

    modules = []
    for candidate in (repo_root / "scripts", repo_root / ".agents" / "skills"):
        if candidate.exists():
            for item in candidate.iterdir():
                if item.is_dir() or item.suffix in {".py", ".ts", ".js"}:
                    modules.append(item.name)

    return {
        "has_context_doc": context_doc.exists(),
        "has_prd": prd_doc.exists(),
        "glossary": glossary,
        "adrs": adrs,
        "modules": modules,
    }


class SocraticGateEngine:
    """Socratic Gate engine for transforming free-text goals into validated specs."""

    def __init__(
        self,
        goal: str,
        repo_root: Path | None = None,
        unit_id: str | None = None,
        run_id: str | None = None,
        state_root: Path | None = None,
    ) -> None:
        self.goal = goal.strip()
        self.repo_root = Path(repo_root).resolve() if repo_root else common.repo_root().resolve()
        self.slug = generate_slug(self.goal)
        self.context = explore_context(self.repo_root)
        self.unit_id = unit_id
        self.run_id = run_id
        self.state_root = Path(state_root).resolve() if state_root else None

    def get_interview_phases(self) -> list[dict]:
        """Generate structured interview questions across four design phases."""
        goal_title = self.goal.capitalize()
        return [
            {
                "name": "Problem Statement & Context",
                "questions": [
                    {
                        "id": "problem_core",
                        "question": f"What specific problem does '{self.goal}' solve for the operator or developer?",
                        "recommended_answer": f"Enables automated, deterministic handling of {self.goal.lower()} without manual overhead.",
                    },
                    {
                        "id": "problem_current_state",
                        "question": "What is the current state in the repository regarding this capability?",
                        "recommended_answer": "Currently absent or requires manual developer interaction in terminal sessions.",
                    },
                ],
            },
            {
                "name": "Architectural Boundaries & Seams",
                "questions": [
                    {
                        "id": "arch_module",
                        "question": f"Where does the logic for '{self.slug}' reside in relation to existing modules?",
                        "recommended_answer": "Implemented as a dedicated standalone script or module adhering to standard library constraints.",
                    },
                    {
                        "id": "arch_contract",
                        "question": "What contracts (CLI flags, JSON envelopes, or APIs) define this boundary?",
                        "recommended_answer": "CLI supporting standard flags (--json, --help) and returning structured exit codes.",
                    },
                ],
            },
            {
                "name": "Scope & Non-Goals",
                "questions": [
                    {
                        "id": "scope_in",
                        "question": f"What is strictly inside the scope of '{self.slug}'?",
                        "recommended_answer": f"Core execution, verification gates, and telemetry integration for {self.goal.lower()}.",
                    },
                    {
                        "id": "scope_out",
                        "question": "What is explicitly out of scope for this vertical iteration?",
                        "recommended_answer": "Third-party cloud dependencies, distributed multi-tenant hosting, or unrelated refactoring.",
                    },
                ],
            },
            {
                "name": "Verifiable Criteria & Scenarios",
                "questions": [
                    {
                        "id": "criteria_verification",
                        "question": "How will delivery be objectively verified before operator acceptance?",
                        "recommended_answer": "Passing automated unit tests, quality gates, and end-to-end integration proof.",
                    },
                    {
                        "id": "criteria_scenarios",
                        "question": "What primary Gherkin scenario proves completion?",
                        "recommended_answer": f"Given repository context, When the operator runs {self.slug}, Then expected results are verified.",
                    },
                ],
            },
        ]

    def log_operator_pause(self, activity: str = "Socratic Interview") -> None:
        """Record milestone phase.started event in Run log with operatorWaiting=true."""
        if not self.unit_id or not self.run_id:
            return
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run": self.run_id,
            "event": "phase.started",
            "issue": f"{self.slug}#00",
            "phase": "Plan",
            "data": {
                "operatorWaiting": True,
                "activity": activity,
            },
        }
        state_root = self.state_root or runlog.default_state_root()
        log_path = runlog.run_log_path(state_root, self.unit_id, self.run_id)
        runlog.append_event(log_path, event)

    def log_operator_response(self) -> None:
        """Record operator.approved event in Run log clearing operatorWaiting."""
        if not self.unit_id or not self.run_id:
            return
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run": self.run_id,
            "event": "operator.approved",
            "issue": f"{self.slug}#00",
            "data": {
                "operatorWaiting": False,
            },
        }
        state_root = self.state_root or runlog.default_state_root()
        log_path = runlog.run_log_path(state_root, self.unit_id, self.run_id)
        runlog.append_event(log_path, event)

    def synthesize_spec(
        self,
        context: str,
        architecture: str,
        constraints: str,
        criteria: list[str],
        guardrails: list[str],
        scenarios: list[dict],
        out_of_scope: list[str],
        date_str: str | None = None,
    ) -> str:
        """Synthesize a complete living-spec Markdown conforming to spec.py --check."""
        today = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        title = self.goal.capitalize()

        criteria_lines = "\n".join(f"- [ ] {c}" for c in criteria)
        guardrails_lines = "\n".join(f"- {g}" for g in guardrails)
        scope_lines = "\n".join(f"- {s}" for s in out_of_scope)

        scenario_blocks = []
        for s in scenarios:
            scenario_blocks.append(
                f"Scenario: {s.get('title', 'Validate ' + self.slug)}\n"
                f"  Given {s.get('given', 'the repository environment')}\n"
                f"  When {s.get('when', 'the command is executed')}\n"
                f"  Then {s.get('then', 'the expected behavior is verified')}"
            )
        gherkin_text = "\n\n".join(scenario_blocks)

        return f"""# Spec: {title}

Type: spec
Status: draft
Map: `ROADMAP.md` (spec NN)
Source: Socratic Gate session
Created: {today}

## Blueprint

### Context

{context.strip()}

### Architecture

{architecture.strip()}

### Constraints

{constraints.strip()}

## Contract

### Definition of Done

{criteria_lines}

### Regression Guardrails

{guardrails_lines}

### Scenarios

```gherkin
{gherkin_text}
```

## Out of Scope

{scope_lines}

## Changelog

- {today} — Initial draft synthesized by gantry-plan Socratic Gate.
"""

    def write_spec(self, content: str) -> Path:
        """Write spec to .scratch/<slug>/spec.md."""
        spec_dir = self.repo_root / ".scratch" / self.slug
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / "spec.md"
        spec_path.write_text(content, encoding="utf-8")
        return spec_path


class SlicingEngine:
    """Tracer-bullet vertical slicing engine adhering to to-issues principles."""

    def __init__(self, spec_path: Path, repo_root: Path | None = None) -> None:
        self.spec_path = Path(spec_path).resolve()
        self.repo_root = Path(repo_root).resolve() if repo_root else common.repo_root().resolve()
        # Derive slug from directory or spec filename
        if self.spec_path.parent.name and self.spec_path.parent.name != ".scratch":
            self.slug = self.spec_path.parent.name
        else:
            self.slug = self.spec_path.stem

    def validate_spec(self) -> None:
        """Ensure input spec passes structural validation."""
        check = spec.validate(self.spec_path, self.repo_root)
        if not check.get("valid"):
            errors = check.get("errors", [])
            raise ValueError(f"Spec validation failed for {self.spec_path}: {'; '.join(errors)}")

    def slice(self) -> list[dict]:
        """Decompose spec into vertical tracer bullets with prefactoring identified first."""
        self.validate_spec()
        spec_text = self.spec_path.read_text(encoding="utf-8")

        # Extract title
        title_match = re.search(r"^#\s+Spec:\s*(.+)$", spec_text, re.MULTILINE)
        feature_title = title_match.group(1).strip() if title_match else self.slug

        # Extract Definition of Done criteria
        dod_matches = re.findall(r"^\s*-\s*\[\s*\]\s*(.+)$", spec_text, re.MULTILINE)
        criteria_list = dod_matches if dod_matches else [f"Implement core capabilities for {feature_title}"]

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        issues = []

        # Slice 01: Always prefactoring / foundation
        prefactor_title = f"Prefactor and foundation seams for {feature_title}"
        issues.append({
            "slice": f"{self.slug}#01",
            "number": 1,
            "title": prefactor_title,
            "is_prefactor": True,
            "spec_path": str(self.spec_path.relative_to(self.repo_root)),
            "parent": self.slug,
            "what_to_build": (
                f"Establish necessary abstractions, module seams, and shared foundation for {feature_title}. "
                "Ensure test harnesses and interfaces are ready before vertical implementation."
            ),
            "files_to_read": [
                f".scratch/{self.slug}/spec.md",
                "CONTEXT.md",
            ],
            "criteria": [
                f"Foundation modules and seams for {self.slug} are defined and importable",
                "Base unit test suite passes cleanly",
            ],
            "blocked_by": [],
            "created": today,
        })

        # Slice 02..N: Vertical tracer-bullet slices
        # Group criteria into chunks of 2-3 per issue
        chunk_size = 2
        slice_num = 2
        for i in range(0, len(criteria_list), chunk_size):
            chunk = criteria_list[i:i + chunk_size]
            slice_ref = f"{self.slug}#{slice_num:02d}"
            primary_criterion = chunk[0]
            slice_title = primary_criterion[:70].strip()

            issues.append({
                "slice": slice_ref,
                "number": slice_num,
                "title": slice_title,
                "is_prefactor": False,
                "spec_path": str(self.spec_path.relative_to(self.repo_root)),
                "parent": self.slug,
                "what_to_build": (
                    f"Implement vertical end-to-end tracer bullet delivering: {'; '.join(chunk)}. "
                    "Cut across API/CLI, business logic, persistence, and tests."
                ),
                "files_to_read": [
                    f".scratch/{self.slug}/spec.md",
                    f".scratch/{self.slug}/issues/01-{self.slug}.md",
                ],
                "criteria": chunk,
                "blocked_by": [f"{self.slug}#01"],
                "created": today,
            })
            slice_num += 1

        return issues

    def write_issues(self, issues: list[dict]) -> list[Path]:
        """Write issue files under .scratch/<slug>/issues/NN-<slug>.md."""
        issues_dir = self.repo_root / ".scratch" / self.slug / "issues"
        issues_dir.mkdir(parents=True, exist_ok=True)
        written = []

        for item in issues:
            num = item["number"]
            filename = f"{num:02d}-{self.slug}.md"
            target = issues_dir / filename

            files_read_text = "\n".join(f"- `{f}`" for f in item["files_to_read"])
            criteria_text = "\n".join(f"- [ ] {c}" for c in item["criteria"])
            blocked_by_text = "\n".join(f"- {b}" for b in item["blocked_by"]) if item["blocked_by"] else "- None"

            content = f"""# {item['title']}

Type: issue
Status: draft
Slice: `{item['slice']}`
Spec: `{item['spec_path']}`
Created: {item['created']}

## Parent

`{item['parent']}`

## What to build

{item['what_to_build']}

### Files to read

{files_read_text}

## Acceptance criteria

{criteria_text}

## Blocked by

{blocked_by_text}
"""
            target.write_text(content, encoding="utf-8")
            written.append(target)

        return written

    def audit_budgets(self, issues: list[dict]) -> list[dict]:
        """Estimate context tokens for each slice based on files to read."""
        results = []
        for issue in issues:
            total_chars = 0
            for rel_path in issue.get("files_to_read", []):
                file_path = self.repo_root / rel_path
                if file_path.exists():
                    total_chars += len(file_path.read_text(encoding="utf-8", errors="ignore"))
                else:
                    total_chars += 500  # Conservative estimate
            tokens = total_chars // 4
            over_budget = tokens > 30000  # Default safe context share
            results.append({
                "slice": issue["slice"],
                "tokens": tokens,
                "over_budget": over_budget,
            })
        return results

    def audit_plan_critic(self, issues: list[dict]) -> dict:
        """Adversarial check of verticality, criteria observability, and DAG acyclicity."""
        problems = []
        graph = {}

        for item in issues:
            ref = item["slice"]
            graph[ref] = item.get("blocked_by", [])

            # Check criteria
            criteria = item.get("criteria", [])
            if not criteria:
                problems.append(f"{ref} has no acceptance criteria")

            # Check horizontal slicing smell
            title = item.get("title", "").lower()
            if "database only" in title or "styling only" in title or "frontend only" in title:
                problems.append(f"{ref} appears to be horizontally sliced: '{item['title']}'")

        # DAG cycle check (Kahn's algorithm)
        in_degree = {n: 0 for n in graph}
        for n in graph:
            for dep in graph[n]:
                if dep in in_degree:
                    in_degree[n] += 1

        queue = [n for n, deg in in_degree.items() if deg == 0]
        visited_count = 0
        while queue:
            node = queue.pop(0)
            visited_count += 1
            for other, deps in graph.items():
                if node in deps:
                    in_degree[other] -= 1
                    if in_degree[other] == 0:
                        queue.append(other)

        is_dag = (visited_count == len(graph))
        if not is_dag:
            problems.append("Cyclic dependency detected in issue blocker graph")

        return {
            "acceptable": len(problems) == 0,
            "problems": problems,
            "is_dag": is_dag,
        }

    def generate_operator_quiz(self, issues: list[dict]) -> list[dict]:
        """Generate interactive quiz for operator reviewing issue breakdown."""
        return [
            {
                "topic": "granularity",
                "question": f"The spec is sliced into {len(issues)} issues. Does this level of granularity feel appropriate for single-round TDD deliveries?",
                "recommended_answer": "Yes, each slice represents a demonstrable increment.",
            },
            {
                "topic": "dependency_order",
                "question": "Prefactoring is scheduled in Slice 01, with remaining slices depending on it. Does this dependency sequence align with your delivery preferences?",
                "recommended_answer": "Yes, prefactoring first reduces risk for subsequent slices.",
            },
            {
                "topic": "split_merge",
                "question": "Are there any specific slices you would like to split further into separate tasks, or merge together before finalizing?",
                "recommended_answer": "Breakdown looks solid as proposed.",
            },
        ]


def approve_plan(
    slug: str,
    repo_root: Path | None = None,
    unit_id: str | None = None,
    run_id: str | None = None,
    state_root: Path | None = None,
) -> dict:
    """Transition approved draft issues to ready-for-agent and update roadmap waves."""
    repo = Path(repo_root).resolve() if repo_root else common.repo_root().resolve()
    issue_dir = repo / ".scratch" / slug / "issues"
    if not issue_dir.exists():
        raise FileNotFoundError(f"Issue directory not found: {issue_dir}")

    updated_issues = []
    for issue_file in sorted(issue_dir.glob("*.md")):
        parsed = common.parse_issue(issue_file)
        ref = parsed.ref
        if not ref:
            continue
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "roadmap.py"), "status", ref, "ready-for-agent"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(f"Failed to update status for {ref}: {res.stderr or res.stdout}")
        updated_issues.append(ref)

    res_waves = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "roadmap.py"), "waves", "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if res_waves.returncode != 0:
        raise RuntimeError(f"Failed to recompute waves: {res_waves.stderr or res_waves.stdout}")
    waves_info = json.loads(res_waves.stdout) if res_waves.stdout else {}

    res_check = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "roadmap.py"), "check", "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if res_check.returncode != 0:
        raise RuntimeError(f"Roadmap check failed after updating waves: {res_check.stderr or res_check.stdout}")

    if unit_id and run_id:
        root_state = Path(state_root).resolve() if state_root else runlog.default_state_root()
        log_path = runlog.run_log_path(root_state, unit_id, run_id)
        done_event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run": run_id,
            "event": "issue.done",
            "issue": f"{slug}#00",
            "phase": "Plan",
            "data": {
                "status": "ready-for-agent",
                "issues": updated_issues,
            },
        }
        runlog.append_event(log_path, done_event)

    return {
        "slug": slug,
        "updated_issues": updated_issues,
        "waves": waves_info,
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Gantry Plan: Socratic Gate and vertical slicing.")
    parser.add_argument("--goal", type=str, help="Free-text goal for Socratic Gate planning")
    parser.add_argument("--spec", type=str, help="Path to spec for vertical slicing")
    parser.add_argument("--check-spec", type=str, help="Check spec validity")
    parser.add_argument("--approve", type=str, help="Approve plan and transition issues to ready-for-agent for a spec slug")
    parser.add_argument("--unit-id", type=str, help="Run log unit ID")
    parser.add_argument("--run-id", type=str, help="Run log run ID")
    parser.add_argument("--state-root", type=str, help="Run log state root")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    repo = common.repo_root()

    if args.approve:
        res = approve_plan(
            args.approve,
            repo_root=repo,
            unit_id=args.unit_id,
            run_id=args.run_id,
            state_root=Path(args.state_root) if args.state_root else None,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Plan approved for {res['slug']}: {len(res['updated_issues'])} issues set to ready-for-agent.")
        return 0

    if args.check_spec:
        res = spec.validate(Path(args.check_spec), repo)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("Valid" if res.get("valid") else f"Invalid: {res.get('errors')}")
        return 0 if res.get("valid") else 1

    if args.goal:
        engine = SocraticGateEngine(args.goal, repo_root=repo)
        phases = engine.get_interview_phases()
        if args.json:
            print(json.dumps({"slug": engine.slug, "phases": phases}, indent=2))
        else:
            print(f"Socratic Gate Plan initialized for: {engine.slug}")
            for p in phases:
                print(f"\n--- {p['name']} ---")
                for q in p["questions"]:
                    print(f"Q: {q['question']}")
                    print(f"  Recommended: {q['recommended_answer']}")
        return 0

    if args.spec:
        slicer = SlicingEngine(Path(args.spec), repo_root=repo)
        issues = slicer.slice()
        written = slicer.write_issues(issues)
        critic = slicer.audit_plan_critic(issues)
        if args.json:
            print(json.dumps({
                "slug": slicer.slug,
                "issues": issues,
                "filesWritten": [str(p) for p in written],
                "critic": critic,
            }, indent=2))
        else:
            print(f"Sliced {len(issues)} issues for {slicer.slug}:")
            for p in written:
                print(f"  - {p.name}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
