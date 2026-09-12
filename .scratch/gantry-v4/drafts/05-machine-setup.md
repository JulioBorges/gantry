## Spec 05 — machine-setup

This spec owns everything that exists *once per machine*: the `~/.gantry` factory (database at the current schema version, global configuration written through the ConfigStore, CLI/MCP/dashboard assets), the skill sources at `~/.agents/skills/gantry-*` and their installation into each detected harness's own convention, the harness compatibility matrix as data, harness presence detection, routing presets, the conversational setup interview, and uninstall. Its risk sits in two places that pull in opposite directions. The first is ADR-0001 at its earliest enforcement point: setup is where an unearned Integration Capability claim could enter configuration and then be trusted by every downstream spec, so `HarnessPresence` and `IntegrationCapabilities` must stay two types with no derivation path between them. The second is skill distribution, where the fragility is not Windows but harness ownership — a harness may reorganize, revalidate, or reject its skill directory after an update, so the design bets on drift being *detectable* and re-sync being *explicit* rather than on links persisting. Everything else here is provisioning mechanics that a temporary `HOME` can prove.

### Slices

---

**01 — Machine factory provisioning**

- **What to build**: `gantry setup` against a fresh temporary `HOME` creates the `~/.gantry` factory end-to-end: the SQLite database opened at the current schema version, the global configuration document written through the ConfigStore with the approved defaults, and the CLI, MCP, and dashboard assets placed. Every path is announced before creation, and setup creates nothing outside `~/.gantry` and `~/.agents/skills/gantry-*`. The same code path handles an existing database: an older schema version refuses to proceed without an explicit migration that records the prior version's provenance, and a newer version refuses to open at all. Setup runs no harness, no model, and no repository tooling, needs no credential, and behaves identically whether entered through `npx` or a global install.
- **Acceptance criteria**:
  - A first run creates exactly the announced paths and nothing outside the two declared trees, asserted by walking the temporary `HOME`.
  - Injected harness drivers, model clients, and network access are fakes that fail the test if invoked; the run completes without touching any of them.
  - A fixture database one schema version behind refuses to proceed and reports that an explicit migration is required; after migration the prior version is recorded as provenance.
  - A fixture database one schema version ahead refuses to open, with a distinct rejection from the older-version case.
  - No file written by setup contains a credential value; credentials appear only as environment variable names.
  - Factory state produced through the `npx` entry point and through the global entry point compares equal.
- **Blocked by**: needs the operation core `invoke` seam and operation catalog registration from `execution-core`; needs the execution version compatibility rules (older requires explicit migration, newer refuses) from `execution-core`; needs the ConfigStore layering and approved defaults from `config-and-snapshot`; needs the redaction sink enforcement interface from `data-handling` for the setup report's display path.
- **Parallelizable with**: 02, and 06 once the config write path lands.

---

**02 — Harness compatibility matrix and presence detection**

- **What to build**: Declare the compatibility matrix as validated data mapping a harness identity to its skill directory convention, skill format, and the evidence kinds that establish presence. Build detection over a temporary `HOME` containing fixture harness installations, producing a `HarnessPresence` record per harness with its evidence (`directory` | `binary` | `manifest`) and path. Classify each detected harness against the matrix as supported or unsupported. Surface the whole inventory through a core operation and a CLI report. Detection writes no Integration Capability claim of any kind — that is the load-bearing property of this slice, not a side note.

  ```ts
  type HarnessPresence = {
    harness: string;
    evidence: Array<{ kind: "directory" | "binary" | "manifest"; path: string }>;
  };
  ```
- **Acceptance criteria**:
  - The matrix is data with its own schema validation; adding a fixture harness entry requires no change outside the data file, proven by a test that adds one and sees it detected and classified.
  - A fixture `HOME` with three harness installations produces one presence record each, carrying the evidence kind and path that established it.
  - A harness present on disk but absent from the matrix is classified unsupported and appears as such in the report.
  - The detection result contains no capability field, and a test asserts the configuration written after detection alone holds no capability claims.
  - `GANTRY_HOST_COMMAND` and a spoofed parent process name change the detection output in no way.
- **Blocked by**: None.
- **Parallelizable with**: 01, 06.

---

**03 — Skill installation into harness conventions**

- **What to build**: Establish the skill sources at `~/.agents/skills/gantry-*` as the single source of truth, versioned with the package so an installed skill's version is always identifiable. For each detected, supported harness, select the installation mechanism and install: a symlink where linking works, a copy where it does not, and nothing where the matrix has no format mapping. Persist a `SkillInstallation` record per harness in telemetry-free local machine state. The setup report carries an explicit, prominent notice for each unsupported harness stating it has CLI and MCP access only.

  ```ts
  type SkillInstallation = {
    harness: string;
    targetPath: string;
    mechanism: "symlink" | "copy" | "unsupported";
    sourceVersion: string;
    installedVersion?: string;   // copies only; equals sourceVersion when in sync
    divergent: boolean;
  };
  ```
