# Demo mode: fixture pipeline with stub agents

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 07, wave 1)
Source: `PRD.md` §2.3, §7.1, §8.2, §13.6
Created: 2026-09-11

## Problem Statement

Someone evaluating Gantry has to decide whether it is worth configuring before they can see it work,
and `PRD.md` identifies that ordering as "the #1 adoption blocker of agent-orchestration tools". The
real pipeline needs a prepared repository, approved verification commands, a configured harness, and
credentials. Anyone unwilling to do that work first sees nothing at all, and a README cannot
substitute — the thing worth seeing is a slice moving through dispatch, gates, correction, and
integration, which is a behavior rather than a description.

The PRD commits to a specific answer: a full pipeline on a fixture project with stub agents, no API
keys, under two minutes. It also attaches two constraints that are easy to violate while building it.
The demo must not mutate a user's real project to demonstrate integration — so it cannot simply run
against the current directory — and the interface must identify simulated evidence so demo results are
not mistaken for production readiness. That second constraint is the sharper one: a demo that produces
records indistinguishable from real ones becomes a way to show a green factory that verified nothing.

A third risk follows from the first two. If demo records live alongside real ones without a boundary, a
real execution could reference simulated evidence, or a readiness report could be derived from a
pipeline that never ran a check.

## Solution

`gantry init --demo` provisions a self-contained fixture repository in its own location, registers it
as a Repository Execution Unit marked `demo`, and runs the full pipeline against it using stub drivers
that return pre-recorded GTP envelopes and stub check adapters that return pre-recorded findings. No
credentials, no network, no harness, and no write anywhere near the user's project.

The demo mode marker lives on the unit and propagates to every record produced under it. A hard
invariant enforces the boundary: no operation may relate a record in one mode to a record in the other.
A live execution cannot reference simulated evidence, a demo approval cannot authorize a real merge, and
no readiness assessment can be derived from demo records. Every projection carries the marker, so the
CLI and the dashboard label simulated evidence without needing to remember to.

The fixture is scripted to exercise the parts of the pipeline worth seeing rather than a happy path: one
slice completes cleanly, one fails a gate and is corrected within budget, and one surfaces an entropy
regression that blocks. Re-running is one operation that removes the demo unit and rebuilds it, which is
safe precisely because its scope is a unit that owns nothing external.

## User Stories

1. As someone evaluating Gantry, I want to see a full pipeline run without configuring anything, so that I can judge the tool before investing in setup.
2. As someone evaluating Gantry, I want the demo to need no API key or credential, so that I can try it on a machine where I have no keys.
3. As someone evaluating Gantry, I want the demo to need no network access, so that it works on a plane or behind a restrictive proxy.
4. As someone evaluating Gantry, I want the demo to reach a visible pipeline in under two minutes, so that trying it costs me almost nothing.
5. As someone evaluating Gantry, I want the demo to run against its own fixture project, so that it never touches the repository I care about.
6. As someone evaluating Gantry, I want to see spec authoring, slicing, building, gates, and integration, so that I understand the whole shape rather than one step.
7. As someone evaluating Gantry, I want to see a gate actually block something, so that I learn what the tool is for rather than watching everything pass.
8. As someone evaluating Gantry, I want to see a correction attempt consumed and the slice recover, so that I understand how failure is handled.
9. As someone evaluating Gantry, I want to see an entropy regression block a delivery, so that the differential policy is concrete rather than abstract.
10. As someone evaluating Gantry, I want to re-run the demo with one action, so that I can watch a part I missed.
11. As someone evaluating Gantry, I want the demo to be deterministic, so that what I describe to a colleague is what they will see.
12. As an operator, I want every demo record labeled as simulated, so that I can never mistake it for evidence about my own repository.
13. As an operator, I want the label to come from the unit and propagate automatically, so that a new record type cannot forget to carry it.
14. As an operator, I want the dashboard to show a persistent indicator while viewing demo data, so that a screenshot cannot be mistaken for a real run.
15. As an operator, I want the CLI to state that evidence is simulated in its output, so that a pasted terminal log is not misleading either.
16. As an operator, I want a live execution unable to reference a demo record, so that simulated evidence cannot support real work.
17. As an operator, I want a demo approval unable to authorize anything in a live unit, so that the demo's consent has no reach.
18. As an operator, I want no readiness assessment derived from demo records, so that the demo cannot make an unprepared repository look ready.
19. As an operator, I want the demo unit clearly separated in every listing, so that it does not clutter or confuse my real executions.
20. As an operator, I want the demo's fixture location stated before it is created, so that I know exactly what appears on my disk.
21. As an operator, I want the demo to create no Git remote and no provider object, so that it cannot produce an external effect.
22. As an operator, I want demo reset scoped to the demo unit alone, so that resetting cannot remove anything real.
23. As an operator, I want demo reset refused if aimed at a live unit, so that the convenient path cannot become the destructive one.
24. As an operator, I want the demo to exercise the real operation core rather than a parallel mock pipeline, so that what I see reflects actual behavior.
25. As an operator, I want the demo's stub drivers to be the same driver interface real adapters implement, so that the demo proves the seam rather than bypassing it.
26. As an operator, I want the demo's timing measured and reported separately from real-repository targets, so that a fast demo is never presented as a fast real pipeline.
27. As an operator, I want the demo to work immediately after installation with no prior setup, so that it does not depend on the machine factory being configured.
28. As an operator, I want the demo removable without a trace beyond the records I choose to keep, so that trying it leaves my machine clean.
29. As a Gantry maintainer, I want the fixture and its scripted envelopes versioned with the package, so that a change to the protocol updates the demo in the same commit.
30. As a Gantry maintainer, I want the demo used as a regression test of the whole pipeline, so that it cannot rot while remaining a shipped feature.
31. As a Gantry maintainer, I want the demo's scripted evidence to include a deliberately invalid result, so that Protocol Failure handling is visible and tested.
32. As someone writing documentation, I want the demo's output stable enough to reference in a quickstart, so that the documented walkthrough matches reality.

