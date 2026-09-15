# Configure Caveman in setup and use it in the coordinating agent

Type: issue
Status: ready-for-agent
Slice: `caveman-setup#01`
Spec: `.scratch/caveman-setup/spec.md`
Created: 2026-09-15

## Parent

`caveman-setup`

## What to build

Offer Caveman lite as a recommended, explicitly confirmed repository preference. Guide the user through installing the external skill themselves and verify host-harness discovery after reported installation. Carry the effective preference into Run preflight and use the available skill for the coordinating agent's conversational messages and summaries. Provide a shared resolved activation contract that subsequent role slices can consume, with normal-behavior fallback and a warning emitted at most once per Run.

### Files to read

- `.agents/skills/gantry-setup/SKILL.md`
- `.agents/skills/gantry/SKILL.md`
- `.agents/skills/gantry/scripts/common.py`
- `.agents/skills/gantry/scripts/setup.py`
- `tests/test_gantry_setup.py`
- `tests/test_common_policy.py`

## Acceptance criteria

- [ ] Setup explains conversational scope, user-managed installation, fallback and variable savings; declining or skipping a new preference resolves to disabled.
- [ ] The existing setup writer persists one explicitly confirmed repository preference, preserves unrelated settings and existing preferences on repeated setup, and supports explicit disabling.
- [ ] Installation guidance uses a verified upstream skill-only command appropriate to the host harness; Gantry runs no installer, vendors no skill and changes no global agent configuration.
- [ ] After reported installation, setup verifies host-harness discovery and readability rather than relying on the user's claim or a package-manager exit code.
- [ ] Run preflight re-evaluates availability, applies external Caveman lite to the coordinating agent when supported, and makes resolved preference, activation scope and warning state available to both reference workflows without storing machine availability or paths in repository policy.
- [ ] Unavailable or unsupported activation continues normally with at most one actionable warning per Run and no false activation claim; a disabled preference does not load the skill.
- [ ] Fixture and setup transcript tests verify confirmation, persistence, environment changes, coordinating-agent instructions, fallback and warning deduplication without installing Caveman globally or calling a paid model.
- [ ] Documentation describes opt-in, manual installation and fallback; artifacts, exact commands/errors, contracts and approval rules retain required content.

## Blocked by

- `gantry-migration#10`
- `gantry-migration#02`

## Comments

- 2026-09-15 — Operator approved this three-slice breakdown; publication does not start implementation. Issues 02 and 03 may proceed concurrently after 01; keep edits to shared coordinating instructions in 01 and role-specific changes in their respective workflows.

