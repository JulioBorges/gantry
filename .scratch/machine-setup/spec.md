# Machine setup: the user factory and skill distribution

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 05, wave 1)
Source: `PRD.md` §6.3, §3.2, §7.1, §2.2
Created: 2026-09-11

## Problem Statement

Tools in this category are usually configured per repository, which means an operator who works across
five projects configures the same harness routing five times and keeps five copies in sync. `PRD.md`
rejects that: Gantry is "installed **once per machine** — not reconfigured per repository", with a
central factory at `~/.gantry` and skills at `~/.agents/skills/gantry-*` symlinked into every detected
harness.

That design creates three problems the PRD names but does not solve.

The first is distribution. A skill has to appear inside each harness's own convention — `~/.claude/skills`,
`.opencode`, `~/.codex` — from one source of truth. Symlinks do that cleanly where they work and not at
all where they do not, and the PRD calls out "Windows without dev mode" specifically, requiring a
fallback to copies with the divergence recorded. Copies drift, and a stale copy of a skill is worse than
a missing one because it looks installed.

The second is harness detection. Finding a directory or a binary tells you a harness might be present;
it does not tell you what that integration can do. The PRD is firm that "a parent process name or
environment variable alone does not provide access to native subagent APIs" and that discovery metadata
"must be validated; it cannot grant unavailable APIs". A setup routine that writes capability claims
from detection would fabricate exactly the guarantees ADR-0001 forbids.

The third is that setup is meant to be conversational — "the harness LLM interviews the user and writes
config; no manual JSON editing by default" — which means an agent is producing configuration. That is
fine for routing preferences and wrong for anything requiring operator consent, and the boundary has to
be explicit or the interview becomes an approval channel.

## Solution

`gantry setup` provisions the machine factory: the database, the global configuration, the CLI, MCP, and
dashboard assets, and the skills at `~/.agents/skills/gantry-*`. It detects installed harnesses, links
the skills into each one's convention, and falls back to copies where linking is unavailable, recording
the divergence in local state so drift is detectable rather than invisible.

Detection produces two separate things that are never conflated: a harness is *present*, and an
integration *declares* capabilities. Presence comes from detection; capabilities come from the
integration's own declaration, validated before being written. Setup never infers a capability from a
directory, a binary, or an environment variable, so a configuration produced by setup cannot advertise
monitoring or interruption that the integration does not expose.

The interview is a convenience over the same `ConfigStore` every other transport uses. It writes routing
preferences, context policy, and limits — all validated — and it cannot record an operator approval.
Anything requiring consent stays with the operations that require it, in the repository phase.

Setup is idempotent and re-runnable: a second run detects what exists, reports divergence, and
reconciles only what the operator authorizes.

## User Stories

