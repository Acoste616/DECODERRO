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
import uuid
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
    BurningHouseScore,
    BHSCalculationRequest,
)
from app.utils.burning_house import calculate_burning_house_score, BurningHouseCalculator
from app.services.gotham import generate_strategic_context, get_leasing_stats_for_prompt

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
# Database Connection Helper
# =============================================================================

def get_fresh_db_connection():
    """
    Get a fresh PostgreSQL connection with autocommit enabled.
    This avoids 'transaction aborted' errors when using global connection.
    """
    try:
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB
        )
        # Set autocommit FIRST, before any operations
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"✗ Failed to create fresh DB connection: {e}")
        return None

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
        db_conn.autocommit = True
        logger.info("✓ PostgreSQL connected (autocommit enabled)")
    except Exception as e:
        logger.error(f"✗ PostgreSQL connection failed: {e}")
        db_conn = None

    # Initialize Qdrant
    try:
        if QDRANT_HOST.startswith('http'):
            qdrant_client = QdrantClient(url=QDRANT_HOST)
        else:
            qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        logger.info("✓ Qdrant connected")
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
        qdrant_client = None

    # Load embedding model
    try:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"✓ Embedding model loaded: {EMBEDDING_MODEL_NAME}")
    except Exception as e:
        logger.error(f"✗ Embedding model load failed: {e}")
        embedding_model = None
    
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
        logger.warning(f"Unauthorized admin access attempt")
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
            score_threshold=0.50  # Lowered to 0.50 to capture more queries (leasing/subsidies score ~0.50-0.60)
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

def get_smart_session_history(db_conn, session_id: str, max_recent: int = 20) -> str:
    """
    Get session history with smart truncation for Fast Path v2.0:
    - Last 20 messages in full detail
    - Earlier messages as concise summary
    This prevents token overflow while maintaining context
    """
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
        logs = cursor.fetchall()
        cursor.close()

        if len(logs) <= max_recent:
            # All messages fit - return full history
            return "\n".join([
                f"[{log['timestamp']}] {log['role']}: {log['content']}"
                for log in logs
            ])
        else:
            # Split: early + recent
            early_logs = logs[:-max_recent]
            recent_logs = logs[-max_recent:]

            # Summarize early conversation
            first_content = early_logs[0]['content']
            first_topic = first_content[:80] + "..." if len(first_content) > 80 else first_content
            summary = f"[WCZEŚNIEJSZA ROZMOWA: {len(early_logs)} wiadomości, rozpoczęto od: {first_topic}]"

            # Full detail for recent
            recent_history = "\n".join([
                f"[{log['timestamp']}] {log['role']}: {log['content']}"
                for log in recent_logs
            ])

            return f"{summary}\n\n{recent_history}"

    except Exception as e:
        logger.warning(f"Could not fetch smart session history: {e}")
        # Fallback to just current timestamp
        return f"[{datetime.now(timezone.utc)}] Sprzedawca: (Historia niedostępna)"

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


