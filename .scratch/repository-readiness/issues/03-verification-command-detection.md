# Verification command detection and approval proposals

Type: issue
Status: ready-for-agent
Slice: repository-readiness#03
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

Detect the repository's package manager and present tooling by reading manifests, lockfiles and configuration files: npm, pnpm or yarn with TypeScript, ESLint with typescript-eslint, Vitest and dependency-cruiser; uv or pip with Ruff, pytest, Import Linter and pip-audit; plus Gitleaks and license checks where configured.

Turn each detection into an `ApprovedCommandProposal` carrying argv (never a shell string, so approval describes exactly what executes with no shell interpretation in between), working directory, environment variable *names* only, declared effects, expected report format and location, `declaredCoverage`, Check Resource declarations and a Check Stability criterion. Each proposal becomes a `verification` report item with status `needs_approval`.

The same read-only detection pass also produces a secret scanner rule source reference alongside the `ApprovedCommandProposal`: the detected scanner's identity plus the resolved location of its rule configuration. The proposal is a command to run; the reference is the rule set itself, and `data-handling#02` consumes it as its third redaction detector source, so redaction agrees with the scanner the repository already trusts.

Detection reads; it does not run the tools. A repository missing a required check produces a `missing` item that points at the preparation proposal in `repository-readiness#05` rather than inventing one here.

## Acceptance criteria

- [ ] A fixture for each supported package manager yields a proposed command that is correct for that manager, asserted on argv rather than a rendered string.
- [ ] Proposals carry environment variable names and no values anywhere in the persisted record.
- [ ] `declaredCoverage` is required: a proposal constructed without it is rejected at the boundary.
- [ ] No detected command executes during detection, proven by a check-adapter fake that fails the test if invoked.
- [ ] Every proposal appears as a `verification` item with `needs_approval` and `afkEligible` is false while any required check is unapproved.
- [ ] A fixture repository with a configured secret scanner yields a rule source reference naming the scanner and the resolved location of its rule configuration, distinct from the `ApprovedCommandProposal` for running it; a fixture with no scanner configured yields no reference and no error.

## Blocked by

- `repository-readiness#01` — the readiness report skeleton, the producer registry keyed by category, and the temporary-repository fixture builder the per-package-manager fixtures extend.
