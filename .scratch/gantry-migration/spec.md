# Spec: Gantry skill pack — migrating `asdlc` into `gantry`

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 01)
Source: `PRD.md` §4–§14, `CONTEXT.md`, `docs/adr/0003`, `docs/adr/0004`
Created: 2026-09-12

## Blueprint

### Context

Gantry is a harness-neutral skill pack that runs an agentic software development life cycle: deterministic scripts decide which work is ready and whether a delivery is done, agents plan, build, review and refute, and the operator decides in the harness conversation (`PRD.md` §2). Today the only implementation of that loop is the `asdlc` skill at `.agents/skills/asdlc/`: one `SKILL.md`, two workflow templates and five standard-library Python scripts (`frontier.py`, `acceptance.py`, `gates.py`, `roadmap.py`, `common.py`). It works, and it is hardcoded to this repository — it names `.scratch/gantry-v4/slice-index.md`, "the Gantry repository" and `docs/agents/issue-tracker.md` inside its prompts — it validates nothing about a spec before slicing, its gates are pass/fail only, its result schemas live inline in Claude Code Workflow scripts, nothing records what a run did, and nothing can show two runs side by side.

This spec is the migration: `asdlc` becomes the three skills of the pack (`gantry`, `gantry-setup`, `gantry-dashboard`), the repository-specific knowledge moves into a sparse repository policy, and the pieces the PRD adds — spec readiness, context budget, differential gates, result contracts, run log, guard hooks, dashboard, Learner, draft run pull request, capability files and a fixture — land one vertical slice at a time. The migration is executed by `asdlc` itself, so every slice has to leave the loop runnable on this repository.

### Architecture

