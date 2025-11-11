/**
 * ULTRA v3.0 - Question Answer Modal
 * ===================================
 *
 * Modal for capturing client's answer to suggested strategic questions.
 * Flow: Click question → Modal opens → Enter client's answer → Send to conversation
 */

import { useState } from 'react';
import { XMarkIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { useTranslation } from '../utils/i18n';

interface Props {
  question: string;
  onClose: () => void;
  onSubmit: (answer: string) => void;
}

export default function QuestionAnswerModal({ question, onClose, onSubmit }: Props) {
  const { t } = useTranslation();
  const [answer, setAnswer] = useState('');

  const handleSubmit = () => {
    if (answer.trim()) {
      onSubmit(answer.trim());
      onClose();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg shadow-2xl max-w-2xl w-full">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-border-light dark:border-border-dark">
          <div className="flex-1 pr-4">
            <h3 className="text-lg font-semibold mb-2">💡 Pytanie Strategiczne</h3>
            <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
              Zadaj to pytanie klientowi i wprowadź jego odpowiedź poniżej
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-bg-light dark:hover:bg-bg-dark rounded transition"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Question Display */}
        <div className="p-5 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-b border-border-light dark:border-border-dark">
          <div className="text-xs font-semibold text-purple-600 dark:text-purple-400 mb-2">
            PYTANIE DO KLIENTA:
          </div>
          <div className="text-base font-medium text-purple-900 dark:text-purple-100 bg-white dark:bg-gray-800 p-4 rounded border-l-4 border-purple-500">
            "{question}"
          </div>
        </div>

        {/* Answer Input */}
        <div className="p-5">
          <label className="block text-sm font-semibold mb-2">
            Odpowiedź Klienta:
          </label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Wpisz co powiedział klient w odpowiedzi na to pytanie..."
            autoFocus
            rows={6}
            className="w-full px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark resize-none"
          />
          <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-2">
            Ctrl + Enter aby wysłać
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between p-5 border-t border-border-light dark:border-border-dark bg-bg-light dark:bg-bg-dark">
          <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark">
            Ta odpowiedź zostanie dodana do konwersacji dla głębszej analizy AI
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded border border-border-light dark:border-border-dark hover:bg-surface-light dark:hover:bg-surface-dark transition"
            >
              {t('common.cancel')}
            </button>
            <button
              onClick={handleSubmit}
              disabled={!answer.trim()}
              className="px-6 py-2 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2"
            >
              <PaperAirplaneIcon className="w-4 h-4" />
              Wyślij Odpowiedź
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
