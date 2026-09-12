# Data handling: redaction, retention, and egress

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 04, wave 0)
Source: `PRD.md` §6.2
Created: 2026-09-11

## Problem Statement

A factory that records everything becomes a liability. Gantry persists agent output, command output,
provider responses, prompts, diffs, and findings — and every one of those can contain a token pasted
into a log line, a signed URL in an error message, or a private key echoed by a misconfigured tool.
Once written to SQLite, an envelope, a handoff memo, or a dashboard feed, it is there permanently and
in a place the operator does not think of as sensitive.

The same recording creates a second problem. An operator who runs Gantry against a private repository
needs to know which content leaves their machine and where it goes. "The CLI runs locally" answers
nothing: a locally launched CLI can send an entire diff to a remote model. `PRD.md` states the policy —
egress is declared per role and driver, a role may use only an allowed driver and payload class,
missing authorization blocks dispatch — and states plainly that "egress classification follows actual
processing destinations, not the location of the executable".

And a third: retaining everything conflicts with retaining nothing. Full diffs and prompts by default
are both a leak risk and a storage problem, but minimal records still have to support handoffs,
resumption, and audit. The PRD requires references by default with explicit opt-in for detail, and
requires that "a retained record must identify where the required versioned content can be obtained".

All three policies are agreed. Every mechanism is deferred: "redaction rules, secret sources, and
confidence behavior remain to be specified", "exact retention fields and redacted-summary rules remain
to be specified", "egress declaration, payload classification, provider identity, and enforcement
mechanics remain to be specified".

## Solution

One redaction pipeline stands between every output and every place output can land. Nothing reaches
SQLite, an envelope, a handoff memo, a dashboard feed, or a repository artifact without passing through
it, including on error paths. It runs declared detectors, replaces matches with markers, and records
only detector identities and counts as metadata. When it cannot establish confidence that an output is
clean, it refuses to persist or display the full content and marks the affected operation or check as
blocked for review — failing closed, because the absence of a detected secret is not proof that
arbitrary output is safe.

Retention is reference-first by default. A retained record holds identities, timestamps, statuses,
hashes, redacted summaries, and evidence metadata, plus a replayable reference — a Git revision and
path, a provider object identity, or a worktree location — that locates the versioned content again.
Detailed retention is a per-repository opt-in, still subject to redaction, and changing the setting
invalidates evidence that depended on content no longer retained.

Egress is a declared matrix over role, driver, and payload class, approved per repository and captured
in the execution rule snapshot. A dispatch is permitted only when its role, its resolved driver, and
every payload class it carries appear in the matrix. Classification follows where content is actually
processed, so a detached CLI that reaches a remote model is remote egress. Missing or ambiguous
authorization blocks dispatch rather than defaulting either way.

## User Stories

