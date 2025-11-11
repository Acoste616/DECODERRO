/**
 * ULTRA v3.0 - Zustand Global State Store
 * =========================================
 * 
 * Central state management implementing PEGT Module 4.
 * Manages session state, conversation history, AI analysis, and UI preferences.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { 
  IConversationLogEntry, 
  IOpusMagnumJSON, 
  TLanguage 
} from '../types';

/**
 * Application state shape (PEGT Module 4)
 */
interface UltraStore {
  // Session State
  session_id: string | null;
  current_stage: 'Odkrywanie' | 'Analiza' | 'Decyzja';
  suggested_stage: 'Odkrywanie' | 'Analiza' | 'Decyzja' | null;

  // Conversation Data
  conversation_log: IConversationLogEntry[];
  slow_path_data: IOpusMagnumJSON | null;
  
  // Application Status
  app_status: 'idle' | 'fast_path_loading' | 'slow_path_loading' | 'error';
  slow_path_error: string | null;
  
  // UI Preferences
  current_language: TLanguage;
  current_theme: 'light' | 'dark';
  
  // Admin State
  admin_key: string | null;
  
  // Actions
  setSessionId: (id: string | null) => void;
  setCurrentStage: (stage: 'Odkrywanie' | 'Analiza' | 'Decyzja') => void;
  setSuggestedStage: (stage: 'Odkrywanie' | 'Analiza' | 'Decyzja' | null) => void;
  setConversationLog: (log: IConversationLogEntry[]) => void;
  addConversationEntry: (entry: IConversationLogEntry) => void;
  setSlowPathData: (data: IOpusMagnumJSON | null) => void;
  setAppStatus: (status: UltraStore['app_status']) => void;
  setSlowPathError: (error: string | null) => void;
  setLanguage: (language: TLanguage) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setAdminKey: (key: string | null) => void;
  
  // Complex Actions
  resetSession: () => void;
  optimisticAddMessage: (content: string, role: IConversationLogEntry['role']) => void;
  rollbackOptimisticMessage: () => void;
}

/**
 * Create Zustand store with localStorage persistence for preferences
 */
export const useStore = create<UltraStore>()(
  persist(
    (set, get) => ({
      // Initial State
      session_id: null,
      current_stage: 'Odkrywanie',
      suggested_stage: null,
      conversation_log: [],
      slow_path_data: null,
      app_status: 'idle',
      slow_path_error: null,
      current_language: 'pl',
      current_theme: 'light',
      admin_key: null,
      
      // Simple Setters
      setSessionId: (id) => set({ session_id: id }),

      setCurrentStage: (stage) => set({ current_stage: stage }),

      setSuggestedStage: (stage) => set({ suggested_stage: stage }),

      setConversationLog: (log) => set({ conversation_log: log }),
      
      addConversationEntry: (entry) => set((state) => ({
        conversation_log: [...state.conversation_log, entry]
      })),
      
      setSlowPathData: (data) => {
        set({ slow_path_data: data });

        // Update suggested stage from Slow Path AI
        if (data?.suggested_stage) {
          // Normalize stage to Polish format
          const stageMap: Record<string, 'Odkrywanie' | 'Analiza' | 'Decyzja'> = {
            'Odkrywanie': 'Odkrywanie',
            'Discovery': 'Odkrywanie',
            'Analiza': 'Analiza',
            'Analysis': 'Analiza',
            'Decyzja': 'Decyzja',
            'Decision': 'Decyzja',
          };
          const normalizedStage = stageMap[data.suggested_stage];
          if (normalizedStage) {
            set({ suggested_stage: normalizedStage });
          }
        }
      },
      
      setAppStatus: (status) => set({ app_status: status }),
      
      setSlowPathError: (error) => set({ slow_path_error: error }),
      
      setLanguage: (language) => {
        set({ current_language: language });
        // Update document lang attribute
        document.documentElement.lang = language;
      },
      
      setTheme: (theme) => {
        set({ current_theme: theme });
        // Update document class for Tailwind dark mode
        if (theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      },
      
      setAdminKey: (key) => set({ admin_key: key }),
      
      // Complex Actions
      
      /**
       * Reset session state (for new session or navigation)
       */
      resetSession: () => set({
        session_id: null,
        current_stage: 'Odkrywanie',
        suggested_stage: null,
        conversation_log: [],
        slow_path_data: null,
        app_status: 'idle',
        slow_path_error: null,
      }),
      
      /**
       * Optimistic UI: Add message immediately before API confirmation
       * (F-2.2, PEGT Module 6)
       */
      optimisticAddMessage: (content, role) => {
        const tempEntry: IConversationLogEntry = {
          log_id: Date.now(), // Temporary ID
          session_id: get().session_id || '',
          timestamp: new Date().toISOString(),
          role,
          content,
          language: get().current_language,
          journey_stage: get().current_stage,
        };
        
        set((state) => ({
          conversation_log: [...state.conversation_log, tempEntry],
        }));
      },
      
      /**
       * Rollback optimistic message on API error (K11)
       */
      rollbackOptimisticMessage: () => {
        set((state) => ({
          conversation_log: state.conversation_log.slice(0, -1),
        }));
      },
    }),
    {
      name: 'ultra-storage', // localStorage key
      partialize: (state) => ({
        // Only persist UI preferences, not session data
        current_language: state.current_language,
        current_theme: state.current_theme,
        admin_key: state.admin_key,
      }),
    }
  )
);

/**
 * Initialize theme on app load
 */
const initializeTheme = () => {
  const theme = useStore.getState().current_theme;
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  }
};

// Run on module load
initializeTheme();
