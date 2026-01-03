/**
 * Tesla-Gotham ULTRA v4.0 - Burning House Score Component
 * ========================================================
 *
 * Visualizes purchase urgency with:
 * - Fire level indicator (cold/warm/hot/burning)
 * - Progress bar (0-100 score)
 * - Monthly delay cost in PLN
 * - Urgency message
 *
 * Used in Conversation view to show real-time urgency context
 */

import { FireIcon, BanknotesIcon } from '@heroicons/react/24/outline';
import type { IBurningHouseScore } from '../types';

interface BurningHouseScoreProps {
  bhs: IBurningHouseScore;
  language?: 'pl' | 'en';
}

export default function BurningHouseScore({ bhs, language = 'pl' }: BurningHouseScoreProps) {
  // Fire level colors and intensity
  const fireConfig = {
    cold: {
      bgColor: 'bg-blue-100 dark:bg-blue-900',
      barColor: 'bg-blue-500',
      textColor: 'text-blue-700 dark:text-blue-300',
      icon: '❄️',
      label: language === 'pl' ? 'Niski priorytet' : 'Low Priority'
    },
    warm: {
      bgColor: 'bg-yellow-100 dark:bg-yellow-900',
      barColor: 'bg-yellow-500',
      textColor: 'text-yellow-700 dark:text-yellow-300',
      icon: '💡',
      label: language === 'pl' ? 'Średni priorytet' : 'Medium Priority'
    },
    hot: {
      bgColor: 'bg-orange-100 dark:bg-orange-900',
      barColor: 'bg-orange-500',
      textColor: 'text-orange-700 dark:text-orange-300',
      icon: '🔥',
      label: language === 'pl' ? 'Wysoki priorytet' : 'High Priority'
    },
    burning: {
      bgColor: 'bg-red-100 dark:bg-red-900',
      barColor: 'bg-red-600 animate-pulse',
      textColor: 'text-red-700 dark:text-red-300',
      icon: '🔥🔥🔥',
      label: language === 'pl' ? 'PILNE!' : 'URGENT!'
    }
  };

  const config = fireConfig[bhs.fire_level];

  return (
    <div className={`rounded-lg p-4 border-2 ${config.bgColor} ${config.textColor} border-current`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          <h3 className="font-bold text-lg">
            {language === 'pl' ? 'Wskaźnik Pilności' : 'Urgency Score'}
          </h3>
        </div>
        <div className="text-right">
          <div className="text-sm font-medium">{config.label}</div>
          <div className="text-2xl font-bold">{bhs.score}/100</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full ${config.barColor} transition-all duration-500 ease-out`}
            style={{ width: `${bhs.score}%` }}
          />
        </div>
      </div>

      {/* Monthly Delay Cost */}
      <div className="flex items-center gap-2 mb-2 p-3 bg-white dark:bg-gray-800 rounded-md">
        <BanknotesIcon className="w-5 h-5" />
        <div className="flex-1">
          <div className="text-sm font-medium">
            {language === 'pl' ? 'Koszt zwłoki:' : 'Delay cost:'}
          </div>
          <div className="text-xl font-bold">
            {bhs.monthly_delay_cost_pln.toLocaleString('pl-PL')} PLN/
            {language === 'pl' ? 'mies.' : 'month'}
          </div>
        </div>
      </div>

      {/* Urgency Message */}
      <div className="text-sm font-medium p-2 bg-white dark:bg-gray-800 rounded-md">
        {bhs.urgency_message}
      </div>

      {/* Factor Breakdown (Collapsible) */}
      {bhs.factors && Object.keys(bhs.factors).length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm font-medium hover:underline">
            {language === 'pl' ? '📊 Szczegóły czynników' : '📊 Factor Details'}
          </summary>
          <div className="mt-2 text-xs space-y-1 p-2 bg-white dark:bg-gray-800 rounded-md">
            {bhs.factors.fuel_savings_monthly && (
              <div>
                💰 {language === 'pl' ? 'Oszczędność paliwa:' : 'Fuel savings:'}{' '}
                <strong>{bhs.factors.fuel_savings_monthly} PLN/mies.</strong>
              </div>
            )}
            {bhs.factors.subsidy_urgency && bhs.factors.subsidy_urgency !== 'not_applicable' && (
              <div>
                🎁 {language === 'pl' ? 'Pilność dotacji:' : 'Subsidy urgency:'}{' '}
                <strong>{bhs.factors.subsidy_urgency}</strong>
                {bhs.factors.subsidy_expires_days && ` (${bhs.factors.subsidy_expires_days} dni)`}
              </div>
            )}
            {bhs.factors.has_business_benefit && (
              <div>
                🏢 {language === 'pl' ? 'Korzyść B2B:' : 'Business benefit:'}{' '}
                <strong>
                  {bhs.factors.depreciation_benefit_pln} PLN {language === 'pl' ? 'odliczenia' : 'deduction'}
                </strong>
              </div>
            )}
            {bhs.factors.vehicle_age_months && (
              <div>
                🚗 {language === 'pl' ? 'Wiek pojazdu:' : 'Vehicle age:'}{' '}
                <strong>{bhs.factors.vehicle_age_months} miesięcy</strong>
                {' '}({bhs.factors.age_category})
              </div>
            )}
          </div>
        </details>
      )}
    </div>
  );
}
