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
- **Run log:** `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl`, where `unit-id` is the first twelve hex characters of the SHA-256 of the real path of `git rev-parse --git-common-dir`, so every worktree of one clone shares it. One JSON object per line: `ts`, `run`, `event`, optional `issue`, `phase`, `data`. A `run.started` event records the repository root, policy hash, tier and effective `staleAfterSeconds` in `data`; dashboard staleness uses that snapshot for the Run. A `policy.changed` event never changes an existing Run's snapshot, and the new policy takes effect when a later Run starts. Events: `run.started`, `run.resumed`, `run.cancelled`, `run.finished`, `round.started`, `round.finished`, `phase.started`, `phase.finished`, `subagent.started`, `subagent.stopped`, `compaction`, `hook.denied`, `hook.degraded`, `policy.changed`, `issue.done`, `issue.blocked`, `refutation`, `review.finding`. `hook.degraded` records `data.source` (the hook event name), `data.missing` (the list of declared payload field names absent from the payload) and `data.degraded: true`. The log stores references and the role results' JSON, never diffs or command output. Alongside the log, `runlog.py mark|current|unmark` keeps a per-worktree current-Run marker at `<git-dir>/gantry/current-run.json` — the Run ID and, optionally, the state root, no events — so a hook process that inherits no `GANTRY_RUN_ID` still records into the right Run; git keeps one git directory per worktree, which keys the marker per worktree.
- **Capabilities:** `.agents/skills/gantry/capabilities/{claude-code,opencode,codex}.json` with `tier`, `hooks`, `structured_output`, `worktree_isolation`, `per_role_model`, `parallel_round`, `skills_path`, `hook_events` and `payload_fields`. `guard.py` and the setup skill read them; the run report prints the tier.
- **Hook wiring:** `.agents/skills/gantry/hooks/claude-code.settings.json` (a `hooks` fragment merged into `.claude/settings.json`), `.agents/skills/gantry/hooks/opencode.plugin.js` (a plugin forwarding `tool.execute.before` and `session.compacted` to `guard.py`), `.agents/skills/gantry/hooks/codex.hooks.json`. Every entry executes `python3 <skillDir>/scripts/guard.py <event>` with the payload on stdin. Git-level rules — no force push, no test-skip commit — are enforced by the tracked git hooks `.agents/skills/gantry/hooks/git/{pre-commit,pre-push}` (sharing `hooks/git/skipscan.py`, a helper git never executes) activated through `core.hooksPath` (`docs/adr/0005`); `guard.py` only refuses Bash commands that would disable them (`--no-veri` (any `--no-verify` abbreviation), `core.hooksPath` in any case, `--git-dir`, `GIT_DIR=`, `GIT_CONFIG=`/`GIT_CONFIG_*`).
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
- A hook denial names its rule and the path it refused in one line; the same denial is always written to the run log as `hook.denied` when it happens inside a Run. Both the git hooks and `guard.py` resolve that Run in one order: an explicit `--run-id`, then `GANTRY_RUN_ID` when the caller exports it, then the marker, and a harness session ID only when nothing else names a Run and its Run log already exists — a session ID is a session, not a Run, so it never outranks the current-Run marker the round workflow writes into the worktree's own git directory before any agent works there, and a denial is never lost to the environment a git subprocess happened to inherit. A mark lives for the whole Run, never one round: the Run's end enumerates `git worktree list --porcelain` and clears every marker naming that Run, so a worktree marked by an earlier round is never left behind.
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