## Implementation Decisions

### Isolation and location

The fixture is materialized from templates shipped in the package into a dedicated directory under the
machine factory, not into the current working directory and not into any user repository. The path is
printed before creation. It is a real Git repository — initialized, committed, with no remote
configured — because unit identity derives from an actual Git common directory and worktree behavior
must be genuine.

Creating no remote is what makes external effects structurally impossible: there is nothing to push to
and no provider to call. Demo Git workflow policy is local mode.

`gantry init --demo` does not require `gantry setup` to have run. It provisions the minimum machine
factory it needs — the database and a demo-scoped configuration — so the first command a new user runs
can be the demo.

### Mode as a unit property

The `demo` marker is a property of the Repository Execution Unit, set at registration and immutable
afterwards. Every record is scoped to a unit, so the marker reaches every record without each record
type carrying its own flag and without any writer having to remember.

The boundary is a validated invariant in the operation core, not a convention:

- No operation may accept inputs referencing units of different modes.
- No record may reference a record belonging to a unit of a different mode.
- Approvals, snapshots, findings, and merge authorizations are scoped to their unit and therefore to
  their mode.
- Readiness assessments derive only from live units.

Every state projection carries the mode, so the CLI and dashboard render the simulated indicator from
data rather than from a flag passed through the call site. A projection for a demo unit that omitted the
marker would be a bug detectable in tests.

### Stub drivers and adapters

Stubs implement the same driver and check adapter interfaces the real adapters in specs 10 and 12
implement. They resolve a scripted response from the assignment's role, PBI, and iteration, so the
demo exercises the real dispatch, validation, completion, gate, correction, and integration paths. There
is no parallel demo pipeline; a demo run and a real run differ only in which driver is resolved.

Stub drivers declare their Integration Capability honestly: context usage is reported as
`self_reported` from the scripted envelope, never as `measured`, because nothing is measuring
anything. Watermark handoff in the demo is triggered by a scripted `needs_handoff` result rather than
by an observed threshold, which is both truthful and the only option available to a stub.

Scripted content is versioned with the package alongside the envelope schemas, so a protocol change
updates the demo in the same commit.

### The scripted scenario

Three slices, chosen to show the product's argument rather than a happy path:

1. A slice that completes cleanly: dispatch, all criteria completed, Gantry-verified tests pass, gates
   pass, local merge confirmed, integrated.
2. A slice that fails a gate and recovers: initial gate evaluation produces findings, one correction
   attempt is dispatched and consumed, revalidation passes, integration proceeds. The projection shows
   the attempt count moving from zero to one, making the budget visible.
3. A slice that is blocked by an entropy regression: the scripted check adapter returns a finding present
   in the candidate and absent in the target, the entropy gate blocks, and the projection names the
   concrete regression rather than a score.

Two additional scripted moments, brief but present because they are the behaviors hardest to believe
without seeing:

- One dispatch returns an invalid result, producing a Protocol Failure that preserves the work and
  advances nothing.
- One slice depends on another, so the dependent waits in `awaiting_dependency` until the prerequisite is
  integrated.

The demo ends with the pipeline in a state that includes a blocked slice, deliberately. A demo where
everything passes teaches the wrong thing about what the tool does.

### Reset

`demo.reset` removes the demo unit's records, worktrees, and fixture and rebuilds it. It is exempt from
the two-step cleanup manifest required for live units, and the justification is specific rather than
general: the demo unit has no external effects, no remote, no provider objects, and no dependent
executions, so there is nothing for a manifest to protect. The exemption is enforced narrowly —
`demo.reset` applied to a live unit is rejected — rather than by loosening cleanup authorization.

### Measurement

The demo records its own wall-clock duration from command invocation to a visible pipeline, and the
dashboard's SSE latency is measured on demo traffic. Both are reported as demo measurements, separate
from real-repository readiness targets, per §14.3 item 10. A fast demo is never presented as evidence
about a real pipeline's time-to-first-value, which the PRD itself makes conditional on repository
readiness and operator approvals.

## Testing Decisions

**What makes a good test here.** Tests run the demo through the same operation core as everything else
and assert on the resulting state projections, the mode boundary rejections, and the sequence of states
each scripted slice passes through. They never assert on rendered CLI text or dashboard markup beyond
the presence of the simulated marker in the projection data.

