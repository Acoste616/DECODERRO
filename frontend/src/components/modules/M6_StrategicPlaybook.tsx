/**
 * ULTRA v3.0 - Module 6: Strategic Playbook
 * ==========================================
 * 
 * Renders strategic plays as cards with copy button
 */

import { useState } from 'react';
import { ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline';
import { useTranslation } from '../../utils/i18n';
import type { IM6StrategicPlaybook } from '../../types';

interface Props {
  data: IM6StrategicPlaybook;
}

export default function M6_StrategicPlaybook({ data }: Props) {
  const { t } = useTranslation();
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopy = (text: string[], index: number) => {
    navigator.clipboard.writeText(text.join('\n'));
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-4 border border-border-light dark:border-border-dark">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        🎯 {t('modules.m6_title')}
      </h3>

      <div className="space-y-3">
        {data.plays.map((play, idx) => (
          <div
            key={idx}
            className="p-4 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark"
          >
            {/* Header with Copy Button */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h4 className="font-semibold">{play.title}</h4>
                <span className="text-xs text-text-secondary-light dark:text-text-secondary-dark">
                  Confidence: {play.confidence_score}%
                </span>
              </div>
              <button
                onClick={() => handleCopy(play.content, idx)}
                className="ml-3 p-2 rounded hover:bg-surface-light dark:hover:bg-surface-dark transition"
                title={t('common.copy')}
              >
                {copiedIndex === idx ? (
                  <CheckIcon className="w-5 h-5 text-green-500" />
                ) : (
                  <ClipboardIcon className="w-5 h-5" />
                )}
              </button>
            </div>

            {/* Trigger */}
            <div className="mb-2">
              <h5 className="text-xs font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-1">
                {t('modules.m6_trigger')}
              </h5>
              <p className="text-sm">{play.trigger}</p>
            </div>

            {/* Content */}
            <div className="mt-3 p-3 rounded bg-accent-light/10 dark:bg-accent-dark/10 border-l-2 border-accent-light dark:border-accent-dark">
              <h5 className="text-xs font-semibold mb-1">{t('modules.m6_content')}</h5>
              <div className="space-y-1">
                {play.content.map((line, lIdx) => (
                  <p key={lIdx} className="text-sm">{line}</p>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
