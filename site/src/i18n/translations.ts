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
    interfaceLabel: string;
    invocationLabel: string;
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
    planTitle: string;
    planBadge: string;
    planDesc: string;
    planBullet1Title: string;
    planBullet1Desc: string;
    planBullet2Title: string;
    planBullet2Desc: string;
    planBullet3Title: string;
    planBullet3Desc: string;
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
      version: 'v1.1.0 [STANDBY]',
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
      scriptInvariantsTitle: 'WORKFLOW ACTION & GUARANTEES',
      interfaceLabel: 'CONTROL: OPERATOR + GANTRY',
      invocationLabel: 'ACTION / INVOCATION:',
      agentRoleTitle: 'AGENT ROLE',
      responsibilitiesLabel: 'RESPONSIBILITIES:',
      modelLabel: 'MODEL:',
      adversarialBadge: 'ADVERSARIAL',
      cooperativeBadge: 'COOPERATIVE',
      terminalStreamTitle: 'GANTRY SKILL RUN STREAM',
      terminalExecTag: 'HOST: CODING HARNESS',
      jsonLogTitle: 'STRUCTURED RUN LOG EVENT (RFC 6901 / JSONL)',
      prevStageBtn: 'PREVIOUS PHASE',
      nextStageBtn: 'NEXT PHASE',
      stages: {
        setup: {
          name: 'One-Time Repository Setup',
          shortName: '01. Setup Once',
          scriptDescription: 'Adapts the repository to Gantry once, before any feature planning or implementation Run.',
          scriptInvariants: [
            'Runs once per repository, then remains versioned as repository policy.',
            'Maps existing artifacts, templates, checks, Git policy, roles, and supported hooks.',
            'Shows the complete proposed policy and waits for operator approval before writing.',
          ],
          agentName: 'Setup Guide',
          agentModel: 'Host Harness',
          agentResponsibilities: [
            'Inspects repository conventions instead of creating duplicate structures.',
            'Explains each configuration choice, benefit, and trade-off.',
            'Writes policy only after explicit operator confirmation.',
          ],
          terminalPrompt: 'operator>',
          terminalCommand: '/gantry-setup',
          terminalLines: [
            { type: 'dim', text: '[setup] Run once per repository.' },
            { type: 'info', text: '├── Existing docs, checks, Git policy, and harness capabilities inspected' },
            { type: 'info', text: '├── Proposed .gantry/config.json presented for approval' },
            { type: 'success', text: '✓ Repository adapted to Gantry.' },
            { type: 'success', text: '✓ Ready for /gantry-plan.' },
          ],
        },
        plan: {
          name: 'Plan Goal into Spec & Issues',
          shortName: '02. Plan Goal',
          scriptDescription: 'Turns a free-text goal into a verified Spec and tracer-bullet Issues, then stops for approval.',
          scriptInvariants: [
            'Socratic discovery resolves scope, seams, non-goals, and verifiable scenarios.',
            'Writes .scratch/login-otp/spec.md and draft vertical Issues.',
            'Mandatory STOP: the Spec and Issue breakdown require explicit approval.',
          ],
          agentName: 'Planner Agent',
          agentModel: 'Plan Model',
          agentResponsibilities: [
            'Slices approved spec into vertical issues with clear file touches and acceptance criteria.',
            'Estimates context token footprint with budget.py to prevent window degradation.',
            'Stops execution: issues stay draft until explicit operator approval.',
          ],
          terminalPrompt: 'operator>',
          terminalCommand: '/gantry-plan Add login via OTP',
          terminalLines: [
            { type: 'dim', text: '[gantry-plan] Exploring repository context and OTP requirements...' },
            { type: 'info', text: '├── Wrote .scratch/login-otp/spec.md' },
            { type: 'info', text: '├── Proposed 3 vertical Issues; waves follow approval' },
            { type: 'success', text: '✓ Spec validation and Plan Critic passed.' },
            { type: 'warn', text: '! Waiting for approval of the Spec and proposed Issues.' },
          ],
        },
        implement: {
          name: 'Execute Approved Spec',
          shortName: '04. Execute Spec',
          scriptDescription: 'Starts the implementation Run for the approved login-otp Spec; subsequent phases are coordinated automatically.',
          scriptInvariants: [
            'Preflight validates a clean baseline, role selections, roadmap integrity, and in-flight work.',
            'Ready Issues execute by dependency round in isolated worktrees when parallel.',
            'The same /gantry Run continues through Review, Critic, gates, integration, and handoff.',
          ],
          agentName: 'TDD Implementer',
          agentModel: 'Implement Model',
          agentResponsibilities: [
            'Reads issue acceptance criteria and writes minimal failing unit/e2e tests first.',
            'Writes production code until tests turn green with zero regressions.',
            'Emits structured result contract upon completion.',
          ],
          terminalPrompt: 'operator>',
          terminalCommand: '/gantry Implement the login-otp Spec',
          terminalLines: [
            { type: 'dim', text: '[gantry] Preflight passed; starting approved dependency rounds...' },
            { type: 'info', text: '├── login-otp#01 assigned to isolated worktree' },
            { type: 'dim', text: '[implementer] Red → green → refactor...' },
            { type: 'success', text: '✓ Implementation evidence recorded.' },
            { type: 'info', text: '├── Continuing automatically to Review and Critic' },
          ],
        },
        approve: {
          name: 'Approve Spec & Issues',
          shortName: '03. Human Approval',
          scriptDescription: 'The operator approves the concrete Spec and Issue breakdown produced by /gantry-plan.',
          scriptInvariants: [
            'Approval names the exact login-otp Spec and proposed Issues.',
            'Draft Issues become ready-for-agent only after explicit approval.',
            'Any material plan amendment returns to the operator for renewed approval.',
          ],
          agentName: 'Operator Gate',
          agentModel: 'Human Decision',
          agentResponsibilities: [
            'Reviews scope, behavior, acceptance criteria, and dependency order.',
            'Requests changes or approves the exact plan.',
            'Keeps implementation blocked until the decision is explicit.',
          ],
          terminalPrompt: 'operator>',
          terminalCommand: 'I approve the login-otp Spec and proposed Issues.',
          terminalLines: [
            { type: 'dim', text: '[operator gate] Reviewing Spec, slices, criteria, and blocker graph...' },
            { type: 'success', text: '✓ Spec login-otp approved.' },
            { type: 'success', text: '✓ 3 proposed Issues approved and scheduled.' },
            { type: 'info', text: '├── Next command: /gantry Implement the login-otp Spec' },
          ],
        },
        verify: {
          name: 'Automatic Review & Critic',
          shortName: '05. Review + Critic',
          scriptDescription: 'The active /gantry Run performs two-axis review and fresh adversarial verification without another user command.',
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
            'Only Critic acceptance unlocks serial integration into the Run branch.',
          ],
          terminalPrompt: 'operator>',
          terminalCommand: '/gantry continues automatically: Review → Critic',
          terminalLines: [
            { type: 'dim', text: '[automatic] No additional command required.' },
            { type: 'info', text: '├── Reviewer checked standards and Spec alignment' },
            { type: 'dim', text: '[critic] Fresh agent attempting to refute completion...' },
            { type: 'success', text: '✓ Acceptance criteria independently verified.' },
            { type: 'success', text: '✓ Critic Verdict: ACCEPTED' },
          ],
        },
        handoff: {
          name: 'Gates, Integration & Handoff',
          shortName: '06. Gates + Handoff',
          scriptDescription: 'The same /gantry Run raises deterministic or human gates, integrates accepted work, and prepares the handoff.',
          scriptInvariants: [
            'Merges one issue at a time to keep git history linear and bisectable.',
            'Runs differential gates (eslint, typecheck, tests) mapped to RFC 6901 pointers.',
            'roadmap.py done updates issue status, roadmap checkboxes, and progress table in one transaction.',
          ],
          agentName: 'Serial Integrator',
          agentModel: 'Deterministic Script Runner',
          agentResponsibilities: [
            'Executes a clean git merge into the Run branch.',
            'Runs differential quality gates with gates.py; rolls back on failure.',
            'Executes roadmap.py done to record delivery in append-only run log.',
          ],
          terminalPrompt: 'operator>',
          terminalCommand: '/gantry continues automatically; use /gantry-dashboard to observe',
          terminalLines: [
            { type: 'dim', text: '[automatic] Running declared quality gates after each serial integration...' },
            { type: 'success', text: '✓ Deterministic gates passed.' },
            { type: 'success', text: '✓ Approved Issues integrated and roadmap updated.' },
            { type: 'warn', text: '! Human gates are surfaced in the harness when a decision is required.' },
            { type: 'info', text: '├── Optional visibility: /gantry-dashboard' },
            { type: 'success', text: '✓ Final evidence and handoff ready.' },
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
      title: 'The Four Skills',
      badge: 'PACK: 4 SKILLS',
      subtitle:
        'Gantry ships four focused skills: one-time repository setup, standalone planning, automatic implementation, and read-only Run visibility.',
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
      planTitle: 'gantry-plan',
      planBadge: 'Planning',
      planDesc:
        'Transforms a free-text goal or existing Spec into a verified Spec, tracer-bullet Issues, a budgeted breakdown, and an explicit operator approval gate.',
      planBullet1Title: 'Socratic Gate:',
      planBullet1Desc: 'Clarifies scope, seams, non-goals, and scenarios.',
      planBullet2Title: 'Spec & Issues:',
      planBullet2Desc: 'Writes the Spec and vertical Issue breakdown.',
      planBullet3Title: 'Approval Stop:',
      planBullet3Desc: 'Never starts implementation before operator approval.',
      dashboardTitle: 'gantry-dashboard',
      dashboardBadge: 'Observability',
      dashboardDesc:
        'Zero-dependency, read-only multi-run kanban observer. Binds locally to loopback (localhost:4600) with strict zero-mutation guarantees.',
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
        'Supported tier. Direct CLI runner with per-role model arguments, independent Critic verification proven on real runs.',
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
      version: 'v1.1.0 [STANDBY]',
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
      scriptInvariantsTitle: 'AÇÃO DO WORKFLOW & GARANTIAS',
      interfaceLabel: 'CONTROLE: OPERADOR + GANTRY',
      invocationLabel: 'AÇÃO / INVOCAÇÃO:',
      agentRoleTitle: 'CONTRATO DA FUNÇÃO DO AGENTE',
      responsibilitiesLabel: 'RESPONSABILIDADES:',
      modelLabel: 'MODELO:',
      adversarialBadge: 'ADVERSARIAL',
      cooperativeBadge: 'COOPERATIVO',
      terminalStreamTitle: 'FLUXO DO RUN VIA SKILL GANTRY',
      terminalExecTag: 'HOST: HARNESS DE CÓDIGO',
      jsonLogTitle: 'EVENTO ESTRUTURADO DO LOG (RFC 6901 / JSONL)',
      prevStageBtn: 'FASE ANTERIOR',
      nextStageBtn: 'PRÓXIMA FASE',
      stages: {
        setup: {
          name: 'Configuração Única do Repositório',
          shortName: '01. Configuração Única',
          scriptDescription: 'Adapta o repositório ao Gantry uma única vez, antes de qualquer planejamento ou Run de implementação.',
          scriptInvariants: [
            'Executa uma vez por repositório e mantém a política versionada.',
            'Mapeia artefatos, templates, checks, política Git, funções e hooks suportados.',
            'Mostra a política completa e aguarda aprovação antes de escrever.',
          ],
          agentName: 'Guia de Configuração',
          agentModel: 'Harness Host',
          agentResponsibilities: [
            'Inspeciona convenções existentes sem criar estruturas duplicadas.',
            'Explica cada configuração, benefício e trade-off.',
            'Escreve a política somente após confirmação explícita.',
          ],
          terminalPrompt: 'operador>',
          terminalCommand: '/gantry-setup',
          terminalLines: [
            { type: 'dim', text: '[setup] Execute uma vez por repositório.' },
            { type: 'info', text: '├── Docs, checks, política Git e capacidades do harness inspecionados' },
            { type: 'info', text: '├── Proposta de .gantry/config.json apresentada para aprovação' },
            { type: 'success', text: '✓ Repositório adaptado ao Gantry.' },
            { type: 'success', text: '✓ Pronto para /gantry-plan.' },
          ],
        },
        plan: {
          name: 'Planejar Objetivo em Spec & Issues',
          shortName: '02. Planejar Objetivo',
          scriptDescription: 'Transforma um objetivo livre em Spec verificada e Issues verticais, parando para aprovação.',
          scriptInvariants: [
            'Descoberta socrática resolve escopo, seams, não-objetivos e cenários verificáveis.',
            'Escreve .scratch/login-otp/spec.md e Issues verticais em rascunho.',
            'PARADA OBRIGATÓRIA: a Spec e as Issues exigem aprovação explícita.',
          ],
          agentName: 'Agente de Planejamento',
          agentModel: 'Modelo de Planejamento',
          agentResponsibilities: [
            'Fatia a spec aprovada em issues verticais com arquivos tocados e critérios claros.',
            'Estima pegada de tokens com budget.py para evitar degradação da janela de contexto.',
            'Interrompe a execução: issues permanecem como rascunho até aprovação explícita.',
          ],
          terminalPrompt: 'operador>',
          terminalCommand: '/gantry-plan Adicionar login via OTP',
          terminalLines: [
            { type: 'dim', text: '[gantry-plan] Explorando o repositório e os requisitos de OTP...' },
            { type: 'info', text: '├── Criada .scratch/login-otp/spec.md' },
            { type: 'info', text: '├── Propostas 3 Issues verticais; ondas vêm após a aprovação' },
            { type: 'success', text: '✓ Validação da Spec e Crítico de Plano aprovados.' },
            { type: 'warn', text: '! Aguardando aprovação da Spec e das Issues propostas.' },
          ],
        },
        implement: {
          name: 'Executar Spec Aprovada',
          shortName: '04. Executar Spec',
          scriptDescription: 'Inicia o Run da Spec login-otp aprovada; as fases seguintes são coordenadas automaticamente.',
          scriptInvariants: [
            'Preflight valida baseline limpa, funções, roadmap e trabalhos em andamento.',
            'Issues prontas executam por rodada de dependências, em worktrees isoladas quando paralelas.',
            'O mesmo Run /gantry continua por Revisão, Crítico, gates, integração e handoff.',
          ],
          agentName: 'Implementador TDD',
          agentModel: 'Modelo de Implementação',
          agentResponsibilities: [
            'Lê os critérios de aceite e escreve testes unitários/e2e mínimos em estado vermelho.',
            'Escreve código de produção até que todos os testes fiquem verdes sem regressões.',
            'Emite contrato de resultado estruturado após a conclusão.',
          ],
          terminalPrompt: 'operador>',
          terminalCommand: '/gantry Implementar a spec login-otp',
          terminalLines: [
            { type: 'dim', text: '[gantry] Preflight aprovado; iniciando rodadas aprovadas...' },
            { type: 'info', text: '├── login-otp#01 atribuída a uma worktree isolada' },
            { type: 'dim', text: '[implementador] Vermelho → verde → refatorar...' },
            { type: 'success', text: '✓ Evidências de implementação registradas.' },
            { type: 'info', text: '├── Continuando automaticamente para Revisão e Crítico' },
          ],
        },
        approve: {
          name: 'Aprovar Spec & Issues',
          shortName: '03. Aprovação Humana',
          scriptDescription: 'O operador aprova a Spec e o conjunto de Issues concretos produzidos por /gantry-plan.',
          scriptInvariants: [
            'A aprovação nomeia a Spec login-otp e as Issues exatas.',
            'Issues em rascunho ficam ready-for-agent somente após aprovação explícita.',
            'Qualquer mudança material retorna ao operador para nova aprovação.',
          ],
          agentName: 'Gate do Operador',
          agentModel: 'Decisão Humana',
          agentResponsibilities: [
            'Revisa escopo, comportamento, critérios e ordem de dependências.',
            'Solicita mudanças ou aprova o plano exato.',
            'Mantém a implementação bloqueada até a decisão ser explícita.',
          ],
          terminalPrompt: 'operador>',
          terminalCommand: 'Aprovo a Spec login-otp e as Issues propostas.',
          terminalLines: [
            { type: 'dim', text: '[gate do operador] Revisando Spec, fatias, critérios e dependências...' },
            { type: 'success', text: '✓ Spec login-otp aprovada.' },
            { type: 'success', text: '✓ 3 Issues propostas aprovadas e agendadas.' },
            { type: 'info', text: '├── Próximo comando: /gantry Implementar a spec login-otp' },
          ],
        },
        verify: {
          name: 'Revisão & Crítico Automáticos',
          shortName: '05. Revisão + Crítico',
          scriptDescription: 'O Run /gantry ativo executa revisão em dois eixos e verificação adversarial sem outro comando do usuário.',
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
            'Apenas o aceite do Crítico desbloqueia a integração serial no branch do Run.',
          ],
          terminalPrompt: 'operador>',
          terminalCommand: '/gantry continua automaticamente: Revisão → Crítico',
          terminalLines: [
            { type: 'dim', text: '[automático] Nenhum comando adicional necessário.' },
            { type: 'info', text: '├── Revisor checou padrões e alinhamento com a Spec' },
            { type: 'dim', text: '[crítico] Agente novo tentando refutar a conclusão...' },
            { type: 'success', text: '✓ Critérios de aceite verificados independentemente.' },
            { type: 'success', text: '✓ Veredito do Crítico: ACEITO' },
          ],
        },
        handoff: {
          name: 'Gates, Integração & Handoff',
          shortName: '06. Gates + Handoff',
          scriptDescription: 'O mesmo Run /gantry levanta gates determinísticos ou humanos, integra o trabalho aceito e prepara o handoff.',
          scriptInvariants: [
            'Integra uma issue por vez para manter histórico git linear e bisseccionável.',
            'Executa gates diferenciais (eslint, checagem de tipos, testes) com mapeamento RFC 6901.',
            'roadmap.py done atualiza status da issue, caixas de seleção e tabela de progresso atomicamente.',
          ],
          agentName: 'Integrador Serial',
          agentModel: 'Executor Determinístico de Scripts',
          agentResponsibilities: [
            'Executa git merge de forma limpa no branch do Run.',
            'Roda gates diferenciais com gates.py; reverte o merge em caso de falha.',
            'Executa roadmap.py done para registrar a entrega no log append-only da Run.',
          ],
          terminalPrompt: 'operador>',
          terminalCommand: '/gantry continua automaticamente; use /gantry-dashboard para observar',
          terminalLines: [
            { type: 'dim', text: '[automático] Executando gates declarados após cada integração serial...' },
            { type: 'success', text: '✓ Gates determinísticos passaram.' },
            { type: 'success', text: '✓ Issues aprovadas integradas e roadmap atualizado.' },
            { type: 'warn', text: '! Gates humanos aparecem no harness quando uma decisão é necessária.' },
            { type: 'info', text: '├── Visibilidade opcional: /gantry-dashboard' },
            { type: 'success', text: '✓ Evidências finais e handoff prontos.' },
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
      title: 'As Quatro Skills',
      badge: 'PACOTE: 4 SKILLS',
      subtitle:
        'O Gantry oferece quatro skills focadas: configuração única do repositório, planejamento standalone, implementação automática e visibilidade read-only dos Runs.',
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
      planTitle: 'gantry-plan',
      planBadge: 'Planejamento',
      planDesc:
        'Transforma um objetivo livre ou uma Spec existente em Spec verificada, Issues verticais, uma decomposição orçada e um gate explícito de aprovação do operador.',
      planBullet1Title: 'Gate Socrático:',
      planBullet1Desc: 'Esclarece escopo, seams, não-objetivos e cenários.',
      planBullet2Title: 'Spec & Issues:',
      planBullet2Desc: 'Escreve a Spec e o conjunto de Issues verticais.',
      planBullet3Title: 'Parada para Aprovação:',
      planBullet3Desc: 'Nunca inicia implementação antes da aprovação do operador.',
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
        'Tier Suportado. Runner CLI direto com argumentos de modelo por função, verificação independente de Crítico comprovada em execuções reais.',
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
