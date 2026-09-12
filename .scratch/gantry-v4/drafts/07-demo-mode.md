## Spec 07 — demo-mode

This spec owns the evaluation path: `gantry init --demo` provisions a self-contained fixture Repository Execution Unit under the machine factory, registers it with an immutable `demo` marker, and drives the full pipeline through the shared operation core using stub harness drivers and stub check adapters that return pre-recorded content — no credential, no network, no remote, no prior `gantry setup`. It also owns the invariant that keeps simulated evidence quarantined: no operation may relate a record in one mode to a record in the other, and every state projection carries the mode so the simulated-evidence marker is rendered from data rather than remembered by a call site. The risk sits in two places. First, the boundary is only as good as its enforcement point — if it is a convention applied per writer rather than a validated predicate at the operation boundary, a later spec's new record type quietly leaks. Second, the under-two-minute claim degrades monotonically as waves 2–4 add work to the pipeline, and it is unrecoverable if measured once near release rather than from the first commit; that is why the measurement is a slice here and not a §13 checklist item.

### Slices

---

**01 — Demo mode marker and the cross-mode boundary**

- **What to build**: Add `demo` as an immutable mode property of the Repository Execution Unit, set at registration and never mutable afterwards, and make every record's mode derive from its unit rather than from a per-record flag. Add the validated boundary predicate at the operation boundary: an operation whose inputs reference units of differing modes, or whose evidence references a record belonging to a unit of another mode, is rejected with a named rejection code that states the mode boundary. Carry `mode: "live" | "demo"` on the state projection returned by every operation outcome, and prove the CLI renders a simulated-evidence marker from that projection field. This is the prefactoring slice: nothing else in the spec is safe to build until the boundary exists, because retrofitting it means auditing every writer.
- **Acceptance criteria**:
  - Registering a unit with mode `demo` persists the marker; a subsequent attempt to change a registered unit's mode is rejected.
  - An operation relating a demo-unit record to a live-unit record is rejected with a mode-boundary rejection code, asserted by code and not by message text.
  - An approval recorded in a demo unit does not satisfy any authorization check in a live unit.
  - Every state projection for a demo unit carries `mode: "demo"`; a projection that omits it fails a test.
  - One CLI parity test proves the simulated-evidence marker in rendered output is derived from the projection's mode field, not passed at the call site.
- **Blocked by**: needs `unit.register` and Repository Execution Unit identity derivation, the `StateProjection` shape, and the rejection-code contract, all from `execution-core`.
- **Parallelizable with**: 03, 04

---

**02 — Demo fixture lifecycle: `gantry init --demo` and `demo.reset`**

- **What to build**: Materialize the fixture project from templates shipped in the package into a dedicated directory under the machine factory — never the current working directory, never a user repository — printing the path before creating anything. The fixture is a real Git repository: initialized, committed, with no remote configured, so external effects are structurally impossible rather than suppressed. Provision the minimum machine factory the demo needs (database at the current schema version plus a demo-scoped configuration) so the command works with no prior `gantry setup`, then register the fixture as a demo-mode Repository Execution Unit. Add `demo.reset` to the operation catalog: it removes the demo unit's records, worktrees, and fixture and rebuilds them, exempt from the two-step Cleanup Authorization manifest, with the exemption enforced by rejecting `demo.reset` against a live unit rather than by loosening cleanup.
- **Acceptance criteria**:
  - `gantry init --demo` succeeds on a machine with no prior `gantry setup`, no credential, and network access blocked.
  - The printed path is the only path created; the current working directory and any repository under it are byte-identical before and after.
  - The fixture resolves to a valid Repository Execution Unit identity and has zero configured remotes.
  - `demo.reset` against the demo unit removes and rebuilds the fixture without producing a cleanup manifest; `demo.reset` against a live unit is rejected and the live unit is unmodified.
  - Demo Git workflow policy resolves to local mode, and no provider operation is attempted anywhere in the run.
- **Blocked by**: 01; needs the operation catalog and Cleanup Authorization semantics from `execution-core`; needs the `ConfigStore` layering and Execution Rule Snapshot capture from `config-and-snapshot`; needs the database-initialization-at-current-schema-version rule and machine factory location convention from `machine-setup`; needs the redaction sink enforcement interface from `data-handling`.
- **Parallelizable with**: 03, 04

---

**03 — Stub harness drivers and scripted result envelopes**

