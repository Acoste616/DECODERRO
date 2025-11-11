"""
ULTRA v3.0 - FastAPI Main Application
======================================

Complete backend implementation for ULTRA v3.0 cognitive sales engine.
Implements all 14 REST endpoints + 1 WebSocket endpoint as specified in PEGT Module 3.

Key Features:
- Fast Path AI (Gemini 1.5-flash) for <2s response time
- Slow Path AI (DeepSeek 671B via Ollama Cloud) for deep analysis
- RAG integration with Qdrant vector database
- Real-time WebSocket updates for Slow Path progress
- Admin authentication and AI Dojo functionality
- Full i18n support (PL/EN)

This file implements Steps 4 & 6 of PEGT.
"""

import os
import logging
import random
import string
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, cast
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Header, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.generativeai as genai
import requests
from ollama import Client as OllamaClient

from app.models import (
    ConversationLogEntry,
    OpusMagnumJSON,
    SlowPathLogEntry,
    GlobalAPIResponse,
    SendResponseData,
    FeedbackGroupingResponse,
    FeedbackRequest,
    RAGListResponse,
    RAGNugget,
    NuggetPayload,
    STAGE_TO_EN,
    STAGE_TO_PL,
)

# =============================================================================
# Configuration and Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables (with defaults for development)
POSTGRES_USER = os.getenv("POSTGRES_USER", "ultra_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ultra_db")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_CLOUD_URL = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "ULTRA_DOJO_KEY_8a4f9b2c_qoder_ai_2025")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176").split(",")

# AI Model Configuration (PEGT Module 11)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
QDRANT_COLLECTION_NAME = "ultra_rag_v1"
GEMINI_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_NAME", "deepseek-v3.1:671b-cloud")

# Timeouts (PEGT Module 11.2)
FAST_PATH_TIMEOUT = 10  # seconds
SLOW_PATH_TIMEOUT = 90  # seconds (increased for Ollama Cloud deep analysis)

# Global clients (initialized in lifespan)
db_conn: Optional[psycopg2.extensions.connection] = None
qdrant_client: Optional[QdrantClient] = None
embedding_model: Optional[SentenceTransformer] = None
websocket_connections: Dict[str, WebSocket] = {}

# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global db_conn, qdrant_client, embedding_model
    
    logger.info("🚀 Starting ULTRA v3.0 Backend...")
    
    # Initialize Gemini
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)  # pyright: ignore[reportPrivateImportUsage]
        logger.info("✓ Gemini API configured")
    else:
        logger.warning("⚠ GEMINI_API_KEY not set")
    
    # Initialize PostgreSQL
    try:
        db_conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB
        )
        logger.info("✓ PostgreSQL connected")
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection failed: {e}")
    
    # Initialize Qdrant
    try:
        if QDRANT_HOST.startswith('http'):
            qdrant_client = QdrantClient(url=QDRANT_HOST)
        else:
            qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        logger.info("✓ Qdrant connected")
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
    
    # Load embedding model
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"✓ Embedding model loaded: {EMBEDDING_MODEL_NAME}")
    except Exception as e:
        logger.error(f"✗ Embedding model load failed: {e}")
    
    logger.info("🎯 ULTRA v3.0 Backend ready!")
    
    yield
    
    # Cleanup
    if db_conn:
        db_conn.close()
        logger.info("✓ PostgreSQL disconnected")
    
    logger.info("👋 ULTRA v3.0 Backend shutdown complete")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="ULTRA v3.0 API",
    description="Cognitive Sales Engine for Tesla",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Utility Functions
# =============================================================================

def generate_session_id() -> str:
    """
    Generate unique session ID (PEGT Module 2.2)
    Format: S-XXX-NNN (e.g., S-PYR-334)
    """
    prefix = "S"
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{letters}-{numbers}"

def normalize_language(language: Optional[str]) -> str:
    """
    Normalize language parameter to lowercase (PEGT Module 3, T9)
    """
    if not language:
        return "pl"
    return language.lower()

