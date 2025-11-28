/**
 * ULTRA v3.1 - Backend to Frontend Data Mapper
 * 
 * Transforms actual backend analysis format to frontend legacy UI structure.
 * Backend sends: {summary, psychometrics, sales_metrics, next_move, journey_stage}
 * Frontend expects: {m1_dna, m2_indicators, m3_psychometrics, m4_motivation, m6_playbook, journeyStageAnalysis}
 */

import { AnalysisState, JourneyStage } from '../types';

/**
 * Backend Analysis Format (from analysis_engine.py)
 */
export interface BackendAnalysisData {
    // Actual backend format
    summary?: string;
    psychometrics?: {
        disc_type?: string;  // "D", "I", "S", "C"
        disc_confidence?: number;  // 0-100
        main_motivation?: string;  // "Security", "Status", "Gain"
        communication_style?: string;
        emotional_state?: string;
    };
    sales_metrics?: {
        purchase_probability?: number;  // 0-100
        sales_temperature?: string;  // "Cold", "Warm", "Hot"
        objections?: string[];
        buying_signals?: string[];
        pain_points?: string[];
    };
    next_move?: {
        strategic_advice?: string;
        recommended_tactic?: string;  // "SPIN", "Value", "Demo", "Close"
        key_phrase?: string;
    };
    journey_stage?: {
        current_stage?: string;  // "DISCOVERY", "QUALIFICATION", etc.
        confidence?: number;  // 0-100
        reasoning?: string;
    };

    // Legacy format (from main.py initialization)
    m1_dna?: any;
    m2_indicators?: any;
    m3_psychometrics?: any;
    m4_motivation?: any;
    m5_predictions?: any;
    m6_playbook?: any;
    m7_decision?: any;
    journeyStageAnalysis?: any;
    isAnalyzing?: boolean;
    lastUpdated?: number;
}

/**
 * Main mapper function: transforms backend analysis to frontend format
 */
export function mapBackendToFrontend(backendData: BackendAnalysisData): Partial<AnalysisState> {
    console.log('[Mapper] 🔄 Starting transformation...', backendData);

    // Check if this is the NEW backend format (from analysis_engine.py)
    const isNewFormat = backendData.psychometrics || backendData.sales_metrics || backendData.summary;

    // Check if this is the OLD/legacy format (from main.py initialization)
    const isLegacyFormat = backendData.m1_dna || backendData.m2_indicators;

    if (isLegacyFormat && !isNewFormat) {
        console.log('[Mapper] ✅ Legacy format detected - passing through');
        return backendData as Partial<AnalysisState>;
    }

    if (!isNewFormat) {
        console.log('[Mapper] ⚠️ Unknown format - returning empty');
        return {};
    }

    console.log('[Mapper] 🆕 New backend format detected - transforming');

    // Transform new format to legacy format
    const mapped: Partial<AnalysisState> = {};

    // === M1: DNA CLIENT ===
    if (backendData.summary || backendData.psychometrics) {
        const discType = backendData.psychometrics?.disc_type || "C";
        const communicationStyle = mapDISCTypeToStyle(discType);

        mapped.m1_dna = {
            summary: backendData.summary || "Analysis in progress...",
            mainMotivation: backendData.psychometrics?.main_motivation || "Unknown",
            communicationStyle: communicationStyle
        };
        console.log('[Mapper] ✓ M1 DNA mapped:', mapped.m1_dna);
    }

    // === M2: TACTICAL INDICATORS ===
    if (backendData.sales_metrics) {
        const purchaseProb = backendData.sales_metrics.purchase_probability || 0;
        const salesTemp = backendData.sales_metrics.sales_temperature || "Warm";
        const objCount = backendData.sales_metrics.objections?.length || 0;

        mapped.m2_indicators = {
            purchaseTemperature: purchaseProb,
            churnRisk: salesTemp === "Cold" ? "High" : salesTemp === "Warm" ? "Medium" : "Low",
            funDriveRisk: objCount > 2 ? "High" : objCount > 0 ? "Medium" : "Low"
        };
        console.log('[Mapper] ✓ M2 Indicators mapped:', mapped.m2_indicators);
    }

    // === M3: PSYCHOMETRICS ===
    if (backendData.psychometrics) {
        const discType = backendData.psychometrics.disc_type || "C";
        const discScores = mapDISCTypeToDISCScores(discType);

        mapped.m3_psychometrics = {
            disc: discScores,
            bigFive: generateBigFiveFromDISC(discType),
            schwartz: {
                opennessToChange: 50,
                selfEnhancement: 50,
                conservation: 50,
                selfTranscendence: 50
            }
        };
        console.log('[Mapper] ✓ M3 Psychometrics mapped:', mapped.m3_psychometrics);
    }

    // === M4: DEEP MOTIVATION ===
    if (backendData.sales_metrics) {
        mapped.m4_motivation = {
            keyInsights: backendData.sales_metrics.pain_points || [],
            teslaHooks: backendData.sales_metrics.buying_signals || []
        };
        console.log('[Mapper] ✓ M4 Motivation mapped');
    }

    // === M5: PREDICTIONS (optional - use defaults) ===
    mapped.m5_predictions = {
        scenarios: [],
        estimatedTimeline: "Unknown"
    };

    // === M6: PLAYBOOK ===
    if (backendData.next_move || backendData.sales_metrics) {
        const tactics: string[] = [];
        const ssr: any[] = [];

        if (backendData.next_move?.strategic_advice) {
            tactics.push(backendData.next_move.strategic_advice);
        }
        if (backendData.next_move?.key_phrase) {
            tactics.push(`Użyj frazy: "${backendData.next_move.key_phrase}"`);
        }

        // Build SSR from available data
        if (backendData.sales_metrics?.objections) {
            backendData.sales_metrics.objections.forEach((obj, idx) => {
                ssr.push({
                    fact: obj,
                    implication: backendData.psychometrics?.emotional_state || "Wymaga uwagi",
                    solution: backendData.next_move?.strategic_advice || "Addressuj tę obiekcję",
                    action: backendData.next_move?.key_phrase || "Kontynuuj dialog"
                });
            });
        }

        mapped.m6_playbook = {
            suggestedTactics: tactics,
            ssr: ssr
        };
        console.log('[Mapper] ✓ M6 Playbook mapped');
    }

    // === M7: DECISION VECTORS (use defaults) ===
    mapped.m7_decision = {
        decisionMaker: "Unknown",
        influencers: [],
        criticalPath: "Unknown"
    };

    // === JOURNEY STAGE ANALYSIS ===
    if (backendData.journey_stage) {
        const mappedStage = mapBackendStageToEnum(backendData.journey_stage.current_stage || "DISCOVERY");

        mapped.journeyStageAnalysis = {
            currentStage: mappedStage,
            confidence: (backendData.journey_stage.confidence || 0) / 100,  // Convert 0-100 to 0-1
            reasoning: backendData.journey_stage.reasoning || ""
        };
        console.log('[Mapper] ✓ Journey Stage mapped:', mappedStage);
    }

    // === META FIELDS ===
    mapped.isAnalyzing = backendData.isAnalyzing !== undefined ? backendData.isAnalyzing : false;
    mapped.lastUpdated = backendData.lastUpdated || Date.now();

    console.log('[Mapper] ✅ Transformation complete!');

    return mapped;
}