1. As an operator, I want to install Gantry once per machine, so that I do not repeat routing configuration in every repository.
2. As an operator, I want a single central factory directory, so that I know where my global state lives.
3. As an operator, I want the setup interview conducted conversationally by my harness, so that I do not edit JSON by hand.
4. As an operator, I want to skip the interview and accept sensible defaults, so that I can get running quickly and refine later.
5. As an operator, I want the interview's writes validated like any other configuration write, so that a conversation cannot produce an invalid factory.
6. As an operator, I want the interview unable to record an approval on my behalf, so that consent stays with the operations that need it.
7. As an operator, I want to see exactly what will be created before it is created, so that nothing appears on my disk unannounced.
8. As an operator, I want re-running setup to be safe, so that I can use it to repair or update rather than fearing it.
9. As an operator, I want a second run to report what already exists and what diverges, so that I can see the state of my installation.
10. As an operator, I want divergence reconciled only when I authorize it, so that re-running does not overwrite something I changed deliberately.
11. As an operator, I want my installed harnesses detected, so that I do not list them manually.
12. As an operator, I want skills installed once and linked into each harness's own convention, so that all my harnesses see the same version.
13. As an operator, I want an update to a skill to reach every harness at once, so that they cannot drift apart.
14. As an operator, I want copies used where symlinks are unavailable, so that the tool still works on platforms without them.
15. As an operator, I want copy-based installations recorded as divergent, so that I know which harnesses need re-syncing after an update.
16. As an operator, I want stale copies detected, so that a skill that looks installed but is outdated does not silently misbehave.
17. As an operator, I want to re-sync copies on demand, so that I can repair drift without reinstalling.
18. As an operator, I want a harness whose skill format is unsupported to be told so explicitly, so that I know it has CLI and MCP access only.
19. As an operator, I want that notice printed rather than buried, so that I do not discover the limitation during a run.
20. As an operator, I want harness presence and harness capability treated as separate facts, so that finding a binary does not imply what it can do.
21. As an operator, I want capability claims to come from the integration's own declaration, so that my configuration never advertises something unavailable.
22. As an operator, I want an unvalidated declaration rejected, so that a malformed or overstated claim does not become configuration.
23. As an operator, I want an environment variable or parent process name unable to grant a capability, so that discovery metadata cannot be used as permission.
24. As an operator, I want routing presets available, so that a common arrangement takes one choice rather than nine.
25. As an operator, I want a preset to be a starting point I can adjust, so that choosing one does not lock me in.
26. As an operator, I want to see which preset produced my configuration, so that I can understand and explain my own setup.
27. As an operator, I want no credential value written anywhere by setup, so that my factory contains nothing worth stealing.
28. As an operator, I want credentials referenced by environment variable name only, so that rotating a key does not require reconfiguring Gantry.
29. As an operator, I want the database created ready for use, so that the first real command does not fail on schema initialization.
30. As an operator, I want a database from an older version detected and migrated explicitly, so that an upgrade does not reinterpret my history silently.
31. As an operator, I want an unknown newer database version to refuse to open, so that a downgrade cannot corrupt my records.
32. As an operator, I want setup to work through `npx` without a global install, so that I can try it without changing my machine's global packages.
33. As an operator, I want a global install to behave identically, so that how I installed it does not change what it does.
34. As an operator, I want to see the resolved command for each configured role, so that I can verify routing before anything runs.
35. As an operator, I want setup to avoid running any harness or model, so that installation costs nothing and needs no credential.
36. As an operator, I want to uninstall cleanly, so that removing Gantry leaves no orphaned links inside my harnesses.
37. As a Gantry maintainer, I want the harness compatibility matrix declared as data, so that supporting a new harness is a data change rather than a code change.
38. As a Gantry maintainer, I want skill content versioned with the package, so that an installed skill's version is always identifiable.

## Implementation Decisions

### What setup provisions

Under `~/.gantry`: the SQLite database initialized at the current schema version, the global
`config.json` written through the `ConfigStore`, and the CLI, MCP server, and dashboard assets. Under
`~/.agents/skills/gantry-*`: the skill sources, versioned with the package.

Every path is printed before creation. Setup creates nothing outside those two trees and the harness
skill directories it links into.

Setup runs no harness, no model, and no repository tooling. It needs no credential and no network beyond
package installation itself. This is what makes `npx gantry setup` and a global install behave
identically: neither depends on anything but the package and the filesystem.

Setup is idempotent. A second run inventories what exists, classifies each item as present, missing, or
divergent, and applies only reconciliations the operator authorizes. It never overwrites a configuration
file without authorization, and it always writes a `.bak` when it does.

### Skill distribution and drift

Skills have one source of truth at `~/.agents/skills/gantry-*`. For each detected harness, setup
installs into that harness's convention using the best available mechanism:

```ts
type SkillInstallation = {
  harness: string;
  targetPath: string;
  mechanism: "symlink" | "copy" | "unsupported";
  sourceVersion: string;
  installedVersion?: string;       // for copies; equals sourceVersion when in sync
  divergent: boolean;
};
```

A symlink cannot drift, so `divergent` is always false for it. A copy carries its installed version, and
a mismatch against the source marks it divergent. Setup reports divergence on every run and offers to
re-sync; it does not silently re-copy, because an operator may have modified a copy deliberately.

Divergence records live in local machine state, not in telemetry — the PRD's phrasing is "records the
divergence in telemetry-free local state", and the reason is that this is installation state about the
operator's machine rather than execution evidence about a repository.

A harness whose skill format has no mapping in the compatibility matrix is `unsupported`: no skill is
installed, the operator is told explicitly and prominently that this harness has CLI and MCP access
only, and the notice is part of the setup report rather than a line in a log.

The compatibility matrix is declared data mapping harness identity to skill directory convention and
format. Adding a harness is a data change.

### Harness detection versus capability declaration

Two distinct facts, deliberately never merged:

```ts
type HarnessPresence = {
  harness: string;
  evidence: Array<{ kind: "directory" | "binary" | "manifest"; path: string }>;
  // presence only — says nothing about what the integration can do
};

type IntegrationCapabilities = {
  harness: string;
  declaredBy: "integration_adapter";
  contextMonitoring: "per_tool_call" | "between_turns" | "self_reported" | "none";
  agentInterruption: "supported" | "cooperative_only" | "none";
  nativeSubagents: boolean;
  validatedAt: string;
  validationEvidence: string[];
};
```

Presence comes from detection. Capabilities come only from the integration adapter's declaration in spec
10, validated before being written to configuration. Setup has no code path that derives a capability
from a directory, a binary, a parent process name, or an environment variable — including
`GANTRY_HOST_COMMAND`, which is a discovery input and never a grant.

A declaration that fails validation is rejected and the harness is configured with no capability claims
rather than with optimistic defaults. The resulting configuration therefore cannot advertise a strict
context ceiling for an integration that only checks between turns, which is ADR-0001's requirement
expressed at the moment the configuration is written rather than at the moment a guarantee is claimed.

### The conversational interview

The interview is a skill that collects preferences and writes them through the `ConfigStore`. Its scope:
host and role routing, context policy values, capacity and budget values, Git workflow preferences, and
data handling defaults. Every write is validated as a whole document, so a conversation producing an
invalid combination is rejected with the field path rather than persisted.

Its hard limit: the interview runs as an agent, so its channel can never assert operator actorhood.
`plan.approve`, `merge.confirmLocal`, verification command approval, preparation authorization, cleanup
authorization, and snapshot migration are all unavailable to it, by the channel rule in spec 01. This is
why setup is comfortable being conversational — nothing it can do requires consent.

Skipping the interview yields the approved defaults from spec 02 with no prompting at all.

### Presets

`claude-only`, `opencode-host`, `opencode-host+codex-critic`, `gateway`, and `demo`. A preset is a named
set of configuration values applied as a starting point, recorded by name in the configuration so the
operator can see and explain what produced their setup. Adjusting any value keeps the preset name with a
modified marker rather than pretending the configuration is still pristine.

A preset never carries a capability claim; it carries routing. Capabilities still come from validated
declarations.

### Database initialization and version handling

The database is created at the current schema version. An existing database at an older version requires
an explicit migration, which records the prior version's provenance. A database at a version newer than
the running engine refuses to open, because a downgrade guessing at a newer schema is how history gets
corrupted. Both behaviors follow the execution version compatibility rules in spec 01.

### Uninstall

An explicit operation that removes the skill links or copies from each harness directory, leaving the
factory and database intact unless the operator asks for those too. Removing links is what distinguishes
a clean uninstall from one that leaves broken symlinks inside every harness — the failure mode most
likely to be blamed on the harness rather than on Gantry.

## Testing Decisions

**What makes a good test here.** Tests run setup against a temporary home directory containing fixture
harness installations and assert on the resulting filesystem state, the setup report, and the
configuration read back through the core. Filesystem assertions are limited to what is contractual: which
paths exist, whether a path is a link or a copy, and the recorded installation state. Tests never assert
on file formatting or on the text of printed output beyond the presence of the unsupported-harness
notice.

**The seam.** The same seam as spec 01 for everything that touches configuration or the database, with a
temporary `HOME` for filesystem effects. Setup's filesystem work is inherently side-effectful, so it is
tested by observing the tree rather than by mocking a filesystem layer — a mock would prove the mock.

Symlink-unavailable behavior is tested by a fixture that makes linking fail, not by skipping the test on
platforms where linking works. Windows remains unvalidated per §14.1, and this spec's tests are where
that validation will land.

**Modules under test.** Factory provisioning and path reporting, idempotent re-run and divergence
classification, skill installation mechanism selection, drift detection and re-sync, the compatibility
matrix and unsupported-harness handling, harness presence detection, capability declaration validation
and rejection, the interview's write path and its channel restriction, preset application and recording,
database initialization and version handling, and uninstall.

**Scenarios that must exist:**

