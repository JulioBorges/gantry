# Provider conformance suite and support matrix rows

Type: issue
Status: ready-for-agent
Slice: git-integration#09
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

Build the provider conformance suite as a separate test layer that runs the real provider implementation — not the scripted fake — against real providers: GitHub.com and, where reachable, GitHub Enterprise. It exercises the provider operations this spec defines: identity and scope inspection, protection observation, Pull Request creation, update, observation and merge, and mutation reconciliation against authoritative provider state. Its output is the support matrix as data, one row per exercised combination carrying the provider target, the observed capabilities and the limitations found.

This suite runs outside the pull-request required checks, and that is by design: it needs credentials and a live repository, so in most environments it records skips. A skipped run records an explicit reason and produces an unsupported status; a skipped operation means an unestablished capability, never an inherited or assumed one. A limitation observed against one provider target establishes nothing about another, and the matrix says so per row rather than in aggregate. The definition of done for this slice is that the suite runs and the matrix is correct, including in the case where everything skips — not that all rows pass.

The row shape is the one the cross-harness conformance suite already produces, because the release pipeline publishes both matrices through a single row schema. Follow that schema rather than inventing a provider-specific variant.

## Acceptance criteria

- [ ] The suite runs the provider operations — identity and scope inspection, protection observation, Pull Request creation, update, observation and merge, and mutation reconciliation — against a real provider, and records one support matrix row per exercised combination with the provider target, observed capabilities and limitations.
- [ ] Absent, insufficient or expired credentials produce a skipped row carrying an explicit recorded reason and an unsupported status; a test asserts a skipped row is never rendered as supported and never inherits another row's result.
- [ ] The suite is not a pull-request required check; the pull-request workflow completes green in an environment with no provider credentials at all.
- [ ] The emitted rows validate against the same row schema the cross-harness conformance suite produces and the release pipeline publishes; a schema change on either side fails this suite rather than silently producing an unpublishable row.
- [ ] A limitation discovered against GitHub Enterprise — an operation unavailable, restricted, or behaving differently from GitHub.com — is recorded as a limitation on that row rather than suppressed, and it leaves the GitHub.com row unchanged.
- [ ] A run against a real provider uses the real implementation; a test asserts the scripted fake is not reachable from this suite, so a green matrix can never be produced by the fake.

## Blocked by

- `git-integration#05` — provides the provider interface, Provider Identity resolution and the credential mechanisms the suite exercises for real.
- `git-integration#06` — provides the protection observation the suite exercises and the observed protection record it reports.
- `git-integration#07` — provides Pull Request preparation, observation and merge, and the provider-side mutation reconciliation the suite exercises.
- `harness-adapters#07` — provides the support matrix row schema and the skip-is-not-support rule this suite must match; `release-engineering#06` publishes both matrices through it and is a downstream consumer, not a blocker here.