/**
 * Map DISC type letter to communication style
 */
function mapDISCTypeToStyle(discType: string): 'Analytical' | 'Driver' | 'Amiable' | 'Expressive' {
    const normalized = discType.toUpperCase().trim();

    const mapping: Record<string, 'Analytical' | 'Driver' | 'Amiable' | 'Expressive'> = {
        'D': 'Driver',       // Dominance
        'I': 'Expressive',   // Influence
        'S': 'Amiable',      // Steadiness
        'C': 'Analytical'    // Compliance
    };

    return mapping[normalized] || 'Analytical';
}

/**
 * Map DISC type to DISC scores (0-100 for each dimension)
 */
function mapDISCTypeToDISCScores(discType: string): {
    dominance: number;
    influence: number;
    steadiness: number;
    compliance: number;
} {
    const normalized = discType.toUpperCase().trim();

    const profiles: Record<string, any> = {
        'D': { dominance: 90, influence: 30, steadiness: 25, compliance: 40 },
        'I': { dominance: 40, influence: 90, steadiness: 50, compliance: 20 },
        'S': { dominance: 20, influence: 45, steadiness: 90, compliance: 60 },
        'C': { dominance: 25, influence: 20, steadiness: 50, compliance: 90 }
    };

    return profiles[normalized] || { dominance: 50, influence: 50, steadiness: 50, compliance: 50 };
}

/**
 * Generate Big Five personality traits from DISC type
 */
function generateBigFiveFromDISC(discType: string): {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
} {
    const normalized = discType.toUpperCase().trim();

    const profiles: Record<string, any> = {
        'D': { openness: 60, conscientiousness: 70, extraversion: 80, agreeableness: 30, neuroticism: 40 },
        'I': { openness: 80, conscientiousness: 40, extraversion: 90, agreeableness: 70, neuroticism: 30 },
        'S': { openness: 40, conscientiousness: 60, extraversion: 30, agreeableness: 90, neuroticism: 50 },
        'C': { openness: 50, conscientiousness: 90, extraversion: 20, agreeableness: 50, neuroticism: 60 }
    };

    return profiles[normalized] || { openness: 50, conscientiousness: 50, extraversion: 50, agreeableness: 50, neuroticism: 50 };
}

/**
 * Map backend journey stage to frontend enum
 */
function mapBackendStageToEnum(stage: string): JourneyStage {
    const normalized = stage.toUpperCase().trim();

    const stageMap: Record<string, JourneyStage> = {
        'DISCOVERY': JourneyStage.DISCOVERY,
        'QUALIFICATION': JourneyStage.DEMO,  // Map to DEMO as closest match
        'PRESENTATION': JourneyStage.DEMO,
        'DEMO': JourneyStage.DEMO,
        'NEGOTIATION': JourneyStage.OBJECTION_HANDLING,
        'OBJECTION_HANDLING': JourneyStage.OBJECTION_HANDLING,
        'FINANCING': JourneyStage.FINANCING,
        'CLOSING': JourneyStage.CLOSING,
        'DELIVERY': JourneyStage.DELIVERY
    };

    return stageMap[normalized] || JourneyStage.DISCOVERY;
}