- **Skills:** `.agents/skills/gantry/SKILL.md` (the workflow, evolved from `.agents/skills/asdlc/SKILL.md`), `.agents/skills/gantry-setup/SKILL.md` (conversational setup, the only writer of the repository policy) and `.agents/skills/gantry-dashboard/SKILL.md` (opens the kanban). The two thin skills invoke scripts under `../gantry/scripts/`. `.agents/skills/asdlc/` is removed in the last slice; the harness directories `.claude/skills`, `.cursor/skills`, `.opencode/skills` and `.gemini/skills` keep resolving to `.agents/skills`.
- **Workflow templates:** `.agents/skills/gantry/reference/plan-workflow.md` and `.agents/skills/gantry/reference/round-workflow.md`, each carrying harness-neutral prompt functions and the Claude Code `Workflow` script. The plan workflow gains a Requirement Critic phase before slicing and a `budget.py` step before the plan critic; the round workflow gains an optional Learner phase after the last round and writes run-log events at every phase boundary. All prompts read repository-specific inputs from the resolved policy passed in `args`, never from literals.
- **Scripts** (`.agents/skills/gantry/scripts/`, Python 3.10+, standard library only): `common.py` (parsing plus policy resolution), `frontier.py`, `acceptance.py`, `gates.py` (adds the differential mode), `roadmap.py` (unchanged contract), `spec.py` (structural validation derived from the effective template), `budget.py` (initial-package estimate), `result.py` (result-contract validation), `runlog.py` (append and query run events), `guard.py` (hook handler), `cleanup.py` (plan and execute worktree/branch removal), `dashboard.py` (loopback HTTP server and static kanban).
- **Result contracts:** `.agents/skills/gantry/schemas/{planner,plan-critic,implementer,reviewer,critic,learner}.json`, JSON Schema documents using the subset `result.py` implements: `type`, `properties`, `required`, `items`, `enum`, `additionalProperties`. The Claude Code templates load these files into `schema:`; every other harness validates with `result.py --role <role>`.
- **Templates:** `.agents/skills/gantry/templates/spec.md` (this document's skeleton: Blueprint, Contract, Out of Scope, Changelog), `.agents/skills/gantry/templates/prd.md`, `.agents/skills/gantry/templates/issue.md` (the current issue format: `Type`, `Status`, `Slice`, `Spec`, `Created` header lines, `## Parent`, `## What to build`, `## Acceptance criteria`, `## Blocked by`, `## Comments`). `spec.py` derives its required sections from the effective spec template, so a repository that customises `.gantry/templates/spec.md` changes the check.
- **Repository policy:** `.gantry/config.json`, tracked, sparse, written only by `gantry-setup`. Keys: `artifacts` (`specs`, `issues`, `adrs`, `decisions` path patterns), `templates` (`dir`, `headingMap` of equivalent headings), `checks` (list of `{name, command, mode: "absolute" | "differential", mapping: {findings, rule, file, line, message, severity}, secrets: boolean}`), `git` (`target`, `prefix`), `hooks` (`record`, `deny` lists), `budget` (`corrections`, `contextShare`) and `dashboard` (`staleAfterSeconds`, a positive integer). A differential `mapping` uses RFC 6901 JSON Pointers: `findings` resolves from the command's JSON root to an array, and every other field resolves from each array item to one scalar. `file` must resolve to a normalized path relative to the repository root. Any duplicate `(rule, file, message)` identity after normalization, in either the base or delivery output, fails the check with `verdict: fail`, exit 1 and an `invalid` entry naming the source and identity. `staleAfterSeconds` defaults to `900` when absent; a policy value takes precedence over that default. `common.py` resolves the effective policy as pack defaults overlaid by the file.
- **Run log:** `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl`, where `unit-id` is the first twelve hex characters of the SHA-256 of the real path of `git rev-parse --git-common-dir`, so every worktree of one clone shares it. One JSON object per line: `ts`, `run`, `event`, optional `issue`, `phase`, `data`. A `run.started` event records the repository root, policy hash, tier and effective `staleAfterSeconds` in `data`; dashboard staleness uses that snapshot for the Run. A `policy.changed` event never changes an existing Run's snapshot, and the new policy takes effect when a later Run starts. Events: `run.started`, `run.resumed`, `run.cancelled`, `run.finished`, `round.started`, `round.finished`, `phase.started`, `phase.finished`, `subagent.started`, `subagent.stopped`, `compaction`, `hook.denied`, `policy.changed`, `issue.done`, `issue.blocked`, `refutation`, `review.finding`. The log stores references and the role results' JSON, never diffs or command output.
- **Capabilities:** `.agents/skills/gantry/capabilities/{claude-code,opencode,codex}.json` with `tier`, `hooks`, `structured_output`, `worktree_isolation`, `per_role_model`, `parallel_round`, `skills_path`, `hook_events` and `payload_fields`. `guard.py` and the setup skill read them; the run report prints the tier.
- **Hook wiring:** `.agents/skills/gantry/hooks/claude-code.settings.json` (a `hooks` fragment merged into `.claude/settings.json`), `.agents/skills/gantry/hooks/opencode.plugin.js` (a plugin forwarding `tool.execute.before` and `session.compacted` to `guard.py`), `.agents/skills/gantry/hooks/codex.hooks.json`. Every entry executes `python3 <skillDir>/scripts/guard.py <event>` with the payload on stdin.
- **Fixture:** `fixture/`, a small Python project with `fixture/pyproject.toml`, `fixture/tests/`, a standard-library linter `fixture/tools/lint.py` emitting JSON findings, `fixture/.gantry/config.json` declaring one absolute check (`pytest`) and one differential check (the linter), `fixture/.scratch/greeting/spec.md` and three issues under `fixture/.scratch/greeting/issues/`. It is the repository every acceptance scenario below runs against, and the run that proves a support tier is recorded in `fixture/README.md`.
- **Dependencies:** `python3` 3.10 or newer and `git` are required; `gh` is used only when the operator accepts the draft run pull request; the `tdd` and `code-review` skills are invoked when installed and the prompts carry the fallback when they are not. Nothing in the pack imports a third-party package.

### Constraints

- Every module under `.agents/skills/gantry/scripts/` imports only the Python standard library, and a test enumerates the imports to prove it.
- Every script prints usage on `--help`, emits machine-readable output on `--json` where it produces data, and exits 0 on success, 1 on a failed check and 2 when there is nothing to check.
- `spec.py --check` and `result.py` complete in under one second on a 200 KB document.
- `guard.py` answers a 1 MB hook payload in under 200 ms, because hooks fire on every tool call.
- `runlog.py append` writes one complete line per call with a single write system call for lines up to 64 KB, and two processes appending concurrently produce a file where every line parses as JSON.
- `dashboard.py` binds `127.0.0.1` only, serves the kanban from files in the pack with zero external assets, and reflects a new run-log event within two seconds.
- `budget.py` estimates tokens as UTF-8 bytes divided by four, reads the assumed window from the capabilities file for the chosen model, and applies the `contextShare` from the policy, 0.15 by default.
- The differential mode of `gates.py` runs the same declared command on the round's base and on the delivery, in separate worktrees of the same clone, and matches findings by the tuple (rule, file, message). Every differential mapping resolves its RFC 6901 pointers to one findings array and scalar fields for every finding; file paths are normalized repository-relative paths, and duplicate identities in either output result in `verdict: fail`, exit 1 and an `invalid` entry naming the source and identity. Every differential mapping resolves `severity` to exactly one of `info`, `warning` or `error`; their ordering is `info < warning < error`. A matching delivery finding with a higher severity is `aggravated`; a missing or invalid severity is a failed gate configuration. An identity present only on the base is reported as `resolved`.
- A hook denial names its rule and the path it refused in one line, and the same denial is written to the run log as `hook.denied`.
- Every artifact the pack writes — issues, comments, reports, lesson candidates, pull request bodies — is English.

## Contract

### Definition of Done

- [ ] `.agents/skills/gantry/`, `.agents/skills/gantry-setup/` and `.agents/skills/gantry-dashboard/` each contain a `SKILL.md` with the frontmatter the three harnesses accept; `.agents/skills/asdlc/` is gone; `ls .claude/skills .cursor/skills .opencode/skills .gemini/skills` lists the three skills.
- [ ] `grep -r "gantry-v4\|slice-index\|the Gantry repository" .agents/skills/gantry*` returns nothing; repository-specific inputs come from `.gantry/config.json` or pack defaults, and the workflow runs on this repository with no policy file present.
- [ ] `spec.py --check` fails a spec missing `## Contract`, names the missing section, and passes a spec whose `## Delivery contract` heading is mapped to `## Contract` in `templates.headingMap`.
- [ ] The plan workflow runs the Requirement Critic before slicing; on the fixture spec with an injected ambiguous Definition of Done item, the run stops before any issue file is written and the report quotes the blocking finding.
- [ ] `budget.py <issue> --model <id>` prints the estimated tokens, the assumed window and the share; an issue listing files whose size exceeds the share is reported over budget and the plan critic's result quotes the number.
- [ ] `result.py --role critic < result.json` exits 1 and prints `criteria` as the missing field when the result lacks it, and exits 0 on a valid result; the round workflow re-asks once on failure and then records `critic_failed`.
- [ ] On the fixture, `gates.py --run --diff-base <base> --json` resolves the configured RFC 6901 mappings and reports `verdict: fail` with the new finding when a delivery adds a linter finding, `verdict: fail` with the finding under `aggravated` when the matching finding changes from `warning` to `error`, `resolved` for a finding present only on the base, and `verdict: pass` with the finding listed under `preexisting` when the delivery only carries a finding already present on the base at the same or lower severity. A duplicate normalized identity in either command output yields `verdict: fail`, exit 1 and an `invalid` entry naming the base or delivery source.
- [ ] A run on the fixture leaves `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl` whose first event is `run.started` with the repository root, policy hash, tier and effective `staleAfterSeconds`, and whose last is `run.finished`; `runlog.py inflight <unit-id>` lists the issue, phase and worktree of an interrupted run.
- [ ] `guard.py PreToolUse` with a Claude Code payload editing `ROADMAP.md` or an issue's `Status:` line answers deny and logs `hook.denied`; the same payload for a `Read` answers allow; a `SubagentStop` payload appends `subagent.stopped`.
- [ ] `gantry-setup` merges `hooks/claude-code.settings.json` into `.claude/settings.json` idempotently: running it twice produces the same file, and keys it did not write are preserved byte for byte.
- [ ] `dashboard.py` shows two runs from two different `unit-id`s with their issues in the right phase columns, and applies the `staleAfterSeconds` snapshot from each `run.started` event: a run is stale only when its last event is older than that value. The effective value is the positive integer in policy or the `900`-second default, and a later `policy.changed` does not affect an existing run.
- [ ] The Learner reads a run log containing the same refutation on two issues and one refutation on a single issue, and produces exactly one lesson candidate, with its evidence and proposed target; nothing under `AGENTS.md` changes.
- [ ] At the end of a run the orchestrator offers the draft run pull request; with a stub `gh` on `PATH` the body contains each issue's criteria and evidence, and with no `gh` the report names the branch instead.
- [ ] `gantry-setup` shows the full proposed `.gantry/config.json` and writes it only after confirmation; on a repository that already has one it offers merge, overwrite or abort; the `AGENTS.md` section is added between `<!-- gantry:begin -->` and `<!-- gantry:end -->` with the rest of the file byte-identical.
- [ ] `cleanup.py --plan` lists only worktrees and branches of issues with `Status: done` whose branch is merged into the run branch, and `cleanup.py --yes` removes exactly the listed items.
- [ ] `capabilities/claude-code.json`, `capabilities/opencode.json` and `capabilities/codex.json` exist with every field named in the Architecture, and the run report states the tier read from them.
- [ ] `fixture/` runs the whole loop in Claude Code from `gantry greeting` to an offered draft pull request, and `fixture/README.md` records the run log path and the tier.
- [ ] Spec updated in the same merge as any behaviour change.

### Regression Guardrails

- `roadmap.py done` stays the only writer of an issue's `Status:` line and checkboxes, and `roadmap.py check` reports any drift between the roadmap and the issues.
- `frontier.py` refuses a blocker graph with a cycle or a dangling reference and lists parked issues instead of scheduling them.
- The Critic's acceptance remains the only path to `done`; a refuted issue ends `blocked` with its evidence and its worktree kept.
- The correction budget stays a ceiling — two by default — and is never raised by a script or a prompt.
- The run log is never read to decide whether an issue is done.
- The issue file format parsed by `common.py` is unchanged, so issues written before the migration keep working.
- A run keeps working in a harness with no hooks: every hook-enforced rule is also stated in the prompts and verified by the Critic.

### Scenarios

```gherkin
Scenario: Structural validation follows the effective template
  Given the fixture repository maps "## Delivery contract" to "## Contract" in .gantry/config.json
  And a spec that uses "## Delivery contract" and omits "## Changelog"
  When spec.py --check runs on that spec
  Then it exits 1 and names "## Changelog" as the missing section
  And it reports "## Contract" as present through the mapping

Scenario: A blocking requirement finding stops the run before slicing
  Given the fixture spec whose Definition of Done contains "the greeting should be fast"
  When the operator runs gantry greeting
  Then the Requirement Critic reports a blocking finding quoting that item
  And no file exists under fixture/.scratch/greeting/issues/
  And the run report tells the operator to amend the spec

Scenario: A differential check blocks a new finding and tolerates an old one
  Given the fixture base already carries one linter finding in greeting.py
  And a delivery that adds a second finding in cli.py
  When gates.py --run --diff-base <base> --json runs on the delivery
  Then the verdict is fail
  And the new finding in cli.py is listed under new
  And the finding in greeting.py is listed under preexisting

Scenario: A differential check blocks an aggravated finding
  Given the fixture base carries a linter finding with identity (rule, file, message) and severity warning
  And a delivery carries the same finding with severity error
  When gates.py --run --diff-base <base> --json runs on the delivery
  Then the verdict is fail
  And the finding is listed under aggravated

Scenario: A differential check reports a resolved finding
  Given the fixture base carries a linter finding with identity (rule, file, message)
  And the delivery carries no finding with that identity
  When gates.py --run --diff-base <base> --json runs on the delivery
  Then the verdict is pass
  And the base finding is listed under resolved

Scenario: A differential check rejects duplicate finding identities
  Given either the fixture base or delivery output contains two findings with the same normalized (rule, file, message) identity
  When gates.py --run --diff-base <base> --json runs on the delivery
  Then the verdict is fail with exit 1
  And invalid names the output source and duplicate identity

Scenario: A guard hook refuses a roadmap edit and records it
  Given Claude Code with the pack's hooks fragment merged into .claude/settings.json
  When an implementer subagent issues an Edit on ROADMAP.md
  Then the hook answers deny naming the rule and the path
  And the run log gains a hook.denied event for that issue and phase

Scenario: The dashboard shows two runs and a stale one
  Given a run log for repository A with an issue in the Critic phase and a staleAfterSeconds snapshot of 60
  And a run log for repository B with a staleAfterSeconds snapshot of 900
  And both runs have last events 120 seconds old
  When the operator opens the dashboard
  Then repository A's issue appears in the Critic column of its stale swimlane
  And repository B's run is not stale

Scenario: A rerun offers to continue an interrupted issue
  Given a run on the fixture interrupted while greeting#02 was in the Implement phase in worktree W
  When the operator runs gantry greeting again
  Then the orchestrator offers to continue greeting#02 in W
  And greeting#02 keeps Status: ready-for-agent until the Critic accepts it

Scenario: The Learner keeps only recurring lessons
  Given a run log where the refutation "criterion 3 has no test" appears on greeting#01 and greeting#03
  And the refutation "cli.py prints to stderr" appears only on greeting#02
  When the Learner phase runs
  Then exactly one lesson candidate is produced, citing greeting#01 and greeting#03
  And AGENTS.md is unchanged

Scenario: The run ends with an offered draft pull request
  Given a completed run on the fixture with gh available
  When the orchestrator reaches the end of the last round
  Then it asks the operator whether to open a draft pull request to the target branch
  And on yes, the pull request body lists each issue with its criteria and evidence
  And the report states the support tier the run ran at
```

## Out of Scope

- A machine-level installer — copying or symlinking the three skill directories is enough for v1; a script would add a surface to test before the loop itself is proven.
- Merging into the target branch — the draft pull request is the boundary chosen in `PRD.md` §3; merging belongs to the repository's own protection rules.
- Tool-specific gate adapters — the generic `mapping` in the policy covers any linter with JSON output; adapters would be premature before real repositories show which tools matter.
- Parity across the three harnesses as a release gate — the reference tier is proven on the fixture first; the supported and compatible tiers are announced as their fixture runs are recorded, not before.
- Spec authoring — `grilling` and `to-spec` already produce specs; the pack validates and slices them.
- Session security (output redaction, shell floor rules) — a harness policy layer covers it; the pack only avoids logging command output for checks marked `secrets: true`.
- Windows validation — no Windows machine is available to record a fixture run; support is declared only after one exists.

## Changelog

- 2026-09-13 — Documented the explicit derivation of a resumed Run's `correctionsSpent` (count of prior
  `refutation` events for the matching Issue in its own Run log; `runlog.py inflight` never reports it) and
  clarified that a resumed `branch` is optional because `round-workflow.md` derives and verifies it itself;
  documented that a ceiling-spent, refuted Issue keeps its authoritative `Status: ready-for-agent` and is
  only recorded as blocked in the Run log, so `frontier.py` still offers it; added lifecycle tests for the
  derived-resume path, the no-hooks protected-rules-in-prompts contract, and the still-workable refuted
  Issue.
