/**
 * ULTRA v3.0 - Module 7: Decision Vectors
 * ========================================
 * 
 * Renders stakeholder decision vectors as table/list
 */

import { useTranslation } from '../../utils/i18n';
import type { IM7DecisionVectors } from '../../types';

interface Props {
  data: IM7DecisionVectors;
}

export default function M7_DecisionVectors({ data }: Props) {
  const { t } = useTranslation();

  // Get influence color
  const getInfluenceColor = (influence: string) => {
    if (influence === 'high') return 'text-green-500';
    if (influence === 'medium') return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        👥 {t('modules.m7_title')}
      </h3>

      <div className="space-y-3">
        {data.vectors.map((vector, idx) => (
          <div
            key={idx}
            className="p-4 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark"
          >
            {/* Stakeholder Header */}
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">{vector.stakeholder}</h4>
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-secondary-light dark:text-text-secondary-dark">
                  {t('modules.m7_influence')}:
                </span>
                <span className={`text-sm font-bold uppercase ${getInfluenceColor(vector.influence)}`}>
                  {vector.influence}
                </span>
                <span className="text-xs">({vector.confidence_score}%)</span>
              </div>
            </div>

            {/* Vector & Focus */}
            <div className="mb-2">
              <h5 className="text-xs font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-1">
                📍 {t('modules.m7_vector')}
              </h5>
              <p className="text-sm">{vector.vector}</p>
            </div>

            <div className="mb-2">
              <h5 className="text-xs font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-1">
                🎯 {t('modules.m7_focus')}
              </h5>
              <p className="text-sm">{vector.focus}</p>
            </div>

            {/* Strategy */}
            <div className="mt-3 p-3 rounded bg-green-50 dark:bg-green-900/20 border-l-2 border-green-500">
              <h5 className="text-xs font-semibold mb-1">{t('modules.m7_strategy')}</h5>
              <p className="text-sm">{vector.strategy}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
