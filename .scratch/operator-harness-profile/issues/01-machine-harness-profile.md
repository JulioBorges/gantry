# Keep each operator's harness in a machine profile

Type: issue
Status: done
Slice: `operator-harness-profile#01`
Spec: `.scratch/operator-harness-profile/spec.md`
Created: 2026-10-03

## Parent

`operator-harness-profile`

## What to build

Give each operator a machine-local harness profile at `~/.gantry/profiles/<unit-id>/execution.json`, resolved with the existing execution-unit id. An approved personal switch writes that profile and leaves tracked `.gantry/config.json`, adapter files and `AGENTS.md` unchanged. Explicit `--host` wins for one invocation and writes nothing. Repository role defaults stay the shared baseline; a profile role overlay applies only on that machine, above the baseline and below Issue and Run overrides. A legacy tracked `execution.hostHarness` remains a lower-precedence hint until an approved migration copies it into the profile and removes it. Ignored tracked policy still refuses shared setup with the existing migration proposal.

### Files to read

- `.scratch/operator-harness-profile/spec.md`
- `docs/adr/0004-skill-pack-instead-of-an-engine.md`
- `docs/adr/0006-role-execution-can-use-another-harness.md`
- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/setup.py`
- `.agents/skills/gantry/scripts/common.py`
- `.agents/skills/gantry/scripts/execution.py`

## Acceptance criteria

- [x] An approved personal switch writes only `~/.gantry/profiles/<unit-id>/execution.json` and leaves `.gantry/config.json`, adapter files and `AGENTS.md` byte-for-byte unchanged.
- [x] Two temporary homes with different profiles resolve different hosts from one unchanged tracked policy.
- [x] Explicit `--host` selects that invocation, writes no profile and no tracked policy, and outranks the profile and a legacy tracked host.
- [x] Role resolution order is Issue override, Run override, profile overlay, repository default, then confirmed environment default.
- [x] Shared setup against an ignored `.gantry/config.json` exits with the tracked-policy migration proposal and writes no ignore rule and no policy.
- [x] An approved legacy migration removes tracked `execution.hostHarness` after the profile contains it; until approval, readers use the legacy key only when the profile has no host.
- [x] The profile contains harness, model and effort only. A new ADR records `~/.gantry/profiles/<unit-id>/` as the operator home beside observational `~/.gantry/state/`.

## Blocked by

- None

## Comments

- 2026-10-03 — Draft recorded from a personal-project adoption. Planning approval is required before this issue becomes `ready-for-agent`.