- **What to build**: Implement the stub drivers against the same `HarnessAdapter` interface the real adapters implement — `dispatch`, `observe`, `requestStop`, `reconcile` — resolving a pre-recorded GTP result envelope from the assignment's role, PBI, and iteration. Declare Integration Capability honestly: context usage is `self_reported` sourced from the scripted envelope and never `measured`, handoff is triggered by a scripted `needs_handoff` status rather than by an observed watermark, and no capability is declared that has no passing conformance probe behind it. Include the deliberately invalid scripted result so Protocol Failure handling has a source. Version the scripted envelopes with the package alongside the envelope schemas, and validate every scripted envelope against its role's result contract in the test suite so a protocol change breaks the demo in the same commit.
- **Acceptance criteria**:
  - The stub satisfies the `HarnessAdapter` type with no added methods and no demo-only escape hatch on the interface.
  - Every scripted envelope validates against its role's result contract; an envelope that does not fails the build.
  - Stub-reported context usage projects as `self_reported`; a test asserts `measured` never appears for a demo unit.
  - `requestStop` returns an honest variant for a stub (never `stopped` with fabricated evidence), and `reconcile` returns a result derived from the scripted state.
  - Response resolution is deterministic: the same role, PBI, and iteration yields the same envelope across runs and processes.
- **Blocked by**: needs the `HarnessAdapter` interface including `IntegrationCapabilities`, `StopOutcome`, and `ReconciliationResult` from `harness-adapters`; needs the role task and result contracts, `GtpStatus`, and submission identity from `gtp-protocol`.
- **Parallelizable with**: 01, 02, 04

---

**04 — Stub check adapters and scripted Comparison Evidence**

- **What to build**: Implement the stub check adapters against the same `CheckAdapter` interface the real adapters implement, returning pre-recorded structured reports whose findings carry the full normalized shape — rule, path, symbol, severity, content anchor, problem identity — so the real comparison logic can match them. Script the finding sets per subject revision so that one PBI's Merge Candidate carries a finding absent from the current target (a genuine Quality Regression), one PBI's initial evaluation produces findings that the scripted correction resolves, and the remaining PBI is clean. Also script a mandatory-test check so Gantry's re-verification on the delivered revision has evidence to consume. Declare check stability and resource needs through the same declarations real adapters use.
- **Acceptance criteria**:
  - The stub satisfies the `CheckAdapter` type with no added methods and no demo-only branch in the comparison path.
  - Every scripted finding carries enough identity to satisfy Evidence Completeness; an incomplete scripted finding fails closed exactly as a real one would.
  - Running the same scripted check twice against the same revision produces identical reports, satisfying the declared stability requirement.
  - Candidate-versus-target scripted evidence yields exactly one differential regression for the designated PBI and zero for the others.
  - Scripted reports are versioned with the package and validated against the report schema in the test suite.
- **Blocked by**: needs the `CheckAdapter` interface, `StructuredReport`, `NormalizedFinding`, and the problem-identity rule from `verification-adapters`.
- **Parallelizable with**: 01, 02, 03

---

**05 — Scripted walkthrough: clean delivery, Protocol Failure, and the dependency wait**

- **What to build**: Author the fixture's canonical spec and PBI breakdown, record the Planning Approval, and drive the first scripted PBI end to end through the real operation core: dispatch, all criteria completed with evidence, mandatory tests verified on the delivered revision, Implementation Completion, gates passed, local merge confirmed, `integrated`. In the same walkthrough, script one dispatch that returns an invalid result so a Protocol Failure occurs — preserving the completed work and advancing nothing — and declare one PBI dependent on another so it waits in `awaiting_dependency` until Dependency Readiness is satisfied by the prerequisite's integration. Assertions are on the sequence of Execution States each PBI passes through and on the resulting projections, never on rendered text.
- **Acceptance criteria**:
  - The first PBI's state sequence reaches `integrated` through `implementation_complete`, `in_gates`, `awaiting_review`, and `merge_authorized`, with no state skipped.
  - The invalid scripted result produces a Protocol Failure; the PBI's state is unchanged afterwards and the prior completed work is still retrievable.
  - The dependent PBI remains in `awaiting_dependency` while the prerequisite is unintegrated and becomes eligible only after the prerequisite reaches `integrated`.
  - Local merge requires the operator confirmation step; the walkthrough supplies it through an operator channel and a test proves an agent channel is refused.
  - The whole walkthrough runs with no network access and creates no provider object.
