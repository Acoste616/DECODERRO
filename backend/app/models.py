"""
ULTRA DOJO AI - Pydantic Data Models
=====================================

Central repository for all Pydantic data models used across the FastAPI backend.
Defines complete API contracts for all 14 endpoints based on 02_PEGT_FINAL.md Module 3.

This file implements Step 2 of PEGT: Schematy Danych i API (Contracts First).
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Union
from datetime import datetime


# =============================================================================
# Base Schemas
# =============================================================================

class ConversationLogEntry(BaseModel):
    """
    Conversation log entry tracking exchanges between seller and AI system.
    Used in conversation history and session retrieval.
    """
    log_id: int
    session_id: str
    timestamp: datetime
    role: Literal["Sprzedawca", "FastPath", "FastPath-Questions"]
    content: str
    language: Literal["pl", "en"]
    journey_stage: Optional[Literal["Odkrywanie", "Analiza", "Decyzja"]] = None  # (W1) journey_stage accepts null


# =============================================================================
# Opus Magnum Module Schemas (M1-M7)
# =============================================================================

class OpusMagnumModuleBase(BaseModel):
    """
    Base class for all Opus Magnum analysis modules.
    Provides shared confidence scoring mechanism.
    
    (W25) Confidence score interpretation:
    - 90-100: High confidence (Wysoka pewność)
    - 70-89: Medium confidence (Średnia pewność)
    - 0-69: Low confidence (Niska pewność)
    """
    confidence_score: int = Field(..., ge=0, le=100, description="Analysis confidence level (0-100)")


class M1DnaClient(OpusMagnumModuleBase):
    """
    Module 1: DNA Client - Holistic client profile and psychological fingerprint.
    Provides comprehensive client overview and key persuasion levers.
    """
    holistic_summary: str = Field(..., description="Comprehensive client overview")
    main_motivation: str = Field(..., description="Primary purchase driver")
    communication_style: str = Field(..., description="Preferred interaction pattern")
    key_levers: List[Dict[str, str]] = Field(
        ..., 
        description="Persuasion arguments with rationale, e.g., [{'argument': 'TCO', 'rationale': 'Klient liczy koszty'}]"
    )  # (W3) List[Dict[str, str]] maps to TypeScript Array<{ argument: string; rationale: string }>
    red_flags: List[str] = Field(..., description="Warning signals and objections")


class M2TacticalIndicators(OpusMagnumModuleBase):
    """
    Module 2: Tactical Indicators - Real-time sales opportunity metrics.
    Provides purchase temperature, churn risk, and test drive risk assessment.
    """
    purchase_temperature: Dict[str, Union[int, str]] = Field(
        ..., 
        description="Purchase readiness metric, e.g., {'value': 80, 'label': 'Gorący'}"
    )
    churn_risk: Dict[str, Union[str, int, float]] = Field(
        ..., 
        description="Customer loss risk, e.g., {'level': 'High', 'percentage': 75, 'reason': 'Wspomniał o Audi'}"
    )
    fun_drive_risk: Dict[str, Union[str, int, float]] = Field(
        ..., 
        description="Test drive abandonment risk"
    )


class M3PsychometricProfile(OpusMagnumModuleBase):
    """
    Module 3: Psychometric Profile - Deep psychological profiling.
    Uses DISC model, Big Five traits, and Schwartz values frameworks.
    """
    dominant_disc: Dict[str, str] = Field(
        ..., 
        description="Dominant DISC type, e.g., {'type': 'D', 'rationale': '...'}"
    )
    big_five_traits: Dict[str, Dict[str, Union[str, int, float]]] = Field(
        ..., 
        description="Big Five personality traits with levels and scores"
    )
    schwartz_values: List[Dict[str, str]] = Field(
        ..., 
        description="Universal human values, e.g., [{'value': 'Achievement', 'rationale': '...'}]"
    )


class M4DeepMotivation(OpusMagnumModuleBase):
    """
    Module 4: Deep Motivation - Core psychological drivers and evidence.
    Extracts key insights from conversation with supporting quotes.
    """
    key_insight: str = Field(..., description="Central motivational finding")
    evidence_quotes: List[str] = Field(..., description="Direct client quotes supporting insight")
    tesla_hook: str = Field(..., description="Tesla-specific engagement angle")


class M5PredictivePaths(OpusMagnumModuleBase):
    """
    Module 5: Predictive Paths - Forecasted customer journey trajectories.
    Predicts possible scenarios with probabilities and recommendations.
    """
    paths: List[Dict[str, Union[str, int, float, List[str]]]] = Field(
        ..., 
        description="Journey scenarios, e.g., [{'path': '...', 'probability': 60, 'recommendations': ['...']}]"
    )


class M6StrategicPlaybook(OpusMagnumModuleBase):
    """
    Module 6: Strategic Playbook - Situation-specific response templates.
    Provides pre-built conversation plays with trigger conditions.
    """
    plays: List[Dict[str, Union[str, List[str], int]]] = Field(
        ..., 
        description="Response templates, e.g., [{'title': '...', 'trigger': '...', 'content': ['Seller: ...'], 'confidence_score': 90}]"
    )


class M7DecisionVectors(OpusMagnumModuleBase):
    """
    Module 7: Decision Vectors - Stakeholder influence mapping.
    Maps decision influencers and recommended engagement strategies.
    """
    vectors: List[Dict[str, Union[str, int]]] = Field(
        ..., 
        description="Stakeholder influence vectors, e.g., [{'stakeholder': 'Żona', 'influence': 'High', ...}]"
    )


# =============================================================================
# Composite Schemas
# =============================================================================

class OpusMagnumModules(BaseModel):
    """
    Aggregate container for all seven Opus Magnum analysis modules.
    Complete psychological and strategic analysis output from Slow Path AI.
    """
    dna_client: M1DnaClient
    tactical_indicators: M2TacticalIndicators
    psychometric_profile: M3PsychometricProfile
    deep_motivation: M4DeepMotivation
    predictive_paths: M5PredictivePaths
    strategic_playbook: M6StrategicPlaybook
    decision_vectors: M7DecisionVectors


class OpusMagnumJSON(BaseModel):
    """
    Complete Slow Path AI analysis output.
    
    (K3) Language mapping: suggested_stage accepts both Polish and English values.
    Backend must implement bi-directional mapping using STAGE_TO_EN and STAGE_TO_PL.
    """
    overall_confidence: int = Field(..., ge=0, le=100, description="Aggregate analysis confidence")
    suggested_stage: Literal[
        "Odkrywanie", "Analiza", "Decyzja",  # Polish values
        "Discovery", "Analysis", "Decision"   # English values
    ] = Field(..., description="Recommended journey stage (accepts PL/EN)")
    modules: OpusMagnumModules


class SlowPathLogEntry(BaseModel):
    """
    Audit trail for asynchronous Slow Path AI analysis.
    Stores complete Opus Magnum analysis results.
    """
    log_id: int
    session_id: str
    timestamp: datetime
    json_output: OpusMagnumJSON
    status: Literal["Success", "Error"]


# =============================================================================
# Global API Response Wrapper
# =============================================================================

class GlobalAPIResponse(BaseModel):
    """
    Standardized response format across all API endpoints.
    
    Status values:
    - "success": Request completed successfully, data present
    - "fail": Client error (4xx), validation failed
    - "error": Server error (5xx), unexpected failure
    """
    status: Literal["success", "fail", "error"]
    data: Optional[dict] = None
    message: Optional[str] = None


# =============================================================================
# Endpoint-Specific Response Schemas
# =============================================================================

class SendResponseData(BaseModel):
    """
    (K7) Response schema for Fast Path AI suggestions.
    
    Returned by POST /api/v1/sessions/send (Endpoint 3, F-2.2).
    Must deliver within 2-second P95 latency (per UAT-1).
    """
    suggested_response: str = Field(..., description="AI-generated seller response text")
    suggested_questions: List[str] = Field(..., description="Follow-up question suggestions (typically 2-3)")


class FeedbackGroup(BaseModel):
    """
    Single feedback theme cluster for grouping response.
    """
    theme_name: str = Field(..., description="Cluster label (e.g., 'zbyt łagodne')")
    count: int = Field(..., description="Number of occurrences in cluster")
    representative_note: str = Field(..., description="Example feedback text from cluster")


class FeedbackGroupingResponse(BaseModel):
    """
    (K12) Thematic grouping of seller feedback.
    
    Returned by GET /api/v1/admin/feedback/grouped (Endpoint 7, F-3.1).
    Powers AI Dojo feedback analysis UI.
    """
    groups: List[FeedbackGroup] = Field(..., description="Feedback theme clusters")


class NuggetPayload(BaseModel):
    """
    (W12) RAG knowledge nugget payload schema.
    Stored in Qdrant with vector embeddings.
    """
    title: str = Field(..., description="Nugget headline")
    content: str = Field(..., description="Full nugget text content")
    keywords: str = Field(..., description="CSV keyword list (e.g., 'leasing, vat, b2b')")  # (W24)
    language: Literal["pl", "en"] = Field(..., description="Content language")
    type: Optional[str] = Field(None, description="Nugget category")
    tags: Optional[List[str]] = Field(None, description="Additional metadata tags")
    archetype_filter: Optional[List[str]] = Field(None, description="Applicable client archetypes")


class RAGNugget(BaseModel):
    """
    Complete RAG nugget with Qdrant ID and payload.
    """
    id: str = Field(..., description="Qdrant point ID for deletion operations")
    payload: NuggetPayload


class RAGListResponse(BaseModel):
    """
    (W12) Response schema for RAG knowledge nugget listing.
    
    Returned by GET /api/v1/admin/rag/list (Endpoint 10, F-3.2).
    Supports language-filtered queries.
    """
    nuggets: List[RAGNugget] = Field(..., description="All RAG entries with IDs and payloads")


class FeedbackRequest(BaseModel):
    """
    Request schema for submitting user feedback on AI suggestions.

    Used by POST /api/v1/sessions/feedback (Endpoint 6).
    """
    session_id: str = Field(..., description="Session identifier")
    message_index: int = Field(..., description="Index of message being rated")
    sentiment: Literal["positive", "negative"] = Field(..., description="Feedback type")
    user_comment: str = Field(..., description="Seller's feedback comment")
    context: str = Field(..., description="Original AI suggestion being rated")


# =============================================================================
# Tesla-Gotham ULTRA v4.0 - Burning House Score
# =============================================================================

class BurningHouseScore(BaseModel):
    """
    Burning House Score - Urgency scoring for Tesla purchase decision.

    Calculates financial urgency based on:
    - Fuel costs (current combustion vehicle)
    - NaszEauto subsidy expiration risk
    - Depreciation limits (225k/100k for business)
    - Vehicle age and replacement timing

    Used in Tesla-Gotham ULTRA v4.0 for sales prioritization.
    """
    score: int = Field(..., ge=0, le=100, description="Overall urgency score (0-100, higher = more urgent)")
    fire_level: Literal["cold", "warm", "hot", "burning"] = Field(..., description="Visual fire intensity")
    monthly_delay_cost_pln: int = Field(..., description="Estimated monthly cost of delaying purchase (PLN)")
    factors: Dict[str, Union[int, str, bool]] = Field(
        ...,
        description="Individual factor scores and details",
        example={
            "fuel_cost_monthly": 1200,
            "subsidy_expires_days": 45,
            "depreciation_risk": "high",
            "vehicle_age_months": 36,
            "has_business_benefit": True
        }
    )
    urgency_message: str = Field(..., description="Human-readable urgency explanation in client's language")


class BHSCalculationRequest(BaseModel):
    """
    Request for calculating Burning House Score.
    Used internally or via API endpoint.
    """
    current_fuel_consumption_l_100km: Optional[float] = Field(None, description="Current car fuel consumption (liters per 100km)")
    monthly_distance_km: Optional[int] = Field(None, description="Monthly driving distance in km")
    fuel_price_pln_l: Optional[float] = Field(1.50, description="Current fuel price (PLN/liter)")
    vehicle_age_months: Optional[int] = Field(None, description="Age of current vehicle in months")
    purchase_type: Optional[Literal["private", "business"]] = Field("private", description="Purchase type")
    vehicle_price_planned: Optional[int] = Field(None, description="Planned Tesla price (for depreciation calculation)")
    subsidy_deadline_days: Optional[int] = Field(None, description="Days until NaszEauto subsidy expires (if applicable)")
    language: Literal["pl", "en"] = Field("pl", description="Language for urgency message")


# =============================================================================
# Language Mapping Utilities (K3)
# =============================================================================

# Backend mapping dictionaries for bi-directional journey stage conversion
STAGE_TO_EN = {
    'Odkrywanie': 'Discovery',
    'Analiza': 'Analysis',
    'Decyzja': 'Decision'
}

STAGE_TO_PL = {
    'Discovery': 'Odkrywanie',
    'Analysis': 'Analiza',
    'Decision': 'Decyzja'
}
