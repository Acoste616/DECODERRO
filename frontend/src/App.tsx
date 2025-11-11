/**
 * ULTRA v3.0 - Main App Component
 * ================================
 * 
 * Implements routing and global UI controls (theme, language toggles)
 */

import { Routes, Route } from 'react-router-dom';
import { SunIcon, MoonIcon, LanguageIcon } from '@heroicons/react/24/outline';
import { useStore } from './store/useStore';
import { useTranslation } from './utils/i18n';
import Dashboard from './views/Dashboard';
import Conversation from './views/Conversation';
import AdminPanel from './views/AdminPanel';

export default function App() {
  const { current_theme, setTheme, current_language, setLanguage } = useStore();
  const { t } = useTranslation();

  const toggleTheme = () => {
    setTheme(current_theme === 'light' ? 'dark' : 'light');
  };

  const toggleLanguage = () => {
    setLanguage(current_language === 'pl' ? 'en' : 'pl');
  };

  return (
    <div className="min-h-screen bg-bg-light dark:bg-bg-dark text-text-primary-light dark:text-text-primary-dark">
      {/* Global Header with Theme & Language Toggles */}
      <header className="bg-surface-light dark:bg-surface-dark border-b border-border-light dark:border-border-dark">
        <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-xl font-bold">ULTRA v3.0</h1>
          
          <div className="flex gap-3">
            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-2 px-3 py-2 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition"
              title={t('common.language')}
            >
              <LanguageIcon className="w-5 h-5" />
              <span className="font-medium">{current_language.toUpperCase()}</span>
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition"
              title={t('common.theme')}
            >
              {current_theme === 'light' ? (
                <MoonIcon className="w-5 h-5" />
              ) : (
                <SunIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Routes */}
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/session/:id" element={<Conversation />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </main>
    </div>
  );
}