- **Blocked by**: 02, 03, 04; needs PBI Worktree lifecycle, dispatch scheduling, and `awaiting_dependency` handling from `pbi-execution-loop`; needs Protocol Failure semantics from `gtp-protocol`; needs local-mode Git Workflow Policy and local merge confirmation from `git-integration`.
- **Parallelizable with**: 06 (shares the scripted plan; coordinate the fixture's PBI list up front, then proceed independently), 07's measurement plumbing

---

**06 — Scripted walkthrough: Correction Attempt and the entropy regression block**

- **What to build**: Extend the walkthrough with the two PBIs that show what the tool is for. The second PBI's initial gate evaluation produces findings, one Correction Attempt is dispatched and consumed, revalidation passes, and integration proceeds — with the projection showing the attempt count moving from zero to one so the Correction Budget is visible rather than described. The third PBI's Entropy Gate blocks on a Quality Regression present in the Merge Candidate and absent from the current target, and its projection names the concrete finding rather than a score. The walkthrough deliberately ends with a blocked PBI in the final state.
- **Acceptance criteria**:
  - The second PBI consumes exactly one Correction Attempt; the projection shows the count transition and the initial evaluation consumes none.
  - The second PBI reaches `integrated` after revalidation.
  - The third PBI's gate result is `failed` on a differential regression, and the projection identifies the finding by rule and location rather than by an aggregate value.
  - The demo's final state includes at least one blocked PBI; a walkthrough where everything passes fails the test.
  - Re-running the walkthrough from a fresh fixture produces an identical sequence of Execution States.
- **Blocked by**: 02, 03, 04; needs the Entropy Gate differential decision and the Correction Attempt loop from `entropy-gate`; needs Comparison Evidence normalization from `verification-adapters`; needs dispatch scheduling from `pbi-execution-loop`.
- **Parallelizable with**: 05

---

**07 — Demo measurement and the pipeline regression check**

- **What to build**: Record the demo's own wall-clock duration from command invocation to a visible pipeline, persist it as a demo measurement, and report it through a channel that names it as such — explicitly distinct from any real-repository time-to-first-value target, which the PRD makes conditional on Repository Readiness and operator approvals. Expose the same measurement surface the dashboard uses for SSE latency on demo traffic. Then wire the scripted walkthrough into CI as a full-pipeline integration test with a duration assertion, so the two-minute claim degrades visibly from the first commit rather than being discovered near release.
- **Acceptance criteria**:
  - The run's duration is persisted and projected labeled as a demo measurement; no code path presents it as a real-repository target.
  - CI runs the scripted walkthrough as a required check and fails when its duration exceeds the configured demo budget.
  - The check fails loudly with a named cause when any PBI's state sequence diverges from the scripted expectation.
  - Two consecutive CI runs of the walkthrough produce identical state sequences, proving determinism.
  - The SSE latency measurement surface is populated from demo traffic and carries the demo-measurement label.
- **Blocked by**: 05, 06; needs the CI required-check definition and the release pipeline from `release-engineering`; needs the SSE projection channel from `dashboard` for the latency surface only (the duration measurement does not wait on it).
- **Parallelizable with**: the measurement-recording half can start alongside 05/06 once 02 exists; the CI wiring cannot.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| `unit.register` and Repository Execution Unit identity derivation | `execution-core` | 01, 02 |
| `StateProjection` shape | `execution-core` | 01 |
| Rejection code contract (codes asserted by tests, not messages) | `execution-core` | 01 |
| Operation catalog and its extension point | `execution-core` | 02 |
| Cleanup Authorization two-step manifest (to be narrowly exempted) | `execution-core` | 02 |
| Operator channel derivation (`cli` may assert operator) | `execution-core` | 02, 05 |
| `ConfigStore` layering and Execution Rule Snapshot capture | `config-and-snapshot` | 02 |
| Database initialization at current schema version; machine factory location | `machine-setup` | 02 |
| Redaction sink enforcement interface | `data-handling` | 02 |
| Role task and result contracts, `GtpStatus`, submission identity | `gtp-protocol` | 03, 05 |
| Protocol Failure semantics | `gtp-protocol` | 05 |
| `HarnessAdapter` interface (`IntegrationCapabilities`, `StopOutcome`, `ReconciliationResult`) | `harness-adapters` | 03 |
| `CheckAdapter`, `StructuredReport`, `NormalizedFinding`, problem identity | `verification-adapters` | 04 |
| Evidence Completeness and Check Stability declarations | `verification-adapters` | 04 |
| PBI Worktree lifecycle, dispatch scheduling, `awaiting_dependency` | `pbi-execution-loop` | 05, 06 |
| Local-mode Git Workflow Policy and local merge confirmation | `git-integration` | 05 |
| Entropy Gate differential decision and Correction Attempt loop | `entropy-gate` | 06 |
| CI required-check definition | `release-engineering` | 07 |
| SSE projection channel | `dashboard` | 07 (latency surface only) |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| Demo mode as an immutable unit property | 01 | `execution-core` (enforcement site), `repository-readiness` (readiness never derives from demo records), `dashboard` |
| Cross-mode boundary predicate and its rejection code | 01 | `execution-core`, and every spec that adds a record type |
| `mode: "live" \| "demo"` on the state projection | 01 | `dashboard` (persistent simulated indicator), `mcp-server` |
| Demo fixture location and provisioning contract | 02 | `release-engineering` (quickstart and recording), `machine-setup` (`demo` preset routing) |
| `demo.reset` operation and its narrow live-unit refusal | 02 | `dashboard` (one-click re-run control) |
| Stub harness driver as the reference `HarnessAdapter` implementation | 03 | `harness-adapters` (cheap exercise of interface variants), `release-engineering` |
| Stub check adapter as the reference `CheckAdapter` implementation | 04 | `verification-adapters` |
| The scripted scenario as the end-to-end regression suite | 05, 06 | `release-engineering` (required check); every later spec extends it rather than adding a parallel suite |
| Demo measurement (duration, SSE latency) as a labeled non-production measurement | 07 | `dashboard`, `release-engineering` |

### Risks / judgement calls

**Can these start before the real state sequences settle?** Partly, and the split is deliberate. Slices 01, 02, 03, and 04 are independent of the scripted scenario and can be written and picked up now — they depend on interface shapes (`HarnessAdapter`, `CheckAdapter`, `StateProjection`, the operation catalog) that the handoff already lists as contracts to lock, not on the sequences those interfaces produce. Slices 05 and 06 are the ones the handoff's recommendation is really about: they encode concrete state sequences through `pbi-execution-loop`, `entropy-gate`, and `git-integration`, and writing them before those specs' issues exist means rewriting the expected sequences. My recommendation is to write and schedule 01–04 immediately and hold 05–06 until spec 14's issues exist, which matches the handoff's ordering without stalling the spec for weeks. Slice 07's measurement plumbing follows 02; only its CI wiring waits.

**The reset merge.** I folded `demo.reset` into slice 02 rather than giving it its own slice. The argument is that provisioning and destroying the fixture share the same layout knowledge, and splitting them hands two agents the same secret. The counter-argument is real: reset also touches the operation catalog and the Cleanup Authorization exemption, which is a different surface from fixture templating, and slice 02 is already the meatiest non-scenario slice. If 02 looks too large when it is picked up, reset is the clean cut line.

**The scenario split.** I split the walkthrough by dependency depth rather than by scripted PBI — 05 gets the paths that need only the execution loop and local merge, 06 gets the paths that need the Entropy Gate. This lets them run concurrently and unblocks 05 several specs earlier than a single combined slice would. The cost is that both slices touch the same fixture plan, so the fixture's PBI list, dependency edges, and criteria identities have to be agreed once at the start of 05 and treated as fixed by 06. If that coordination looks fragile in practice, the safer shape is one scenario slice blocked on everything, at the price of a much later first green end-to-end run.

**Where I am least confident about ordering.** Slice 01 is listed as blocked by `execution-core`'s projection and rejection-code contracts, but the mode boundary is arguably something `execution-core` should carry in its own issues, with this spec only consuming it. I kept it here because this spec is where the invariant's justification lives and where the Out of Scope section says the property is defined — but if `execution-core`'s slicing already claims the boundary predicate, slice 01 collapses to the projection field plus the demo-specific tests, and that overlap should be reconciled before either is picked up.

**A constraint I did not turn into a slice.** Story 29 (fixture and scripted envelopes versioned with the package, updated in the same commit as a protocol change) is not separable work — it is an acceptance criterion inside slices 03 and 04, enforced by validating scripted content against the live schemas in the test suite. Making it its own slice would produce a slice with no behavior.

Relevant paths: `/Users/julioborges/src/personal/gantry/.scratch/demo-mode/spec.md`, `/Users/julioborges/src/personal/gantry/.scratch/gantry-v4/map.md`, `/Users/julioborges/src/personal/gantry/.scratch/gantry-v4/handoff.md`, `/Users/julioborges/src/personal/gantry/CONTEXT.md`.
