# Same-Run host resumption verification

Issue: `host-harness-resolution#04`
Base revision: `6855d6645a3ca037f778cfa5a615a86d4e3f8b18`
Worktree: `/Users/julioborges/src/personal/gantry-host-harness-planning`
Branch: `feat/host-harness-resolution`
Date: 2026-10-01

## Public seams and behavior

The approved seams are the public execution CLI, Run Log CLI, and canonical round workflow extracted into the existing Node driver. Temporary real Git repositories, linked worktrees and machine-local JSONL logs exercise persistence and isolation. Role agents and the external Critic response are simulated at the harness boundary; this does not prove live role execution on another host.

`execution.py host --require-resolved --host <selection> --run-id <existing-run> --unit-id <unit> --issue <ref> --state-root <path> --cwd <repository> --json` diagnoses the current invocation first, then compares only that Run's recorded host. Its read-only receipt includes old/current identities, `unchanged`, `transition-required` or `establishment-required`, the spent correction count, and whether the latest refutation has an unstarted correction. An unresolved invocation never inherits identity from an existing log or worktree marker. Missing, finished and unsupported Run metadata fail closed.

Canonical recovery binds to `priorRun.run` and its existing assignment. It presents identity/capability/routing effects and preservation guarantees before an explicit transition approval. Decline makes no writes. Approval appends a fixed-shape sanitized `run.resumed.data.hostTransition` in the same log. Unchanged host follows ordinary recovery. No policy, adapter, role-selection or override rewrite occurs. Replaying a correction already started records `recovery=true`; a previously unstarted correction consumes one attempt, and an exhausted ceiling blocks it before role work. Same-Run resumption never appends a copied `correctionsSpent` base.

## Acceptance mapping

1. CLI and workflow fixtures reject unresolved/conflicting hint-only and unsupported identity before agents or initialization. Another Run and both linked worktree markers cannot establish current host.
2. CLI `unchanged` receipts and existing canonical recovery tests exercise ordinary recovery. Transition prompts show old/new identities and requested effects.
3. Decline compares every file in the temporary repository/worktrees/state directory byte for byte, including revisions and the original Run log. No role or mutating command runs.
4. Approved workflow receipts contain the same Run ID, one original `run.started`, sanitized transition provenance and the new capability tier. Native Implement uses the preserved model/effort; the intentional Claude Code Critic dispatch retains its explicit harness/model/high effort after transition to Codex.
5. Recovery keeps the assigned linked worktree and an already-started correction attempt. Shipped correction queries demonstrate no double count, no reset and no free pending correction. Older absent host metadata requires explicit establishment; another Run's newer host cannot substitute.
6. Real linked Git worktrees share the execution unit while separate Run logs retain independent host histories. Test receipts are simulated. Live evidence below is deliberately limited to a read-only comparison.

## Red/green receipts

