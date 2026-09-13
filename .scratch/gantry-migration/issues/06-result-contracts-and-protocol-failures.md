# Result contracts and protocol failures

Type: issue
Status: ready-for-agent
Slice: `gantry-migration#06`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add the six role schemas under `.agents/skills/gantry/schemas/` and `.agents/skills/gantry/scripts/result.py`. Implement only the declared JSON Schema subset: `type`, `properties`, `required`, `items`, `enum`, and `additionalProperties`. Replace inline result schemas in the canonical workflow templates with schema-file loading for structured harnesses and `result.py --role <role>` validation otherwise. A missing or invalid result gets one re-ask, then remains a failed phase without changing Issue state.

## Acceptance criteria

- [ ] `printf '%s' '{"complete":false}' | python3 .agents/skills/gantry/scripts/result.py --role critic --json` exits 1 and reports `criteria` as missing, while a valid critic result exits 0; `--help` works and a 200 KB result validates in under one second.
- [ ] The planner, plan-critic, implementer, reviewer, critic, and learner schema files each use only the supported subset and enforce the workflow result fields their roles consume, including exact critic gate verdicts.
- [ ] A workflow test proves an invalid critic result is re-requested once, then records `critic_failed`, leaves the Issue status and checkboxes unchanged, and does not consume or raise the correction budget.
- [ ] The Spec Changelog receives an English entry in the same merge, and `result.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#02` — consumes the canonical workflow template locations and role protocol.

## Comments
