# Canonical Gantry workflow skill

Type: issue
Status: done
Slice: `gantry-migration#02`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Create the canonical `.agents/skills/gantry/` skill by moving the portable legacy loop into `.agents/skills/gantry/SKILL.md`, `reference/plan-workflow.md`, `reference/round-workflow.md`, and `scripts/{common,frontier,acceptance,gates,roadmap}.py`. Add the default `templates/{spec,prd,issue}.md` used by the workflow. The new skill must retain the proven frontier, TDD implementation, two-axis review, adversarial critic, serial integration, and roadmap-authority behavior while `asdlc` remains available during migration.

## Acceptance criteria

- [x] `.agents/skills/gantry/SKILL.md` has accepted skill frontmatter and documents a harness-neutral invocation that resolves `skillDir`, repository root, and effective policy without a repository policy file; its proof test runs the new `frontier.py`, `acceptance.py`, `gates.py`, and `roadmap.py` help or JSON paths.
- [x] The canonical plan and round templates preserve the legacy behavior: drafts stop for operator approval, implementation follows TDD, review has standards and Spec axes, the Critic is the only path to `roadmap.py done`, and parallel Issues use isolated worktrees with serial integration.
- [x] A planning-state test proves draft Issue creation does not modify `ROADMAP.md`; after explicit operator approval, the runner calls `roadmap.py status <ref> ready-for-agent`, then `roadmap.py waves`, and `roadmap.py check` exits 0 with the generated Issue projection.
- [x] Frontier regression tests prove the canonical script refuses cyclic and dangling blocker references with exit 1, lists draft, blocked, and needs-operator Issues as parked rather than scheduling them, and computes valid dependency rounds from authoritative Issue statuses.
- [x] The three default templates contain the required Spec, PRD, and current Issue structures, and tests show the copied scripts continue parsing legacy-format Issue files without changing their execution state.
- [x] The Spec Changelog receives an English entry in the same merge, and every Python module added under `.agents/skills/gantry/scripts/` passes the standard-library-only import test and its runnable test command.
- [x] The repository declares a real `make test` gate that runs `python3 -m unittest discover -v`; `gates.py --run --diff-base <base>` detects it and reports `verdict: pass`.

## Blocked by

- `gantry-migration#01` — consumes the portable policy contract and de-hardcoded legacy workflow.

## Comments
- 2026-09-13 — Critic refutation after correction budget exhausted: the executable round workflow accepts a Critic result with criteria: [] when complete is true and gatesVerdict is pass, then invokes roadmap.py done. This violates fail-closed adversarial verification because there is no evidence entry for each Issue criterion. Required fix: validate exactly one passing, non-empty evidence entry for every authoritative criterion before integration or roadmap.py done. Worktree: /Users/julioborges/src/personal/gantry-asdlc-gantry-migration. Branch: asdlc/gantry-migration.
- 2026-09-13 — Operator authorized one additional correction after the previous budget was exhausted. Scope is limited to requiring one passing, non-empty evidence entry for every authoritative acceptance criterion before the round workflow can integrate or invoke roadmap.py done.
- 2026-09-13 — Critic refutation after the operator-authorized additional correction: all six acceptance criteria have executable evidence, but gates.py --run --diff-base b8d7146908a26e7f68fc4a8dda2e97e05e7f1492 returns verdict no_gates because this repository declares and detects no gate. The round workflow correctly requires gatesVerdict pass, so this Issue cannot be complete under the fail-closed rule. Required operator decision: declare a real repository gate that runs the canonical suite, then resume and re-verify. Worktree: /Users/julioborges/src/personal/gantry-asdlc-gantry-migration. Branch: asdlc/gantry-migration.
- 2026-09-13 — Operator-approved plan amendment: add a real make test repository gate that runs python3 -m unittest discover -v; gates.py must detect and pass it before this Issue can complete.
