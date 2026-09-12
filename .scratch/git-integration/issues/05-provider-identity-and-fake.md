# Provider Identity, the provider interface, and the scripted provider fake

Type: issue
Status: ready-for-agent
Slice: git-integration#05
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

The GitHub provider interface — identity and access inspection, protection observation, Pull Request creation, update, observation and merge — as the single seam all provider behavior sits behind, plus a scriptable fake implementing it that can return protection variants, check and review states, mergeability, lost responses and externally changed state.

Authentication uses what the environment already has: an authenticated `gh` installation or a token referenced by an approved environment variable for API operations, and existing SSH or HTTPS credentials for Git transport. These are distinct, and transport access proves nothing about API authorization.

The resolved `ProviderIdentity` — login, mechanism, variable *name* only, observed scopes, repository access — is shown and approved before the first mutating provider operation. No credential value is ever written to configuration, the database, envelopes, projections, or repository artifacts.

## Acceptance criteria

- [ ] The first mutating provider operation is rejected until the identity has been approved; the approval records the observed scopes and repository access.
- [ ] A unit with working SSH transport but no API authorization is rejected with a typed code on an API operation, and the rejection names API authorization rather than transport.
- [ ] Missing, ambiguous, expired, and insufficient credentials each produce a distinct typed rejection and zero retry attempts.
- [ ] A test scans the configuration store, the SQLite database, emitted envelopes and every projection for the fake's token value and finds no occurrence; the environment-variable name is present, the value is not.
- [ ] The provider fake implements the full interface and can script a lost response and an externally changed remote state.
- [ ] A conformance suite against real GitHub.com and GitHub Enterprise exists, records its rows in the support matrix, and skips with an explicit stated reason when credentials are absent.

## Blocked by

- `git-integration#01` — provides the resolved Git Workflow Policy and the `integration.*` operation surface.
- `data-handling#01` — provides the redaction sink enforcement interface every provider and Git output is written through.
