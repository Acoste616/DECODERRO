/**
 * ULTRA v3.0 - Admin: Feedback Tab (IMPROVED LAYOUT)
 * ===================================================
 *
 * Improved 2-column layout + modal for Golden Standard creation
 * Better readability and usability
 */

import { useState, useEffect } from 'react';
import { ChevronRightIcon, PlusIcon, XMarkIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';
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
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form state for Golden Standard
  const [formData, setFormData] = useState({
    trigger_context: '',
    golden_response: '',
    language: current_language,
    category: '',
  });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formSuccess, setFormSuccess] = useState(false);

  // Bulk import state
  const [bulkImporting, setBulkImporting] = useState(false);
  const [bulkImportResult, setBulkImportResult] = useState<{
    success_count: number;
    error_count: number;
    errors: string[];
  } | null>(null);

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
        setTimeout(() => {
          setFormSuccess(false);
          setShowCreateModal(false);
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to create golden standard:', error);
    } finally {
      setFormSubmitting(false);
    }
  };

  // Handle bulk import for golden standards
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
        alert('Invalid JSON format. Expected an array of golden standards.');
        return;
      }

      // Call bulk import API
      const response = await fetch('http://localhost:8000/api/v1/admin/golden-standards/bulk-import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': 'ultra-admin-key-2024',
        },
        body: JSON.stringify({
          standards: data,
          language: current_language,
        }),
      });

      const result = await response.json();

      if (result.status === 'success' || result.status === 'partial') {
        setBulkImportResult(result.data);
        loadGroups(); // Reload the groups
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
    <div className="h-[calc(100vh-200px)] flex flex-col gap-4">
      {/* Header with Create Button */}
      <div className="flex items-center justify-between bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">📊 Tablica Feedbacku</h2>
          <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
            Analizuj feedback sprzedawców i twórz złote standardy odpowiedzi
          </p>
        </div>
        <div className="flex gap-3">
          <input
            type="file"
            accept=".json"
            onChange={handleBulkImport}
            disabled={bulkImporting}
            className="hidden"
            id="bulk-import-golden-standards"
          />
          <label
            htmlFor="bulk-import-golden-standards"
            className={`inline-flex items-center gap-2 px-6 py-3 rounded bg-blue-500 text-white hover:bg-blue-600 transition font-semibold cursor-pointer shadow-lg ${
              bulkImporting ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <ArrowUpTrayIcon className="w-5 h-5" />
            {bulkImporting ? 'Importing...' : 'Bulk Import JSON'}
          </label>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition font-semibold flex items-center gap-2 shadow-lg"
          >
            <PlusIcon className="w-5 h-5" />
            Utwórz Złoty Standard
          </button>
        </div>
      </div>

      {/* Main Content: 2-column layout */}
      <div className="flex-1 grid grid-cols-[400px_1fr] gap-6 overflow-hidden">
        {/* Column 1: Grouped Themes */}
        <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
          <div className="p-4 border-b border-border-light dark:border-border-dark bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20">
            <h3 className="text-lg font-bold">Tematy Feedbacku</h3>
            <p className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-1">
              Zgrupowany feedback według kategorii
            </p>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center text-text-secondary-light dark:text-text-secondary-dark">
                Ładowanie...
              </div>
            ) : groups.length === 0 ? (
              <div className="p-6 text-center">
                <div className="text-4xl mb-2">📭</div>
                <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
                  Brak feedbacku
                </div>
              </div>
            ) : (
              <div className="divide-y divide-border-light dark:divide-border-dark">
                {groups.map((group) => (
                  <button
                    key={group.theme_name}
                    onClick={() => handleThemeSelect(group.theme_name)}
                    className={`w-full p-4 text-left hover:bg-bg-light dark:hover:bg-bg-dark transition flex items-start justify-between group ${
                      selectedTheme === group.theme_name
                        ? 'bg-accent-light/10 dark:bg-accent-dark/10 border-l-4 border-accent-light dark:border-accent-dark'
                        : ''
                    }`}
                  >
                    <div className="flex-1">
                      <div className="font-semibold mb-1">{group.theme_name}</div>
                      <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark mb-2">
                        {group.count} opinii
                      </div>
                      <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark line-clamp-2">
                        "{group.representative_note}"
                      </div>
                    </div>
                    <ChevronRightIcon className="w-5 h-5 text-text-secondary-light dark:text-text-secondary-dark ml-3 mt-1 group-hover:text-accent-light dark:group-hover:text-accent-dark transition" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Feedback Details */}
        <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden flex flex-col">
          <div className="p-4 border-b border-border-light dark:border-border-dark bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-900/20 dark:to-green-900/20">
            <h3 className="text-lg font-bold">Szczegóły Feedbacku</h3>
            {selectedTheme && (
              <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-1">
                Temat: <span className="font-semibold">{selectedTheme}</span>
              </p>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {!selectedTheme ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="text-6xl mb-4">👈</div>
                  <div className="text-text-secondary-light dark:text-text-secondary-dark">
                    Wybierz temat z listy po lewej<br/>aby zobaczyć szczegóły
                  </div>
                </div>
              </div>
            ) : detailsLoading ? (
              <div className="h-full flex items-center justify-center text-text-secondary-light dark:text-text-secondary-dark">
                Ładowanie szczegółów...
              </div>
            ) : details.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="text-4xl mb-2">📭</div>
                  <div className="text-text-secondary-light dark:text-text-secondary-dark">
                    Brak szczegółów
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {details.map((detail) => (
                  <div
                    key={detail.feedback_id}
                    className="bg-bg-light dark:bg-bg-dark rounded-lg border border-border-light dark:border-border-dark p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-mono text-text-secondary-light dark:text-text-secondary-dark bg-surface-light dark:bg-surface-dark px-2 py-1 rounded">
                        {detail.session_id}
                      </span>
                      <span className={`text-2xl ${
                        detail.sentiment === 'positive' ? '' : ''
                      }`}>
                        {detail.sentiment === 'positive' ? '👍' : '👎'}
                      </span>
                    </div>

                    {detail.user_comment && (
                      <div className="mb-3 p-3 rounded bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500">
                        <div className="text-xs font-semibold mb-1 text-yellow-800 dark:text-yellow-300">
                          💬 Komentarz sprzedawcy:
                        </div>
                        <div className="text-sm">{detail.user_comment}</div>
                      </div>
                    )}

                    <div>
                      <div className="text-xs font-semibold mb-1 text-text-secondary-light dark:text-text-secondary-dark">
                        📝 Kontekst (wiadomość AI):
                      </div>
                      <div className="text-sm p-3 bg-surface-light dark:bg-surface-dark rounded border border-border-light dark:border-border-dark">
                        {detail.context}
                      </div>
                    </div>

                    <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark mt-3 flex items-center gap-2">
                      <span>📅</span>
                      {new Date(detail.timestamp).toLocaleString('pl-PL')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Golden Standard Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-border-light dark:border-border-dark bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold flex items-center gap-2">
                    <PlusIcon className="w-6 h-6" />
                    Utwórz Złoty Standard Odpowiedzi
                  </h3>
                  <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark mt-1">
                    Zdefiniuj wzorcową odpowiedź na często pojawiającą się sytuację
                  </p>
                </div>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="p-2 hover:bg-bg-light dark:hover:bg-bg-dark rounded transition"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleCreateGoldenStandard} className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Trigger Context */}
              <div>
                <label className="block text-sm font-bold mb-2 flex items-center gap-2">
                  <span>📍</span>
                  Kontekst Wyzwalacza (sytuacja/pytanie klienta) *
                </label>
                <textarea
                  value={formData.trigger_context}
                  onChange={(e) => setFormData({ ...formData, trigger_context: e.target.value })}
                  placeholder="np. Klient pyta o zasięg w zimie..."
                  rows={4}
                  required
                  className="w-full px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border-2 border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
                />
              </div>

              {/* Golden Response */}
              <div>
                <label className="block text-sm font-bold mb-2 flex items-center gap-2">
                  <span>⭐</span>
                  Wzorcowa Odpowiedź *
                </label>
                <textarea
                  value={formData.golden_response}
                  onChange={(e) => setFormData({ ...formData, golden_response: e.target.value })}
                  placeholder="Wprowadź idealną odpowiedź, która powinna być użyta w tej sytuacji..."
                  rows={8}
                  required
                  className="w-full px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border-2 border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Language Selector */}
                <div>
                  <label className="block text-sm font-bold mb-2">
                    Język *
                  </label>
                  <select
                    value={formData.language}
                    onChange={(e) => setFormData({ ...formData, language: e.target.value as 'pl' | 'en' })}
                    className="w-full px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border-2 border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
                  >
                    <option value="pl">🇵🇱 Polski</option>
                    <option value="en">🇬🇧 English</option>
                  </select>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-bold mb-2">
                    Kategoria
                  </label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="np. obiekcje, ceny, zasięg..."
                    className="w-full px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border-2 border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
                  />
                </div>
              </div>

              {/* Success Message */}
              {formSuccess && (
                <div className="p-4 rounded bg-green-100 dark:bg-green-900/30 border-2 border-green-500 text-green-700 dark:text-green-300 flex items-center gap-2">
                  <span className="text-2xl">✅</span>
                  <span className="font-semibold">Złoty standard utworzony pomyślnie!</span>
                </div>
              )}
            </form>

            {/* Modal Footer */}
            <div className="p-6 border-t border-border-light dark:border-border-dark bg-bg-light dark:bg-bg-dark flex items-center justify-between">
              <div className="text-xs text-text-secondary-light dark:text-text-secondary-dark">
                Złote standardy pomogą AI generować lepsze odpowiedzi
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-6 py-3 rounded border-2 border-border-light dark:border-border-dark hover:bg-surface-light dark:hover:bg-surface-dark transition"
                >
                  Anuluj
                </button>
                <button
                  onClick={handleCreateGoldenStandard}
                  disabled={formSubmitting || !formData.trigger_context.trim() || !formData.golden_response.trim()}
                  className="px-8 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition font-bold disabled:opacity-50 shadow-lg"
                >
                  {formSubmitting ? 'Tworzenie...' : 'Utwórz Złoty Standard'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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
