/**
 * ULTRA v3.0 - Module 2: Tactical Indicators
 * ===========================================
 * 
 * Renders purchase temperature (progress bar), churn risk, and fun drive risk
 */

import { useTranslation } from '../../utils/i18n';
import type { IM2TacticalIndicators } from '../../types';

interface Props {
  data: IM2TacticalIndicators;
}

export default function M2_TacticalIndicators({ data }: Props) {
  const { t } = useTranslation();

  // Get risk color
  const getRiskColor = (level: string) => {
    if (level === 'Low') return 'text-green-500';
    if (level === 'Medium') return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        📊 {t('modules.m2_title')}
      </h3>

      {/* Purchase Temperature */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark">
            🌡️ {t('modules.m2_purchase_temperature')}
          </h4>
          <span className="text-lg font-bold">{data.purchase_temperature.value}%</span>
        </div>
        <div className="w-full bg-bg-light dark:bg-bg-dark rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all bg-accent-light dark:bg-accent-dark"
            style={{ width: `${data.purchase_temperature.value}%` }}
          ></div>
        </div>
        <p className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-1">
          {data.purchase_temperature.label}
        </p>
      </div>

      {/* Churn Risk */}
      <div className="mb-3">
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-1">
          🔄 {t('modules.m2_churn_risk')}
        </h4>
        <p className={`text-sm font-semibold ${getRiskColor(data.churn_risk.level)}`}>
          {data.churn_risk.level} ({data.churn_risk.percentage}%)
        </p>
        <p className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-1">
          {data.churn_risk.reason}
        </p>
      </div>

      {/* Fun Drive Risk */}
      <div>
        <h4 className="font-semibold text-sm text-text-secondary-light dark:text-text-secondary-dark mb-1">
          🎯 {t('modules.m2_fun_drive_risk')}
        </h4>
        <p className={`text-sm font-semibold ${getRiskColor(data.fun_drive_risk.level)}`}>
          {data.fun_drive_risk.level} ({data.fun_drive_risk.percentage}%)
        </p>
        <p className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-1">
          {data.fun_drive_risk.reason}
        </p>
      </div>
    </div>
  );
}
