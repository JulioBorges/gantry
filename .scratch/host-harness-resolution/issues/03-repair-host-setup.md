# Apply an approved host-only setup and adapter repair

Type: issue
Status: ready-for-agent
Slice: `host-harness-resolution#03`
Spec: `.scratch/host-harness-resolution/spec.md`
Created: 2026-09-30
User stories covered: 17–21, 24

## Parent

`host-harness-resolution`

## What to build

Let setup consume host diagnosis and propose a targeted repository preference and/or host adapter repair without role presets. Preview concrete policy and adapter effects, apply only operator-approved changes and preserve unrelated configuration. Missing or ignored policy receives normal setup or portability guidance rather than an automatic overwrite. Deliver usage documentation and CLI transcript evidence as part of this behavior.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/setup.py`
- `.agents/skills/gantry/scripts/common.py`
- `.agents/skills/gantry-setup/SKILL.md`
- `tests/test_gantry_setup.py`
- `tests/test_guard_hook_wiring.py`
- `tests/test_role_execution_defaults.py`

## Acceptance criteria

- [ ] Setup CLI previews host-only policy and selected adapter effects before writes; decline, EOF and invalid identity leave files unchanged.
- [ ] Host-only application preserves all base/derived roles, custom model/effort selections, execution extensions, gates, artifacts, Caveman and unknown unrelated fields; malformed policy cannot be silently replaced.
- [ ] Only the selected host's Gantry-owned adapter entries change according to approved hook policy. Unrelated settings and other adapters remain intact; repetition produces no duplicates or further changes.
- [ ] Installed binaries and common directories do not independently choose adapters. A host without verified hook support receives honest manual guidance without fabricated enforcement.
- [ ] Configuration with quotes and shell metacharacters passes through structured arguments or configuration-file input with no shell execution; no synthetic overwrite approval is supplied.
- [ ] Missing policy requires normal setup approval; ignored existing policy yields a concrete tracked-policy migration proposal without editing ignore rules automatically.
- [ ] Setup transcript and preservation tests verify the complete path, and operator docs explain why host repair leaves role choices independent.

## Blocked by

- `host-harness-resolution#01`

## Comments

- 2026-09-30 — Operator approved the Spec, test seams and four-Issue breakdown in conversation. Planning approval does not authorize implementation.
