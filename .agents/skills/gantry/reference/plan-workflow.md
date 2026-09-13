# Canonical planning workflow

Use this workflow only for an unplanned Spec, an Issue with no criteria, or an approved free-text goal.
The caller resolves and supplies `args.skillDir`, `args.repoRoot`, effective `args.policy`, rendered
`args.paths`, and `args.models.plan` / `args.models.critic`; this file assumes no repository location.
For the approval transition, the host supplies its command runner as `runCommand(command, { cwd })`.
`args.operatorApproved` is `true` only after the host has obtained explicit operator approval; an omitted
or any other value leaves the plan awaiting approval.

## Roles and sequence

1. `spec.py --check` validates the Spec structurally (required sections, order, placeholders,
   scenarios). It is objective and pass/fail; it does not approve planning.
2. The read-only Requirement Critic (Critic model) reads the Spec and assesses ambiguity, coherence,
   verifiability and non-goal coverage. A blocking finding stops the run before any research or Issue
   is written, quotes the finding, and tells the operator to amend the Spec; the Critic never edits it
   and does not approve planning either.
3. Run research in parallel: repository conventions, the Spec and settled decisions, and an exemplar Issue.
4. The Planner writes vertical-slice Issues in the effective issue template, each with `Status: draft`,
   observable acceptance criteria and real non-cyclic blockers.
5. The Plan Critic attempts to refute granularity, coverage, criterion observability, contract ownership,
   format and `frontier.py --scope <slug> --include-parked`.
6. Allow exactly one Planner revision when refuted, then present the result and **stop for explicit operator
   approval**.

Structural validation and Requirement Review are both read-only checks that a Spec must clear before
research and slicing; neither one, alone or together, approves planning. Every Requirement Critic finding,
like every other generated artifact and operator report, is in English.

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

async function validateSpecBeforePlanning() {
  if (t.kind === 'goal') return null
  const specPath = t.specPath || paths.specPath
  const check = await runCommand(`python3 "${scripts}/spec.py" --check "${specPath}" --json`, { cwd: A.repoRoot })
  let findings = {}
  try {
    findings = JSON.parse(check.stdout || '{}')
  } catch {
    findings = { error: 'spec.py did not return JSON findings' }
  }
  if (check && check.exitCode === 0 && findings.valid === true) return findings
  const details = ['missing', 'out_of_order', 'placeholders', 'malformed_scenarios']
    .flatMap((key) => findings[key] || [])
    .map((item) => typeof item === 'string' ? item : JSON.stringify(item))
  return {
    ...findings,
    valid: false,
    report: `Spec structural validation failed: ${details.join('; ') || findings.error || check.stderr || 'unknown finding'}`,
  }
}

function requirementCriticPrompt(specPath) {
  return `You are the read-only Requirement Critic reviewing the Spec at ${specPath} before ${targetText}
is sliced into Issues. Read the whole Spec. Assess:
- ambiguity: every Definition of Done item and acceptance criterion must state a verifiable threshold,
  not a vague quality word ("fast", "robust", "user-friendly") with no measurable test;
- coherence: no internal contradiction between the Blueprint, Contract and Out of Scope sections;
- verifiability: a human or a script must be able to check each item as met or not met;
- non-goal coverage: nothing the Out of Scope section excludes is silently required elsewhere.
Default to a blocking finding when uncertain. Never edit the Spec.
Return structured output: a \`blocking\` array of {quote, reason} for findings that must stop planning
before slicing, and a \`findings\` array of {quote, reason} for non-blocking observations. An empty
\`blocking\` array means the Spec may proceed to research and slicing.`
}

async function roleSchema(role) {
  const result = await runCommand(
    `python3 "${scripts}/result.py" --role "${role}" --schema`,
    { cwd: A.repoRoot },
  )
  if (!result || result.exitCode !== 0) throw new Error(`could not load ${role} result schema`)
  return JSON.parse(result.stdout)
}

async function validRoleResult(role, result) {
  if (!result) return false
  if (A.structuredOutput === true) return true
  if (typeof runCommand !== 'function') return true
  const validation = await runCommand(
    `python3 "${scripts}/result.py" --role "${role}" --json`,
    { cwd: A.repoRoot, input: JSON.stringify(result) },
  )
  return Boolean(validation && validation.exitCode === 0)
}

async function requestRole(role, prompt, options) {
  const native = A.structuredOutput === true
  const result = await agent(prompt, {
    ...options,
    ...(native ? { schema: await roleSchema(role) } : {}),
  })
  if (await validRoleResult(role, result)) return result
  const retry = await agent(`${prompt}\nYour prior result was invalid. Return the complete ${role} result contract.`, {
    ...options,
    label: `${options.label}:retry`,
    ...(native ? { schema: await roleSchema(role) } : {}),
  })
  return (await validRoleResult(role, retry)) ? retry : null
}

