# Gantry — Product Requirements

**What it is:** a harness-neutral skill pack that runs an agentic software development life cycle inside the operator's coding harness. Deterministic scripts decide which work is ready and whether a delivery is done; agents plan, build, review and refute; the operator decides, in the conversation.

**Status:** requirements agreed on 2026-09-12 (see [ADR-0004](docs/adr/0004-skill-pack-instead-of-an-engine.md)). The pack evolves the existing `asdlc` skill in this repository; nothing described here is claimed to exist until the fixture exercises it (§13). Vocabulary is defined in [`CONTEXT.md`](CONTEXT.md) and is used here without redefinition.

---

## 1. Problem

Agentic coding fails in predictable ways: agents lose precision as context grows, split work by layer instead of by behaviour, pass tests while eroding architecture, declare themselves done without evidence, and tick their own boxes. Prose instructions in `AGENTS.md` reduce none of this reliably, because prose is probabilistic. Tools that fix it with a separate orchestrating engine add a second runtime, a database and a setup step that most repositories never complete.

The `asdlc` skill showed that the loop can be made trustworthy with five dependency-free scripts and two workflow templates, as long as the scripts own every decision that must not be improvised. Gantry is that approach finished: packaged, configurable per repository, observable, and honest about what each harness can guarantee.

## 2. Principles

1. **Agents + code > agents alone.** Every decision that must not be improvised — what is ready, what must be proven, whether gates pass, when an issue is done — is made by a workflow script. Agents never re-decide what a script decided.
2. **Scripts decide; hooks guard and record; agents propose; the operator decides** ([ADR-0003](docs/adr/0003-scripts-decide-hooks-guard-and-record.md)). Guard hooks block shortcuts and write events. They never grant completion.
3. **Fail closed.** An uncertain critic, a missing result, a dirty tree, a gate that could not run: not done.
4. **One authority per fact.** An issue's `Status:` line and checkboxes, written only by the roadmap script, say where work stands. The run log says how it got there. The dashboard shows both and changes neither.
5. **Never weaken verification.** No test is skipped, disabled, mocked-away or deleted to get green, and no delivery that did so is accepted.
6. **The operator's checkout stays free.** A run offers a dedicated worktree before it creates anything.
7. **Honest capabilities.** Each harness's capabilities are declared in a file and exercised on the fixture; a run report states the support tier it ran at. Gantry never advertises a guarantee it cannot measure.
8. **Artifacts are English**, whatever the conversation language.

## 3. Scope

| In v1 | Out, deliberately |
|---|---|
| Plan: spec structural validation, requirement review, slicing into issues, plan critique, stop for planning approval | Spec authoring (covered by existing skills such as `grilling` → `to-spec`) |
| Rounds: TDD implementer → two-axis review → adversarial critic with a correction budget → serial integration with gates → roadmap update | Merging into the target branch; stacked branches or per-issue pull requests |
| Declared gates, pass/fail or differential (entropy gate) through a generic structured-output mapping | Tool-specific adapters; evidence classification; baseline transition manifests |
| Result contracts (JSON Schema per role) validated by a script | Task envelopes, submission receipts, idempotent replay |
| Guard hooks where the harness supports them; run log; read-only dashboard | Database, MCP server, settings screen, capability tokens, mutating dashboard |
| Learner phase proposing lesson candidates | Automatic injection of lessons |
| Draft run pull request via `gh` | Pull request observation, provider reconciliation, release lifecycle |
| Setup skill writing the repository policy, templates and `AGENTS.md` section | Machine-level installer (copy or symlink the pack; a script may come later) |
| Context budget estimate at planning; compaction recorded as a signal | Context watermark as a guarantee; handoff memos |
| Three harness support tiers with a fixture per tier | Parity across all harnesses as a release gate |
| Cleanup plan printed at the end of a run | Automatic worktree or branch removal; session security (redaction, shell floor rules — see §11) |

## 4. Shape of the pack

Three skills, side by side, one thick and two thin:

```
.agents/skills/
├── gantry/                    the workflow; triggers on "implement spec X", "run wave 1", "rodar o gantry"
│   ├── SKILL.md               preflight → models → frontier → plan | rounds → run PR → report
│   ├── reference/             plan-workflow.md, round-workflow.md (harness-neutral prompts + Claude Code Workflow scripts)
│   ├── scripts/               frontier, acceptance, gates, roadmap, spec, budget, result, runlog, guard, cleanup, dashboard
│   ├── schemas/               result contracts: planner, plan-critic, implementer, reviewer, critic, learner
│   ├── templates/             spec.md, prd.md, issue.md — the pack defaults
│   ├── capabilities/          claude-code.json, opencode.json, codex.json
│   └── hooks/                 wiring per harness for the guard script
├── gantry-setup/SKILL.md      conversational; the only writer of the repository policy
└── gantry-dashboard/SKILL.md  opens the read-only kanban
```

