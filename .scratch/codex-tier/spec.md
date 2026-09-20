# Spec: Supported Codex harness tier

Type: spec
Status: done
Map: `ROADMAP.md` (spec 08)
Source: Operator-approved grilling decisions, 2026-09-20; PRD.md; CONTEXT.md; ADR-0004; ADR-0006
Created: 2026-09-20

## Blueprint

### Context

Gantry is a harness-neutral agentic SDLC skill pack. Initially, Codex CLI was classified in the Compatible tier with manual prompt chaining and no native hooks. With cross-harness role execution (ADR-0006) proven via `codex exec`, Codex can serve both as an execution harness and as a host harness.

However, Codex support is not yet formal across all lifecycle stages and documentation:
- Capability definitions in `.agents/skills/gantry/capabilities/codex.json` remain at `"tier": "compatible"`.
- Setup wizard (`scripts/setup.py`) lacks automatic Codex detection, login verification, and policy configuration.
- Reference workflows (`reference/plan-workflow.md`, `reference/round-workflow.md`) lack formal documentation for Codex host orchestration.
- PRD, README, and documentation contain discrepancies across Compatible and Supported designations.

This feature formalizes Codex at the Supported tier across all lifecycle steps and documentation, with implementation scheduled after current open specs (`interactive-dashboard`, `dashboard-lifecycle`, and `gantry-plan`) complete.

### Architecture

- **Supported Tier Capabilities**: Update `capabilities/codex.json` to `"tier": "supported"`. Formalize runtime discovery and model context windows in `scripts/discovery.py` (`codex models`, `codex --version`).
- **Setup Wizard & Policy**: Update `scripts/setup.py` to detect Codex environments (CLI on PATH, `.codex`), guide operator authentication (`codex login`), configure `execution.hostHarness: "codex"` in `.gantry/config.json`, and inject explicit policy instructions into `AGENTS.md`.
- **Hybrid Orchestration Workflow**: Codex as Host Harness coordinates runs by reading root `AGENTS.md` and invoking sub-tasks and role agents (Implementer, Reviewer, Critic) via bounded `codex exec` commands (or external harnesses via ADR-0006 cross-harness dispatch).
- **Defense in Depth**: In the absence of native Codex hook events, guardrail enforcement combines explicit `AGENTS.md` invariants, local git hooks (protecting branches and ROADMAP.md), and adversarial verification by an independent Critic.
- **Unified Documentation & Site**: Update `PRD.md`, `README.md`, `docs/role-execution.md`, and the Astro site harness matrix with synchronized EN/PT-BR translations.

### Constraints

- Bounded execution only: `codex exec` calls must obey timeout and error-capture contracts defined in `execution.py`.
- No global environment mutation: Gantry runs no package managers or global agent installers; it guides the operator to authenticate and verify locally.
- Invariant preservation: ROADMAP.md, issue statuses, and acceptance criteria checkboxes must never be modified by automated agents without `roadmap.py done`.
- Clean DAG scheduling: Implementation is blocked by terminal issues of currently open specs (`dashboard-lifecycle#03`, `gantry-plan#04`, and `interactive-dashboard#05`).

## Contract

### Definition of Done

- [ ] Codex capability declaration in `capabilities/codex.json` is updated to `"tier": "supported"` with verified model context windows.
- [ ] Runtime discovery in `discovery.py` validates `codex` CLI availability, version detection, and model listing without regression to other harnesses.
- [ ] Setup wizard in `setup.py` detects Codex, guides authentication, writes host and role configuration to `.gantry/config.json`, and injects Gantry policy into `AGENTS.md`.
- [ ] Reference workflows document Codex host orchestration and hybrid role dispatch via `codex exec` and cross-harness processes.
- [ ] Defense-in-depth guardrails ensure git hooks and independent Critic verification protect branch integrity, ROADMAP.md, and test suites.
- [ ] Test suites verify capability loading, setup configuration, command dispatch, and error handling for missing/unauthenticated Codex CLI.
- [ ] `PRD.md`, `README.md`, `docs/role-execution.md`, Astro site matrix, and translations consistently represent Codex as Supported tier.
- [ ] Playwright tests on the website pass without visual, functional, or accessibility regressions.

### Regression Guardrails

- Existing Claude Code, OpenCode, and Antigravity execution, discovery, and hook pathways remain unaffected.
- ADR-0004 skill-pack architecture and ADR-0006 cross-harness role dispatch contracts remain intact.
- Deterministic gating via `gates.py`, `spec.py`, and `result.py` remains authoritative over model outputs.
- `ROADMAP.md` and `frontier.py` DAG constraints remain cycle-free and fully verifiable.

### Scenarios

```gherkin
Scenario: Runtime discovery detects Codex CLI
  Given a system with Codex CLI installed and on PATH
  When runtime discovery runs for harness "codex"
  Then discovery reports installed status with valid version and model list
  And preflight validation succeeds

Scenario: Setup wizard configures repository for Codex
  Given an unconfigured repository and Codex detected in the environment
  When the operator runs setup and selects Codex as the host harness
  Then .gantry/config.json records Codex under execution policy
  And AGENTS.md receives the Gantry policy block with Codex orchestration guidance
  And existing unrelated configuration is preserved

Scenario: Codex host executes role via hybrid dispatch
  Given a Gantry run hosted by Codex
  When a phase invokes an Implementer or Critic role
  Then execution builds a bounded command using codex exec or configured cross-harness
  And role results are validated against result.py contracts before integration

Scenario: Adversarial Critic catches prompt rule violation
  Given a Codex-hosted run where an agent attempts an unauthorized status or roadmap edit
  When the Critic evaluates the delivered changes
  Then the verification fails visibly with refutation evidence
  And the run is halted before merge or milestone progression
```

## Out of Scope

- Implementing an external server or background daemon specifically for Codex.
- Mocking or bypassing authentication credentials during live runs.
- Modifying upstream OpenAI Codex binary behavior or CLI argument parsing.
- Dynamic native subagent model switching within a single interactive Codex CLI session (handled via bounded subprocess dispatch).

## Changelog

- 2026-09-20 — Operator approved the Spec and four-slice breakdown for full Supported Codex tier. Implementation scheduled after open specs finish.
