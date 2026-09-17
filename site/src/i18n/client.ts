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
    updateDomTranslations(locale);
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

  // Update elements with data-i18n (plain text)
  const elements = document.querySelectorAll<HTMLElement>('[data-i18n]');
  elements.forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (!key) return;
    const text = getNestedTranslation(dict, key);
    if (text !== undefined) {
      el.textContent = text;
    }
  });

  // Update elements with data-i18n-html (HTML markup preserved)
  const htmlElements = document.querySelectorAll<HTMLElement>('[data-i18n-html]');
  htmlElements.forEach((el) => {
    const key = el.getAttribute('data-i18n-html');
    if (!key) return;
    const html = getNestedTranslation(dict, key);
    if (html !== undefined) {
      el.innerHTML = html;
    }
  });
}
