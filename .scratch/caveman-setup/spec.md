# Spec: Optional environment-installed Caveman skill

Type: spec
Status: approved
Map: `ROADMAP.md` (spec 11)
Source: Operator-approved grilling decisions, 2026-09-15; PRD.md; CONTEXT.md; ADR-0004
Created: 2026-09-15

## Blueprint

### Context

Gantry Runs consume substantial tokens. The operator wants an optional way to reduce agent verbosity without changing verification or the detail of delivered artifacts. Caveman provides an external skill with a `lite` mode. Its repository is https://github.com/JuliusBrussee/caveman.

Gantry remains a harness-neutral skill pack. Caveman is installed by the user in their own agent environment, rather than copied into Gantry. Shorter prose is an optimization; token savings depend on the workload and are not guaranteed.

### Architecture

- `gantry-setup` presents one recommended choice: use Caveman `lite` for agent messages and summaries in this repository. Explain the scope, external installation, normal-behavior fallback and variable savings. Explicit confirmation is required; declining or skipping leaves the feature disabled in a new policy. Existing confirmed preferences are preserved unless the operator changes them.
- Save the preference in the sparse tracked Repository Policy through the existing `setup.py` writer. An absent preference resolves to disabled. Store only the repository preference, never a machine-specific installation path or availability result.
- When installation is needed, show the upstream skill-only installation command appropriate to the user's harness (for Claude Code: `npx skills add caveman` or directory clone; for Antigravity: clone into `~/.gemini/config/skills/caveman` or `.agents/skills/caveman`). The user runs it themselves. After the user reports installation, verify that the host harness can discover and read the Caveman skill. A successful installation claim or package-manager exit code alone does not prove availability.
- Resolve the preference and actual availability during Run preflight. Availability means the current host harness can discover and load the external skill. Do not assume one fixed directory, scan unrelated user files, or infer availability from the repository preference.
- Apply the available external skill in `lite` mode to the coordinating agent and every agent role invoked by the workflow: Requirement Critic, research, Planner, Plan Critic, Implementer, Reviewer, Critic and optional Learner. Each fresh agent must receive the instruction and access to the external skill through the host harness's supported mechanism; parent activation alone is insufficient evidence of propagation.
- The scope is conversational messages and agent summaries. Specs, Issues, documentation, lesson candidates, PR descriptions and persisted role results retain the detail necessary for implementation and review. Code, commands, exact errors, JSON contracts, evidence references and acceptance criteria retain their required content. Gantry's workflow and Result Contracts take precedence over conflicting style instructions.
- If discovery, loading or role activation cannot be supported reliably, use normal behavior for the affected execution and give one warning per Run with installation or activation guidance. Never block delivery solely because this optional skill is unavailable. Never claim activation where it could not be established.
- The implementation must define a single policy field and propagate the resolved setting consistently through the portable runtime and both reference workflows. The field name and harness-specific discovery mechanisms are implementation choices; their behavior must satisfy this Spec.

### Constraints

- Offer the option during setup as recommended, with explicit opt-in; do not silently enable it for existing repositories.
- Use only Caveman `lite` in this feature. Keep the external skill outside the Gantry pack and operated repository structure.
- Display installation guidance only; Gantry runs no installer, downloads no Caveman copy and changes no global agent configuration.
- Keep availability local to the current environment and re-evaluate it for each Run.
- Preserve the same deterministic readiness, verification, correction-budget, integration and completion rules with the option enabled or disabled.
- All generated policy and artifacts remain English; conversation follows the operator's language.
- Report measured savings only when actual comparable usage evidence exists. This feature needs no new token measurement subsystem.

## Contract

### Definition of Done