1. As an operator, I want every output redacted before it is stored anywhere, so that a secret in a log line does not become a permanent record.
2. As an operator, I want redaction applied to error paths too, so that the failure output that nobody planned for is not the one that leaks.
3. As an operator, I want redaction applied to dashboard display as well as storage, so that a screen share does not expose what the database refused to keep.
4. As an operator, I want no persistence path that bypasses redaction, so that a new writer added later cannot quietly skip it.
5. As an operator, I want the values of environment variables my configuration references treated as secrets, so that the credentials I declared are detected by name rather than by luck.
6. As an operator, I want declared pattern detectors for tokens, private keys, and signed URLs, so that common shapes are caught even when I did not declare them.
7. As an operator, I want my repository's configured secret scanner rules reused when present, so that redaction agrees with the scanner I already trust.
8. As an operator, I want detector rules versioned, so that I can tell which ruleset produced a given redaction.
9. As an operator, I want only detector identities and counts recorded as redaction metadata, so that the metadata does not reveal what it protected.
10. As an operator, I want no offsets or lengths recorded, so that the shape of a secret cannot be reconstructed from the audit trail.
11. As an operator, I want output that cannot be confidently cleaned withheld rather than stored partially, so that uncertainty never resolves toward exposure.
12. As an operator, I want an unconfident redaction to mark the affected operation or check blocked for review, so that withholding content is visible rather than silent.
13. As an operator, I want to see that content was withheld and why, so that I know to inspect it myself.
14. As an operator, I want a redaction failure never to be reported as a passing check, so that a gate cannot pass because its evidence was unreadable.
15. As an operator, I want references, hashes, statuses, and summaries retained by default rather than full content, so that my database does not accumulate diffs and prompts.
16. As an operator, I want every retained record to say where its full versioned content can be obtained, so that a reference is actually replayable.
17. As an operator, I want a record whose source content is gone to block reconciliation rather than be treated as complete, so that resumption does not proceed on a broken reference.
18. As an operator, I want to opt into detailed retention per repository, so that I can trade storage for depth where I choose to.
19. As an operator, I want detailed retention still subject to redaction, so that opting in never opts out of secret protection.
20. As an operator, I want the retention setting captured in the execution rule snapshot, so that a change does not retroactively alter a running execution's records.
21. As an operator, I want changing retention to invalidate evidence that depended on content no longer kept, so that a gate cannot pass on evidence I can no longer inspect.
22. As an operator, I want handoff memos to carry remaining criteria, modified file references, and the relevant failure rather than raw history, so that continuity does not mean copying a conversation.
23. As an operator, I want the dispatch payload distinguished from its retained representation, so that an agent can receive full context that is not permanently stored.
24. As an operator, I want to declare, per role and driver, which classes of my repository content may leave this machine, so that routing is a decision I make rather than a default I discover.
25. As an operator, I want a dispatch blocked when its role and driver combination is not in my approved matrix, so that content never reaches an unapproved destination.
26. As an operator, I want a dispatch blocked when it carries a payload class my matrix does not allow for that destination, so that an approved driver cannot receive more than I permitted.
27. As an operator, I want egress classified by where content is actually processed, so that a locally launched CLI reaching a remote model counts as remote.
28. As an operator, I want secrets prohibited regardless of egress approval, so that approving a destination never approves sending credentials to it.
29. As an operator, I want missing or ambiguous egress authorization to block, so that silence is never read as permission.
30. As an operator, I want fully local processing available when I configure it, so that a repository can run without any egress at all.
31. As an operator, I want the provider identity for each egress destination recorded, so that the audit trail names where content went.
32. As an operator, I want the egress matrix captured in the snapshot, so that a change applies to new executions rather than to work already in flight.
33. As an operator, I want changing a driver for a role to require renewed egress authorization, so that swapping a harness does not silently change my data boundary.
34. As an operator, I want the payload classes of each dispatch recorded, so that I can audit what was sent, not just where.
35. As an auditor, I want redaction metadata, retention level, and egress decisions recorded alongside each record, so that the data boundary is reconstructible after the fact.
36. As a Gantry implementer, I want one pipeline interface every writer must go through, so that compliance is structural rather than a convention to remember.

## Implementation Decisions

### The redaction pipeline

A single pipeline sits between output producers and every sink. There is no second path. Sinks —
SQLite records, GTP envelope storage, handoff memos, dashboard feeds, generated repository artifacts —
accept only content that carries a pipeline result, so an unredacted string is not a valid input to a
sink. This is structural: a writer added later cannot bypass the pipeline without changing the sink
signature.

```ts
type RedactionOutcome =
  | { confidence: "clean"; content: string; metadata: RedactionMetadata }
  | { confidence: "redacted"; content: string; metadata: RedactionMetadata }
  | { confidence: "uncertain"; content: null; metadata: RedactionMetadata; reason: string };

type RedactionMetadata = {
  rulesetVersion: string;
  detectorHits: Array<{ detector: string; count: number }>;   // identity and count only
};
```

`uncertain` yields no content at all. There is no partial-content variant, because a partial store is
where a leak hides. An `uncertain` outcome marks the associated operation or check
`blocked_for_review`, which is visible in the projection and blocks the gate that depended on it. A
redaction failure is never reported as a passing check.

Detector sources, in declaration order:

1. Values of environment variables referenced by the effective configuration. These are matched as
   literal values without ever being stored.
2. Versioned pattern detectors for common shapes: bearer tokens, API key formats, PEM private key
   blocks, signed URL query parameters, connection strings with embedded credentials.
3. The repository's configured secret scanner rules where one is configured, so redaction agrees with
   the scanner the repository already trusts.

The ruleset version is recorded in every metadata record. Metadata holds detector identity and hit
count only — no offsets, lengths, prefixes, or hashes of matched content, because each of those narrows
a guess.

Confidence is determined by declared rules rather than inferred: output is `uncertain` when a detector
errors, when the output exceeds the configured inspection bound, when it is not decodable text, or when
a detector reports a partial match it cannot resolve. Everything else is `clean` or `redacted`.

### Retention

Default retention keeps identities, timestamps, statuses, content hashes, redacted summaries, evidence
metadata, and a replayable reference. It does not keep full diffs, prompts, source files, or build logs.

```ts
type ReplayableReference =
  | { kind: "git"; unit: RepositoryExecutionUnitId; revision: string; path?: string }
  | { kind: "provider"; provider: string; objectKind: string; objectId: string }
  | { kind: "worktree"; unit: RepositoryExecutionUnitId; pbi: PbiId; path: string }
  | { kind: "snapshot"; snapshot: SnapshotId; field: string };
```

