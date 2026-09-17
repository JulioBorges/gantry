import React, { useState, useEffect } from 'react';

export type StageId = 'spec' | 'plan' | 'implement' | 'review' | 'critic' | 'gate';

export interface StageData {
  id: StageId;
  index: number;
  number: string;
  name: string;
  shortName: string;
  deterministicScript: {
    command: string;
    description: string;
    invariants: string[];
  };
  agentRole: {
    name: string;
    model: string;
    responsibilities: string[];
    adversarial: boolean;
  };
  terminal: {
    prompt: string;
    command: string;
    lines: Array<{
      type: 'cmd' | 'info' | 'success' | 'warn' | 'dim' | 'json';
      text: string;
    }>;
    jsonEvent: Record<string, unknown>;
  };
}

export const PIPELINE_STAGES: StageData[] = [
  {
    id: 'spec',
    index: 0,
    number: '01',
    name: 'Spec & Requirement Critic',
    shortName: '01. Spec & Critic',
    deterministicScript: {
      command: 'python3 .agents/skills/gantry/scripts/spec.py --check',
      description: 'Validates structural integrity of living spec before any slicing or planning begins.',
      invariants: [
        'Enforces mandatory Living Spec headings: Blueprint, Contract, Definition of Done, Scenarios.',
        'Refuses ambiguous requirements, unverified non-goals, or dangling dependencies.',
        'Deterministic zero-exit required before planning phase is unlocked.',
      ],
    },
    agentRole: {
      name: 'Requirement Critic',
      model: 'Critic Model (Read-Only)',
      responsibilities: [
        'Assesses ambiguity, coherence, and verifiability across all user scenarios.',
        'Emits blocking findings if any requirement cannot be verified objectively.',
        'Never edits the spec directly; operator amends spec on refutation.',
      ],
      adversarial: true,
    },
    terminal: {
      prompt: 'gantry@worktree:~$',
      command: 'python3 .agents/skills/gantry/scripts/spec.py --check .scratch/gantry-site/spec.md',
      lines: [
        { type: 'dim', text: '[spec.py] Checking structural compliance for spec.md...' },
        { type: 'info', text: '├── Validating sections: Blueprint, Contract, Definition of Done' },
        { type: 'info', text: '├── Checking Scenarios: 4 Gherkin scenarios discovered' },
        { type: 'success', text: '✓ Structure verified: 0 schema violations' },
        { type: 'dim', text: '[requirement-critic] Assessing ambiguity & testability...' },
        { type: 'success', text: '✓ Requirement Critic: ambiguity index 0.02 [CLEAN]' },
        { type: 'success', text: '✓ Specification passes preflight checks.' },
      ],
      jsonEvent: {
        event: 'spec.verified',
        spec: 'gantry-site',
        scenarios: 4,
        status: 'approved-for-planning',
        timestamp: '2026-09-17T18:00:00Z',
      },
    },
  },
  {
    id: 'plan',
    index: 1,
    number: '02',
    name: 'Planning & Context Budget',
    shortName: '02. Plan & Budget',
    deterministicScript: {
      command: 'python3 .agents/skills/gantry/scripts/frontier.py --scope <slug>',
      description: 'Constructs DAG blocker graph, computes execution waves, and enforces context token ceilings.',
      invariants: [
        'Blocker graph must remain a strict DAG with zero cycles.',
        'Every slice is an atomic vertical delivery with demonstrable acceptance criteria.',
        'Mandatory STOP: Planning outputs draft issues and halts for explicit operator approval.',
      ],
    },
    agentRole: {
      name: 'Planner Agent',
      model: 'Plan Model',
      responsibilities: [
        'Slices approved spec into vertical issues with clear file touches and acceptance criteria.',
        'Estimates context token footprint with budget.py to prevent window degradation.',
        'Stages draft markdown files under .scratch/<slug>/issues/.',
      ],
      adversarial: false,
    },
    terminal: {
      prompt: 'gantry@worktree:~$',
      command: 'python3 .agents/skills/gantry/scripts/frontier.py --scope gantry-site --json',
      lines: [
        { type: 'dim', text: '[frontier.py] Resolving dependency graph across 6 issues...' },
        { type: 'info', text: '├── Checking cycles: DAG validated (0 cycles)' },
        { type: 'info', text: '├── Scheduled Wave 12: gantry-site#01 (scaffold)' },
        { type: 'info', text: '├── Scheduled Wave 13: gantry-site#02 (hero), gantry-site#03 (simulator)' },
        { type: 'success', text: '✓ Wave breakdown computed: 5 total waves' },
        { type: 'warn', text: '⚠ MANDATORY STOP: 5 draft issues staged in .scratch/gantry-site/' },
        { type: 'warn', text: '  Waiting for explicit operator approval before ready-for-agent.' },
      ],
      jsonEvent: {
        event: 'plan.staged',
        scope: 'gantry-site',
        total_issues: 6,
        waves: 5,
        operator_approval: 'pending',
      },
    },
  },
  {
    id: 'implement',
    index: 2,
    number: '03',
    name: 'TDD Implementer',
    shortName: '03. TDD Implement',
    deterministicScript: {
      command: 'git worktree add .worktrees/<branch> && guard.py check',
      description: 'Enforces worktree isolation, branch naming templates, and test-first red-green cycles.',
      invariants: [
        'Each issue executes in its own isolated worktree and git branch.',
        'Guard hooks block destructive git operations (push, reset --hard, dirty commits).',
        'Tests must be committed or written in RED state before implementation code.',
      ],
    },
    agentRole: {
      name: 'Implementer Agent',
      model: 'Implement Model',
      responsibilities: [
        'Follows strict TDD: writes failing test first, writes minimal code to pass, refactors.',
        'Validates changes locally with full test suite before requesting review.',
        'Confines file touch surface strictly to paths defined in the issue.',
      ],
      adversarial: false,
    },
    terminal: {
      prompt: 'gantry@worktree:~/worktrees/gantry-site-02$',
      command: 'npm run test:e2e',
      lines: [
        { type: 'dim', text: '[git] Created worktree .worktrees/gantry-site-02 on branch feat/gantry-site-02' },
        { type: 'dim', text: '[tdd] Running test suite in RED phase...' },
        { type: 'warn', text: '✗ FAIL: tests/hero.spec.ts: Hero renders quick install widget (widget not found)' },
        { type: 'dim', text: '[tdd] Implementing InstallWidget.tsx and HeroSection.astro...' },
        { type: 'dim', text: '[tdd] Re-running test suite in GREEN phase...' },
        { type: 'success', text: '✓ PASS: tests/hero.spec.ts: Hero renders quick install widget (432ms)' },
        { type: 'success', text: '✓ Hook pre-commit: Guard validated, 0 unauthorized edits.' },
      ],
      jsonEvent: {
        event: 'phase.started',
        phase: 'Implement',
        issue: 'gantry-site#02',
        tdd_cycle: 'green',
        worktree: '.worktrees/gantry-site-02',
      },
    },
  },
  {
    id: 'review',
    index: 3,
    number: '04',
    name: 'Two-Axis Reviewer',
    shortName: '04. Two-Axis Review',
    deterministicScript: {
      command: 'python3 .agents/skills/gantry/scripts/result.py review --check',
      description: 'Runs parallel subagents reviewing changes against two disjoint axes: Standards and Spec.',
      invariants: [
        'Standards review: verifies coding patterns, architecture, lint, and types.',
        'Spec review: verifies full alignment against originating spec scenarios.',
        'Review findings emit RFC 6901 JSON pointers; exactly one fix pass permitted.',
      ],
    },
    agentRole: {
      name: 'Reviewer Agents (Parallel)',
      model: 'Review Model',
      responsibilities: [
        'Subagent A (Standards): Inspects code quality, error handling, accessibility, and zero-slop.',
        'Subagent B (Spec): Verifies that delivered functionality matches the approved scope.',
        'Produces structured review.finding event with actionable remediations.',
      ],
      adversarial: false,
    },
    terminal: {
      prompt: 'gantry@worktree:~$',
      command: 'python3 .agents/skills/gantry/scripts/result.py review --check',
      lines: [
        { type: 'dim', text: '[review] Spawning parallel review subagents...' },
        { type: 'info', text: '├── Subagent [Standards]: Running ESLint, Prettier, TypeScript checks...' },
        { type: 'success', text: '│   ✓ Standards Review passed: 0 lints, 0 type errors' },
        { type: 'info', text: '├── Subagent [Spec]: Cross-checking against .scratch/gantry-site/spec.md...' },
        { type: 'success', text: '│   ✓ Spec Review passed: 4/4 acceptance criteria covered' },
        { type: 'success', text: '✓ Result Contract validated. Staging for Adversarial Critic.' },
      ],
      jsonEvent: {
        event: 'review.finding',
        issue: 'gantry-site#02',
        verdict: 'clean',
        axes: ['standards', 'spec'],
        findings_count: 0,
      },
    },
  },
  {
    id: 'critic',
    index: 4,
    number: '05',
    name: 'Adversarial Critic',
    shortName: '05. Adversarial Critic',
    deterministicScript: {
      command: 'python3 .agents/skills/gantry/scripts/runlog.py inflight --unit-id gantry',
      description: 'Fresh independent agent verification. Refutations consume correction budget.',
      invariants: [
        'Fresh subagent instance with zero shared memory with Implementer or Reviewer.',
        'Actively attempts to disprove delivery by running verification commands directly.',
        'Zero self-approval: only Critic acceptance allows issue to proceed to integration.',
      ],
    },
    agentRole: {
      name: 'Adversarial Critic',
      model: 'Critic Model (Adversarial)',
      responsibilities: [
        'Executes Playwright tests, edge-case assertions, and responsive viewport checks.',
        'Verifies evidence directly in the isolated worktree without relying on agent claims.',
        'Refutes incomplete deliveries; bounded correction budget prevents infinite loops.',
      ],
      adversarial: true,
    },
    terminal: {
      prompt: 'gantry@worktree:~$',
      command: 'python3 .agents/skills/gantry/scripts/runlog.py critic-verify --issue gantry-site#02',
      lines: [
        { type: 'dim', text: '[critic] Starting fresh adversarial verification pass...' },
        { type: 'info', text: '[critic] Running independent Playwright suite on chromium & mobile...' },
        { type: 'success', text: '├── Criterion 1 (Tagline & Crane Visual): verified' },
        { type: 'success', text: '├── Criterion 2 (Multi-harness Tabs): verified (5/5 harnesses active)' },
        { type: 'success', text: '├── Criterion 3 (Clipboard Copy): verified with visual confirmation' },
        { type: 'success', text: '├── Criterion 4 (Mobile Responsiveness): verified across 375px & 1280px' },
        { type: 'success', text: '✓ Critic Verdict: ACCEPTED. Zero refutations. Proceed to merge.' },
      ],
      jsonEvent: {
        event: 'subagent.stopped',
        role: 'critic',
        issue: 'gantry-site#02',
        verdict: 'ACCEPTED',
        corrections_spent: 0,
        corrections_budget: 3,
      },
    },
  },
  {
    id: 'gate',
    index: 5,
    number: '06',
    name: 'Serial Integration Gate',
    shortName: '06. Integration Gate',
    deterministicScript: {
      command: 'python3 .agents/skills/gantry/scripts/gates.py && roadmap.py done',
      description: 'Serial branch merge, differential RFC 6901 gate validation, and atomic roadmap update.',
      invariants: [
        'Merged serially: one accepted issue at a time into target branch.',
        'Differential quality gates run post-merge; first red gate aborts Run.',
        'roadmap.py done is the SOLE authority that marks issue complete and updates roadmap.',
      ],
    },
    agentRole: {
      name: 'Integrator & Operator',
      model: 'System / Orchestrator',
      responsibilities: [
        'Fast-forwards verified branch into target branch after differential gates pass.',
        'Atomically updates ROADMAP.md and issue status to done.',
        'Cleans up isolated worktree and preserves append-only Run Log.',
      ],
      adversarial: false,
    },
    terminal: {
      prompt: 'gantry@worktree:~$',
      command: 'python3 .agents/skills/gantry/scripts/roadmap.py done gantry-site#02',
      lines: [
        { type: 'dim', text: '[gates.py] Running differential quality gates post-merge...' },
        { type: 'success', text: '├── Gate 1: Typecheck [PASS - 0 errors]' },
        { type: 'success', text: '├── Gate 2: E2E Playwright [PASS - 2/2 suites green]' },
        { type: 'dim', text: '[roadmap.py] Updating authoritative delivery records...' },
        { type: 'info', text: '├── Setting Status: done in .scratch/gantry-site/issues/02-...' },
        { type: 'info', text: '├── Updating ROADMAP.md execution wave 13 status...' },
        { type: 'success', text: '✓ Issue gantry-site#02 marked done. Roadmap: 28/32 issues.' },
        { type: 'success', text: '✓ Run Log appended: issue.done recorded.' },
      ],
      jsonEvent: {
        event: 'issue.done',
        issue: 'gantry-site#02',
        gates_verdict: 'green',
        roadmap_drift: 'none',
        timestamp: '2026-09-17T18:05:00Z',
      },
    },
  },
];

