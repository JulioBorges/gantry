## Spec 12 — verification-adapters

This spec owns the **evidence production layer** beneath the entropy gate: one adapter interface per tool, the normalized finding shape and its problem identity, evidence completeness and its narrow operator classification escape, check stability declarations, and check resource declaration with scoped locking. It produces and validates evidence; it decides nothing. The risk sits almost entirely in one place — **problem identity**. Identity is `rule` + `path` + `symbol` + `contentAnchor` with the message excluded, `symbol` derived by Gantry via tree-sitter rather than taken from the tool. Every adapter parser, all of spec 13, and spec 15's rule mappings are written against that shape, so a wrong call here is expensive and late to discover. The secondary risks are mechanical but real: a `machine`-scoped lease that is secretly an in-process mutex passes a naive test and fails the requirement, and the opt-in mutation adapter is the slowest thing in the system with the least obvious correctness story.

### Slices

---

**01 — Check adapter seam and normalized finding shape**

- **What to build**: The `CheckAdapter` interface, the `CheckRun` / `CheckOutcome` / `StructuredReport` / `NormalizedFinding` types, and the operation-core operation that runs an approved verification command against a stated revision and persists its report bound to revision, tool version, rule set version, command reference, and declared coverage. Problem identity lands here in its content-anchor form: `rule` + normalized `path` + `contentAnchor` hashed over the normalized reported line plus a fixed number of neighbours, with the no-location fallback to `rule` + `path` and count-per-identity matching, and the derivation actually used recorded on every finding. Line and column are persisted for display and structurally excluded from identity. Ship the Gitleaks adapter as the reference parser — it is language-agnostic, flat, and needs no package-manager resolution — so the slice is demonstrable end to end from recorded tool output to a persisted, retrievable report.
- **Acceptance criteria**:
  - Invoking the check-run operation with an approved Gitleaks command and recorded output persists a report and returns findings carrying rule, path, severity, `problemIdentity`, and the recorded derivation.
  - Parsing the same recorded output twice yields identical problem identities; a report differing only in reported line and column yields identical identities.
  - Two occurrences of the same rule in the same file receive different identities via their content anchors.
  - A tool reporting no location at all yields `rule` + `path` identity with the count-fallback derivation recorded; target two / candidate three resolves to one introduced finding, target two / candidate one to a recorded improvement crediting nothing.
  - The Gitleaks adapter passes a conformance test against captured fixture output with no live tool invocation.
  - Reports and findings are written through the redaction sink; no writer bypasses it.
- **Blocked by**: `operation catalog registration and the in-process invoke seam` + `record families and persistence conventions` (execution-core); `normalized content hashing over line endings` (data-handling); `redaction sink enforcement interface` (data-handling); `approved verification command reference and its declared coverage` (repository-readiness).
- **Parallelizable with**: none — this is the bootstrap.

---

**02 — Enclosing-symbol derivation and the fallback ladder**

- **What to build**: Gantry-side derivation of the enclosing symbol from the file and the reported line using tree-sitter, with grammars for the languages in the approved adapter set, promoting identity to `rule` + `path` + `symbol` + `contentAnchor`. Tree-sitter becomes an engine dependency shared by every adapter rather than reimplemented per tool. The grammar version travels in the report alongside the tool version. The fallback ladder is completed and ordered: symbol-anchored, then no-grammar (`rule` + `path` + `contentAnchor`), then no-location (count). Adapters are untouched — they never derive identity — which is what lets the adapter slices run concurrently with this one.
- **Acceptance criteria**:
  - A finding in a language with a grammar gets a symbol-anchored identity; the derivation used is recorded on the finding.
  - A tool that reports no symbol still produces per-occurrence identities, because the symbol comes from the file and line.
  - A file whose language has no available grammar falls back to `rule` + `path` + `contentAnchor` and records that fallback rather than failing.
  - Identity is unchanged when the tool's message text changes between versions, and unchanged when a function is moved within a file without its body changing.
  - Symbol derivation is deterministic across two runs of the same file; a grammar that parses wrongly still parses consistently.
  - Grammar version is present on every report and participates in the reuse key.
