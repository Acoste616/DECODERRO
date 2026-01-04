/**
 * ULTRA v3.0 - View 1: Dashboard (Session Management)
 * ====================================================
 *
 * Implements:
 * - F-1.1: Start New Session (Optimistic UI)
 * - F-1.2: Resume Session by ID
 * - F-1.3: Recent Sessions List (localStorage)
 * - F-4.0: Burning House Widget (Tesla-Gotham v4.0)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, ArrowRightIcon, ClockIcon, FireIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { useStore } from '../store/useStore';
import { useTranslation } from '../utils/i18n';
import { api } from '../utils/api';
import BurningHouseWidget from '../components/BurningHouseWidget';
import BurningHouseScore from '../components/BurningHouseScore';
import type { IBurningHouseScore } from '../types';

interface RecentSession {
  id: string;
  context: string;
  timestamp: number;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { resetSession, current_language } = useStore();

  const [resumeId, setResumeId] = useState('');
  const [resumeError, setResumeError] = useState('');
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([]);

  // Tesla-Gotham v4.0: Burning House Score State
  const [bhsData, setBhsData] = useState<IBurningHouseScore | null>(null);
  const [bhsLoading, setBhsLoading] = useState(false);
  const [bhsError, setBhsError] = useState<string | null>(null);
  const [showBhsPanel, setShowBhsPanel] = useState(false);

  // Load recent sessions from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('ultra_recent_sessions');
    if (stored) {
      try {
        const sessions = JSON.parse(stored);
        setRecentSessions(sessions.slice(0, 10)); // Max 10
      } catch (e) {
        console.error('Failed to load recent sessions:', e);
      }
    }
  }, []);

  // F-1.1: Start New Session (Optimistic UI)
  const handleNewSession = () => {
    // Reset any previous session state
    resetSession();
    
    // Generate temporary session ID
    const tempId = `TEMP-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    
    // Immediately navigate with optimistic UI (no API wait)
    navigate(`/session/${tempId}`);
  };

  // F-1.2: Resume Session by ID
  const handleResumeSession = async (sessionId: string) => {
    setResumeError('');
    
    if (!sessionId.trim()) {
      return;
    }

    try {
      // Try to fetch session data
      const response = await api.getSession(sessionId);
      
      if (response.status === 'success') {
        // Session exists, navigate to it
        navigate(`/session/${sessionId}`);
      } else {
        // Session not found
        setResumeError(t('view1_dashboard.resume_error'));
      }
    } catch (error) {
      // Error - session not found or API issue
      setResumeError(t('view1_dashboard.resume_error'));
    }
  };

  // F-1.3: Click on recent session
  const handleRecentSessionClick = (sessionId: string) => {
    handleResumeSession(sessionId);
  };

  // Tesla-Gotham v4.0: Calculate Burning House Score
  const handleCalculateBHS = async () => {
    setBhsLoading(true);
    setBhsError(null);

    // Sample input data for demonstration
    // In production, this would come from a form or session context
    const sampleData = {
      current_fuel_consumption_l_100km: 8.5,
      monthly_distance_km: 2500,
      fuel_price_pln_l: 6.03,
      vehicle_age_months: 42,
      purchase_type: 'business' as const,
      vehicle_price_planned: 250000,
      subsidy_deadline_days: 75,
      language: current_language as 'pl' | 'en',
    };

    try {
      const response = await api.calculateBurningHouseScore(sampleData);
      if (response.status === 'success' && response.data) {
        setBhsData(response.data);
        setShowBhsPanel(true);
      } else {
        setBhsError(response.message || 'Failed to calculate score');
      }
    } catch (error) {
      console.error('BHS calculation error:', error);
      setBhsError(current_language === 'pl'
        ? 'Błąd połączenia z serwerem. Sprawdź czy backend jest uruchomiony.'
        : 'Connection error. Check if backend is running.');
    } finally {
      setBhsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative p-6">
      {/* Tesla-Gotham v4.0: Burning House Widget or Live Score - Top Right */}
      <div className="fixed top-20 right-6 z-50 w-96 hidden lg:block">
        {bhsData && showBhsPanel ? (
          <div className="relative">
            <button
              onClick={() => setShowBhsPanel(false)}
              className="absolute -top-2 -right-2 z-10 bg-gray-800 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-gray-700"
            >
              ×
            </button>
            <BurningHouseScore
              bhs={bhsData}
              language={current_language as 'pl' | 'en'}
            />
          </div>
        ) : (
          <BurningHouseWidget
            language={current_language as 'pl' | 'en'}
            demoMode={true}
          />
        )}
      </div>

      {/* Main Content - Centered */}
      <div className="flex items-center justify-center min-h-[calc(100vh-3rem)]">
        <div className="w-full max-w-2xl space-y-8">
          {/* Title */}
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-2">{t('view1_dashboard.title')}</h1>
            <p className="text-text-secondary-light dark:text-text-secondary-dark">
              Cognitive Sales Engine for Tesla
            </p>
          </div>

        {/* F-1.1: New Session Button */}
        <button
          onClick={handleNewSession}
          className="w-full flex items-center justify-center gap-3 px-8 py-6 text-lg font-semibold rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition shadow-lg"
        >
          <PlusIcon className="w-6 h-6" />
          {t('view1_dashboard.new_session')}
        </button>

        {/* Tesla-Gotham v4.0: High-Energy Risk Analysis Button */}
        <button
          onClick={handleCalculateBHS}
          disabled={bhsLoading}
          className={`w-full flex items-center justify-center gap-3 px-8 py-5 text-lg font-bold rounded-xl shadow-xl transition-all duration-300 ${
            bhsLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-red-500 via-orange-500 to-yellow-500 hover:from-red-600 hover:via-orange-600 hover:to-yellow-600 hover:scale-[1.02] hover:shadow-2xl'
          } text-white`}
        >
          {bhsLoading ? (
            <>
              <SparklesIcon className="w-6 h-6 animate-spin" />
              {current_language === 'pl' ? 'Analizuję...' : 'Analyzing...'}
            </>
          ) : (
            <>
              <FireIcon className="w-6 h-6 animate-pulse" />
              {current_language === 'pl' ? '🔥 Analizuj Ryzyko (Gotham)' : '🔥 Analyze Risk (Gotham)'}
            </>
          )}
        </button>

        {/* BHS Error Display */}
        {bhsError && (
          <div className="p-4 bg-red-100 dark:bg-red-900/30 border border-red-500 rounded-lg text-red-800 dark:text-red-300 text-sm">
            {bhsError}
          </div>
        )}

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border-light dark:border-border-dark"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-bg-light dark:bg-bg-dark text-text-secondary-light dark:text-text-secondary-dark">
              lub
            </span>
          </div>
        </div>

        {/* F-1.2: Resume Session */}
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={resumeId}
              onChange={(e) => {
                setResumeId(e.target.value);
                setResumeError(''); // Clear error on input change
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleResumeSession(resumeId);
                }
              }}
              placeholder={t('view1_dashboard.resume_placeholder')}
              className={`flex-1 px-4 py-3 rounded bg-surface-light dark:bg-surface-dark border ${
                resumeError
                  ? 'border-red-500'
                  : 'border-border-light dark:border-border-dark'
              } focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark`}
            />
            <button
              onClick={() => handleResumeSession(resumeId)}
              className="px-6 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition flex items-center gap-2"
            >
              {t('view1_dashboard.resume_session')}
              <ArrowRightIcon className="w-5 h-5" />
            </button>
          </div>
          
          {/* Resume Error */}
          {resumeError && (
            <p className="text-red-500 text-sm">{resumeError}</p>
          )}
        </div>

        {/* F-1.3: Recent Sessions List */}
        {recentSessions.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <ClockIcon className="w-5 h-5" />
              {t('view1_dashboard.recent_sessions')}
            </h2>
            <div className="space-y-2">
              {recentSessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleRecentSessionClick(session.id)}
                  className="w-full flex items-center justify-between p-4 rounded bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark hover:border-accent-light dark:hover:border-accent-dark transition text-left"
                >
                  <div className="flex-1">
                    <div className="font-medium">{session.id}</div>
                    <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark truncate">
                      {session.context}
                    </div>
                  </div>
                  <ArrowRightIcon className="w-5 h-5 text-text-secondary-light dark:text-text-secondary-dark" />
                </button>
              ))}
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
