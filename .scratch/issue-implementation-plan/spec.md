# Spec: Ground implementation in a short per-Issue technical plan

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 20)
Source: Operator-approved design from the 2026-10-06 grilling conversation
Created: 2026-10-06
Planning: Behavior confirmed; testing seams and four-Issue breakdown approved for publication by the operator PR request on 2026-10-06

## Blueprint

### Context

Gantry's existing Plan prepares a Spec and decomposes it into Issues. An already planned Spec enters the round workflow directly. The Implementer reads the Issue, Spec and standing decisions, but no explicit source investigation or validated technical plan must precede edits. The operator wants a short Research-and-Plan checkpoint to constrain implementation choices against actual code, without adding routine human approval or serializing independent Issues.

The MyShopList Run prompted this proposal; its existence is not evidence that a particular implementation failed or that the proposed checkpoint saves tokens. This Spec changes future authorized execution, not a Run already executing elsewhere.

### Architecture

Keep the Host Harness as coordinator and deterministic scripts as workflow authorities. Add one bounded, read-only technical-planning call inside each Issue's execution chain after its worktree is assigned and before its first implementation call. Research and planning share this call. The technical planner inherits the effective Implement selection's harness and model, including Run and Issue overrides; it does not inherit the existing decomposition Plan model or Result Contract.

A separate validated technical-plan Result Contract records source findings, criterion coverage, proposed changes, tests, conflicts and input identity. The next fresh Implementer receives that compact result and starts TDD only after the checkpoint accepts it. Independent Review and Critic remain mandatory.

### Constraints

- Technical planning must not change code, approved Issue/Spec content, roadmap state or acceptance criteria.
- Target approximately 500–1,000 tokens of useful plan content; do not pad short plans or truncate required evidence to meet a cosmetic length target.
- Preserve repository language rules, authorization boundaries, correction budgets, worktree isolation and serial integration.
- Planning failure is distinct from a Critic refutation and does not consume a correction attempt.
- Requested and observed execution identity remain distinct; unsupported or unknown capabilities must not be invented.

## Problem Statement

As an operator, I want an Implementer to compare approved requirements with the current source before editing. Reading the Spec alone can leave an agent choosing the wrong extension point, duplicating existing behavior, overlooking tests or discovering contract conflicts only during Review or Critic correction. A short plan should expose these mistakes earlier and provide a focused handoff to implementation. Its added cost must be measured rather than assumed to be offset by fewer corrections.

## Solution

For every Issue entering implementation, first produce a compact technical plan grounded in the exact assigned checkout. Identify current behavior, the gap to every acceptance criterion, reusable components, proposed changes, verification and unresolved conflicts. Release implementation automatically when the result is valid and within approved scope. Otherwise preserve the Issue and return an actionable failure or operator decision.

Use the selected Implement model for both calls. Request high reasoning for technical planning when that exact selection supports it. Under the accepted effort policy, select the greatest supported effort no higher than high when high is unavailable, or the model default when effort is not configurable. Keep the implementation call's original configured effort. Reuse the plan during corrections and resumption after checking freshness; revise only affected parts when relevant inputs change.

## User Stories

1. As an operator, I want code investigation before edits, so that implementation reflects the repository's actual state.
2. As an operator, I want this checkpoint for every executable Issue, so that existing Spec approval does not bypass technical planning.
3. As an Implementer, I want cited current behavior and reusable components, so that I avoid invented extension points and duplicate code.
4. As an Implementer, I want every acceptance criterion mapped to changes and tests, so that no required behavior is forgotten.
5. As an operator, I want contract and scope conflicts surfaced before edits, so that approved behavior remains authoritative.
6. As an operator, I want incomplete or invalid plans to block implementation, so that prose claims cannot bypass the checkpoint.
7. As an operator, I want valid plans to advance automatically, so that routine implementation does not wait for another approval.
8. As an operator, I want technical planning to use the effective Implement harness and model, so that my model selection is preserved.
9. As an operator, I want high reasoning only for technical planning, so that implementation keeps its configured effort.
10. As an operator, I want supported effort negotiation reported honestly, so that an unavailable high setting does not trigger a silent model substitution.
11. As an operator, I want research and planning combined into one short call, so that repeated exploration does not dominate execution cost.
12. As an operator, I want independent Issues to plan and implement concurrently, so that one Issue does not create a round-wide planning barrier.
13. As an operator, I want plans retained through interruption, so that resumption does not repeat valid completed research.
14. As an operator, I want stale plans rejected when relevant inputs change, so that implementation is not guided by obsolete code or criteria.
15. As an Implementer, I want correction passes to reuse valid findings and update affected parts, so that every review fix does not restart research.
16. As an operator, I want scope-neutral implementation adjustments recorded, so that a useful plan does not become a rigid replacement for TDD.
17. As an operator, I want planning protocol and execution failures distinguished from refutations, so that correction budgets remain trustworthy.
18. As an operator, I want planning and implementation visible as separate phases, so that I can attribute elapsed time and available usage.
19. As an operator, I want total token usage and Review/Critic correction counts reported with provenance, so that I can evaluate the net cost.
20. As an operator, I want unknown usage shown as unknown and no unsupported savings claim, so that comparisons remain honest.
21. As a Host Harness integrator, I want the same checkpoint and contracts on supported native and manual paths, so that execution semantics stay portable.
22. As an operator, I want independent Review, Critic, gates and roadmap authority preserved, so that a valid plan is not mistaken for a completed delivery.

