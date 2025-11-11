/**
 * ULTRA v3.0 - Module 4: Deep Motivation
 * =======================================
 * 
 * Renders key insight and evidence quotes
 */

import { useTranslation } from '../../utils/i18n';
import type { IM4DeepMotivation } from '../../types';

interface Props {
  data: IM4DeepMotivation;
}

export default function M4_DeepMotivation({ data }: Props) {
  const { t } = useTranslation();

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        💡 {t('modules.m4_title')}
      </h3>

      {/* Key Insight */}
      <div className="mb-4 p-3 rounded bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500">
        <h4 className="font-semibold text-sm mb-2">{t('modules.m4_key_insight')}</h4>
        <p className="text-sm italic">{data.key_insight}</p>
      </div>

      {/* Evidence Quotes */}
      <div>
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-2">
          💬 {t('modules.m4_evidence_quotes')}
        </h4>
        <div className="space-y-2">
          {data.evidence_quotes.map((quote, idx) => (
            <div
              key={idx}
              className="p-3 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark"
            >
              <p className="text-sm italic">"{quote}"</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