- **Acceptance criteria**:
  - A supported harness on a linking-capable fixture receives a symlink, recorded with `mechanism: "symlink"` and `divergent: false`.
  - A fixture that makes linking fail receives a copy, recorded with `mechanism: "copy"` and an `installedVersion` equal to the source version — the test forces link failure rather than skipping on platforms where linking works.
  - A harness with no matrix format mapping has no skill written into its directory and produces the CLI-and-MCP-only notice in the setup report.
  - Every installed skill's version is readable from the installation record and matches the package version.
  - Installation records are written to local machine state and appear in no telemetry or execution record.
- **Blocked by**: 01 (factory and local machine state), 02 (matrix and presence detection).
- **Parallelizable with**: 05, 06, 07.

---

**04 — Installation lifecycle: idempotent re-run, divergence reconciliation, and uninstall**

- **What to build**: A second `gantry setup` run inventories everything the first one produced — factory items and skill installations alike — and classifies each as present, missing, or divergent. A copy whose source version has advanced is divergent; a symlink never is. The run changes nothing without operator authorization, and any authorized overwrite of a configuration file writes a `.bak` first. Re-sync of a divergent copy happens only on request, never silently, because an operator may have modified a copy deliberately. Uninstall is the inverse operation: it removes every link and copy from every harness directory, leaving none broken, and leaves the factory and database intact unless the operator explicitly asks for those too.
- **Acceptance criteria**:
  - A second run over an intact installation reports every item present and writes nothing, asserted by comparing the tree before and after.
  - A run against an installation with a deleted asset and a stale copy reports one missing and one divergent item and still changes nothing without authorization.
  - An authorized reconciliation of a configuration file writes a `.bak` containing the prior content before overwriting.
  - A copy whose source version advances is reported divergent on every subsequent run until re-sync is requested; after re-sync its installed version matches the source.
  - A symlinked installation is never reported divergent, including after the source version advances.
  - Uninstall leaves no link or copy in any harness directory and no broken symlink, verified by resolving every path under the fixture harness directories; the factory and database survive unless explicitly included.
- **Blocked by**: 01, 03.
- **Parallelizable with**: 05, 06, 07.

---

**05 — Integration Capability declaration validation**

- **What to build**: Accept `IntegrationCapabilities` into configuration only from an integration adapter's own declaration, validated before it is written. A declaration that is malformed, or that claims more than its validation evidence supports, is rejected and leaves that harness configured with no capability claims — never with optimistic defaults. There is no code path from presence evidence, a directory, a binary, a parent process name, or an environment variable to a capability value. The resulting configuration cannot advertise a Context Watermark ceiling or agent interruption for an integration whose declaration says otherwise; the setup report shows each harness's capability state, including "none declared".
- **Acceptance criteria**:
  - A valid declaration from a fake adapter is written to configuration with its `validatedAt` timestamp and validation evidence.
  - A malformed declaration is rejected with the offending field path, and the harness ends with zero capability claims in the written configuration.
  - A declaration claiming `contextMonitoring: "per_tool_call"` without supporting validation evidence is rejected, and the configuration does not advertise per-tool-call monitoring for that harness.
  - A harness declaring `between_turns` monitoring and `cooperative_only` interruption produces a configuration that advertises exactly those and no stronger variant.
  - Presence detection output, `GANTRY_HOST_COMMAND`, and parent process name are all exercised as inputs and grant no capability in any combination.
- **Blocked by**: 01 (configuration write path), 02 (presence records, so the no-derivation assertion has both facts available); needs the Integration Capability declaration shape and its validation evidence contract from `harness-adapters` — the adapter itself is injected as a fake, so only the declared shape is required, not a working adapter.
- **Parallelizable with**: 03, 04, 06, 07.

---

**06 — Routing presets**

- **What to build**: Ship `claude-only`, `opencode-host`, `opencode-host+codex-critic`, `gateway`, and `demo` as named sets of configuration values applied as a starting point. Applying a preset records its name in the configuration; adjusting any value afterwards keeps the name with a modified marker rather than presenting the configuration as pristine. A preset carries routing only — never a capability claim and never a credential value. After application, the report prints the resolved command for each configured role so the operator can verify routing before anything runs.
- **Acceptance criteria**:
  - Each of the five presets produces a configuration that passes whole-document validation.
  - The applied preset's name is readable from the configuration through the core.
  - Adjusting any value after applying a preset sets the modified marker while retaining the preset name.
  - No preset writes any Integration Capability field, asserted per preset.
  - No preset writes a credential value; credentials appear only as environment variable names.
  - The report lists a resolved command for every configured role.
- **Blocked by**: 01; needs the routing, context policy, and capacity/budget field vocabulary from `config-and-snapshot`.
- **Parallelizable with**: 02, 03, 04, 05.

---

**07 — The conversational setup interview**