- `python3 -m unittest tests.test_host_resume -q`: initial red at the new CLI seam because `--run-id` and `--state-root` were not implemented (two JSON decode errors from argparse rejecting the invocation). The first driver accidentally discovered 58 imported helper tests as well; the helper imports were changed to modules so only the intended tests are discovered. The two new CLI tests then passed.
- `python3 -m unittest tests.test_host_resume.HostResumeTests.test_transition_log_rejects_raw_provenance_and_wrong_previous_host -q`: red (`1 != 0`) because raw confirmation provenance was accepted; green after fixed-shape identity/provenance validation and same-Run old-host validation.
- `python3 -m unittest tests.test_host_resume.HostResumeTests.test_resume_of_unstarted_correction_spends_budget_and_exhaustion_stops_work -q`: red because an exhausted pending correction still started role work; green after same-Run event-order classification and budget enforcement. The unchanged-host fixture initially retained Codex roles under Claude Code and reached the real external CLI, which rejected the unsupported effort argument before execution; the fixture was corrected to use native roles for that accounting test. Cross-harness routing uses an explicit simulated dispatch response.
- `python3 -m unittest tests.test_host_resume -q`: 8 tests passed in 9.420 seconds, including same-Run decline/approval, missing older metadata, linked-worktree isolation, sanitized event rejection, pending correction accounting and intentional external Critic routing.
- `python3 -m unittest tests.test_canonical_gantry_workflow tests.test_host_resume tests.test_runlog tests.test_workflow_host_binding tests.test_round_workflow_lifecycle_hooks -q`: 80 tests passed in 56.894 seconds. Historical fixtures that copied recovery into another Run were migrated to the same-Run contract; assertions retain worktree, roadmap/status authority, correction counts, policy-drift events and lifecycle checks. Exhausted recovery explicitly stops rather than granting a free initial correction. Marker cleanup uses a final empty round after exhausted work, retaining checks that all assigned worktree markers are cleared.
- Full initial gates: `npm test` ran 364 Python tests and exposed two older role-recovery fixtures without current host metadata (1 failure, 1 error); `pack:check` passed 10 package tests. Both fixtures now record their original Host Harness. The role-replacement fixture additionally records a real started correction through the public Run Log CLI, so its preserved-count assertion derives evidence rather than trusting the caller. Targeted rerun of the two affected `RoleExecutionRecoveryAndPauseContractTests` passed (2 tests, 2.496 seconds).
- `python3 -m compileall -q .agents/skills/gantry/scripts/execution.py .agents/skills/gantry/scripts/runlog.py tests/test_host_resume.py tests/test_canonical_gantry_workflow.py`: passed.
- `python3 .agents/skills/gantry/scripts/roadmap.py check`: passed, `issues 51/52, specs 8/9`; this Implementer did not change Issue completion or roadmap authority.
- `python3 .agents/skills/gantry/scripts/frontier.py --scope all`: passed with zero graph errors.

## Live current-invocation receipt (read-only)

The coordinator confirmed this invocation's host as Codex. On the actual worktree and existing `run-1790858665`, the shipped CLI was invoked with `host --require-resolved --host codex --run-id run-1790858665 --issue host-harness-resolution#04 --json`.

Sanitized receipt: `status=resolved`, `effectiveHost=codex`, `savedPreference=codex`, `mismatch=false`, `capabilities.tier=supported`, `hooks=false`, `resume.runId=run-1790858665`, `previousHost=codex`, `decision=unchanged`, `correctionsSpent=0`, `correctionPending=false`. Provenance is `invocation:explicit-selection`; environment and installation sources remain hints. This verifies live read-only same-host comparison, not automatic detection or a live host transition. No live transition, replacement Run, replacement worktree, policy mutation or cross-harness role execution is claimed.

## Final gates

Final declared/detected gates run against the base revision above. Receipts are recorded after completion below.

Additional distribution checks: `npm audit --audit-level=high` passed with zero vulnerabilities; `npm pack --dry-run --ignore-scripts` passed with 57 package files. No release or publication occurred.

`python3 .agents/skills/gantry/scripts/gates.py --run --diff-base 6855d6645a3ca037f778cfa5a615a86d4e3f8b18 --cwd /Users/julioborges/src/personal/gantry-host-harness-planning --json` returned exit 0 and `verdict=pass` before commit. Detected `test` (`npm run test`) passed all 364 Python tests in 114.143 seconds. Detected `pack:check` (`npm run pack:check`) passed all 10 package tests in 2.444 seconds. This precommit receipt reports `git.tree_clean=false` and retains the completion requirement `working tree is dirty: uncommitted changes are not part of the delivery`. Full machine-readable receipt: `/tmp/wave29-gates-final.json` (local, not tracked). Implementation commit: `91edb40`.

A separate postcommit inspection at `d25e7e8cb305423dff53e9959a763dd991d3535d`, using the same command without `--run`, reports `git.tree_clean=true` and `requirements=[]`. Receipt: `/tmp/wave29-gates-postcommit-inspection.json` (local, not tracked). This inspection did not rerun tests and does not change the precommit receipt's requirements; fresh Critic execution remains required for the delivered revision.

The delivered change is non-visual CLI/workflow/Run Log behavior; no frontend component or browser interaction changed, so the AGENTS.md Playwright exception applies. `git diff --check` passed. Independent Reviewer and Critic acceptance are still required; this receipt does not mark the Issue done.
