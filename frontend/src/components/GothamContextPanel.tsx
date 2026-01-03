/**
 * Tesla-Gotham ULTRA v4.0 - Gotham Strategic Context Panel
 * ==========================================================
 *
 * Displays strategic market intelligence from Gotham Intelligence:
 * - Fuel price trends and TCO calculations
 * - Subsidy program status and deadlines
 * - Leasing expiry opportunities (CEPiK)
 * - Charging infrastructure + wealth mapping (EIPA)
 *
 * "Bloomberg Brain" for Tesla sales - provides market context beyond client conversation
 */

import { useState } from 'react';
import {
  ChartBarIcon,
  BoltIcon,
  GlobeAltIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';

interface GothamContextPanelProps {
  language?: 'pl' | 'en';
}

export default function GothamContextPanel({ language = 'pl' }: GothamContextPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // In production, this data would come from API call to Gotham service
  // For now, we'll display placeholder data to demonstrate UI
  const contextData = {
    fuel_prices: {
      pb95: 6.49,
      diesel: 6.35,
      electricity: 0.80,
      annual_savings: 4200,
    },
    subsidies: {
      moj_elektryk: {
        amount: 18750,
        budget_remaining: 30,
        deadline: '2025-12-31',
      },
      nasz_eauto: {
        amount: 27000,
        status: 'active',
      },
    },
    regional_intel: {
      leasing_expiry_count: 3,
      top_opportunity: 'Katowice',
      opportunity_score: 85,
    },
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition"
      >
        <div className="flex items-center gap-2">
          <GlobeAltIcon className="w-5 h-5" />
          <h3 className="font-bold text-sm">
            {language === 'pl' ? '🧠 Gotham Intelligence - Kontekst Strategiczny' : '🧠 Gotham Intelligence - Strategic Context'}
          </h3>
        </div>
        {isExpanded ? <ChevronUpIcon className="w-5 h-5" /> : <ChevronDownIcon className="w-5 h-5" />}
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 space-y-4 text-sm">
          {/* Fuel Prices & TCO */}
          <div className="bg-bg-light dark:bg-bg-dark p-3 rounded-md border border-border-light dark:border-border-dark">
            <div className="flex items-center gap-2 mb-2">
              <ChartBarIcon className="w-4 h-4 text-blue-500" />
              <h4 className="font-semibold">
                {language === 'pl' ? '⛽ Ceny Paliw & TCO' : '⛽ Fuel Prices & TCO'}
              </h4>
            </div>
            <div className="text-xs space-y-1 text-text-secondary-light dark:text-text-secondary-dark">
              <div>
                Pb95: <strong>{contextData.fuel_prices.pb95} PLN/l</strong> | Diesel: <strong>{contextData.fuel_prices.diesel} PLN/l</strong>
              </div>
              <div>
                {language === 'pl' ? 'Energia' : 'Electricity'}: <strong>{contextData.fuel_prices.electricity} PLN/kWh</strong>
              </div>
              <div className="text-green-600 dark:text-green-400 font-bold mt-2">
                💰 {language === 'pl' ? 'Oszczędność roczna:' : 'Annual savings:'} {contextData.fuel_prices.annual_savings.toLocaleString()} PLN
              </div>
            </div>
          </div>

          {/* Subsidies */}
          <div className="bg-bg-light dark:bg-bg-dark p-3 rounded-md border border-border-light dark:border-border-dark">
            <div className="flex items-center gap-2 mb-2">
              <BoltIcon className="w-4 h-4 text-yellow-500" />
              <h4 className="font-semibold">
                {language === 'pl' ? '🎁 Programy Dotacji' : '🎁 Subsidy Programs'}
              </h4>
            </div>
            <div className="text-xs space-y-2 text-text-secondary-light dark:text-text-secondary-dark">
              <div>
                <div className="font-medium">Mój Elektryk</div>
                <div>
                  {language === 'pl' ? 'Dotacja:' : 'Subsidy:'} <strong>{contextData.subsidies.moj_elektryk.amount.toLocaleString()} PLN</strong>
                </div>
                <div className="text-orange-600 dark:text-orange-400">
                  ⚠️ {language === 'pl' ? 'OGRANICZONA' : 'LIMITED'} ({contextData.subsidies.moj_elektryk.budget_remaining}% {language === 'pl' ? 'budżetu' : 'budget'})
                </div>
              </div>
              <div>
                <div className="font-medium">NaszEauto (B2B)</div>
                <div>
                  {language === 'pl' ? 'Dotacja:' : 'Subsidy:'} <strong>{contextData.subsidies.nasz_eauto.amount.toLocaleString()} PLN</strong>
                </div>
                <div className="text-green-600 dark:text-green-400">
                  ✅ {language === 'pl' ? 'AKTYWNY' : 'ACTIVE'}
                </div>
              </div>
            </div>
          </div>

          {/* Regional Intelligence */}
          <div className="bg-bg-light dark:bg-bg-dark p-3 rounded-md border border-border-light dark:border-border-dark">
            <div className="flex items-center gap-2 mb-2">
              <GlobeAltIcon className="w-4 h-4 text-purple-500" />
              <h4 className="font-semibold">
                {language === 'pl' ? '📊 Inteligencja Regionalna' : '📊 Regional Intelligence'}
              </h4>
            </div>
            <div className="text-xs space-y-1 text-text-secondary-light dark:text-text-secondary-dark">
              <div>
                {language === 'pl' ? 'Wygasające leasingi:' : 'Expiring leases:'} <strong>{contextData.regional_intel.leasing_expiry_count}</strong> {language === 'pl' ? 'pojazdy premium' : 'premium vehicles'}
              </div>
              <div>
                {language === 'pl' ? 'Top Opportunity:' : 'Top Opportunity:'} <strong>{contextData.regional_intel.top_opportunity}</strong>
              </div>
              <div className="text-blue-600 dark:text-blue-400 font-bold mt-2">
                🎯 Opportunity Score: {contextData.regional_intel.opportunity_score}/100
              </div>
            </div>
          </div>

          {/* Sales Insight */}
          <div className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900 dark:to-purple-900 rounded-md border border-blue-200 dark:border-blue-700">
            <div className="text-xs font-medium">
              💡 <strong>{language === 'pl' ? 'Sales Angle:' : 'Sales Angle:'}</strong>
              <div className="mt-1">
                {language === 'pl'
                  ? 'Klient w segmencie premium, leasing wygasa, wysokie koszty paliwa. Podkreśl TCO i dotacje przed wyczerpaniem budżetu.'
                  : 'Premium segment client, lease expiring, high fuel costs. Emphasize TCO and subsidies before budget depletion.'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
