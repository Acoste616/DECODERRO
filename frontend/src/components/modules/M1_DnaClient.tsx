/**
 * ULTRA v3.0 - Module 1: DNA Client
 * ==================================
 * 
 * Renders holistic summary, main motivation, key levers, and red flags
 */

import { useTranslation } from '../../utils/i18n';
import type { IM1DnaClient } from '../../types';

interface Props {
  data: IM1DnaClient;
}

export default function M1_DnaClient({ data }: Props) {
  const { t } = useTranslation();

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        🧬 {t('modules.m1_title')}
      </h3>

      {/* Holistic Summary */}
      <div className="mb-4">
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          {t('modules.m1_holistic_summary')}
        </h4>
        <p className="text-sm">{data.holistic_summary}</p>
      </div>

      {/* Main Motivation */}
      <div className="mb-4">
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          {t('modules.m1_main_motivation')}
        </h4>
        <p className="text-sm">{data.main_motivation}</p>
      </div>

      {/* Key Levers */}
      <div className="mb-4">
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          ⚡ {t('modules.m1_key_levers')}
        </h4>
        <ul className="space-y-2">
          {data.key_levers.map((lever, idx) => (
            <li key={idx} className="text-sm">
              <div className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <div className="flex-1">
                  <div className="font-medium">{lever.argument}</div>
                  <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-0.5">
                    {lever.rationale}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Red Flags */}
      <div>
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          🚩 {t('modules.m1_red_flags')}
        </h4>
        <ul className="space-y-1">
          {data.red_flags.map((flag, idx) => (
            <li key={idx} className="text-sm flex items-start gap-2">
              <span className="text-red-500">⚠</span>
              <span>{flag}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