function shellQuote(value) {
  return `"${String(value).replace(/(["\\$`])/g, '\\$1')}"`
}

async function measureBudgets(plan) {
  if (!plan || !Array.isArray(plan.issues) || typeof runCommand !== 'function') return []
  const measurements = []
  for (const [index, issue] of plan.issues.entries()) {
    const ref = issue && typeof issue.ref === 'string' && issue.ref.trim()
      ? issue.ref.trim()
      : `issues[${index}]`
    if (!issue || typeof issue.path !== 'string' || !issue.path.trim()) {
      throw new Error(`planned Issue ${ref} has no valid path`)
    }
    const command = `python3 ${shellQuote(`${scripts}/budget.py`)} ${shellQuote(issue.path.trim())} --model ${shellQuote(A.models.plan)} --json`
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

phase('Validation')
const structuralValidation = await validateSpecBeforePlanning()
if (structuralValidation && !structuralValidation.valid) {
  return {
    target: t, structuralValidation, plan: null, critique: null,
    awaitingOperatorApproval: true, approved: false,
    blocked: 'spec_structural_validation_failed',
    report: structuralValidation.report,
  }
}

phase('Requirement Review')
let requirementReview = null
if (t.kind !== 'goal') {
  requirementReview = await agent(requirementCriticPrompt(t.specPath || paths.specPath), {
    label: 'requirement-critic', phase: 'Requirement Review', model: A.models.critic,
  })
  const blocking = Array.isArray(requirementReview && requirementReview.blocking) ? requirementReview.blocking : []
  if (blocking.length) {
    const quotes = blocking
      .map((finding) => (finding && finding.quote) ? `"${finding.quote}" (${finding.reason || 'no reason given'})` : JSON.stringify(finding))
      .join('; ')
    return {
      target: t, structuralValidation, requirementReview, plan: null, critique: null,
      awaitingOperatorApproval: true, approved: false,
      blocked: 'requirement_review_failed',
      report: `Requirement Critic found a blocking finding: ${quotes}. Amend the Spec and rerun planning; `
        + 'structural validation and Requirement Review do not approve planning — only the operator does.',
    }
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
let plan = await requestRole('planner', planPrompt(null), {
  label: 'plan', phase: 'Plan', model: A.models.plan,
})
if (!plan) {
  return {
    target: t, plan: null, critique: null,
    protocolFailure: { phase: 'Plan', role: 'planner' },
    awaitingOperatorApproval: false, approved: false,
  }
}
phase('Critique')
let measurements
try {
  measurements = await measureBudgets(plan)
} catch (error) {
  return {
    target: t, plan, critique: null,
    budgetFailure: String(error.message || error),
    awaitingOperatorApproval: false, approved: false,
  }
}
let critique = await requestRole('plan-critic', critiquePrompt(plan, measurements), {
  label: 'critique', phase: 'Critique', model: A.models.critic,
})
if (!critique) {
  return {
    target: t, plan, critique: null,
    protocolFailure: { phase: 'Critique', role: 'plan-critic' },
    awaitingOperatorApproval: false, approved: false,
  }
}
critique = applyBudgetRefutations(critique, measurements)
if (!critique.acceptable) {
  log(`plan refuted: ${critique.problems.length} problem(s) — one revision pass`)
  const revisedPlan = await requestRole('planner', planPrompt(critique.problems), {
    label: 'plan:revise', phase: 'Plan', model: A.models.plan,
  })
  if (!revisedPlan) {
    return {
      target: t, plan, critique,
      protocolFailure: { phase: 'Plan', role: 'planner' },
      awaitingOperatorApproval: false, approved: false,
    }
  }
  plan = revisedPlan
  try {
    measurements = await measureBudgets(plan)
  } catch (error) {
    return {
      target: t, plan, critique: null,
      budgetFailure: String(error.message || error),
      awaitingOperatorApproval: false, approved: false,
    }
  }
  const revisedCritique = await requestRole('plan-critic', critiquePrompt(plan, measurements), {
    label: 'critique:2', phase: 'Critique', model: A.models.critic,
  })
  if (!revisedCritique) {
    return {
      target: t, plan, critique: null,
      protocolFailure: { phase: 'Critique', role: 'plan-critic' },
      awaitingOperatorApproval: false, approved: false,
    }
  }
  critique = applyBudgetRefutations(revisedCritique, measurements)
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
return { target: t, structuralValidation, requirementReview, plan, critique, awaitingOperatorApproval: !approved, approved }
```