- A first run creates exactly the announced paths and nothing outside them.
- Setup completes with no credential, no network beyond installation, and no harness or model invocation, verified by fakes that fail the test if invoked.
- A second run reports present, missing, and divergent items and changes nothing without authorization.
- An authorized reconciliation writes a `.bak` before overwriting configuration.
- A detected harness supporting symlinks gets a link, and the installation is never divergent.
- A fixture where linking fails gets a copy, recorded as a copy with its installed version.
- A copy whose source version advances is reported divergent and is re-synced only on request.
- A harness absent from the compatibility matrix installs no skill and produces an explicit CLI-and-MCP-only notice in the report.
- Detection records presence evidence and writes no capability claim.
- A capability declaration is written only after validation; a malformed or overstated one is rejected and leaves the harness with no capability claims.
- A configuration produced by setup never advertises per-tool-call monitoring or interruption for an integration declaring `between_turns` or `cooperative_only`.
- `GANTRY_HOST_COMMAND` and a parent process name do not grant any capability.
- The interview's writes are validated as a whole document, and an invalid combination is rejected with the field path.
- The interview's channel cannot perform plan approval, command approval, preparation authorization, cleanup authorization, merge confirmation, or snapshot migration.
- Skipping the interview yields the approved defaults.
- Each preset produces a valid configuration, is recorded by name, and is marked modified after any adjustment.
- No preset writes a capability claim.
- No credential value appears in any file setup writes.
- A fresh database opens at the current schema version; an older one requires explicit migration recording prior provenance; a newer one refuses to open.
- `npx` and global installation produce identical factory state.
- Uninstall removes every link and copy from harness directories and leaves none broken.

## Out of Scope

- **Configuration schema and validation rules** (spec 02): this spec writes configuration; spec 02 defines its shape, constraints, and defaults.
- **Operations, channels, database schema and migrations** (spec 01): the channel rule this spec relies on, and the schema it initializes.
- **Repository-level onboarding** (spec 06): `gantry init`, artifact mapping, verification command approval, preparation authorization, dirty working tree. Setup is machine scope only.
- **Demo mode** (spec 07): `init --demo` and the fixture pipeline. The `demo` preset here is routing configuration; the demo experience is spec 07's, and it deliberately does not require setup to have run.
- **Integration capability declaration content and validation rules** (spec 10): this spec consumes validated declarations and refuses unvalidated ones; spec 10 defines what a declaration asserts and how it is proven.
- **Skill content** (specs 08, 09, 11, 13, 14): what each `gantry-*` skill instructs. This spec distributes them and versions them; their behavior belongs to the specs that define the workflows.
- **MCP server and dashboard behavior** (specs 16, 17): setup installs their assets; their operation is theirs.
- **Packaging and release** (spec 19): how the package is built and published.

Out of scope by product decision:

- Per-repository harness configuration. The machine factory is configured once (§2.2).
- Setup executing repository tooling or agents. Installation needs no credential, and running anything would break that.
- Inferring capabilities from the environment. ADR-0001 and §6.1 forbid it, and this spec has no code path for it.
- Windows support claimed rather than tested. It remains expected and pending validation (§14.1); this spec's symlink-fallback tests are where the evidence will come from.

## Further Notes

**Binding decisions.** ADR-0001 is the load-bearing constraint in this spec. The separation of
`HarnessPresence` from `IntegrationCapabilities` into two types with no derivation between them is the
structural form of its rule, placed here because setup is the earliest point where an unearned capability
claim could enter the system and then be trusted by everything downstream.

**Glossary alignment.** Integration Capability and Context Watermark follow `CONTEXT.md`. The glossary's
warning against "universal context ceiling" is exactly what the capability validation prevents setup from
writing.

**Glossary gap for `/domain-modeling`.** Harness presence, skill installation mechanism, and installation
divergence are introduced here without entries and should get them.

**Where the risk actually sits.** Skill distribution by symlink is the fragile part, and not because of
Windows. Harnesses own their skill directories and may rewrite, reorganize, or validate them, so a
symlink that works today can be replaced or ignored after a harness update. The design mitigates this by
making drift detectable and re-sync explicit rather than by assuming links persist, and by keeping the
compatibility matrix as data so a changed convention is a data fix. The residual risk is a harness that
actively rejects symlinked skills, which would push it to the copy mechanism and make drift reporting the
thing operators actually rely on.

**Sequencing note.** This spec depends on spec 02 and spec 01 and is depended on by nothing except
convenience — spec 07's demo deliberately bypasses it. That makes it safe to build late despite its
position in wave 1. The one piece worth landing early is the compatibility matrix as data, because
specs 08, 09, 11, 13, and 14 each ship a skill and need to know where it goes.
