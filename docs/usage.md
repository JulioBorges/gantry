# Using Gantry

Gantry has two interfaces. Use the skills for normal work: they coordinate
agents, deterministic scripts, operator approvals, worktrees, and handoff as a
single Run. Use the Python CLI when you need one deterministic operation for
diagnostics, CI, or a custom integration.

## Via skills (recommended)

The examples below use Gantry's slash-command interface in the coding harness.
They are not shell commands.

### 1. Configure the repository

```text
/gantry-setup
```

Run setup once per repository. It inspects existing artifact locations,
templates, checks, Git policy, role defaults, and supported hooks. Review and
approve the complete proposed policy. Setup does not approve a Spec or start a
Run.

### 2. Turn a goal into a Spec and Issues

```text
/gantry-plan Add login via OTP
```

`/gantry-plan` explores the repository and requirements, writes the
`login-otp` Spec, prepares draft vertical Issues, checks their dependency graph
and context budgets, runs Plan Critic, and stops. Inspect the generated Spec,
criteria, non-goals, Issues, and blocker graph.

### 3. Approve the Spec and Issues

```text
I approve the login-otp Spec and the proposed Issues.
```

Approval transitions the proposed Issues from draft to ready-for-agent and
updates the roadmap. A material change to the approved Spec or breakdown
requires renewed approval.

### 4. Execute the approved Spec

```text
/gantry Implement the login-otp Spec
```

That single invocation starts the implementation Run. Gantry automatically
coordinates dependency rounds, TDD implementation, two-axis Review, fresh
adversarial Critic verification, bounded corrections, deterministic gates,
serial integration, roadmap updates, and final handoff. It stops only when a
human gate or explicit recovery decision is required. Draft pull requests and
cleanup remain separately authorized.

Once a Spec has been approved, `/gantry` also accepts these execution scopes:

| Scope | Meaning |
|---|---|
| `delivery-api` | All Issues belonging to one Spec |
| `delivery-api#01` | One Issue |
| `wave:1` | One roadmap wave |
| `frontier` | All currently ready Issues |
| `all` | All discovered Issues |

Use `/gantry-plan <goal>` for a new or unplanned goal. That keeps planning and
approval visibly separate from the implementation Run.

### 5. Observe Runs when useful

```text
/gantry-dashboard
```

The dashboard can be opened before or during execution. It observes Run logs;
it does not approve, retry, integrate, or mark Issues done.

## Via the Python CLI (advanced/manual)

The scripts under `.agents/skills/gantry/scripts/` are deterministic building
blocks. They answer specific workflow questions, but invoking them individually
does not reproduce a Gantry Run: no agent roles are coordinated, no operator
approval is inferred, and no draft pull request is opened.

Set a convenience path when Gantry is installed in the repository:

```bash
GANTRY_SKILL_DIR="$(pwd)/.agents/skills/gantry"
```

### Repository setup

Use the config writer only after reviewing the intended policy. The skill is
preferred because it presents each choice and trade-off conversationally.

```bash
python3 "$GANTRY_SKILL_DIR/scripts/setup.py" --harness codex --verify-auth
```

### Spec and readiness checks

```bash
python3 "$GANTRY_SKILL_DIR/scripts/spec.py" --check .scratch/delivery-api/spec.md --json
python3 "$GANTRY_SKILL_DIR/scripts/frontier.py" --scope delivery-api --json
python3 "$GANTRY_SKILL_DIR/scripts/roadmap.py" check
```

`spec.py` checks structure, not semantic quality or planning approval.
`frontier.py` computes dependency readiness from authoritative Issue state.
`roadmap.py check` detects drift; it does not decide that incomplete work is
done.

### Acceptance and quality gates

```bash
python3 "$GANTRY_SKILL_DIR/scripts/acceptance.py" delivery-api#01 --json
python3 "$GANTRY_SKILL_DIR/scripts/gates.py" --run --json
```

These commands provide deterministic evidence for the Reviewer and Critic. A
green command by itself does not replace independent Critic acceptance or
authorize integration.

### Roadmap updates

After every acceptance criterion is met, Critic acceptance exists, integration
gates pass, and the worktree is clean, the orchestrator records completion with:

```bash
python3 "$GANTRY_SKILL_DIR/scripts/roadmap.py" done delivery-api#01
python3 "$GANTRY_SKILL_DIR/scripts/roadmap.py" check
```

Do not edit Issue status, acceptance checkboxes, or `ROADMAP.md` by hand.

### Dashboard and cleanup planning

```bash
python3 "$GANTRY_SKILL_DIR/scripts/dashboard.py" start --daemon
python3 "$GANTRY_SKILL_DIR/scripts/dashboard.py" status --json
python3 "$GANTRY_SKILL_DIR/scripts/cleanup.py" --plan --json
```

Cleanup execution requires explicit authorization of the unchanged generated
plan. Consult each command's `--help` before embedding it into automation.
