# Routing presets

Type: issue
Status: ready-for-agent
Slice: machine-setup#06
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

Ship `claude-only`, `opencode-host`, `opencode-host+codex-critic`, `gateway`, and `demo` as named sets of configuration values applied as a starting point. Applying a preset records its name in the configuration; adjusting any value afterwards keeps the name with a modified marker rather than presenting the configuration as pristine.

A preset carries routing only — never a capability claim and never a credential value. After application, the report prints the resolved command for each configured role so the operator can verify routing before anything runs.

## Acceptance criteria

- [ ] Each of the five presets produces a configuration that passes whole-document validation.
- [ ] The applied preset's name is readable from the configuration through the core.
- [ ] Adjusting any value after applying a preset sets the modified marker while retaining the preset name.
- [ ] No preset writes any Integration Capability field, asserted per preset.
- [ ] No preset writes a credential value; credentials appear only as environment variable names.
- [ ] The report lists a resolved command for every configured role.

## Blocked by

- `machine-setup#01` — the factory and the configuration write path a preset is applied through.
- `config-and-snapshot#01` — the configuration field vocabulary for routing, context policy, and capacity and budget limits that a preset sets values in.
