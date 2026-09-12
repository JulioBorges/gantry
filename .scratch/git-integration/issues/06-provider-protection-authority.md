# Provider Protection Authority and divergence blocking

Type: issue
Status: ready-for-agent
Slice: git-integration#06
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

The target branch's actual protection rules, required checks and required approvals are observed through the provider interface and treated as authoritative. Observation happens at readiness and again immediately before any mutation, and the result is compared against the local Git Workflow Policy captured in the snapshot.

A missing, weaker, or otherwise divergent protection blocks until the operator adjusts either the policy or the provider configuration, after which the affected validations rerun. Local configuration can never compensate for weaker provider protection, Gantry never bypasses a provider rule, and there is no fallback to local merge when the Pull Request path is blocked.

## Acceptance criteria

- [ ] Observed protection requiring fewer approvals or fewer checks than the local policy blocks with a typed divergence rejection naming the specific divergent fields.
- [ ] Adjusting the policy to match observed protection reruns the affected validations rather than silently accepting prior evidence.
- [ ] Protection that changes between the readiness observation and the pre-mutation observation blocks until reconciled, and the mutation does not occur.
- [ ] With the Pull Request path blocked for any reason, no operation in the spec performs a local merge; a test enumerates the blocked reasons and asserts the target commit is unchanged in every one.
- [ ] The observed protection record is produced in a shape readiness can report without re-observing.

## Blocked by

- `git-integration#05` — provides the provider interface and the protection observation call.
- `config-and-snapshot#06` — provides Governance Precedence resolution for conflicting rule sources.