export function PipelineSimulator() {
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);

  const activeStage = PIPELINE_STAGES[activeStageIndex];

  // Keyboard navigation for accessibility and rapid exploration
  const handleTabKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      e.stopPropagation();
      const nextIdx = index < PIPELINE_STAGES.length - 1 ? index + 1 : 0;
      setActiveStageIndex(nextIdx);
      const nextTab = document.getElementById(`stage-tab-${PIPELINE_STAGES[nextIdx].id}`);
      nextTab?.focus();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      e.stopPropagation();
      const prevIdx = index > 0 ? index - 1 : PIPELINE_STAGES.length - 1;
      setActiveStageIndex(prevIdx);
      const prevTab = document.getElementById(`stage-tab-${PIPELINE_STAGES[prevIdx].id}`);
      prevTab?.focus();
    } else if (e.key === 'Home') {
      e.preventDefault();
      e.stopPropagation();
      setActiveStageIndex(0);
      document.getElementById(`stage-tab-${PIPELINE_STAGES[0].id}`)?.focus();
    } else if (e.key === 'End') {
      e.preventDefault();
      e.stopPropagation();
      const lastIdx = PIPELINE_STAGES.length - 1;
      setActiveStageIndex(lastIdx);
      document.getElementById(`stage-tab-${PIPELINE_STAGES[lastIdx].id}`)?.focus();
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented) return;
      // If user is inside an input/textarea, ignore
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      if (e.key === 'ArrowRight') {
        setActiveStageIndex((prev) => (prev < PIPELINE_STAGES.length - 1 ? prev + 1 : prev));
      } else if (e.key === 'ArrowLeft') {
        setActiveStageIndex((prev) => (prev > 0 ? prev - 1 : prev));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleNext = () => {
    if (activeStageIndex < PIPELINE_STAGES.length - 1) {
      setActiveStageIndex(activeStageIndex + 1);
    }
  };

  const handlePrev = () => {
    if (activeStageIndex > 0) {
      setActiveStageIndex(activeStageIndex - 1);
    }
  };

  return (
    <div
      data-testid="pipeline-simulator"
      className="border border-obsidian-700 bg-obsidian-900/90 rounded-none overflow-hidden shadow-2xl backdrop-blur-sm"
    >
      {/* Top telemetry bar */}
      <div className="flex flex-wrap items-center justify-between border-b border-obsidian-700 px-4 py-3 bg-obsidian-950/80 text-xs font-mono">
        <div className="flex items-center space-x-3">
          <span className="w-2.5 h-2.5 bg-amber-glow animate-pulse"></span>
          <span className="font-bold tracking-wider text-slate-200 uppercase">
            PIPELINE SIMULATOR // DETERMINISTIC SDLC RIG
          </span>
        </div>
        <div className="flex items-center space-x-2 text-[11px] text-slate-400">
          <span>PROGRESS:</span>
          <span className="px-2 py-0.5 bg-obsidian-800 border border-obsidian-700 text-amber-accent font-bold">
            STAGE {activeStage.number} / 06
          </span>
        </div>
      </div>

      {/* Stage Selector Bar (Indicators: Completed, Active, Pending) */}
      <div
        role="tablist"
        aria-label="Gantry SDLC Pipeline Stages"
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 border-b border-obsidian-700 bg-obsidian-950/40 text-xs font-mono"
      >
        {PIPELINE_STAGES.map((stage, idx) => {
          const isActive = idx === activeStageIndex;
          const isCompleted = idx < activeStageIndex;
          const isPending = idx > activeStageIndex;

          let statusBadge = 'PENDING';
          let statusBadgeClass = 'text-slate-500 bg-obsidian-900/50 border-obsidian-800';

          if (isActive) {
            statusBadge = 'ACTIVE';
            statusBadgeClass = 'text-amber-glow bg-amber-glow/10 border-amber-glow/40 animate-pulse';
          } else if (isCompleted) {
            statusBadge = 'VERIFIED';
            statusBadgeClass = 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60';
          }

          return (
            <button
              key={stage.id}
              role="tab"
              id={`stage-tab-${stage.id}`}
              aria-selected={isActive}
              aria-controls={`stage-panel-${stage.id}`}
              data-testid={`stage-tab-${stage.id}`}
              data-active={isActive ? 'true' : 'false'}
              data-status={isActive ? 'active' : isCompleted ? 'completed' : 'pending'}
              tabIndex={isActive ? 0 : -1}
              onKeyDown={(e) => handleTabKeyDown(e, idx)}
              onClick={() => setActiveStageIndex(idx)}
              className={`p-3 text-left transition-all cursor-pointer border-r border-b lg:border-b-0 border-obsidian-700 relative group flex flex-col justify-between min-h-[76px] focus:outline-none focus:ring-1 focus:ring-amber-glow ${
                isActive
                  ? 'bg-obsidian-850 text-slate-100 border-t-2 border-t-amber-glow'
                  : isCompleted
                  ? 'bg-obsidian-950/80 text-slate-300 hover:bg-obsidian-900'
                  : 'bg-obsidian-950/40 text-slate-500 hover:text-slate-300 hover:bg-obsidian-900/40'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <span className={`text-[11px] font-bold ${isActive ? 'text-amber-glow' : 'text-slate-500'}`}>
                  STAGE {stage.number}
                </span>
                <span className={`text-[9px] px-1.5 py-0.2 border uppercase ${statusBadgeClass}`}>
                  {statusBadge}
                </span>
              </div>
              <div
                className={`text-xs font-semibold leading-tight transition-colors ${
                  isActive ? 'text-slate-100' : 'text-slate-400 group-hover:text-slate-200'
                }`}
              >
                {stage.name}
              </div>
            </button>
          );
        })}
      </div>

      {/* Main Simulator Content Grid (Split: Script/Agent Rules vs Console Terminal) */}
      <div
        id={`stage-panel-${activeStage.id}`}
        role="tabpanel"
        aria-labelledby={`stage-tab-${activeStage.id}`}
        className="grid grid-cols-1 lg:grid-cols-12 gap-0"
      >
        {/* Left Column: Script Invariants & Agent Role Contract */}
        <div className="lg:col-span-6 p-5 sm:p-6 border-b lg:border-b-0 lg:border-r border-obsidian-700 space-y-6">
          {/* Header & Description */}
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-amber-accent mb-1.5">
              <span>PHASE {activeStage.number} DETAILS</span>
              <span>//</span>
              <span className="uppercase">{activeStage.id}</span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold font-mono text-slate-100">
              {activeStage.name}
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 mt-2 font-mono leading-relaxed">
              {activeStage.deterministicScript.description}
            </p>
          </div>

          {/* Script Enforcement (Deterministic Code Rules) */}
          <div className="border border-obsidian-700 bg-obsidian-950/60 p-4 space-y-3 font-mono">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-glow uppercase tracking-wider flex items-center space-x-1.5">
                <span>⚡</span>
                <span>DETERMINISTIC SCRIPT INVARIANTS</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.5 bg-obsidian-800 border border-obsidian-700 text-slate-400">
                STRICT CODE
              </span>
            </div>
            <div className="text-xs bg-obsidian-900 border border-obsidian-800 p-2 text-slate-300">
              <code>{activeStage.deterministicScript.command}</code>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {activeStage.deterministicScript.invariants.map((inv, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-amber-glow font-bold mt-0.5">↳</span>
                  <span className="leading-snug">{inv}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Agent Role Contract */}
          <div className="border border-obsidian-700 bg-obsidian-950/60 p-4 space-y-3 font-mono">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                <span>🤖</span>
                <span>AGENT ROLE: {activeStage.agentRole.name.toUpperCase()}</span>
              </span>
              {activeStage.agentRole.adversarial && (
                <span className="text-[10px] px-1.5 py-0.5 bg-amber-950/60 border border-amber-800 text-amber-glow font-bold uppercase">
                  ADVERSARIAL
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400">
              Assigned Model: <span className="text-amber-accent">{activeStage.agentRole.model}</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {activeStage.agentRole.responsibilities.map((resp, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-amber-accent font-bold mt-0.5">↳</span>
                  <span className="leading-snug">{resp}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Stepper Navigation Buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              data-testid="prev-stage-btn"
              onClick={handlePrev}
              disabled={activeStageIndex === 0}
              className={`px-3.5 py-2 text-xs font-mono font-bold uppercase border transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeStageIndex === 0
                  ? 'opacity-30 cursor-not-allowed border-obsidian-800 text-slate-600 bg-transparent'
                  : 'bg-obsidian-800 hover:bg-obsidian-700 text-slate-200 border-obsidian-600 hover:border-amber-accent'
              }`}
            >
              <span>← PREVIOUS PHASE</span>
            </button>

            <span className="text-xs text-slate-500 font-mono hidden sm:inline-block">
              Use <kbd className="px-1.5 py-0.5 bg-obsidian-800 border border-obsidian-700 text-slate-300">←</kbd>{' '}
              <kbd className="px-1.5 py-0.5 bg-obsidian-800 border border-obsidian-700 text-slate-300">→</kbd> to step
            </span>

            <button
              type="button"
              data-testid="next-stage-btn"
              onClick={handleNext}
              disabled={activeStageIndex === PIPELINE_STAGES.length - 1}
              className={`px-3.5 py-2 text-xs font-mono font-bold uppercase border transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeStageIndex === PIPELINE_STAGES.length - 1
                  ? 'opacity-30 cursor-not-allowed border-obsidian-800 text-slate-600 bg-transparent'
                  : 'bg-amber-accent hover:bg-amber-glow text-obsidian-950 border-amber-accent hover:border-amber-glow shadow-[0_0_10px_#ff9900]/30 font-extrabold'
              }`}
            >
              <span>NEXT PHASE →</span>
            </button>
          </div>
        </div>

        {/* Right Column: Industrial Terminal Console & JSON Event Log */}
        <div className="lg:col-span-6 bg-obsidian-950 flex flex-col justify-between font-mono text-xs">
          {/* Terminal Console Bar */}
          <div className="flex items-center justify-between border-b border-obsidian-700 px-4 py-2 bg-obsidian-900 text-slate-400">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500/80"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-green-500/80"></span>
              <span className="text-[11px] tracking-wider text-slate-300 font-bold ml-2">
                CONSOLE // TELEMETRY TRACE
              </span>
            </div>
            <span className="text-[10px] text-amber-glow">LIVE STREAM</span>
          </div>

          {/* Terminal Log Output */}
          <div data-testid="terminal-stream" className="p-4 sm:p-5 space-y-2 overflow-x-auto min-h-[260px]">
            {/* Command Prompt */}
            <div className="flex items-center space-x-2 text-slate-400">
              <span className="text-amber-glow font-bold">{activeStage.terminal.prompt}</span>
              <span className="text-slate-100 font-bold">{activeStage.terminal.command}</span>
            </div>

            {/* Trace Lines */}
            <div className="space-y-1 pt-2">
              {activeStage.terminal.lines.map((line, idx) => {
                let colorClass = 'text-slate-300';
                if (line.type === 'success') colorClass = 'text-emerald-400 font-semibold';
                if (line.type === 'warn') colorClass = 'text-amber-accent font-semibold';
                if (line.type === 'dim') colorClass = 'text-slate-500';
                if (line.type === 'info') colorClass = 'text-cyan-400';

                return (
                  <div key={idx} className={`leading-relaxed whitespace-pre-wrap ${colorClass}`}>
                    {line.text}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Append-Only JSON Run Log Viewer */}
          <div className="border-t border-obsidian-700 bg-obsidian-900/90 p-4 space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="uppercase tracking-wider font-bold text-slate-300 flex items-center space-x-1.5">
                <span className="text-amber-glow">◆</span>
                <span>APPEND-ONLY RUN LOG EVENT (RFC 6901)</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.2 bg-obsidian-800 border border-obsidian-700 text-amber-accent">
                EVENT: {String(activeStage.terminal.jsonEvent.event)}
              </span>
            </div>
            <pre
              data-testid="json-event-log"
              className="text-[11px] text-amber-glow/90 bg-obsidian-950 border border-obsidian-800 p-3 overflow-x-auto scrollbar-thin"
            >
              {JSON.stringify(activeStage.terminal.jsonEvent, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