async def analyze_with_fallback(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    session_id: str = ""
) -> Dict[str, Any]:
    """
    Unified AI analysis function with automatic fallback.

    Strategy:
    1. Try Ollama Cloud (DeepSeek 671B) - best for deep analysis
    2. If Ollama fails/timeouts -> Fallback to Gemini 1.5 Flash
    3. Returns result with metadata about which model was used

    Args:
        prompt: The analysis prompt
        temperature: Model temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        session_id: Optional session ID for logging

    Returns:
        Dictionary with:
        - result: The parsed JSON response
        - model_used: Which model provided the response
        - fallback_used: Whether fallback was triggered
        - error: Error message if any
    """
    result = None
    model_used = None
    fallback_used = False
    error_message = None

    # Step 1: Try Ollama Cloud (Primary - Deep Analysis)
    try:
        logger.info(f"🤖 [analyze_with_fallback] Attempting Ollama Cloud for {session_id or 'unknown'}")
        result = call_ollama_slow_path(prompt, temperature=temperature, max_tokens=max_tokens)
        model_used = f"ollama_cloud_{OLLAMA_MODEL}"
        logger.info(f"✅ [analyze_with_fallback] Ollama Cloud success for {session_id or 'unknown'}")

    except HTTPException as http_err:
        error_message = f"Ollama HTTP error ({http_err.status_code}): {http_err.detail}"
        logger.warning(f"⚠️ [analyze_with_fallback] {error_message}")
        fallback_used = True

    except Exception as ollama_err:
        error_message = f"Ollama error: {type(ollama_err).__name__}: {str(ollama_err)}"
        logger.warning(f"⚠️ [analyze_with_fallback] {error_message}")
        fallback_used = True

    # Step 2: Fallback to Gemini if Ollama failed
    if fallback_used and result is None:
        try:
            logger.info(f"🔄 [analyze_with_fallback] Falling back to Gemini for {session_id or 'unknown'}")
            result = call_gemini_fast_path(prompt, temperature=temperature, max_tokens=max_tokens)
            model_used = f"gemini_{GEMINI_MODEL}"
            logger.info(f"✅ [analyze_with_fallback] Gemini fallback success for {session_id or 'unknown'}")

            # Add fallback metadata to result
            if isinstance(result, dict):
                result["_fallback_used"] = True
                result["_primary_model"] = f"ollama_cloud_{OLLAMA_MODEL}"
                result["_fallback_model"] = f"gemini_{GEMINI_MODEL}"
                result["_fallback_reason"] = error_message

        except Exception as gemini_err:
            final_error = f"Both Ollama and Gemini failed. Ollama: {error_message}. Gemini: {str(gemini_err)}"
            logger.error(f"❌ [analyze_with_fallback] {final_error}")
            raise Exception(final_error)

    return {
        "result": result,
        "model_used": model_used,
        "fallback_used": fallback_used,
        "error": error_message if fallback_used else None
    }