**The seam.** The same seam as spec 01, with the demo's own stub drivers in place of the generic fakes.
This is the one spec where the fakes under test are shipped code rather than test doubles, which is
deliberate: the stubs are a product feature and deserve the same treatment as any adapter.

**Modules under test.** Fixture provisioning and its location, unit registration with the demo mode
marker, mode boundary enforcement, stub driver and adapter response resolution, the scripted scenario's
state sequences, capability declaration honesty, reset scoping, and the demo's own timing measurement.

**The demo as a regression test.** The scripted scenario runs in CI as a full-pipeline integration test.
This is the reason the scenario is deterministic: it doubles as the only test that exercises every wave
of the product end to end, and it fails loudly when any spec's behavior changes underneath it. Later
specs extend the scripted scenario rather than adding a parallel end-to-end suite.

**Scenarios that must exist:**

- The demo runs to completion with no credential, no network access, and no prior `gantry setup`.
- The fixture is created only at the printed path; the current working directory and any user repository are unmodified.
- The fixture has no Git remote, and no provider operation is attempted during the run.
- Every record produced carries the demo mode through its unit, verified by projection rather than by inspecting storage.
- An operation relating a demo record to a live record is rejected; the rejection names the mode boundary.
- A demo approval does not authorize any action in a live unit.
- A readiness assessment for a live unit ignores demo records entirely.
- Slice one reaches `integrated` through implementation completion, gates, and local merge confirmation.
- Slice two consumes exactly one correction attempt and the projection shows the count.
- Slice three is blocked by an entropy regression naming the concrete finding, not a score.
- The scripted invalid result produces a Protocol Failure that preserves work and advances nothing.
- The dependent slice waits in `awaiting_dependency` and becomes eligible only after its prerequisite is integrated.
- Stub context usage is projected as `self_reported`, never as `measured`.
- `demo.reset` rebuilds the fixture and is rejected when aimed at a live unit.
- The run's duration is recorded and reported as a demo measurement, distinct from any real-repository target.
- The demo's final state includes a blocked slice.

## Out of Scope

- **State machine, operations, mode boundary enforcement mechanics** (spec 01): this spec defines the demo mode property and the invariant it requires; the core enforces it.
- **Envelope contracts** (spec 03): scripted envelopes conform to them; they are not defined here.
- **Configuration and snapshots** (spec 02): the demo's scoped configuration is a minimal instance of the real schema.
- **Redaction and retention** (spec 04): demo records pass through the same pipeline; nothing is exempted.
- **Machine setup** (spec 05): `gantry setup` and skill installation. The demo deliberately does not require them, and the minimal provisioning it performs is the subset it needs.
- **Repository readiness** (spec 06): real diagnosis, detection, and approved preparation. The demo asserts that readiness never derives from its records.
- **Real harness adapters** (spec 10) and **real check adapters** (spec 12): the stubs implement the same interfaces those specs define.
- **Gate semantics** (spec 13): what makes a finding blocking. The demo scripts findings and observes the real decision.
- **Dashboard implementation** (spec 17): the persistent simulated indicator, SSE transport, and one-click re-run control. This spec guarantees the data and the operation behind them.
- **Documentation and the quickstart GIF** (spec 19).

Out of scope by product decision:

- A demo that runs against the user's real repository. The PRD forbids mutating a user's project to demonstrate integration (§7.1).
- A demo with real agents behind a shared key. The demo's value is that it needs no credential, and a hosted key would introduce egress with no approval path.
- A demo that exercises provider operations against a real GitHub repository. There is no remote, by design.
- Presenting demo timing as the real-pipeline target. §13.6 makes the real target conditional on readiness and approvals.

## Further Notes

**Binding decisions.** ADR-0001 is why the stubs declare `self_reported` context usage and script the
handoff rather than simulating a measured watermark: a capability that does not exist must not be
advertised, and a demo is exactly where an unearned guarantee would be most tempting to show.

**Glossary alignment.** Repository Execution Unit, Protocol Failure, Correction Attempt, Dependency
Readiness, and Quality Regression follow `CONTEXT.md`. The scripted scenario is built around the terms
the glossary marks as distinct, because those distinctions are what the demo is showing.

**Glossary gap for `/domain-modeling`.** Demo mode as a unit property, and simulated evidence as a
projection property, are introduced here without entries and should get them.

**Where the risk actually sits.** The under-two-minute target is the one claim in this spec that could
fail for reasons outside it. Fixture creation, database provisioning, three slices through the full
state machine, and Gantry's own re-execution of mandatory tests on each delivered revision all consume
time that grows as later specs add work. Measuring the duration in CI from the first commit — rather
than checking it once near release — is the only way the target survives, which is why the measurement
is part of this spec rather than of §13.

**Sequencing note.** This spec is placed fifth in the order of attack for a reason unrelated to its own
value: once the demo runs in CI, every subsequent spec inherits a working end-to-end regression test.
Building it before waves 2 and 3 costs a little rework when the scripted scenario extends, and saves
the much larger cost of discovering an integration break three specs later.
