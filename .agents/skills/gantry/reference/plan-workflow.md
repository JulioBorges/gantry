# Canonical planning workflow

Use this workflow only for an unplanned Spec, an Issue with no criteria, or an approved free-text goal.
The caller resolves and supplies `args.skillDir`, `args.repoRoot`, effective `args.policy`, rendered
`args.paths`, and `args.models.plan` / `args.models.critic`; this file assumes no repository location.
For the approval transition, the host supplies its command runner as `runCommand(command, { cwd })`.
`args.operatorApproved` is `true` only after the host has obtained explicit operator approval; an omitted
or any other value leaves the plan awaiting approval.

## Roles and sequence

1. Run research in parallel: repository conventions, the Spec and settled decisions, and an exemplar Issue.
2. The Planner writes vertical-slice Issues in the effective issue template, each with `Status: draft`,
   observable acceptance criteria and real non-cyclic blockers.
3. The Plan Critic attempts to refute granularity, coverage, criterion observability, contract ownership,
   format and `frontier.py --scope <slug> --include-parked`.
4. Allow exactly one Planner revision when refuted, then present the result and **stop for explicit operator
   approval**.

## Planner contract

The Planner returns `filesWritten`, `issues` (`ref`, `path`, `title`, `criteriaCount`, `blockedBy`),
`roadmapAdditions` and `openDecisions`. It must:

- write only draft Issue files under `args.paths.issueDir`;
- use `args.paths.specPath`, `decisions`, `context`, `adrs`, `issueTracker` and `exemplarIssue` rather
  than inferred paths;
- when an Issue needs additional initial-context files, put them under `## What to build` in a
  `### Files to read` section. Each list item must be exactly one repository-relative path in a code
  span (`- \`path/to/file\``); prose, code spans outside that list and paths under another heading are
  not declarations and are not counted by `budget.py`;
- never write `ROADMAP.md`, set an Issue to `ready-for-agent`, or implement any issue;
- use English for every artifact.

## Approval transition

After, and only after, an operator approves the exact breakdown, the host harness calls:

```sh
python3 "$skillDir/scripts/roadmap.py" status <ref> ready-for-agent
python3 "$skillDir/scripts/roadmap.py" waves
python3 "$skillDir/scripts/roadmap.py" check
```

The last command must exit 0 before the Run recomputes the frontier. Planning approval does not permit
silent issue additions, splits, merges or dependency changes.

## Executable Claude Code Workflow

The following is the executable Workflow script. Other harnesses execute the same prompt functions and
phase order manually; they do not substitute isolated script calls for the workflow transitions.

```js
export const meta = {
  name: 'gantry-plan',
  description: 'Gantry planning: research, draft Issues, adversarial critique, operator stop',
  phases: [
    { title: 'Research', detail: 'repository, Spec, decisions and Issue format' },
    { title: 'Plan', detail: 'write draft vertical-slice Issues' },
    { title: 'Critique', detail: 'refute the draft before approval' },
  ],
}

const A = args
const scripts = `${A.skillDir}/scripts`
const t = A.target
const paths = A.paths
const policy = A.policy
const targetText = t.kind === 'goal' ? `the goal "${t.goal}" (new slug: ${t.slug})`
  : t.kind === 'issue' ? `the Issue at ${t.issuePath} (Spec ${t.specPath})`
  : `the Spec at ${t.specPath} (slug ${t.slug})`

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    filesWritten: { type: 'array', items: { type: 'string' } },
    issues: { type: 'array', items: { type: 'object' } },
    roadmapAdditions: { type: 'array', items: { type: 'string' } },
    openDecisions: { type: 'array', items: { type: 'string' } },
  },
  required: ['filesWritten', 'issues', 'roadmapAdditions'],
}
const CRITIQUE_SCHEMA = {
  type: 'object',
  properties: {
    acceptable: { type: 'boolean' },
    problems: { type: 'array', items: { type: 'object' } },
    frontierErrors: { type: 'array', items: { type: 'string' } },
    budgets: { type: 'array', items: { type: 'object' } },
  },
  required: ['acceptable', 'problems', 'frontierErrors'],
}

function shellQuote(value) {
  return `"${String(value).replace(/(["\\$`])/g, '\\$1')}"`
}

