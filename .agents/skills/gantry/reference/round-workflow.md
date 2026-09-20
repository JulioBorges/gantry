# Canonical round workflow

One round contains only Issues selected by `frontier.py` whose dependency readiness is satisfied. The
caller supplies `args.round`, `args.issues`, `args.models`, `args.branch`, `args.baseRef`,
`args.isolate`, `args.correctionBudget`, `args.skillDir`, `args.repoRoot`, effective `args.policy` and
rendered `args.paths`. A Run spans one or more rounds, each a separate invocation of this workflow
sharing the same `args.runId` and `args.unitId`: the caller supplies `args.isFirstRound = false` for
every round after the first (it defaults to `true`, so a single-round Run or a harness that never sets
it needs no change), and, for the last round of a Run, `args.isLastRound` (boolean, true only for that
final frontier round) and `args.learnerRunLogs` (an array of Run-log JSONL paths, normally just the
current Run's `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl`), so the optional Learner phase below can
run; `args.models.learn` is optional and falls back to `args.models.critic` when absent.
The host supplies its command runner as `runCommand(command, { cwd, input })`; integration cannot
proceed without it. `input`, when provided, is written to the invoked command's stdin — every recorded
Run event (`runlog.py append <unitId> <runId> [--state-root <path>]`) is called this way, with the JSON
event payload passed as `input` rather than as a command-line argument, so a harness that only forwards
`cwd` and drops `input` silently breaks every recorded round.

## Recorded Run lifecycle

When the caller also supplies `args.runId` and `args.unitId` (the value of
`runlog.py unit-id --cwd <repoRoot>`), this workflow appends every lifecycle event through
`runlog.py append <unitId> <runId>`: on the first round of a Run (`args.isFirstRound` not explicitly
`false`), `run.started` always opens the recorded Run first (this Run log's required first event, per
`runlog.py`'s own rule), and `run.resumed` follows immediately after when `args.priorRun` names the Run
and worktree being continued; a later round of the same Run passes `args.isFirstRound = false` so
`run.started`, `run.resumed` and `policy.changed` are never appended again — a Run log accepts only one
`run.started` and rejects a duplicate. Every round, first or not, appends `round.started`, one `phase.started` /
`phase.finished` pair per phase that actually runs — Implement, Review and Critic for each Issue, plus the
optional Learner phase (below) on the last round when it finds recurring evidence — one `subagent.started` /
`subagent.stopped` pair per fresh agent carrying the role result, `review.finding` after the Reviewer returns,
`refutation` on every non-accepted Critic verdict, `issue.blocked` when the correction ceiling is spent
without acceptance, `issue.done` on successful integration, `policy.changed` when `args.priorRun.policyHash`
(the policy hash recorded on the prior Run) differs from the current effective policy hash,
`run.cancelled` on the first red post-merge gate and `round.finished` / `run.finished` at the end. When the
Learner phase runs, it is recorded before `run.finished`: `run.finished` remains the Run log's last event
on a completed Run, never followed by a subagent. The
Critic's `subagent.stopped` never carries its verdict unchanged: `runlog.py append` rejects any
`command`, `output` (and similarly-tokenized) field at any nesting level per its own rule, and the
Critic's `gateResult` is a real `gates.py --json` payload whose `gates[]` entries carry exactly those
fields (`command`, `output_tail`) alongside a real command's execution details. The workflow instead
records `projectCriticResult(verdict)`: `complete`, `criteria`, `gatesVerdict`, `gateFailures`,
`refutations`, `requiredFixes` and `decisionsForOperator` unchanged, plus `gateResult` narrowed to only
its `verdict` and `requirements` (both free of command/output data) — never `gateResult.gates`. This
keeps the Run log a record of the Critic's role result and reasoning, never of command output, while the
full verdict (including the untouched `gateResult`) still drives `criticAccepted` and the workflow's own
structured output. Every other role's result reaches `subagent.stopped` unprojected, and `runlog.py`
still fails loudly if any of them carries prohibited data.
Before any agent works in a worktree, the workflow marks that worktree with the Run
(`runlog.py mark <runId> --cwd <worktree>`, written into the worktree's own git directory): the
repository root at the start of every round, and each Issue worktree as it is assigned. A git hook
inherits whatever environment shelled out to `git`, so `GANTRY_RUN_ID` cannot be relied on to reach
`pre-commit`/`pre-push`; the marker is how they resolve the Run instead, which is what makes their
`hook.denied` recording a guarantee rather than a best effort. The hooks and `guard.py` share one
resolution order: `GANTRY_RUN_ID` when the caller exports it, then the marker, and a harness session
ID only when nothing else names a Run and its Run log already exists. Marks are cleared
(`runlog.py unmark`) only when the Run itself ends — the last round, or a cancelled one — never
between rounds of the same Run, and never across worktrees: git keeps one git directory per worktree,
so two worktrees of the same execution unit running different Runs cannot attribute a denial to each
other. Because each round is a separate invocation that only remembers what it marked itself, the
Run's end enumerates `git worktree list --porcelain` and clears every marker naming that Run, so a
worktree marked by an earlier round is never left behind.
Preflight resolves `args.runId` and `args.unitId` once per Run and never rereads the log to decide
readiness or completion — only `frontier.py`, Issue `Status:` lines and `roadmap.py` decide that. When
`args.priorRun` names the Issue being continued (`args.priorRun.issue`), its preserved worktree, branch
and `correctionsSpent` are reused instead of
creating a new worktree or resetting the correction count, and the Issue keeps its authoritative Status
until the Critic accepts it. `args.priorRun.correctionsSpent` is scoped to `args.priorRun.issue` alone —
`runlog.py corrections` (the sole source of this value; see `SKILL.md`) withholds the `run.resumed`
base from any other Issue that happens to share the same Run log, so callers must never reuse one
Issue's derived `correctionsSpent` for a different Issue. Omitting `args.runId` or `args.unitId` disables
all of the above and leaves the round behaviorally identical, so a harness without a resolved Run log
keeps working.

```
implement (TDD) → review (standards + Spec) → one review fix pass
→ adversarial Critic → correction implementer ⇄ Critic (at most two correction attempts)
```

## Per-Issue roles

**Implementer:** a fresh agent reads the complete Issue, parent Spec, settled decisions, context and ADRs.
It follows red → green TDD at the approved CLI, script-interface and template-file seams, makes small
commits, runs `gates.py --run --diff-base <baseRef> --cwd "$(pwd)"`, and leaves a clean tree. It does not
edit `ROADMAP.md`, Issue statuses or criteria checkboxes.

**Reviewer:** a fresh agent reviews the delivery against two independent axes:

- standards: documented repository rules, context and ADRs;
- Spec: every Issue acceptance criterion and its `What to build` contract.

It reports blocking and non-blocking findings. Exactly one fresh Implementer pass addresses blocking review
findings in the same worktree.

**Critic:** a fresh adversarial Critic defaults to refutation. It runs `acceptance.py <issue> --json` and
`gates.py --run --diff-base <baseRef> --cwd "$(pwd)" --json`, verifies evidence per criterion, checks the
tree and diff for weakened tests, placeholders and scope creep, and returns `complete` only with proof.
Refutations generate ordered required fixes and consume one correction attempt; the correction-budget
ceiling is two and exhaustion leaves the Issue refuted with its worktree retained.

## Learner phase (optional)

After the last round of a Run, an optional Learner reads only the `refutation` and `review.finding`
events already recorded in the Run log — never source files, `AGENTS.md`, `CONTEXT.md`, a template or
the repository policy. `learner.py <runlog...> --json` groups identical evidence text across different
Issues or attempts and drafts one lesson candidate per recurring group, each carrying the recurring
evidence and a proposed target (the Gantry section of `AGENTS.md`, `CONTEXT.md`, or an effective
template); a problem that occurred on only one Issue or attempt produces no candidate. When the
extraction finds nothing recurring, or no Run-log path is available, the phase is skipped — no
`phase.started`/`subagent.started`/`subagent.stopped`/`phase.finished` events are recorded for a
skipped Learner phase. When the Learner does run, it is recorded like every other phase: `phase.started`,
`subagent.started`, `subagent.stopped` (carrying the candidates as its result) and `phase.finished`, all
appended after `round.finished` and before `run.finished`, so `run.finished` stays the Run log's last
event and no subagent runs after it. `runlog.py` requires an `issue` on every `phase.started`/
`phase.finished` event; because the Learner is not scoped to one Issue, these events use the reserved
non-Issue reference `learn#00` rather than a real Issue ref. The Learner
never writes anything: a lesson candidate is a draft for the operator to accept or discard, surfaced by
the final report, never auto-injected into `AGENTS.md`, `CONTEXT.md`, a template or policy.

## Isolation and integration

When `args.isolate` is true, each Implementer uses its own worktree and branch from `args.baseRef`; agents
in the round may run concurrently. The host harness waits for accepted deliveries and integrates branches
one at a time with `git merge --no-ff`. Run the declared gates after every merge. A failing merge gate stops
the Run rather than fixing forward.

Only a Critic-complete, gate-green and clean delivery may be integrated. Completion requires exactly one
passing, non-empty evidence entry for every criterion returned by `acceptance.py`; the workflow does not
trust Issue fields carried in its input. Then, and only then, the orchestrator calls `roadmap.py done <ref>`
and commits the resulting authoritative projection. Refuted, failed, parked and externally blocked Issues
remain unticked.

When the correction ceiling is spent without acceptance, the workflow records `issue.blocked` in the Run
log and preserves the worktree, but it never writes to the Issue file: the Issue keeps its authoritative
`Status: ready-for-agent` so `frontier.py` still reports it as workable and a fresh Run (with or without
continuation) can pick it up. "Blocked" here names a Run-log fact about this attempt, not an Issue-file
projection — status authority stays in Issue files, per this Issue's contract, and only `roadmap.py done`
(after Critic acceptance) ever changes an Issue's `Status:` line.

## Dashboard lifecycle hooks

Before the `Implement` phase begins in any round, the workflow queries `dashboard.py status --json`:
- If inactive, it prompts the operator asking whether to start the dashboard (`dashboard.py start --daemon`). If approved, it launches the daemon and displays the URL; if declined, it proceeds without prompting again.
- If already active, it logs the active URL without prompting.

Immediately after the `Integrate` step completes at the end of each round:
- The workflow queries `dashboard.py status --json`. If active, it prompts the operator asking whether to terminate the dashboard (`dashboard.py stop`). If approved, it terminates the server daemon.

## Executable Claude Code Workflow

This Workflow script is the executable chain. It creates one Implementer chain per Issue; `pipeline`
may run those independent chains in parallel, but each chain keeps TDD → review → Critic ordering.

```js
export const meta = {
  name: 'gantry-round',
  description: 'Gantry round: TDD, two-axis review and adversarial Critic per Issue',
  phases: [
    { title: 'Implement', detail: 'one TDD Implementer per Issue' },
    { title: 'Review', detail: 'standards and Spec, with one fix pass' },
    { title: 'Critic', detail: 'adversarial verification and bounded corrections' },
    { title: 'Learn', detail: 'optional recurring lesson candidates for the operator' },
  ],
}

const A = args
const scripts = `${A.skillDir}/scripts`
const paths = A.paths
const policy = A.policy
const requestedBudget = A.correctionBudget ?? policy.budget.corrections
const budget = Number.isInteger(requestedBudget) && requestedBudget >= 0
  ? Math.min(requestedBudget, 2)
  : 2

const runLogEnabled = Boolean(A.runId && A.unitId)
const stateRootFlag = A.stateRoot ? ` --state-root '${String(A.stateRoot).replaceAll("'", "'\\''")}'` : ''

const cavemanState = A.caveman || { active: false, preference: false, scope: 'none' }
const cavemanActive = Boolean(cavemanState && cavemanState.active)
if (cavemanState && cavemanState.warning) {
  if (typeof log === 'function') log(cavemanState.warning)
  cavemanState.warned = true
}
const cavemanInstruction = cavemanActive
  ? 'Caveman lite is active: use concise phrasing for conversational messages and summaries. Code, documentation, lesson candidates, PR descriptions, Result Contracts, exact commands, exact errors, acceptance criteria, and verification evidence retain full detail.'
  : ''

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical)
  if (value && typeof value === 'object') {
    return Object.keys(value).sort().reduce((acc, key) => {
      acc[key] = canonical(value[key])
      return acc
    }, {})
  }
  return value
}

function stableHash(value) {
  const json = JSON.stringify(canonical(value))
  let hash = 5381
  for (let index = 0; index < json.length; index += 1) {
    hash = ((hash * 33) ^ json.charCodeAt(index)) >>> 0
  }
  return hash.toString(16).padStart(8, '0')
}

function projectCriticResult(verdict) {
  if (!verdict || typeof verdict !== 'object') return verdict
  const projected = {
    complete: verdict.complete,
    criteria: verdict.criteria,
    gatesVerdict: verdict.gatesVerdict,
    gateFailures: verdict.gateFailures,
    refutations: verdict.refutations,
    requiredFixes: verdict.requiredFixes,
    decisionsForOperator: verdict.decisionsForOperator,
  }
  if (verdict.gateResult && typeof verdict.gateResult === 'object') {
    projected.gateResult = { verdict: verdict.gateResult.verdict, requirements: verdict.gateResult.requirements }
  }
  return projected
}

async function appendRunEvent(event, issueRef, phaseName, data) {
  if (!runLogEnabled) return
  const payload = {
    ts: new Date().toISOString(),
    run: A.runId,
    event,
    ...(issueRef ? { issue: issueRef } : {}),
    ...(phaseName ? { phase: phaseName } : {}),
    ...(data !== undefined ? { data } : {}),
  }
  await runWorkflowCommand(
    `python3 "${scripts}/runlog.py" append '${A.unitId}' '${A.runId}'${stateRootFlag}`,
    { cwd: A.repoRoot, input: JSON.stringify(payload) },
  )
}

// A git hook inherits the environment of whatever shelled out to `git`, which no harness
// controls, so `GANTRY_RUN_ID` cannot be relied on to reach `pre-commit`/`pre-push`. Every
// worktree this Run works in is therefore marked with the Run before any agent runs there
// (`runlog.py mark`, which writes into that worktree's own git directory); the hooks read it
// back through `runlog.resolve_hook_run`, which is what makes their `hook.denied` recording a
// guarantee. The marks are cleared when the Run itself ends, never between rounds.
const markedWorktrees = new Set()

async function markRunIn(worktree) {
  if (!runLogEnabled || !worktree || markedWorktrees.has(worktree)) return
  await runWorkflowCommand(
    `python3 "${scripts}/runlog.py" mark '${A.runId}' --cwd ${shellQuote(worktree)}${stateRootFlag}`,
    { cwd: worktree },
  )
  markedWorktrees.add(worktree)
}

// Each round is a separate invocation with its own memory, so `markedWorktrees` only ever holds
// what *this* invocation marked -- an Issue finished in an earlier round is absent from the last
// one and its worktree would keep a marker naming a Run that is already over. The Run's end
// therefore enumerates the clone's worktrees and clears every marker that names this Run.
async function unmarkRun() {
  if (!runLogEnabled) return
  const worktrees = new Set(markedWorktrees)
  const listed = await runCommand('git worktree list --porcelain', { cwd: A.repoRoot })
  if (listed && listed.exitCode === 0) {
    for (const line of String(listed.stdout || '').split('\n')) {
      if (line.startsWith('worktree ')) worktrees.add(line.slice('worktree '.length).trim())
    }
  }
  for (const worktree of worktrees) {
    if (!worktree) continue
    const current = await runCommand(
      `python3 "${scripts}/runlog.py" current --cwd ${shellQuote(worktree)}`, { cwd: A.repoRoot },
    )
    if (!current || current.exitCode !== 0 || String(current.stdout || '').trim() !== A.runId) continue
    await runCommand(`python3 "${scripts}/runlog.py" unmark --cwd ${shellQuote(worktree)}`, { cwd: A.repoRoot })
  }
  markedWorktrees.clear()
}

function priorAssignment(issue) {
  return A.priorRun && A.priorRun.issue === issue.ref ? A.priorRun : null
}

// `runlog.py` requires `issue` on every `phase.started`/`phase.finished` event; the Learn phase is not
// tied to any single Issue, so it records its phase/subagent events against this reserved, non-Issue
// reference rather than omitting `issue` (which `runlog.py append` would reject).
const LEARN_PHASE_ISSUE = 'learn#00'

const isFirstRound = A.isFirstRound !== false
if (runLogEnabled && isFirstRound) {
  const runStartedData = {
    repositoryRoot: A.repoRoot,
    policyHash: stableHash(policy),
    tier: A.tier || 'unknown',
    staleAfterSeconds: (policy.dashboard && policy.dashboard.staleAfterSeconds) || 900,
  }
  await appendRunEvent('run.started', undefined, undefined, runStartedData)
  if (A.priorRun && A.priorRun.run) {
    await appendRunEvent('run.resumed', undefined, undefined, {
      priorRun: A.priorRun.run,
      worktree: A.priorRun.worktree,
      issue: A.priorRun.issue,
      correctionsSpent: A.priorRun.correctionsSpent,
    })
  }
  if (A.priorRun && A.priorRun.policyHash && A.priorRun.policyHash !== runStartedData.policyHash) {
    await appendRunEvent('policy.changed', undefined, undefined, { policyHash: runStartedData.policyHash })
  }
}
if (runLogEnabled) {
  await markRunIn(A.repoRoot)
  await appendRunEvent('round.started', undefined, undefined, { round: A.round })
}

async function roleSchema(role) {
  const result = await runWorkflowCommand(
    `python3 "${scripts}/result.py" --role "${role}" --schema`,
  )
  return JSON.parse(result.stdout)
}

function resolveRoleForIssue(issueRef, role, options) {
  if (options && options.selection) return options.selection
  if (issueRef && A.issueRoleReplacements && A.issueRoleReplacements[issueRef] && A.issueRoleReplacements[issueRef][role]) {
    return A.issueRoleReplacements[issueRef][role]
  }
  if (issueRef && A.issueRoles && A.issueRoles[issueRef] && A.issueRoles[issueRef][role]) {
    return A.issueRoles[issueRef][role]
  }
  const roleKey = role === 'implementer' ? 'implement' : role === 'reviewer' ? 'review' : role
  if (A.roles && (A.roles[role] || A.roles[roleKey])) {
    return A.roles[role] || A.roles[roleKey]
  }
  if (A.models && (A.models[role] || A.models[roleKey])) {
    return { harness: A.hostHarness || 'claude-code', model: A.models[role] || A.models[roleKey] }
  }
  return null
}

async function logRoleSelected(issueRef, role, selection) {
  const isSelectionConfigured = Boolean(A.roles || A.issueRoles || A.issueRoleReplacements || A.recordRoleSelection)
  if (!runLogEnabled || !selection || !issueRef || !isSelectionConfigured) return
  await appendRunEvent('role.selected', issueRef, undefined, {
    role,
    issue: issueRef,
    requested: selection,
    effective: selection,
    evidence: { source: 'role_selection' },
  })
}

// Check for unresolved execution failures
let unresolvedFailures = Array.isArray(A.unresolvedFailures) ? [...A.unresolvedFailures] : []
if (unresolvedFailures.length === 0 && runLogEnabled && !isFirstRound) {
  try {
    const unresCheck = await runCommand(
      `python3 "${scripts}/execution.py" unresolved-failures '${A.unitId}' '${A.runId}'${stateRootFlag} --json`,
      { cwd: A.repoRoot },
    )
    if (unresCheck && unresCheck.exitCode === 0) {
      unresolvedFailures = JSON.parse(unresCheck.stdout)
    }
  } catch (e) {}
}

if (unresolvedFailures.length > 0) {
  const remainingUnresolved = []
  for (const failure of unresolvedFailures) {
    const replacement = resolveRoleForIssue(failure.issue, failure.role, null)
    const hasReplacement = Boolean(
      replacement &&
      ((A.issueRoles && A.issueRoles[failure.issue] && A.issueRoles[failure.issue][failure.role]) ||
       (A.issueRoleReplacements && A.issueRoleReplacements[failure.issue] && A.issueRoleReplacements[failure.issue][failure.role]))
    )
    if (hasReplacement) {
      const repJson = JSON.stringify(replacement)
      const valCmd = `python3 "${scripts}/execution.py" validate-replacement --issue "${failure.issue}" --role "${failure.role}" --selection '${repJson.replaceAll("'", "'\\''")}' --cwd ${shellQuote(A.repoRoot)} --json`
      const valRes = await runCommand(valCmd, { cwd: A.repoRoot })
      let valid = false
      if (valRes && valRes.exitCode === 0) {
        try {
          const parsed = JSON.parse(valRes.stdout)
          valid = parsed.valid === true
        } catch (e) {}
      }
      if (!valid) {
        return {
          round: A.round,
          blocked: true,
          nextRoundBlocked: true,
          reason: 'invalid_role_replacement',
          error: `Invalid replacement selection for ${failure.issue} role ${failure.role}`,
          results: [],
        }
      }
      await appendRunEvent('role.changed', failure.issue, undefined, {
        role: failure.role,
        issue: failure.issue,
        previous: failure.selection || { harness: 'unknown' },
        requested: replacement,
        effective: replacement,
        evidence: { source: 'explicit_recovery' },
      })
    } else {
      remainingUnresolved.push(failure)
    }
  }
  if (remainingUnresolved.length > 0) {
    return {
      round: A.round,
      blocked: true,
      nextRoundBlocked: true,
      reason: 'unresolved_execution_failure',
      unresolvedFailures: remainingUnresolved,
      results: [],
    }
  }
}

async function validRoleResult(role, result) {
  if (!result) return false
  if (A.structuredOutput === true) return true
  const validation = await runCommand(
    `python3 "${scripts}/result.py" --role "${role}" --json`,
    { cwd: A.repoRoot, input: JSON.stringify(result) },
  )
  return Boolean(validation && validation.exitCode === 0)
}
async function requestRole(role, prompt, options) {
  const issueRef = options && options.issueRef
  const selection = resolveRoleForIssue(issueRef, role, options)
  const hostHarness = A.hostHarness || 'claude-code'
  if (options && options.executionUnavailable) {
    return { executionUnavailable: true, error: options.error || 'Role execution unavailable' }
  }
  if (selection && selection.harness && selection.harness !== hostHarness) {
    const cwd = (options && options.cwd) || A.repoRoot
    const selectionJson = JSON.stringify(selection)
    const agentPrompt = cavemanActive ? `${prompt}\n\n${cavemanInstruction}` : prompt
    const cmd = `python3 "${scripts}/execution.py" dispatch --role "${role}" --cwd ${shellQuote(cwd)} --selection '${selectionJson.replaceAll("'", "'\\''")}'`
    const res = await runCommand(cmd, { cwd: A.repoRoot, input: agentPrompt })
    if (res && res.exitCode === 0) {
      try {
        return JSON.parse(res.stdout)
      } catch (e) {
        return null
      }
    }
    if (res && res.exitCode === 2) {
      return null
    }
    return { executionUnavailable: true, error: (res && res.stderr) || 'Harness execution failed' }
  }
  const native = A.structuredOutput === true
  const schema = native ? await roleSchema(role) : null
  const agentPrompt = cavemanActive ? `${prompt}\n\n${cavemanInstruction}` : prompt
  const agentOptions = {
    ...options,
    ...(cavemanActive ? { skills: (options.skills || []).concat(cavemanState.skill_path || 'caveman'), caveman: true } : {}),
    ...(schema ? { schema } : {}),
  }
  let result
  try {
    result = await agent(agentPrompt, agentOptions)
  } catch (err) {
    return { executionUnavailable: true, error: String(err && err.message ? err.message : err) }
  }
  if (result && result.executionUnavailable) {
    return { executionUnavailable: true, error: result.error || 'Execution unavailable' }
  }
  if (await validRoleResult(role, result)) return result
  const retryPrompt = `${agentPrompt}\nYour prior result was invalid. Return the complete ${role} result contract.`
  const retryOptions = {
    ...agentOptions,
    label: `${options.label}:retry`,
  }
  let retry
  try {
    retry = await agent(retryPrompt, retryOptions)
  } catch (err) {
    return { executionUnavailable: true, error: String(err && err.message ? err.message : err) }
  }
  if (retry && retry.executionUnavailable) {
    return { executionUnavailable: true, error: retry.error || 'Execution unavailable' }
  }
  return (await validRoleResult(role, retry)) ? retry : null
}

function location(impl) {
  return impl && impl.worktree ? impl.worktree : A.repoRoot
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`
}

function issueWorktreePath(issue) {
  const [spec, number] = issue.ref.split('#')
  return `${A.repoRoot}.gantry-${spec}-${String(Number(number)).padStart(2, '0')}`
}

async function configuredIssueBranch(issue) {
  let result
  try {
    result = await runWorkflowCommand(
      `python3 "${scripts}/common.py" --cwd ${shellQuote(A.repoRoot)} --issue ${shellQuote(issue.path)} --json`,
    )
    const payload = JSON.parse(result.stdout)
    if (typeof payload.issueBranch !== 'string' || !payload.issueBranch) throw new Error('missing issueBranch')
    return payload.issueBranch
  } catch {
    return null
  }
}

async function implementationLocation(issue, previous) {
  if (!A.isolate) return { worktree: A.repoRoot, branch: A.branch }
  const prior = priorAssignment(issue)
  if (!previous && prior && prior.worktree) {
    const branch = prior.branch || await configuredIssueBranch(issue)
    if (!branch) return null
    const current = await runCommand('git branch --show-current', { cwd: prior.worktree })
    return current && current.exitCode === 0 && current.stdout.trim() === branch
      ? { worktree: prior.worktree, branch }
      : null
  }
  const branch = await configuredIssueBranch(issue)
  if (!branch) return null
  if (previous) {
    if (previous.branch !== branch) return null
    const current = await runCommand('git branch --show-current', { cwd: previous.worktree })
    return current && current.exitCode === 0 && current.stdout.trim() === branch
      ? { worktree: previous.worktree, branch }
      : null
  }
  const worktree = issueWorktreePath(issue)
  try {
    await runWorkflowCommand(
      `git worktree add --quiet -b ${shellQuote(branch)} ${shellQuote(worktree)} ${shellQuote(A.baseRef)}`,
    )
    const current = await runCommand('git branch --show-current', { cwd: worktree })
    return current && current.exitCode === 0 && current.stdout.trim() === branch
      ? { worktree, branch }
      : null
  } catch {
    return null
  }
}

async function authoritativeCriterionIndexes(issue) {
  let result
  try {
    result = await runWorkflowCommand(
      `python3 "${scripts}/acceptance.py" "${A.repoRoot}/${issue.path}" --json`,
    )
  } catch {
    return null
  }
  try {
    const acceptance = JSON.parse(result.stdout)
    if (!Array.isArray(acceptance.criteria) || acceptance.criteria.length === 0) return null
    const indexes = acceptance.criteria.map(item => item && item.index)
    if (!indexes.every(index => Number.isInteger(index) && index > 0)) return null
    if (new Set(indexes).size !== indexes.length) return null
    return indexes
  } catch {
    return null
  }
}

async function criticAccepted(verdict, issue) {
  if (!verdict || verdict.complete !== true || verdict.gatesVerdict !== 'pass' ||
      !verdict.gateResult || verdict.gateResult.verdict !== verdict.gatesVerdict) return false
  const expectedIndexes = await authoritativeCriterionIndexes(issue)
  if (!expectedIndexes || !Array.isArray(verdict.criteria) || verdict.criteria.length !== expectedIndexes.length) return false
  const observedIndexes = new Set()
  for (const criterion of verdict.criteria) {
    if (!criterion || typeof criterion !== 'object' || !Number.isInteger(criterion.index) ||
        !expectedIndexes.includes(criterion.index) || observedIndexes.has(criterion.index) ||
        criterion.met !== true || typeof criterion.evidence !== 'string' || !criterion.evidence.trim()) {
      return false
    }
    observedIndexes.add(criterion.index)
  }
  return observedIndexes.size === expectedIndexes.length
}

async function runWorkflowCommand(command, options) {
  const result = await runCommand(command, { cwd: A.repoRoot, ...(options || {}) })
  if (!result || result.exitCode !== 0) {
    throw new Error(`workflow command failed: ${command}`)
  }
  return result
}

async function integrationGatePasses() {
  let result
  try {
    result = await runWorkflowCommand(
      `python3 "${scripts}/gates.py" --run --diff-base ${A.baseRef} --cwd "${A.repoRoot}" --json`,
    )
  } catch {
    return false
  }
  try {
    const payload = JSON.parse(result.stdout)
    return payload.verdict === 'pass' && Array.isArray(payload.requirements) && payload.requirements.length === 0
  } catch {
    return false
  }
}

function implementPrompt(issue, feedback, assigned) {
  const work = `Work in ${assigned.worktree} on ${assigned.branch}; verify the current branch and never switch it.`
  return `You are the fresh TDD Implementer for ${issue.ref} — "${issue.title}".
${work}
Read ${issue.path}, ${issue.specPath}, ${paths.decisions}, ${paths.context}, and ${paths.adrs} first.
Implement only this Issue. Invoke the \`tdd\` skill and work behavior by behavior: failing test → minimal
code → refactor. Keep tests real where the criterion requires a real process, file, repository or command.
Run \`python3 ${scripts}/gates.py --run --diff-base ${A.baseRef} --cwd "$(pwd)"\` before returning.
Never edit ROADMAP.md, Status, or criteria checkboxes. Never force-push, and never skip, disable
or weaken a test. Never bypass the repository git hooks: no \`--no-verify\` in any abbreviation
(e.g. \`--no-veri\`) or \`-n\`, no \`core.hooksPath\` override in any spelling, no
\`--git-dir\`/\`GIT_DIR=\`, no \`GIT_CONFIG_*\`.
Commit small changes and leave a clean tree.
Effective Git policy: target ${policy.git.target}, prefix ${policy.git.prefix}.
${feedback ? `Fix every item first:\n${feedback.items.map((item, index) => `${index + 1}. ${typeof item === 'string' ? item : `${item.finding} → ${item.fix}`}`).join('\n')}` : ''}
Return worktree, branch, commits, summary, testsAdded, gatesResult, decisions and blockers as structured output.`
}

function reviewPrompt(issue, impl) {
  return `You are the fresh Reviewer for ${issue.ref}, in ${location(impl)}, against ${A.baseRef}.
Invoke the \`code-review\` skill; if unavailable, perform its two axes yourself.
Standards: AGENTS.md, ${paths.context}, ${paths.adrs}, repository standards, and no weakened verification.
Spec: every criterion and every paragraph of ${issue.path}'s What to build; identify missing, wrong or
scope-creeping behavior. Do not edit. Return blocking, nonBlocking and summary as structured output.`
}

function criticPrompt(issue, impl, review, attempt) {
  return `You are the fresh adversarial Critic for ${issue.ref}, attempt ${attempt}, in ${location(impl)}
against ${A.baseRef}. Default to complete=false when uncertain; never trust the Implementer. The correction
budget ceiling is two attempts and must never be raised.
Run \`python3 ${scripts}/acceptance.py ${A.repoRoot}/${issue.path} --json\` and prove every criterion with
code plus a real test or required command output. Run
\`python3 ${scripts}/gates.py --run --diff-base ${A.baseRef} --cwd "$(pwd)" --json\`; parse its JSON verdict
and requirements. Return that parsed result unchanged in \`gateResult\`; derive \`gatesVerdict\` and
\`gateFailures\` from it, never a prose paraphrase. \`no_gates\` and \`not_run\` are not passing results.
Require a clean tree and commits after ${A.baseRef}. Inspect the diff for skipped,
disabled or mock-replaced tests, TODO/FIXME/not implemented text, Status/checkbox/ROADMAP edits, and scope
creep. Check \`git reflog\` and the branch history for a forced rewrite; a force-push is a refutation on
its own. So is any commit or push made with \`--no-verify\` in any abbreviation (e.g.
\`--no-veri\`) or \`-n\`, or under a \`core.hooksPath\`/\`--git-dir\`/\`GIT_DIR=\`/\`GIT_CONFIG_*\`
override, and any test-skip pattern that reached HEAD despite the hooks. Verify the Review
findings were actually fixed. Do not edit.
Return complete only for gate-green, clean, fully evidenced work; otherwise ordered requiredFixes,
refutations, gateResult, gateFailures and decisionsForOperator as structured output.`
}

async function implement(issue, feedback, previous) {
  const assigned = await implementationLocation(issue, previous)
  if (!assigned) return null
  const selection = resolveRoleForIssue(issue.ref, 'implementer', null)
  await logRoleSelected(issue.ref, 'implementer', selection)
  const options = {
    label: `implement:${issue.ref}`, phase: 'Implement', model: A.models.implement, cwd: assigned.worktree,
    issueRef: issue.ref, selection,
    ...(A.issueExecutionUnavailable && A.issueExecutionUnavailable[issue.ref] === 'implementer' ? { executionUnavailable: true } : {}),
  }
  await markRunIn(assigned.worktree)
  await appendRunEvent('phase.started', issue.ref, 'Implement', { worktree: assigned.worktree })
  await appendRunEvent('subagent.started', issue.ref, 'Implement', { role: 'implementer' })
  const result = await requestRole('implementer', implementPrompt(issue, feedback, assigned), options)
  if (result && result.executionUnavailable) {
    return { executionUnavailable: true, role: 'implementer', error: result.error, worktree: assigned.worktree, branch: assigned.branch }
  }
  await appendRunEvent('subagent.stopped', issue.ref, 'Implement', { role: 'implementer', result })
  await appendRunEvent('phase.finished', issue.ref, 'Implement', { worktree: assigned.worktree })
  return result && result.worktree === assigned.worktree && result.branch === assigned.branch ? result : null
}

// Pre-implementation dashboard check
if (typeof prompt === 'function' && !A.skipDashboardPrompt) {
  const dashCheck = await runCommand(`python3 "${scripts}/dashboard.py" status --json`, { cwd: A.repoRoot })
  let dashStatus = null
  if (dashCheck && dashCheck.exitCode === 0 && dashCheck.stdout && dashCheck.stdout.trim()) {
    try { dashStatus = JSON.parse(dashCheck.stdout) } catch (e) {}
  }
  if (dashStatus && dashStatus.running) {
    log(`Dashboard active at ${dashStatus.url}`)
  } else if (dashStatus && !dashStatus.running) {
    const askStart = await prompt('The dashboard is currently inactive. Would you like to start it in the background (dashboard.py start --daemon)? (yes/no)')
    if (askStart && askStart.toLowerCase().trim() === 'yes') {
      const startRes = await runCommand(`python3 "${scripts}/dashboard.py" start --daemon`, { cwd: A.repoRoot })
      if (startRes && startRes.exitCode === 0) {
        const recheck = await runCommand(`python3 "${scripts}/dashboard.py" status --json`, { cwd: A.repoRoot })
        try {
          const recheckStatus = JSON.parse(recheck.stdout)
          log(`Dashboard started at ${recheckStatus.url}`)
        } catch (e) {}
      }
    }
  }
}

const results = await pipeline(
  A.issues,
  issue => implement(issue, null, null),
  async (impl, issue) => {
    if (!impl) return null
    if (impl.executionUnavailable) return impl
    const selection = resolveRoleForIssue(issue.ref, 'reviewer', null)
    await logRoleSelected(issue.ref, 'reviewer', selection)
    await appendRunEvent('phase.started', issue.ref, 'Review', { worktree: location(impl) })
    await appendRunEvent('subagent.started', issue.ref, 'Review', { role: 'reviewer' })
    const review = await requestRole('reviewer', reviewPrompt(issue, impl), {
      label: `review:${issue.ref}`, phase: 'Review', model: A.models.review, cwd: location(impl),
      issueRef: issue.ref, selection,
      ...(A.issueExecutionUnavailable && A.issueExecutionUnavailable[issue.ref] === 'reviewer' ? { executionUnavailable: true } : {}),
    })
    if (review && review.executionUnavailable) {
      return { executionUnavailable: true, role: 'reviewer', error: review.error, impl }
    }
    await appendRunEvent('subagent.stopped', issue.ref, 'Review', { role: 'reviewer', result: review })
    await appendRunEvent('phase.finished', issue.ref, 'Review', {})
    if (review) {
      await appendRunEvent('review.finding', issue.ref, 'Review', {
        blocking: review.blocking.length, nonBlocking: review.nonBlocking.length,
      })
    }
    if (!review) return { impl, reviewerFailed: true }
    const reviewed = review && review.blocking.length
      ? await implement(issue, { kind: 'review', items: review.blocking }, impl)
      : impl
    if (!reviewed) {
      return { impl: null, implementerFailed: true, failedImpl: impl, review, reviewFix: true }
    }
    if (reviewed.executionUnavailable) return reviewed
    return { impl: reviewed, review, reviewFix: Boolean(review && review.blocking.length) }
  },
  async (state, issue) => {
    if (!state) return { ref: issue.ref, outcome: 'implementer_failed' }
    if (state.executionUnavailable) {
      const impl = state.impl
      const worktree = (impl && impl.worktree) || state.worktree || issueWorktreePath(issue)
      const branch = (impl && impl.branch) || state.branch || await configuredIssueBranch(issue)
      const corrections = state.corrections || 0
      await appendRunEvent('issue.paused', issue.ref, state.role === 'reviewer' ? 'Review' : state.role === 'implementer' ? 'Implement' : 'Critic', {
        role: state.role || 'critic',
        reason: 'execution_unavailable',
        worktree,
        error: state.error || 'Role execution unavailable',
      })
      return {
        ref: issue.ref,
        issuePath: issue.path,
        outcome: 'paused',
        status: 'paused',
        reason: 'execution_unavailable',
        executionUnavailable: true,
        role: state.role || 'critic',
        error: state.error || 'Role execution unavailable',
        worktree,
        branch,
        commits: (impl && impl.commits) || [],
        corrections,
        reviewFix: state.reviewFix,
        review: state.review,
        verdict: null,
        decisions: (impl && impl.decisions) || [],
        blockers: (impl && impl.blockers) || [],
      }
    }
    if (state.implementerFailed) {
      return {
        ref: issue.ref, outcome: 'implementer_failed',
        worktree: state.failedImpl.worktree, branch: state.failedImpl.branch,
        commits: state.failedImpl.commits, corrections: 0, reviewFix: state.reviewFix,
        review: state.review, verdict: null,
        decisions: state.failedImpl.decisions || [], blockers: state.failedImpl.blockers || [],
      }
    }
    if (!state.impl) return { ref: issue.ref, outcome: 'implementer_failed' }
    if (state.reviewerFailed) return { ref: issue.ref, outcome: 'reviewer_failed', worktree: state.impl.worktree, branch: state.impl.branch }
    let impl = state.impl
    let verdict = null
    const prior = priorAssignment(issue)
    let corrections = prior && Number.isInteger(prior.correctionsSpent) ? prior.correctionsSpent : 0
    let accepted = false
    for (let attempt = 1; ; attempt += 1) {
      const selection = resolveRoleForIssue(issue.ref, 'critic', null)
      await logRoleSelected(issue.ref, 'critic', selection)
      await appendRunEvent('phase.started', issue.ref, 'Critic', { attempt, worktree: location(impl) })
      await appendRunEvent('subagent.started', issue.ref, 'Critic', { role: 'critic', attempt })
      verdict = await requestRole('critic', criticPrompt(issue, impl, state.review, attempt), {
        label: `critic:${issue.ref}#${attempt}`, phase: 'Critic', model: A.models.critic, cwd: location(impl),
        issueRef: issue.ref, selection,
        ...(A.issueExecutionUnavailable && A.issueExecutionUnavailable[issue.ref] === 'critic' ? { executionUnavailable: true } : {}),
      })
      if (verdict && verdict.executionUnavailable) {
        await appendRunEvent('issue.paused', issue.ref, 'Critic', {
          role: 'critic',
          reason: 'execution_unavailable',
          worktree: location(impl),
          error: verdict.error || 'Critic execution unavailable',
        })
        return {
          ref: issue.ref,
          issuePath: issue.path,
          outcome: 'paused',
          status: 'paused',
          reason: 'execution_unavailable',
          executionUnavailable: true,
          role: 'critic',
          error: verdict.error || 'Critic execution unavailable',
          worktree: impl.worktree,
          branch: impl.branch,
          commits: impl.commits,
          corrections,
          reviewFix: state.reviewFix,
          review: state.review,
          verdict: null,
          decisions: (impl.decisions) || [],
          blockers: (impl.blockers) || [],
        }
      }
      await appendRunEvent('subagent.stopped', issue.ref, 'Critic', { role: 'critic', attempt, result: projectCriticResult(verdict) })
      await appendRunEvent('phase.finished', issue.ref, 'Critic', { attempt })
      if (!verdict) {
        return {
          ref: issue.ref, issuePath: issue.path, outcome: 'critic_failed',
          worktree: impl.worktree, branch: impl.branch, commits: impl.commits,
          corrections, reviewFix: state.reviewFix, review: state.review, verdict: null,
          decisions: (impl.decisions) || [], blockers: impl.blockers || [],
        }
      }
      accepted = await criticAccepted(verdict, issue)
      if (!accepted) {
        await appendRunEvent('refutation', issue.ref, 'Critic', {
          attempt, refutations: verdict.refutations || [],
        })
      }
      if (accepted || corrections >= budget) break
      const corrected = await implement(issue, { kind: 'critic', items: verdict.requiredFixes }, impl)
      if (!corrected) {
        return {
          ref: issue.ref, issuePath: issue.path, outcome: 'implementer_failed',
          worktree: impl.worktree, branch: impl.branch, commits: impl.commits,
          corrections, reviewFix: state.reviewFix, review: state.review, verdict,
          decisions: [...(impl.decisions || []), ...(verdict.decisionsForOperator || [])],
          blockers: impl.blockers || [],
        }
      }
      if (corrected.executionUnavailable) {
        await appendRunEvent('issue.paused', issue.ref, 'Implement', {
          role: 'implementer',
          reason: 'execution_unavailable',
          worktree: location(corrected),
          error: corrected.error || 'Implementer execution unavailable',
        })
        return {
          ref: issue.ref,
          issuePath: issue.path,
          outcome: 'paused',
          status: 'paused',
          reason: 'execution_unavailable',
          executionUnavailable: true,
          role: 'implementer',
          error: corrected.error || 'Implementer execution unavailable',
          worktree: corrected.worktree || impl.worktree,
          branch: corrected.branch || impl.branch,
          commits: impl.commits,
          corrections,
          reviewFix: state.reviewFix,
          review: state.review,
          verdict,
          decisions: [...(impl.decisions || []), ...(verdict.decisionsForOperator || [])],
          blockers: impl.blockers || [],
        }
      }
      corrections += 1
      impl = corrected
    }
    if (!accepted) {
      await appendRunEvent('issue.blocked', issue.ref, 'Critic', {
        worktree: impl && impl.worktree, corrections,
      })
    }
    return {
      ref: issue.ref,
      issuePath: issue.path,
      outcome: accepted ? 'accepted' : 'refuted',
      worktree: impl && impl.worktree, branch: impl && impl.branch, commits: impl && impl.commits,
      corrections, reviewFix: state.reviewFix, review: state.review, verdict,
      decisions: [...((impl && impl.decisions) || []), ...((verdict && verdict.decisionsForOperator) || [])],
      blockers: (impl && impl.blockers) || [],
    }
  },
)

function learnerPrompt(extracted) {
  return `You are the fresh optional Learner for this Run.
Read only the recurring refutation and review-finding evidence already extracted below from the Run
log; never open AGENTS.md, CONTEXT.md, a template, the repository policy or any source file.
${JSON.stringify(extracted.candidates)}
Draft one English lesson candidate per recurring group above, unchanged in its evidence, and name its
proposed target (the Gantry section of AGENTS.md, CONTEXT.md, or an effective template). Never edit
AGENTS.md, CONTEXT.md, a template or policy; a candidate is a draft for the operator.
Return candidates as structured output.`
}

async function learn() {
  const logs = Array.isArray(A.learnerRunLogs) ? A.learnerRunLogs.filter(Boolean) : []
  if (!logs.length) return []
  let extracted
  try {
    const result = await runWorkflowCommand(
      `python3 "${scripts}/learner.py" ${logs.map(shellQuote).join(' ')} --json`,
    )
    extracted = JSON.parse(result.stdout)
  } catch {
    return []
  }
  if (!Array.isArray(extracted.candidates) || !extracted.candidates.length) return []
  await appendRunEvent('phase.started', LEARN_PHASE_ISSUE, 'Learn', {})
  await appendRunEvent('subagent.started', LEARN_PHASE_ISSUE, 'Learn', { role: 'learner' })
  const learned = await requestRole('learner', learnerPrompt(extracted), {
    label: 'learn', phase: 'Learn', model: A.models.learn ?? A.models.critic, cwd: A.repoRoot,
  })
  const candidates = learned && Array.isArray(learned.candidates) ? learned.candidates : extracted.candidates
  await appendRunEvent('subagent.stopped', LEARN_PHASE_ISSUE, 'Learn', { role: 'learner', result: { candidates } })
  await appendRunEvent('phase.finished', LEARN_PHASE_ISSUE, 'Learn', {})
  return candidates
}

const deliveries = results.filter(Boolean)
let integrationStopped = false
let cancelReason = null
for (const delivery of deliveries) {
  if (delivery.outcome !== 'accepted') continue
  if (A.unitId && A.runId && A.waitGate) {
    const stateRootArg = A.stateRoot ? ` --state-root "${A.stateRoot}"` : ''
    await runWorkflowCommand(`python3 "${scripts}/wait_gate.py" ${delivery.ref} --unit "${A.unitId}" --run "${A.runId}"${stateRootArg}`)
  }
  if (integrationStopped) {
    delivery.outcome = 'integration_pending'
    continue
  }
  const strategy = (A.policy && A.policy.delivery && A.policy.delivery.strategy) || 'branch-merge'
  if (strategy === 'pull-request') {
    const target = (A.policy && A.policy.git && A.policy.git.target) || 'main'
    try {
      await runWorkflowCommand(`gh pr view "${delivery.branch}" --json state -q .state`)
    } catch {
      await runWorkflowCommand(`git merge-base --is-ancestor "${delivery.branch}" "${target}"`)
    }
  } else if (A.isolate) {
    if (!delivery.branch) {
      delivery.outcome = 'integration_failed'
      integrationStopped = true
      cancelReason = { issue: delivery.ref, reason: 'integration_branch_missing' }
      continue
    }
    try {
      await runWorkflowCommand(`git merge --no-ff "${delivery.branch}" -m "gantry: integrate ${delivery.ref}"`)
    } catch {
      delivery.outcome = 'integration_failed'
      integrationStopped = true
      cancelReason = { issue: delivery.ref, reason: 'integration_merge_failed' }
      continue
    }
  }
  if (!await integrationGatePasses()) {
    delivery.outcome = 'integration_failed'
    integrationStopped = true
    cancelReason = { issue: delivery.ref, reason: 'integration_gate_failed' }
    continue
  }
  try {
    await runWorkflowCommand(`python3 "${scripts}/roadmap.py" done ${delivery.ref}`)
    await runWorkflowCommand(`git add -- ROADMAP.md "${delivery.issuePath}"`)
    await runWorkflowCommand(`git commit -m "gantry: complete ${delivery.ref}"`)
    delivery.outcome = 'done'
    await appendRunEvent('issue.done', delivery.ref, undefined, { worktree: delivery.worktree, strategy })
  } catch {
    delivery.outcome = 'integration_failed'
    integrationStopped = true
    cancelReason = { issue: delivery.ref, reason: 'integration_commit_failed' }
  }
}

// Post-integration dashboard check
if (typeof prompt === 'function' && !A.skipDashboardPrompt) {
  const postDashCmd = await runCommand(`python3 "${scripts}/dashboard.py" status --json`, { cwd: A.repoRoot })
  let postDashStatus = null
  if (postDashCmd && postDashCmd.exitCode === 0 && postDashCmd.stdout && postDashCmd.stdout.trim()) {
    try { postDashStatus = JSON.parse(postDashCmd.stdout) } catch (e) {}
  }
  if (postDashStatus && postDashStatus.running) {
    const askStop = await prompt('Integration complete. Would you like to shut down the background dashboard server (dashboard.py stop)? (yes/no)')
    if (askStop && askStop.toLowerCase().trim() === 'yes') {
      await runCommand(`python3 "${scripts}/dashboard.py" stop`, { cwd: A.repoRoot })
      log('Dashboard stopped.')
    }
  }
}

await appendRunEvent('round.finished', undefined, undefined, { round: A.round })
if (integrationStopped) {
  await appendRunEvent('run.cancelled', cancelReason && cancelReason.issue, undefined, {
    round: A.round, reason: cancelReason && cancelReason.reason,
  })
}
const hasPaused = deliveries.some(d => d.outcome === 'paused')
const candidates = (A.isLastRound && !hasPaused) ? await learn() : []
if (!integrationStopped && A.isLastRound && !hasPaused) {
  await appendRunEvent('run.finished', undefined, undefined, { round: A.round })
}
if (integrationStopped || (A.isLastRound && !hasPaused)) {
  await unmarkRun()
}
let prOffer = null
if (!integrationStopped && A.isLastRound && !hasPaused) {
  const completed = deliveries.filter(d => d.outcome === 'done')
  if (completed.length > 0) {
    const ghCheck = await runCommand('gh --version', { cwd: A.repoRoot })
    if (ghCheck && ghCheck.exitCode === 0 && typeof prompt === 'function') {
      const checkRoadmap = await runCommand(`python3 "${scripts}/roadmap.py" check`, { cwd: A.repoRoot })
      const checkFrontier = await runCommand(`python3 "${scripts}/frontier.py" --scope all --json`, { cwd: A.repoRoot })
      if ((!checkRoadmap || checkRoadmap.exitCode === 0) && (!checkFrontier || checkFrontier.exitCode === 0)) {
        const bodyLines = []
        for (const d of completed) {
          const accCheck = await runCommand(`python3 "${scripts}/acceptance.py" "${A.repoRoot}/${d.issuePath}" --json`)
          let texts = {}
          if (accCheck && accCheck.exitCode === 0) {
            try {
              const accPayload = JSON.parse(accCheck.stdout)
              if (Array.isArray(accPayload.criteria)) {
                for (const c of accPayload.criteria) {
                  texts[c.index] = c.text
                }
              }
            } catch (e) {}
          }
          const criteriaText = (d.verdict && d.verdict.criteria ? d.verdict.criteria : []).map(c => `- [x] ${texts[c.index] || 'Criterion'}: ${c.evidence}`).join('\\n')
          bodyLines.push(`## ${d.ref}\\n\\n${criteriaText}`)
        }
        const body = bodyLines.join('\\n\\n')
        const target = policy.git && policy.git.target ? policy.git.target : 'main'
        const answer = await prompt(`Open a draft pull request from ${A.branch} to ${target}?\\n\\nBody preview:\\n${body}\\n\\n(yes/no)`)
        if (answer && answer.toLowerCase().trim() === 'yes') {
          const pr = await runCommand(`gh pr create --draft --base ${shellQuote(target)} --head ${shellQuote(A.branch)} --title "Run delivery" --body ${shellQuote(body)}`, { cwd: A.repoRoot })
          if (pr && pr.exitCode === 0) {
            prOffer = { status: 'opened', target }
          } else {
            prOffer = { status: 'failed', target }
          }
        } else {
          prOffer = { status: 'declined', target }
        }
      } else {
         prOffer = { status: 'failed_checks', target: policy.git && policy.git.target ? policy.git.target : 'main' }
      }
    } else {
      prOffer = { status: 'unavailable', target: policy.git && policy.git.target ? policy.git.target : 'main' }
    }
  }
}
return {
  round: A.round,
  date: A.date,
  results: deliveries,
  caveman: cavemanState,
  nextRoundBlocked: hasPaused || integrationStopped,
  ...(hasPaused ? { pausedIssues: deliveries.filter(d => d.outcome === 'paused') } : {}),
  ...(A.isLastRound && !hasPaused ? { candidates, prOffer } : {}),
}
```

The Workflow returns `done` only after serial integration (when isolated), a passing post-integration
gate and `roadmap.py done`. `no_gates` is not a generic acceptance path: a future bootstrap contract must
explicitly supply and prove its exceptional checks before it can be modeled here.
