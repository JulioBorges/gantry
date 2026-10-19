import { useEffect, useState } from 'react';
import { getStoredLocale, LOCALE_CHANGE_EVENT } from './client';
import type { Locale } from './translations';

/** Shared by the three islands that re-render when the operator switches locale. */
export function useLocale(): Locale {
  const [locale, setLocale] = useState<Locale>('en');

  useEffect(() => {
    setLocale(getStoredLocale());

    const handleLocaleChange = (event: Event) => {
      const next = (event as CustomEvent<{ locale: Locale }>).detail?.locale;
      if (next) setLocale(next);
    };

    window.addEventListener(LOCALE_CHANGE_EVENT, handleLocaleChange);
    return () => window.removeEventListener(LOCALE_CHANGE_EVENT, handleLocaleChange);
  }, []);

  return locale;
}