## Implementation Decisions

- Name the checkpoint Technical Plan to distinguish it from Spec/Issue decomposition Plan. It is an execution prerequisite, not a new Spec approval or a replacement for the existing Plan Critic.
- Resolve its selection from the effective Implement role after existing profile, Run and Issue overrides. Do not persist the temporary planning-effort override into operator profiles or repository defaults.
- Use a dedicated structured result and existing result validation/dispatch boundaries. A decomposition planner result is not a valid technical plan.
- Record plan identity, source revision, Issue and Spec identity, relevant source findings, criterion-to-change/test coverage, proposed changes, reusable behavior, scope-neutral choices and blocking questions. Include applicable standing decisions in freshness checks.
- Check source references against the assigned checkout and verify complete criterion coverage deterministically. Semantic conflict detection remains agent work; structural validity alone cannot establish semantic correctness.
- The planning call inspects source without editing it. Detect unexpected checkout changes and refuse the handoff; use supported read-only execution capabilities without claiming universal filesystem enforcement.
- Missing/invalid results use existing bounded Protocol Failure handling. Execution failures preserve work and require existing explicit recovery; they never cause automatic model/harness fallback.
- Accepting a valid plan releases the separate implementation call automatically. An explicit conflict stops affected work for an operator decision before any change to behavior, contracts, dependencies or decomposition.
- Scope-neutral implementation adjustments are permitted and reported with a reason. Issue acceptance criteria remain authoritative over the plan.
- Retain technical-plan results as machine-local execution artifacts, separate from sanitized observational Run events. Do not put plan bodies, source excerpts, prompts or secrets in the Run log.
- Bind reuse to the same Issue/worktree and relevant content. A changed HEAD triggers freshness evaluation rather than blindly discarding research after the Implementer's own commits. Input changes affecting findings require targeted replanning; changes to approved scope still require operator approval.
- Each Issue progresses independently from its own checkpoint into TDD. Technical planning is not unconditionally repeated inside every review-fix or correction invocation.
- Record separate phase intervals and available provider usage with provenance. Report unavailable measurements explicitly; avoid counting reused results twice. Review fix passes and Critic correction attempts are separate counts.
- Keep the first delivery end-to-end. Any routing prefactoring belongs inside that slice and must preserve existing execution behavior through the same public workflow seam.

## Testing Decisions

- Primary seam: execute the canonical per-Issue round workflow with controlled role responses and real temporary repositories. Assert observable ordering, refusal to invoke implementation, operator handoff, worktree isolation and preserved independent verification; avoid testing prompt wording as proof of enforcement.
- Supporting seam: public role dispatch and result validation with controlled harness executables. Assert actual invocation identity/effort, supported effort handling, contract rejection and Protocol Failure behavior without depending on developer credentials.
- Recovery and observation are exercised through public Run queries/reports and the same workflow driver, not a new private test API. Real temporary Git histories distinguish self-authored changes, relevant external changes and unrelated changes.
- Existing lifecycle, role dispatch, result continuation and Run-log fixtures provide prior art. Extend those seams rather than creating a parallel harness simulator that bypasses the production entry path.
- Test a one-Issue happy path and multi-Issue interleaving, incomplete criterion coverage, fabricated source references, reported conflicts, missing results, read-only violations, unsupported effort, recovery, targeted replanning and missing usage.
- A live adapter compatibility probe may supplement implementation verification where supported; CI uses controlled executables and does not require a logged-in developer harness.
- No frontend behavior is proposed. Any later Dashboard UI change would require its own approved scope and Playwright evidence.

