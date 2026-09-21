import React, { useState, useEffect } from 'react';
import { getStoredLocale, LOCALE_CHANGE_EVENT } from '../i18n/client';
import { translations, type Locale } from '../i18n/translations';

export type StageId = 'setup' | 'plan' | 'approve' | 'implement' | 'verify' | 'handoff';

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

const STAGE_IDS: StageId[] = ['setup', 'plan', 'approve', 'implement', 'verify', 'handoff'];

function buildStages(locale: Locale): StageData[] {
  const dict = translations[locale]?.simulator ?? translations.en.simulator;
  const stagesDict = dict.stages;

  return [
    {
      id: 'setup',
      index: 0,
      number: '01',
      name: stagesDict.setup.name,
      shortName: stagesDict.setup.shortName,
      deterministicScript: {
        command: stagesDict.setup.terminalCommand,
        description: stagesDict.setup.scriptDescription,
        invariants: stagesDict.setup.scriptInvariants,
      },
      agentRole: {
        name: stagesDict.setup.agentName,
        model: stagesDict.setup.agentModel,
        responsibilities: stagesDict.setup.agentResponsibilities,
        adversarial: false,
      },
      terminal: {
        prompt: stagesDict.setup.terminalPrompt,
        command: stagesDict.setup.terminalCommand,
        lines: stagesDict.setup.terminalLines,
        jsonEvent: {
          event: 'setup.completed',
          repository: 'otp-service',
          policy: '.gantry/config.json',
          status: 'ready-for-planning',
          timestamp: '2026-09-17T18:00:00Z',
        },
      },
    },
    {
      id: 'plan',
      index: 1,
      number: '02',
      name: stagesDict.plan.name,
      shortName: stagesDict.plan.shortName,
      deterministicScript: {
        command: stagesDict.plan.terminalCommand,
        description: stagesDict.plan.scriptDescription,
        invariants: stagesDict.plan.scriptInvariants,
      },
      agentRole: {
        name: stagesDict.plan.agentName,
        model: stagesDict.plan.agentModel,
        responsibilities: stagesDict.plan.agentResponsibilities,
        adversarial: false,
      },
      terminal: {
        prompt: stagesDict.plan.terminalPrompt,
        command: stagesDict.plan.terminalCommand,
        lines: stagesDict.plan.terminalLines,
        jsonEvent: {
          event: 'plan.ready-for-approval',
          spec: 'login-otp',
          issues: 3,
          waves: 2,
          status: 'awaiting-operator',
        },
      },
    },
    {
      id: 'approve',
      index: 2,
      number: '03',
      name: stagesDict.approve.name,
      shortName: stagesDict.approve.shortName,
      deterministicScript: {
        command: stagesDict.approve.terminalCommand,
        description: stagesDict.approve.scriptDescription,
        invariants: stagesDict.approve.scriptInvariants,
      },
      agentRole: {
        name: stagesDict.approve.agentName,
        model: stagesDict.approve.agentModel,
        responsibilities: stagesDict.approve.agentResponsibilities,
        adversarial: false,
      },
      terminal: {
        prompt: stagesDict.approve.terminalPrompt,
        command: stagesDict.approve.terminalCommand,
        lines: stagesDict.approve.terminalLines,
        jsonEvent: {
          event: 'plan.approved',
          spec: 'login-otp',
          issues: ['login-otp#01', 'login-otp#02', 'login-otp#03'],
          status: 'ready-for-agent',
        },
      },
    },
    {
      id: 'implement',
      index: 3,
      number: '04',
      name: stagesDict.implement.name,
      shortName: stagesDict.implement.shortName,
      deterministicScript: {
        command: stagesDict.implement.terminalCommand,
        description: stagesDict.implement.scriptDescription,
        invariants: stagesDict.implement.scriptInvariants,
      },
      agentRole: {
        name: stagesDict.implement.agentName,
        model: stagesDict.implement.agentModel,
        responsibilities: stagesDict.implement.agentResponsibilities,
        adversarial: false,
      },
      terminal: {
        prompt: stagesDict.implement.terminalPrompt,
        command: stagesDict.implement.terminalCommand,
        lines: stagesDict.implement.terminalLines,
        jsonEvent: {
          event: 'run.started',
          spec: 'login-otp',
          scope: 'all-approved-issues',
          status: 'implementing',
        },
      },
    },
    {
      id: 'verify',
      index: 4,
      number: '05',
      name: stagesDict.verify.name,
      shortName: stagesDict.verify.shortName,
      deterministicScript: {
        command: stagesDict.verify.terminalCommand,
        description: stagesDict.verify.scriptDescription,
        invariants: stagesDict.verify.scriptInvariants,
      },
      agentRole: {
        name: stagesDict.verify.agentName,
        model: stagesDict.verify.agentModel,
        responsibilities: stagesDict.verify.agentResponsibilities,
        adversarial: true,
      },
      terminal: {
        prompt: stagesDict.verify.terminalPrompt,
        command: stagesDict.verify.terminalCommand,
        lines: stagesDict.verify.terminalLines,
        jsonEvent: {
          event: 'critic.accepted',
          spec: 'login-otp',
          issue: 'login-otp#02',
          role: 'critic',
          verdict: 'ACCEPTED',
          criteria: '5/5',
        },
      },
    },
    {
      id: 'handoff',
      index: 5,
      number: '06',
      name: stagesDict.handoff.name,
      shortName: stagesDict.handoff.shortName,
      deterministicScript: {
        command: stagesDict.handoff.terminalCommand,
        description: stagesDict.handoff.scriptDescription,
        invariants: stagesDict.handoff.scriptInvariants,
      },
      agentRole: {
        name: stagesDict.handoff.agentName,
        model: stagesDict.handoff.agentModel,
        responsibilities: stagesDict.handoff.agentResponsibilities,
        adversarial: false,
      },
      terminal: {
        prompt: stagesDict.handoff.terminalPrompt,
        command: stagesDict.handoff.terminalCommand,
        lines: stagesDict.handoff.terminalLines,
        jsonEvent: {
          event: 'run.finished',
          spec: 'login-otp',
          issues_done: 3,
          gates: 'passed',
          handoff: 'ready',
        },
      },
    },
  ];
}