- 2026-09-13 — Wired the canonical `SKILL.md` preflight and `round-workflow.md` execution to the Run log: `run.started`/`run.resumed` open a recorded Run, every phase, subagent start/stop, review finding, refutation, Issue outcome, policy change and completion or cancellation appends its event, a rerun offers continuation of an in-flight Issue in its preserved worktree with spent correction attempts retained, and Issue `Status:` and `roadmap.py` remain the only authority for readiness and completion.
- 2026-09-13 — Added an explicit, read-only cleanup plan that removes only done Issue branches and worktrees already merged into the Run branch after operator authorization.
- 2026-09-13 — Added effective-template Spec structural validation before planning, including mapped headings, required-section order, placeholder and Gherkin scenario checks.
- 2026-09-13 — Added an append-only, shared-worktree Run log with validated lifecycle events, atomic JSONL appends, policy snapshots, and interrupted Issue queries.
- 2026-09-13 — Made the Planner Issue result contract require every workflow-consumed field and fail planning before approval when an Issue has no valid path for deterministic context-budget measurement.
- 2026-09-13 — Added deterministic initial context-budget estimation from an Issue, its parent Spec and explicitly named files; declared model windows per harness and made over-budget plans numeric refutations with a two-attempt correction ceiling.
- 2026-09-13 — Added declared absolute and RFC 6901-mapped differential gates with isolated base comparisons, normalized finding identities, and severity-aware regressions.
- 2026-09-13 — Added role result contracts, standard-library validation and protocol-failure handling with one re-request before the phase fails.
- 2026-09-13 — Operator-approved a `make test` repository gate for the canonical workflow slice so the Run can establish a real passing gate instead of relying on a `no_gates` exception.
- 2026-09-13 — Made the executable round workflow fail closed unless the Critic supplies one passing,
  non-empty evidence entry for every acceptance criterion returned by `acceptance.py`.
- 2026-09-13 — Corrected the executable canonical plan and round workflows, policy-derived Issue/Spec artifact discovery, read-only acceptance CLI, and parked Issue reporting before readiness filtering.
- 2026-09-13 — Added the canonical harness-neutral Gantry workflow skill, default templates and portable legacy script contracts with regression coverage.
- 2026-09-13 — Added portable legacy policy defaults, optional repository overlay resolution and policy-rendered workflow paths while preserving the Markdown issue parser.
- 2026-09-13 — Defined RFC 6901 differential mapping, duplicate-identity rejection and resolved findings; defined canonical differential severity (`info < warning < error`) and per-Run dashboard stale-threshold snapshots (`dashboard.staleAfterSeconds`, default 900 seconds) after Requirement Critic findings.
- 2026-09-12 — Initial draft written from `PRD.md` §4–§14 after the pivot merge (823d27e); awaiting operator approval before slicing.