- [ ] Setup presents the recommended option, scope and trade-offs, and persists only an explicitly confirmed repository preference through the existing writer.
- [ ] Missing policy and absent preference resolve to disabled; repeated setup preserves unrelated policy and existing preferences unless explicitly changed.
- [ ] Setup shows verified upstream skill-only installation guidance and verifies host-harness availability after the user reports installation.
- [ ] Every invoked workflow role and the coordinating agent receives the available external skill in `lite` mode for conversational messages and summaries.
- [ ] Missing or unsupported skill activation produces normal behavior and at most one warning per Run, with actionable guidance and no false activation claim.
- [ ] Artifact content, Result Contract requirements and full verification evidence remain intact with the feature enabled.
- [ ] Fixture coverage exercises preference resolution, setup persistence, availability fallback, fresh-agent propagation in planning and rounds, and artifact preservation without requiring a global Caveman installation or a paid model call.
- [ ] User-facing documentation explains opt-in, user-managed installation, fallback and variable savings without asserting universal harness support or a savings percentage.

### Regression Guardrails

- Scripts remain the authority on readiness and completion; style never changes an approval or verdict.
- Requirement Review and planning continue to stop at the existing operator approval boundaries.
- Verification, acceptance criteria, correction budgets and serial integration gates remain unchanged.
- Caveman absence cannot introduce a new blocking prerequisite.
- Existing repository policy, templates and unrelated working-tree changes are preserved.
- A mocked fixture proves propagation contracts and fallback logic, not live model behavior, actual token savings or external integration quality.

### Scenarios

```gherkin
Scenario: Recommended option requires explicit confirmation
  Given a repository without a Caveman preference
  When the operator declines or skips the recommended setup option
  Then the effective preference remains disabled
  And no installation or agent activation takes place

Scenario: User installs the external skill
  Given the operator confirms the Caveman lite option
  And the host harness cannot discover the skill
  When setup presents the skill-only installation command
  Then the user executes installation in their own environment
  And Gantry executes no installer

Scenario: Setup verifies reported installation
  Given the operator enabled the option and installed the skill themselves
  When the user reports installation
  Then setup checks whether the host harness can discover and read the skill
  And reports the observed availability without promising token savings

Scenario: Available skill reaches fresh agents
  Given the repository preference is enabled
  And the host harness can discover and load Caveman
  When a Run invokes planning or implementation roles
  Then each fresh invoked role receives the external skill in lite mode
  And the coordinating agent uses the same conversational scope
  And generated artifacts and persisted role results retain all required detail

Scenario: Environment changes after setup
  Given the repository preference is enabled
  And Caveman was available during setup
  But the current host harness cannot load or propagate the skill
  When a Run starts
  Then affected agents use normal behavior
  And the Run continues under its existing rules
  And the operator receives one warning with actionable guidance
  And later rounds do not repeat that warning

Scenario: Existing configuration remains stable
  Given a repository with an enabled Caveman preference and unrelated policy settings
  When setup is repeated without changing that preference
  Then the preference and unrelated settings are preserved

Scenario: Operator disables the preference
  Given a repository with an enabled Caveman preference
  When the operator explicitly disables the option through setup
  Then subsequent Runs use normal behavior

Scenario: Style conflicts with evidence requirements
  Given Caveman lite is active for agent messages
  When a role delivers a review or a Critic result
  Then every required contract field and acceptance-evidence reference is retained
  And exact errors and commands remain intact
  And validation and operator approval rules remain unchanged
```

## Out of Scope

- Caveman proxy, runtime wrapper, output compression and provider routing.
- Bundling, vendoring, automatic installation or global agent configuration changes.
- Compressing Specs, Issues, documentation, PR descriptions, lesson candidates or persisted Result Contracts.
- Additional Caveman modes, per-role intensity settings and new Run override flags.
- A token analytics subsystem, benchmark suite or promised savings percentage.
- Issue decomposition, roadmap additions and implementation approval; this draft is prepared for operator review first.

## Changelog

- 2026-09-16 — Clarified Antigravity host-harness skill discovery and installation paths (`~/.gemini/config/skills/caveman` and `.agents/skills/caveman`).
- 2026-09-15 — Operator approved the Spec and three-slice breakdown: setup/coordinator, planning agents and round agents. Implementation Issues published separately; implementation has not started.
- 2026-09-15 — Initial draft from the confirmed grilling scope; implementation has not started.