- **Blocked by**: 01
- **Parallelizable with**: 03, 04, 05, 06, 07

---

**03 — Evidence validity: completeness, operator classification, and report reuse**

- **What to build**: The consumption-time verdict on whether a stored report may serve as comparison evidence. A finding missing `rule`, `path`, `severity`, or `problemIdentity`, or a report missing `subjectRevision`, `toolVersion`, `ruleSetVersion`, or `declaredCoverage`, is invalid evidence that leaves the dependent gate unapproved and is never read as zero findings. The single escape is a `FindingClassification`: operator-channel only, scoped to one problem identity in one report version, recorded as additive evidence beside the tool's output and never a rewrite of it, auto-invalidated by a revision change, a rule version change, or a change to the finding. Report reuse is decided at the point of consumption — revision, rule set version, tool version, grammar version, and command reference must all match — not trusted from a cache key. `pass_fail` outcomes are accepted as mandatory checks while being structurally unable to feed the comparison. One CLI parity test covers the classification command.
- **Acceptance criteria**:
  - A finding missing `problemIdentity`, and separately a report missing `toolVersion`, `ruleSetVersion`, or `declaredCoverage`, each leave the gate unapproved; no path infers zero findings from either.
  - A classification permits exactly one finding in one report version; the same problem identity in a new report version is blocked again, and the recorded evidence still shows the tool's original output.
  - Each of a revision change, a rule version change, and a change to the finding invalidates the classification, with the reason recorded.
  - A classification from a non-operator channel is rejected as `operator_channel_required`; a catalog-shape test proves no operation exists that waives a rule globally or suppresses by rule.
  - A report is reused only when revision, rule set version, tool version, grammar version, and command all match; any difference forces a fresh run.
  - A `pass_fail` outcome satisfies a mandatory check and is rejected by the comparison input, and `declaredCoverage` accompanies every surfaced report.
- **Blocked by**: 01; `actor provenance and the operator-only channel` (execution-core)
- **Parallelizable with**: 02, 04, 05, 06, 07

---

**04 — Check stability and adapter failure classification**

- **What to build**: The stability declaration — environment, inputs, isolation requirement, and criterion — and its evaluation, so that a single passing run counts only when the declared criterion allows it. Reruns follow the check's approved policy and stop at its bound rather than looping to green. Inconsistent outcomes append to observed instability, surface as a check problem, and leave the dependent gate unapproved until the check is reviewed. In the same slice, adapter failures are classified `infrastructure` or `permanent` and wired to the retry accounting, because the whole point is that instability and infrastructure failure are different things: instability spends no retry allowance, an infrastructure failure spends one, a permanent failure blocks without spending any.
- **Acceptance criteria**:
  - A check declaring `consecutive: 2` is not satisfied by one passing run; `quorum` is evaluated as declared; `single_run` is accepted.
  - Inconsistent outcomes are appended as observed instability, surface as a check problem, and leave the gate unapproved.
  - The rerun loop terminates at the approved bound and reports; no configuration permits unbounded reruns.
  - Instability consumes no infrastructure retry allowance; an adapter `infrastructure` failure consumes one; a `permanent` failure blocks without consuming.
  - A check that runs and reports findings — however many, however severe — is treated as working, not as a broken setup.
  - Stability declarations and rerun bounds are read from the execution rule snapshot, not from live configuration.
- **Blocked by**: 01; `infrastructure retry allowance accounting` (execution-core); `execution rule snapshot binding and limit values` (config-and-snapshot)
- **Parallelizable with**: 02, 03, 05, 06, 07

---

**05 — Check resources: scoped declaration, allocation, and lease reclamation**

