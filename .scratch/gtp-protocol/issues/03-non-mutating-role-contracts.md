# Non-mutating role contracts

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#03
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

The remaining eight branches of the role-discriminated union — requirement critic, adversarial critic, slicer, spec architect, architectural sentinel, appsec gatekeeper, merger, and compound learner — each with its task inputs and its result evidence, all validated through the boundary.

The decision-rich part is the adversarial critic. Its findings are restricted to `spec-deviation`, `adr-deviation`, `semantic-conflict`, and `scope-creep`, and its result payload has no field capable of expressing approval, clearance, or downgrade of an existing finding. The "may only add" rule is therefore enforced by the shape of the type rather than by a runtime check someone could forget to run.

The union is closed and exhaustive, so adding a role later cannot weaken validation for the existing ones. This slice and `gtp-protocol#02` share that union; whichever lands second must not weaken the exhaustiveness check the first one established.

## Acceptance criteria

- [ ] Each of the eight roles has a task payload carrying its declared inputs and a result payload carrying its declared evidence, both validated through the boundary.
- [ ] The adversarial critic result type has no field that can clear, downgrade, or approve a deterministic finding — demonstrated by the absence of the field, not by a runtime check.
- [ ] An adversarial critic finding outside the four allowed classes is a validation violation.
- [ ] A slicer result carries proposed PBIs with criterion identities, dependencies, a story coverage map, and a per-PBI context estimate with method and uncertainty, each as a structured field rather than prose.
- [ ] Exhaustiveness over the role union is enforced at the type level, so an unhandled role fails to build rather than falling through to a permissive default.

## Blocked by

- `gtp-protocol#01` — provides the common envelope layer and the validation order these payloads plug into.
- `spec-validation#02` — provides the criterion identity rule carried in slicer results.
- `slicing-and-approval#01` — provides the plan version hash definition.
- `slicing-and-approval#02` — provides the story coverage map shape.
- `slicing-and-approval#03` — provides the per-PBI context estimate fields, including method and uncertainty.
- `verification-adapters#01` — provides the normalized finding shape for the deterministic findings passed into the adversarial critic task.
