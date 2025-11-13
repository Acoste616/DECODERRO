/**
 * ULTRA v3.0 - Journey Stage Selector
 * ====================================
 *
 * Advanced journey stage selector with:
 * - AI-suggested stage highlighting
 * - Manual override capability
 * - Visual differentiation between manual and AI selection
 * - Stage-dependent strategy recommendations
 */

import { useState } from 'react';
import { SparklesIcon, UserIcon } from '@heroicons/react/24/outline';
import { useTranslation } from '../utils/i18n';

type JourneyStage = 'Odkrywanie' | 'Analiza' | 'Decyzja';

interface Props {
  currentStage: JourneyStage | null;
  suggestedStage?: JourneyStage | null;
  onStageChange: (stage: JourneyStage) => void;
}

export default function JourneyStageSelector({ currentStage, suggestedStage, onStageChange }: Props) {
  const { t } = useTranslation();
  const [manualOverride, setManualOverride] = useState(false);

  const stages: JourneyStage[] = ['Odkrywanie', 'Analiza', 'Decyzja'];

  const handleStageClick = (stage: JourneyStage) => {
    onStageChange(stage);

    // If clicking different stage than AI suggestion, mark as manual override
    if (suggestedStage && stage !== suggestedStage) {
      setManualOverride(true);
    } else {
      setManualOverride(false);
    }
  };

  const getStageDescription = (stage: JourneyStage): string => {
    switch (stage) {
      case 'Odkrywanie':
        return t('view2_conversation.stage_odkrywanie_desc');
      case 'Analiza':
        return t('view2_conversation.stage_analiza_desc');
      case 'Decyzja':
        return t('view2_conversation.stage_decyzja_desc');
    }
  };

  const getStageStrategy = (stage: JourneyStage): string[] => {
    switch (stage) {
      case 'Odkrywanie':
        return [
          t('view2_conversation.strategy_odkrywanie_1'),
          t('view2_conversation.strategy_odkrywanie_2'),
          t('view2_conversation.strategy_odkrywanie_3'),
          t('view2_conversation.strategy_odkrywanie_4'),
        ];
      case 'Analiza':
        return [
          t('view2_conversation.strategy_analiza_1'),
          t('view2_conversation.strategy_analiza_2'),
          t('view2_conversation.strategy_analiza_3'),
          t('view2_conversation.strategy_analiza_4'),
        ];
      case 'Decyzja':
        return [
          t('view2_conversation.strategy_decyzja_1'),
          t('view2_conversation.strategy_decyzja_2'),
          t('view2_conversation.strategy_decyzja_3'),
          t('view2_conversation.strategy_decyzja_4'),
        ];
    }
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark border-b border-border-light dark:border-border-dark p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold">{t('view2_conversation.journey_stage')}</div>

        {/* AI Suggestion Indicator */}
        {suggestedStage && (
          <div className="flex items-center gap-2 text-xs">
            <SparklesIcon className="w-4 h-4 text-purple-500" />
            <span className="text-text-secondary-light dark:text-text-secondary-dark">
              {t('view2_conversation.ai_suggests')} <span className="font-semibold text-purple-500">{suggestedStage}</span>
            </span>
          </div>
        )}
      </div>

      {/* Stage Buttons */}
      <div className="flex gap-2 mb-3">
        {stages.map((stage) => {
          const isSelected = currentStage === stage;
          const isAISuggested = suggestedStage === stage;
          const isDifferentFromAI = manualOverride && isSelected && !isAISuggested;

          return (
            <button
              key={stage}
              onClick={() => handleStageClick(stage)}
              className={`
                flex-1 px-4 py-3 rounded transition relative
                ${isSelected
                  ? 'bg-accent-light dark:bg-accent-dark text-accent-text-light font-semibold shadow-lg'
                  : 'bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark hover:border-accent-light dark:hover:border-accent-dark'
                }
                ${isAISuggested && !isSelected
                  ? 'ring-2 ring-purple-500 ring-opacity-50 animate-pulse'
                  : ''
                }
              `}
            >
              {/* AI Suggested Badge */}
              {isAISuggested && !isSelected && (
                <div className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
                  <SparklesIcon className="w-3 h-3" />
                  AI
                </div>
              )}

              {/* Manual Override Badge */}
              {isDifferentFromAI && (
                <div className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
                  <UserIcon className="w-3 h-3" />
                  Manual
                </div>
              )}

              <div className="text-sm">{stage === 'Odkrywanie' ? t('view2_conversation.stage_discovery') : stage === 'Analiza' ? t('view2_conversation.stage_analysis') : t('view2_conversation.stage_decision')}</div>
            </button>
          );
        })}
      </div>

      {/* Current Stage Info */}
      {currentStage && (
        <div className="mt-4 space-y-3">
          {/* Description */}
          <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark bg-bg-light dark:bg-bg-dark p-3 rounded">
            <div className="font-semibold mb-1">📍 {t('view2_conversation.stage_characteristics')}</div>
            {getStageDescription(currentStage)}
          </div>

          {/* Strategy Recommendations */}
          <div className="text-xs bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 p-3 rounded border border-purple-200 dark:border-purple-800">
            <div className="font-semibold mb-2 flex items-center gap-2">
              <SparklesIcon className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <span className="text-purple-900 dark:text-purple-100">{t('view2_conversation.stage_strategy')}</span>
            </div>
            <ul className="space-y-1.5">
              {getStageStrategy(currentStage).map((strategy, idx) => (
                <li key={idx} className="flex items-start gap-2 text-purple-900 dark:text-purple-100">
                  <span className="text-purple-500 mt-0.5">→</span>
                  <span>{strategy}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