export function PipelineSimulator() {
  const [locale, setLocale] = useState<Locale>('en');
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);

  useEffect(() => {
    setLocale(getStoredLocale());

    const handleLocaleChange = (e: Event) => {
      const customEvent = e as CustomEvent<{ locale: Locale }>;
      if (customEvent.detail?.locale) {
        setLocale(customEvent.detail.locale);
      }
    };

    window.addEventListener(LOCALE_CHANGE_EVENT, handleLocaleChange);
    return () => window.removeEventListener(LOCALE_CHANGE_EVENT, handleLocaleChange);
  }, []);

  const stages = buildStages(locale);
  const activeStage = stages[activeStageIndex] ?? stages[0];
  const dict = translations[locale]?.simulator ?? translations.en.simulator;

  // Keyboard navigation for accessibility and rapid exploration
  const handleTabKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      e.stopPropagation();
      const nextIdx = index < stages.length - 1 ? index + 1 : 0;
      setActiveStageIndex(nextIdx);
      const nextTab = document.getElementById(`stage-tab-${stages[nextIdx].id}`);
      nextTab?.focus();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      e.stopPropagation();
      const prevIdx = index > 0 ? index - 1 : stages.length - 1;
      setActiveStageIndex(prevIdx);
      const prevTab = document.getElementById(`stage-tab-${stages[prevIdx].id}`);
      prevTab?.focus();
    } else if (e.key === 'Home') {
      e.preventDefault();
      e.stopPropagation();
      setActiveStageIndex(0);
      document.getElementById(`stage-tab-${stages[0].id}`)?.focus();
    } else if (e.key === 'End') {
      e.preventDefault();
      e.stopPropagation();
      const lastIdx = stages.length - 1;
      setActiveStageIndex(lastIdx);
      document.getElementById(`stage-tab-${stages[lastIdx].id}`)?.focus();
    }
  };

  const handleNext = () => {
    if (activeStageIndex < stages.length - 1) {
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
            {dict.headerTitle}
          </span>
        </div>
        <div className="flex items-center space-x-2 text-[11px] text-slate-400">
          <span>{dict.progressLabel}</span>
          <span className="px-2 py-0.5 bg-obsidian-800 border border-obsidian-700 text-amber-accent font-bold">
            {dict.stageLabel} {activeStage.number} / {dict.ofStages}
          </span>
        </div>
      </div>

      {/* Stage Selector Bar (Indicators: Completed, Active, Pending) */}
      <div
        role="tablist"
        aria-label="Gantry SDLC Pipeline Stages"
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 border-b border-obsidian-700 bg-obsidian-950/40 text-xs font-mono"
      >
        {stages.map((stage, idx) => {
          const isActive = idx === activeStageIndex;
          const isCompleted = idx < activeStageIndex;

          let statusBadge = locale === 'pt-br' ? 'PENDENTE' : 'PENDING';
          let statusBadgeClass = 'text-slate-400 bg-obsidian-900/50 border-obsidian-800';

          if (isActive) {
            statusBadge = locale === 'pt-br' ? 'ATIVO' : 'ACTIVE';
            statusBadgeClass = 'text-amber-glow bg-amber-glow/10 border-amber-glow/60 font-bold';
          } else if (isCompleted) {
            statusBadge = locale === 'pt-br' ? 'VERIFICADO' : 'VERIFIED';
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
                  : 'bg-obsidian-950/40 text-slate-400 hover:text-slate-300 hover:bg-obsidian-900/40'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <span className={`text-[11px] font-bold ${isActive ? 'text-amber-glow' : 'text-slate-400'}`}>
                  {dict.stageLabel} {stage.number}
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
        {/* Left Column: Skill guarantees & Agent Role Contract */}
        <div className="lg:col-span-6 p-5 sm:p-6 border-b lg:border-b-0 lg:border-r border-obsidian-700 space-y-6">
          {/* Header & Description */}
          <div>
            <div className="flex items-center space-x-2 text-xs font-mono text-amber-accent mb-1.5">
              <span>{dict.phaseDetails} {activeStage.number}</span>
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

          {/* Section A: Recommended skill invocation and deterministic guarantees */}
          <div className="border border-obsidian-700 bg-obsidian-950/70 p-4 space-y-3 font-mono">
            <div className="flex items-center justify-between border-b border-obsidian-800 pb-2">
              <span className="text-xs font-bold text-amber-glow uppercase tracking-wider flex items-center space-x-1.5">
                <span>⚙</span>
                <span>{dict.scriptInvariantsTitle}</span>
              </span>
              <span className="text-[10px] text-slate-400 uppercase">{dict.interfaceLabel}</span>
            </div>

            <div className="text-xs space-y-1">
              <span className="text-[10px] text-slate-400 uppercase block">{dict.invocationLabel}</span>
              <code
                tabIndex={0}
                role="region"
                aria-label="Recommended Gantry skill invocation"
                className="text-amber-accent bg-obsidian-900 border border-obsidian-800 px-2 py-1 block text-xs whitespace-pre-wrap break-words focus:outline-none focus:ring-1 focus:ring-amber-glow"
              >
                {activeStage.deterministicScript.command}
              </code>
            </div>

            <ul className="space-y-1.5 text-xs text-slate-300 pt-1">
              {activeStage.deterministicScript.invariants.map((inv, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="text-amber-glow font-bold">■</span>
                  <span className="leading-snug">{inv}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Section B: Agent Role & Adversarial Guard */}
          <div className="border border-obsidian-700 bg-obsidian-950/70 p-4 space-y-3 font-mono">
            <div className="flex items-center justify-between border-b border-obsidian-800 pb-2">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                <span>🤖</span>
                <span>{dict.agentRoleTitle}: {activeStage.agentRole.name.toUpperCase()}</span>
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.2 border uppercase font-bold ${
                  activeStage.agentRole.adversarial
                    ? 'text-red-400 bg-red-950/50 border-red-800/80'
                    : 'text-amber-glow bg-amber-glow/10 border-amber-glow/40'
                }`}
              >
                {activeStage.agentRole.adversarial ? dict.adversarialBadge : dict.cooperativeBadge}
              </span>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase mr-2">{dict.modelLabel}</span>
                <span className="text-slate-300 font-bold">{activeStage.agentRole.model}</span>
              </div>
              <span className="text-[10px] text-slate-400">
                {activeStage.agentRole.adversarial
                  ? 'Fresh independent agent verification'
                  : 'Isolated worktree implementation'}
              </span>
            </div>

            <div className="space-y-1.5 pt-1">
              <span className="text-[10px] text-slate-400 uppercase block">{dict.responsibilitiesLabel}</span>
              <ul className="space-y-1 text-xs text-slate-300">
                {activeStage.agentRole.responsibilities.map((resp, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-amber-accent">›</span>
                    <span className="leading-snug">{resp}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Right Column: Console / Terminal Output & Structured Runlog Preview */}
        <div className="lg:col-span-6 bg-obsidian-950 flex flex-col justify-between font-mono">
          {/* Terminal Title Bar */}
          <div className="border-b border-obsidian-700 px-4 py-2.5 bg-obsidian-900/80 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-none bg-emerald-500"></span>
              <span className="text-slate-300 font-bold uppercase tracking-wider">
                {dict.terminalStreamTitle}
              </span>
            </div>
            <span className="text-[11px] text-slate-400">
              {dict.terminalExecTag}
            </span>
          </div>

          {/* Terminal Command Stream */}
          <div
            data-testid="terminal-stream"
            tabIndex={0}
            aria-label="Simulated Terminal Output"
            className="p-4 sm:p-5 space-y-2 text-xs overflow-y-auto max-h-[300px] sm:max-h-[360px] bg-obsidian-950/90 focus:outline-none focus:ring-1 focus:ring-amber-glow"
          >
            {/* Shell Prompt & Command */}
            <div className="flex items-center space-x-2 text-slate-200 pb-2 border-b border-obsidian-850">
              <span className="text-amber-glow font-bold select-none">{activeStage.terminal.prompt}</span>
              <code className="text-slate-100 font-semibold">{activeStage.terminal.command}</code>
            </div>

            {/* Execution Lines */}
            <div className="space-y-1 pt-1 font-mono">
              {activeStage.terminal.lines.map((line, idx) => {
                let colorClass = 'text-slate-400';
                if (line.type === 'success') colorClass = 'text-emerald-400';
                if (line.type === 'warn') colorClass = 'text-amber-glow font-bold';
                if (line.type === 'info') colorClass = 'text-slate-300';
                if (line.type === 'dim') colorClass = 'text-slate-400';

                return (
                  <div key={idx} className={`leading-relaxed ${colorClass}`}>
                    {line.text}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Structured Event Log Output Panel (RFC 6901 / Runlog JSON preview) */}
          <div className="border-t border-obsidian-700 p-4 bg-obsidian-900/60">
            <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2">
              <span className="uppercase text-amber-accent font-bold">
                {dict.jsonLogTitle}
              </span>
              <span className="text-slate-400 font-mono">APPEND-ONLY // SNAPSHOT</span>
            </div>
            <pre
              data-testid="json-event-log"
              tabIndex={0}
              role="region"
              aria-label="JSON Event Log"
              className="bg-obsidian-950 border border-obsidian-800 p-3 text-[11px] text-slate-300 overflow-x-auto font-mono leading-tight max-h-28 focus:outline-none focus:ring-1 focus:ring-amber-glow"
            >
              {JSON.stringify(activeStage.terminal.jsonEvent, null, 2)}
            </pre>
          </div>

          {/* Stepper Navigation Footer */}
          <div className="border-t border-obsidian-700 p-4 bg-obsidian-950 flex items-center justify-between gap-4">
            <button
              type="button"
              data-testid="prev-stage-btn"
              onClick={handlePrev}
              disabled={activeStageIndex === 0}
              className={`px-3 py-1.5 text-xs font-mono uppercase font-bold border flex items-center space-x-1 ${
                activeStageIndex === 0
                  ? 'opacity-40 cursor-not-allowed border-obsidian-800 text-slate-400'
                  : 'border-obsidian-700 hover:border-amber-glow text-slate-200 hover:text-amber-glow bg-obsidian-900 cursor-pointer'
              }`}
            >
              <span>←</span>
              <span>{dict.prevStageBtn}</span>
            </button>

            <div className="text-[11px] text-slate-400 font-mono">
              STAGE {activeStage.number} OF 06
            </div>

            <button
              type="button"
              data-testid="next-stage-btn"
              onClick={handleNext}
              disabled={activeStageIndex === stages.length - 1}
              className={`px-3 py-1.5 text-xs font-mono uppercase font-bold border flex items-center space-x-1 ${
                activeStageIndex === stages.length - 1
                  ? 'opacity-40 cursor-not-allowed border-obsidian-800 text-slate-400'
                  : 'border-amber-glow/60 bg-amber-glow/10 text-amber-glow hover:bg-amber-glow hover:text-obsidian-950 cursor-pointer'
              }`}
            >
              <span>{dict.nextStageBtn}</span>
              <span>→</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
