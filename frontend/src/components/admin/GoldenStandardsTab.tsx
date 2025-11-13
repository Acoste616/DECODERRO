/**
 * ULTRA v3.0 - Admin: Golden Standards Tab
 * =========================================
 *
 * Displays all Golden Standards from PostgreSQL database
 * Shows trigger context, response, category, and tags
 */

import { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, TagIcon, FolderIcon } from '@heroicons/react/24/outline';
import { useStore } from '../../store/useStore';
import { api } from '../../utils/api';

interface GoldenStandard {
  id: number;
  trigger_context: string;
  golden_response: string;
  tags: string[];
  category: string | null;
  language: string;
  created_at: string;
}

export default function GoldenStandardsTab() {
  const { current_language } = useStore();

  const [standards, setStandards] = useState<GoldenStandard[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Load standards on mount and language change
  useEffect(() => {
    loadStandards();
  }, [current_language]);

  const loadStandards = async () => {
    setLoading(true);
    try {
      const response = await api.listGoldenStandards(current_language);
      if (response.status === 'success' && response.data) {
        setStandards(response.data.standards || []);
      }
    } catch (error) {
      console.error('Failed to load golden standards:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter standards by search query and category
  const filteredStandards = standards.filter((std) => {
    const matchesSearch =
      searchQuery === '' ||
      std.trigger_context.toLowerCase().includes(searchQuery.toLowerCase()) ||
      std.golden_response.toLowerCase().includes(searchQuery.toLowerCase()) ||
      std.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory =
      selectedCategory === 'all' ||
      std.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = ['all', ...new Set(standards.map(s => s.category).filter(Boolean))];

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold mb-1">⭐ Złote Standardy Odpowiedzi</h2>
            <p className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
              Przeglądaj i analizuj wzorcowe odpowiedzi zaimportowane do systemu
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-accent-light dark:text-accent-dark">
              {standards.length}
            </div>
            <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
              Total Standards
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-secondary-light dark:text-text-secondary-dark" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Szukaj w kontekście, odpowiedziach, tagach..."
              className="w-full pl-10 pr-4 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm"
            />
          </div>

          {/* Category Filter */}
          <div className="relative">
            <FolderIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-secondary-light dark:text-text-secondary-dark" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark text-sm appearance-none"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? '🗂️ Wszystkie kategorie' : `📁 ${cat || 'Bez kategorii'}`}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter results count */}
        {(searchQuery || selectedCategory !== 'all') && (
          <div className="mt-3 text-sm text-text-secondary-light dark:text-text-secondary-dark">
            Znaleziono: <span className="font-semibold">{filteredStandards.length}</span> z {standards.length}
          </div>
        )}
      </div>

      {/* Standards List */}
      <div className="bg-surface-light dark:bg-surface-dark rounded-lg border border-border-light dark:border-border-dark overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-text-secondary-light dark:text-text-secondary-dark">
            Ładowanie...
          </div>
        ) : filteredStandards.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <div className="text-text-secondary-light dark:text-text-secondary-dark">
              {searchQuery || selectedCategory !== 'all'
                ? 'Nie znaleziono pasujących standardów'
                : 'Brak złotych standardów'
              }
            </div>
          </div>
        ) : (
          <div className="divide-y divide-border-light dark:divide-border-dark max-h-[calc(100vh-400px)] overflow-y-auto">
            {filteredStandards.map((standard) => (
              <div
                key={standard.id}
                className="p-6 hover:bg-bg-light dark:hover:bg-bg-dark transition"
              >
                {/* Header with category */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {standard.category && (
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                          📁 {standard.category}
                        </span>
                      )}
                      <span className="text-xs text-text-secondary-light dark:text-text-secondary-dark">
                        ID: {standard.id}
                      </span>
                    </div>

                    {/* Trigger Context */}
                    <div className="mb-3">
                      <div className="text-xs font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-1 flex items-center gap-1">
                        <span>📍</span>
                        KONTEKST WYZWALACZA:
                      </div>
                      <div className="font-semibold text-lg">
                        {standard.trigger_context}
                      </div>
                    </div>

                    {/* Golden Response */}
                    <div className="mb-3">
                      <div className="text-xs font-semibold text-text-secondary-light dark:text-text-secondary-dark mb-1 flex items-center gap-1">
                        <span>⭐</span>
                        WZORCOWA ODPOWIEDŹ:
                      </div>
                      <div className="text-sm p-3 bg-bg-light dark:bg-bg-dark rounded border border-border-light dark:border-border-dark leading-relaxed">
                        {standard.golden_response}
                      </div>
                    </div>

                    {/* Tags */}
                    {standard.tags && standard.tags.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap">
                        <TagIcon className="w-4 h-4 text-text-secondary-light dark:text-text-secondary-dark" />
                        {standard.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-xs bg-accent-light/10 dark:bg-accent-dark/10 text-accent-light dark:text-accent-dark"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer with metadata */}
                <div className="mt-3 pt-3 border-t border-border-light dark:border-border-dark flex items-center justify-between text-xs text-text-secondary-light dark:text-text-secondary-dark">
                  <div className="flex items-center gap-4">
                    <span>🌐 {standard.language.toUpperCase()}</span>
                    {standard.created_at && (
                      <span>📅 {new Date(standard.created_at).toLocaleDateString('pl-PL')}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