- **What to build**: Resource declaration with kind, real shared identity, sharing scope, and isolatability, plus the allocator that prefers isolation and falls back to serialization. When isolatable, a per-execution instance is provisioned and no lock is taken; otherwise a lease is acquired at the declared scope with heartbeat and expiry, reclaimable only after the holder is reconciled. Machine scope is what makes two clones of the same repository serialize on one port — worktree separation never substitutes for it. Coordination applies identically to target validation and candidate validation of the same check. Expose the declarations as a projection the scheduler can consult for dispatch eligibility without knowing adapter internals.
- **Acceptance criteria**:
  - Two checks in different repository execution units declaring the same machine-scoped port identity serialize; a worktree-scoped temporary directory takes no lock.
  - An isolatable resource is provisioned per execution and takes no lock.
  - Target validation and candidate validation of the same check serialize against each other on a shared resource.
  - A lease whose holder crashed is reclaimed only after reconciliation, proven by a test running two operating-system processes — not an in-process mutex.
  - A machine-scoped requirement is still serialized when the two runs come from distinct worktrees.
  - The resource declaration projection is readable by a scheduler consumer and contains scope and identity without adapter-internal detail.
- **Blocked by**: 01; `lease primitive with heartbeat, expiry, and reconciliation before reclamation` (execution-core)
- **Parallelizable with**: 02, 03, 04, 06, 07

---

**06 — TypeScript and JavaScript adapter set**

- **What to build**: Adapters for TypeScript compilation, ESLint with typescript-eslint, Vitest, dependency-cruiser, and the configured license check, each translating its tool's native JSON into the normalized finding shape, each declaring what its tool actually examines, each with its own severity mapping into blocker/major/minor/info and its own absolute-rule flagging. Approved commands must run unmodified under npm, pnpm, and yarn. Every adapter ships a conformance test against recorded real output rather than a live tool run, per this spec's deliberate exception to the shared seam; the behavioral assertions still go through the operation core.
- **Acceptance criteria**:
  - Each of the five adapters parses recorded real output into normalized findings and passes a conformance test against fixture files with no live tool invocation.
  - Severity mapping from each tool's native levels is table-driven and covered by a test per tool.
  - Every produced report carries a `declaredCoverage` string naming what its tool actually examines; generic tool support is nowhere presented as complete analysis coverage.
  - The same approved command executes under npm, pnpm, and yarn without rewriting, proven for all three.
  - A failing Vitest run yields findings plus its mandatory-test outcome; a crashed tool yields `adapter_failure` with a classification, never findings.
  - Identities produced from two runs over the same fixture are identical.
- **Blocked by**: 01; `approved verification command reference and its declared coverage` (repository-readiness)
- **Parallelizable with**: 02, 03, 04, 05, 07

---

**07 — Python adapter set**

- **What to build**: Adapters for Ruff, pytest, Import Linter, pip-audit, and the configured license check, on the same terms as slice 06 — native output into the normalized shape, per-adapter declared coverage, severity mapping, absolute-rule flagging — with approved commands running under both uv and pip. Same conformance-test discipline against recorded output.
- **Acceptance criteria**:
  - Each of the five adapters parses recorded real output into normalized findings and passes a conformance test against fixture files with no live tool invocation.
  - Severity mapping from each tool's native levels is table-driven and covered by a test per tool.
  - Every produced report carries a `declaredCoverage` string naming what its tool actually examines.
  - The same approved command executes under both uv and pip without rewriting, proven for both.
  - A failing pytest run yields findings plus its mandatory-test outcome; a crashed tool yields `adapter_failure` with a classification, never findings.
  - Identities produced from two runs over the same fixture are identical.
- **Blocked by**: 01; `approved verification command reference and its declared coverage` (repository-readiness)
- **Parallelizable with**: 02, 03, 04, 05, 06

---

**08 — Opt-in mutation adapter**

