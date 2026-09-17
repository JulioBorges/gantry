export type Locale = 'en' | 'pt-br';

export interface StageTranslation {
  name: string;
  shortName: string;
  scriptDescription: string;
  scriptInvariants: string[];
  agentName: string;
  agentModel: string;
  agentResponsibilities: string[];
  terminalPrompt: string;
  terminalCommand: string;
  terminalLines: Array<{
    type: 'cmd' | 'info' | 'success' | 'warn' | 'dim' | 'json';
    text: string;
  }>;
}

export interface Dictionary {
  nav: {
    pipeline: string;
    skills: string;
    harnesses: string;
    github: string;
    version: string;
  };
  hero: {
    systemStrip: string;
    badgeStatus: string;
    badgeHarness: string;
    badgeLicense: string;
    badgeAiSlop: string;
    kicker: string;
    titleHarness: string;
    titleAgentic: string;
    tagline: string;
    valueProp: string;
    craneTitle: string;
    craneLoad: string;
    metricArchLabel: string;
    metricArchVal: string;
    metricVerifLabel: string;
    metricVerifVal: string;
    metricGatesLabel: string;
    metricGatesVal: string;
    metricOperatorLabel: string;
    metricOperatorVal: string;
  };
  install: {
    quickInstallTitle: string;
    statusVerified: string;
    copy: string;
    copied: string;
    altSetupLabel: string;
    harnessDescriptions: {
      claude: string;
      opencode: string;
      codex: string;
      antigravity: string;
      cursor: string;
    };
  };
  simulator: {
    headerTitle: string;
    progressLabel: string;
    stageLabel: string;
    ofStages: string;
    phaseDetails: string;
    scriptInvariantsTitle: string;
    agentRoleTitle: string;
    responsibilitiesLabel: string;
    modelLabel: string;
    adversarialBadge: string;
    cooperativeBadge: string;
    terminalStreamTitle: string;
    terminalExecTag: string;
    jsonLogTitle: string;
    prevStageBtn: string;
    nextStageBtn: string;
    stages: Record<string, StageTranslation>;
  };
  problemSolution: {
    tag: string;
    title: string;
    subtitle: string;
    thesisTag: string;
    thesisQuote: string;
    thesisDesc: string;
    thesisAuthorityLabel: string;
    thesisAuthorityVal: string;
    pitfall1Tag: string;
    pitfall1Category: string;
    pitfall1Title: string;
    pitfall1Desc: string;
    gantry1Title: string;
    gantry1Desc: string;
    pitfall2Tag: string;
    pitfall2Category: string;
    pitfall2Title: string;
    pitfall2Desc: string;
    gantry2Title: string;
    gantry2Desc: string;
    pitfall3Tag: string;
    pitfall3Category: string;
    pitfall3Title: string;
    pitfall3Desc: string;
    gantry3Title: string;
    gantry3Desc: string;
    pitfall4Tag: string;
    pitfall4Category: string;
    pitfall4Title: string;
    pitfall4Desc: string;
    gantry4Title: string;
    gantry4Desc: string;
  };
  skills: {
    tag: string;
    title: string;
    badge: string;
    subtitle: string;
    triggersLabel: string;
    viewSpec: string;
    gantryTitle: string;
    gantryBadge: string;
    gantryDesc: string;
    gantryBullet1Title: string;
    gantryBullet1Desc: string;
    gantryBullet2Title: string;
    gantryBullet2Desc: string;
    gantryBullet3Title: string;
    gantryBullet3Desc: string;
    setupTitle: string;
    setupBadge: string;
    setupDesc: string;
    setupBullet1Title: string;
    setupBullet1Desc: string;
    setupBullet2Title: string;
    setupBullet2Desc: string;
    setupBullet3Title: string;
    setupBullet3Desc: string;
    dashboardTitle: string;
    dashboardBadge: string;
    dashboardDesc: string;
    dashboardBullet1Title: string;
    dashboardBullet1Desc: string;
    dashboardBullet2Title: string;
    dashboardBullet2Desc: string;
    dashboardBullet3Title: string;
    dashboardBullet3Desc: string;
  };
  matrix: {
    tag: string;
    title: string;
    badge: string;
    subtitle: string;
    tierRefTitle: string;
    tierRefBadge: string;
    tierRefDesc: string;
    tierSupTitle: string;
    tierSupBadge: string;
    tierSupDesc: string;
    tierCompTitle: string;
    tierCompBadge: string;
    tierCompDesc: string;
    colHarness: string;
    colTier: string;
    colHooks: string;
    colRoles: string;
    colWorktrees: string;
    colStructured: string;
    colEvidence: string;
    claudeNotes: string;
    opencodeNotes: string;
    codexNotes: string;
    antigravityNotes: string;
    cursorNotes: string;
  };
  footer: {
    rigTitle: string;
    license: string;
    verification: string;
    operator: string;
  };
}