- 2026-09-14 — Corrected the Run resolution order a hook records through, and the Run-end unmark.
  `guard.py` resolved a payload's session ID ahead of the worktree's current-Run marker, and a
  harness session ID is not a Gantry Run ID: Claude Code sends a UUID `session_id` and OpenCode a
  `sessionID`, so no Run log is ever keyed by one. The guaranteed recording the entry below
  established was therefore empty for the configuration the pack actually ships — a real Claude Code
  `PreToolUse` payload carries no `--run-id` and no `GANTRY_*` variable, so every `hook.denied` in a
  marked worktree was resolved to a Run with no log and silently dropped. The order is now an
  explicit `--run-id`, then `GANTRY_RUN_ID` when the caller exports it, then the marker, and a
  harness session ID only when nothing else names a Run and its Run log already exists, matching
  `runlog.resolve_hook_run` at the git layer; `tests/test_guard.py` proves it with a real Claude Code
  payload (UUID `session_id`, `cwd`, `transcript_path`, `tool_name`, `tool_input`) and
  `tests/test_guard_hook_wiring.py` with the OpenCode equivalent forwarded through
  `hooks/opencode.plugin.js`. Separately, `reference/round-workflow.md` cleared only the worktrees
  the *current invocation* had marked, and each round is a separate invocation: an Issue finished in
  an earlier round is absent from the last one, so its worktree kept a marker naming a Run that was
  already over and the next denial there would record into a finished Run. The Run's end now
  enumerates `git worktree list --porcelain` from the repository root and unmarks every worktree
  whose `runlog.py current` equals this Run, proven by a `tests/test_canonical_gantry_workflow.py`
  case where an isolated Issue is worked in round 1 and absent from round 2.
- 2026-09-14 — Widened the guard's hook-disabling substring rule from `--no-verify` to `--no-veri`,
  the shortest abbreviation git itself accepts for that flag on both `commit` and `push`
  (`--no-ver` is refused as ambiguous with `--no-verbose`). git accepts any unambiguous
  abbreviation of a long option, so `git push --no-veri --force` was passing the previous
  substring check and landing a real forced update on a bare remote with no hook run and no
  denial line — a git hook cannot defend against its own `--no-verify`, so `guard.py` is the only
  layer where that spelling can be refused. Kept as a plain linear substring, so `--no-veri`,
  `--no-verif` and `--no-verify` are all caught, `--no-verb`/`--no-verbose` (a different flag that
  disables no hook) stays allowed, and a 1 MB payload is still answered in a few milliseconds.
  `tests/test_git_hooks.py` documents why with a temporary repository whose `core.hooksPath` is
  set, and `reference/round-workflow.md`'s Implementer and Critic prompts, `docs/adr/0005` and the
  Hook-wiring architecture bullet above now say "`--no-verify` in any abbreviation (e.g.
  `--no-veri`)" instead of the literal flag. Also added a round-workflow test proving the
  per-worktree current-Run marker on an *isolated* round: `runlog.py mark` is called with the
  Issue's own worktree (`<repoRoot>.gantry-<spec>-<nn>`) before the Implementer agent runs there,
  the marker exists in that worktree's own git directory (`git rev-parse --git-dir`) after the
  round, and is gone after the Run's last round.
