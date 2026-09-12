# Configuration, rule snapshots, and governance precedence

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 02, wave 0)
Source: `PRD.md` §6.2, §8.2
Created: 2026-09-11

## Problem Statement

An operator configures a factory once and then expects the rules to hold still while work runs. Two
things break that expectation today, and `PRD.md` names both without resolving either.

First, configuration is layered — built-in defaults, a machine-wide file, a sparse repository override
— and three interfaces can write it. Without one validated store, the CLI, the dashboard, and the MCP
server would each merge and validate differently, an override could relax a limit it was never meant to
reach, and a secret could land in a file on disk. The PRD fixes the policy ("config writes go through
one validated `ConfigStore` shared by CLI, dashboard and MCP", "no secret ever lives in the config
file") but leaves the schema, the merge semantics, and the validation rules open.

Second, an execution that runs for hours reads its rules continuously. If an edit to the constitution,
an ADR, or a check command takes effect mid-flight, then work validated under the old rules sits beside
work validated under the new ones, approvals granted against one baseline silently govern another, and
nobody can say afterwards which rules produced a given merge. The PRD requires a fixed Execution Rule
Snapshot and says "snapshot storage, identity, and rule-change commands remain to be specified".

Underneath both sits a third problem: when the constitution, an ADR, the approved plan, and `AGENTS.md`
disagree, something has to decide, and an agent choosing silently is the outcome the PRD explicitly
forbids. The precedence order is fixed; the mechanism that applies it, and that recognizes a conflict
the order cannot resolve, is not.

## Solution

One `ConfigStore` owns reading, merging, validating, and writing configuration. It resolves built-in
defaults, then the machine-wide file, then the repository override into a single effective document and
validates that document as a whole, so a combination that is invalid cannot exist even when each layer
looks reasonable alone. Writes go through it from every transport, are validated before they land, and
back up the previous file. Secret values are rejected at validation: the schema accepts environment
variable names, never values.

At execution start, the store captures an Execution Rule Snapshot — the effective configuration plus
content hashes of the governance documents, approved verification commands, and tool versions that
govern this run — identified by a hash of its own content and stored immutably. Every dispatch,
approval, finding, and merge authorization records the snapshot that governed it. Later edits apply to
new executions. Moving an in-flight execution to a new snapshot is an explicit operator operation that
records the change, invalidates affected approvals, and marks affected evidence for revalidation.

Governance precedence is applied by resolving each rule that bears on a decision into a typed assertion
tagged with its source level, then taking the highest level for each rule key. Two assertions that
conflict at the same level are a conflict the order cannot resolve, so the affected transition blocks
and surfaces a proposed amendment rather than letting anyone choose quietly.

## User Stories

1. As an operator, I want one store to own every configuration read and write, so that the CLI, the dashboard, and the MCP server cannot disagree about my settings.
2. As an operator, I want defaults, machine settings, and repository overrides merged into one document and validated together, so that an individually valid override cannot produce an invalid whole.
3. As an operator, I want to keep my repository override sparse, so that I state only what differs and inherit the rest.
4. As an operator, I want a repository override unable to raise the global capacity limit, so that a single repository cannot consume more of my machine than I allowed.
5. As an operator, I want to know which layer produced each effective value, so that I can tell an inherited default from something I set.
6. As an operator, I want array-valued settings replaced rather than concatenated by an override, so that overriding a list means replacing it, not appending to it.
7. As an operator, I want secrets rejected by validation, so that a key cannot be written into a configuration file by accident.
8. As an operator, I want only environment variable names stored for credentials, so that my files and my database never contain a value worth stealing.
9. As an operator, I want a validation failure to explain which field and which layer is wrong, so that I can fix it without reading the schema.
10. As an operator, I want the previous file backed up on every save, so that a bad edit is recoverable.
11. As an operator, I want a write rejected wholesale when any part of it is invalid, so that I never end up with a half-applied change.
12. As an operator, I want roles that are configured but never invoked flagged, so that dead configuration does not look like working configuration.
13. As an operator, I want the resolved command for each role previewable before anything runs, so that I can see what will actually be executed.
14. As an operator, I want the rules of my execution fixed when it starts, so that editing a file mid-run cannot change what my in-flight work is judged against.
15. As an operator, I want the snapshot to cover governance documents as well as configuration, so that an edit to the constitution or an ADR does not leak into a running execution.
16. As an operator, I want each snapshot identified by its content, so that two executions under identical rules share an identity and a changed rule produces a new one.
17. As an operator, I want every approval, finding, and merge authorization to record its governing snapshot, so that I can reconstruct which rules produced any outcome.
18. As an operator, I want new executions to pick up my latest settings automatically, so that fixing a rule does not require touching anything else.
19. As an operator, I want moving an in-flight execution to new rules to be an explicit decision, so that it never happens as a side effect of an edit.
20. As an operator, I want a snapshot migration to invalidate the approvals it affects, so that my earlier consent is not reused under rules I had not seen.
21. As an operator, I want a snapshot migration to mark affected evidence for revalidation, so that a green gate under old rules does not carry into new ones.
22. As an operator, I want the snapshot unable to authorize a violation of the rules it captured, so that it is a record rather than a loophole.
23. As an operator, I want the snapshot unable to justify using a stale target revision, so that live repository protections still apply.
24. As an operator, I want conflicting rules resolved in the documented order, so that the outcome is predictable rather than a matter of which file was read first.
25. As an operator, I want provider protections and absolute security requirements to win over everything else, so that no local setting can weaken them.
26. As an operator, I want a lower-precedence document unable to relax a higher-precedence invariant, so that `AGENTS.md` cannot soften the constitution.
27. As an operator, I want a conflict the order cannot resolve to block the affected transition, so that an agent never picks silently.
28. As an operator, I want a blocking conflict surfaced as a concrete proposed amendment, so that I have something to decide rather than an error to interpret.
29. As an operator, I want to see which source level supplied each rule in a decision, so that I can audit why a transition was allowed or refused.
30. As an operator, I want changing the precedence order itself to require explicit governance approval, so that the tie-breaker cannot be edited casually.
31. As an operator, I want capacity, correction, and infrastructure limits to live in configuration with validated ranges, so that a typo cannot grant unlimited attempts.
32. As an operator, I want the default limits to match the approved policy without my having to write them, so that a fresh install is already correct.
33. As an operator, I want approved verification commands captured in the snapshot with their working directory and environment references, so that evidence is bound to the exact command that produced it.
34. As an operator, I want a changed verification command to invalidate evidence produced by the previous version, so that stale results cannot pass a gate.
35. As an operator, I want tool versions recorded in the snapshot, so that a silent upgrade does not invalidate comparisons without anyone noticing.
36. As an operator, I want the effective artifact locations captured in the snapshot, so that authoring, linting, and governance protection all use the same mapping for the whole execution.
37. As a host harness, I want to read the effective configuration through a read operation, so that I never parse configuration files myself.
38. As a host harness, I want a dispatch refused when role routing cannot be resolved, with setup guidance, so that I report a fixable problem instead of failing obscurely.
39. As a Gantry implementer, I want the effective configuration expressed as one validated type, so that consumers receive a resolved document rather than three layers to merge again.
40. As an auditor, I want snapshots stored immutably and never garbage-collected while any record references them, so that historical evidence remains interpretable.

## Implementation Decisions

### ConfigStore

One module owns the full lifecycle: locate, read, merge, validate, expose, write, back up. Every
transport calls it; none reads or writes a configuration file directly. Its read surface returns a
resolved, validated, immutable document plus per-field provenance.

Layer order is built-in defaults, then `~/.gantry/config.json`, then the repository's
`.gantry/config.json`. Merge semantics are fixed:

- Objects merge key by key.
- Arrays are replaced wholesale. Overriding a list means stating the new list.
- An explicit `null` in a higher layer clears the value rather than being treated as absent.
- Unknown keys are a validation error, not a preserved extension. Configuration is not an
  extensibility surface — that distinction belongs to GTP envelopes, which do preserve unknowns.

Validation runs on the merged document, not per layer, because the constraints that matter are
relational: a repository capacity limit cannot exceed the global one, a role routed to a gateway cannot
be a file-mutating role, a check declaring a shared resource must declare its serialization behavior.
Validation returns every violation at once with the field path and the layer that supplied the value.

Writes are whole-document and transactional from the caller's perspective: the merged result is
validated before anything is written, the target layer's previous file is copied to a `.bak` sibling,
and the write either fully lands or leaves the original in place. A write touching a field the target
layer may not set — a repository override attempting to raise a global limit — is rejected with the
field path.

Configuration shape, by section: host and role routing, context policy (watermark, PBI context budget),
capacity limits (global, per repository, per driver), budgets (correction, infrastructure, backoff base),
Git workflow policy, artifact location mapping, verification commands and declared resources, data
handling (egress matrix, retention level), and dashboard settings. Approved defaults are set here, not
discovered at runtime: global capacity two, correction budget five, infrastructure retries three,
context watermark forty percent, PBI initial context budget fifteen percent.

### Secrets

The schema has no field whose type admits a credential value. Credentials are referenced by environment
variable name, and validation rejects a name field whose content fails to look like an environment
variable name, and rejects any string in the document matching the configured secret detectors. The
check is a defense against accident, not a security boundary; the boundary is that no field exists to
put a secret in.

### Execution Rule Snapshot

Captured by the core at execution start, before the plan-approval transition, and stored immutably.
Contents:

- The resolved effective configuration document.
- Content hashes and resolved paths of the governance documents in effect: `CONSTITUTION.md`, each
  applicable ADR, the root `AGENTS.md`, and the approved spec and PBI artifacts.
- The approved verification commands, each with its working directory, environment variable references,
  declared effects, declared resources, and stability criterion.
- Observed versions of the tools those commands invoke.
- The effective artifact location mapping.
- The engine and GTP protocol versions.

Identity is a hash over the canonicalized snapshot content, so identical rules yield one identity and
any change yields a new one. Snapshots are immutable and retained while any record references them.

Every dispatch, approval, finding, gate result, and merge authorization records its snapshot identity.
A record whose snapshot is unavailable is not silently reinterpreted: it blocks and requires
reconciliation.

Governance document content is hashed, not copied, with the resolved location retained so the versioned
content can be recovered from Git. A hash whose content cannot be recovered is a missing-source
condition to reconcile, not a reason to proceed.

### Snapshot migration

`execution.migrateRuntime` and its rule-change counterpart are operator-only. A migration records the
old and new snapshot identities and the reason, then classifies every existing record: approvals whose
governing rules changed are invalidated, gate results whose rules or commands changed return to
`pending`, and unaffected records keep their original binding. Affected work is revalidated before it
advances. New executions always capture a fresh snapshot from current configuration, so the normal path
for a rule change is simply the next execution.

A snapshot never authorizes anything its own captured rules forbid, and never justifies using a stale
target revision. Live provider protections and current-target verification are checked at the moment of
integration regardless of what the snapshot says.

### Governance precedence

Rules that bear on a decision are resolved into typed assertions, each tagged with its source level:

```ts
type SourceLevel =
  | 1 // provider protections and absolute security requirements
  | 2 // the approved execution rule snapshot
  | 3 // CONSTITUTION.md
  | 4 // applicable ADRs
  | 5 // approved spec and PBIs
  | 6 // AGENTS.md and operational configuration

type RuleAssertion = {
  key: string;            // the rule being asserted, e.g. "merge.requiresApprovals"
  value: unknown;
  level: SourceLevel;
  source: { document: string; contentHash: string; location?: string };
};

type Resolution =
  | { resolved: true; value: unknown; level: SourceLevel; overridden: RuleAssertion[] }
  | { resolved: false; conflict: RuleAssertion[] };   // same level, incompatible values
```

Resolution takes the lowest-numbered level asserting a key. Assertions it overrides are retained in the
resolution so an audit can show what was outranked. Two incompatible assertions at the same level are
unresolvable: the affected transition blocks, and the core surfaces a proposed governance or plan
amendment naming both sources and the conflicting key. A lower level may not relax a higher-level
invariant — an assertion that would weaken a higher-level rule is rejected as an override attempt rather
than silently losing.

Changing the precedence order is itself a level-3 change requiring explicit governance approval.

Resolutions are recorded with the decision they informed, so the audit trail answers not only what was
decided but under which rule from which document version.

### Dead configuration

The store computes, from execution history, which configured roles have never been invoked and which
verification commands have never produced evidence, and exposes that as part of its read surface. It is
advisory: it never blocks anything. It exists because a role configured with a typo is silent until the
moment it matters.

## Testing Decisions

**What makes a good test here.** Tests exercise the store through the operation core's `config.read`
and `config.write`, and exercise snapshots and precedence through the operations that consume them.
Assertions are on resolved values, provenance, rejection codes, and the recorded snapshot or resolution
attached to a decision. Tests never assert on file formatting, key order, merge implementation, or Zod
internals.

**The seam.** The same seam as spec 01. Layer files are written into a temporary home and repository
directory by fixture helpers, and everything else goes through `invoke`. A precedence test does not call
a resolver directly; it drives an operation whose outcome depends on the resolution and asserts on the
recorded resolution, because a resolver nobody consults is not a governance mechanism.

**Modules under test.** Layer resolution and merge semantics, whole-document validation and its
relational constraints, write authorization per layer, backup behavior, secret rejection, snapshot
capture and identity, snapshot migration and its invalidation classification, precedence resolution and
conflict blocking, and dead-configuration reporting.

**Scenarios that must exist:**

- A sparse repository override inherits every unstated value, with provenance naming the supplying layer.
- Two individually valid layers whose merge violates a relational constraint are rejected, naming both the field and the layer.
- A repository override attempting to raise the global capacity limit is rejected.
- An override replaces an array rather than appending to it, and an explicit null clears an inherited value.
- An unknown configuration key is rejected.
- A file-mutating role routed to a gateway is rejected.
- A write with any invalid field leaves the previous file untouched, and a valid write produces a `.bak`.
- A string matching a secret detector anywhere in the document is rejected.
- A snapshot captured at execution start is unaffected by a subsequent edit to configuration, the constitution, or an ADR; the running execution continues under the captured rules and a new execution captures the edit.
- Identical rules produce one snapshot identity; changing any captured input produces a new one.
- A decision records its snapshot identity, and a record whose snapshot is missing blocks rather than being reinterpreted.
- A migration invalidates affected approvals, returns affected gates to `pending`, leaves unaffected records bound to their original snapshot, and is refused from a non-operator channel.
- A changed verification command invalidates evidence produced by its previous version.
- A tool version change recorded in the snapshot invalidates comparison evidence that depended on it.
- Precedence: a level-6 assertion loses to a level-3 one, and the resolution records what was overridden.
- A level-6 assertion attempting to weaken a level-3 invariant is rejected as an override attempt, not merely outranked.
- Two incompatible assertions at the same level block the transition and produce a proposed amendment naming both sources.
- A snapshot claiming permission for something its captured rules forbid does not grant it.
- Current-target verification still applies at integration regardless of the snapshot.

## Out of Scope

- **State machine, operations, persistence, budget accounting** (spec 01): this spec supplies limit values and snapshot content; the core enforces and counts.
- **Envelope contracts** (spec 03): every envelope binds a snapshot identity; the envelope shape is spec 03's.
- **Redaction, retention, egress enforcement** (spec 04): this spec holds the egress matrix and retention level as validated configuration; spec 04 defines their meaning and enforcement.
- **Setup and onboarding** (specs 05, 06): the conversational interview that writes configuration, detection of tools and artifact locations, verification command approval, and preparation authorization. This spec validates and stores what those produce.
- **Dashboard Settings UI and capability token** (spec 17): the form, live preview rendering, and token issuance. This spec guarantees that dashboard writes traverse the same store with the same validation.
- **Git workflow preset semantics** (spec 14): what a branch naming or target policy means operationally. This spec validates its shape and captures it in the snapshot.
- **Check execution, stability evaluation, resource locking** (spec 12): this spec validates declarations; spec 12 acts on them.
- **Baseline transition approval** (spec 15): how a change to the governance baseline is proposed, compared, and adopted. This spec provides snapshot identity and migration; spec 15 provides the transition.
- **Executable ADR rules** (spec 13): turning an ADR into a machine-checkable assertion. This spec resolves assertions once they exist and treats a prose-only ADR as a level-4 source without machine-checkable keys.

Out of scope by product decision:

- Live configuration reload into a running execution. Rules are fixed per execution by design (§6.2).
- A per-role or per-gate correction allowance. The budget is one shared allowance per PBI (§6.2).
- Multi-user permission scoping of settings. Global versus repository scope is a configuration-layer distinction, not an authorization model (§8.2).

## Further Notes

**Binding decisions.** Nothing here contradicts ADR-0001 or ADR-0002. The snapshot's inability to
override live provider protection is the configuration-side expression of ADR-0001's rule that Gantry
claims only the control an integration actually exposes.

**Glossary alignment.** Execution Rule Snapshot, Governance Precedence, and Verification Command
Approval follow `CONTEXT.md`, including the terms it marks to avoid: a snapshot is not "live settings",
and precedence is not "document order on disk".

**Glossary gap for `/domain-modeling`.** Rule assertion, source level, and field provenance are
introduced here without entries and should get them.

**Where the risk actually sits.** Precedence resolution assumes rules can be expressed as keyed
assertions, which is straightforward for configuration and provider protection and much harder for
prose in a constitution or an ADR. The honest position is the one taken above: a prose-only document
participates at its level but contributes no machine-checkable keys, so it can block a transition
through conflict but cannot silently resolve one. Expect spec 13 to push on this when executable ADR
rules arrive, and expect the set of recognized keys to grow rather than the mechanism to change.

**Sequencing note.** This spec depends only on spec 01, and specs 05, 06, and 17 all write through it,
so settling the schema sections early is worth more than settling any single field. The one decision to
make before starting is whether unknown configuration keys are rejected — stated above as rejected,
deliberately opposite to the GTP envelope rule — because reversing it later would loosen validation for
every consumer.