async function measureBudgets(plan) {
  if (!plan || !Array.isArray(plan.issues) || typeof runCommand !== 'function') return []
  const measurements = []
  for (const issue of plan.issues) {
    if (!issue || typeof issue.path !== 'string') continue
    const command = `python3 ${shellQuote(`${scripts}/budget.py`)} ${shellQuote(issue.path)} --model ${shellQuote(A.models.plan)} --json`
    const result = await runCommand(command, { cwd: A.repoRoot })
    if (!result || ![0, 1].includes(result.exitCode)) {
      throw new Error(`context budget command failed: ${command}`)
    }
    let payload
    try {
      payload = JSON.parse(result.stdout)
    } catch {
      throw new Error(`context budget command returned invalid JSON: ${command}`)
    }
    if (!payload || typeof payload !== 'object' || typeof payload.error === 'string' ||
        !Number.isFinite(payload.estimatedTokens) || !Number.isFinite(payload.contextWindow) ||
        !Number.isFinite(payload.contextShare) || !Number.isFinite(payload.budgetTokens) ||
        typeof payload.overBudget !== 'boolean') {
      throw new Error(`context budget configuration is invalid: ${command}`)
    }
    measurements.push(payload)
  }
  return measurements
}

function applyBudgetRefutations(critique, measurements) {
  const overBudget = measurements.filter(measurement => measurement.overBudget)
  if (!overBudget.length) return { ...critique, budgets: measurements }
  const problems = Array.isArray(critique && critique.problems) ? critique.problems : []
  const refutations = overBudget.map(measurement => ({
    problem: `Initial Context Budget exceeded for ${measurement.issue}: ${measurement.estimatedTokens} estimated tokens exceeds ${measurement.budgetTokens} tokens (${measurement.contextShare} of ${measurement.contextWindow}).`,
    fix: 'Reduce the Issue initial package or split the Issue before requesting approval.',
  }))
  return {
    ...(critique || {}),
    acceptable: false,
    problems: [...problems, ...refutations],
    frontierErrors: Array.isArray(critique && critique.frontierErrors) ? critique.frontierErrors : [],
    budgets: measurements,
  }
}

function planPrompt(feedback) {
  return `You are the Planner for ${targetText} in ${A.repoRoot}.

Research:
${research.join('\n\n---\n\n')}

Write only draft Issue files under ${paths.issueDir}/NN-<slug>.md, using ${paths.exemplarIssue} and
${paths.issueTracker}. Read ${paths.specPath}, ${paths.decisions}, ${paths.context} and ${paths.adrs}.
Every Issue is a demonstrable vertical slice with observable checkbox criteria and real, acyclic
\`## Blocked by\` refs. Use \`Status: draft\`, the rendered effective paths, and English artifacts.
When additional initial-context files are needed, declare them only under \`## What to build\` as
\`### Files to read\`, using list items exactly in the form \`- \`path/to/file\`\` with
repository-relative paths. \`budget.py\` counts only those list items, not prose, incidental code spans,
or paths under another heading.
The effective Git policy is target \`${policy.git.target}\`, prefix \`${policy.git.prefix}\`.
${t.kind === 'goal' ? `First draft ${paths.specPath} in the existing Spec format.` : ''}
${t.kind === 'issue' ? `Rewrite only ${t.issuePath}; preserve its number and slug.` : ''}
Never write ROADMAP.md or change any Issue to ready-for-agent. Return filesWritten, issues,
roadmapAdditions and openDecisions as structured output.
${feedback ? `Address every previous critic finding:\n${feedback.map((item, index) => `${index + 1}. ${item.problem} → ${item.fix}`).join('\n')}` : ''}`
}