**Content hashes are computed over normalized content, not over bytes on disk.** A repository with
`core.autocrlf` enabled has working-tree files whose line endings differ from the stored blob, so a hash
taken from the filesystem is platform-dependent: the same revision produces different hashes on Windows
and on Linux. Every content hash in the system — retained record hashes, governance document hashes in the
execution rule snapshot, and the content anchors in spec 12 — is therefore computed over content
normalized to a single line-ending convention, with a trailing-newline rule applied consistently. Hashing
raw filesystem bytes would make an execution's evidence unverifiable on a different platform and would
make a content anchor useless in any repository with mixed-platform contributors.

Every retained record that summarizes content carries at least one reference. A reference whose source
cannot be resolved is a missing-source condition: it blocks reconciliation and resumption rather than
being treated as a complete record. `worktree` references are the weakest, since cleanup can remove
them, so cleanup authorization must account for records that depend on them.

Detailed retention is a per-repository opt-in captured in the snapshot. It stores fuller content, still
through the pipeline, still subject to `uncertain` withholding. Turning it off invalidates evidence that
depended on content no longer retained: affected gate results return to `pending` and the invalidation
is recorded, following the snapshot-migration classification in spec 02.

The dispatch payload and its retained representation are separate artifacts. A builder may receive the
full approved context; what persists is the reference-first record. This is the distinction the PRD
review flagged as previously contradictory, and it is resolved by never treating the dispatch payload as
the record.

Handoff memo content is constrained to remaining criteria, completed criteria, modified file references,
and the relevant failure — the fields spec 11 constructs, retained under the same rules, never raw
conversation history.

### Egress

The matrix is a declared set of allowances over three axes:

```ts
type PayloadClass =
  | "spec_text" | "pbi_text" | "governance_doc"
  | "source_context" | "diff"
  | "check_report" | "finding"
  | "prompt_template" | "agent_output";

type EgressAllowance = {
  role: GtpRole;
  driver: DriverRef;                 // resolved driver identity, not a category
  destination: "local" | "remote";   // where processing actually occurs
  providerIdentity?: string;         // required when destination is remote
  allowedPayloadClasses: PayloadClass[];
  restrictions?: string[];           // repository-declared content limits
};
```

A dispatch is permitted only when an allowance matches its role and resolved driver and lists every
payload class the dispatch carries. Absent or ambiguous matching — two allowances disagreeing, or none
matching — blocks the dispatch. There is no permissive default in either direction.

`destination` is classified by where processing actually occurs, declared per driver during onboarding
and captured in the snapshot. A detached CLI that reaches a remote model is `remote` even though the
executable is local. A gateway is always `remote`. A static or stub driver is `local`. Changing a role's
driver requires renewed egress authorization, because the data boundary changed even though the role did
not.

Secrets are prohibited regardless of allowance. Egress approval governs repository content, never
credentials; the pipeline runs before dispatch payload assembly as well as before retention.

Each dispatch records its resolved driver, destination, provider identity, and the payload classes it
carried, so an audit can answer what was sent and not only where.

Enforcement is at the boundaries Gantry controls: payload assembly and dispatch. The honest limit,
stated in the projection rather than hidden: a native harness can send content through its own channels
without passing through Gantry, so enforcement covers Gantry-mediated dispatch, not every action a
harness can take. This follows §14.2 and ADR-0001.

## Testing Decisions

**What makes a good test here.** Tests drive operations that produce or retain output and assert on
what is observable: the stored record's content and metadata, the projection's blocked-for-review
state, the rejection code on a blocked dispatch, and the recorded egress decision. Tests never call the
pipeline directly for behavioral claims — a pipeline that works but is not wired into a sink is the
exact failure this spec exists to prevent, so its use is proven through the sinks.

One exception is deliberate: detector coverage is tested through the pipeline's own interface, because
enumerating detector cases through operations would be slow and would obscure what is being asserted.
Those tests assert only on `RedactionOutcome`, never on internals.

**The seam.** The same seam as spec 01. A fake harness driver and fake check adapter are scripted to
emit outputs containing planted secret-shaped strings, undecodable bytes, oversized output, and a
detector-error trigger.

**Modules under test.** The pipeline and its detector sources, sink enforcement, confidence
classification and blocked-for-review propagation, retention defaults and replayable references,
missing-source blocking, detailed-retention opt-in and its invalidation on change, the egress matrix and
its resolution, destination classification, and the recorded egress audit fields.

**Scenarios that must exist:**

