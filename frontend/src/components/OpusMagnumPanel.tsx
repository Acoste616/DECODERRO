/**
 * ULTRA v3.0 - Opus Magnum Panel
 * ===============================
 * 
 * Main container for 7 analysis modules
 * 
 * Implements:
 * - F-2.4: Subtle animation on Slow Path refresh
 * - F-2.5: Loading state and error state with retry button
 */

import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import { useTranslation } from '../utils/i18n';
import { api } from '../utils/api';

// Import all 7 modules
import M1_DnaClient from './modules/M1_DnaClient';
import M2_TacticalIndicators from './modules/M2_TacticalIndicators';
import M3_PsychometricProfile from './modules/M3_PsychometricProfile';
import M4_DeepMotivation from './modules/M4_DeepMotivation';
import M5_PredictivePaths from './modules/M5_PredictivePaths';
import M6_StrategicPlaybook from './modules/M6_StrategicPlaybook';
import M7_DecisionVectors from './modules/M7_DecisionVectors';

export default function OpusMagnumPanel() {
  const { t } = useTranslation();
  const {
    session_id,
    slow_path_data,
    app_status,
    slow_path_error,
    setAppStatus,
  } = useStore();

  // F-2.5: Retry Slow Path
  const handleRetrySlowPath = async () => {
    if (!session_id) return;

    setAppStatus('slow_path_loading');

    try {
      await api.retrySlowPath(session_id);
    } catch (error) {
      console.error('Retry Slow Path failed:', error);
    }
  };

  // Loading state
  if (app_status === 'slow_path_loading') {
    return (
      <div className="h-full flex items-center justify-center bg-surface-light dark:bg-surface-dark">
        <div className="text-center">
          <ArrowPathIcon className="w-12 h-12 mx-auto mb-4 animate-spin text-accent-light dark:text-accent-dark" />
          <div className="text-lg font-semibold">{t('view2_conversation.slow_path_loading')}</div>
          <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-2">
            {t('view2_conversation.slow_path_loading_desc')}
          </div>
        </div>
      </div>
    );
  }

  // F-2.5: Error state with retry button
  if (app_status === 'error' && slow_path_error) {
    return (
      <div className="h-full flex items-center justify-center bg-surface-light dark:bg-surface-dark p-6">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <div className="text-lg font-semibold mb-2">{t('view2_conversation.error_slow_path')}</div>
          <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark mb-6">
            {slow_path_error}
          </div>
          <button
            onClick={handleRetrySlowPath}
            className="px-6 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition flex items-center gap-2 mx-auto"
          >
            <ArrowPathIcon className="w-5 h-5" />
            {t('view2_conversation.retry_slow_path')}
          </button>
        </div>
      </div>
    );
  }

  // Empty state (no data yet)
  if (!slow_path_data) {
    return (
      <div className="h-full flex items-center justify-center bg-surface-light dark:bg-surface-dark p-6">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">🧠</div>
          <div className="text-lg font-semibold mb-2">{t('view2_conversation.strategic_panel_title')}</div>
          <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
            {t('view2_conversation.opus_magnum_empty')}
          </div>
        </div>
      </div>
    );
  }

  // F-2.4: Subtle animation on data refresh
  return (
    <div className="h-full overflow-y-auto bg-bg-light dark:bg-bg-dark p-4 space-y-4 animate-fade-in">
      {/* Header */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
        <h2 className="text-xl font-bold">{t('view2_conversation.strategic_panel_title')}</h2>
        <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-1">
          {t('view2_conversation.opus_magnum_desc')}
        </p>
      </div>

      {/* Module 1: DNA Client */}
      <M1_DnaClient data={slow_path_data.modules.dna_client} />

      {/* Module 2: Tactical Indicators */}
      <M2_TacticalIndicators data={slow_path_data.modules.tactical_indicators} />

      {/* Module 3: Psychometric Profile */}
      <M3_PsychometricProfile data={slow_path_data.modules.psychometric_profile} />

      {/* Module 4: Deep Motivation */}
      <M4_DeepMotivation data={slow_path_data.modules.deep_motivation} />

      {/* Module 5: Predictive Paths */}
      <M5_PredictivePaths data={slow_path_data.modules.predictive_paths} />

      {/* Module 6: Strategic Playbook */}
      <M6_StrategicPlaybook data={slow_path_data.modules.strategic_playbook} />

      {/* Module 7: Decision Vectors */}
      <M7_DecisionVectors data={slow_path_data.modules.decision_vectors} />
    </div>
  );
}