def build_prompt_1(language: str, session_history: str, last_seller_input: str, relevant_context: str) -> str:
    """
    Fast Path v2.0: JARVIS - AI Coach for Salesperson in Real-Time
    Returns: suggested_response, optional_followup, seller_questions, confidence, client_style
    """
    return f"""You are JARVIS - an AI sales coach helping a Tesla salesperson during LIVE client conversation.

CONTEXT:
- Language: {language}
- Full Session History: {session_history}
- Current Seller Note: {last_seller_input} (This is what the CLIENT just said/asked)
- Tesla Knowledge Base: {relevant_context}

YOUR ROLE:
You're coaching the salesperson in REAL-TIME. The seller will take your response and say it in their own words to the client.

YOUR TASK - 6 OUTPUTS:

1. SUGGESTED RESPONSE (CRITICAL - ANSWER CLIENT'S QUESTION):
   - FIRST: Answer the client's specific question using Tesla Knowledge Base
   - Use concrete facts, numbers, specifications from the knowledge base
   - Match the CLIENT'S STYLE detected from conversation:
     * Technical client → precise data, specs, comparisons
     * Spontaneous client → simple language, benefits-focused
     * Emotional client → empathetic, lifestyle-focused
   - SECOND: Add empathetic context connecting to their situation
   - Keep it concise (2-4 sentences) - seller will expand naturally

2. OPTIONAL FOLLOW-UP (0 or 1 question, NOT 3):
   - Suggest ONE strategic question IF it genuinely helps
   - Only if: uncovers budget/timeline/decision-makers/objections
   - If no strategic value → return null
   - Natural, conversational, not robotic

3. SELLER QUESTIONS (Meta-information you CAN'T deduce from text):
   - Ask the SELLER 1-2 questions about client's behavior
   - Focus on: tone of voice, body language, mood, who's present
   - These help you understand client psychology
   - Max 2 questions, or [] if not needed
   - Example: "Jak brzmi ton głosu klienta - pewny czy wahający się?"

4. CLIENT STYLE ANALYSIS:
   - Detect from conversation history: technical | spontaneous | emotional
   - This helps seller adjust their delivery

5. CONFIDENCE SCORING:
   - Score 0.0-1.0 how confident you are in your answer
   - HIGH (0.8-1.0): Knowledge Base has exact data for client's question
   - MEDIUM (0.5-0.79): Partial info or question is ambiguous
   - LOW (0.0-0.49): No relevant data, using general principles

6. CONFIDENCE REASON:
   - Explain WHY this confidence level in one sentence

CRITICAL RULES:
- Tesla Knowledge Base is your PRIMARY SOURCE for facts - use it!
- If Knowledge Base says "No specific product knowledge" → acknowledge you lack that specific info
- ANSWER FIRST, then optionally ask follow-up
- Seller will phrase your response naturally - don't worry about perfect wording
- Be helpful, specific, and strategic
- LANGUAGE REQUIREMENT: ALL outputs (suggested_response, optional_followup, seller_questions) MUST be in {language}. If language is "pl" (Polish), respond ONLY in Polish. If "en" (English), respond ONLY in English.

BAD EXAMPLE (old behavior):
Client: "Jaki zasięg ma Model 3 LR AWD?"
Bad response: "Czy planuje Pan długie trasy? Jaki zasięg byłby optymalny?"
(AI only asks questions, doesn't answer!)

GOOD EXAMPLE (new behavior):
Client: "Jaki zasięg ma Model 3 LR AWD?"
Good response: "Model 3 Long Range AWD: 614km WLTP. W praktyce przy autostradzie ~130km/h to około 450-500km. Dla Pana codziennych 200km to spokojnie wystarczy z zapasem."
(Answers with facts, connects to client's situation)

Respond ONLY in {language} using this JSON format:
{{
  "suggested_response": "Complete answer to client's question (2-4 sentences, uses Knowledge Base facts)",
  "optional_followup": "One strategic question or null",
  "seller_questions": ["Meta-question 1", "Meta-question 2"] or [],
  "client_style": "technical|spontaneous|emotional",
  "confidence_score": 0.85,
  "confidence_reason": "Knowledge Base contains exact range specifications for Model 3 LR AWD"
}}
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

def build_prompt_4_slow_path(
    language: str,
    session_history: str,
    journey_stage: str,
    nuggets_context: str,
    gotham_context: str = "",
    bhs_context: str = ""
) -> str:
    """
    Prompt 4.4: Slow Path - Opus Magnum Deep Analysis (TESLA-GOTHAM v4.0)

    ENHANCED with Gotham Intelligence:
    - Real-time market context (fuel prices, subsidies, infrastructure)
    - Regional intelligence (leasing expiry, wealth mapping)
    - Strategic angles beyond client conversation
    - Burning House Score data injection

    Args:
        bhs_context: Burning House Score data to inject (e.g., "System wykrył stratę 1400 PLN/mc")
    """
    # Map journey stage to English for LLM
    stage_en = STAGE_TO_EN.get(journey_stage, journey_stage)

    # Build BHS section if available
    bhs_section = ""
    if bhs_context:
        bhs_section = f"""
🔥 BURNING HOUSE ANALYSIS (Critical Urgency Data):
{bhs_context}
Use this data to enhance urgency arguments and TCO comparisons in your analysis.
"""

    return f"""You are the "Opus Magnum" Oracle – a holistic sales psychologist and strategist for Tesla sales. Your mission: Analyze the entire client session in ONE cohesive synthesis, then generate a complete Strategic Panel for the seller. Ensure ALL modules derive from this single, unified client understanding – no contradictions.