- 2026-09-14 — Made `hook.denied` recording a guarantee, per the operator's decision on
  `gantry-migration#09` (Option A), replacing the provisional best-effort wording of the entry below.
  A git hook inherits the environment of whatever shelled out to `git`, which no harness controls, so
  the mechanism is not an exported variable: `runlog.py` gained a per-worktree current-Run marker
  (`mark`, `current`, `unmark`, stored at `<git-dir>/gantry/current-run.json` — the Run ID and an
  optional state root, no events), and `runlog.resolve_hook_run` resolves `GANTRY_RUN_ID` first and
  that marker second. `reference/round-workflow.md` marks the repository root at the start of every
  round and each Issue worktree as it is assigned, before any agent works there, and unmarks only when
  the Run ends; git keeps one git directory per worktree, so concurrent worktrees of one execution
  unit can never attribute a denial to each other's Run — the misattribution risk that made the earlier
  round defer this. `hooks/git/pre-commit`, `hooks/git/pre-push` and `guard.py` all record through that
  resolution, and `tests/test_git_hooks.py` now provokes a pre-commit and a pre-push denial in an
  environment stripped of every `GANTRY_` variable and still finds `hook.denied` in the Run log.
  Restored this spec's Constraints wording and `docs/adr/0005`'s decision paragraph to the
  unconditional guarantee, describing that mechanism. Also hardened `guard.py`'s hook-disabling
  substring rule with the spellings the round-4 critic landed real test-skip commits through —
  `core.hooksPath` matched case-insensitively (git configuration keys are case-insensitive) and the
  `GIT_CONFIG=`/`GIT_CONFIG_*` environment overrides — still a linear substring scan, still answering a
  1 MB payload in a few milliseconds. `git commit -n` (git's own short `--no-verify`) is deliberately
  *not* added to that list, because `-n` is unremarkable in `head -n` or `sort -n` and denying it would
  refuse ordinary commands: it is closed at the git layer instead, where `pre-push` now scans what a
  fast-forward push introduces (the remote's tip, or the parent of the oldest commit the push adds) for
  the same test-skip patterns `pre-commit` refuses, naming the same rule and path. Those patterns and
  the diff reader moved to `hooks/git/skipscan.py`, a helper beside the hooks that git never executes,
  and the standard-library import test now covers the git hooks as well as `scripts/`.
- 2026-09-14 — The round-3 critic asked for an operator decision before touching code: keep the
  `hook.denied`-recording contract guaranteed (build real `GANTRY_RUN_ID` propagation now) or accept
  best-effort recording as the shipped contract (amend this spec, keep ADR-0005's wording, and open the
  propagation Issue it already points at). The operator was asked (comment on `gantry-migration#09`) but
  had not answered by the time this round had to proceed; best-effort was kept as the lower-risk default
  because guaranteed recording's only pack-owned mechanism -- a per-unit "current Run" marker in
  `runlog.py` -- would misattribute denials across concurrent worktrees of one execution unit unless keyed
  per-worktree, which is real design work an operator should sign off on, not something to improvise
  un-reviewed in a hook that also has security consequences. This is a provisional call, not a closed
  decision: amended this Constraints section to say a hook denial is recorded "when a Run ID is present in
  the environment the hook's git subprocess inherits" rather than unconditionally (ADR-0005's own wording,
  which already stated this honestly, is unchanged), and opened `gantry-migration#19` as the owner of
  closing the gap (propagating `GANTRY_RUN_ID`/`GANTRY_STATE_ROOT` correctly, including across concurrent
  worktrees), left `Status: draft` pending the operator's choice of mechanism and confirmation that
  best-effort is acceptable in the meantime. Also added the literal `-i` spelling to `PreCommitHookTests`
  (AC4 names it; the suite previously only exercised `--include`) and tightened
  `NoHooksFallbackTests.test_implementer_prompt_states_every_protected_rule` to assert the exact
  `implementPrompt` sentence rather than four separate file-wide substrings, matching how
  `test_critic_prompt_checks_every_protected_rule` already asserts its exact sentence.
- 2026-09-14 — Addressed adversarial-critic feedback on the no-hooks fallback: `round-workflow.md`'s
  `implementPrompt` now states the hook-bypass rule explicitly ("Never bypass the repository git hooks:
  no `--no-verify`, no `core.hooksPath` override, no `--git-dir`/`GIT_DIR=`.") alongside the existing
  ROADMAP/Status/checkbox and no-force-push/no-test-skip rules, and `criticPrompt` now checks for it too
  ("So is any commit or push made with `--no-verify` or under a `core.hooksPath`/`--git-dir`/`GIT_DIR=`
  override, and any test-skip pattern that reached HEAD despite the hooks."), so a harness with no hook
  support still gets the rule stated to the Implementer and verified by the Critic.
  `tests/test_guard_hook_wiring.py`'s `NoHooksFallbackTests` now asserts the exact wording of both.
- 2026-09-14 — Addressed code-review findings on the git hooks: `pre-push`/`pre-commit` printed their denial line twice (stdout and stderr), which git echoes onto the operator's terminal as a duplicate; both now print it once, on stderr only, and `tests/test_git_hooks.py` asserts exactly one `deny:`-prefixed line per denial the way `tests/test_guard.py` already does for `hook-bypass-protected`. Also corrected `docs/adr/0005-git-hooks-enforce-git-rules.md`'s claim that "the harness guard already propagates" `GANTRY_RUN_ID`: nothing in this pack exports that variable into a subagent's Bash environment, so outside a test that sets it directly, a hook denial still prints and still refuses the operation but is not yet recorded. Making the Run orchestrator (`gantry-migration#14`'s round workflow) export `GANTRY_RUN_ID` (and `GANTRY_STATE_ROOT`) into every subagent invocation it starts is deferred pending an operator decision on which Issue absorbs it, recorded as a comment on `gantry-migration#09`, the same way writing `core.hooksPath` into the operator's repository was deferred to `gantry-migration#10`.
- 2026-09-14 — Moved no-force-push and no-test-skip-commit enforcement out of `guard.py`'s Bash-command parsing and into the repository's own git hooks (`docs/adr/0005-git-hooks-enforce-git-rules.md`): added `.agents/skills/gantry/hooks/git/pre-push`, which rejects any ref update whose remote SHA is not an ancestor of its local SHA -- `git merge-base --is-ancestor <remote-sha> <local-sha>` failing -- covering `--force`, `-f`, combined short flags (`-uf`), `+refspec`, `--mirror` and `--force-with-lease` without recognising any of them by name, and `.agents/skills/gantry/hooks/git/pre-commit`, which rejects a commit whose staged diff (`git diff --cached`, inheriting whatever `GIT_INDEX_FILE` git itself set for a pathspec/`--include` commit) introduces a test-skip pattern, covering `-a`, pathspecs, `-i`/`--include`, `git stage` and a plain prior `git add` because git resolves that staging semantics before the hook ever runs. Both hooks print one denial line naming the rule and the path/ref and append `hook.denied` through `runlog.py` using `GANTRY_RUN_ID` (and a new `GANTRY_STATE_ROOT` override for tests) whenever a Run log already exists for that Run. Deleted the quadratic-risk Bash-command machinery this replaces from `guard.py` (`COMMIT_SEGMENT_RE`, `GIT_ADD_SEGMENT_RE`, `FORCE_FLAG_RE`, `FORCE_REFSPEC_RE`, `_bounded_tokens`, `commit_uses_all_flag`, `extract_git_add_targets`, `tracked_worktree_skip_match`, `staged_diff_skip_match`, `untracked_skip_match` and their tests); `guard.py`'s only remaining Bash rule is a linear substring check (`hook-bypass-protected`) refusing a command carrying `--no-verify`, `core.hooksPath`, `--git-dir` or `GIT_DIR=`, since those would disable the git hook layer -- it tokenises nothing, so a 1 MB command is answered in a few milliseconds, and it allows every other Bash command. Edit/Write/MultiEdit protection of `ROADMAP.md` and Issue Status/checkbox fields, and `hook.degraded` handling, are unchanged.
- 2026-09-14 — Hardened the guard hook handler a third time: `CHECKBOX_LINE_RE`/`CHECKBOX_FULL_LINE_RE`/`CHECKED_CHECKBOX_RE` now anchor on `[ \t]*` instead of `\s*` after `^`, so a large whitespace-heavy Issue edit or write (which could previously trigger O(n^2) backtracking because `\s` also matches the newlines `^` anchors on) is still decided in well under 200ms; `_bounded_tokens()` no longer truncates a `git commit`/`git add` segment to a fixed prefix before tokenising -- segments up to 4096 characters still use `shlex.split()`, longer segments fall back to a full, linear-time `segment.split()` -- so a trailing `-a`/`-A`/`--all` after a long commit message, or a `git add` target beyond the first few hundred files, is never silently dropped; and `decide()` now normalizes a Bash command with `re.sub(r"\\\n", " ", command)` before any segmenting, so a `git commit`/`git add`/`git push` split across a shell backslash-newline continuation is evaluated the same as its single-line equivalent instead of bypassing detection.
- 2026-09-14 — Fixed the guard hook handler's Bash-command gating for `no-force-push`/`no-test-skip-commit`: the `\bgit\b[^&|;]*\bpush\b`/`...commit\b` regex searches were quadratic (each retried a full backtrack from every `git` occurrence when no `push`/`commit` followed), so a 1 MB command carrying many `git` tokens but no `push`/`commit` could hang; `decide()` now splits the command on `[&|;\n]` and whitespace-tokenises each segment once, flagging a segment only when a `git` token is followed later by a `push`/`commit` token, keeping the whole check O(n) regardless of how many `git` tokens the command contains.
- 2026-09-13 — Hardened the guard hook handler again: `roadmap-protected` now compares an edited or written file's basename case-insensitively (`roadmap.md`/`Roadmap.md` are denied the same as `ROADMAP.md`), and the `git commit`/`git add` segment tokeniser now excludes newlines from its match (so a heredoc body never reaches the tokeniser) and bounds what it hands to `shlex.split()` to a fixed prefix length, so a 1 MB heredoc-shaped or single-token commit-message payload is still decided in under 200ms.
- 2026-09-13 — Fixed the guard hook handler's Edit/MultiEdit simulation to honor a truthy `replace_all`/`replaceAll` flag on each edit by replacing every occurrence of `old_string` (not just the first), so a `replace_all` edit whose first textual match sits outside the Status/checkbox lines but whose later match is one of them is still denied; edits without the flag keep replacing only the first occurrence, and a missing `old_string` still falls back to `None` for the coarser text-based check.
- 2026-09-13 — Hardened the guard hook handler further: a `git commit` preceded by a `git add` segment, or passing `-a`/`--all`/`-A`, is now checked against the working tree (unstaged tracked changes via `git diff HEAD`, plus untracked files named by the `git add` arguments or all untracked files for `git add .`/`-A`) instead of the index alone; an Edit/MultiEdit on an existing Issue file is now evaluated by applying its edits to the file's real content in memory and comparing Status lines and checkbox lines before and after, so a value-only edit (e.g. `ready-for-agent` -> `done`, or `[ ]` -> `[x]` without its `- ` scaffolding) is denied even though neither its `old_string` nor its `new_string` alone matches the protected pattern.
- 2026-09-13 — Added `hook.degraded` to the Run log's Blueprint Events list alongside its data contract, and changed the guard hook handler so empty/undecodable/non-object stdin records one `hook.degraded` event with `data.missing == ["payload"]` whenever a Run ID is resolvable from `--run-id` or `$GANTRY_RUN_ID` (never from the unreadable payload); with no Run ID at all it still records nothing.
- 2026-09-13 — Fixed the guard hook handler's draft-Issue exemption to apply only to *creating* a new Issue file: an existing Issue's Status/checkbox fields now always fall through to protection even when the new content looks draft-safe on its own, and `decide()` now prefers the payload's own `cwd`/`directory` field over `--cwd` when locating an Issue path or the staged diff to check for test-skip commits.
- 2026-09-13 — Hardened the guard hook handler: capability-incomplete payloads (per the harness's declared `payload_fields`) now record a `hook.degraded` Run log event instead of a false completion or a denial, draft Issue creation is exempt from the Status/checkbox protection, test-skip patterns are anchored so they no longer match their own literals in guard's sources, and a force-pushing `+refspec` is denied alongside `--force`.
- 2026-09-13 — Added the guard hook handler and its Claude Code, OpenCode and Codex wiring, protecting the roadmap and Issue Status/checkbox fields, force-pushes and test-skip commits, and recording hook and subagent events into the Run log.
- 2026-09-14 — Addressed a fifth retry round of adversarial-critic feedback on the optional Learner
  phase and the host command-runner contract. `round-workflow.md`'s `learn()` now records the Learner
  phase like every other phase — `phase.started`, `subagent.started` (`role: 'learner'`),
  `subagent.stopped` (carrying the drafted candidates as its result) and `phase.finished` — but only
  when it actually runs (recurring evidence found); a short-circuited Learner (no Run-log path, or
  nothing recurring) records none of those four events. Because `runlog.py` requires an `issue` on
  every `phase.started`/`phase.finished` event and the Learner is not scoped to one Issue, these events
  use the reserved, non-Issue reference `learn#00`. The workflow's tail was reordered so
  `const candidates = A.isLastRound ? await learn() : []` runs after `round.finished` but before
  `run.finished` is appended, so `run.finished` remains the Run log's last event on a completed Run and
  no subagent runs after it — previously `learn()` ran after `run.finished`, letting a Learner subagent
  execute after the Run's own recorded completion. `SKILL.md` and `round-workflow.md`'s 'Recorded Run
  lifecycle' prose no longer scope phase/subagent pairs to only Implement, Review and Critic, and both
  now state the Learner phase is recorded before `run.finished`. A new workflow integration test,
  `test_round_workflow_records_the_learner_phase_before_run_finished`, runs the canonical workflow as
  the last round of a Run with `learnerRunLogs` pointing at a fixture Run log containing two recurring
  `refutation` events, and asserts the Learn phase's `phase.started`/`subagent.started`/
  `subagent.stopped` (with a `result`)/`phase.finished` events are present, in order, between
  `round.finished` and the final `run.finished` event. The host contract prose in both `SKILL.md` and
  `round-workflow.md` now reads `runCommand(command, { cwd, input })` and states that `input`, when
  supplied, is written to the invoked command's stdin — every recorded Run event goes through
  `runlog.py append` this way, so a harness port that drops `input` breaks every recorded round, not
  only this one.
- 2026-09-14 — Addressed a fourth retry round of adversarial-critic feedback: the Critic's `subagent.stopped`
  no longer carries its verdict unchanged into the Run log. A Critic proving completion runs a real
  `gates.py --run --diff-base <baseRef> --json` and returns that parsed payload unchanged in
  `gateResult` (the spec's own contract), so `gateResult.gates[]` carries real `command` and
  `output_tail` fields for every gate it ran — and `runlog.py append` rejects any `command`- or
  `output`-tokenized key at any nesting depth by its own rule (spec line 25: the Run log records
  references and role results, never command output). Recording the raw verdict would therefore throw
  on every genuinely gate-green Critic pass, breaking the Run log for real work rather than only for
  disallowed data. `round-workflow.md` now records `projectCriticResult(verdict)` instead: `complete`,
  `criteria`, `gatesVerdict`, `gateFailures`, `refutations`, `requiredFixes` and `decisionsForOperator`
  pass through unchanged, and `gateResult` is narrowed to only its `verdict` and `requirements` strings
  — dropping `gates` (and therefore every `command`/`output_tail`) entirely. This keeps the Run log a
  record of the Critic's role result and reasoning about the gates, never of the gate commands' output,
  while `criticAccepted` and the workflow's own structured output still see the full, untouched verdict.
  `runlog.py` keeps failing loudly on prohibited data from any other role. `SKILL.md` and
  `round-workflow.md`'s 'Recorded Run lifecycle' prose now describe this projection, and a new workflow
  integration test in `tests/test_canonical_gantry_workflow.py` runs the canonical workflow with a Critic
  double that returns a `gateResult` shaped exactly like real `gates.py --json` output (`gates[{name,
  source, command, exit_code, output_tail, status}]`, `requirements`, `git`, `verdict: 'pass'`) under
  `commandMode: 'real'` with `runId`/`unitId` set, asserting the round reaches `'done'`, a Critic
  `subagent.stopped` event is present, and no line of the recorded Run log contains a `command` or
  `output` key.
- 2026-09-13 — Addressed a third retry round of adversarial-critic feedback on multi-round Runs:
  `round-workflow.md` now takes an explicit `args.isFirstRound` (default `true`) alongside
  `args.isLastRound`, so `run.started`, `run.resumed` and `policy.changed` are appended only on the
  first round of a Run and `run.finished` only on its last, while `round.started` / `round.finished`
  still record every round — a Run log accepts exactly one `run.started` and rejects a duplicate, so a
  second round that still emitted it would previously throw. Proven by a new test that runs
  `round-workflow.md` twice under the same `runId`/`unitId` (round 1 with `isFirstRound` defaulted and
  `isLastRound: false`, round 2 with `isFirstRound: false` and `isLastRound: true`) and asserts exactly
  one `run.started`, one `round.started`/`round.finished` pair per round, and exactly one `run.finished`
  emitted last, only after round 2. The previously merged single-round lifecycle test now passes
  `isLastRound: true` to match. This branch has also been updated by merging current `main` (which
  carries `gantry-migration#04`, `#11`, `#13` and `#16`'s real `fixture/` history) rather than the prior
  round's copy-only stand-in, resolving a real conflict in `round-workflow.md`'s final block where the
  `run.finished` and Learner-phase gating from both branches are unified under `args.isLastRound`.
- 2026-09-13 — Addressed a retry round of adversarial-critic feedback: `runlog.py`'s
  `derive_corrections_spent` now withholds the `run.resumed.data.correctionsSpent` base unless that
  same `run.resumed` event's `data.issue` also equals the Issue being queried — the base is per-Issue,
  never per-Run, so one Issue's resumed budget can no longer leak into another Issue that shares the
  same Run log — proven by a dedicated unit test with one Run log resuming Issue A (base 2) alongside
  Issue B's own started correction pass and an unrelated Issue C absent from the log entirely (A stays
  2, B is 1 from its own pass alone, C is 0). `runlog.py corrections` also now fails closed
  (`runlog error: no Run log for <runId>`, exit 1) instead of silently reporting `0` when no Run log
  exists for the requested Run ID; `SKILL.md`'s preflight prose, `round-workflow.md`'s 'Recorded Run
  lifecycle' section and this changelog now say so. The AC1 fixture test
  (`test_gantry_greeting_offers_and_resumes_a_fixture_interrupted_run_in_its_worktree`) was strengthened
  so the prior interrupted Run's log carries a real refutation for `greeting#02` followed by a
  `phase.started` Implement (so `runlog.py corrections` derives `1`, not `0`), the resumed Run's
  `run.resumed.data.correctionsSpent` is asserted to equal `1`, and the resumed round is asserted to
  spend its one remaining correction attempt before `issue.blocked` records `data.corrections == 2`,
  with worktree `W` preserved and `greeting#02` still `Status: ready-for-agent`.
- 2026-09-13 — Addressed adversarial-critic feedback on the recorded-Run wiring: `run.resumed` now carries
  `issue` and `correctionsSpent` alongside the prior Run and worktree; Review and Critic `phase.started`
  events now carry `worktree` so an interrupted Review or Critic phase surfaces in `runlog.py inflight`;
  documented the derivation rule for a resumed `correctionsSpent` as `run.resumed.data.correctionsSpent`
  (or `0`) plus refutations in that same Run's log that actually started a correction pass (a later
  `phase.started` Implement for the same Issue), replacing the earlier `data.attempt - 1` sub-rule; and
  added a chained-resume test proving the rule composes correctly across three Runs, an inflight test for
  interrupted Review/Critic phases, and stronger ordering assertions on the isolated multi-Issue serial
  integration test (exactly one `--no-ff` merge and one gate per Issue, in order, with nothing after the
  red post-merge gate).
- 2026-09-13 — Resolved the prior entry's open stand-in: the `fixture/` tree from `gantry-migration#16`
  (as it stands on `gantry/wave-3` at `e546aa8`) is now merged into this branch, and
  `test_gantry_greeting_offers_and_resumes_a_fixture_interrupted_run_in_its_worktree` proves this Issue's
  acceptance criterion against the real fixture: it builds an isolated `copy_fixture.py --mode approved`
  copy, simulates a Run interrupted while the fixture's real `greeting#02` Issue was in the Implement phase
  in worktree `W`, shows `runlog.py inflight` offering `W`, and resumes `round-workflow.md` in `W` so that
  `run.resumed` carries the prior Run id and `W` while `greeting#02` keeps `Status: ready-for-agent` (proven
  against the real Issue file, not a synthetic stand-in). The `resumeq#01`/`resume#01`-based tests remain as
  additional coverage of the derivation and chained-resume rules, not as a substitute for this criterion.
- 2026-09-13 — Addressed a second round of adversarial-critic feedback: `runlog.py corrections <unitId>
  <runId> <issue> [--json]` is now a shipped, tested query — the sole implementation of the documented
  `correctionsSpent` derivation rule — and `SKILL.md`'s preflight prose and this Issue's tests all invoke it
  instead of duplicating the rule in prose or in test-local Python; `appendRunEvent` in
  `round-workflow.md` now runs `runlog.py append` through `runWorkflowCommand`, so a rejected event (for
  example a prohibited key such as `gateResult.diff`) throws instead of being silently discarded, proven by
  a test that asserts the thrown error and the missing Run log line; and the 'Recorded Run lifecycle'
  paragraph now states plainly that `run.started` always opens a recorded Run and `run.resumed` follows it
  when `args.priorRun` is supplied, matching both the code and `runlog.py`'s own first-event rule.
- 2026-09-13 — Documented the explicit derivation of a resumed Run's `correctionsSpent` (the prior Run's own
  `run.resumed.data.correctionsSpent`, if any, plus every `refutation` event for the matching Issue that is
  later followed by a `phase.started` `Implement` event — i.e. only refutations whose correction pass
  actually started — read from the matched Run's own log; `runlog.py inflight` never reports it) and
  clarified that a resumed `branch` is optional because `round-workflow.md` derives and verifies it itself;
  documented that a ceiling-spent, refuted Issue keeps its authoritative `Status: ready-for-agent` and is
  only recorded as blocked in the Run log, so `frontier.py` still offers it; added lifecycle tests for the
  derived-resume path, the no-hooks protected-rules-in-prompts contract, and the still-workable refuted
  Issue.
- 2026-09-13 — Wired the canonical `SKILL.md` preflight and `round-workflow.md` execution to the Run log: `run.started`/`run.resumed` open a recorded Run, every phase, subagent start/stop, review finding, refutation, Issue outcome, policy change and completion or cancellation appends its event, a rerun offers continuation of an in-flight Issue in its preserved worktree with spent correction attempts retained, and Issue `Status:` and `roadmap.py` remain the only authority for readiness and completion.

- 2026-09-13 — Routed the Requirement Critic result through the same `requestRole` validation as every
  other role, added its Result Contract schema and registered role, and stopped the run with a Protocol
  Failure instead of silently proceeding when the result is missing or invalid.
- 2026-09-13 — Added a read-only Requirement Critic phase after Spec structural validation and before
  research or Issue slicing; a blocking finding quotes the Spec and stops the run for the operator to
  amend the Spec, and structural validation and Requirement Review are documented as not approving
  planning by themselves.
- 2026-09-13 — Added the read-only, loopback-only multi-Run kanban dashboard (`dashboard.py` and the `gantry-dashboard` skill): swimlanes per Run, Ready/Plan/Implement/Review/Critic/Integrate/Done/Blocked columns, per-Issue badges, and staleness computed only from each Run's own `run.started` `staleAfterSeconds` snapshot.
- 2026-09-13 — Added the optional Learner phase: a deterministic `learner.py` groups recurring
  `refutation` and `review.finding` Run-log evidence across Issues or attempts into lesson candidates
  validated by `schemas/learner.json`, and the round workflow and final report surface them as operator
  decisions without writing to `AGENTS.md`, `CONTEXT.md`, a template or policy.
- 2026-09-13 — Added the reusable `fixture/` reference repository (a minimal
  Python greeting project, a standard-library JSON linter, a declared absolute
  `pytest` check and RFC 6901-mapped differential `lint` check, and a valid
  greeting Spec) and its deterministic isolated-copy builder,
  `fixture/tools/copy_fixture.py`, producing an unplanned no-Issue copy and an
  approved copy with three `ready-for-agent` legacy-format greeting Issues,
  each an independent Git repository with a baseline commit and a pack-visible
  local Gantry-skill installation.
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