## Contract

### Definition of Done

- [ ] Every first implementation call is preceded by an accepted Technical Plan tied to its assigned Issue checkout.
- [ ] Plans cite actual source, cover all criteria and identify proposed changes, verification and conflicts within the compact target.
- [ ] Invalid, missing, incomplete, stale or conflicting results cannot release affected implementation.
- [ ] Planning inherits effective Implement harness/model, uses the accepted high-effort policy and preserves the implementation effort.
- [ ] Valid plans advance automatically while independent Issues remain independently schedulable.
- [ ] Corrections and resumption reuse valid plans; relevant changes trigger focused revalidation or replanning.
- [ ] Reports attribute separate phase duration, available tokens and correction counts without invented savings or double counting.
- [ ] Native and manual execution instructions preserve the same contracts and failure behavior, with real capability limitations stated.
- [ ] Existing Review, Critic, gates, correction ceilings and roadmap completion authority remain unchanged and independently exercised.

### Regression Guardrails

- Spec/Issue decomposition Plan and its approval transition remain separate.
- No automatic model/harness fallback, default-policy mutation or silent scope amendment.
- A valid Technical Plan never establishes delivery completion or authorizes PR creation, merge, release or cleanup.
- Planning failures do not spend the Critic correction budget or overwrite preserved work.
- Run logs remain sanitized, machine-local and observational; retained artifacts never replace authoritative Issue status.

### Scenarios

```gherkin
Scenario: A grounded technical plan releases TDD automatically
  Given an executable Issue and its assigned clean checkout
  When technical planning returns valid source findings and coverage for every criterion
  Then a separate Implementer receives the compact plan and begins TDD without routine operator approval

Scenario: Incomplete coverage blocks edits
  Given a technical plan omitting an Issue acceptance criterion
  When the Host validates the result
  Then implementation is not invoked and the existing Protocol Failure path reports the defect

Scenario: A contract conflict needs an operator decision
  Given source behavior contradicts an approved Spec contract
  When technical planning reports the conflict
  Then affected implementation waits for the operator without editing the Spec or code

Scenario: Planning effort does not alter implementation effort
  Given an effective Implement selection configured with medium effort and supporting high
  When its Technical Plan and implementation calls execute
  Then planning requests high and implementation requests medium using the same harness and model

Scenario: Unsupported high uses the accepted effort policy
  Given the selected model supports low and medium but not high
  When the Technical Plan selection is resolved
  Then medium is selected and reported without changing the model or saved defaults

Scenario: Independent Issues do not share a planning barrier
  Given two ready Issues assigned separate worktrees
  When one plan succeeds while the other is awaiting a result
  Then the first Issue can begin implementation while the second remains in technical planning

Scenario: Correction and recovery reuse valid findings
  Given a retained plan and implementation commits in the same Issue worktree
  When correction or resumption confirms the relevant inputs remain valid
  Then the plan is reused without repeating its full research or resetting correction counts

Scenario: Relevant input changes require focused replanning
  Given a retained plan whose cited source contract changed
  When implementation would resume
  Then the affected findings and coverage are revalidated and updated before affected work starts

Scenario: Missing token measurements remain unknown
  Given completed planning and implementation calls with no provider token usage
  When the Run report is produced
  Then duration and correction counts are reported with unknown token usage and no savings claim
```

## Out of Scope

- Redesigning Spec/Issue decomposition or proving historical planning approval provenance.
- Changing the active MyShopList Run, its configuration, processes or source files.
- Requiring human approval for every valid technical plan or adding an independent Plan Critic call per Issue.
- Separate Research and Plan calls, a new execution engine, or mandatory round-wide research.
- Changing delivery gates, correction ceilings, implementation model selections or completion authority.
- Dashboard UI changes, automatic publication, merging, release, cleanup or injected lessons.
- Promising lower total tokens, duration or correction counts before comparable evidence exists.

## Further Notes

The operator approved the behavioral design in conversation. Publication of the primary workflow seam, supporting dispatch seam and four slices was authorized by the subsequent operator request for a PR to main. The planning PR adds no implementation authorization. Documentation follows Gantry's English artifact convention; consumed repository content retains its own language policy.

## Changelog

- 2026-10-06 — Synthesized the confirmed design; testing seams and four vertical slices approved for publication with the planning PR.
