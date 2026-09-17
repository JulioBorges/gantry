import React, { useState, useEffect } from 'react';
import { getStoredLocale, LOCALE_CHANGE_EVENT } from '../i18n/client';
import { translations, type Locale } from '../i18n/translations';

export type HarnessId = 'claude' | 'opencode' | 'codex' | 'antigravity' | 'cursor';

export interface HarnessConfig {
  id: HarnessId;
  name: string;
  badge: string;
  command: string;
  altCommand?: string;
  tier: 'Reference' | 'Supported' | 'Compatible';
}

export const HARNESSES: HarnessConfig[] = [
  {
    id: 'claude',
    name: 'Claude Code',
    badge: 'REFERENCE',
    command: 'npx skills add JulioBorges/gantry',
    altCommand: 'npx @julioborges/gantry setup --harness claude',
    tier: 'Reference',
  },
  {
    id: 'opencode',
    name: 'OpenCode',
    badge: 'COMPATIBLE',
    command: 'npx skills add JulioBorges/gantry',
    altCommand: 'npx @julioborges/gantry setup --harness opencode',
    tier: 'Compatible',
  },
  {
    id: 'codex',
    name: 'Codex',
    badge: 'SUPPORTED',
    command: 'npx skills add JulioBorges/gantry',
    altCommand: 'npx @julioborges/gantry setup --harness codex',
    tier: 'Supported',
  },
  {
    id: 'antigravity',
    name: 'Gemini / Antigravity',
    badge: 'SUPPORTED',
    command: 'npx skills add JulioBorges/gantry',
    altCommand: 'npx @julioborges/gantry setup --harness antigravity',
    tier: 'Supported',
  },
  {
    id: 'cursor',
    name: 'Cursor',
    badge: 'COMPATIBLE',
    command: 'npx skills add JulioBorges/gantry',
    altCommand: 'npx @julioborges/gantry setup --harness cursor',
    tier: 'Compatible',
  },
];

export function InstallWidget() {
  const [selectedHarnessId, setSelectedHarnessId] = useState<HarnessId>('claude');
  const [copied, setCopied] = useState<boolean>(false);
  const [locale, setLocale] = useState<Locale>('en');

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

  const activeHarness = HARNESSES.find((h) => h.id === selectedHarnessId) ?? HARNESSES[0];
  const dict = translations[locale]?.install ?? translations.en.install;
  const description = dict.harnessDescriptions[activeHarness.id];

  const handleCopy = async () => {
    const textToCopy = activeHarness.command;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(textToCopy);
      } else {
        const textArea = document.createElement('textarea');
        textArea.value = textToCopy;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      data-testid="install-widget"
      className="border border-obsidian-700 bg-obsidian-900/90 rounded-none overflow-hidden shadow-2xl backdrop-blur-sm"
    >
      {/* Widget Header bar */}
      <div className="flex flex-wrap items-center justify-between border-b border-obsidian-700 px-4 py-2.5 bg-obsidian-950/70 text-xs">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-none bg-amber-glow animate-pulse"></span>
          <span className="font-mono uppercase tracking-wider text-slate-300 font-bold">
            {dict.quickInstallTitle}
          </span>
        </div>
        <div className="flex items-center space-x-2 font-mono text-[11px] text-slate-400">
          <span className="px-1.5 py-0.5 bg-obsidian-800 border border-obsidian-700 text-amber-accent">
            TIER: {activeHarness.tier.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Harness Tabs */}
      <div
        role="tablist"
        aria-label="Target Coding Harness"
        className="flex overflow-x-auto border-b border-obsidian-700 bg-obsidian-900 scrollbar-none text-xs font-mono"
      >
        {HARNESSES.map((harness) => {
          const isSelected = harness.id === selectedHarnessId;
          return (
            <button
              key={harness.id}
              role="tab"
              id={`tab-${harness.id}`}
              aria-selected={isSelected}
              aria-controls={`panel-${harness.id}`}
              data-testid={`tab-${harness.id}`}
              onClick={() => setSelectedHarnessId(harness.id)}
              className={`flex-1 min-w-[120px] px-3.5 py-2.5 text-center transition-all cursor-pointer border-b-2 flex items-center justify-center space-x-1.5 ${
                isSelected
                  ? 'border-amber-glow text-amber-glow bg-obsidian-850 font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-obsidian-800/60'
              }`}
            >
              <span>{harness.name}</span>
            </button>
          );
        })}
      </div>

      {/* Command Display & Copy Action */}
      <div
        id={`panel-${activeHarness.id}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeHarness.id}`}
        className="p-4 space-y-3 font-mono"
      >
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-obsidian-950 border border-obsidian-700/80 p-3">
          <div className="flex items-center space-x-2 text-xs sm:text-sm text-slate-200 overflow-x-auto">
            <span className="text-amber-glow select-none">$</span>
            <code data-testid="install-command" className="text-slate-100 font-bold whitespace-nowrap">
              {activeHarness.command}
            </code>
          </div>

          <button
            type="button"
            data-testid="copy-btn"
            onClick={handleCopy}
            className={`px-4 py-2 text-xs font-mono font-bold tracking-wider uppercase transition-all duration-150 flex items-center justify-center space-x-1.5 border cursor-pointer shrink-0 ${
              copied
                ? 'bg-amber-glow text-obsidian-950 border-amber-glow shadow-[0_0_10px_#ff9900]'
                : 'bg-obsidian-800 hover:bg-obsidian-700 text-slate-200 hover:text-amber-glow border-obsidian-600 hover:border-amber-accent'
            }`}
          >
            {copied ? (
              <>
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
                <span>{dict.copied}</span>
              </>
            ) : (
              <>
                <svg
                  className="w-3.5 h-3.5 text-amber-accent"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                  />
                </svg>
                <span>{dict.copy}</span>
              </>
            )}
          </button>
        </div>

        {/* Harness Context & Flags */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] text-slate-400 gap-2">
          <span>{description}</span>
          <span className="text-slate-500 font-mono">
            {dict.altSetupLabel} <code className="text-slate-400">{activeHarness.altCommand}</code>
          </span>
        </div>
      </div>
    </div>
  );
}
