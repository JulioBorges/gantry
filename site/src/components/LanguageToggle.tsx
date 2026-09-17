import React, { useEffect, useState } from 'react';
import { getStoredLocale, setStoredLocale, LOCALE_CHANGE_EVENT } from '../i18n/client';
import type { Locale } from '../i18n/translations';

export function LanguageToggle() {
  const [locale, setLocale] = useState<Locale>('en');

  useEffect(() => {
    // Initial load from storage
    const stored = getStoredLocale();
    setLocale(stored);

    const handleLocaleChange = (e: Event) => {
      const customEvent = e as CustomEvent<{ locale: Locale }>;
      if (customEvent.detail?.locale) {
        setLocale(customEvent.detail.locale);
      }
    };

    window.addEventListener(LOCALE_CHANGE_EVENT, handleLocaleChange);
    return () => window.removeEventListener(LOCALE_CHANGE_EVENT, handleLocaleChange);
  }, []);

  const handleSelect = (newLocale: Locale) => {
    if (newLocale !== locale) {
      setLocale(newLocale);
      setStoredLocale(newLocale);
    }
  };

  return (
    <div
      data-testid="language-toggle"
      className="inline-flex items-center border border-obsidian-700 bg-obsidian-950 p-0.5 font-mono text-[11px] sm:text-xs"
      role="group"
      aria-label="Language selector"
    >
      <button
        type="button"
        data-testid="lang-btn-en"
        data-active={locale === 'en' ? 'true' : 'false'}
        onClick={() => handleSelect('en')}
        className={`px-2 py-0.5 transition-colors uppercase font-bold focus:outline-none ${
          locale === 'en'
            ? 'bg-obsidian-800 text-amber-glow border border-amber-glow/40 shadow-sm'
            : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-900'
        }`}
        aria-pressed={locale === 'en'}
      >
        EN
      </button>

      <span className="text-obsidian-700 px-0.5 select-none">/</span>

      <button
        type="button"
        data-testid="lang-btn-pt"
        data-active={locale === 'pt-br' ? 'true' : 'false'}
        onClick={() => handleSelect('pt-br')}
        className={`px-2 py-0.5 transition-colors uppercase font-bold focus:outline-none ${
          locale === 'pt-br'
            ? 'bg-obsidian-800 text-amber-glow border border-amber-glow/40 shadow-sm'
            : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-900'
        }`}
        aria-pressed={locale === 'pt-br'}
      >
        PT
      </button>
    </div>
  );
}
