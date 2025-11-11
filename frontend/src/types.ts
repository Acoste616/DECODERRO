/**
 * ULTRA DOJO AI - TypeScript Type Definitions
 * ============================================
 * 
 * Central repository for all TypeScript type definitions and interfaces.
 * Defines complete API contracts for all 14 endpoints based on 02_PEGT_FINAL.md Module 3.
 * 
 * This file implements Step 2 of PEGT: Schematy Danych i API (Contracts First).
 * 
 * @module types
 */

// =============================================================================
// Base Type Literals
// =============================================================================

/** Conversation role types for message attribution */
export type TConversationRole = "Sprzedawca" | "FastPath" | "FastPath-Questions";

/** Supported application languages */
export type TLanguage = "pl" | "en";


// =============================================================================
// Base Interfaces
// =============================================================================

/**
 * Conversation log entry tracking exchanges between seller and AI system.
 * Used in conversation history and session retrieval.
 */
export interface IConversationLogEntry {
  log_id: number;
  session_id: string;
  /** (W27) ISO 8601 format timestamp */
  timestamp: string;
  role: TConversationRole;
  content: string;
  language: TLanguage;
  /** (W1) journey_stage accepts null for initial conversation states */
  journey_stage: "Odkrywanie" | "Analiza" | "Decyzja" | null;
}


// =============================================================================
// Opus Magnum Module Interfaces (M1-M7)
// =============================================================================

/**
 * Base interface for all Opus Magnum analysis modules.
 * Provides shared confidence scoring mechanism.
 * 
 * (W25) Confidence score interpretation:
 * - 90-100: High confidence (Wysoka pewność)
 * - 70-89: Medium confidence (Średnia pewność)
 * - 0-69: Low confidence (Niska pewność)
 */
export interface IOpusMagnumModuleBase {
  /** Analysis confidence level (0-100) */
  confidence_score: number;
}

/**
 * Module 1: DNA Client - Holistic client profile and psychological fingerprint.
 * Provides comprehensive client overview and key persuasion levers.
 */
export interface IM1DnaClient extends IOpusMagnumModuleBase {
  /** Comprehensive client overview */
  holistic_summary: string;
  /** Primary purchase driver */
  main_motivation: string;
  /** Preferred interaction pattern */
  communication_style: string;
  /** (W3) Persuasion arguments with rationale */
  key_levers: Array<{ argument: string; rationale: string }>;
  /** Warning signals and objections */
  red_flags: string[];
}

/**
 * Module 2: Tactical Indicators - Real-time sales opportunity metrics.
 * Provides purchase temperature, churn risk, and test drive risk assessment.
 */
export interface IM2TacticalIndicators extends IOpusMagnumModuleBase {
  /** Purchase readiness metric */
  purchase_temperature: { value: number; label: string };
  /** Customer loss risk */
  churn_risk: { 
    level: "Low" | "Medium" | "High"; 
    percentage: number; 
    reason: string;
  };
  /** Test drive abandonment risk */
  fun_drive_risk: { 
    level: "Low" | "Medium" | "High"; 
    percentage: number; 
    reason: string;
  };
}

/**
 * Module 3: Psychometric Profile - Deep psychological profiling.
 * Uses DISC model, Big Five traits, and Schwartz values frameworks.
 */
export interface IM3PsychometricProfile extends IOpusMagnumModuleBase {
  /** Dominant DISC personality type */
  dominant_disc: { 
    type: "D" | "I" | "S" | "C"; 
    rationale: string;
  };
  /** Big Five personality traits with levels and scores */
  big_five_traits: {
    openness: { level: string; score: number };
    conscientiousness: { level: string; score: number };
    extraversion: { level: string; score: number };
    agreeableness: { level: string; score: number };
    neuroticism: { level: string; score: number };
  };
  /** Universal human values */
  schwartz_values: Array<{ value: string; rationale: string }>;
}

/**
 * Module 4: Deep Motivation - Core psychological drivers and evidence.
 * Extracts key insights from conversation with supporting quotes.
 */
export interface IM4DeepMotivation extends IOpusMagnumModuleBase {
  /** Central motivational finding */
  key_insight: string;
  /** Direct client quotes supporting insight */
  evidence_quotes: string[];
  /** Tesla-specific engagement angle */
  tesla_hook: string;
}

/**
 * Module 5: Predictive Paths - Forecasted customer journey trajectories.
 * Predicts possible scenarios with probabilities and recommendations.
 */
export interface IM5PredictivePaths extends IOpusMagnumModuleBase {
  /** Journey scenarios with probabilities and recommendations */
  paths: Array<{ 
    path: string; 
    probability: number; 
    recommendations: string[];
  }>;
}

/**
 * Module 6: Strategic Playbook - Situation-specific response templates.
 * Provides pre-built conversation plays with trigger conditions.
 */
export interface IM6StrategicPlaybook extends IOpusMagnumModuleBase {
  /** Response templates with triggers and content */
  plays: Array<{ 
    title: string; 
    trigger: string; 
    content: string[]; 
    confidence_score: number;
  }>;
}

/**
 * Module 7: Decision Vectors - Stakeholder influence mapping.
 * Maps decision influencers and recommended engagement strategies.
 */
export interface IM7DecisionVectors extends IOpusMagnumModuleBase {
  /** Stakeholder influence vectors */
  vectors: Array<{ 
    stakeholder: string; 
    influence: string; 
    vector: string; 
    focus: string; 
    strategy: string; 
    confidence_score: number;
  }>;
}


