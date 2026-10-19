import { translations, type Locale } from './translations';

export const LOCALE_STORAGE_KEY = 'gantry_locale';
export const LOCALE_CHANGE_EVENT = 'gantry:locale-change';

export function getStoredLocale(): Locale {
  if (typeof window === 'undefined') return 'en';
  try {
    const val = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (val === 'pt-br' || val === 'en') {
      return val;
    }
  } catch {
    // ignore
  }
  return 'en';
}

export function setStoredLocale(locale: Locale): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    document.documentElement.lang = locale;
    window.dispatchEvent(
      new CustomEvent(LOCALE_CHANGE_EVENT, { detail: { locale } })
    );
  } catch {
    // ignore
  }
}

function getNestedTranslation(obj: any, path: string): string | undefined {
  const parts = path.split('.');
  let current = obj;
  for (const part of parts) {
    if (current == null) return undefined;
    current = current[part];
  }
  return typeof current === 'string' ? current : undefined;
}

export function updateDomTranslations(locale: Locale): void {
  if (typeof document === 'undefined') return;
  const dict = translations[locale];
  if (!dict) return;

  const elements = document.querySelectorAll<HTMLElement>('[data-i18n]');
  elements.forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (!key) return;
    // textContent would delete element children, such as a nested code tag.
    if (el.children.length > 0) return;
    const text = getNestedTranslation(dict, key);
    if (text !== undefined) {
      el.textContent = text;
    }
  });
}
