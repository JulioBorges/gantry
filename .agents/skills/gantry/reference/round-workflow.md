# Canonical round workflow

One round contains only Issues selected by `frontier.py` whose dependency readiness is satisfied. The
caller supplies `args.round`, `args.issues`, `args.models`, `args.branch`, `args.baseRef`,
`args.isolate`, `args.correctionBudget`, `args.skillDir`, `args.repoRoot`, effective `args.policy` and
rendered `args.paths`.
The host supplies its command runner as `runCommand(command, { cwd })`; integration cannot proceed
without it.

```
implement (TDD) → review (standards + Spec) → one review fix pass
→ adversarial Critic → correction implementer ⇄ Critic (at most correctionBudget)
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
Refutations generate ordered required fixes and consume one correction attempt; budget exhaustion leaves
the Issue refuted and its worktree retained.

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
const budget = A.correctionBudget ?? policy.budget.corrections
const IMPL_SCHEMA = {
  type: 'object',
  properties: {
    worktree: { type: 'string' }, branch: { type: 'string' },
    commits: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' }, testsAdded: { type: 'array', items: { type: 'string' } },
    gatesResult: { type: 'string' }, decisions: { type: 'array', items: { type: 'string' } },
    blockers: { type: 'array', items: { type: 'string' } },
  },
  required: ['worktree', 'branch', 'commits', 'summary', 'gatesResult'],
}
const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    blocking: { type: 'array', items: { type: 'object' } },
    nonBlocking: { type: 'array', items: { type: 'object' } },
    summary: { type: 'string' },
  },
  required: ['blocking', 'nonBlocking', 'summary'],
}
const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    complete: { type: 'boolean' }, criteria: { type: 'array', items: { type: 'object' } },
    gatesVerdict: { type: 'string', enum: ['pass', 'fail', 'no_gates', 'not_run'] },
    gateResult: { type: 'object' },
    gateFailures: { type: 'array', items: { type: 'string' } },
    refutations: { type: 'array', items: { type: 'string' } },
    requiredFixes: { type: 'array', items: { type: 'string' } },
    decisionsForOperator: { type: 'array', items: { type: 'string' } },
  },
  required: ['complete', 'criteria', 'gatesVerdict', 'gateResult', 'gateFailures', 'refutations', 'requiredFixes'],
}

function location(impl) {
  return impl && impl.worktree ? impl.worktree : A.repoRoot
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

function implementPrompt(issue, feedback, previous) {
  const work = previous
    ? `Continue in ${previous.worktree} on ${previous.branch}.`
    : A.isolate
      ? 'You are in this Issue’s dedicated git worktree and branch. Verify pwd and git branch --show-current.'
      : `Work in ${A.repoRoot} on ${A.branch}; verify the current branch and never switch it.`
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
against ${A.baseRef}. Default to complete=false when uncertain; never trust the Implementer.
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
  const options = {
    label: `implement:${issue.ref}`, phase: 'Implement', schema: IMPL_SCHEMA, model: A.models.implement,
  }
  if (A.isolate && !previous) options.isolation = 'worktree'
  const result = await agent(implementPrompt(issue, feedback, previous), options)
  if (!result) return previous || null
  if (previous && !result.worktree) result.worktree = previous.worktree
  if (previous && !result.branch) result.branch = previous.branch
  return result
}

const results = await pipeline(
  A.issues,
  issue => implement(issue, null, null),
  async (impl, issue) => {
    if (!impl) return null
    const review = await agent(reviewPrompt(issue, impl), {
      label: `review:${issue.ref}`, phase: 'Review', schema: REVIEW_SCHEMA, model: A.models.review,
    })
    const reviewed = review && review.blocking.length
      ? await implement(issue, { kind: 'review', items: review.blocking }, impl)
      : impl
    return { impl: reviewed, review, reviewFix: Boolean(review && review.blocking.length) }
  },
  async (state, issue) => {
    if (!state || !state.impl) return { ref: issue.ref, outcome: 'implementer_failed' }
    let impl = state.impl
    let verdict = null
    let corrections = 0
    let accepted = false
    for (let attempt = 1; ; attempt += 1) {
      verdict = await agent(criticPrompt(issue, impl, state.review, attempt), {
        label: `critic:${issue.ref}#${attempt}`, phase: 'Critic', schema: CRITIC_SCHEMA, model: A.models.critic,
      })
      accepted = await criticAccepted(verdict, issue)
      if (!verdict || accepted || corrections >= budget) break
      corrections += 1
      impl = await implement(issue, { kind: 'critic', items: verdict.requiredFixes }, impl)
      if (!impl) break
    }
    return {
      ref: issue.ref,
      issuePath: issue.path,
      outcome: accepted ? 'accepted' : (verdict ? 'refuted' : 'critic_failed'),
      worktree: impl && impl.worktree, branch: impl && impl.branch, commits: impl && impl.commits,
      corrections, reviewFix: state.reviewFix, review: state.review, verdict,
      decisions: [...((impl && impl.decisions) || []), ...((verdict && verdict.decisionsForOperator) || [])],
      blockers: (impl && impl.blockers) || [],
    }
  },
)

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
return { round: A.round, date: A.date, results: deliveries }
```

The Workflow returns `done` only after serial integration (when isolated), a passing post-integration
gate and `roadmap.py done`. `no_gates` is not a generic acceptance path: a future bootstrap contract must
explicitly supply and prove its exceptional checks before it can be modeled here.
