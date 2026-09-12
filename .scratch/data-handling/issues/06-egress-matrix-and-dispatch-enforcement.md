# Egress matrix resolution and dispatch enforcement

Type: issue
Status: ready-for-agent
Slice: data-handling#06
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

The declared Data Egress Policy matrix and the enforcement point at dispatch. A dispatch is permitted only when an allowance matches its role and its *resolved* driver and lists every payload class the dispatch carries. Absence blocks and ambiguity blocks — two allowances disagreeing for the same role and driver resolve to neither — with a rejection that names the missing or conflicting allowance.

Destination is classified by where processing actually occurs, taken from the driver's declaration rather than from the location of the executable, so a detached CLI reaching a remote model is remote and a stub driver is local.

Secrets are prohibited regardless of allowance: the pipeline runs before dispatch payload assembly as well as before retention, so approving a destination never approves sending credentials to it.

The matrix schema, resolution, blocking, and destination classification carry no intra-spec blocker and can be developed against slice `data-handling#01`'s published pipeline interface before it lands; only the pre-assembly redaction criterion consumes it.

```ts
type PayloadClass =
  | "spec_text" | "pbi_text" | "governance_doc"
  | "source_context" | "diff"
  | "check_report" | "finding"
  | "prompt_template" | "agent_output";
```

## Acceptance criteria

- [ ] A dispatch whose role and resolved driver are absent from the matrix is blocked, and the rejection names the missing allowance.
- [ ] A dispatch carrying a payload class the matrix does not allow for that destination is blocked, and the rejection names the class.
- [ ] Two conflicting allowances for the same role and driver block rather than resolving to either one.
- [ ] A driver declared to reach a remote model is classified remote even when launched locally; a stub driver is classified local.
- [ ] A repository configured for local-only processing completes a full dispatch with no remote destination recorded anywhere.
- [ ] A secret-shaped string in a dispatch payload is redacted before assembly even when the destination is approved for that payload class.

## Blocked by

- `data-handling#01` — the pipeline interface, consumed by the pre-assembly redaction criterion only; the rest of this slice can be built against the published interface beforehand.
- `config-and-snapshot#01` — the egress matrix configuration section and its validation.
- `harness-adapters#01` — the resolved driver identity and its declared processing destination on the dispatch record.
- `gtp-protocol#01` — the role identity in the envelope's common identity layer and the dispatch payload assembly point enforcement hooks into.
- `repository-readiness#06` — the onboarding declaration that collects the repository's Data Egress Policy and produces the matrix.