Scripts are Python 3.10+ standard library only and need nothing from the harness beyond `python3` and `git` (`gh` for the run pull request). Cleanup and the Learner are steps of `gantry`, not skills.

This repository is the pack: the three directories above are real directories under `.agents/skills/`, with `.claude/`, `.cursor/`, `.opencode/` and `.gemini/` skill directories symlinked to it. It also holds `fixture/` (§13), `docs/adr/`, `CONTEXT.md`, `AGENTS.md` and this document.

## 5. Where things live

| What | Where | Tracked | Written by |
|---|---|---|---|
| Skill pack | `<repo>/.agents/skills/gantry*` **or** `~/.agents/skills/gantry*`; the repository copy wins | repo copy: yes | installation |
| Repository policy | `<repo>/.gantry/config.json`, sparse; absent keys fall back to pack defaults | yes | `gantry-setup` only |
| Repository templates | `<repo>/.gantry/templates/` only when the operator customised them | yes | `gantry-setup` |
| Run log | `~/.gantry/state/<unit-id>/runs/<run>.jsonl`; `unit-id` derives from the Git common directory so every worktree of a clone shares it | no | workflow scripts and guard hooks only |

The run log holds events and references — issue refs, phases, worktree paths, commit SHAs, counts, the JSON results of each role — never diffs, prompts or command output beyond what a declared check's policy allows (§7). Nothing about execution enters git; git keeps only what it already keeps: `Status:` lines and criteria checkboxes.

## 6. The workflow

### 6.1 Preflight and models (orchestrator, inline)

Parse the scope (`<spec-slug> | spec#NN | wave:N | frontier | all | "goal"`), `--limit` (issues per round, default 4) and `--budget` (correction budget, default from policy, 2). Refuse a dirty tree. Offer a dedicated worktree on branch `<prefix>/<scope-slug>` from the target branch — always, before anything is created. Present all models the effective execution environment can actually run, with supported reasoning effort levels. Ask once for harness, model and effort for Plan, Implement, Review and Critic; every role may use a harness different from the Host Harness (ADR-0006). Relative strength of Plan and Critic versus Implement is advisory; the operator retains the final choice. Versioned role defaults live in `.gantry/config.json`, written through `gantry-setup`; validate every effective selection before work starts. Run and Issue-role overrides do not change saved defaults. Execution failures preserve work and pause the affected Issue without automatic fallback; independent Issues may finish, but the next round waits for explicit recovery. An external Critic directly inspects the delivered revision and independently executes acceptance and gates. These are agreed requirements, not a claim of implemented support (see `.scratch/role-execution-selection/spec.md`). Run `roadmap.py check`; drift is fixed with the operator before anything else. Open the run in the run log with the policy hash, the harness and its support tier.

### 6.2 Readiness of the spec (scripts, then a critic)

Before slicing: `spec.py --check <spec>` validates the spec against the effective template — required sections, order, placeholders, scenarios — accepting equivalent headings declared in the policy's mapping. Then the **Requirement Critic** (Critic model) reviews ambiguity, coherence, verifiability and non-goal coverage. A blocking finding stops the run; the operator amends the spec. Neither step edits the spec.

### 6.3 Planning (plan workflow)

Only when the scope is unplanned (a spec without issues, an issue without criteria, or a free-text goal). Research in parallel (codebase, spec and settled decisions, exemplar issue format) → the planner writes issues in the effective issue template with `Status: draft`, observable acceptance criteria, real `## Blocked by` refs and no cycles → `budget.py` estimates each issue's initial package (issue + spec + files it tells the implementer to read) against the chosen model's window; over 15% is refuted with the number → the plan critic refutes slicing, criteria quality, coverage and format, with one revision pass → **stop**. The operator approves the breakdown; only then are issues set to `ready-for-agent` and the roadmap regenerated.

### 6.4 Rounds (round workflow)

`frontier.py` computes rounds from the blocker graph; it exits non-zero on a cycle or dangling ref, and lists parked (`blocked`, `needs-operator`, `draft`) and externally blocked issues, which are skipped, not failed. Per round, every issue runs its own chain without barriers:

1. **Implementer** (fresh agent, `tdd` skill, its own worktree when the round has more than one issue): every criterion, failing test → minimal code → refactor, small commits, clean tree, `gates.py --run`. Never touches `ROADMAP.md`, `Status:` or checkboxes.
2. **Reviewer**: standards axis and spec axis; blocking findings get exactly one fix pass by a fresh implementer in the same worktree.
3. **Critic** (fresh agent): runs `acceptance.py` and `gates.py` itself, demands evidence per criterion, inspects the diff for skipped tests, mocks standing in for required real things, TODOs and scope creep, defaults to not complete. Refutation → a fresh implementer with the ordered `requiredFixes`, up to the correction budget. Budget spent → `Status: blocked` with the critic's refutations and the worktree path in `## Comments`.
4. **Integration** (orchestrator): `complete` issues merge into the run branch one at a time with `--no-ff`; `gates.py` runs after each merge; a red gate after a merge stops the run — the merge, not the slice, is at fault. Then `roadmap.py done <ref>` — the only way an issue becomes done — and a commit naming the slice.

If every issue in a round completes, the next round starts without asking. Otherwise the run stops after the round and reports; later rounds may depend on what failed.

### 6.5 After the last round

`roadmap.py check` clean; `frontier.py` shows what is left. **Learner** (optional, Critic model): reads only the refutations and review findings recorded in the run log and drafts lesson candidates for problems that recurred across issues or attempts, each with evidence and a proposed target (`AGENTS.md` Gantry section, `CONTEXT.md`, a template). Candidates are drafts; nothing is injected. **Run pull request**: offer to open a draft PR from the run branch to the target with `gh`, one per run, its body generated from each issue's critic evidence; no `gh` or no yes → report the branch instead. **Report**: outcome per issue with the critic's evidence, operator decisions surfaced by agents, gate results after integration, lesson candidates, the support tier the run ran at, the next frontier, and the cleanup plan (`cleanup.py --plan`).

### 6.6 Results and protocol failures

Every agent's result must satisfy the role's result contract in `schemas/`. Where the harness enforces structured output the schema is loaded directly; everywhere else the orchestrator runs `result.py --role <role>` before accepting. A missing or invalid result is a protocol failure: the work stays in the worktree, the agent is asked once more, then the issue is reported as failed for that phase. There is no separate infrastructure retry budget.

## 7. Gates

Gates are declared in the repository policy by the setup skill (§10) and detected by `gates.py` where no policy exists (package scripts, pytest, Makefile targets, pre-commit). Each declared check is **absolute** (pass/fail by exit code — tests, secret scans) or **differential**: the policy names where `rule`, `file`, `line` and `message` live in the command's structured output, and `gates.py` runs the same command on the round's base and on the delivery, matches findings by rule, file and problem identity, and reports new, aggravated, resolved and preexisting findings. New or aggravated findings block; preexisting ones stay visible and do not. A check without a declared mapping is pass/fail only. `gates.py --json` is what the critic reads; it never paraphrases it. `no_gates` means not complete unless the issue's own criteria create the gates and the critic ran them. Changing a check's command or configuration simply changes what runs on both sides; there is no separate baseline-transition procedure.

## 8. Guard hooks

Where the harness supports hooks, `guard.py` reads the harness's event payload on stdin and answers allow, deny or context; `hooks/` holds the wiring per harness (a `settings.json` fragment for Claude Code, a generated plugin for OpenCode, `hooks.json` for Codex). v1 invariants, each also enforced by prose and by the critic so that a harness without hooks loses enforcement, not semantics:

- deny edits to `ROADMAP.md`, to an issue's `Status:` line or to its criteria checkboxes by any tool other than the roadmap script;
- deny `git push --force` and test-skip patterns being committed;
- record `SubagentStart`/`SubagentStop`, phase transitions and compaction events (`PreCompact`, `session.compacted`) into the run log.

The setup skill enables recording hooks by default and asks before enabling denying ones. A hook that fires in a harness where the payload lacks a field it needs degrades to recording and says so in the run log.

## 9. Dashboard

`gantry-dashboard` runs `dashboard.py`: a Python `http.server` bound to loopback serving a static kanban that reads every run log under `~/.gantry/state/`. Cards are issues; columns are phases (Ready, Plan, Implement, Review, Critic, Integrate, Done, Blocked); swimlanes are runs; badges show repository, branch or worktree, model per role, corrections spent against budget, time in phase, and compaction events. A card waiting for the operator says so and names the harness session. A run whose last event is old is shown stale. The dashboard makes no request that changes anything.

## 10. Setup

`gantry-setup` connects a repository to the pack, conversationally and item by item — benefit, trade-off, default, yes or no — never enabling what the operator did not accept, showing the full proposed `config.json` before writing, and idempotent (an existing policy is shown and merged, overwritten or left alone on request). It owns:

| Item | Writes | Default when skipped |
|---|---|---|
| Artifact locations | where specs, issues, ADRs and settled decisions live | `.scratch/<slug>/spec.md`, `.scratch/<slug>/issues/`, `docs/adr/` |
| Templates | copies pack templates to `.gantry/templates/` only if customised; declares equivalent-heading mappings for legacy specs | pack templates |
| Checks | commands, absolute or differential, output mapping, whether output may contain secrets (then only exit codes and counts are logged) | `gates.py` detection, all pass/fail |
| Git | target branch, branch prefix | `main`, `gantry/` |
| Guard hooks | which to enable, per detected harness capabilities | recording on, denying asked |
| `AGENTS.md` | a marked `<!-- gantry:begin -->…<!-- gantry:end -->` section with the workflow rules; never overwrites the rest | created if absent |

The effective template is the source of structural validation: changing the template is changing the check.

## 11. Compatibility with a harness policy layer

Gantry is not a session security layer. Output redaction, shell floor rules, secret-access denial and policy-tamper detection belong to a harness policy layer such as the [harness-toolkit](https://github.com/tech-leads-club/harness-toolkit); Gantry does not depend on one and stays compatible with one. The pack ships an example operator rule for that toolkit ("no `roadmap.py done` without a critic subagent since HEAD") for operators who already run it.

## 12. Run lifecycle

| Aspect | Rule |
|---|---|
| Correction budget | 2 per issue by default (policy or `--budget`); a ceiling, never raised silently; the review fix pass is separate and fixed at 1 |
| Agent failure | protocol failure: one re-ask, then `failed`; no retry budget |
| Resume | rerun the same scope: the frontier is recomputed from `Status:` lines; the run log's in-flight record lets the orchestrator offer to continue an issue in its existing worktree; the operator chooses; spent budgets stay spent |
| Policy changed mid-run | recorded as an event; shown on the dashboard; nothing else |
| Cancel | stop the harness; `run.cancelled` is logged when possible, otherwise the dashboard marks the run stale; nothing is undone |
| Cleanup | never automatic; `cleanup.py --plan` lists worktrees and branches of done, already-merged issues; `--yes` executes exactly that plan |

## 13. Harness support

Support is declared per harness in `capabilities/<harness>.json` — `hooks`, `structured_output`, `worktree_isolation`, `per_role_model`, `parallel_round`, `skills_path` — and grouped in three tiers. A tier is announced only after the fixture runs the full loop in it.

| Tier | Harness | How the loop runs |
|---|---|---|
| Reference | Claude Code | `Workflow` tool from the templates' inline scripts; native `schema`; `isolation: 'worktree'`; guard hooks via `settings.json` |
| Supported | Codex CLI | Hybrid process runner (`codex exec`) with ADR-0006 cross-harness dispatch; per-role model selection; independent Critic verification; defense-in-depth git hooks |
| Supported | OpenCode | skills read natively from `.agents/skills`; subagents with `model` per role; hooks through a generated plugin; `result.py` mandatory; rounds parallel when the primary agent can, else sequential |

`fixture/` is a minimal repository with one spec, a few issues and real gates, used to exercise every tier with real agents. Acceptance for v1:

1. The fixture runs to a draft run pull request in each announced tier, and the report states the tier.
2. A refuted issue ends `blocked` with the critic's evidence and its worktree preserved; the roadmap stays unticked.
3. `roadmap.py check` reports drift when a checkbox is ticked by hand; where hooks are enabled, the edit is denied.
4. A differential check blocks a delivery that adds a finding and passes one that only carries preexisting findings.
5. `spec.py` refuses a spec missing a required section of the effective template and accepts one using a mapped equivalent heading.
6. `budget.py` refutes an issue whose initial package exceeds 15% of the chosen model's window, with the number.
7. `result.py` rejects a result missing a required field and the orchestrator asks once, then fails the phase.
8. The dashboard shows two concurrent runs from two repositories with their phases, and shows a stale run.
9. Rerunning a scope after an interrupted round offers to continue the in-flight issue in its worktree.
10. The Learner produces a candidate only for a refutation that recurred, and nothing is written to `AGENTS.md` without the operator.

## 14. From `asdlc` to Gantry

The migration of the `asdlc` skill (in this repository) is the first spec of this repository and is executed by `asdlc` itself: rename and split into the three skills, remove repository-specific hardcoding (`slice-index`, this repository's name) in favour of the repository policy, add the new scripts and schemas, port the structural spec check, add the Requirement Critic and Learner phases to the templates, write the capability files and hook wiring, and build the fixture. Each step is a vertical slice demonstrable on the fixture.