- **What to build**: An adapter, off by default, that measures verification strength rather than finding source defects — the one deterministic signal for an assertion weakened in place. Stryker for TypeScript and JavaScript, mutmut for Python, both run incrementally and scoped strictly to code the PBI's diff touched and code covered by tests the diff modified. Only a transition from killed-by-assertion to survived produces a finding; a mutant killed by the clock is recorded and displayed but never contributes to the decision. The per-mutant bound is derived from the unmutated suite's own measured duration times a declared factor, never a wall-clock constant, and the check itself has no elapsed-time cap — its duration is recorded, not enforced. Comparability comes from declaring a machine-scoped check resource so target and candidate runs serialize, rather than from a tolerance threshold. Surviving mutants are emitted as ordinary normalized findings under a `mutation:<operator>` rule namespace, so the entropy gate needs no special case.
- **Acceptance criteria**:
  - The adapter runs only under explicit opt-in; a default check set invokes no mutation run.
  - Mutants are generated only for diff-touched code and code covered by tests the diff modified; a whole-repository run is not reachable through any configuration.
  - A test weakened from an equality assertion to a presence assertion produces surviving mutants that were previously killed by assertion, emitted as normalized findings under the `mutation:<operator>` rule namespace with standard identity derivation.
  - A mutant transitioning from killed-by-assertion to killed-by-timeout is recorded and displayed, produces no finding, and does not block.
  - The per-mutant bound scales numerically when the fixture suite is made slower, proving derivation from measured duration rather than a constant; the check records its own duration and enforces no wall-clock limit on itself.
  - Two mutation runs serialize on the machine-scoped resource, including a target run against a candidate run of the same check.
- **Blocked by**: 01, 05; `merge candidate and current target revision pair with its touched-path diff` (git-integration); `mutation opt-in configuration value bound to the execution rule snapshot` (config-and-snapshot)
- **Parallelizable with**: 02, 03, 04, 06, 07 (once 05 has landed)

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Needed by slice |
|---|---|---|
| Operation catalog registration and the in-process `invoke` seam | `execution-core` | 01 (then all) |
| Record families and persistence conventions | `execution-core` | 01 |
| Repository Execution Unit identity | `execution-core` | 01, 05 |
| Actor provenance and the operator-only channel (`operator_channel_required`) | `execution-core` | 03 |
| Lease primitive: heartbeat, expiry, reconciliation before reclamation | `execution-core` | 05 |
| Infrastructure Retry allowance accounting | `execution-core` | 04 |
| Normalized content hashing over line endings | `data-handling` | 01, 02 |
| Redaction sink enforcement interface | `data-handling` | 01, 04, 06, 07 |
| Execution Rule Snapshot binding and limit values (anchor neighbour count, rerun bound, stability defaults, mutation opt-in) | `config-and-snapshot` | 01, 04, 08 |
| Approved verification command reference and its declared coverage collection | `repository-readiness` | 01, 03, 06, 07 |
| Artifact Location Mapping schema | `repository-readiness` | 01 (report storage location), 06, 07 |
| PBI Worktree path and its checked-out revision | `pbi-execution-loop` | 01, 05 |
| Merge candidate and current target revision pair with its touched-path diff | `git-integration` | 08 |

### Contracts this spec PUBLISHES for other specs

| Contract name | Defining slice | Specs waiting on it |
|---|---|---|
| Normalized finding shape, content anchor, derivation record, count fallback | 01 | every adapter slice here (06, 07, 08), `entropy-gate`, `baseline-transitions` |
| `CheckAdapter` / `CheckRun` / `CheckOutcome` interface, including `pass_fail` and `adapter_failure` | 01 | `demo-mode` (stub adapter satisfies the real interface), `entropy-gate`, `pbi-execution-loop` |
| `StructuredReport` binding (revision, tool version, rule set version, command, coverage) | 01 | `entropy-gate`, `baseline-transitions` |
| Tree-sitter enclosing-symbol derivation and grammar version | 02 | `entropy-gate`, `baseline-transitions` (rule mappings plus per-rule count fallback), `release-engineering` (new engine dependency) |
| Evidence completeness rule and `FindingClassification` scope/invalidation | 03 | `entropy-gate`, `baseline-transitions`, `dashboard` (displaying a classification) |
| Report reuse and invalidation key | 03 | `entropy-gate`, `baseline-transitions` |
| `CheckStabilityDeclaration` and observed instability as a check problem | 04 | `entropy-gate` (blocking reason), `baseline-transitions`, `config-and-snapshot` (storage) |
| Adapter failure classification `infrastructure` \| `permanent` | 04 | `execution-core` (retry accounting), `entropy-gate` |
| `CheckResourceDeclaration` and scoped allocation projection | 05 | `pbi-execution-loop` (dispatch eligibility), `entropy-gate` |
| Mutation finding emission under the `mutation:<operator>` rule namespace | 08 | `entropy-gate` |