def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format and existence
    Rejects TEMP-* IDs for most endpoints (K8)
    """
    if session_id.startswith("TEMP-"):
        return False
    
    # If no database connection, accept all non-TEMP IDs (demo mode)
    if db_conn is None:
        return True
    
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT 1 FROM sessions WHERE session_id = %s", (session_id,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return False

async def verify_admin_key(x_admin_key: str = Header(None)):
    """
    Verify admin API key from header (PEGT Module 5)
    """
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing X-Admin-Key")
    return True

# =============================================================================
# RAG Functions (PEGT Module 11.1)
# =============================================================================

def query_rag(query_text: str, language: str = "pl", top_k: int = 3) -> str:
    """
    Query Qdrant for relevant knowledge nuggets
    Returns concatenated context string for AI prompts
    """
    try:
        # Check if embedding model is loaded
        if embedding_model is None:
            logger.error("Embedding model not loaded")
            return "No specific product knowledge available. Use general sales principles."
        
        # Check if Qdrant client is available
        if qdrant_client is None:
            logger.error("Qdrant client not initialized")
            return "No specific product knowledge available. Use general sales principles."
        
        # Generate query embedding
        embedding_result = embedding_model.encode(query_text)
        # Convert to list of floats - handle both numpy arrays and tensors
        query_vector: List[float] = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else list(embedding_result)  # type: ignore[union-attr]
        
        # Search with language filter
        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="language",
                        match=models.MatchValue(value=language)
                    )
                ]
            ),
            limit=top_k,
            score_threshold=0.75  # PEGT Module 11.1
        )
        
        if not results:
            # (T12) Fallback when no results
            return "No specific product knowledge available. Use general sales principles."
        
        # Concatenate top results (PEGT Module 11.1)
        context = "\n---\n".join([hit.payload['content'] for hit in results[:3]])
        return context[:2000]  # Max 2000 chars (W21)
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return "No specific product knowledge available. Use general sales principles."

# =============================================================================
# AI Functions (PEGT Module 4, 7, 11)
# =============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
)
def call_gemini_fast_path(prompt: str, temperature: float = 0.5, max_tokens: int = 1024) -> Dict[str, Any]:
    """
    Call Google Gemini for Fast Path responses (Prompts 1, 2, 3, 5)
    Implements retry logic (PEGT Module 11.4)
    Uses REST API instead of SDK for better compatibility
    """
    try:
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured")
            raise ValueError("GEMINI_API_KEY not configured in environment")
        
        logger.info(f"🚀 Calling Gemini API...")
        logger.info(f"📦 Model: {GEMINI_MODEL}")
        
        # Use REST API for better model compatibility
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"
            }
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=FAST_PATH_TIMEOUT
        )
        
        logger.info(f"📡 Gemini response status: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()
        
        # Extract text from response
        text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
        
        if not text:
            logger.error(f"❌ Empty response from Gemini")
            logger.error(f"Full response: {result}")
            raise ValueError("Empty response from Gemini")
        
        logger.info(f"📝 Gemini response length: {len(text)} chars")
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        logger.info(f"🔍 Parsing Gemini JSON...")
        
        parsed = json.loads(text)
        logger.info(f"✅ Gemini JSON parsed successfully")
        
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Gemini JSON parse error: {e}")
        logger.error(f"📄 Text: {text[:500] if 'text' in locals() else 'N/A'}")
        raise
    except Exception as e:
        logger.error(f"❌ Gemini Fast Path error: {type(e).__name__}: {e}")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    retry=retry_if_exception_type((Exception,))
)
def call_ollama_slow_path(prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> Dict[str, Any]:
    """
    Call Ollama Cloud for Slow Path deep analysis (Prompt 4.4)
    Uses official Ollama Python client library
    Reference: BIGD12.md documentation
    """
    try:
        if not OLLAMA_API_KEY:
            logger.error("❌ OLLAMA_API_KEY not configured")
            raise ValueError("OLLAMA_API_KEY not configured in environment")
        
        logger.info(f"🤖 Initializing Ollama Cloud client...")
        logger.info(f"📦 Model: {OLLAMA_MODEL}")
        logger.info(f"🔗 Host: {OLLAMA_CLOUD_URL}")
        
        # Create Ollama client with proper authentication
        # According to BIGD12.md documentation
        client = OllamaClient(
            host=OLLAMA_CLOUD_URL,
            headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
        )
        
        # Prepare messages in chat format
        messages = [
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        logger.info(f"📡 Calling Ollama Cloud chat endpoint...")
        logger.info(f"💬 Prompt length: {len(prompt)} chars")
        
        # Call chat endpoint (non-streaming for JSON response)
        # This is the correct way according to BIGD12.md
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            stream=False,
            options={
                'temperature': temperature
            }
        )
        
        logger.info(f"✓ Ollama response received")
        logger.debug(f"📄 Response keys: {response.keys()}")
        
        # Extract content from response
        # Response structure: {'message': {'role': 'assistant', 'content': '...'}, ...}
        if 'message' not in response:
            logger.error(f"❌ No 'message' in response. Keys: {response.keys()}")
            raise ValueError(f"Invalid Ollama response structure: {response.keys()}")
        
        content = response['message'].get('content', '').strip()
        
        if not content:
            logger.error(f"❌ Empty content in response")
            raise ValueError("Empty response from Ollama Cloud")
        
        logger.info(f"📝 Content length: {len(content)} chars")
        
        # Strip markdown code blocks if present
        text = content
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        logger.info(f"🔍 Parsing JSON response...")
        
        try:
            parsed = json.loads(text)
            logger.info(f"✅ JSON parsed successfully")
            
            # Validate structure
            if 'modules' not in parsed:
                logger.warning(f"⚠️ 'modules' key missing in parsed JSON")
            if 'overall_confidence' not in parsed:
                logger.warning(f"⚠️ 'overall_confidence' key missing in parsed JSON")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            logger.error(f"📄 First 500 chars of text: {text[:500]}")
            raise ValueError(f"Invalid JSON from Ollama: {e}")
        
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"❌ Ollama Slow Path error [{error_type}]: {e}")
        
        # Re-raise with more context
        if "unauthorized" in str(e).lower() or "401" in str(e):
            raise HTTPException(
                status_code=401,
                detail="Invalid Ollama API Key - check OLLAMA_API_KEY in .env"
            )
        elif "timeout" in str(e).lower():
            raise HTTPException(
                status_code=504,
                detail=f"Ollama Cloud timeout after {SLOW_PATH_TIMEOUT}s"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ollama Cloud error: {error_type}: {str(e)}"
            )

def build_prompt_1(language: str, session_history: str, last_seller_input: str, relevant_context: str) -> str:
    """
    Prompt 1: Fast Path - Suggested Response with RAG (SUPER-BLUEPRINT Section 4.1)
    ENHANCED: Now includes full session history for contextual responses
    """
    return f"""You are a world-class Tesla sales ambassador. Your task is to generate one concise "Suggested Response" based on the seller's last note and the overall session history. Analyze the full conversation context to provide empathetic, contextually-aware suggestions. Use the provided "Relevant Facts" to support your response naturally. Respond ONLY in JSON format. Respond in the language defined by the 'language' tag.

Context:
- Language: {language} (e.g., 'pl' or 'en')
- Session History: {session_history}
- Last Seller Note: {last_seller_input}
- Relevant Fact (from RAG): {relevant_context}

Instructions:
- Review the FULL session history to understand the client's journey, concerns, and evolution
- Consider previous objections, questions, and seller's approach
- Generate a response that builds on the conversation context, not just the last note
- Be empathetic and reference earlier discussion points when relevant
- Weave in the RAG fact naturally and contextually

Respond ONLY in this JSON format:
{{ "suggested_response": "string (Your generated response in the correct language)" }}
"""

def build_prompt_2(language: str, session_history: str, last_seller_input: str) -> str:
    """
    Prompt 2: Fast Path - SPIN Questions (SUPER-BLUEPRINT Section 4.2)
    ENHANCED: Now includes full session history for contextual questions
    """
    return f"""You are a SPIN methodology sales analyst. Your task is to generate 3 open-ended follow-up questions based on the last note and the provided session history. Analyze the full conversation to identify gaps in understanding and areas requiring deeper exploration. The questions should aim to uncover "Problems" (P) and "Implications" (I) that haven't been addressed yet. Respond ONLY in JSON format. Respond in the language defined by the 'language' tag.

