/**
 * ULTRA v3.0 - View 2: Live Conversation
 * =======================================
 * 
 * Implements:
 * - F-2.1: Journey Stage Selector with AI suggestion highlighting
 * - F-2.2: Conversation log and message input (Optimistic UI)
 * - F-2.3: Feedback logic (thumbs up/down)
 * - F-2.4: WebSocket for Slow Path updates
 * - F-2.6: End Session button and modal
 */

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  PaperAirplaneIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  XMarkIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpSolid, HandThumbDownIcon as HandThumbDownSolid } from '@heroicons/react/24/solid';
import { useStore } from '../store/useStore';
import { useTranslation } from '../utils/i18n';
import { api } from '../utils/api';
import { WebSocketManager } from '../utils/websocket';
import OpusMagnumPanel from '../components/OpusMagnumPanel';
import JourneyStageSelector from '../components/JourneyStageSelector';
import QuestionAnswerModal from '../components/QuestionAnswerModal';
import type { IConversationLogEntry, IFastPathResponse } from '../types';

export default function Conversation() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const {
    session_id,
    setSessionId,
    current_stage,
    suggested_stage,
    setCurrentStage,
    conversation_log,
    setConversationLog,
    app_status,
    setAppStatus,
    setSlowPathData,
    slow_path_error,
    setSlowPathError,
    current_language,
    addConversationEntry,
  } = useStore();

  const [userInput, setUserInput] = useState('');
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [showEndModal, setShowEndModal] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState('');
  const [feedbackState, setFeedbackState] = useState<{ [key: number]: 'positive' | 'negative' | null }>({});

  // Fast Path v2.0: Metadata state
  const [fastPathMetadata, setFastPathMetadata] = useState<{
    optional_followup: string | null;
    seller_questions: string[];
    client_style: string;
    confidence_score: number;
    confidence_reason: string;
  } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsManagerRef = useRef<WebSocketManager | null>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation_log]);

  // Initialize session and setup WebSocket when session ID changes
  useEffect(() => {
    if (!id) return;

    // Update session_id in store
    if (session_id !== id) {
      setSessionId(id);
    }

    // If TEMP-* ID, we'll convert it on first message send (W30, F-1.1)
    // Do NOT initialize WebSocket for TEMP-* IDs
    if (id.startsWith('TEMP-')) {
      return; // Skip WebSocket initialization
    }

    // For real IDs, load existing conversation
    loadSession(id);

    // Initialize WebSocket for Slow Path updates (F-2.4)
    wsManagerRef.current = new WebSocketManager();
    wsManagerRef.current.connect(id, handleWebSocketMessage);

    return () => {
      wsManagerRef.current?.disconnect();
    };
  }, [id]);

  // Watch for session_id changes in store (TEMP-* → S-XXX-YYY conversion)
  useEffect(() => {
    // If session_id changed from TEMP-* to real ID, initialize WebSocket
    if (session_id && !session_id.startsWith('TEMP-')) {
      // Only initialize WebSocket if it's not already connected
      if (!wsManagerRef.current || !wsManagerRef.current.isConnected()) {
        wsManagerRef.current = new WebSocketManager();
        wsManagerRef.current.connect(session_id, handleWebSocketMessage);
      }
    }

    return () => {
      // Cleanup only if we're navigating away from this session
      if (session_id && session_id !== id && !session_id.startsWith('TEMP-')) {
        wsManagerRef.current?.disconnect();
      }
    };
  }, [session_id]);

  // Load existing session
  const loadSession = async (sessionId: string) => {
    try {
      const response = await api.getSession(sessionId);
      if (response.status === 'success' && response.data) {
        setConversationLog(response.data.conversation_log || []);
        setCurrentStage(response.data.current_stage || 'Odkrywanie');

        // CRITICAL FIX: Load Slow Path data if available
        if (response.data.slow_path_log && response.data.slow_path_log.json_output) {
          setSlowPathData(response.data.slow_path_log.json_output);
          setAppStatus('idle');
        }
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  // F-2.4: Handle WebSocket messages (Slow Path updates)
  const handleWebSocketMessage = (message: any) => {
    if (message.type === 'slow_path_complete') {
      setSlowPathData(message.data);
      setAppStatus('idle');
      setSlowPathError(null);
    } else if (message.type === 'slow_path_error') {
      setSlowPathError(message.error || 'Slow Path analysis failed');
      setAppStatus('error');
    }
  };

  // Fallback polling if WebSocket doesn't deliver Slow Path results
  useEffect(() => {
    if (app_status !== 'slow_path_loading') return;

    // Start polling after 60s if WebSocket hasn't delivered
    const pollTimer = setTimeout(() => {
      console.log('⏰ WebSocket timeout - starting fallback polling');

      const pollInterval = setInterval(async () => {
        try {
          const response = await api.getSession(session_id || id);
          if (response.data?.slow_path_log?.json_output) {
            console.log('✅ Fallback polling retrieved Slow Path data from DB');
            setSlowPathData(response.data.slow_path_log.json_output);
            setAppStatus('idle');
            clearInterval(pollInterval);
          }
        } catch (error) {
          console.error('❌ Polling failed:', error);
        }
      }, 5000); // Poll every 5s

      // Stop polling after 2 minutes
      setTimeout(() => {
        console.log('⏹️ Stopping fallback polling after 2 minutes');
        clearInterval(pollInterval);
      }, 120000);
    }, 60000); // Start polling after 60s

    return () => clearTimeout(pollTimer);
  }, [app_status, session_id, id]);

  // F-2.2: Send message (Optimistic UI)
  const handleSendMessage = async () => {
    if (!userInput.trim() || !id) return;

    const messageContent = userInput.trim();
    setUserInput('');

    // Optimistic UI: Add user message immediately
    const userEntry: IConversationLogEntry = {
      log_id: Date.now(),
      session_id: id,
      role: 'Sprzedawca',
      content: messageContent,
      timestamp: new Date().toISOString(),
      language: current_language,
      journey_stage: current_stage,
    };
    addConversationEntry(userEntry);

    // Set loading state
    setAppStatus('fast_path_loading');

    try {
      const response = await api.sendMessage({
        session_id: id,
        user_input: messageContent,
        journey_stage: current_stage,
        language: current_language,
      });

      if (response.status === 'success') {
        const data = response.data as IFastPathResponse;

        // If session was converted from TEMP-*, update session ID and URL (W30, K8)
        if (id.startsWith('TEMP-') && data.session_id && data.session_id !== id) {
          setSessionId(data.session_id);
          // Update URL without full page reload
          window.history.replaceState({}, '', `/session/${data.session_id}`);

          // CRITICAL FIX: Connect WebSocket IMMEDIATELY after ID conversion
          // Don't wait for useEffect - Slow Path is already running!
          if (!wsManagerRef.current || !wsManagerRef.current.isConnected()) {
            wsManagerRef.current = new WebSocketManager();
            wsManagerRef.current.connect(data.session_id, handleWebSocketMessage);
            console.log(`🔌 WebSocket connected immediately for ${data.session_id}`);
          }
        }

        // Add AI response to conversation
        if (data.suggested_response) {
          const aiEntry: IConversationLogEntry = {
            log_id: Date.now(),
            session_id: data.session_id || id,
            role: 'FastPath',
            content: data.suggested_response,
            timestamp: new Date().toISOString(),
            language: current_language,
            journey_stage: current_stage,
          };
          addConversationEntry(aiEntry);
        }

        // Fast Path v2.0: Save metadata
        setFastPathMetadata({
          optional_followup: data.optional_followup,
          seller_questions: data.seller_questions || [],
          client_style: data.client_style || 'spontaneous',
          confidence_score: data.confidence_score || 0.5,
          confidence_reason: data.confidence_reason || '',
        });

        // Update suggested questions (legacy - only optional_followup)
        if (data.optional_followup) {
          setSuggestedQuestions([data.optional_followup]);
        } else {
          setSuggestedQuestions([]);
        }

        setAppStatus('slow_path_loading'); // Slow Path starts automatically
      } else {
        // Error - rollback optimistic message
        setAppStatus('error');
      }
    } catch (error) {
      console.error('Send message failed:', error);
      setAppStatus('error');
    }
  };

  // F-2.3: Handle feedback (thumbs up/down)
  const handleFeedback = async (messageIndex: number, sentiment: 'positive' | 'negative') => {
    if (!id || messageIndex >= conversation_log.length) return;

    const message = conversation_log[messageIndex];
    
    // Update local feedback state
    setFeedbackState({ ...feedbackState, [messageIndex]: sentiment });

    try {
      await api.sendFeedback({
        session_id: id,
        message_index: messageIndex,
        sentiment,
        user_comment: '',
        context: message.content,
      });
    } catch (error) {
      console.error('Feedback submission failed:', error);
    }
  };

  // Handle strategic question click - open modal
  const handleQuestionClick = (question: string) => {
    setSelectedQuestion(question);
    setShowQuestionModal(true);
  };

  // Handle question answer submission
  const handleQuestionAnswer = async (answer: string) => {
    // Format the message as "P: [question] A: [answer]"
    const formattedMessage = `P: ${selectedQuestion}\n\nO: ${answer}`;

    // Send formatted message directly
    if (!id) return;

    setAppStatus('fast_path_loading');

    // Optimistic: Add seller's message immediately
    const sellerEntry: IConversationLogEntry = {
      log_id: Date.now(),
      session_id: id,
      timestamp: new Date().toISOString(),
      role: 'Sprzedawca',
      content: formattedMessage,
      language: current_language,
      journey_stage: current_stage,
    };
    addConversationEntry(sellerEntry);

    try {
      const response = await api.sendMessage({
        session_id: id,
        user_input: formattedMessage,
        journey_stage: current_stage,
        language: current_language,
      });

      if (response.status === 'success' && response.data) {
        // Add AI response if available
        if (response.data.suggested_response) {
          const aiEntry: IConversationLogEntry = {
            log_id: Date.now() + 1,
            session_id: id,
            timestamp: new Date().toISOString(),
            role: 'FastPath',
            content: response.data.suggested_response,
            language: current_language,
            journey_stage: current_stage,
          };
          addConversationEntry(aiEntry);
        }

        // Update suggested questions
        if (response.data.suggested_questions && response.data.suggested_questions.length > 0) {
          setSuggestedQuestions(response.data.suggested_questions);
        }

        setAppStatus('slow_path_loading');
      } else {
        setAppStatus('error');
      }
    } catch (error) {
      console.error('Send message failed:', error);
      setAppStatus('error');
    }
  };

  // F-2.6: End session
  const handleEndSession = async (finalStatus: string) => {
    if (!id) return;

    try {
      await api.endSession(id, finalStatus);

      // Save to recent sessions in localStorage
      const recentSessions = JSON.parse(localStorage.getItem('ultra_recent_sessions') || '[]');
      const newSession = {
        id: id,
        context: conversation_log[0]?.content?.substring(0, 50) || 'New session',
        timestamp: Date.now(),
      };
      localStorage.setItem('ultra_recent_sessions', JSON.stringify([newSession, ...recentSessions].slice(0, 10)));

      // Close modal and navigate back to dashboard
      setShowEndModal(false);
      navigate('/');
    } catch (error) {
      console.error('End session failed:', error);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-bg-light dark:bg-bg-dark">
      {/* Top Bar */}
      <div className="bg-surface-light dark:bg-surface-dark border-b border-border-light dark:border-border-dark px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-bg-light dark:hover:bg-bg-dark rounded transition"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <div className="text-sm text-text-secondary-light dark:text-text-secondary-dark">
              {t('view2_conversation.session_id')}
            </div>
            <div className="font-mono text-sm">{id}</div>
          </div>
        </div>

        <button
          onClick={() => setShowEndModal(true)}
          className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600 transition"
        >
          {t('view2_conversation.end_session')}
        </button>
      </div>

      {/* Main Content: 2-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Conversation */}
        <div className="flex-1 flex flex-col border-r border-border-light dark:border-border-dark">
          {/* F-2.1: Journey Stage Selector with AI Suggestion */}
          <JourneyStageSelector
            currentStage={current_stage}
            suggestedStage={suggested_stage}
            onStageChange={setCurrentStage}
          />

          {/* Conversation Log */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {conversation_log.map((entry, index) => (
              <div
                key={index}
                className={`flex ${entry.role === 'Sprzedawca' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg px-4 py-3 ${
                    entry.role === 'Sprzedawca'
                      ? 'bg-accent-light dark:bg-accent-dark text-accent-text-light'
                      : 'bg-surface-light dark:bg-surface-dark border border-border-light dark:border-border-dark'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{entry.content}</div>
                  
                  {/* F-2.3: Feedback buttons (only for FastPath messages) */}
                  {(entry.role === 'FastPath' || entry.role === 'FastPath-Questions') && (
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleFeedback(index, 'positive')}
                        className="p-1 rounded hover:bg-bg-light dark:hover:bg-bg-dark transition"
                      >
                        {feedbackState[index] === 'positive' ? (
                          <HandThumbUpSolid className="w-4 h-4 text-green-500" />
                        ) : (
                          <HandThumbUpIcon className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleFeedback(index, 'negative')}
                        className="p-1 rounded hover:bg-bg-light dark:hover:bg-bg-dark transition"
                      >
                        {feedbackState[index] === 'negative' ? (
                          <HandThumbDownSolid className="w-4 h-4 text-red-500" />
                        ) : (
                          <HandThumbDownIcon className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Slow Path Error Display */}
          {app_status === 'error' && slow_path_error && (
            <div className="mx-4 mb-4 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded">
              <div className="flex items-start gap-3">
                <div className="text-red-600 dark:text-red-400 text-sm">
                  <strong>❌ {t('view2_conversation.slow_path_error_title')}</strong>
                  <p className="mt-1">{slow_path_error}</p>
                  <p className="mt-2 text-xs opacity-75">
                    {t('view2_conversation.slow_path_error_causes')}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Fast Path v2.0: Metadata Panel */}
          {fastPathMetadata && (
            <div className="mx-4 mb-4 p-3 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="text-xs font-bold text-blue-900 dark:text-blue-100 mb-2">🤖 {t('view2_conversation.jarvis_metadata_title')}</div>

              {/* Confidence + Client Style */}
              <div className="grid grid-cols-2 gap-2 mb-2">
                <div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{t('view2_conversation.ai_confidence')}</div>
                  <div className="flex items-center gap-2">
                    <div className={`text-sm font-bold ${
                      fastPathMetadata.confidence_score >= 0.8 ? 'text-green-600' :
                      fastPathMetadata.confidence_score >= 0.5 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {(fastPathMetadata.confidence_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      ({fastPathMetadata.confidence_reason})
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{t('view2_conversation.client_style')}</div>
                  <span className={`text-xs px-2 py-1 rounded font-semibold ${
                    fastPathMetadata.client_style === 'technical' ? 'bg-purple-100 text-purple-800' :
                    fastPathMetadata.client_style === 'emotional' ? 'bg-pink-100 text-pink-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {fastPathMetadata.client_style === 'technical' ? `🔧 ${t('view2_conversation.client_style_technical')}` :
                     fastPathMetadata.client_style === 'emotional' ? `❤️ ${t('view2_conversation.client_style_emotional')}` : `💬 ${t('view2_conversation.client_style_spontaneous')}`}
                  </span>
                </div>
              </div>

              {/* Seller Questions */}
              {fastPathMetadata.seller_questions.length > 0 && (
                <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 rounded text-xs">
                  <div className="font-semibold text-yellow-800 dark:text-yellow-300 mb-1">
                    🤔 {t('view2_conversation.ai_needs_context')}
                  </div>
                  {fastPathMetadata.seller_questions.map((q, i) => (
                    <div key={i} className="text-gray-700 dark:text-gray-300">• {q}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Strategic Questions */}
          {suggestedQuestions.length > 0 && (
            <div className="border-t border-border-light dark:border-border-dark bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 p-4">
              <div className="text-sm font-semibold mb-2 flex items-center gap-2">
                💡 {t('view2_conversation.suggested_questions')}
              </div>
              <div className="text-xs text-purple-600 dark:text-purple-400 mb-3">
                {t('view2_conversation.question_modal_instruction')}
              </div>
              <div className="space-y-2">
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuestionClick(question)}
                    className="w-full text-left px-4 py-3 text-sm rounded bg-white dark:bg-gray-800 border-2 border-purple-200 dark:border-purple-800 hover:border-purple-500 dark:hover:border-purple-500 hover:shadow-md transition transform hover:-translate-y-0.5"
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-purple-500 mt-0.5 font-bold">{idx + 1}.</span>
                      <span className="flex-1 text-purple-900 dark:text-purple-100">{question}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* F-2.2: Input Field */}
          <div className="border-t border-border-light dark:border-border-dark bg-surface-light dark:bg-surface-dark p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={t('view2_conversation.chat_placeholder')}
                disabled={app_status === 'fast_path_loading'}
                className="flex-1 px-4 py-3 rounded bg-bg-light dark:bg-bg-dark border border-border-light dark:border-border-dark focus:outline-none focus:ring-2 focus:ring-accent-light dark:focus:ring-accent-dark disabled:opacity-50"
              />
              <button
                onClick={handleSendMessage}
                disabled={!userInput.trim() || app_status === 'fast_path_loading'}
                className="px-6 py-3 rounded bg-accent-light dark:bg-accent-dark text-accent-text-light hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
                {t('common.send')}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Opus Magnum */}
        <div className="w-[500px] overflow-y-auto">
          <OpusMagnumPanel />
        </div>
      </div>

      {/* F-2.6: End Session Modal */}
      {showEndModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-light dark:bg-surface-dark rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">{t('view2_conversation.end_session_modal_title')}</h2>
              <button onClick={() => setShowEndModal(false)}>
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <p className="text-text-secondary-light dark:text-text-secondary-dark mb-6">
              {t('view2_conversation.end_session_modal_title')}
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => handleEndSession('success')}
                className="flex-1 px-4 py-2 rounded bg-green-500 text-white hover:bg-green-600 transition"
              >
                {t('view2_conversation.end_session_status_success')}
              </button>
              <button
                onClick={() => handleEndSession('fail')}
                className="flex-1 px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600 transition"
              >
                {t('view2_conversation.end_session_status_fail')}
              </button>
              <button
                onClick={() => setShowEndModal(false)}
                className="px-4 py-2 rounded border border-border-light dark:border-border-dark hover:bg-bg-light dark:hover:bg-bg-dark transition"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Question Answer Modal */}
      {showQuestionModal && (
        <QuestionAnswerModal
          question={selectedQuestion}
          onClose={() => setShowQuestionModal(false)}
          onSubmit={handleQuestionAnswer}
        />
      )}
    </div>
  );
}
