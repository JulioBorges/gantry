# Canonical Gantry workflow skill

Type: issue
Status: ready-for-agent
Slice: `gantry-migration#02`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Create the canonical `.agents/skills/gantry/` skill by moving the portable legacy loop into `.agents/skills/gantry/SKILL.md`, `reference/plan-workflow.md`, `reference/round-workflow.md`, and `scripts/{common,frontier,acceptance,gates,roadmap}.py`. Add the default `templates/{spec,prd,issue}.md` used by the workflow. The new skill must retain the proven frontier, TDD implementation, two-axis review, adversarial critic, serial integration, and roadmap-authority behavior while `asdlc` remains available during migration.

## Acceptance criteria

- [ ] `.agents/skills/gantry/SKILL.md` has accepted skill frontmatter and documents a harness-neutral invocation that resolves `skillDir`, repository root, and effective policy without a repository policy file; its proof test runs the new `frontier.py`, `acceptance.py`, `gates.py`, and `roadmap.py` help or JSON paths.
- [ ] The canonical plan and round templates preserve the legacy behavior: drafts stop for operator approval, implementation follows TDD, review has standards and Spec axes, the Critic is the only path to `roadmap.py done`, and parallel Issues use isolated worktrees with serial integration.
- [ ] A planning-state test proves draft Issue creation does not modify `ROADMAP.md`; after explicit operator approval, the runner calls `roadmap.py status <ref> ready-for-agent`, then `roadmap.py waves`, and `roadmap.py check` exits 0 with the generated Issue projection.
- [ ] Frontier regression tests prove the canonical script refuses cyclic and dangling blocker references with exit 1, lists draft, blocked, and needs-operator Issues as parked rather than scheduling them, and computes valid dependency rounds from authoritative Issue statuses.
- [ ] The three default templates contain the required Spec, PRD, and current Issue structures, and tests show the copied scripts continue parsing legacy-format Issue files without changing their execution state.
- [ ] The Spec Changelog receives an English entry in the same merge, and every Python module added under `.agents/skills/gantry/scripts/` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#01` — consumes the portable policy contract and de-hardcoded legacy workflow.

## Comments
