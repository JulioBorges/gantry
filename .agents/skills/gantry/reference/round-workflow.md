# Canonical round workflow

One round contains only Issues selected by `frontier.py` whose dependency readiness is satisfied. The
caller supplies `args.round`, `args.issues`, `args.models`, `args.branch`, `args.baseRef`,
`args.isolate`, `args.correctionBudget`, `args.skillDir`, `args.repoRoot`, effective `args.policy` and
rendered `args.paths`.
The host supplies its command runner as `runCommand(command, { cwd })`; integration cannot proceed
without it.

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
extraction finds nothing recurring, or no Run-log path is available, the phase is skipped. The Learner
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

async function roleSchema(role) {
  const result = await runWorkflowCommand(
    `python3 "${scripts}/result.py" --role "${role}" --schema`,
  )
  return JSON.parse(result.stdout)
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
  const native = A.structuredOutput === true
  const schema = native ? await roleSchema(role) : null
  const result = await agent(prompt, {
    ...options,
    ...(schema ? { schema } : {}),
  })
  if (await validRoleResult(role, result)) return result
  const retry = await agent(`${prompt}\nYour prior result was invalid. Return the complete ${role} result contract.`, {
    ...options,
    label: `${options.label}:retry`,
    ...(schema ? { schema } : {}),
  })
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

async function runWorkflowCommand(command) {
  const result = await runCommand(command, { cwd: A.repoRoot })
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
Never edit ROADMAP.md, Status, or criteria checkboxes. Commit small changes and leave a clean tree.
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
creep. Verify the Review findings were actually fixed. Do not edit.
Return complete only for gate-green, clean, fully evidenced work; otherwise ordered requiredFixes,
refutations, gateResult, gateFailures and decisionsForOperator as structured output.`
}

async function implement(issue, feedback, previous) {
  const assigned = await implementationLocation(issue, previous)
  if (!assigned) return null
  const options = {
    label: `implement:${issue.ref}`, phase: 'Implement', model: A.models.implement, cwd: assigned.worktree,
  }
  const result = await requestRole('implementer', implementPrompt(issue, feedback, assigned), options)
  return result && result.worktree === assigned.worktree && result.branch === assigned.branch ? result : null
}

const results = await pipeline(
  A.issues,
  issue => implement(issue, null, null),
  async (impl, issue) => {
    if (!impl) return null
    const review = await requestRole('reviewer', reviewPrompt(issue, impl), {
      label: `review:${issue.ref}`, phase: 'Review', model: A.models.review, cwd: location(impl),
    })
    if (!review) return { impl, reviewerFailed: true }
    const reviewed = review && review.blocking.length
      ? await implement(issue, { kind: 'review', items: review.blocking }, impl)
      : impl
    if (!reviewed) {
      return { impl: null, implementerFailed: true, failedImpl: impl, review, reviewFix: true }
    }
    return { impl: reviewed, review, reviewFix: Boolean(review && review.blocking.length) }
  },
  async (state, issue) => {
    if (!state) return { ref: issue.ref, outcome: 'implementer_failed' }
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
    let corrections = 0
    let accepted = false
    for (let attempt = 1; ; attempt += 1) {
      verdict = await requestRole('critic', criticPrompt(issue, impl, state.review, attempt), {
        label: `critic:${issue.ref}#${attempt}`, phase: 'Critic', model: A.models.critic, cwd: location(impl),
      })
      if (!verdict) {
        return {
          ref: issue.ref, issuePath: issue.path, outcome: 'critic_failed',
          worktree: impl.worktree, branch: impl.branch, commits: impl.commits,
          corrections, reviewFix: state.reviewFix, review: state.review, verdict: null,
          decisions: (impl.decisions) || [], blockers: impl.blockers || [],
        }
      }
      accepted = await criticAccepted(verdict, issue)
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
      corrections += 1
      impl = corrected
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
  const learned = await requestRole('learner', learnerPrompt(extracted), {
    label: 'learn', phase: 'Learn', model: A.models.learn ?? A.models.critic, cwd: A.repoRoot,
  })
  return learned && Array.isArray(learned.candidates) ? learned.candidates : extracted.candidates
}

const deliveries = results.filter(Boolean)
let integrationStopped = false
for (const delivery of deliveries) {
  if (delivery.outcome !== 'accepted') continue
  if (integrationStopped) {
    delivery.outcome = 'integration_pending'
    continue
  }
  if (A.isolate) {
    if (!delivery.branch) {
      delivery.outcome = 'integration_failed'
      integrationStopped = true
      continue
    }
    try {
      await runWorkflowCommand(`git merge --no-ff "${delivery.branch}" -m "gantry: integrate ${delivery.ref}"`)
    } catch {
      delivery.outcome = 'integration_failed'
      integrationStopped = true
      continue
    }
  }
  if (!await integrationGatePasses()) {
    delivery.outcome = 'integration_failed'
    integrationStopped = true
    continue
  }
  try {
    await runWorkflowCommand(`python3 "${scripts}/roadmap.py" done ${delivery.ref}`)
    await runWorkflowCommand(`git add -- ROADMAP.md "${delivery.issuePath}"`)
    await runWorkflowCommand(`git commit -m "gantry: complete ${delivery.ref}"`)
    delivery.outcome = 'done'
  } catch {
    delivery.outcome = 'integration_failed'
    integrationStopped = true
  }
}
const candidates = A.isLastRound ? await learn() : []
return { round: A.round, date: A.date, results: deliveries, ...(A.isLastRound ? { candidates } : {}) }
```

The Workflow returns `done` only after serial integration (when isolated), a passing post-integration
gate and `roadmap.py done`. `no_gates` is not a generic acceptance path: a future bootstrap contract must
explicitly supply and prove its exceptional checks before it can be modeled here.