- An agent output containing a referenced environment variable's value is stored with the value replaced and metadata naming the detector and count, with no offsets or lengths.
- The same output rendered to the dashboard feed is equally redacted.
- A check's failure output is redacted on the error path.
- Every sink rejects content lacking a pipeline result, demonstrated by type-level and runtime refusal.
- A detector error, undecodable output, and oversized output each yield `uncertain`, store no content, and mark the operation or check `blocked_for_review`.
- A gate whose evidence was withheld as `uncertain` does not pass.
- By default, a completed PBI's records hold references and summaries rather than the diff, and each summarizing record resolves to a reachable reference.
- A record whose Git revision no longer exists blocks reconciliation instead of being treated as complete.
- Enabling detailed retention stores fuller content that is still redacted; disabling it invalidates dependent gate results back to `pending` and records the invalidation.
- The retention level in effect for a record is the one captured in its snapshot, not the current setting.
- A dispatch whose role and driver are absent from the matrix is blocked; the rejection names the missing allowance.
- A dispatch carrying a payload class the matrix does not allow for that destination is blocked.
- Two conflicting allowances for the same role and driver block rather than resolving to either.
- A detached CLI declared to reach a remote model is classified `remote`; a stub driver is `local`.
- Changing a role's driver invalidates the prior egress authorization and blocks until reauthorized.
- A repository configured for local-only processing runs a full pipeline with no remote egress recorded.
- A secret-shaped string in a dispatch payload is redacted before assembly even when the destination is approved for that payload class.
- Each dispatch record names its resolved driver, destination, provider identity, and payload classes.

## Out of Scope

- **State machine, blocked states, invalidation mechanics** (spec 01): this spec decides when content must be withheld and what invalidation it triggers; the core owns the transitions.
- **Envelope shapes and dispatch assembly order** (spec 03): this spec constrains what may be retained from an envelope and what may be sent; the envelope contract is spec 03's.
- **Configuration schema and snapshot capture** (spec 02): the egress matrix, retention level, and detector ruleset reference are validated and captured there.
- **Onboarding declaration of egress and detectors** (spec 06): the interview that produces the matrix and detects the repository's secret scanner. This spec consumes the result.
- **Driver capability and destination declaration** (spec 10): what a driver actually does and where it processes content. This spec requires the declaration and classifies from it.
- **Secret scanning as a quality gate** (specs 12, 13): finding a committed secret in the repository is a check with findings; this spec is about not persisting secrets that pass through Gantry. The glossary distinguishes these and they must not be merged.
- **Handoff memo construction** (spec 11): which continuity fields are produced. This spec constrains what persists.
- **Cleanup and worktree removal** (spec 01): cleanup must account for records depending on `worktree` references; the authorization flow is the core's.
- **Dashboard rendering** (spec 17): the withheld-content and provenance display. This spec guarantees the data behind it.

Out of scope by product decision:

- Cryptographic guarantees about stored records. Redaction reduces exposure; it is not encryption at rest.
- Preventing a native harness from sending content outside Gantry. Enforcement covers Gantry-mediated dispatch, and the limitation is documented rather than overstated (§14.2, ADR-0001).
- Entropy-based secret discovery as a primary detector. Declared detectors and the repository's own scanner rules are the sources; unbounded entropy heuristics produce false positives that would withhold ordinary output.

## Further Notes

**Binding decisions.** ADR-0001's principle — never advertise a guarantee the integration cannot
enforce — is why the egress section states its enforcement boundary explicitly rather than claiming
that approved egress means no content can leave by another path.

**Glossary alignment.** Output Redaction, Telemetry Retention, and Data Egress Policy follow
`CONTEXT.md`, including its warnings: redaction is not "best-effort log filtering" and not a
"secret-free claim"; retention is not "full diff by default"; egress policy is not "implicit provider
routing" and is distinct from credential policy.

**Glossary gap for `/domain-modeling`.** Payload class, replayable reference, and redaction confidence
are introduced here without entries and should get them.

**Where the risk actually sits.** Failing closed on `uncertain` will block real work — an oversized
build log or a tool emitting binary output will withhold content and mark a check for review, and
operators will feel that as friction. The inspection bound and the undecodable-output rule are the two
dials, and both belong in configuration so a repository can widen them deliberately rather than having
the pipeline guess. The alternative — storing partial content on low confidence — is the failure mode
this spec exists to prevent, so the friction is the intended trade.

**Sequencing note.** Sink enforcement must land before any other spec writes a record, because
retrofitting it means auditing every writer. That makes this spec's pipeline interface the one piece of
wave 0 worth building first even though the spec sits fourth in the order of attack.
