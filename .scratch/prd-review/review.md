# Gantry v4 PRD consistency review

Status: reviewed
Date: 2026-09-11

## Outcome

The PRD now distinguishes agreed product policy from unimplemented contracts. The approved decisions remain in scope. No implementation, live provider change, or release was performed.

## Corrections made

| Previous inconsistency | Consolidated treatment |
|---|---|
| Introductory diagrams still promised a hard 40% ceiling and recovered reasoning quality | Context thresholds are operating policies; guarantees depend on demonstrated adapter capabilities |
| Main workflow omitted human plan approval and the entropy decision | Workflow now includes approved planning, verification, entropy comparison, both Git modes, and reconciliation |
| Handoff unconditionally killed a process | Agent stop/handoff uses supported capabilities and ownership reconciliation |
| Host environment/process identity was equated with native subagent control | Discovery metadata must be validated; it cannot grant unavailable APIs or override an execution snapshot |
| Version 4.0 requirements mixed with a v4.1 adapter label and claims of existing UI | One v4 document describing planned behavior, with explicit implementation status |
| A builder-shaped JSON sample was presented as the universal GTP schema | Shared identities and role-specific inputs/results are described as contracts; exact schemas remain design work |
| Single result path conflicted with immutable corrected submissions | Submission identities, receipts and persistence are specified together in the GTP design backlog |
| Governance was permanently read-only even when approved work changed the baseline | Ordinary assignments protect mapped paths; approved baseline transitions have an explicit evaluation/adoption path |
| New baseline immediately applied to all PBIs despite frozen in-flight snapshots | New executions use the adopted baseline; existing executions require explicit snapshot migration |
| Tool readiness could reject all historical findings | Tool execution/evidence validity is separated from differential debt and absolute gate failures |
| Passing feature tests and removing merge markers implied completion | Role completion, gate approval and integration authorization remain distinct |
| Security/architecture tables implied universal semantic or vulnerability detection | Configured checks declare actual coverage; entropy consolidates evidence and LLM review adds findings |
| All LLM reviewers appeared optional | The Requirement Critic remains part of spec preparation; the delivery adversarial reviewer is optional and required once enabled |
| SSH authentication appeared sufficient for PR API operations | Git transport authentication is distinguished from GitHub API credentials |
| Cleanup still happened automatically in the runbook | Integration and learning proposals preserve artifacts; cleanup remains separately approved |
| Minimal-retention policy contradicted full persisted prompt examples | Dispatch content is distinguished from its retained audit representation and replayable references |
| Sample DDL lacked repository identity, approvals, operations and required states | Removed executable-looking obsolete DDL; replaced with required record families and a schema-design obligation |
| Cancelling and resuming appeared to retain stale ownership | Resumption reconciles and reacquires current ownership, retaining budgets and approved rule versions |
| Onboarding requirements repeated across sections | §6.3 owns readiness and preparation; §7.1 references it and describes demo/presets |
| README retained strict context and broad support claims | README now matches the planned product and Codex/OpenCode validation targets |

## Remaining product scope choices

One validation item remains, also listed in PRD §14.1:

1. Windows support. TypeScript/Node.js is the Gantry runtime; initial repository adapters target TypeScript/JavaScript and Python with the approved package-manager/tool matrix; Git integration is local Git or GitHub Pull Requests, and GitHub.com and GitHub Enterprise use the `gh` workflow. Windows remains expected but unverified.

No new decision is needed for the already agreed worktrees, budgets, retry policy, review gates, plan approvals, dashboard Settings, or existing-repository conventions.

## Technical work, not another policy interview

PRD §14.2 groups implementation contracts for the shared operations/state machine, GTP payloads, persistence, harness integrations, human approval provenance, dashboard token bootstrap, check adapters, Git operations, context/retention, and recovery. §14.3 supplies the cross-cutting acceptance scenarios.

Important feasibility boundaries to verify during design:

- Native harness activity can bypass Gantry APIs. Gantry can enforce its accepted operations and report integration limitations; it cannot claim OS-level isolation without an enforcement mechanism.
- The ephemeral dashboard token must have a concrete delivery and scope design, including global Settings changes, while respecting the approved no-persistent-token rule.
- An agent's report of operator approval is insufficient. The operation design must define a verifiable operator action without adding another approval stage for the same reviewed proposal.
- Minimal retained evidence still needs replayable versioned context for handoffs and resumption. Test missing references, redaction failures and historical rule loading.
- GitHub target changes and results on different revisions must be reconciled by the provider adapter; a local mutex is not a distributed merge guarantee.

## Validation

Reviewed PRD, README, glossary and both ADRs. Checked that named policy blocks survived consolidation, section references resolve, Markdown fences are balanced, and local Markdown links resolve. The old schema and sample routing configuration were removed instead of being presented as validated implementations. No runtime tests apply to this documentation-only review; Windows and adapter integration claims remain pending actual acceptance tests.
