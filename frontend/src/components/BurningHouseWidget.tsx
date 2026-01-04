/**
 * Tesla-Gotham ULTRA v4.0 - Burning House Widget
 * ================================================
 *
 * Sales Psychology Visualization:
 * - Progress bar with color-coded urgency (0-40% green, 41-70% yellow, 71-100% red pulsing)
 * - Large monthly delay cost counter
 * - Fire-themed urgency messaging
 *
 * Positioned in Dashboard top-right for maximum visibility
 */

import { useState, useEffect } from 'react';
import { FireIcon, BanknotesIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';
import { api } from '../utils/api';

interface BHSData {
  score: number;
  fire_level: 'cold' | 'warm' | 'hot' | 'burning';
  monthly_delay_cost_pln: number;
  urgency_message: string;
  messages: string[];
  factors: Record<string, any>;
}

interface BurningHouseWidgetProps {
  language?: 'pl' | 'en';
  // Optional: pass BHS data directly instead of fetching
  initialData?: BHSData;
  // Optional: demo mode with sample data
  demoMode?: boolean;
}

// Sample demo data for testing
const DEMO_BHS_DATA: BHSData = {
  score: 78,
  fire_level: 'burning',
  monthly_delay_cost_pln: 1847,
  urgency_message: 'POŻAR! Zwlekanie kosztuje Cię ~1,847 PLN miesięcznie. DZIAŁAJ TERAZ!',
  messages: [
    'KARA PODATKOWA 2026: Limit amortyzacji dla ICE spadł do 100k PLN! Przy wartości 250k PLN tracisz 28,500 PLN odliczenia (475 PLN/mies). Tesla EV ma limit 225k!',
    'OSZCZĘDNOŚĆ PALIWA: Diesel 6.03 PLN/l vs G12 nocna 0.46 PLN/kWh. Przy 2500 km/mies. oszczędzasz 1,097 PLN miesięcznie!',
    'PILNE - NaszEauto: Tylko 75 dni do końca programu! Dotacja 18,750 PLN przepada. Działaj teraz!',
    'IDEALNY MOMENT: 42 miesięcy - koniec typowego leasingu. Maksymalna wartość trade-in, minimalne ryzyko napraw.'
  ],
  factors: {
    tax_penalty: { applicable: true, lost_deduction_pln: 28500, monthly_loss_pln: 475 },
    fuel_savings: { monthly_savings_pln: 1097 },
    subsidy: { days_remaining: 75, urgency_level: 'high' },
    vehicle_age: { age_months: 42, category: 'optimal' }
  }
};

export default function BurningHouseWidget({
  language = 'pl',
  initialData,
  demoMode = true
}: BurningHouseWidgetProps) {
  const [bhsData, setBhsData] = useState<BHSData | null>(initialData || (demoMode ? DEMO_BHS_DATA : null));
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  // Color configuration based on score
  const getColorConfig = (score: number) => {
    if (score <= 40) {
      return {
        bg: 'bg-gradient-to-r from-green-500 to-green-600',
        barBg: 'bg-green-500',
        text: 'text-green-700 dark:text-green-400',
        border: 'border-green-500',
        label: language === 'pl' ? 'Bezpiecznie' : 'Safe',
        icon: '✅'
      };
    } else if (score <= 70) {
      return {
        bg: 'bg-gradient-to-r from-yellow-500 to-orange-500',
        barBg: 'bg-yellow-500',
        text: 'text-yellow-700 dark:text-yellow-400',
        border: 'border-yellow-500',
        label: language === 'pl' ? 'Uwaga' : 'Warning',
        icon: '⚠️'
      };
    } else {
      return {
        bg: 'bg-gradient-to-r from-red-500 to-red-700',
        barBg: 'bg-red-600 animate-pulse',
        text: 'text-red-700 dark:text-red-400',
        border: 'border-red-500',
        label: language === 'pl' ? 'POŻAR!' : 'FIRE!',
        icon: '🔥'
      };
    }
  };

  if (!bhsData) {
    return (
      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 animate-pulse">
        <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded mb-4"></div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4"></div>
      </div>
    );
  }

  const colorConfig = getColorConfig(bhsData.score);
  const isCritical = bhsData.score > 70;

  return (
    <div
      className={`relative overflow-hidden rounded-xl shadow-lg border-2 ${colorConfig.border} bg-white dark:bg-gray-900 transition-all duration-300 ${
        isExpanded ? 'p-6' : 'p-4'
      }`}
    >
      {/* Animated fire background for critical state */}
      {isCritical && (
        <div className="absolute inset-0 bg-gradient-to-t from-red-500/10 to-transparent animate-pulse pointer-events-none" />
      )}

      {/* Header */}
      <div className="relative flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`text-3xl ${isCritical ? 'animate-bounce' : ''}`}>
            {colorConfig.icon}
          </div>
          <div>
            <h3 className="font-bold text-lg text-gray-900 dark:text-white">
              {language === 'pl' ? 'Płonący Dom' : 'Burning House'}
            </h3>
            <span className={`text-sm font-medium ${colorConfig.text}`}>
              {colorConfig.label}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-black ${colorConfig.text}`}>
            {bhsData.score}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {language === 'pl' ? 'pilność' : 'urgency'}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
          <div
            className={`h-full ${colorConfig.barBg} transition-all duration-1000 ease-out rounded-full`}
            style={{ width: `${bhsData.score}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
          <span>0%</span>
          <span className="text-yellow-600">40%</span>
          <span className="text-orange-600">70%</span>
          <span className="text-red-600">100%</span>
        </div>
      </div>

      {/* Monthly Delay Cost - BIG COUNTER */}
      <div
        className={`relative rounded-lg p-4 mb-4 ${
          isCritical
            ? 'bg-red-100 dark:bg-red-900/30 border-2 border-red-500'
            : 'bg-gray-100 dark:bg-gray-800'
        }`}
      >
        {isCritical && (
          <ExclamationTriangleIcon className="absolute top-2 right-2 w-6 h-6 text-red-500 animate-pulse" />
        )}
        <div className="flex items-center gap-3">
          <BanknotesIcon className={`w-10 h-10 ${colorConfig.text}`} />
          <div>
            <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {language === 'pl' ? 'MIESIĘCZNY KOSZT ZWŁOKI:' : 'MONTHLY DELAY COST:'}
            </div>
            <div className={`text-4xl font-black ${colorConfig.text} ${isCritical ? 'animate-pulse' : ''}`}>
              {bhsData.monthly_delay_cost_pln.toLocaleString('pl-PL')} PLN
            </div>
          </div>
        </div>
      </div>

      {/* Urgency Message */}
      <div className={`text-sm font-medium p-3 rounded-lg ${
        isCritical
          ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300'
          : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
      }`}>
        {bhsData.urgency_message}
      </div>

      {/* Expandable Sales Arguments */}
      {bhsData.messages.length > 0 && (
        <div className="mt-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
          >
            <FireIcon className="w-4 h-4" />
            {language === 'pl'
              ? `${isExpanded ? 'Ukryj' : 'Pokaż'} argumenty sprzedażowe (${bhsData.messages.length})`
              : `${isExpanded ? 'Hide' : 'Show'} sales arguments (${bhsData.messages.length})`
            }
            <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
              ▼
            </span>
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-2">
              {bhsData.messages.map((msg, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm"
                >
                  <span className="text-lg">
                    {idx === 0 ? '💰' : idx === 1 ? '⛽' : idx === 2 ? '🎁' : '🚗'}
                  </span>
                  <p className="text-gray-700 dark:text-gray-300">{msg}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Factor Summary Pills */}
      {bhsData.factors && (
        <div className="mt-4 flex flex-wrap gap-2">
          {bhsData.factors.tax_penalty?.applicable && (
            <span className="px-2 py-1 text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded-full">
              💰 {language === 'pl' ? 'Kara podatkowa' : 'Tax penalty'}
            </span>
          )}
          {bhsData.factors.fuel_savings?.monthly_savings_pln > 500 && (
            <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full">
              ⛽ {bhsData.factors.fuel_savings.monthly_savings_pln.toLocaleString()} PLN/mies
            </span>
          )}
          {bhsData.factors.subsidy?.urgency_level === 'high' && (
            <span className="px-2 py-1 text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 rounded-full">
              🎁 NaszEauto: {bhsData.factors.subsidy.days_remaining} dni
            </span>
          )}
          {bhsData.factors.vehicle_age?.category === 'optimal' && (
            <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full">
              🚗 {language === 'pl' ? 'Optymalny moment' : 'Optimal timing'}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
