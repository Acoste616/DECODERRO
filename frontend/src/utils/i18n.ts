/**
 * ULTRA v3.0 - Internationalization (i18n) Utility
 * ==================================================
 * 
 * Simple translation function that loads i18n_locales.json
 * and provides translations based on current language from Zustand store.
 */

import i18nData from '../../../backend/i18n_locales.json';
import type { TLanguage } from '../types';

/**
 * Get translation for a key path
 * @param key - Dot-notation path to translation (e.g., "view1_dashboard.title")
 * @param language - Language code (defaults to current store language)
 * @returns Translated string or key if not found
 */
export function t(key: string, language?: TLanguage): string {
  // Get language from parameter or use 'pl' as fallback
  const lang = language || 'pl';
  
  // Split key by dots to navigate nested object
  const keys = key.split('.');
  
  // Navigate through the i18n object
  let value: any = i18nData[lang];
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      // Key not found, return the key itself
      console.warn(`Translation not found for key: ${key} (language: ${lang})`);
      return key;
    }
  }
  
  return typeof value === 'string' ? value : key;
}

/**
 * Hook to use translations with current language from store
 */
import { useStore } from '../store/useStore';

export function useTranslation() {
  const currentLanguage = useStore((state) => state.current_language);
  
  return {
    t: (key: string) => t(key, currentLanguage),
    language: currentLanguage,
  };
}

export default t;