Core Principles:
- Base everything STRICTLY on what the client actually said in the conversation history.
- DO NOT speculate about family, relationships, or personal circumstances unless explicitly mentioned.
- DO NOT assume stakeholders (family, spouse, etc.) unless the client mentions them.
- Analyze only the linguistic patterns, objections, and intents present in the history.
- Tailor to Tesla context: Emphasize TCO, innovation, safety, ecosystem.
- Incorporate Journey Stage to filter outputs.
- **NEW (v4.0)**: Use Gotham Strategic Context to enrich analysis with market intelligence.
- Output MUST be ONE complete, valid JSON object. Self-validate.
- LANGUAGE REQUIREMENT: ALL text outputs in JSON (holistic_summary, main_motivation, key_insight, strategy, etc.) MUST be in {language}. If "pl" (Polish), use ONLY Polish. If "en" (English), use ONLY English.

CRITICAL: If the client hasn't mentioned family, children, spouse, or other stakeholders - DO NOT invent them in your analysis. Stick to facts from the conversation.

Context:
- Language: {language} (ALL OUTPUTS MUST BE IN THIS LANGUAGE)
- Session History: {session_history}
- Journey Stage: {stage_en}
- Relevant Knowledge: {nuggets_context}

{gotham_context}

{bhs_section}

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
            data={
                "session_id": session_id,
                "journey_stage": "Odkrywanie"  # Default initial stage
            }
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

        # Get current journey_stage from database
        current_journey_stage = request.journey_stage  # Default from request
        if db_conn is not None and not session_id.startswith("TEMP-"):
            try:
                cursor = db_conn.cursor()
                cursor.execute("SELECT journey_stage FROM sessions WHERE session_id = %s", (session_id,))
                row = cursor.fetchone()
                if row:
                    current_journey_stage = row[0]
                cursor.close()
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch journey_stage: {e}")

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
        
        # === RETRIEVE SMART SESSION HISTORY (Fast Path v2.0) ===
        # Uses last 20 messages + summary for earlier messages
        session_history = ""
        if db_conn is not None:
            session_history = get_smart_session_history(db_conn, session_id, max_recent=20)
        else:
            # No database - use only current message
            session_history = f"[{datetime.now(timezone.utc)}] Sprzedawca: {request.user_input}"
        
        # === FAST PATH v2.0: Single Unified Prompt (JARVIS) ===

        # Query RAG for context
        rag_context = query_rag(request.user_input, language)
        logger.info(f"📚 RAG context retrieved ({len(rag_context)} chars): {rag_context[:200]}...")

        # Build unified prompt
        prompt = build_prompt_1(language, session_history, request.user_input, rag_context)

        # Call Gemini
        try:
            result = call_gemini_fast_path(prompt)

            # Extract all fields from new JSON structure
            suggested_response = result.get("suggested_response", "")
            optional_followup = result.get("optional_followup")  # Can be null
            seller_questions = result.get("seller_questions", [])
            client_style = result.get("client_style", "spontaneous")
            confidence_score = result.get("confidence_score", 0.5)
            confidence_reason = result.get("confidence_reason", "")

            # Legacy compatibility: put optional_followup in suggested_questions
            suggested_questions = []
            if optional_followup:
                suggested_questions.append(optional_followup)

            logger.info(f"✅ Fast Path complete - confidence: {confidence_score}, style: {client_style}")

            # Prepare response data
            fast_path_data = {
                "session_id": session_id,  # W30: Return session_id for TEMP-* conversion
                "journey_stage": current_journey_stage,  # Current journey stage
                "suggested_response": suggested_response,
                "suggested_questions": suggested_questions,  # Legacy field
                "optional_followup": optional_followup,
                "seller_questions": seller_questions,
                "client_style": client_style,
                "confidence_score": confidence_score,
                "confidence_reason": confidence_reason,
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
                         suggested_response, language)
                    )
                    # Save metadata as JSON
                    metadata_json = json.dumps({
                        "optional_followup": optional_followup,
                        "seller_questions": seller_questions,
                        "client_style": client_style,
                        "confidence_score": confidence_score,
                        "confidence_reason": confidence_reason
                    })
                    cursor.execute(
                        """
                        INSERT INTO conversation_log (session_id, timestamp, role, content, language)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (session_id, datetime.now(timezone.utc), "FastPath-Metadata",
                         metadata_json, language)
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
                "journey_stage": current_journey_stage,
                "suggested_response": error_message,
                "suggested_questions": [],
                "optional_followup": None,
                "seller_questions": [],
                "client_style": "spontaneous",
                "confidence_score": 0.0,
                "confidence_reason": "Fast Path service unavailable"
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
        # Increased to 5.0s for maximum reliability
        await asyncio.sleep(5.0)
        logger.info(f"⏳ Waited 5s for WebSocket connection for {session_id}")

        # Active check if WebSocket actually connected
        import time
        max_wait = 10  # seconds
        wait_start = time.time()
        while session_id not in websocket_connections:
            if time.time() - wait_start > max_wait:
                logger.warning(f"⚠️ WebSocket never connected for {session_id} after {max_wait}s")
                break
            await asyncio.sleep(0.5)

        if session_id in websocket_connections:
            logger.info(f"✅ WebSocket connected for {session_id}")
        else:
            logger.warning(f"⚠️ Proceeding without WebSocket for {session_id} - results will be DB-only")

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

        # Generate Gotham Strategic Context (Tesla-Gotham v4.0)
        try:
            gotham_context = generate_strategic_context(
                voivodeship="śląskie",  # TODO: Extract from client location or seller config
                include_leasing_intel=True,
                include_infrastructure=True,
                include_fuel_prices=True,
                include_subsidies=True
            )
            logger.info(f"✓ Gotham context generated: {len(gotham_context)} chars")
        except Exception as gotham_err:
            logger.warning(f"⚠️ Gotham context generation failed: {gotham_err}")
            gotham_context = ""

        # Generate Burning House Score context (Tesla-Gotham v4.0)
        # This injects urgency data into the AI prompt
        bhs_context = ""
        try:
            # Calculate example BHS for B2B client with typical premium vehicle
            # In production, this would be extracted from conversation context
            calc = BurningHouseCalculator(
                fuel_cost_monthly=1200,  # Typical premium sedan fuel cost
                vehicle_age_months=42,   # Typical leasing end
                client_type="B2B",       # Assume B2B for max impact
                vehicle_value_pln=250000,  # Premium segment
                is_ice=True,
                subsidy_days_remaining=75,  # NaszEauto urgency
                monthly_distance_km=2500,
                language=language
            )
            bhs_result = calc.calculate()

            if bhs_result.score > 30:  # Only inject if there's notable urgency
                bhs_context = f"""
BURNING HOUSE SCORE: {bhs_result.score}/100 ({bhs_result.fire_level.upper()})
MIESIĘCZNY KOSZT ZWŁOKI: {bhs_result.monthly_loss:,} PLN

Kluczowe argumenty pilności:
{chr(10).join(['- ' + msg for msg in bhs_result.messages])}

UŻYJ tych danych do wzmocnienia argumentacji TCO i pilności zakupu w analizie.
"""
                logger.info(f"✓ BHS context generated: score={bhs_result.score}, loss={bhs_result.monthly_loss} PLN/month")
        except Exception as bhs_err:
            logger.warning(f"⚠️ BHS context generation failed: {bhs_err}")
            bhs_context = ""

        # Build Slow Path prompt with Gotham intelligence + BHS
        prompt4 = build_prompt_4_slow_path(language, session_history, journey_stage, rag_context, gotham_context, bhs_context)
        
        logger.info(f"🤖 Calling Ollama Cloud for {session_id}...")

        # ENHANCED (Tesla-Gotham v4.0): Retry policy with Gemini fallback
        # Primary: Ollama Cloud (DeepSeek 671B) for deep analysis
        # Fallback: Google Gemini 1.5 Pro if Ollama fails/times out
        opus_magnum = None
        primary_failed = False

        # Try Ollama Cloud first (primary deep analysis model)
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
            primary_failed = True
        except json.JSONDecodeError as json_err:
            error_msg = f"Invalid JSON response from Ollama: {str(json_err)}"
            logger.error(f"📄 JSON PARSE ERROR for {session_id}: {error_msg}")
            primary_failed = True
        except Exception as ollama_err:
            error_msg = f"Ollama Cloud communication failed: {str(ollama_err)}"
            logger.error(f"☁️ OLLAMA ERROR for {session_id}: {error_msg}")
            primary_failed = True

        # FALLBACK: Try Gemini 1.5 Pro if Ollama failed
        if primary_failed and opus_magnum is None:
            logger.warning(f"⚠️ PRIMARY FAILED - Attempting Gemini fallback for {session_id}")
            try:
                # Use Gemini with same Opus Magnum prompt
                # Note: Gemini may have different token limits, so we might need to truncate
                opus_magnum = call_gemini_fast_path(
                    prompt4,
                    temperature=0.3,  # Match Ollama's creative temperature
                    max_tokens=4096   # Gemini supports up to 8192, but 4096 is safer
                )
                logger.info(f"✅ FALLBACK SUCCESS - Gemini 1.5 Pro response received for {session_id}")

                # Add metadata to indicate fallback was used
                opus_magnum["_fallback_used"] = True
                opus_magnum["_primary_model"] = "ollama_cloud_deepseek_671b"
                opus_magnum["_fallback_model"] = "gemini_1.5_pro"
                opus_magnum["_fallback_reason"] = error_msg

            except Exception as gemini_err:
                # Both primary and fallback failed - critical error
                final_error_msg = f"CRITICAL: Both Ollama and Gemini fallback failed. Ollama: {error_msg}. Gemini: {str(gemini_err)}"
                logger.critical(f"❌ TOTAL FAILURE for {session_id}: {final_error_msg}")
                raise Exception(final_error_msg)

        # If we still don't have opus_magnum, something went very wrong
        if opus_magnum is None:
            raise Exception("Opus Magnum analysis failed - no valid response from any model")
        
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

            # Update journey_stage if AI suggested a change
            suggested_stage = opus_magnum.get("suggested_stage", "")
            if suggested_stage and suggested_stage != journey_stage:
                # Normalize stage to Polish (database standard)
                normalized_stage = STAGE_TO_PL.get(suggested_stage, suggested_stage)
                try:
                    cursor = db_conn.cursor()
                    cursor.execute(
                        "UPDATE sessions SET journey_stage = %s WHERE session_id = %s",
                        (normalized_stage, session_id)
                    )
                    db_conn.commit()
                    cursor.close()
                    logger.info(f"🔄 Updated journey_stage: {journey_stage} → {normalized_stage} for {session_id}")
                except Exception as stage_err:
                    logger.warning(f"⚠ Could not update journey_stage for {session_id}: {stage_err}")

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
# Endpoint 9.5: [GET] /api/v1/admin/golden-standards/list
# =============================================================================

@app.get("/api/v1/admin/golden-standards/list", dependencies=[Depends(verify_admin_key)])
async def list_golden_standards(language: str = Query("pl")):
    """
    List all Golden Standards from PostgreSQL
    Returns paginated list of golden standards with their metadata
    """
    conn = None
    try:
        language = normalize_language(language)

        # Get fresh connection using helper
        conn = get_fresh_db_connection()
        if not conn:
            raise Exception("Could not establish database connection")

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT
                gs_id,
                trigger_context,
                golden_response,
                tags,
                category,
                language,
                created_at
            FROM golden_standards
            WHERE language = %s
            ORDER BY created_at DESC
            """,
            (language,)
        )
        standards = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format response
        formatted_standards = []
        for std in standards:
            formatted_standards.append({
                "id": std["gs_id"],
                "trigger_context": std["trigger_context"],
                "golden_response": std["golden_response"],
                "tags": std["tags"] if std["tags"] else [],
                "category": std["category"],
                "language": std["language"],
                "created_at": std["created_at"].isoformat() if std["created_at"] else None
            })

        logger.info(f"✓ Listed {len(formatted_standards)} golden standards for language: {language}")

        return GlobalAPIResponse(
            status="success",
            data={
                "standards": formatted_standards,
                "total": len(formatted_standards)
            }
        )

    except Exception as e:
        logger.error(f"✗ List golden standards failed: {e}")
        if conn:
            conn.close()
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
                "nugget_id": str(point.id),
                "title": point.payload.get("title", ""),
                "content": point.payload.get("content", ""),
                "keywords": point.payload.get("keywords", ""),
                "language": point.payload.get("language", "pl"),
                "type": point.payload.get("type", "unknown"),
                "tags": point.payload.get("tags", [])
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
# Endpoint 12.5: [POST] /api/v1/admin/rag/bulk-import (Bulk Import RAG Nuggets)
# =============================================================================