### Risks / judgement calls

**Splitting tree-sitter out of slice 01 is the call most worth reviewing.** The handoff names one contract — "normalized finding shape, content anchor, tree-sitter symbol derivation" — and I split it across slices 01 and 02. The argument for splitting: adapters never derive identity themselves, so the five adapter slices and the three validity/stability/resource slices can all start once 01 lands, and grammar wiring (a new engine dependency, six-plus grammars, build and packaging consequences) does not sit on the critical path of six other slices. The argument against: spec 13 and spec 15 are written against the *final* identity, so they effectively wait for 02 anyway, and shipping 01 alone leaves a brief window where identity means something narrower than the settled contract. If the operator prefers one atomic contract, merge 02 into 01 and accept a larger, slower slice 01.

**Slice 03 bundles three things** — completeness, operator classification, and reuse. They share a single question ("may this stored report serve as evidence right now?") and a single consumption point, which is why I kept them together, but classification is the only operator-facing surface in this spec and could reasonably become its own slice with the CLI parity test. I resisted because a classification slice without the completeness rule it escapes has nothing to demonstrate against.

**`pass_fail` sits in 03, not 01.** The type is defined in slice 01's outcome union; the *rule* that it satisfies a mandatory check yet cannot feed non-regression is a comparison-input concern, so its enforcement and test live with evidence validity.

**Gitleaks as slice 01's reference adapter** is a granularity choice. Slice 01 needs something real to be demoable, and Gitleaks is the only tool in the approved set that is language-agnostic, flat, and free of package-manager resolution. The cost is that the cross-language secrets adapter is not in an ecosystem slice where a reviewer might look for it. The configured license check, similarly, is distributed into slices 06 and 07 rather than centralized, because license tooling is per-ecosystem.

**The mutation adapter gets its own slice, and I recommend keeping it that way.** It is two tools across two ecosystems, so folding it into 06 and 07 is superficially tempting — but its substance is not parsing. It is diff scoping, the killed-by-timeout exclusion, a per-mutant bound derived from measured suite duration, the deliberate absence of a wall-clock cap, and comparability enforced by a machine-scoped lock rather than a tolerance. That is one coherent body of reasoning that would be split awkwardly and duplicated across two ecosystem slices. It is also off by default, so it can land last without blocking spec 13, and it is the one slice whose cost profile the operator should expect to feel: enabling it serializes mutation runs machine-wide and drops observed parallelism. Its surviving mutants arrive at the entropy gate as ordinary findings with no special case, which is what keeps it out of spec 13's scope entirely.

**The diff source for mutation scoping is my least confident cross-spec attribution.** I named the contract "merge candidate and current target revision pair with its touched-path diff" against `git-integration`, since spec 14 owns worktree and branch operations and the candidate-versus-target pairing. It could plausibly be `pbi-execution-loop`. The contract name is what matters; the owner should be confirmed when spec 14's issues are written.

**Ordering I am least sure about**: slice 05 (resources) blocks slice 08 but nothing else, so if mutation is deprioritized, 05 could move later without cost. Conversely, if spec 11's dispatch scheduling starts early, it needs 05's declaration projection sooner than this spec's own sequencing implies. Slice 04 has no dependants inside this spec and could be scheduled anywhere after 01.

**One process note**: slice 05's lease test must run two operating-system processes. A same-process test passes against an in-process mutex and proves nothing about a `machine`-scoped lock — the spec calls this out explicitly and the acceptance criterion is written to make it non-optional.
