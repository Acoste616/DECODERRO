/**
 * ULTRA v3.0 - View 3: Admin Panel
 * =================================
 * 
 * Implements:
 * - F-3.1: Admin authentication with API key (localStorage)
 * - 3-tab layout: Feedback, RAG, Analytics
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { KeyIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import { useTranslation } from '../utils/i18n';
import FeedbackTab from '../components/admin/FeedbackTab';
import RagTab from '../components/admin/RagTab';
import AnalyticsTab from '../components/admin/AnalyticsTab';

type AdminTab = 'feedback' | 'rag' | 'analytics';

export default function AdminPanel() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { admin_key, setAdminKey } = useStore();

  const [keyInput, setKeyInput] = useState('');
  const [loginError, setLoginError] = useState('');
  const [activeTab, setActiveTab] = useState<AdminTab>('feedback');

  // Check if admin key exists in localStorage on mount
  useEffect(() => {
    const storedKey = localStorage.getItem('ultra_admin_key');
    if (storedKey && !admin_key) {
      setAdminKey(storedKey);
    }
  }, []);

  // F-3.1: Handle admin login
  const handleLogin = () => {
    if (!keyInput.trim()) {
      setLoginError(t('view3_admin.login_error_empty'));
      return;
    }

    // Save to localStorage and store
    localStorage.setItem('ultra_admin_key', keyInput);
    setAdminKey(keyInput);
    setLoginError('');
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('ultra_admin_key');
    setAdminKey(null);
    setKeyInput('');
  };

  // Login screen
  if (!admin_key) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-light dark:bg-bg-dark p-6">
        <div className="w-full max-w-md">
          {/* Back button */}
          <button
            onClick={() => navigate('/')}
            className="mb-6 flex items-center gap-2 text-text-secondary-light dark:text-text-secondary-dark hover:text-text-primary-light dark:hover:text-text-primary-dark transition"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            {t('common.back')}
          </button>

          {/* Login card */}
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-8 border border-border-light dark:border-border-dark shadow-lg">
            <div className="flex items-center justify-center mb-6">
              <KeyIcon className="w-12 h-12 text-accent-light dark:text-accent-dark" />
            </div>

            <h1 className="text-2xl font-bold text-center mb-2">
              {t('view3_admin.login_title')}
            </h1>
            <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark text-center mb-6">
              {t('view3_admin.login_subtitle')}
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2">
                  {t('view3_admin.admin_key')}
                </label>
                <input
                  type="password"
                  value={keyInput}
                  onChange={(e) => {
                    setKeyInput(e.target.value);
                    setLoginError('');
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleLogin();
                    }
                  }}
                  placeholder={t('view3_admin.admin_key_placeholder')}
                  className={`w-full px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border ${
                    loginError
                      ? 'border-red-500'
                      : 'border-border-light dark:border-border-dark'
                  } focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark`}
                />
                {loginError && (
                  <p className="text-red-500 text-sm mt-2">{loginError}</p>
                )}
              </div>

              <button
                onClick={handleLogin}
                className="w-full px-6 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition font-semibold"
              >
                {t('view3_admin.login_button')}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Admin panel with tabs
  return (
    <div className="min-h-screen bg-bg-light dark:bg-bg-dark">
      {/* Header */}
      <div className="bg-surface-light dark:bg-surface-dark border-b border-border-light dark:border-border-dark">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-bg-light dark:hover:bg-bg-dark rounded transition"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <h1 className="text-2xl font-bold">{t('view3_admin.panel_title')}</h1>
          </div>

          <button
            onClick={handleLogout}
            className="px-4 py-2 rounded border border-border-light dark:border-border-dark hover:bg-bg-light dark:hover:bg-bg-dark transition text-sm"
          >
            {t('view3_admin.logout')}
          </button>
        </div>

        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-2 border-b border-border-light dark:border-border-dark">
            <button
              onClick={() => setActiveTab('feedback')}
              className={`px-6 py-3 font-semibold transition border-b-2 ${
                activeTab === 'feedback'
                  ? 'border-accent-light dark:border-accent-dark text-accent-light dark:text-accent-dark'
                  : 'border-transparent text-text-secondary-light dark:text-text-secondary-dark hover:text-text-primary-light dark:hover:text-text-primary-dark'
              }`}
            >
              {t('view3_admin.tab_feedback')}
            </button>
            <button
              onClick={() => setActiveTab('rag')}
              className={`px-6 py-3 font-semibold transition border-b-2 ${
                activeTab === 'rag'
                  ? 'border-accent-light dark:border-accent-dark text-accent-light dark:text-accent-dark'
                  : 'border-transparent text-text-secondary-light dark:text-text-secondary-dark hover:text-text-primary-light dark:hover:text-text-primary-dark'
              }`}
            >
              {t('view3_admin.tab_rag')}
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-6 py-3 font-semibold transition border-b-2 ${
                activeTab === 'analytics'
                  ? 'border-accent-light dark:border-accent-dark text-accent-light dark:text-accent-dark'
                  : 'border-transparent text-text-secondary-light dark:text-text-secondary-dark hover:text-text-primary-light dark:hover:text-text-primary-dark'
              }`}
            >
              {t('view3_admin.tab_analytics')}
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'feedback' && <FeedbackTab />}
        {activeTab === 'rag' && <RagTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </div>
    </div>
  );
}