export const translations: Record<Locale, Dictionary> = {
  en: {
    nav: {
      pipeline: 'PIPELINE',
      skills: 'SKILLS',
      harnesses: 'HARNESSES',
      github: 'GITHUB',
      version: 'v1.0.6 [STANDBY]',
    },
    hero: {
      systemStrip: 'SYSTEM RIG // GANTRY CORE ONLINE',
      badgeStatus: 'STATUS: SPEC-VERIFIED',
      badgeHarness: 'HARNESS-NEUTRAL',
      badgeLicense: 'APACHE-2.0',
      badgeAiSlop: 'ZERO AI-SLOP',
      kicker: 'THE AGENTIC SDLC SKILL PACK',
      titleHarness: 'Harness-Neutral',
      titleAgentic: 'Agentic SDLC',
      tagline: 'Turn an approved Spec into verified software deliveries inside your coding harness.',
      valueProp:
        'Gantry is a skill pack, not an execution engine. Workflow scripts decide readiness, acceptance, gates, and roadmap state; agents plan, implement, review, and refute; the operator holds approval authority.',
      craneTitle: 'GANTRY CRANE // RIG MK-IV',
      craneLoad: 'LOAD: SPEC → VERIFIED',
      metricArchLabel: 'Architecture',
      metricArchVal: 'Skill Pack',
      metricVerifLabel: 'Verification',
      metricVerifVal: 'Adversarial Critic',
      metricGatesLabel: 'Quality Gates',
      metricGatesVal: 'RFC 6901 Differential',
      metricOperatorLabel: 'Operator In Loop',
      metricOperatorVal: 'Approval Authority',
    },
    install: {
      quickInstallTitle: 'QUICK INSTALL // HARNESS RUNTIME',
      statusVerified: 'STATUS: VERIFIED',
      copy: 'COPY',
      copied: 'COPIED!',
      altSetupLabel: 'Alternative CLI setup:',
      harnessDescriptions: {
        claude: 'Reference tier. Native settings, hooks guard, and multi-role subagents.',
        opencode: 'Compatible tier. Plugin hooks wiring and per-role subagent execution.',
        codex: 'Supported tier. Direct process runner and independent Critic verification.',
        antigravity: 'Supported tier. Hook guard integration via .agents/hooks.json and agy execution.',
        cursor: 'Compatible tier. Rules and commands integration for Cursor composer workflows.',
      },
    },
    simulator: {
      headerTitle: 'PIPELINE SIMULATOR // DETERMINISTIC SDLC RIG',
      progressLabel: 'PROGRESS:',
      stageLabel: 'STAGE',
      ofStages: '06',
      phaseDetails: 'PHASE DETAILS',
      scriptInvariantsTitle: 'DETERMINISTIC SCRIPT INVARIANTS',
      agentRoleTitle: 'AGENT ROLE',
      responsibilitiesLabel: 'RESPONSIBILITIES:',
      modelLabel: 'MODEL:',
      adversarialBadge: 'ADVERSARIAL',
      cooperativeBadge: 'COOPERATIVE',
      terminalStreamTitle: 'DETERMINISTIC TERMINAL STREAM',
      terminalExecTag: 'EXEC: REAL COMMAND TAIL',
      jsonLogTitle: 'STRUCTURED RUN LOG EVENT (RFC 6901 / JSONL)',
      prevStageBtn: 'PREVIOUS PHASE',
      nextStageBtn: 'NEXT PHASE',
      stages: {
        spec: {
          name: 'Spec & Requirement Critic',
          shortName: '01. Spec & Critic',
          scriptDescription: 'Validates structural integrity of living spec before any slicing or planning begins.',
          scriptInvariants: [
            'Enforces mandatory Living Spec headings: Blueprint, Contract, Definition of Done, Scenarios.',
            'Refuses ambiguous requirements, unverified non-goals, or dangling dependencies.',
            'Deterministic zero-exit required before planning phase is unlocked.',
          ],
          agentName: 'Requirement Critic',
          agentModel: 'Critic Model (Read-Only)',
          agentResponsibilities: [
            'Assesses ambiguity, coherence, and verifiability across all user scenarios.',
            'Emits blocking findings if any requirement cannot be verified objectively.',
            'Never edits the spec directly; operator amends spec on refutation.',
          ],
          terminalPrompt: 'gantry@worktree:~$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/spec.py --check .scratch/gantry-site/spec.md',
          terminalLines: [
            { type: 'dim', text: '[spec.py] Checking structural compliance for spec.md...' },
            { type: 'info', text: '├── Validating sections: Blueprint, Contract, Definition of Done' },
            { type: 'info', text: '├── Checking Scenarios: 4 Gherkin scenarios discovered' },
            { type: 'success', text: '✓ Structure verified: 0 schema violations' },
            { type: 'dim', text: '[requirement-critic] Assessing ambiguity & testability...' },
            { type: 'success', text: '✓ Requirement Critic: ambiguity index 0.02 [CLEAN]' },
            { type: 'success', text: '✓ Specification passes preflight checks.' },
          ],
        },
        plan: {
          name: 'Planning & Context Budget',
          shortName: '02. Plan & Budget',
          scriptDescription: 'Constructs DAG blocker graph, computes execution waves, and enforces context token ceilings.',
          scriptInvariants: [
            'Blocker graph must remain a strict DAG with zero cycles.',
            'Every slice is an atomic vertical delivery with demonstrable acceptance criteria.',
            'Mandatory STOP: Planning outputs draft issues and halts for explicit operator approval.',
          ],
          agentName: 'Planner Agent',
          agentModel: 'Plan Model',
          agentResponsibilities: [
            'Slices approved spec into vertical issues with clear file touches and acceptance criteria.',
            'Estimates context token footprint with budget.py to prevent window degradation.',
            'Stops execution: issues stay draft until explicit operator approval.',
          ],
          terminalPrompt: 'gantry@worktree:~$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/frontier.py --scope gantry-site --json',
          terminalLines: [
            { type: 'dim', text: '[frontier.py] Calculating dependency graph waves...' },
            { type: 'info', text: '├── Resolved 6 issues across 5 execution waves' },
            { type: 'info', text: '├── DAG validation: 0 cycles detected, 0 dangling references' },
            { type: 'dim', text: '[budget.py] Checking token budget against context ceiling...' },
            { type: 'success', text: '✓ Budget footprint: 4,820 tokens (6.4% of 15% ceiling)' },
            { type: 'warn', text: '! Mandatory STOP reached: waiting for operator approval.' },
            { type: 'success', text: '✓ Operator approved wave 15. Status: ready-for-agent.' },
          ],
        },
        implement: {
          name: 'TDD Implementation Loop',
          shortName: '03. Implement (TDD)',
          scriptDescription: 'Enforces strict test-driven development: write failing test first, make it green, refactor.',
          scriptInvariants: [
            'Implementer works in isolated git worktree branch: gantry/<spec>-<issue>.',
            'Cannot skip tests or weaken assertions; guard hooks reject mock escapes.',
            'Context compaction enforced: only files explicitly declared in issue are touched.',
          ],
          agentName: 'TDD Implementer',
          agentModel: 'Implement Model',
          agentResponsibilities: [
            'Reads issue acceptance criteria and writes minimal failing unit/e2e tests first.',
            'Writes production code until tests turn green with zero regressions.',
            'Emits structured result contract upon completion.',
          ],
          terminalPrompt: 'gantry@worktree:~/worktrees/gantry-site-05$',
          terminalCommand: 'npm test -- site/tests/i18n.spec.ts',
          terminalLines: [
            { type: 'dim', text: '[tdd-runner] Red phase: executing tests before implementation...' },
            { type: 'warn', text: '✘ tests/i18n.spec.ts: language toggle not defined (EXPECTED)' },
            { type: 'dim', text: '[implementer] Writing LanguageToggle component & translations dictionary...' },
            { type: 'info', text: '├── Updated: site/src/i18n/translations.ts (+350 lines)' },
            { type: 'info', text: '├── Created: site/src/components/LanguageToggle.tsx' },
            { type: 'dim', text: '[tdd-runner] Green phase: re-running tests...' },
            { type: 'success', text: '✓ tests/i18n.spec.ts: 4 passed (1.2s)' },
          ],
        },
        review: {
          name: 'Two-Axis Code Review',
          shortName: '04. Review (2-Axis)',
          scriptDescription: 'Reviews uncommitted diff across Standards and Spec axes independently in parallel.',
          scriptInvariants: [
            'Axis 1 (Standards): Clean code, architectural seam compliance, zero anti-patterns.',
            'Axis 2 (Spec): Strict alignment with issue requirements and acceptance criteria.',
            'Non-destructive: Reviewer cannot modify code; emits actionable findings.',
          ],
          agentName: 'Code Reviewer',
          agentModel: 'Review Model',
          agentResponsibilities: [
            'Inspects diff against repository coding standards and guidelines.',
            'Checks that no acceptance criterion is silently dropped or mocked away.',
            'Authorizes single fix pass if findings exist.',
          ],
          terminalPrompt: 'gantry@worktree:~/worktrees/gantry-site-05$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/result.py validate review-output.json',
          terminalLines: [
            { type: 'dim', text: '[review] Commencing two-axis review of diff...' },
            { type: 'info', text: '├── Axis 1 (Standards): Checking AST, types, linting, accessibility' },
            { type: 'success', text: '✓ Standards Axis: CLEAN (zero style violations)' },
            { type: 'info', text: '├── Axis 2 (Spec): Checking 4/4 acceptance criteria' },
            { type: 'success', text: '✓ Spec Axis: ALL CRITERIA SATISFIED' },
            { type: 'dim', text: '[result.py] Validating review contract schema...' },
            { type: 'success', text: '✓ Review Contract: schema valid, 0 blocking findings' },
          ],
        },
        critic: {
          name: 'Adversarial Critic Verification',
          shortName: '05. Adversarial Critic',
          scriptDescription: 'Independent subagent actively attempts to refute completion claims before integration.',
          scriptInvariants: [
            'Fresh subagent instance with zero shared memory from implementer.',
            'Inspects real execution evidence, not prose claims or mock assertions.',
            'Adversarial mandate: actively hunts for boundary bugs, race conditions, and mock escapes.',
          ],
          agentName: 'Adversarial Critic',
          agentModel: 'Critic Model (Adversarial)',
          agentResponsibilities: [
            'Verifies acceptance criteria with independent verification commands.',
            'Rejects delivery if tests are bypassed, mocked, or assertions are weak.',
            'Only Critic acceptance unlocks serial integration into main branch.',
          ],
          terminalPrompt: 'gantry@worktree:~/worktrees/gantry-site-05$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/runlog.py inflight gantry-site --json',
          terminalLines: [
            { type: 'dim', text: '[critic] Spawning fresh adversarial critic subagent...' },
            { type: 'dim', text: '[critic] Attempting to refute implementation claims...' },
            { type: 'info', text: '├── Testing language persistence across browser reload...' },
            { type: 'success', text: '✓ Verification confirmed: localStorage state preserved' },
            { type: 'info', text: '├── Auditing translation completeness for missing keys...' },
            { type: 'success', text: '✓ Verification confirmed: 100% dictionary key coverage' },
            { type: 'success', text: '✓ Critic Verdict: ACCEPTED (all refutations failed)' },
          ],
        },
        gate: {
          name: 'Serial Integration Gate',
          shortName: '06. Gate & Roadmap',
          scriptDescription: 'Merges accepted branch serially, runs differential quality gates, and updates roadmap.',
          scriptInvariants: [
            'Merges one issue at a time to keep git history linear and bisectable.',
            'Runs differential gates (eslint, typecheck, tests) mapped to RFC 6901 pointers.',
            'roadmap.py done updates issue status, roadmap checkboxes, and progress table in one transaction.',
          ],
          agentName: 'Serial Integrator',
          agentModel: 'Deterministic Script Runner',
          agentResponsibilities: [
            'Executes git merge into main/run branch cleanly.',
            'Runs differential quality gates with gates.py; rolls back on failure.',
            'Executes roadmap.py done to record delivery in append-only run log.',
          ],
          terminalPrompt: 'gantry@worktree:~$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/roadmap.py done gantry-site#05',
          terminalLines: [
            { type: 'dim', text: '[gates.py] Executing differential quality gates...' },
            { type: 'success', text: '✓ Typecheck: 0 errors' },
            { type: 'success', text: '✓ Playwright E2E: 21 tests passed (0 failures)' },
            { type: 'dim', text: '[roadmap.py] Updating delivery tracking...' },
            { type: 'info', text: '├── Marked gantry-site#05 as DONE' },
            { type: 'info', text: '├── Ticked 4/4 acceptance criteria checkboxes' },
            { type: 'info', text: '├── Updated ROADMAP.md: 31 / 32 issues completed (97%)' },
            { type: 'success', text: '✓ Run event recorded: issue.done' },
          ],
        },
      },
    },
    problemSolution: {
      tag: 'ANALYSIS // PROBLEM VS SOLUTION',
      title: 'Why Raw Agents Fail — And How Gantry Fixes It',
      subtitle:
        'Prose instructions in prompts are probabilistic. Gantry replaces wishful prompting with deterministic code, adversarial checks, and operator approval.',
      thesisTag: 'FIRST PRINCIPLE // ADR-0004 & PRD §2',
      thesisQuote: '"Agents + code > agents alone."',
      thesisDesc:
        'Every decision that must not be improvised — what is ready, what must be proven, whether quality gates pass, and when an Issue is done — is made by a workflow script. Agents propose; scripts verify; the operator retains final approval.',
      thesisAuthorityLabel: 'AUTHORITY:',
      thesisAuthorityVal: 'SCRIPTS DECIDE',
      pitfall1Tag: 'FAILURE MODE 01 // PITFALL',
      pitfall1Category: 'STATE DRIFT',
      pitfall1Title: 'Context Degradation & Hallucination',
      pitfall1Desc:
        'Long-running agent chat sessions accumulate tokens, lose instruction precision, drop critical constraints, and hallucinate missing architecture.',
      gantry1Title: 'GANTRY PRINCIPLE: Bounded Context & Fresh Agents',
      gantry1Desc:
        'Preflight validates tokens with budget.py (refuting packages > 15% window). Every phase (Implementer, Reviewer, Critic) spawns a fresh subagent with zero memory pollution.',
      pitfall2Tag: 'FAILURE MODE 02 // PITFALL',
      pitfall2Category: 'TEST CORROSION',
      pitfall2Title: 'Mock Escapes & Test Tampering',
      pitfall2Desc:
        'When code fails, agents casually mock out complex modules, weaken assertions, delete failing tests, or claim victory on untested stubs.',
      gantry2Title: 'GANTRY PRINCIPLE: Adversarial Verification & No Mocks',
      gantry2Desc:
        'The adversarial Critic directly inspects the git diff for mock escapes, deleted tests, or weakened checks. No delivery is accepted if tests were bypassed or watered down.',
      pitfall3Tag: 'FAILURE MODE 03 // PITFALL',
      pitfall3Category: 'UNEARNED TRUST',
      pitfall3Title: 'Wishful Self-Approval & Premature Done',
      pitfall3Desc:
        'When the builder grades its own homework, the implementer hallucinates that edge cases pass, summarizes away defects, and marks its own tasks as completed.',
      gantry3Title: 'GANTRY PRINCIPLE: Zero Self-Approval & Critic Refutation',
      gantry3Desc:
        'Zero self-approval: roadmap.py done is the sole authority to mark issues complete, guarded by differential quality gates (RFC 6901 mappings) and clean test exits. Critic refutation enforces proof.',
      pitfall4Tag: 'FAILURE MODE 04 // PITFALL',
      pitfall4Category: 'MERGE CONFLICTS',
      pitfall4Title: 'Big-Bang Divergence & Integration Hell',
      pitfall4Desc:
        'Parallel multi-agent branches create silent regressions when merged in bulk, hiding broken dependencies until after the repository is corrupted.',
      gantry4Title: 'GANTRY PRINCIPLE: Serial Wave Integration & Differential Gates',
      gantry4Desc:
        'frontier.py computes DAG execution waves. Accepted slices merge serially, running differential quality gates (gates.py) after every merge.',
    },
    skills: {
      tag: 'ARCHITECTURE // MODULAR PACK',
      title: 'The Three Skills',
      badge: 'PACK RIG: 1 THICK // 2 THIN',
      subtitle:
        'Gantry distributes as three focused, complementary skills in .agents/skills/. One workflow engine coordinates the full SDLC, while two specialized tools govern policy and runtime visibility.',
      triggersLabel: 'INVOCATION TRIGGERS:',
      viewSpec: 'VIEW SPEC',
      gantryTitle: 'gantry',
      gantryBadge: 'Core Workflow',
      gantryDesc:
        'The orchestrator executing the full SDLC loop: spec validation, context budget checks, TDD implementation loops, two-axis reviews (standards + spec), and adversarial verification.',
      gantryBullet1Title: 'TDD Cycles:',
      gantryBullet1Desc: 'Red-green-refactor with strictly minimal diffs.',
      gantryBullet2Title: 'Adversarial Critic:',
      gantryBullet2Desc: 'Fresh agent disproves claims before integration.',
      gantryBullet3Title: 'Quality Gates:',
      gantryBullet3Desc: 'Differential gates.py run serially.',
      setupTitle: 'gantry-setup',
      setupBadge: 'Policy & Governance',
      setupDesc:
        'Conversational repository setup and governance assistant. The sole authorized writer of repository policy (.gantry/config.json) and marked AGENTS.md policy sections.',
      setupBullet1Title: 'Policy Generation:',
      setupBullet1Desc: 'Interactive questionnaire configuring gates and budgets.',
      setupBullet2Title: 'Harness Detection:',
      setupBullet2Desc: 'Inspects active IDE harness and configures hooks.',
      setupBullet3Title: 'Drift Protection:',
      setupBullet3Desc: 'Never writes unvalidated or conflicting settings.',
      dashboardTitle: 'gantry-dashboard',
      dashboardBadge: 'Observability',
      dashboardDesc:
        'Zero-dependency, read-only multi-run kanban observer. Binds locally to loopback (localhost:42687) with strict zero-mutation guarantees.',
      dashboardBullet1Title: 'Multi-Run Kanban:',
      dashboardBullet1Desc: 'Visual swimlanes tracking issues across all phases.',
      dashboardBullet2Title: 'Append-Only Log:',
      dashboardBullet2Desc: 'Reads ~/.gantry/state/ without database overhead.',
      dashboardBullet3Title: 'Strict Loopback:',
      dashboardBullet3Desc: 'Binds exclusively to 127.0.0.1 for local privacy.',
    },
    matrix: {
      tag: 'INTEROPERABILITY // VERIFIED TIERS',
      title: 'Harness Compatibility Matrix',
      badge: 'TIER AUDIT // HONEST CLAIMS',
      subtitle:
        'Gantry declares harness capabilities in machine-readable JSON files (.agents/skills/gantry/capabilities/) and proves them against real test fixtures. Gantry never advertises guarantees it cannot measure.',
      tierRefTitle: 'REFERENCE TIER',
      tierRefBadge: 'GOLD STANDARD',
      tierRefDesc:
        'Full native harness support: lifecycle hooks guard, structured output contracts, isolated worktrees, per-role model selection, and complete end-to-end fixture proof.',
      tierSupTitle: 'SUPPORTED TIER',
      tierSupBadge: 'VERIFIED IN CI',
      tierSupDesc:
        'Multi-role execution, hook guard integration (via harness hooks or runner wrap), and independent Critic verification proven in automated test suites.',
      tierCompTitle: 'COMPATIBLE TIER',
      tierCompBadge: 'INSTRUCTION RIG',
      tierCompDesc:
        'Executable workflow through process runner, skill discovery, and prompt instructions. Guard hooks fall back to repository policy and manual operator gates.',
      colHarness: 'Harness',
      colTier: 'Tier',
      colHooks: 'Hook Guardrails',
      colRoles: 'Role Execution',
      colWorktrees: 'Worktree Isolation',
      colStructured: 'Structured Output',
      colEvidence: 'Verification Evidence & Notes',
      claudeNotes:
        'Native subagents, settings hooks, result contract validation, and full end-to-end fixture run recorded in CI.',
      opencodeNotes:
        'Plugin hooks wiring for guard.py, sequential and parallel rounds, verified against OpenCode test harnesses.',
      codexNotes:
        'Direct CLI runner with per-role model arguments, independent Critic verification proven on real runs.',
      antigravityNotes:
        'Supported tier. Hook guard integration via .agents/hooks.json and agy execution verified in local test suite.',
      cursorNotes:
        'Compatible tier. Rules and commands integration for Cursor composer workflows with manual operator gates.',
    },
    footer: {
      rigTitle: 'GANTRY AGENTIC SDLC',
      license: 'APACHE-2.0',
      verification: 'DETERMINISTIC VERIFICATION',
      operator: 'OPERATOR IN LOOP // HARNESS-NEUTRAL',
    },
  },
  'pt-br': {
    nav: {
      pipeline: 'PIPELINE',
      skills: 'SKILLS',
      harnesses: 'HARNESSES',
      github: 'GITHUB',
      version: 'v1.0.6 [STANDBY]',
    },
    hero: {
      systemStrip: 'RIG DO SISTEMA // NÚCLEO GANTRY ONLINE',
      badgeStatus: 'STATUS: ESPECIFICAÇÃO VERIFICADA',
      badgeHarness: 'NEUTRO A HARNESS',
      badgeLicense: 'APACHE-2.0',
      badgeAiSlop: 'ZERO ENROLAÇÃO DE IA',
      kicker: 'O PACOTE DE SKILLS PARA SDLC AGÊNTICO',
      titleHarness: 'SDLC Agêntico',
      titleAgentic: 'Neutro a Harness',
      tagline: 'Transforme uma Spec aprovada em entregas de software verificadas dentro do seu coding harness.',
      valueProp:
        'O Gantry é um pacote de skills, não um motor de execução. Scripts de fluxo determinam prontidão, aceite, gates e estado do roadmap; agentes planejam, implementam, revisam e refutam; o operador retém autoridade de aprovação.',
      craneTitle: 'GUINDASTE GANTRY // RIG MK-IV',
      craneLoad: 'CARGA: SPEC → VERIFICADA',
      metricArchLabel: 'Arquitetura',
      metricArchVal: 'Pacote de Skills',
      metricVerifLabel: 'Verificação',
      metricVerifVal: 'Crítico Adversarial',
      metricGatesLabel: 'Gates de Qualidade',
      metricGatesVal: 'Diferencial RFC 6901',
      metricOperatorLabel: 'Operador no Circuito',
      metricOperatorVal: 'Autoridade de Aprovação',
    },
    install: {
      quickInstallTitle: 'INSTALAÇÃO RÁPIDA // RUNTIME DO HARNESS',
      statusVerified: 'STATUS: VERIFICADO',
      copy: 'COPIAR',
      copied: 'COPIADO!',
      altSetupLabel: 'Configuração CLI alternativa:',
      harnessDescriptions: {
        claude: 'Tier Referência. Configurações nativas, guard de hooks e subagentes multi-função.',
        opencode: 'Tier Compatível. Integração via plugin hooks e execução de subagentes por função.',
        codex: 'Tier Suportado. Executor direto de processos e verificação independente por Crítico.',
        antigravity: 'Tier Suportado. Integração de hooks via .agents/hooks.json e execução agy.',
        cursor: 'Tier Compatível. Integração de regras e comandos para fluxos no Cursor composer.',
      },
    },
    simulator: {
      headerTitle: 'SIMULADOR DE PIPELINE // RIG SDLC DETERMINÍSTICO',
      progressLabel: 'PROGRESSO:',
      stageLabel: 'ETAPA',
      ofStages: '06',
      phaseDetails: 'DETALHES DA FASE',
      scriptInvariantsTitle: 'INVARIANTES DETERMINÍSTICOS DO SCRIPT',
      agentRoleTitle: 'CONTRATO DA FUNÇÃO DO AGENTE',
      responsibilitiesLabel: 'RESPONSABILIDADES:',
      modelLabel: 'MODELO:',
      adversarialBadge: 'ADVERSARIAL',
      cooperativeBadge: 'COOPERATIVO',
      terminalStreamTitle: 'STREAM DO TERMINAL DETERMINÍSTICO',
      terminalExecTag: 'EXECUÇÃO: COMANDO REAL',
      jsonLogTitle: 'EVENTO ESTRUTURADO DO LOG (RFC 6901 / JSONL)',
      prevStageBtn: 'FASE ANTERIOR',
      nextStageBtn: 'PRÓXIMA FASE',
      stages: {
        spec: {
          name: 'Spec & Crítico de Requisitos',
          shortName: '01. Spec & Crítico',
          scriptDescription: 'Valida a integridade estrutural da living spec antes de iniciar fatiamento ou planejamento.',
          scriptInvariants: [
            'Exige seções obrigatórias da Living Spec: Blueprint, Contrato, Definição de Pronto, Cenários.',
            'Recusa requisitos ambíguos, não-objetivos sem teste ou dependências pendentes.',
            'Saída de erro zero é estritamente exigida para desbloquear o planejamento.',
          ],
          agentName: 'Crítico de Requisitos',
          agentModel: 'Modelo Crítico (Somente Leitura)',
          agentResponsibilities: [
            'Avalia ambiguidade, coerência e testabilidade em todos os cenários de usuário.',
            'Emite apontamentos impeditivos caso algum requisito não possa ser verificado objetivamente.',
            'Nunca edita a spec diretamente; o operador ajusta a especificação em caso de refutação.',
          ],
          terminalPrompt: 'gantry@worktree:~$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/spec.py --check .scratch/gantry-site/spec.md',
          terminalLines: [
            { type: 'dim', text: '[spec.py] Verificando conformidade estrutural da spec.md...' },
            { type: 'info', text: '├── Validando seções: Blueprint, Contrato, Definição de Pronto' },
            { type: 'info', text: '├── Verificando Cenários: 4 cenários Gherkin descobertos' },
            { type: 'success', text: '✓ Estrutura verificada: 0 violações de schema' },
            { type: 'dim', text: '[crítico-requisitos] Avaliando ambiguidade e testabilidade...' },
            { type: 'success', text: '✓ Crítico de Requisitos: índice de ambiguidade 0.02 [LIMPO]' },
            { type: 'success', text: '✓ Especificação aprovada nos testes de preflight.' },
          ],
        },
        plan: {
          name: 'Planejamento & Orçamento de Contexto',
          shortName: '02. Plano & Orçamento',
          scriptDescription: 'Gera grafo DAG de bloqueios, calcula ondas de execução e impõe limites de tokens de contexto.',
          scriptInvariants: [
            'Grafo de bloqueios deve ser estritamente acíclico (DAG com zero ciclos).',
            'Cada fatia representa uma entrega vertical atômica com critérios de aceite demonstráveis.',
            'PARADA OBRIGATÓRIA: O planejamento emite rascunhos de issues e para aguardando aprovação do operador.',
          ],
          agentName: 'Agente de Planejamento',
          agentModel: 'Modelo de Planejamento',
          agentResponsibilities: [
            'Fatia a spec aprovada em issues verticais com arquivos tocados e critérios claros.',
            'Estima pegada de tokens com budget.py para evitar degradação da janela de contexto.',
            'Interrompe a execução: issues permanecem como rascunho até aprovação explícita.',
          ],
          terminalPrompt: 'gantry@worktree:~$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/frontier.py --scope gantry-site --json',
          terminalLines: [
            { type: 'dim', text: '[frontier.py] Calculando ondas do grafo de dependências...' },
            { type: 'info', text: '├── Resolvidas 6 issues ao longo de 5 ondas de execução' },
            { type: 'info', text: '├── Validação DAG: 0 ciclos detectados, 0 referências pendentes' },
            { type: 'dim', text: '[budget.py] Verificando pegada de tokens contra limite do contexto...' },
            { type: 'success', text: '✓ Pegada de orçamento: 4.820 tokens (6.4% do teto de 15%)' },
            { type: 'warn', text: '! PARADA OBRIGATÓRIA atingida: aguardando aprovação do operador.' },
            { type: 'success', text: '✓ Operador aprovou a onda 15. Status: pronto-para-agente.' },
          ],
        },
        implement: {
          name: 'Ciclo de Implementação TDD',
          shortName: '03. Implementar (TDD)',
          scriptDescription: 'Impõe desenvolvimento estritamente orientado a testes: teste falhando primeiro, código, refatoração.',
          scriptInvariants: [
            'Implementador trabalha em worktree git isolada: gantry/<spec>-<issue>.',
            'Proibido pular testes ou enfraquecer asserts; hooks bloqueiam fugas com mocks.',
            'Compactação de contexto aplicada: apenas arquivos declarados na issue são alterados.',
          ],
          agentName: 'Implementador TDD',
          agentModel: 'Modelo de Implementação',
          agentResponsibilities: [
            'Lê os critérios de aceite e escreve testes unitários/e2e mínimos em estado vermelho.',
            'Escreve código de produção até que todos os testes fiquem verdes sem regressões.',
            'Emite contrato de resultado estruturado após a conclusão.',
          ],
          terminalPrompt: 'gantry@worktree:~/worktrees/gantry-site-05$',
          terminalCommand: 'npm test -- site/tests/i18n.spec.ts',
          terminalLines: [
            { type: 'dim', text: '[tdd-runner] Fase Vermelha: executando testes antes do código...' },
            { type: 'warn', text: '✘ tests/i18n.spec.ts: seletor de idioma não definido (ESPERADO)' },
            { type: 'dim', text: '[implementador] Criando componente LanguageToggle e dicionário de traduções...' },
            { type: 'info', text: '├── Atualizado: site/src/i18n/translations.ts (+350 linhas)' },
            { type: 'info', text: '├── Criado: site/src/components/LanguageToggle.tsx' },
            { type: 'dim', text: '[tdd-runner] Fase Verde: reexecutando suite de testes...' },
            { type: 'success', text: '✓ tests/i18n.spec.ts: 4 passaram (1.2s)' },
          ],
        },
        review: {
          name: 'Revisão em Dois Eixos',
          shortName: '04. Revisão (2 Eixos)',
          scriptDescription: 'Revisa o diff não-comitado nos eixos Padrões e Especificação paralelamente e sem interferência.',
          scriptInvariants: [
            'Eixo 1 (Padrões): Código limpo, limites arquiteturais, zero padrões indesejados.',
            'Eixo 2 (Spec): Alinhamento rigoroso com os requisitos e critérios de aceite da issue.',
            'Não-destrutivo: O revisor não altera código; ele emite apontamentos práticos de correção.',
          ],
          agentName: 'Revisor de Código',
          agentModel: 'Modelo de Revisão',
          agentResponsibilities: [
            'Inspeciona o diff contra os padrões de código e diretrizes do repositório.',
            'Verifica se nenhum critério de aceite foi silenciosamente descartado ou substituído por mock.',
            'Autoriza uma rodada única de correções caso haja apontamentos.',
          ],
          terminalPrompt: 'gantry@worktree:~/worktrees/gantry-site-05$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/result.py validate review-output.json',
          terminalLines: [
            { type: 'dim', text: '[revisão] Iniciando revisão em dois eixos do diff...' },
            { type: 'info', text: '├── Eixo 1 (Padrões): Analisando AST, tipagem, lint e acessibilidade' },
            { type: 'success', text: '✓ Eixo Padrões: LIMPO (zero violações de estilo)' },
            { type: 'info', text: '├── Eixo 2 (Spec): Checando 4/4 critérios de aceite' },
            { type: 'success', text: '✓ Eixo Spec: TODOS OS CRITÉRIOS ATENDIDOS' },
            { type: 'dim', text: '[result.py] Validando schema do contrato de revisão...' },
            { type: 'success', text: '✓ Contrato de Revisão: schema válido, 0 apontamentos impeditivos' },
          ],
        },
        critic: {
          name: 'Verificação Adversarial por Crítico',
          shortName: '05. Crítico Adversarial',
          scriptDescription: 'Subagente independente que tenta refutar ativamente as afirmações de entrega antes do merge.',
          scriptInvariants: [
            'Instância limpa de subagente com zero memória compartilhada do implementador.',
            'Inspeciona evidências reais de execução, não relatos em texto ou asserções simuladas.',
            'Mandato adversarial: procura ativamente falhas de limite, condições de corrida e mocks indevidos.',
          ],
          agentName: 'Crítico Adversarial',
          agentModel: 'Modelo Crítico (Adversarial)',
          agentResponsibilities: [
            'Verifica os critérios de aceite executando comandos de prova independentes.',
            'Rejeita a entrega se testes tiverem sido contornados ou assertions forem fracas.',
            'Apenas o aceite do Crítico desbloqueia a integração serial no branch principal.',
          ],
          terminalPrompt: 'gantry@worktree:~/worktrees/gantry-site-05$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/runlog.py inflight gantry-site --json',
          terminalLines: [
            { type: 'dim', text: '[crítico] Iniciando subagente crítico adversarial independente...' },
            { type: 'dim', text: '[crítico] Tentando refutar as afirmações de implementação...' },
            { type: 'info', text: '├── Testando persistência do idioma após recarregamento do navegador...' },
            { type: 'success', text: '✓ Verificação confirmada: estado no localStorage preservado' },
            { type: 'info', text: '├── Auditando completude do dicionário para chaves faltantes...' },
            { type: 'success', text: '✓ Verificação confirmada: 100% de cobertura de chaves' },
            { type: 'success', text: '✓ Veredito do Crítico: ACEITO (todas as refutações falharam)' },
          ],
        },
        gate: {
          name: 'Gate de Integração Serial',
          shortName: '06. Gate & Roadmap',
          scriptDescription: 'Integra o branch aceito em série, executa gates diferenciais de qualidade e atualiza o roadmap.',
          scriptInvariants: [
            'Integra uma issue por vez para manter histórico git linear e bisseccionável.',
            'Executa gates diferenciais (eslint, checagem de tipos, testes) com mapeamento RFC 6901.',
            'roadmap.py done atualiza status da issue, caixas de seleção e tabela de progresso atomicamente.',
          ],
          agentName: 'Integrador Serial',
          agentModel: 'Executor Determinístico de Scripts',
          agentResponsibilities: [
            'Executa git merge de forma limpa no branch principal de execução.',
            'Roda gates diferenciais com gates.py; reverte o merge em caso de falha.',
            'Executa roadmap.py done para registrar a entrega no log append-only da Run.',
          ],
          terminalPrompt: 'gantry@worktree:~$',
          terminalCommand: 'python3 .agents/skills/gantry/scripts/roadmap.py done gantry-site#05',
          terminalLines: [
            { type: 'dim', text: '[gates.py] Executando gates diferenciais de qualidade...' },
            { type: 'success', text: '✓ Tipagem: 0 erros' },
            { type: 'success', text: '✓ Playwright E2E: 21 testes passaram (0 falhas)' },
            { type: 'dim', text: '[roadmap.py] Atualizando controle de entregas...' },
            { type: 'info', text: '├── Marcada issue gantry-site#05 como CONCLUÍDA' },
            { type: 'info', text: '├── Marcados 4/4 critérios de aceite como atendidos' },
            { type: 'info', text: '├── Atualizado ROADMAP.md: 31 / 32 issues concluídas (97%)' },
            { type: 'success', text: '✓ Evento registrado na Run: issue.done' },
          ],
        },
      },
    },
    problemSolution: {
      tag: 'ANÁLISE // PROBLEMA VS SOLUÇÃO',
      title: 'Por que Agentes Puros Falham — E Como o Gantry Resolve',
      subtitle:
        'Instruções em texto corrido são probabilísticas. O Gantry substitui expectativas frágeis por código determinístico, verificações adversariais e aprovação do operador.',
      thesisTag: 'PRIMEIRO PRINCÍPIO // ADR-0004 & PRD §2',
      thesisQuote: '"Agentes + código > apenas agentes."',
      thesisDesc:
        'Toda decisão que não pode ser improvisada — o que está pronto, o que deve ser provado, se os gates passam e quando uma Issue está concluída — é tomada por um script de fluxo. Agentes propõem; scripts verificam; o operador mantém aprovação final.',
      thesisAuthorityLabel: 'AUTORIDADE:',
      thesisAuthorityVal: 'SCRIPTS DECIDEM',
      pitfall1Tag: 'FALHA TÍPICA 01 // ARMADILHA',
      pitfall1Category: 'DESVIO DE ESTADO',
      pitfall1Title: 'Degradação de Contexto & Alucinações',
      pitfall1Desc:
        'Sessões longas acumulam tokens, perdem precisão nas instruções, descartam restrições críticas e alucinam soluções inexistentes.',
      gantry1Title: 'PRINCÍPIO GANTRY: Contexto Delimitado & Agentes Limpos',
      gantry1Desc:
        'Preflight valida tokens com budget.py (rejeitando pacotes > 15% da janela). Cada fase (Implementador, Revisor, Crítico) executa um subagente limpo sem poluição de memória.',
      pitfall2Tag: 'FALHA TÍPICA 02 // ARMADILHA',
      pitfall2Category: 'CORROSÃO DE TESTES',
      pitfall2Title: 'Fugas com Mocks & Alteração de Testes',
      pitfall2Desc:
        'Quando o código falha, agentes frequentemente criam mocks triviais, enfraquecem asserções ou deletam testes que falham para forjar um status verde.',
      gantry2Title: 'PRINCÍPIO GANTRY: Verificação Adversarial & Sem Mocks',
      gantry2Desc:
        'O Crítico adversarial inspeciona diretamente o git diff em busca de mocks indevidos, testes apagados ou verificações enfraquecidas. Nenhuma entrega é aceita se testes tiverem sido contornados.',
      pitfall3Tag: 'FALHA TÍPICA 03 // ARMADILHA',
      pitfall3Category: 'CONFIANÇA INDEVIDA',
      pitfall3Title: 'Auto-Aprovação Frágil & Conclusão Prematura',
      pitfall3Desc:
        'Quando o próprio construtor avalia sua entrega, o implementador assume que casos de borda funcionam, ignora defeitos e marca as próprias tarefas como concluídas.',
      gantry3Title: 'PRINCÍPIO GANTRY: Zero Auto-Aprovação & Refutação pelo Crítico',
      gantry3Desc:
        'Zero auto-aprovação: roadmap.py done é a única autoridade para concluir issues, resguardado por gates diferenciais de qualidade (mapeamento RFC 6901) e testes limpos.',
      pitfall4Tag: 'FALHA TÍPICA 04 // ARMADILHA',
      pitfall4Category: 'CONFLITOS DE MERGE',
      pitfall4Title: 'Divergência em Massa & Caos de Integração',
      pitfall4Desc:
        'Agentes tentando alterar dezenas de arquivos ao mesmo tempo causam conflitos graves de merge, quebrando builds e gerando regressões difíceis de rastrear.',
      gantry4Title: 'PRINCÍPIO GANTRY: Integração Serial em Ondas & Worktrees Isoladas',
      gantry4Desc:
        'frontier.py calcula ondas DAG de execução. As branches aceitas são integradas em série, executando gates diferenciais de qualidade (gates.py) a cada merge.',
    },
    skills: {
      tag: 'ARQUITETURA // PACOTE MODULAR',
      title: 'As Três Skills',
      badge: 'PACOTE: 1 ROBUSTO // 2 LEVES',
      subtitle:
        'O Gantry distribui-se em três skills focadas e complementares em .agents/skills/. Um motor de fluxo coordena todo o SDLC, enquanto duas ferramentas especializadas governam políticas e visibilidade em runtime.',
      triggersLabel: 'GATILHOS DE INVOCAÇÃO:',
      viewSpec: 'VER ESPECIFICAÇÃO',
      gantryTitle: 'gantry',
      gantryBadge: 'Fluxo Central',
      gantryDesc:
        'O orquestrador que executa o loop completo de SDLC: validação de spec, checagens de orçamento de contexto, loops TDD, revisões em dois eixos (padrões + spec) e verificação adversarial.',
      gantryBullet1Title: 'Ciclos TDD:',
      gantryBullet1Desc: 'Red-green-refactor com diffs estritamente mínimos.',
      gantryBullet2Title: 'Crítico Adversarial:',
      gantryBullet2Desc: 'Agente independente refuta afirmações antes do merge.',
      gantryBullet3Title: 'Gates de Qualidade:',
      gantryBullet3Desc: 'Diferencial gates.py executado em série.',
      setupTitle: 'gantry-setup',
      setupBadge: 'Política & Governança',
      setupDesc:
        'Assistente de configuração e governança conversacional. O único escritor autorizado da política do repositório (.gantry/config.json) e das seções marcadas em AGENTS.md.',
      setupBullet1Title: 'Geração de Política:',
      setupBullet1Desc: 'Questionário interativo para configurar gates e orçamentos.',
      setupBullet2Title: 'Detecção de Harness:',
      setupBullet2Desc: 'Inspeciona o ambiente da IDE ativa e configura hooks.',
      setupBullet3Title: 'Proteção contra Desvios:',
      setupBullet3Desc: 'Nunca escreve configurações inválidas ou em conflito.',
      dashboardTitle: 'gantry-dashboard',
      dashboardBadge: 'Telemetria em Tempo Real',
      dashboardDesc:
        'Painel kanban multi-run em modo somente leitura e loopback local. Exibe execuções ativas e históricas com raias de fases, transições e falhas de gates mapeadas por RFC 6901.',
      dashboardBullet1Title: 'Kanban Multi-Run:',
      dashboardBullet1Desc: 'Raias visuais rastreando issues em todas as fases.',
      dashboardBullet2Title: 'Log Append-Only:',
      dashboardBullet2Desc: 'Lê ~/.gantry/state/ sem overhead de banco de dados.',
      dashboardBullet3Title: 'Loopback Restrito:',
      dashboardBullet3Desc: 'Escuta exclusivamente em 127.0.0.1 para total privacidade.',
    },
    matrix: {
      tag: 'INTEROPERABILIDADE // TIERS VERIFICADOS',
      title: 'Matriz de Compatibilidade de Harnesses',
      badge: 'AUDITORIA DE TIERS // GARANTIAS HONESTAS',
      subtitle:
        'O Gantry declara capacidades de harness em arquivos JSON legíveis por máquina (.agents/skills/gantry/capabilities/) e as comprova em fixtures reais de teste. O Gantry nunca anuncia garantias que não pode medir.',
      tierRefTitle: 'TIER REFERÊNCIA',
      tierRefBadge: 'PADRÃO OURO',
      tierRefDesc:
        'Suporte nativo completo: guard de hooks de ciclo de vida, contratos de saída estruturada, worktrees isoladas, seleção de modelo por função e prova em fixture de ponta a ponta.',
      tierSupTitle: 'TIER SUPORTADO',
      tierSupBadge: 'VERIFICADO EM CI',
      tierSupDesc:
        'Execução multi-função, integração de hooks de segurança (nativa ou via runner) e verificação independente por Crítico comprovada em suíte automatizada.',
      tierCompTitle: 'TIER COMPATÍVEL',
      tierCompBadge: 'RIG POR INSTRUÇÃO',
      tierCompDesc:
        'Fluxo executável via executor de processos, descoberta de skills e instruções de prompt. Hooks de proteção recorrem à política do repositório e gates manuais do operador.',
      colHarness: 'Harness',
      colTier: 'Tier',
      colHooks: 'Guardrails de Hook',
      colRoles: 'Execução de Funções',
      colWorktrees: 'Isolamento por Worktree',
      colStructured: 'Saída Estruturada',
      colEvidence: 'Evidência de Verificação & Notas',
      claudeNotes:
        'Subagentes nativos, hooks de configuração, validação de contrato de resultado e fixture completa gravada em CI.',
      opencodeNotes:
        'Integração de hooks via plugin para guard.py, rodadas sequenciais e paralelas, verificado contra test harnesses do OpenCode.',
      codexNotes:
        'Runner CLI direto com argumentos de modelo por função, verificação independente de Crítico comprovada em execuções reais.',
      antigravityNotes:
        'Tier Suportado. Integração de hooks via .agents/hooks.json e execução agy verificada na suite de testes local.',
      cursorNotes:
        'Tier Compatível. Integração de regras e comandos para fluxos no Cursor composer com gates manuais pelo operador.',
    },
    footer: {
      rigTitle: 'SDLC AGÊNTICO GANTRY',
      license: 'APACHE-2.0',
      verification: 'VERIFICAÇÃO DETERMINÍSTICA',
      operator: 'OPERADOR NO CIRCUITO // NEUTRO A HARNESS',
    },
  },
};