- **What to build**: Package the interview as a `gantry-*` skill that collects host and role routing, context policy values, capacity and budget values, Git workflow preferences, and data handling defaults, then writes them through the ConfigStore as a whole validated document — so a conversation producing an invalid combination is rejected with the field path rather than persisted. The interview runs as an agent, so its channel can never assert operator actorhood: plan approval, local merge confirmation, Verification Command Approval, Preparation Authorization, Cleanup Authorization, and snapshot migration are all unavailable to it and return the operator-channel rejection. Skipping the interview yields the approved defaults with no prompting.
- **Acceptance criteria**:
  - An interview transcript producing a valid combination results in a configuration readable back through the core with those values.
  - An invalid combination is rejected as a whole document with the offending field path, and nothing is persisted.
  - Each of the six operator-only operations invoked through the interview's channel returns `operator_channel_required`, enumerated one test per operation.
  - Skipping the interview produces exactly the approved defaults, compared against the defaults read directly from the ConfigStore.
  - The interview writes no credential value and no Integration Capability claim.
- **Blocked by**: 01, 06 (the interview offers presets); needs the actor channel rule and the `operator_channel_required` rejection code from `execution-core`.
- **Parallelizable with**: 02, 03, 04, 05.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| ConfigStore layering, whole-document validation, approved defaults | `config-and-snapshot` | 01, 05, 06, 07 |
| Configuration field vocabulary for routing, context policy, capacity and budget limits | `config-and-snapshot` | 06, 07 |
| Shared operation core `invoke` seam and operation catalog registration | `execution-core` | 01 (and every slice's tests) |
| Database schema initialization and execution version compatibility rules | `execution-core` | 01 |
| Actor channel rule and the `operator_channel_required` rejection code | `execution-core` | 07 |
| Redaction sink enforcement interface | `data-handling` | 01, 04 (setup report display path) |
| Integration Capability declaration shape and validation evidence | `harness-adapters` | 05 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Harness compatibility matrix as data** (harness identity → skill directory convention, skill format, presence evidence rules) | 02 | `spec-validation`, `slicing-and-approval`, `pbi-execution-loop`, `entropy-gate`, `git-integration` — each ships a skill and needs to know where it goes; `harness-adapters` for the harness identity vocabulary |
| Skill source layout and package-versioned skill identity at `~/.agents/skills/gantry-*` | 03 | `spec-validation`, `slicing-and-approval`, `pbi-execution-loop`, `entropy-gate`, `git-integration` |
| Harness presence versus Integration Capability separation (setup writes no capability claim; declaration is the only source) | 02 defines presence, 05 defines the validated write | `harness-adapters` (it owns the declaration; this is the consuming boundary it must satisfy) |
| `~/.gantry` factory layout and global configuration location | 01 | `config-and-snapshot` (global source level resolves here), `mcp-server` and `dashboard` (their assets install here) |

### Risks / judgement calls

**Database version gating sits inside slice 01 rather than standing alone.** I was tempted to split it, and it would make a clean small slice. I folded it in because open-or-create is one code path and because a factory that provisions without a version gate is a factory you have to revisit before anything else can safely use it. The cost is that slice 01 is the largest here. If an agent's context budget is tight, the older/newer version gating is the cleanest thing to peel off into its own follow-up.

**Uninstall is folded into slice 04 rather than standing alone.** Uninstall and re-sync share the same inventory-and-classify machinery, and the operator instruction favours fewer meatier slices. The argument against: uninstall's failure mode — broken symlinks left inside directories Gantry does not own, which operators will blame on the harness — is distinct enough to deserve its own attention. Splitting it out gives 8 slices and both halves still parallelize off slice 03. Worth a look.

**The matrix and presence detection are one slice, not two.** Detection without the matrix produces a list nothing can classify, and the matrix without detection has no consumer to prove it. They are separable on paper and I do not think that separation earns its coordination cost.

**Slice 02 should probably be pulled forward ahead of the rest of this spec.** The spec's own sequencing note says the compatibility matrix is the one piece worth landing early, and five other specs read it. It has no blockers at all, so it can start before spec 01's core seam exists if the matrix is delivered as validated data plus a detection function, with its operation-core surfacing deferred. That is a departure from this spec's late position in the map and worth an explicit decision.

**Slice 05 leans on a contract `harness-adapters` owns.** This spec states the `IntegrationCapabilities` shape concretely, but spec 10 owns what a declaration asserts and how it is proven. I declared the dependency on the shape only, since the adapter is injected as a fake either way. If spec 10's declaration ends up carrying conformance probe results in a different structure, slice 05's validation rules change — the rejection behavior does not, which is the part ADR-0001 cares about.

**Slice 07 is not blocked on slice 03.** The interview's substance is the config write path and the channel restriction, both testable through the core with no skill installed anywhere. Its skill source does land in slice 03's `~/.agents/skills/gantry-*` layout, so if you want the packaging proven in the same PBI, add 03 as a blocker and accept the chain 01 → 02 → 03 → 07.

**One question for `execution-core`, not resolvable here.** Setup operations are registered in the shared operation catalog, but `gantry setup` runs before the factory and database exist — so the catalog and its seam have to be constructible against a not-yet-provisioned factory. That is a bootstrap ordering constraint on spec 01's design, and slice 01 of this spec is where it will first bite.

**Windows remains unvalidated, deliberately.** Slice 03 forces link failure with a fixture rather than skipping on linking-capable platforms, which is the evidence path §14.1 and spec 19 expect. No slice here claims Windows support, and none should be written to imply it.
