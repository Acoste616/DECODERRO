/**
 * ULTRA v3.0 - Admin: Feedback Tab
 * =================================
 * 
 * Implements F-3.1: 3-column Master-Detail interface for feedback management
 * - Column 1: Grouped feedback themes
 * - Column 2: Feedback details for selected theme
 * - Column 3: Create Golden Standard form
 */

import { useState, useEffect } from 'react';
import { ChevronRightIcon, PlusIcon } from '@heroicons/react/24/outline';
import { useTranslation } from '../../utils/i18n';
import { api } from '../../utils/api';
import { useStore } from '../../store/useStore';
import type { IFeedbackGroup } from '../../types';

interface FeedbackDetail {
  feedback_id: number;
  session_id: string;
  message_index: number;
  sentiment: string;
  user_comment: string;
  context: string;
  timestamp: string;
}

export default function FeedbackTab() {
  const { t } = useTranslation();
  const { current_language } = useStore();

  // State
  const [groups, setGroups] = useState<IFeedbackGroup[]>([]);
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [details, setDetails] = useState<FeedbackDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Form state for Golden Standard
  const [formData, setFormData] = useState({
    trigger_context: '',
    golden_response: '',
    language: current_language,
    category: '',
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formSuccess, setFormSuccess] = useState(false);

  // Load grouped feedback on mount
  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    setLoading(true);
    try {
      const response = await api.getFeedbackGrouped(current_language);
      if (response.status === 'success' && response.data) {
        setGroups(response.data.groups || []);
      }
    } catch (error) {
      console.error('Failed to load feedback groups:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load details for selected theme
  const handleThemeSelect = async (themeName: string) => {
    setSelectedTheme(themeName);
    setDetailsLoading(true);

    try {
      const response = await api.getFeedbackDetails(themeName, current_language);
      if (response.status === 'success' && response.data) {
        setDetails(response.data.details || []);
      }
    } catch (error) {
      console.error('Failed to load feedback details:', error);
      setDetails([]);
    } finally {
      setDetailsLoading(false);
    }
  };

  // Handle Golden Standard creation
  const handleCreateGoldenStandard = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.trigger_context.trim() || !formData.golden_response.trim()) {
      return;
    }

    setFormSubmitting(true);
    setFormSuccess(false);

    try {
      const response = await api.createGoldenStandard({
        trigger_context: formData.trigger_context,
        golden_response: formData.golden_response,
        language: formData.language,
        category: formData.category || 'general',
      });

      if (response.status === 'success') {
        setFormSuccess(true);
        setFormData({
          trigger_context: '',
          golden_response: '',
          language: current_language,
          category: '',
        });
        setTimeout(() => setFormSuccess(false), 3000);
      }
    } catch (error) {
      console.error('Failed to create golden standard:', error);
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div className="grid grid-cols-3 gap-6 h-[calc(100vh-200px)]">
      {/* Column 1: Grouped Themes */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border-light dark:border-border-dark">
          <h2 className="text-lg font-bold">{t('admin.feedback_themes')}</h2>
          <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
            {t('admin.feedback_themes_desc')}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('common.loading')}...
            </div>
          ) : groups.length === 0 ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('admin.no_feedback')}
            </div>
          ) : (
            <div className="divide-y divide-border-light dark:divide-border-dark">
              {groups.map((group) => (
                <button
                  key={group.theme_name}
                  onClick={() => handleThemeSelect(group.theme_name)}
                  className={`w-full p-4 text-left hover:bg-bg-light dark:hover:bg-bg-dark transition flex items-center justify-between ${
                    selectedTheme === group.theme_name
                      ? 'bg-accent-light/10 dark:bg-accent-dark/10 border-l-4 border-accent-light dark:border-accent-dark'
                      : ''
                  }`}
                >
                  <div className="flex-1">
                    <div className="font-semibold">{group.theme_name}</div>
                    <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
                      {group.count} {t('admin.feedback_count')}
                    </div>
                    <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-1 line-clamp-2">
                      {group.representative_note}
                    </div>
                  </div>
                  <ChevronRightIcon className="w-5 h-5 text-text-secondary-light dark:text-text-secondary-dark ml-2" />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Column 2: Feedback Details */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border-light dark:border-border-dark">
          <h2 className="text-lg font-bold">{t('admin.feedback_details')}</h2>
          {selectedTheme && (
            <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
              {selectedTheme}
            </p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {!selectedTheme ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('admin.select_theme')}
            </div>
          ) : detailsLoading ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('common.loading')}...
            </div>
          ) : details.length === 0 ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('admin.no_details')}
            </div>
          ) : (
            <div className="divide-y divide-border-light dark:divide-border-dark">
              {details.map((detail) => (
                <div key={detail.feedback_id} className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-text-secondary-light dark:text-text-secondary-dark">
                      {detail.session_id}
                    </span>
                    <span className={`text-xs font-semibold ${
                      detail.sentiment === 'positive' ? 'text-green-500' : 'text-red-500'
                    }`}>
                      {detail.sentiment === 'positive' ? '👍' : '👎'}
                    </span>
                  </div>
                  
                  {detail.user_comment && (
                    <div className="mb-2 p-2 rounded bg-bg-light dark:bg-bg-dark">
                      <div className="text-xs font-semibold mb-1">{t('admin.user_comment')}:</div>
                      <div className="text-sm">{detail.user_comment}</div>
                    </div>
                  )}
                  
                  <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
                    <div className="text-xs font-semibold mb-1">{t('admin.context')}:</div>
                    <div className="line-clamp-3">{detail.context}</div>
                  </div>
                  
                  <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-2">
                    {new Date(detail.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Column 3: Create Golden Standard Form */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border-light dark:border-border-dark">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <PlusIcon className="w-5 h-5" />
            {t('admin.create_golden_standard')}
          </h2>
        </div>

        <form onSubmit={handleCreateGoldenStandard} className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Trigger Context */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.trigger_context')} *
            </label>
            <textarea
              value={formData.trigger_context}
              onChange={(e) => setFormData({ ...formData, trigger_context: e.target.value })}
              placeholder={t('admin.trigger_context_placeholder')}
              rows={3}
              required
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Golden Response */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.golden_response')} *
            </label>
            <textarea
              value={formData.golden_response}
              onChange={(e) => setFormData({ ...formData, golden_response: e.target.value })}
              placeholder={t('admin.golden_response_placeholder')}
              rows={5}
              required
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Language Selector */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.language')} *
            </label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value as 'pl' | 'en' })}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            >
              <option value="pl">Polski (PL)</option>
              <option value="en">English (EN)</option>
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.category')}
            </label>
            <input
              type="text"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              placeholder={t('admin.category_placeholder')}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={formSubmitting}
            className="w-full px-4 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition font-semibold disabled:opacity-50"
          >
            {formSubmitting ? t('common.submitting') : t('admin.create_button')}
          </button>

          {/* Success Message */}
          {formSuccess && (
            <div className="p-3 rounded bg-green-100 dark:bg-green-900/30 border border-green-500 text-green-700 dark:text-green-300 text-sm">
              {t('admin.golden_standard_created')}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
