/**
 * ULTRA v3.0 - Module 5: Predictive Paths
 * ========================================
 * 
 * Renders scenario paths as clickable cards
 */

import { useTranslation } from '../../utils/i18n';
import type { IM5PredictivePaths } from '../../types';

interface Props {
  data: IM5PredictivePaths;
}

export default function M5_PredictivePaths({ data }: Props) {
  const { t } = useTranslation();

  // Get probability color
  const getProbabilityColor = (prob: number) => {
    if (prob >= 70) return 'text-green-500';
    if (prob >= 40) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        🔮 {t('modules.m5_title')}
      </h3>

      <div className="space-y-3">
        {data.paths.map((pathItem, idx) => (
          <div
            key={idx}
            className="p-4 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark hover:border-accent-light dark:hover:border-accent-dark transition cursor-pointer"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h4 className="font-semibold">{pathItem.path}</h4>
              </div>
              <div className={`text-2xl font-bold ml-3 ${getProbabilityColor(pathItem.probability)}`}>
                {pathItem.probability}%
              </div>
            </div>

            {/* Recommendations */}
            <div className="mt-3">
              <h5 className="text-xs font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-1">
                {t('modules.m5_recommendations')}
              </h5>
              <ul className="space-y-1">
                {pathItem.recommendations.map((rec, rIdx) => (
                  <li key={rIdx} className="text-sm flex items-start gap-2">
                    <span className="text-accent-light dark:text-accent-dark">→</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
