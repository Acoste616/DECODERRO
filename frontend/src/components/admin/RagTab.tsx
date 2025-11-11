/**
 * ULTRA v3.0 - Admin: RAG Tab
 * ============================
 * 
 * Implements F-3.2: Full CRUD for RAG knowledge base
 * - List all RAG nuggets with delete button
 * - Form to add new nuggets (title, content, keywords, language)
 */

import { useState, useEffect } from 'react';
import { TrashIcon, PlusIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import { useTranslation } from '../../utils/i18n';
import { api } from '../../utils/api';
import { useStore } from '../../store/useStore';
import type { TLanguage } from '../../types';

interface RAGNugget {
  nugget_id: string;
  title: string;
  content: string;
  keywords: string;
  language: string;
}

export default function RagTab() {
  const { t } = useTranslation();
  const { current_language } = useStore();

  // State
  const [nuggets, setNuggets] = useState<RAGNugget[]>([]);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    keywords: '',
    language: current_language,
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formSuccess, setFormSuccess] = useState(false);

  // Bulk import state
  const [showBulkImportModal, setShowBulkImportModal] = useState(false);
  const [bulkImporting, setBulkImporting] = useState(false);
  const [bulkImportResult, setBulkImportResult] = useState<{
    success_count: number;
    error_count: number;
    errors: string[];
  } | null>(null);

  // Load nuggets on mount and language change
  useEffect(() => {
    loadNuggets();
  }, [current_language]);

  const loadNuggets = async () => {
    setLoading(true);
    try {
      const response = await api.listRAGNuggets(current_language);
      if (response.status === 'success' && response.data) {
        setNuggets(response.data.nuggets || []);
      }
    } catch (error) {
      console.error('Failed to load RAG nuggets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle delete nugget
  const handleDelete = async (nuggetId: string) => {
    if (!confirm(t('view3_admin.confirm_delete'))) {
      return;
    }

    setDeleting(nuggetId);
    try {
      const response = await api.deleteRAGNugget(nuggetId);
      if (response.status === 'success') {
        setNuggets(nuggets.filter((n) => n.nugget_id !== nuggetId));
      }
    } catch (error) {
      console.error('Failed to delete nugget:', error);
    } finally {
      setDeleting(null);
    }
  };

  // Handle add nugget
  const handleAddNugget = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim() || !formData.content.trim()) {
      return;
    }

    setFormSubmitting(true);
    setFormSuccess(false);

    try {
      const response = await api.addRAGNugget({
        title: formData.title,
        content: formData.content,
        keywords: formData.keywords,
        language: formData.language,
      });

      if (response.status === 'success') {
        setFormSuccess(true);
        setFormData({
          title: '',
          content: '',
          keywords: '',
          language: current_language,
        });

        // Reload nuggets
        loadNuggets();

        setTimeout(() => setFormSuccess(false), 3000);
      }
    } catch (error) {
      console.error('Failed to add nugget:', error);
    } finally {
      setFormSubmitting(false);
    }
  };

  // Handle bulk import
  const handleBulkImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setBulkImporting(true);
    setBulkImportResult(null);

    try {
      const text = await file.text();
      const data = JSON.parse(text);

      // Validate that it's an array
      if (!Array.isArray(data)) {
        alert('Invalid JSON format. Expected an array of nuggets.');
        return;
      }

      // Call bulk import API
      const response = await fetch('http://localhost:8000/api/v1/admin/rag/bulk-import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': 'ultra-admin-key-2024',
        },
        body: JSON.stringify({
          nuggets: data,
          language: current_language,
        }),
      });

      const result = await response.json();

      if (result.status === 'success' || result.status === 'partial') {
        setBulkImportResult(result.data);
        loadNuggets(); // Reload the list
      } else {
        alert(`Import failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Bulk import failed:', error);
      alert('Failed to import file. Please check the JSON format.');
    } finally {
      setBulkImporting(false);
      // Reset file input
      event.target.value = '';
    }
  };

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left: Nuggets List */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border-light dark:border-border-dark">
          <div className="flex items-start justify-between mb-2">
            <div>
              <h2 className="text-lg font-bold">{t('view3_admin.rag_nuggets')}</h2>
              <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
                {t('view3_admin.rag_nuggets_desc')}
              </p>
            </div>
            <div>
              <input
                type="file"
                accept=".json"
                onChange={handleBulkImport}
                disabled={bulkImporting}
                className="hidden"
                id="bulk-import-file"
              />
              <label
                htmlFor="bulk-import-file"
                className={`inline-flex items-center gap-2 px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600 transition cursor-pointer ${
                  bulkImporting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <ArrowUpTrayIcon className="w-4 h-4" />
                {bulkImporting ? 'Importing...' : 'Bulk Import JSON'}
              </label>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('common.loading')}...
            </div>
          ) : nuggets.length === 0 ? (
            <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
              {t('view3_admin.no_nuggets')}
            </div>
          ) : (
            <div className="divide-y divide-border-light dark:divide-border-dark">
              {nuggets.map((nugget) => (
                <div key={nugget.nugget_id} className="p-4 hover:bg-bg-light dark:hover:bg-bg-dark transition">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold">{nugget.title}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs px-2 py-0.5 rounded bg-accent-light/20 dark:bg-accent-dark/20 text-accent-light dark:text-accent-dark font-semibold">
                          {nugget.language.toUpperCase()}
                        </span>
                        <span className="text-xs font-mono text-text-secondary-light dark:text-text-secondary-dark">
                          ID: {nugget.nugget_id}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(nugget.nugget_id)}
                      disabled={deleting === nugget.nugget_id}
                      className="ml-3 p-2 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 hover:text-red-600 transition disabled:opacity-50"
                      title={t('common.delete')}
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>

                  <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark line-clamp-3 mb-2">
                    {nugget.content}
                  </p>

                  {nugget.keywords && (
                    <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark">
                      <span className="font-semibold">{t('view3_admin.keywords')}:</span> {nugget.keywords}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Add Nugget Form */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border-light dark:border-border-dark">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <PlusIcon className="w-5 h-5" />
            {t('view3_admin.add_rag_nugget')}
          </h2>
        </div>

        <form onSubmit={handleAddNugget} className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('view3_admin.nugget_title')} *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder={t('view3_admin.nugget_title_placeholder')}
              required
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Content */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('view3_admin.nugget_content')} *
            </label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              placeholder={t('view3_admin.nugget_content_placeholder')}
              rows={8}
              required
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Keywords */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('view3_admin.keywords')}
            </label>
            <input
              type="text"
              value={formData.keywords}
              onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
              placeholder={t('view3_admin.keywords_placeholder')}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
            <p className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-1">
              {t('view3_admin.keywords_hint')}
            </p>
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              {t('view3_admin.language')} *
            </label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value as TLanguage })}
              className="w-full px-3 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            >
              <option value="pl">Polski (PL)</option>
              <option value="en">English (EN)</option>
            </select>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={formSubmitting}
            className="w-full px-4 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition font-semibold disabled:opacity-50"
          >
            {formSubmitting ? t('common.submitting') : t('view3_admin.add_button')}
          </button>

          {/* Success Message */}
          {formSuccess && (
            <div className="p-3 rounded bg-green-100 dark:bg-green-900/30 border border-green-500 text-green-700 dark:text-green-300 text-sm">
              {t('view3_admin.nugget_added')}
            </div>
          )}
        </form>
      </div>

      {/* Bulk Import Results Modal */}
      {bulkImportResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg shadow-2xl max-w-2xl w-full">
            <div className="p-5 border-b border-border-light dark:border-border-dark">
              <h3 className="text-lg font-semibold">Bulk Import Results</h3>
            </div>

            <div className="p-5 space-y-4">
              <div className="flex gap-4">
                <div className="flex-1 p-4 rounded bg-green-100 dark:bg-green-900/30 border border-green-500">
                  <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                    {bulkImportResult.success_count}
                  </div>
                  <div className="text-sm text-green-600 dark:text-green-400">
                    Successfully Imported
                  </div>
                </div>

                {bulkImportResult.error_count > 0 && (
                  <div className="flex-1 p-4 rounded bg-red-100 dark:bg-red-900/30 border border-red-500">
                    <div className="text-2xl font-bold text-red-700 dark:text-red-300">
                      {bulkImportResult.error_count}
                    </div>
                    <div className="text-sm text-red-600 dark:text-red-400">
                      Failed
                    </div>
                  </div>
                )}
              </div>

              {bulkImportResult.errors.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Errors:</h4>
                  <div className="bg-red-50 dark:bg-red-900/20 rounded p-3 max-h-60 overflow-y-auto">
                    {bulkImportResult.errors.map((error, idx) => (
                      <div key={idx} className="text-sm text-red-700 dark:text-red-300 mb-1">
                        • {error}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-5 border-t border-border-light dark:border-border-dark flex justify-end">
              <button
                onClick={() => setBulkImportResult(null)}
                className="px-6 py-2 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