function critiquePrompt(plan, measurements) {
  return `You are the adversarial Plan Critic for ${targetText}. Default to acceptable=false when uncertain.
Read every file in: ${plan.filesWritten.join(', ') || '(none)'}.
Refute non-vertical slices, unobservable criteria, invented or re-owned contracts, invalid format or
dependencies, and incomplete Spec coverage. Run:
\`python3 ${scripts}/frontier.py --scope ${t.slug} --include-parked --json\`
and report every graph error. The deterministic context-budget measurements are:
${JSON.stringify(measurements)}
Every entry with \`overBudget: true\` is a required numeric refutation: quote its \`estimatedTokens\`,
\`budgetTokens\`, \`contextShare\` and \`contextWindow\`, and set \`acceptable: false\`. Confirm every new
Issue remains \`Status: draft\`; neither ROADMAP.md nor ready-for-agent state may be written before explicit
operator approval. Do not edit files. Return acceptable, problems (with actionable fixes), frontierErrors
and budgets as structured output.`
}

phase('Research')
const research = await parallel([
  () => agent(`Survey ${A.repoRoot}: conventions, current code/tests, ${paths.context}, and ${paths.adrs}.
Return facts and paths for the Planner.`, { label: 'research:codebase', phase: 'Research', model: A.models.plan }),
  () => agent(`Read ${t.specPath || paths.specPath}, ${paths.decisions}, and the relevant repository documents.
Return owned and consumed contracts, settled decisions, and the testing seam.`, { label: 'research:spec', phase: 'Research', model: A.models.plan }),
  () => agent(`Read ${paths.exemplarIssue} and ${paths.issueTracker}. Run
\`python3 ${scripts}/frontier.py --scope frontier --json\`. Return the exact Issue format and frontier facts.`,
    { label: 'research:format', phase: 'Research', model: A.models.plan }),
])

phase('Plan')
let plan = await agent(planPrompt(null), {
  label: 'plan', phase: 'Plan', schema: PLAN_SCHEMA, model: A.models.plan,
})
phase('Critique')
let measurements = await measureBudgets(plan)
let critique = plan && await agent(critiquePrompt(plan, measurements), {
  label: 'critique', phase: 'Critique', schema: CRITIQUE_SCHEMA, model: A.models.critic,
})
critique = applyBudgetRefutations(critique, measurements)
if (plan && critique && !critique.acceptable) {
  log(`plan refuted: ${critique.problems.length} problem(s) — one revision pass`)
  plan = await agent(planPrompt(critique.problems), {
    label: 'plan:revise', phase: 'Plan', schema: PLAN_SCHEMA, model: A.models.plan,
  }) || plan
  measurements = await measureBudgets(plan)
  critique = await agent(critiquePrompt(plan, measurements), {
    label: 'critique:2', phase: 'Critique', schema: CRITIQUE_SCHEMA, model: A.models.critic,
  }) || critique
  critique = applyBudgetRefutations(critique, measurements)
}

async function runApprovalCommand(command) {
  const result = await runCommand(command, { cwd: A.repoRoot })
  if (!result || result.exitCode !== 0) {
    throw new Error(`planning approval transition failed: ${command}`)
  }
  return result
}

async function approvePlan() {
  if (A.operatorApproved !== true || !plan || !critique || !critique.acceptable) return false
  for (const issue of plan.issues) {
    await runApprovalCommand(`python3 "${scripts}/roadmap.py" status ${issue.ref} ready-for-agent`)
  }
  await runApprovalCommand(`python3 "${scripts}/roadmap.py" waves`)
  await runApprovalCommand(`python3 "${scripts}/roadmap.py" check`)
  return true
}

const approved = await approvePlan()
return { target: t, plan, critique, awaitingOperatorApproval: !approved, approved }
```