Context:
- Language: {language}
- Session History: {session_history}
- Last Seller Note: {last_seller_input}

Instructions:
- Review the FULL session history to understand what has already been discussed
- Identify uncovered areas, unresolved objections, or emerging concerns
- Generate questions that build on the conversation flow, not repeat topics
- Focus on Problems (P) and Implications (I) in SPIN methodology
- Ensure questions are contextually relevant to the client's journey stage

Respond ONLY in this JSON format:
{{ "suggested_questions": ["string (Question 1)", "string (Question 2)", "string (Question 3)"] }}
"""

def build_prompt_3(language: str, original_input: str, bad_suggestion: str, feedback_note: str) -> str:
    """
    Prompt 3: Fast Path - Refinement/Correction (SUPER-BLUEPRINT Section 4.3)
    """
    return f"""You are a Sales Assistant who just made a mistake. Your task is to IMMEDIATELY correct your suggestion based on the seller's feedback. Be humble and precise. Respond ONLY in JSON format. Respond in the language defined by the 'language' tag.

Context:
- Language: {language}
- Original Seller Note: {original_input}
- Your Bad Suggestion: {bad_suggestion}
- Seller Feedback (Criticism): {feedback_note}

Task: Generate a new, refined "Suggested Response" that addresses the criticism.

Respond ONLY in this JSON format:
{{ "refined_suggestion": "string (Your new, refined suggestion in the correct language)" }}
"""

def build_prompt_4_slow_path(language: str, session_history: str, journey_stage: str, nuggets_context: str) -> str:
    """
    Prompt 4.4: Slow Path - Opus Magnum Deep Analysis (SUPER-BLUEPRINT Section 4.4)
    """
    # Map journey stage to English for LLM
    stage_en = STAGE_TO_EN.get(journey_stage, journey_stage)
    
    return f"""You are the "Opus Magnum" Oracle – a holistic sales psychologist and strategist for Tesla sales. Your mission: Analyze the entire client session in ONE cohesive synthesis, then generate a complete Strategic Panel for the seller. Ensure ALL modules derive from this single, unified client understanding – no contradictions.

Core Principles:
- Base everything on linguistic patterns, objections, and intents in the history.
- Tailor to Tesla context: Emphasize TCO, innovation, safety, ecosystem.
- Incorporate Journey Stage to filter outputs.
- Output MUST be ONE complete, valid JSON object. Self-validate.

Context:
- Language: {language} (Respond in this language)
- Session History: {session_history}
- Journey Stage: {stage_en}
- Relevant Knowledge: {nuggets_context}

Output ONLY this exact JSON structure. No additional text.
{{
  "overall_confidence": number (0-100),
  "suggested_stage": "string (Odkrywanie/Analiza/Decyzja or Discovery/Analysis/Decision)",
  "modules": {{
    "dna_client": {{
      "holistic_summary": "string",
      "main_motivation": "string",
      "communication_style": "string",
      "key_levers": [{{"argument": "string", "rationale": "string"}}],
      "red_flags": ["string"],
      "confidence_score": number
    }},
    "tactical_indicators": {{
      "purchase_temperature": {{"value": number, "label": "string"}},
      "churn_risk": {{"level": "Low/Medium/High", "percentage": number, "reason": "string"}},
      "fun_drive_risk": {{"level": "Low/Medium/High", "percentage": number, "reason": "string"}},
      "confidence_score": number
    }},
    "psychometric_profile": {{
      "dominant_disc": {{"type": "string (one of: D, I, S, C)", "rationale": "string"}},
      "big_five_traits": {{
        "openness": {{"level": "High/Medium/Low", "score": number}},
        "conscientiousness": {{"level": "High/Medium/Low", "score": number}},
        "extraversion": {{"level": "High/Medium/Low", "score": number}},
        "agreeableness": {{"level": "High/Medium/Low", "score": number}},
        "neuroticism": {{"level": "High/Medium/Low", "score": number}}
      }},
      "schwartz_values": [{{"value": "string", "rationale": "string"}}],
      "confidence_score": number
    }},
    "deep_motivation": {{
      "key_insight": "string",
      "evidence_quotes": ["string"],
      "tesla_hook": "string",
      "confidence_score": number
    }},
    "predictive_paths": {{
      "paths": [{{"path": "string", "probability": number, "recommendations": ["string"]}}],
      "confidence_score": number
    }},
    "strategic_playbook": {{
      "plays": [{{"title": "string", "trigger": "string", "content": ["Seller: string"], "confidence_score": number}}],
      "confidence_score": number
    }},
    "decision_vectors": {{
      "vectors": [{{"stakeholder": "string", "influence": "string", "vector": "string", "focus": "string", "strategy": "string", "confidence_score": number}}],
      "confidence_score": number
    }}
  }}
}}

IMPORTANT: You MUST always include "suggested_stage" in your response, even if confidence is low.
"""

def build_prompt_5_feedback_grouping(language: str, feedback_notes: List[str]) -> str:
    """
    Prompt 5: Fast Path - AI Dojo Feedback Grouping (SUPER-BLUEPRINT Section 4.5)
    """
    notes_str = ", ".join([f'"{note}"' for note in feedback_notes])
    
    return f"""You are a world-class Sales Master Analyst. Your task is to analyze a raw list of feedback notes from sellers and group them into logical themes. Keep theme names short (2–3 words). Respond ONLY in JSON. Respond in the language defined by 'language'.

Context:
- Language: {language}
- Feedback Notes: [{notes_str}]