// =============================================================================
// Composite Interfaces
// =============================================================================

/**
 * Aggregate container for all seven Opus Magnum analysis modules.
 * Complete psychological and strategic analysis output from Slow Path AI.
 */
export interface IOpusMagnumModules {
  dna_client: IM1DnaClient;
  tactical_indicators: IM2TacticalIndicators;
  psychometric_profile: IM3PsychometricProfile;
  deep_motivation: IM4DeepMotivation;
  predictive_paths: IM5PredictivePaths;
  strategic_playbook: IM6StrategicPlaybook;
  decision_vectors: IM7DecisionVectors;
}

/**
 * Complete Slow Path AI analysis output.
 * 
 * (K3) Language mapping: suggested_stage accepts both Polish and English values.
 * Frontend must handle bi-directional mapping with backend.
 */
export interface IOpusMagnumJSON {
  /** Aggregate analysis confidence (0-100) */
  overall_confidence: number;
  /** Recommended journey stage (accepts PL/EN values) */
  suggested_stage: 
    | "Odkrywanie" | "Analiza" | "Decyzja"  // Polish values
    | "Discovery" | "Analysis" | "Decision"; // English values
  /** All seven module outputs */
  modules: IOpusMagnumModules;
}

/**
 * Audit trail for asynchronous Slow Path AI analysis.
 * Stores complete Opus Magnum analysis results.
 */
export interface ISlowPathLogEntry {
  log_id: number;
  session_id: string;
  /** ISO 8601 format timestamp */
  timestamp: string;
  json_output: IOpusMagnumJSON;
  status: "Success" | "Error";
}


// =============================================================================
// Global API Response Wrapper
// =============================================================================

/**
 * Standardized response format across all API endpoints.
 * 
 * Status values:
 * - "success": Request completed successfully, data present
 * - "fail": Client error (4xx), validation failed
 * - "error": Server error (5xx), unexpected failure
 * 
 * @template T - Type of data payload
 */
export interface IGlobalAPIResponse<T> {
  status: "success" | "fail" | "error";
  data?: T;
  message?: string;
}


// =============================================================================
// Endpoint-Specific Response Interfaces
// =============================================================================

/**
 * (K7) Response data for Fast Path AI suggestions.
 * 
 * Returned by POST /api/v1/sessions/send (Endpoint 3, F-2.2).
 * Must deliver within 2-second P95 latency (per UAT-1).
 * 
 * @see IGlobalAPIResponse for wrapper structure
 */
export interface ISendResponseData {
  /** AI-generated seller response text */
  suggested_response: string;
  /** Follow-up question suggestions (typically 2-3) */
  suggested_questions: string[];
}

/**
 * Single feedback theme cluster.
 */
export interface IFeedbackGroup {
  /** Cluster label (e.g., "zbyt łagodne") */
  theme_name: string;
  /** Number of occurrences in cluster */
  count: number;
  /** Example feedback text from cluster */
  representative_note: string;
}

/**
 * (K12) Thematic grouping of seller feedback.
 * 
 * Returned by GET /api/v1/admin/feedback/grouped (Endpoint 7, F-3.1).
 * Powers AI Dojo feedback analysis UI.
 * 
 * @see IGlobalAPIResponse for wrapper structure
 */
export interface FeedbackGroupingResponse {
  /** Feedback theme clusters */
  groups: IFeedbackGroup[];
}

/**
 * (W12) RAG knowledge nugget payload schema.
 * Stored in Qdrant with vector embeddings.
 */
export interface INuggetPayload {
  /** Nugget headline */
  title: string;
  /** Full nugget text content */
  content: string;
  /** (W24) CSV keyword list (e.g., "leasing, vat, b2b") */
  keywords: string;
  /** Content language */
  language: TLanguage;
  /** Nugget category (optional) */
  type?: string;
  /** Additional metadata tags (optional) */
  tags?: string[];
  /** Applicable client archetypes (optional) */
  archetype_filter?: string[];
}

/**
 * Complete RAG nugget with Qdrant ID and payload.
 */
export interface IRAGNugget {
  /** Qdrant point ID for deletion operations */
  id: string;
  /** Nugget metadata and content */
  payload: INuggetPayload;
}

/**
 * (W12) Response schema for RAG knowledge nugget listing.
 * 
 * Returned by GET /api/v1/admin/rag/list (Endpoint 10, F-3.2).
 * Supports language-filtered queries.
 * 
 * @see IGlobalAPIResponse for wrapper structure
 */
export interface IRAGListResponse {
  /** All RAG entries with IDs and payloads */
  nuggets: IRAGNugget[];
}


// =============================================================================
// WebSocket Message Types (K2)
// =============================================================================

/**
 * (K2) Real-time Slow Path progress update messages.
 * 
 * Server→Client only (no client messages required).
 * Endpoint: wss://{domain}/api/v1/ws/sessions/{session_id}
 * 
 * (W30) Authentication: Backend must validate session_id exists before accepting connection.
 * 
 * Message types:
 * - "slow_path_update": Final analysis complete
 * - "slow_path_error": Analysis failed
 * - "slow_path_progress": Incremental progress update
 */
export type WebSocketMessage =
  | {
      type: "slow_path_update";
      status?: "Success" | "Error";
      data?: IOpusMagnumJSON;
      message?: string;
    }
  | {
      type: "slow_path_error";
      status?: "Error";
      message?: string;
    }
  | {
      type: "slow_path_progress";
      progress?: number; // 0-100
      message?: string;
    };