class BulkRagImportRequest(BaseModel):
    nuggets: List[dict]
    language: str = "pl"

@app.post("/api/v1/admin/rag/bulk-import", dependencies=[Depends(verify_admin_key)])
async def bulk_import_rag_nuggets(request: BulkRagImportRequest):
    """
    Bulk import RAG nuggets from JSON array
    Expected format: [{"title": "...", "content": "...", "type": "...", ...}, ...]
    """
    try:
        language = normalize_language(request.language)

        # Validate and prepare points for Qdrant
        points_to_upsert = []
        success_count = 0
        error_count = 0
        errors = []

        for idx, nugget in enumerate(request.nuggets):
            try:
                # Validate required fields
                if "title" not in nugget or "content" not in nugget:
                    errors.append(f"Item {idx+1}: Missing title or content")
                    error_count += 1
                    continue

                # Generate embedding for content using SentenceTransformer
                content_to_embed = f"{nugget['title']} {nugget['content']}"
                if embedding_model is None:
                    raise Exception("Embedding model not available")
                embedding = embedding_model.encode(content_to_embed).tolist()

                # Create point
                point_id = str(uuid.uuid4())
                payload = {
                    "title": nugget["title"],
                    "content": nugget["content"],
                    "type": nugget.get("type", "general"),
                    "tags": nugget.get("tags", []),
                    "language": language,
                    "keywords": nugget.get("keywords", ""),
                    "archetype_filter": nugget.get("archetype_filter", []),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }

                points_to_upsert.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
                success_count += 1

            except Exception as e:
                errors.append(f"Item {idx+1}: {str(e)}")
                error_count += 1

        # Upsert all valid points to Qdrant
        if points_to_upsert:
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=points_to_upsert
            )

        logger.info(f"✓ Bulk import completed: {success_count} success, {error_count} errors")

        return GlobalAPIResponse(
            status="success" if error_count == 0 else "partial",
            data={
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10]  # Return first 10 errors
            }
        )

    except Exception as e:
        logger.error(f"✗ Bulk RAG import failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Endpoint 12.6: [POST] /api/v1/admin/golden-standards/bulk-import (Bulk Import Golden Standards)
# =============================================================================

class BulkGoldenStandardRequest(BaseModel):
    standards: List[dict]
    language: str = "pl"

@app.post("/api/v1/admin/golden-standards/bulk-import", dependencies=[Depends(verify_admin_key)])
async def bulk_import_golden_standards(request: BulkGoldenStandardRequest):
    """
    Bulk import golden standards from JSON array
    Expected format: [{"trigger_context": "...", "golden_response": "...", "tags": []}, ...]
    """
    try:
        language = normalize_language(request.language)
        cursor = db_conn.cursor()

        success_count = 0
        error_count = 0
        errors = []

        for idx, standard in enumerate(request.standards):
            try:
                # Validate required fields
                if "trigger_context" not in standard or "golden_response" not in standard:
                    errors.append(f"Item {idx+1}: Missing trigger_context or golden_response")
                    error_count += 1
                    continue

                # Insert into database
                cursor.execute(
                    """
                    INSERT INTO golden_standards
                    (trigger_context, golden_response, tags, language, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        standard["trigger_context"],
                        standard["golden_response"],
                        standard.get("tags", []),
                        language,
                        datetime.now(timezone.utc)
                    )
                )

                # Generate embedding and add to Qdrant using SentenceTransformer
                embedding_content = f"{standard['trigger_context']} {standard['golden_response']}"
                if embedding_model is None:
                    raise Exception("Embedding model not available")
                embedding = embedding_model.encode(embedding_content).tolist()

                point_id = str(uuid.uuid4())
                qdrant_client.upsert(
                    collection_name=QDRANT_COLLECTION_NAME,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "title": f"Golden Standard: {standard['trigger_context'][:50]}...",
                                "content": standard["golden_response"],
                                "type": "golden_standard",
                                "tags": standard.get("tags", []),
                                "language": language,
                                "trigger_context": standard["trigger_context"],
                                "created_at": datetime.now(timezone.utc).isoformat()
                            }
                        )
                    ]
                )

                success_count += 1

            except Exception as e:
                errors.append(f"Item {idx+1}: {str(e)}")
                error_count += 1

        # Commit all database changes
        db_conn.commit()
        cursor.close()

        logger.info(f"✓ Bulk golden standard import completed: {success_count} success, {error_count} errors")

        return GlobalAPIResponse(
            status="success" if error_count == 0 else "partial",
            data={
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10]  # Return first 10 errors
            }
        )

    except Exception as e:
        logger.error(f"✗ Bulk golden standard import failed: {e}")
        if 'cursor' in locals():
            db_conn.rollback()
            cursor.close()
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
# Endpoint 15: [POST] /api/v1/gotham/burning-house-score (Tesla-Gotham v4.0)
# =============================================================================

@app.post("/api/v1/gotham/burning-house-score")
async def calculate_bhs(request: BHSCalculationRequest):
    """
    Calculate Burning House Score for Tesla purchase urgency.

    Part of Tesla-Gotham ULTRA v4.0 - provides urgency scoring based on:
    - Fuel cost savings potential
    - NaszEauto subsidy expiration
    - Tax depreciation benefits
    - Vehicle replacement timing

    Returns:
        BurningHouseScore with overall score, fire level, monthly delay cost, and urgency message
    """
    try:
        bhs = calculate_burning_house_score(
            current_fuel_consumption_l_100km=request.current_fuel_consumption_l_100km,
            monthly_distance_km=request.monthly_distance_km,
            fuel_price_pln_l=request.fuel_price_pln_l,
            vehicle_age_months=request.vehicle_age_months,
            purchase_type=request.purchase_type,
            vehicle_price_planned=request.vehicle_price_planned,
            subsidy_deadline_days=request.subsidy_deadline_days,
            language=request.language
        )

        logger.info(f"✓ BHS calculated: score={bhs.score}, fire_level={bhs.fire_level}, delay_cost={bhs.monthly_delay_cost_pln} PLN/month")

        return GlobalAPIResponse(
            status="success",
            data=bhs.dict()
        )

    except Exception as e:
        logger.error(f"✗ BHS calculation failed: {e}")
        return GlobalAPIResponse(
            status="error",
            message=str(e)
        )

# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health")
async def health_check():
    """
    Health check for Railway/Docker
    """
    return {"status": "healthy", "version": "4.0.0"}

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