Respond ONLY in this JSON format:
{{
  "groups": [
    {{ "theme_name": "string", "count": number, "representative_note": "string" }}
  ]
}}
"""

# =============================================================================
# Request/Response Models
# =============================================================================

class NewSessionRequest(BaseModel):
    pass  # No body required

class SendRequest(BaseModel):
    session_id: str
    user_input: str = Field(..., max_length=5000)
    journey_stage: str
    language: str

class RefineRequest(BaseModel):
    session_id: str
    original_input: str
    bad_suggestion: str
    feedback_note: str = Field(..., max_length=5000)
    language: str

class RetrySlowPathRequest(BaseModel):
    session_id: str

class EndSessionRequest(BaseModel):
    session_id: str
    final_status: str

class CreateStandardRequest(BaseModel):
    trigger_context: str
    golden_response: str
    language: str
    category: str

class AddRAGRequest(BaseModel):
    title: str
    content: str
    keywords: str
    language: str

# =============================================================================
# Endpoint 1: [POST] /api/v1/sessions/new (F-1.1)
# =============================================================================

@app.post("/api/v1/sessions/new")
async def create_new_session():
    """
    Create new session with generated ID
    Returns session_id immediately for Optimistic UI
    """
    try:
        session_id = generate_session_id()
        
        # If database available, persist session
        if db_conn is not None:
            cursor = db_conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (session_id, created_at) VALUES (%s, %s)",
                (session_id, datetime.now(timezone.utc))
            )
            db_conn.commit()
            cursor.close()
        
        logger.info(f"✓ Created session: {session_id}")
        
        return GlobalAPIResponse(
            status="success",
            data={"session_id": session_id}
        )
        
    except Exception as e:
        logger.error(f"✗ Create session failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 2: [GET] /api/v1/sessions/{session_id} (F-1.2)
# =============================================================================

@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Retrieve session conversation history and latest Slow Path analysis
    Rejects TEMP-* IDs (K8)
    """
    if session_id.startswith("TEMP-"):
        raise HTTPException(
            status_code=400,
            detail="Temporary session ID not allowed"
        )
    
    # Check if database is available
    if db_conn is None:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
    
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Get conversation log
        cursor.execute(
            """
            SELECT log_id, session_id, timestamp, role, content, language
            FROM conversation_log
            WHERE session_id = %s
            ORDER BY timestamp ASC
            """,
            (session_id,)
        )
        conversation_log = cursor.fetchall()
        
        # Get latest slow path log
        cursor.execute(
            """
            SELECT log_id, session_id, timestamp, json_output, status
            FROM slow_path_logs
            WHERE session_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (session_id,)
        )
        slow_path_log = cursor.fetchone()
        
        cursor.close()
        
        if not conversation_log and not slow_path_log:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return GlobalAPIResponse(
            status="success",
            data={
                "conversation_log": conversation_log,
                "slow_path_log": slow_path_log
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Get session failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 3: [POST] /api/v1/sessions/send (F-2.2)
# =============================================================================

@app.post("/api/v1/sessions/send")
async def send_message(request: SendRequest):
    """
    Main conversation loop endpoint
    - Returns Fast Path response immediately (<2s)
    - Triggers Slow Path asynchronously
    - Handles TEMP-* ID conversion (K8)
    """
    try:
        session_id = request.session_id
        language = normalize_language(request.language)
        
        # Handle TEMP-* ID conversion
        if session_id.startswith("TEMP-"):
            # Create new permanent session
            new_session_id = generate_session_id()

            # If database available, persist session
            if db_conn is not None:
                try:
                    cursor = db_conn.cursor()
                    cursor.execute(
                        "INSERT INTO sessions (session_id, created_at) VALUES (%s, %s)",
                        (new_session_id, datetime.now(timezone.utc))
                    )
                    db_conn.commit()
                    cursor.close()
                    logger.info(f"✓ Converted {request.session_id} → {new_session_id} (saved to DB)")
                except Exception as db_err:
                    logger.warning(f"⚠️ Could not save session to database: {db_err}")
                    # Continue anyway - session ID conversion still succeeds
            else:
                logger.info(f"✓ Converted {request.session_id} → {new_session_id} (demo mode, no DB)")

            session_id = new_session_id

        # Save seller note to conversation_log (if database available)
        if db_conn is not None:
            try:
                cursor = db_conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO conversation_log (session_id, timestamp, role, content, language)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session_id, datetime.now(timezone.utc), "Sprzedawca", request.user_input, language)
                )
                db_conn.commit()
                cursor.close()
            except Exception as db_err:
                logger.warning(f"⚠️ Could not save seller note to database: {db_err}")
                # Continue anyway - Fast Path can still work
        
        # === RETRIEVE SESSION HISTORY FOR FAST PATH CONTEXT ===
        # This is critical for quality - Fast Path needs full context like Slow Path
        session_history = ""
        if db_conn is not None:
            try:
                cursor = db_conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    """
                    SELECT timestamp, role, content
                    FROM conversation_log
                    WHERE session_id = %s
                    ORDER BY timestamp ASC
                    """,
                    (session_id,)
                )
                history = cursor.fetchall()
                cursor.close()
                
                # Format history for prompts (same format as Slow Path)
                session_history = "\n".join([
                    f"[{h['timestamp']}] {h['role']}: {h['content']}"
                    for h in history
                ])
            except Exception as e:
                logger.warning(f"Could not fetch session history: {e}")
                # Fallback to just current message if history fetch fails
                session_history = f"[{datetime.now(timezone.utc)}] Sprzedawca: {request.user_input}"
        else:
            # No database - use only current message
            session_history = f"[{datetime.now(timezone.utc)}] Sprzedawca: {request.user_input}"
        
        # === FAST PATH: Prompts 1 & 2 (Parallel) WITH FULL CONTEXT ===
        
        # Query RAG for context
        rag_context = query_rag(request.user_input, language)
        
        # Build prompts WITH SESSION HISTORY
        prompt1 = build_prompt_1(language, session_history, request.user_input, rag_context)
        prompt2 = build_prompt_2(language, session_history, request.user_input)
        
        # Call Gemini for both prompts
        try:
            result1 = call_gemini_fast_path(prompt1)
            result2 = call_gemini_fast_path(prompt2)
            
            # Combine results (SUPER-BLUEPRINT Section 4.2.1, W14, K1)
            fast_path_data = {
                "session_id": session_id,  # W30: Return session_id for TEMP-* conversion
                "suggested_response": result1.get("suggested_response", ""),
                "suggested_questions": result2.get("suggested_questions", [])
            }
            
            # Save Fast Path responses to conversation_log (if database available)
            if db_conn is not None:
                try:
                    cursor = db_conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO conversation_log (session_id, timestamp, role, content, language)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (session_id, datetime.now(timezone.utc), "FastPath",
                         fast_path_data["suggested_response"], language)
                    )
                    cursor.execute(
                        """
                        INSERT INTO conversation_log (session_id, timestamp, role, content, language)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (session_id, datetime.now(timezone.utc), "FastPath-Questions",
                         json.dumps(fast_path_data["suggested_questions"]), language)
                    )
                    db_conn.commit()
                    cursor.close()
                except Exception as db_err:
                    logger.warning(f"⚠️ Could not save Fast Path responses to database: {db_err}")
                    # Continue anyway - responses are already in fast_path_data
            
        except Exception as e:
            logger.error(f"✗ Fast Path failed: {e}")

            # ENHANCED: Provide detailed error message based on exception type
            error_message = "Fast Path temporarily unavailable. Please continue your note."

            # Check if it's a rate limit error (429)
            if "429" in str(e) or "Too Many Requests" in str(e):
                error_message = "⚠️ Gemini API rate limit exceeded. Slow Path analysis will continue. Try again in a few minutes."
            # Check if it's an authentication error (401)
            elif "401" in str(e) or "Unauthorized" in str(e):
                error_message = "⚠️ Gemini API authentication failed. Please check API key configuration."
            # Check if it's a timeout
            elif "timeout" in str(e).lower():
                error_message = "⚠️ Gemini API timeout. Slow Path analysis will continue."

            fast_path_data = {
                "session_id": session_id,
                "suggested_response": error_message,
                "suggested_questions": []
            }
        
        # === SLOW PATH: Trigger asynchronously (only if database available) ===
        if db_conn is not None:
            asyncio.create_task(run_slow_path(session_id, language, request.journey_stage))
        
        return GlobalAPIResponse(
            status="success",
            data=fast_path_data
        )
        
    except Exception as e:
        logger.error(f"✗ Send message failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

async def run_slow_path(session_id: str, language: str, journey_stage: str):
    """
    Asynchronous Slow Path AI analysis
    Runs DeepSeek 671B via Ollama Cloud
    Sends results via WebSocket
    ENHANCED: Comprehensive error handling to prevent server crashes
    """
    try:
        logger.info(f"🧠 Starting Slow Path for {session_id}...")

        # CRITICAL FIX: Wait for WebSocket to connect
        # Give frontend time to establish WebSocket connection after receiving HTTP response
        await asyncio.sleep(1.0)
        logger.info(f"⏳ Waited for WebSocket connection for {session_id}")

        # Check if database is available
        if db_conn is None:
            error_msg = "PostgreSQL not available - Slow Path requires database connection"
            logger.error(f"❌ {error_msg} for {session_id}")
            raise Exception(error_msg)

        # Get full session history from PostgreSQL (SUPER-BLUEPRINT Section 2.1)
        try:
            cursor = db_conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT timestamp, role, content
                FROM conversation_log
                WHERE session_id = %s
                ORDER BY timestamp ASC
                """,
                (session_id,)
            )
            history = cursor.fetchall()
            cursor.close()
        except Exception as db_err:
            logger.error(f"❌ Database query failed for {session_id}: {db_err}")
            raise Exception(f"Failed to fetch session history: {str(db_err)}")

        # Format history for prompt
        session_history = "\n".join([
            f"[{h['timestamp']}] {h['role']}: {h['content']}"
            for h in history
        ])

        # Get latest seller note for RAG context
        latest_note = next((h['content'] for h in reversed(history) if h['role'] == "Sprzedawca"), "")
        rag_context = query_rag(latest_note, language)
        
        # Build Slow Path prompt
        prompt4 = build_prompt_4_slow_path(language, session_history, journey_stage, rag_context)
        
        logger.info(f"🤖 Calling Ollama Cloud for {session_id}...")
        
        # Call Ollama Cloud - THIS IS THE CRITICAL POINT THAT CAN FAIL
        try:
            opus_magnum = call_ollama_slow_path(prompt4)
            logger.info(f"✓ Ollama Cloud response received for {session_id}")
        except HTTPException as http_err:
            # Handle HTTP errors (401, 404, 500, etc.)
            if http_err.status_code == 401:
                error_msg = "Invalid Ollama API Key - please check OLLAMA_API_KEY in .env"
                logger.critical(f"🔑 AUTHENTICATION ERROR for {session_id}: {error_msg}")
            else:
                error_msg = f"Ollama API error ({http_err.status_code}): {http_err.detail}"
                logger.error(f"🌐 HTTP ERROR for {session_id}: {error_msg}")
            raise Exception(error_msg)
        except json.JSONDecodeError as json_err:
            error_msg = f"Invalid JSON response from Ollama: {str(json_err)}"
            logger.error(f"📄 JSON PARSE ERROR for {session_id}: {error_msg}")
            raise Exception(error_msg)
        except Exception as ollama_err:
            error_msg = f"Ollama Cloud communication failed: {str(ollama_err)}"
            logger.error(f"☁️ OLLAMA ERROR for {session_id}: {error_msg}")
            raise Exception(error_msg)
        
        # Save to slow_path_logs
        try:
            cursor = db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO slow_path_logs (session_id, timestamp, json_output, status)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, datetime.now(timezone.utc), json.dumps(opus_magnum), "Success")
            )
            db_conn.commit()
            cursor.close()
            logger.info(f"💾 Saved Slow Path results to database for {session_id}")
        except Exception as db_err:
            logger.warning(f"⚠ Could not save to database for {session_id}: {db_err}")
            # Continue anyway - WebSocket delivery is more important
        
        # Send via WebSocket if connected
        if session_id in websocket_connections:
            try:
                ws = websocket_connections[session_id]
                await ws.send_json({
                    "type": "slow_path_complete",
                    "status": "Success",
                    "data": opus_magnum,
                    "message": "Analysis complete"
                })
                logger.info(f"📡 Sent Slow Path results via WebSocket for {session_id}")
            except Exception as ws_err:
                logger.warning(f"⚠ WebSocket send failed for {session_id}: {ws_err}")
        else:
            logger.warning(f"⚠ No WebSocket connection for {session_id} - results saved to DB only")
        
        logger.info(f"✓ Slow Path complete for {session_id}")
        
    except Exception as e:
        # CRITICAL: This catch-all prevents server crashes
        logger.error(f"❌ CRITICAL SLOW PATH ERROR for {session_id}: {type(e).__name__}: {str(e)}")
        
        # Try to save error to database (best effort)
        try:
            if db_conn is not None:
                cursor = db_conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO slow_path_logs (session_id, timestamp, json_output, status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, datetime.now(timezone.utc), 
                     json.dumps({"error": str(e), "error_type": type(e).__name__}), "Error")
                )
                db_conn.commit()
                cursor.close()
                logger.info(f"💾 Saved error to database for {session_id}")
        except Exception as db_err:
            logger.error(f"⚠ Could not save error to database for {session_id}: {db_err}")
        
        # Send error via WebSocket (best effort)
        try:
            if session_id in websocket_connections:
                ws = websocket_connections[session_id]
                await ws.send_json({
                    "type": "slow_path_error",
                    "status": "Error",
                    "message": f"Slow Path analysis failed: {str(e)}",
                    "error_type": type(e).__name__
                })
                logger.info(f"📡 Sent error notification via WebSocket for {session_id}")
        except Exception as ws_err:
            logger.error(f"⚠ Could not send error via WebSocket for {session_id}: {ws_err}")
        
        # IMPORTANT: Do NOT re-raise - this would crash the async task and potentially the server
        logger.info(f"🛡️ Slow Path error handled gracefully for {session_id} - server remains stable")

# =============================================================================
# Endpoint 4: [POST] /api/v1/sessions/refine (F-2.3)
# =============================================================================

@app.post("/api/v1/sessions/refine")
async def refine_suggestion(request: RefineRequest):
    """
    Corrective loop for bad AI suggestions
    Uses Prompt 3 to generate refined response
    Saves feedback to feedback_logs for AI Dojo
    """
    try:
        language = normalize_language(request.language)
        
        # Build Prompt 3
        prompt3 = build_prompt_3(
            language,
            request.original_input,
            request.bad_suggestion,
            request.feedback_note
        )
        
        # Call Gemini
        result = call_gemini_fast_path(prompt3)
        refined = result.get("refined_suggestion", "")
        
        # Save to feedback_logs (W17, W29)
        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO feedback_logs 
            (session_id, feedback_type, original_input, bad_suggestion, 
             feedback_note, language, refined_suggestion, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (request.session_id, "down", request.original_input, 
             request.bad_suggestion, request.feedback_note, language, refined, 
             datetime.now(timezone.utc))
        )
        db_conn.commit()
        cursor.close()
        
        logger.info(f"✓ Refined suggestion for {request.session_id}")
        
        return GlobalAPIResponse(
            status="success",
            data={"refined_suggestion": refined}
        )
        
    except Exception as e:
        logger.error(f"✗ Refine failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 5: [POST] /api/v1/sessions/retry_slowpath (F-2.5, W8)
# =============================================================================

@app.post("/api/v1/sessions/retry_slowpath")
async def retry_slow_path(request: RetrySlowPathRequest):
    """
    Manual retry of Slow Path analysis
    Rejects TEMP-* IDs (K8)
    """
    if request.session_id.startswith("TEMP-"):
        raise HTTPException(
            status_code=400,
            detail="Temporary session ID not allowed"
        )
    
    try:
        # Get last journey stage from conversation_log (W9)
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT language FROM conversation_log
            WHERE session_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (request.session_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        language = row[0]
        
        # Trigger Slow Path
        asyncio.create_task(run_slow_path(request.session_id, language, "Discovery"))
        
        return GlobalAPIResponse(
            status="success",
            data={"message": "Slow path retry triggered"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Retry Slow Path failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 6: [POST] /api/v1/sessions/end (F-2.6, W26)
# =============================================================================

@app.post("/api/v1/sessions/end")
async def end_session(request: EndSessionRequest):
    """
    End session with final status
    No admin auth required (W26)
    Rejects TEMP-* IDs (K8)
    """
    if request.session_id.startswith("TEMP-"):
        raise HTTPException(
            status_code=400,
            detail="Temporary session ID not allowed"
        )
    
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            UPDATE sessions
            SET ended_at = %s, status = %s
            WHERE session_id = %s
            """,
            (datetime.now(timezone.utc), request.final_status, request.session_id)
        )
        db_conn.commit()
        cursor.close()
        
        logger.info(f"✓ Ended session {request.session_id} with status: {request.final_status}")
        
        return GlobalAPIResponse(
            status="success",
            data={"message": "Session ended"}
        )
        
    except Exception as e:
        logger.error(f"✗ End session failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 6: [POST] /api/v1/sessions/feedback
# =============================================================================

@app.post("/api/v1/sessions/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback on AI suggestions
    No admin auth required
    Stores feedback in feedback_logs table
    """
    # Check if database is available
    if db_conn is None:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
    
    try:
        # Determine feedback_type based on sentiment
        feedback_type = "up" if request.sentiment == "positive" else "down"
        
        # Get language from session
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT language FROM conversation_log WHERE session_id = %s LIMIT 1",
            (request.session_id,)
        )
        result = cursor.fetchone()
        language = result[0] if result else "pl"
        
        # Insert feedback into database
        cursor.execute(
            """
            INSERT INTO feedback_logs 
            (session_id, log_id_ref, feedback_type, original_input, bad_suggestion, 
             feedback_note, language, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (request.session_id, request.message_index, feedback_type, 
             request.context, request.context, request.user_comment, 
             language, datetime.now(timezone.utc))
        )
        db_conn.commit()
        cursor.close()
        
        logger.info(f"✓ Feedback submitted for session {request.session_id}: {feedback_type}")
        
        return GlobalAPIResponse(
            status="success",
            data={"message": "Feedback saved successfully"}
        )
        
    except Exception as e:
        logger.error(f"✗ Feedback submission failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 7: [GET] /api/v1/admin/feedback/grouped (F-3.1, W15)
# =============================================================================

@app.get("/api/v1/admin/feedback/grouped", dependencies=[Depends(verify_admin_key)])
async def get_feedback_grouped(language: str = Query("pl")):
    """
    Get AI-grouped feedback themes
    Uses Prompt 5 for intelligent grouping
    """
    try:
        language = normalize_language(language)
        
        # Get all feedback notes for language
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT feedback_note
            FROM feedback_logs
            WHERE language = %s AND feedback_type = 'down'
            ORDER BY created_at DESC
            """,
            (language,)
        )
        notes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        if not notes:
            return GlobalAPIResponse(
                status="success",
                data={"groups": []}
            )
        
        # Build Prompt 5
        prompt5 = build_prompt_5_feedback_grouping(language, notes)
        
        # Call Gemini
        result = call_gemini_fast_path(prompt5)
        
        return GlobalAPIResponse(
            status="success",
            data=result
        )
        
    except Exception as e:
        logger.error(f"✗ Feedback grouping failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 8: [GET] /api/v1/admin/feedback/details (F-3.1)
# =============================================================================

@app.get("/api/v1/admin/feedback/details", dependencies=[Depends(verify_admin_key)])
async def get_feedback_details(note: str = Query(...), language: str = Query("pl")):
    """
    Get detailed feedback entries for a specific theme
    """
    try:
        language = normalize_language(language)
        
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT feedback_id, original_input, bad_suggestion, feedback_note
            FROM feedback_logs
            WHERE feedback_note ILIKE %s AND language = %s
            ORDER BY created_at DESC
            """,
            (f"%{note}%", language)
        )
        details = cursor.fetchall()
        cursor.close()
        
        return GlobalAPIResponse(
            status="success",
            data={"details": details}
        )
        
    except Exception as e:
        logger.error(f"✗ Feedback details failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 9: [POST] /api/v1/admin/feedback/create_standard (F-3.1, W28)
# =============================================================================

@app.post("/api/v1/admin/feedback/create_standard", dependencies=[Depends(verify_admin_key)])
async def create_golden_standard(request: CreateStandardRequest):
    """
    Create Golden Standard from feedback
    Saves to both PostgreSQL and Qdrant (transactionally, W28)
    """
    try:
        language = normalize_language(request.language)
        
        # Normalize trigger_context (T5)
        trigger_context = ' '.join(request.trigger_context.split())
        
        # Start transaction
        cursor = db_conn.cursor()
        
        try:
            # Insert into PostgreSQL
            cursor.execute(
                """
                INSERT INTO golden_standards 
                (category, trigger_context, golden_response, language, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (trigger_context, language) DO NOTHING
                """,
                (request.category, trigger_context, request.golden_response, 
                 language, datetime.now(timezone.utc))
            )
            
            # Check if embedding model is loaded
            if embedding_model is None:
                raise ValueError("Embedding model not loaded")
            
            # Generate embedding and insert into Qdrant
            embedding_result = embedding_model.encode(request.golden_response)
            # Convert to list of floats - handle both numpy arrays and tensors
            vector: List[float] = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else list(embedding_result)  # type: ignore[union-attr]
            
            point_id = f"GS-{int(datetime.now(timezone.utc).timestamp())}"
            
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "title": f"Golden Standard: {request.category}",
                            "content": request.golden_response,
                            "keywords": request.category.lower(),
                            "language": language,
                            "type": "golden_standard",
                            "tags": ["golden_standard", request.category],
                            "trigger_context": trigger_context
                        }
                    )
                ],
                wait=True
            )
            
            # Commit PostgreSQL transaction
            db_conn.commit()
            cursor.close()
            
            logger.info(f"✓ Created Golden Standard: {request.category}")
            
            return GlobalAPIResponse(
                status="success",
                data={"message": "Golden standard created"}
            )
            
        except Exception as e:
            # Rollback on error (W28)
            db_conn.rollback()
            cursor.close()
            raise e
            
    except Exception as e:
        logger.error(f"✗ Create Golden Standard failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 10: [GET] /api/v1/admin/rag/list (F-3.2, W12)
# =============================================================================

@app.get("/api/v1/admin/rag/list", dependencies=[Depends(verify_admin_key)])
async def list_rag_nuggets(language: str = Query("pl")):
    """
    List all RAG nuggets for a language
    """
    try:
        language = normalize_language(language)
        
        # Scroll through Qdrant collection
        points, _ = qdrant_client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="language",
                        match=models.MatchValue(value=language)
                    )
                ]
            ),
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        
        nuggets = [
            {
                "id": str(point.id),
                "payload": point.payload
            }
            for point in points
        ]
        
        return GlobalAPIResponse(
            status="success",
            data={"nuggets": nuggets}
        )
        
    except Exception as e:
        logger.error(f"✗ List RAG failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 11: [POST] /api/v1/admin/rag/add (F-3.2)
# =============================================================================

@app.post("/api/v1/admin/rag/add", dependencies=[Depends(verify_admin_key)])
async def add_rag_nugget(request: AddRAGRequest):
    """
    Add new RAG nugget to Qdrant
    """
    try:
        language = normalize_language(request.language)
        
        # Check if embedding model is loaded
        if embedding_model is None:
            raise ValueError("Embedding model not loaded")
        
        # Generate embedding
        embedding_result = embedding_model.encode(request.content)
        # Convert to list of floats - handle both numpy arrays and tensors
        vector: List[float] = embedding_result.tolist() if hasattr(embedding_result, 'tolist') else list(embedding_result)  # type: ignore[union-attr]
        
        # Generate unique ID
        point_id = f"CUSTOM-{int(datetime.now(timezone.utc).timestamp())}"
        
        # Insert into Qdrant
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "title": request.title,
                        "content": request.content,
                        "keywords": request.keywords,  # (W24) CSV string
                        "language": language,
                        "type": "custom",
                        "tags": request.keywords.split(",")
                    }
                )
            ],
            wait=True
        )
        
        logger.info(f"✓ Added RAG nugget: {request.title}")
        
        return GlobalAPIResponse(
            status="success",
            data={"message": "Nugget added"}
        )
        
    except Exception as e:
        logger.error(f"✗ Add RAG failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 12: [DELETE] /api/v1/admin/rag/delete/{nugget_id} (F-3.2, T11)
# =============================================================================

@app.delete("/api/v1/admin/rag/delete/{nugget_id}", dependencies=[Depends(verify_admin_key)])
async def delete_rag_nugget(nugget_id: str):
    """
    Delete RAG nugget from Qdrant only
    Does not touch golden_standards table (T11)
    """
    try:
        qdrant_client.delete(
            collection_name=QDRANT_COLLECTION_NAME,
            points_selector=models.PointIdsList(
                points=[nugget_id]
            )
        )
        
        logger.info(f"✓ Deleted RAG nugget: {nugget_id}")
        
        return GlobalAPIResponse(
            status="success",
            data={"message": "Nugget deleted"}
        )
        
    except Exception as e:
        logger.error(f"✗ Delete RAG failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 13: [GET] /api/v1/admin/analytics/v1_dashboard (F-3.3, W18, K13)
# =============================================================================

@app.get("/api/v1/admin/analytics/v1_dashboard", dependencies=[Depends(verify_admin_key)])
async def get_analytics_dashboard(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    language: Optional[str] = Query(None)
):
    """
    Analytics dashboard with 3 charts
    Requires complex JSONB queries (K13)
    """
    try:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        # Build date filter
        date_filter = ""
        params = []
        if date_from and date_to:
            date_filter = "AND slow_path_logs.timestamp BETWEEN %s AND %s"
            params = [date_from, date_to]
        
        # Chart 1: Playbook Effectiveness (K13)
        cursor.execute(f"""
            SELECT 
                jsonb_array_elements(json_output->'modules'->'strategic_playbook'->'plays')->>'title' as playbook_title,
                COUNT(*) as usage_count
            FROM slow_path_logs
            WHERE status = 'Success' {date_filter}
            GROUP BY playbook_title
            ORDER BY usage_count DESC
            LIMIT 10
        """, params)
        chart1_data = cursor.fetchall()
        
        # Chart 2: DISC Correlation (K13)
        cursor.execute(f"""
            SELECT 
                json_output->'modules'->'psychometric_profile'->'dominant_disc'->>'type' as disc_type,
                sessions.status,
                COUNT(*) as count
            FROM slow_path_logs
            JOIN sessions ON slow_path_logs.session_id = sessions.session_id
            WHERE slow_path_logs.status = 'Success' 
              AND sessions.status IS NOT NULL
              {date_filter}
            GROUP BY disc_type, sessions.status
        """, params)
        chart2_data = cursor.fetchall()
        
        # Chart 3: Temperature Validation (K13)
        cursor.execute(f"""
            SELECT 
                (json_output->'modules'->'tactical_indicators'->'purchase_temperature'->>'value')::int as temperature,
                sessions.status,
                COUNT(*) as count
            FROM slow_path_logs
            JOIN sessions ON slow_path_logs.session_id = sessions.session_id
            WHERE slow_path_logs.status = 'Success'
              AND sessions.status IS NOT NULL
              {date_filter}
            GROUP BY temperature, sessions.status
            ORDER BY temperature DESC
        """, params)
        chart3_data = cursor.fetchall()
        
        cursor.close()
        
        return GlobalAPIResponse(
            status="success",
            data={
                "chart1_data": chart1_data,
                "chart2_data": chart2_data,
                "chart3_data": chart3_data
            }
        )
        
    except Exception as e:
        logger.error(f"✗ Analytics failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 14: [WebSocket] /api/v1/ws/sessions/{session_id} (F-2.4, K2, W30)
# =============================================================================

@app.websocket("/api/v1/ws/sessions/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time Slow Path updates
    (W30) Validates session_id exists before accepting
    FIXED: Gracefully handles database unavailability for demo mode
    """
    # Reject TEMP-* IDs immediately (per spec W30)
    if session_id.startswith("TEMP-"):
        logger.warning(f"🔌 WebSocket rejected: TEMP session ID {session_id} not allowed")
        await websocket.close(code=4004, reason="Temporary session ID not allowed")
        return

    # If database available, validate session exists
    if db_conn is not None:
        try:
            cursor = db_conn.cursor()
            cursor.execute("SELECT 1 FROM sessions WHERE session_id = %s", (session_id,))
            exists = cursor.fetchone() is not None
            cursor.close()

            if not exists:
                logger.warning(f"🔌 WebSocket rejected: Session {session_id} not found in database")
                await websocket.close(code=4004, reason="Session not found")
                return
        except Exception as e:
            logger.error(f"⚠️ WebSocket validation error (database): {e}")
            # In case of database error, accept connection anyway (graceful degradation)
            logger.info(f"🔌 WebSocket accepting {session_id} despite validation error (demo mode)")
    else:
        # Demo mode: accept all non-TEMP session IDs
        logger.info(f"🔌 WebSocket demo mode: accepting {session_id} without database validation")

    await websocket.accept()
    websocket_connections[session_id] = websocket

    logger.info(f"🔌 WebSocket connected: {session_id}")
    
    try:
        while True:
            # Keep connection alive, listen for client disconnect
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
        if session_id in websocket_connections:
            del websocket_connections[session_id]

# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health")
async def health_check():
    """
    Health check for Railway/Docker
    """
    return {"status": "healthy", "version": "3.0.0"}

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """
    API root endpoint
    """
    return {
        "name": "ULTRA v3.0 API",
        "version": "3.0.0",
        "description": "Cognitive Sales Engine for Tesla",
        "docs": "/docs"
    }
