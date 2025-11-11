/**
 * ULTRA v3.0 - Admin: Analytics Tab
 * ==================================
 * 
 * Implements F-3.3: Analytics dashboard with 3 charts
 * - Date range and language filters
 * - 3 Recharts visualizations (BarChart, RadarChart, LineChart)
 */

import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  RadarChart,
  Radar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { useTranslation } from '../../utils/i18n';
import { api } from '../../utils/api';
import { useStore } from '../../store/useStore';

interface AnalyticsData {
  chart1_data: any[];
  chart2_data: any[];
  chart3_data: any[];
  summary?: {
    total_sessions: number;
    avg_confidence: number;
    top_playbook: string;
  };
}

export default function AnalyticsTab() {
  const { t } = useTranslation();
  const { current_language } = useStore();

  // Filter state
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [filterLanguage, setFilterLanguage] = useState(current_language);

  // Data state
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);

  // Load analytics on mount
  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (filterLanguage) params.language = filterLanguage;

      const response = await api.getAnalyticsDashboard(params);
      if (response.status === 'success' && response.data) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFilters = () => {
    loadAnalytics();
  };

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-4">
        <h2 className="text-lg font-bold mb-4">{t('admin.filters')}</h2>
        
        <div className="grid grid-cols-4 gap-4">
          {/* Date From */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.date_from')}
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Date To */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.date_to')}
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('admin.language')}
            </label>
            <select
              value={filterLanguage}
              onChange={(e) => setFilterLanguage(e.target.value as 'pl' | 'en')}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            >
              <option value="">All / Wszystkie</option>
              <option value="pl">Polski (PL)</option>
              <option value="en">English (EN)</option>
            </select>
          </div>

          {/* Apply Button */}
          <div className="flex items-end">
            <button
              onClick={handleApplyFilters}
              disabled={loading}
              className="w-full px-4 py-2 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition font-semibold disabled:opacity-50"
            >
              {loading ? t('common.loading') : t('admin.apply_filters')}
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12 text-text-secondary-light dark:text-text-secondary-dark">
          {t('common.loading')}...
        </div>
      )}

      {/* Charts */}
      {!loading && data && (
        <>
          {/* Summary Stats */}
          {data.summary && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-4">
                <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark mb-1">
                  {t('admin.total_sessions')}
                </div>
                <div className="text-3xl font-bold">{data.summary.total_sessions}</div>
              </div>
              <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-4">
                <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark mb-1">
                  {t('admin.avg_confidence')}
                </div>
                <div className="text-3xl font-bold">{data.summary.avg_confidence}%</div>
              </div>
              <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-4">
                <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark mb-1">
                  {t('admin.top_playbook')}
                </div>
                <div className="text-lg font-bold truncate">{data.summary.top_playbook}</div>
              </div>
            </div>
          )}

          {/* Chart 1: Playbook Effectiveness (BarChart) */}
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-6">
            <h3 className="text-lg font-bold mb-4">{t('admin.chart1_title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.chart1_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="name" stroke="#999" />
                <YAxis stroke="#999" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a1a',
                    border: '1px solid #333',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="effectiveness" fill="#3b82f6" name={t('admin.effectiveness')} />
                <Bar dataKey="usage_count" fill="#10b981" name={t('admin.usage_count')} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 2: DISC Correlation (RadarChart) */}
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-6">
            <h3 className="text-lg font-bold mb-4">{t('admin.chart2_title')}</h3>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={data.chart2_data}>
                <PolarGrid stroke="#333" />
                <PolarAngleAxis dataKey="disc_type" tick={{ fill: '#999', fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#999' }} />
                <Radar
                  name={t('admin.conversion_rate')}
                  dataKey="conversion_rate"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.6}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a1a',
                    border: '1px solid #333',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 3: Temperature Validation (LineChart) */}
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-6">
            <h3 className="text-lg font-bold mb-4">{t('admin.chart3_title')}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.chart3_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="date" stroke="#999" />
                <YAxis stroke="#999" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a1a',
                    border: '1px solid #333',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="predicted_temp"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name={t('admin.predicted_temp')}
                />
                <Line
                  type="monotone"
                  dataKey="actual_temp"
                  stroke="#10b981"
                  strokeWidth={2}
                  name={t('admin.actual_temp')}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* Empty State */}
      {!loading && !data && (
        <div className="text-center py-12 text-text-secondary-light dark:text-text-secondary-dark">
          {t('admin.no_analytics_data')}
        </div>
      )}
    </div>
  );
}
