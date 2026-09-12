# Integration Capability declaration validation

Type: issue
Status: ready-for-agent
Slice: machine-setup#05
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

Accept `IntegrationCapabilities` into configuration only from an integration adapter's own declaration, validated before it is written. A declaration that is malformed, or that claims more than its validation evidence supports, is rejected and leaves that harness configured with no capability claims — never with optimistic defaults.

There is no code path from presence evidence, a directory, a binary, a parent process name, or an environment variable to a capability value. The resulting configuration cannot advertise a Context Watermark ceiling or agent interruption for an integration whose declaration says otherwise. The setup report shows each harness's capability state, including "none declared".

The dependency on `harness-adapters` is narrow: this slice needs the **shape** of the declaration and of its validation evidence, not a working adapter. The adapter is injected as a fake throughout. If the declaration's structure later changes, the validation rules here change with it; the rejection behavior does not, and that is the part ADR-0001 cares about.

## Acceptance criteria

- [ ] A valid declaration from a fake adapter is written to configuration with its `validatedAt` timestamp and validation evidence.
- [ ] A malformed declaration is rejected with the offending field path, and the harness ends with zero capability claims in the written configuration.
- [ ] A declaration claiming `contextMonitoring: "per_tool_call"` without supporting validation evidence is rejected, and the configuration does not advertise per-tool-call monitoring for that harness.
- [ ] A harness declaring `between_turns` monitoring and `cooperative_only` interruption produces a configuration that advertises exactly those and no stronger variant.
- [ ] Presence detection output, `GANTRY_HOST_COMMAND`, and parent process name are all exercised as inputs and grant no capability in any combination.

## Blocked by

- `machine-setup#01` — the configuration write path the validated declaration lands through.
- `machine-setup#02` — the presence records, so the no-derivation assertion has both facts available in one test.
- `harness-adapters#02` — the Integration Capability declaration shape and its validation evidence contract; the adapter itself is injected as a fake, so only the declared shape is required.
