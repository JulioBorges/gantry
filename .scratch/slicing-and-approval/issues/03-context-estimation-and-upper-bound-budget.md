# Context estimation and the upper-bound budget

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#03
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Implement the `ContextEstimate` computation and the `PBI-BUDGET` rule. A pluggable tokenizer (injected, with a deterministic stub in tests) counts known components — instructions, spec, PBI text, contracts, governance — and records a `sampled` or `declared` basis for unknown ones such as source files, with the basis mandatory per component. The estimate records tokenizer id and version, assumed model and window, per-component tokens and basis, total, uncertainty margin, `upperBoundFraction`, and method. `PBI-BUDGET` compares the **upper bound** — never the point estimate — against the configured Initial Context Budget; using the point estimate would turn the uncertainty margin into decoration.

The same evaluator is exposed for a continuity package including a handoff memo, with no separate allowance. The boundary is deliberate: the handoff sequence that triggers continuity evaluation lives in `pbi-execution-loop#04`, but "there is no separate smaller allowance for continuity" is a property of the budget evaluator, not of the handoff — so this slice owns the evaluator and spec 11 calls one function. A package that cannot fit without dropping contracts, criteria, or governance produces a review pause rather than a trimmed package.

The state projection carries estimated and observed context as separate fields, with observed `unknown` until measured.

## Acceptance criteria

- [ ] An estimate whose point value is under budget but whose upper bound exceeds it fails `PBI-BUDGET`.
- [ ] An estimate missing tokenizer, assumed window, margin, method, or any component's basis is rejected as invalid rather than defaulted.
- [ ] Evaluating a continuity package that includes the handoff memo uses the same budget value and the same comparison; no code path applies a reduced or separate allowance.
- [ ] A package whose mandatory content alone exceeds the budget yields a review pause; no output path drops contracts, criteria, or governance content.
- [ ] The projection exposes estimated and observed as distinct fields, and observed is `unknown` before any integration reports a measurement — there is no code path that writes an estimate into the observed field.
- [ ] Assertions are structural (fields present, comparison uses the upper bound); no test asserts an exact token count.

## Blocked by

- `slicing-and-approval#01` — provides the persisted plan proposal and the per-PBI record the estimate attaches to.
- `config-and-snapshot#01` — provides the Initial Context Budget limit value and the assumed model and window configuration.
