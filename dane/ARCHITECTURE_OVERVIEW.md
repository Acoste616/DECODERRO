# ARCHITECTURE_OVERVIEW.md
# System Architecture: ULTRA v3.0
# Cognitive Sales Engine for Tesla

---

## 1. System Components Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ULTRA v3.0 System                        │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Frontend   │◄───┤   Backend    │◄───┤  AI Models   │ │
│  │ React + TS   │    │   FastAPI    │    │Gemini+DeepSeek│ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         │                    │                    │         │
│  ┌──────▼──────┐    ┌───────▼────────┐  ┌────────▼─────┐ │
│  │  WebSocket  │    │   PostgreSQL   │  │   Qdrant     │ │
│  │ Real-time   │    │  Conversations │  │  RAG Vector  │ │
│  └─────────────┘    └────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Purpose | Port |
|-----------|-----------|---------|------|
| **Frontend** | React 18 + TypeScript + Vite | User interface for salespeople | 5173 |
| **Backend** | Python 3.11 + FastAPI | Business logic, AI orchestration | 8000 |
| **PostgreSQL** | PostgreSQL 14+ | Conversation history, sessions, feedback | 5432 |
| **Qdrant** | Qdrant 1.7+ | Vector database for RAG knowledge | 6333 |
| **Gemini AI** | Google Gemini 2.0 Flash | Fast Path responses (< 3s) | API |
| **DeepSeek AI** | Ollama Cloud 671B | Slow Path deep analysis (10-20s) | API |

---

## 2. Frontend Architecture

### Technology Stack
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite (fast HMR, optimized builds)
- **State Management:** Zustand ([`frontend/src/store/useStore.ts`](frontend/src/store/useStore.ts))
- **Styling:** Tailwind CSS 3
- **i18n:** Custom implementation (Polish/English)
- **WebSocket:** Native WebSocket API

### Key Views

#### View 1: Dashboard ([`frontend/src/views/Dashboard.tsx`](frontend/src/views/Dashboard.tsx))
**Purpose:** Display 7 analytical modules from Slow Path (Opus Magnum)

**Modules (M1-M7):**
1. **M1: DNA Client** - Holistic client summary, main motivation, communication style
2. **M2: Tactical Indicators** - Purchase temperature, churn risk, fun drive risk
3. **M3: Psychometric Profile** - DISC, Big Five, Schwartz values
4. **M4: Deep Motivation** - Key insights, evidence quotes, Tesla hooks
5. **M5: Predictive Paths** - Scenario predictions with probabilities
6. **M6: Strategic Playbook** - Contextual tactics and phrases
7. **M7: Decision Vectors** - Stakeholder influence analysis

**State Management:**
```typescript
interface OpusMagnumState {
  modules: {
    dna_client: DNAClientModule;
    tactical_indicators: TacticalIndicatorsModule;
    psychometric_profile: PsychometricProfileModule;
    deep_motivation: DeepMotivationModule;
    predictive_paths: PredictivePathsModule;
    strategic_playbook: StrategicPlaybookModule;
    decision_vectors: DecisionVectorsModule;
  };
  overall_confidence: number;
  suggested_stage: string;
}
```

#### View 2: Conversation ([`frontend/src/views/Conversation.tsx`](frontend/src/views/Conversation.tsx))
**Purpose:** Real-time sales conversation interface

**Key Features:**
- **Optimistic UI:** Messages appear immediately (no loading spinner)
- **Fast Path Responses:** 3 suggested responses from AI (< 3s)
- **Strategic Questions:** SPIN-methodology questions with modal UI
- **Feedback System:** Thumbs up/down on AI suggestions
- **Journey Stage Selector:** Odkrywanie/Analiza/Decyzja with AI suggestions
- **WebSocket Updates:** Real-time Opus Magnum progress (M1→M7)

**Component Structure:**
```typescript
<Conversation>
  ├── <JourneyStageSelector /> // Journey stage with AI badge
  ├── <MessageList>
  │   ├── <SellerMessage />
  │   ├── <AIResponse>
  │   │   ├── <SuggestedResponses /> // 3 "Golden Phrases"
  │   │   ├── <FeedbackButtons /> // 👍 👎
  │   │   └── <StrategicQuestions /> // SPIN questions
  │   └── ...
  ├── <InputBox /> // Seller note input
  └── <OpusMagnumPanel /> // Right sidebar with M1-M7
</Conversation>
```

#### View 3: Admin Panel ([`frontend/src/views/AdminPanel.tsx`](frontend/src/views/AdminPanel.tsx))
**Purpose:** System administration and analytics

**Tabs:**
1. **Analytics** - Session metrics, success rates, AI confidence scores
2. **Feedback** - Grouped feedback with AI clustering (Prompt 5)
3. **Golden Standards** - CRUD for best-practice responses
4. **RAG Configuration** - Knowledge base management

**Authentication:** Requires `X-Admin-Key` header

---

## 3. Backend Architecture

### Core Application: [`backend/app/main.py`](backend/app/main.py)

**Statistics:**
- **Total Lines:** 2474
- **Endpoints:** 14 REST + 1 WebSocket
- **AI Prompts:** 4 (Fast Path, Slow Path, Refinement, Feedback Grouping)
- **Database Tables:** 5 (sessions, conversation_log, slow_path_logs, feedback_logs, golden_standards)

### Key Architectural Patterns

#### 1. Dual-Path AI Processing

```python
@app.post("/api/v1/sessions/send")
async def send_message(request: SendRequest):
    # === FAST PATH (Synchronous) ===
    # Returns immediately (< 3s)
    rag_context = query_rag(request.user_input, language)
    fast_response = call_gemini_fast_path(prompt)
    
    # Return to user immediately
    
    # === SLOW PATH (Asynchronous) ===
    # Runs in background, sends via WebSocket
    asyncio.create_task(run_slow_path(session_id, language, journey_stage))
```

**Why Dual-Path?**
- **Fast Path:** Salesperson needs immediate guidance (< 3s)
- **Slow Path:** Deep analysis takes time but provides strategic insights (10-20s)
- **User Experience:** Conversation continues while analysis runs

#### 2. RAG Integration (Retrieval-Augmented Generation)

**Function:** `query_rag()` (Lines 269-341)

```python
def query_rag(query_text: str, language: str = "pl", top_k: int = 3) -> str:
    """
    Query Qdrant for relevant knowledge nuggets
    
    CRITICAL: Uses Gemini embeddings (768D) to match deployment
    Returns: Concatenated context string for AI prompts
    """
    # Step 1: Generate query embedding
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=query_text,
        task_type="retrieval_query"  # Different from indexing!
    )
    query_vector = result['embedding']  # 768D
    
    # Step 2: Search Qdrant with calibrated threshold
    results = qdrant_client.search(
        collection_name="ultra_rag_v1",
        query_vector=query_vector,
        query_filter=models.Filter(must=[
            models.FieldCondition(key="language", match=models.MatchValue(value=language))
        ]),
        limit=top_k,
        score_threshold=0.55  # ← CALIBRATED THRESHOLD
    )
    
    # Step 3: Fallback if no results (try without language filter)
    if not results:
        results = qdrant_client.search(
            collection_name="ultra_rag_v1",
            query_vector=query_vector,
            limit=top_k,
            score_threshold=0.50  # Slightly lower for fallback
        )
    
    # Step 4: Concatenate top results
    context = "\n---\n".join([hit.payload['content'] for hit in results[:3]])
    return context[:2000]  # Max 2000 chars
```

**Critical Configuration:**
- **Embedding Model:** `text-embedding-004` (768D)
- **Task Type (Query):** `retrieval_query` (optimized for search)
- **Task Type (Index):** `retrieval_document` (used during deployment)
- **Threshold:** 0.55 (calibrated via validation set)
- **Fallback Threshold:** 0.50 (when no language match)

**Why These Settings?**
- Different task_types produce slightly different embeddings
- Query: "retrieval_query" optimizes for finding similar docs
- Index: "retrieval_document" optimizes for document representation
- Threshold 0.55 balances precision (avoid irrelevant) vs recall (find all relevant)

#### 3. Session Management & Conversation History

**Smart History Retrieval:** `get_smart_session_history()` (Lines 343-391)

```python
def get_smart_session_history(db_conn, session_id: str, max_recent: int = 20) -> str:
    """
    Prevents token overflow while maintaining context
    
    Strategy:
    - Last 20 messages: Full detail
    - Earlier messages: Concise summary
    """
    logs = fetch_all_messages(session_id)
    
    if len(logs) <= max_recent:
        # All messages fit - return full history
        return format_full_history(logs)
    else:
        # Split: early + recent
        early_logs = logs[:-max_recent]
        recent_logs = logs[-max_recent:]
        
        # Summarize early conversation
        summary = f"[EARLIER: {len(early_logs)} messages, started with: {first_topic}]"
        
        # Full detail for recent
        recent_history = format_full_history(recent_logs)
        
        return f"{summary}\n\n{recent_history}"
```

**Why Smart Truncation?**
- Token limits: Gemini has ~32K token limit
- Context relevance: Recent messages more important
- Conversation continuity: Avoids cutting mid-thread

#### 4. Error Handling & Resilience

**Pattern:** Try-Except with Graceful Degradation

```python
async def run_slow_path(session_id: str, language: str, journey_stage: str):
    """
    Asynchronous Slow Path - CANNOT crash the server!
    """
    try:
        # Main processing logic
        opus_magnum = call_ollama_slow_path(prompt)
        save_to_database(opus_magnum)
        send_via_websocket(opus_magnum)
        
    except Exception as e:
        # CRITICAL: Catch-all prevents server crashes
        logger.error(f"Slow Path error: {e}")
        
        # Best-effort error handling
        try:
            save_error_to_database(e)
            send_error_via_websocket(e)
        except:
            pass  # Even error handling can fail - don't crash!
        
        # IMPORTANT: Do NOT re-raise - swallow error gracefully
        logger.info("Slow Path error handled - server remains stable")
```

**Resilience Strategies:**
1. **Database Failures:** Continue with in-memory state, log warning
2. **AI API Failures:** Return fallback response, notify user
3. **WebSocket Disconnects:** Save to DB, user can fetch later
4. **Slow Path Errors:** Never crash main server, degrade gracefully

### API Endpoints (14 REST + 1 WebSocket)

#### Core Conversation Endpoints

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/api/v1/sessions/new` | POST | Create new session | < 50ms |
| `/api/v1/sessions/{id}` | GET | Retrieve session history | < 200ms |
| `/api/v1/sessions/send` | POST | Send message (Fast Path) | < 3s |
| `/api/v1/sessions/refine` | POST | Refine bad AI response | < 3s |
| `/api/v1/sessions/retry_slowpath` | POST | Re-run Slow Path analysis | < 30s |
| `/api/v1/sessions/end` | POST | End session with status | < 50ms |
| `/ws/sessions/{id}` | WebSocket | Real-time Slow Path updates | Streaming |

#### Admin Endpoints (Require `X-Admin-Key`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/admin/feedback/grouped` | GET | AI-grouped feedback themes |
| `/api/v1/admin/golden_standards` | GET/POST | Manage best-practice responses |
| `/api/v1/admin/rag/list` | GET | List RAG nuggets |
| `/api/v1/admin/rag/add` | POST | Add new RAG nugget |
| `/api/v1/admin/rag/bulk_import` | POST | Bulk import from JSON |
| `/api/v1/admin/analytics` | GET | System analytics dashboard |
| `/health` | GET | Health check |

---

## 4. AI Orchestration Layer

### Prompt Engineering Architecture

The system uses **4 specialized prompts** for different AI tasks:

#### Prompt 1: "JARVIS" - Fast Path Sales Coach

**Function:** `build_prompt_1()` (Lines 596-748)

**Persona:** Sales Shark with Authority

**Structure:**
```
YOU ARE: JARVIS - World-class Tesla sales shark
CONTEXT: Session history, seller note, RAG knowledge base
YOUR ROLE: Generate SHORT (1-3 sentences) "Golden Phrases"

⚠️ CRITICAL RULES:
1. ANSWER THE ACTUAL QUESTION (don't answer a different question!)
2. USE SPECIFIC DATA from RAG (prices, ranges, specs)
3. BE AUTHORITATIVE (not passive or uncertain)
4. MATCH QUESTION TOPIC (price→price, range→range)

STEP 0: QUESTION ANALYSIS
- What is client asking? (price | range | comparison | features | ...)
- Read ALL 7 nuggets in Knowledge Base
- Which nugget contains info about THIS topic?
- If NO match → acknowledge lack of data

OUTPUT (JSON):
{
  "suggested_response": "GOLDEN PHRASE with specific data",
  "optional_followup": "One strategic question or null",
  "seller_questions": ["Meta-question about client behavior"],
  "client_style": "technical|spontaneous|emotional",
  "confidence_score": 0.85,
  "confidence_reason": "Found nugget about [topic] matching question"
}
```

**Key Innovation: Topic Matching**
- Previously: AI would answer ANY question it found in RAG (wrong!)
- Now: AI must first identify question topic, THEN find matching nugget
- Example:
  - ❌ Client asks "Ile kosztuje?" → AI answers about range (wrong topic!)
  - ✅ Client asks "Ile kosztuje?" → AI finds price nugget → answers about price

**Confidence Scoring:**
- **HIGH (0.8-1.0):** RAG has exact data AND topic matches
- **MEDIUM (0.5-0.79):** Partial info or ambiguous question
- **LOW (0.0-0.49):** No relevant data OR answered wrong question

#### Prompt 2: Slow Path "Opus Magnum"

**Function:** `build_prompt_4_slow_path()` (Lines 768-848)

**Purpose:** Deep psychometric analysis across 7 modules

**Structure:**
```
YOU ARE: "Opus Magnum" Oracle - Holistic sales psychologist

CORE PRINCIPLES:
- Base STRICTLY on what client ACTUALLY SAID
- DO NOT speculate about family/relationships unless mentioned
- DO NOT assume stakeholders (spouse, kids) unless mentioned
- Analyze only linguistic patterns, objections, intents

CONTEXT:
- Full session history (all messages)
- Journey stage (Odkrywanie/Analiza/Decyzja)
- Relevant knowledge from RAG

OUTPUT (JSON):
{
  "overall_confidence": 85,
  "suggested_stage": "Odkrywanie",
  "modules": {
    "dna_client": { holistic_summary, main_motivation, ... },
    "tactical_indicators": { purchase_temperature, churn_risk, ... },
    "psychometric_profile": { dominant_disc, big_five_traits, ... },
    "deep_motivation": { key_insight, evidence_quotes, ... },
    "predictive_paths": { paths: [probability, recommendations] },
    "strategic_playbook": { plays: [trigger, content, confidence] },
    "decision_vectors": { vectors: [stakeholder, influence, strategy] }
  }
}
```

**CRITICAL RULE: Evidence-Based Only**
```python
# ❌ BAD: Speculation
"Client likely has a family based on age range..."

# ✅ GOOD: Evidence-based
"Client mentioned 'dzieci' (children) in message #3"
```

#### Prompt 3: Refinement (Corrective Loop)

**Function:** `build_prompt_3()` (Lines 750-766)

**Purpose:** Fix bad AI suggestions based on seller feedback

**Structure:**
```
YOU ARE: A humble assistant who made a mistake

CONTEXT:
- Original seller note: "Klient pyta o zasięg"
- Your bad suggestion: "Tesla oferuje świetny zasięg..."
- Seller feedback: "To zbyt ogólne, daj konkretne km!"

TASK: Generate NEW refined suggestion addressing criticism

OUTPUT:
{ "refined_suggestion": "Model 3 LR: 614km WLTP..." }
```

**Use Case:** AI Dojo learning loop
- Seller clicks 👎 (thumbs down)
- Enters criticism
- AI generates refined version
- Both saved to `feedback_logs` for future training

#### Prompt 4: Feedback Grouping (AI Dojo)

**Function:** `build_prompt_5_feedback_grouping()` (Lines 850-868)

**Purpose:** Cluster seller feedback into themes

**Structure:**
```
YOU ARE: Sales Master Analyst

INPUT: ["Zbyt ogólne", "Brak ceny", "Za długie", "Brak konkretów"]

TASK: Group into logical themes

OUTPUT:
{
  "groups": [
    { "theme_name": "Brak konkretów", "count": 3, "representative_note": "..." },
    { "theme_name": "Długość", "count": 1, "representative_note": "..." }
  ]
}
```

---

## 5. Data Architecture

### PostgreSQL Schema (5 Tables)

#### Table 1: `sessions`
```sql
CREATE TABLE sessions (
    session_id VARCHAR(20) PRIMARY KEY,  -- Format: S-XXX-NNN
    created_at TIMESTAMP NOT NULL,
    journey_stage VARCHAR(20) DEFAULT 'Odkrywanie',
    status VARCHAR(20) DEFAULT 'active',  -- active | completed | lost | scheduled
    final_status_notes TEXT
);
```

#### Table 2: `conversation_log`
```sql
CREATE TABLE conversation_log (
    log_id SERIAL PRIMARY KEY,
    session_id VARCHAR(20) REFERENCES sessions(session_id),
    timestamp TIMESTAMP NOT NULL,
    role VARCHAR(50) NOT NULL,  -- Sprzedawca | FastPath | FastPath-Metadata
    content TEXT NOT NULL,
    language VARCHAR(5)
);
```

**Roles:**
- `Sprzedawca` - Seller's notes about client
- `FastPath` - AI-generated suggested responses
- `FastPath-Metadata` - JSON with confidence, questions, etc.

#### Table 3: `slow_path_logs`
```sql
CREATE TABLE slow_path_logs (
    log_id SERIAL PRIMARY KEY,
    session_id VARCHAR(20) REFERENCES sessions(session_id),
    timestamp TIMESTAMP NOT NULL,
    json_output JSONB NOT NULL,  -- Full Opus Magnum analysis (7 modules)
    status VARCHAR(20)  -- Success | Error
);
```

**JSONB Benefits:**
- Index on specific modules (e.g., `json_output->'modules'->'dna_client'`)
- Query by confidence scores
- Store full nested structure efficiently

#### Table 4: `feedback_logs`
```sql
CREATE TABLE feedback_logs (
    log_id SERIAL PRIMARY KEY,
    session_id VARCHAR(20) REFERENCES sessions(session_id),
    feedback_type VARCHAR(10),  -- up | down
    original_input TEXT,
    bad_suggestion TEXT,
    feedback_note TEXT,
    language VARCHAR(5),
    refined_suggestion TEXT,
    created_at TIMESTAMP NOT NULL
);
```

**Purpose: AI Dojo Training Data**
- Collect seller feedback on AI suggestions
- Train future models on what works/doesn't work
- Group feedback into themes (Prompt 5)

#### Table 5: `golden_standards`
```sql
CREATE TABLE golden_standards (
    gs_id SERIAL PRIMARY KEY,
    trigger_context TEXT NOT NULL,  -- Client's question/objection
    golden_response TEXT NOT NULL,  -- Best-practice response
    language VARCHAR(5),
    category VARCHAR(50),
    created_at TIMESTAMP NOT NULL
);
```

**Purpose:** Best-practice library
- Pre-approved responses for common scenarios
- Used by Fast Path for high-confidence answers
- Managed via Admin Panel

### Qdrant Vector Database

#### Collection: `ultra_rag_v1`

**Configuration:**
```python
{
    "vectors_config": {
        "size": 768,           # Gemini text-embedding-004
        "distance": "Cosine"   # Cosine similarity
    },
    "optimizers_config": {
        "indexing_threshold": 0  # Index immediately
    }
}
```

**Point Structure:**
```python
{
    "id": "5a9af675-d6f9-481b-8923-d5ec617d669a",  # UUID from JSON
    "vector": [0.123, -0.456, ...],  # 768D embedding
    "payload": {
        "title": "Typ D (Dominance) - Szybkość vs. Szczegóły",
        "content": "Klient D myśli szybko, podejmuje decyzje...",
        "keywords": "DISC, Typ D, szybkie decyzje, benefity",
        "type": "psychologia",
        "tags": ["DISC", "Typ D", "szybkie decyzje"],
        "language": "pl",
        "archetype_filter": ["dominance"],
        "id": "5a9af675-d6f9-481b-8923-d5ec617d669a"
    }
}
```

**Critical: ID Consistency**
- Point ID in Qdrant = UUID from JSON source file
- Enables validation set testing (ground truth UUIDs match!)
- Previous bug: Qdrant used auto-increment IDs (1, 2, 3...) → broke validation

**Indexing Process:**
1. Load [`nuggets_v2.1_FINAL_WITH_IDS.json`](backend/nuggets_v2.1_FINAL_WITH_IDS.json)
2. For each nugget:
   - Extract UUID from `id` field
   - Combine `title + content` for embedding
   - Generate 768D embedding (Gemini, `task_type="retrieval_document"`)
   - Create PointStruct with UUID as ID
   - Upsert to Qdrant
3. Total: 581 points

**Search Process:**
1. User query → Embedding (Gemini, `task_type="retrieval_query"`)
2. Search Qdrant (cosine similarity, threshold=0.55, language filter)
3. Return top 3 nuggets
4. Fallback: If no results, retry without language filter (threshold=0.50)

---

## 6. External Integrations

### Google Gemini API

**Models Used:**
1. **Gemini 2.0 Flash** - Fast Path generation
   - Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
   - Temperature: 0.5 (balanced creativity)
   - Max Tokens: 1024
   - Response Format: JSON

2. **text-embedding-004** - Embeddings for RAG
   - Endpoint: `models/text-embedding-004`
   - Dimensions: 768
   - Task Types:
     - `retrieval_document` (for indexing)
     - `retrieval_query` (for searching)

**Rate Limits (Free Tier):**
- 60 requests/minute
- 1500 requests/day
- Auto-retry with exponential backoff (tenacity library)

**Error Handling:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
)
def call_gemini_fast_path(prompt: str, temperature: float = 0.5, max_tokens: int = 1024):
    # Retry up to 3 times with exponential backoff
```

### Ollama Cloud (DeepSeek v3.1)

**Model:** `deepseek-v3.1:671b-cloud`

**Configuration:**
```python
client = OllamaClient(
    host="https://ollama.com",
    headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
)

response = client.chat(
    model="deepseek-v3.1:671b-cloud",
    messages=[{"role": "user", "content": prompt}],
    stream=False,
    options={"temperature": 0.3}  # Lower for analytical consistency
)
```

**Why DeepSeek 671B?**
- 671 billion parameters (largest open-source model)
- Superior reasoning for complex psychometric analysis
- Lower cost than GPT-4 Turbo
- Good JSON adherence (7 nested modules)

**Timeout:** 90 seconds (complex analysis takes time)

---

## 7. Real-Time Communication

### WebSocket Architecture

**Endpoint:** `ws://localhost:8000/ws/sessions/{session_id}`

**Connection Lifecycle:**
```python
# Client connects
websocket_connections[session_id] = websocket

# Server sends progress updates
await websocket.send_json({
    "type": "slow_path_progress",
    "module": "M1_DnaClient",
    "status": "processing"
})

# Server sends final result
await websocket.send_json({
    "type": "slow_path_complete",
    "status": "Success",
    "data": opus_magnum,  # Full 7-module analysis
    "message": "Analysis complete"
})

# Client disconnects
del websocket_connections[session_id]
```

**Why WebSocket?**
- Slow Path takes 10-20 seconds
- User sees real-time progress (M1→M2→M3...)
- Better UX than polling or SSE
- Bidirectional (future: allow user to cancel)

**Fallback Strategy:**
```python
# If WebSocket disconnected
if session_id not in websocket_connections:
    # Still process Slow Path
    # Save to database
    # User can fetch later via GET /api/v1/sessions/{id}
```

---

## 8. Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────┐
│ Windows 11 (User's Machine)                    │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐           │
│  │  Backend     │  │  Frontend    │           │
│  │  Port 8000   │  │  Port 5173   │           │
│  │  (uvicorn)   │  │  (vite)      │           │
│  └──────────────┘  └──────────────┘           │
│         │                  │                    │
│  ┌──────▼──────────────────▼────┐              │
│  │  PostgreSQL (localhost:5432) │              │
│  └──────────────────────────────┘              │
│         │                                       │
│  ┌──────▼──────────────────┐                   │
│  │ Qdrant (localhost:6333) │                   │
│  │ (Docker or standalone)  │                   │
│  └─────────────────────────┘                   │
└─────────────────────────────────────────────────┘
           │                │
           ▼                ▼
    ┌──────────┐     ┌──────────┐
    │ Gemini   │     │ Ollama   │
    │ API      │     │ Cloud    │
    └──────────┘     └──────────┘
```

### Production Deployment (Future)

**Recommended Stack:**
- **Frontend:** Vercel or Netlify (static hosting)
- **Backend:** AWS ECS or Google Cloud Run (containerized)
- **PostgreSQL:** AWS RDS or Google Cloud SQL (managed)
- **Qdrant:** Qdrant Cloud or self-hosted on AWS EC2
- **CDN:** CloudFlare for static assets

**Docker Deployment:**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: ultra_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ultra_db
    ports:
      - "5432:5432"
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - qdrant
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OLLAMA_API_KEY=${OLLAMA_API_KEY}
```

---

## 9. Security Architecture

### Authentication & Authorization

**Admin Panel:** API Key-based
```python
async def verify_admin_key(x_admin_key: str = Header(None)):
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
```

**Protected Endpoints:**
- All `/api/v1/admin/*` routes
- Require header: `X-Admin-Key: ULTRA_DOJO_KEY_8a4f9b2c_qoder_ai_2025`

**Future Enhancements:**
- OAuth 2.0 for user authentication
- JWT tokens for session management
- Role-based access control (RBAC)
- Rate limiting per user/session

### Data Privacy

**Sensitive Data:**
- Client conversation history (PostgreSQL)
- Psychometric analysis (slow_path_logs)
- Salesperson feedback (feedback_logs)

**Protection Measures:**
1. **Database:** PostgreSQL with SSL (production)
2. **API Keys:** Environment variables (never in code)
3. **CORS:** Whitelist only allowed origins
4. **Session IDs:** Non-guessable format (S-XXX-NNN)

**GDPR Compliance (Future):**
- Session deletion endpoint
- Data export functionality
- Conversation anonymization
- Consent tracking

---

## 10. Performance Optimization

### Caching Strategy

**Current State:** No caching (all queries hit database/Qdrant)

**Planned Improvements:**
1. **Redis Cache:**
   - Cache RAG query results (5-minute TTL)
   - Cache Slow Path analysis (session-scoped)
   - Cache Golden Standards (1-hour TTL)

2. **Application-Level:**
   ```python
   # In-memory cache for frequently queried nuggets
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def query_rag_cached(query_text: str, language: str):
       return query_rag(query_text, language)
   ```

### Database Optimization

**Indexes (Recommended):**
```sql
-- Speed up session lookups
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created ON sessions(created_at DESC);

-- Speed up conversation history queries
CREATE INDEX idx_conv_session_time ON conversation_log(session_id, timestamp);

-- Speed up feedback queries
CREATE INDEX idx_feedback_type ON feedback_logs(feedback_type, created_at DESC);

-- Speed up Slow Path lookups
CREATE INDEX idx_slowpath_session ON slow_path_logs(session_id, timestamp DESC);
```

**Connection Pooling:**
```python
# Future: Use connection pool instead of global connection
from psycopg2.pool import SimpleConnectionPool

db_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    database=POSTGRES_DB
)
```

### Qdrant Optimization

**Current Config:** Good for dev, needs tuning for production

**Production Settings:**
```python
client.create_collection(
    collection_name="ultra_rag_v1",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    optimizers_config=OptimizersConfigDiff(
        indexing_threshold=20000,  # Delay indexing until 20K points
        memmap_threshold=50000     # Use memory-mapped files for large datasets
    ),
    hnsw_config=HnswConfigDiff(
        m=16,                      # Links per node (higher = better recall)
        ef_construct=100           # Construction quality (higher = slower indexing, better search)
    )
)
```

---

## 11. Monitoring & Observability

### Logging Architecture

**Current:** Python `logging` module to console

**Planned:**
```python
import structlog

logger = structlog.get_logger()
logger.info("rag_query", query=query_text, results_count=len(results), latency_ms=latency)
```

**Log Aggregation:** Elasticsearch + Kibana or Datadog

### Metrics to Track

**Performance Metrics:**
- Fast Path latency (p50, p95, p99)
- Slow Path latency
- RAG query latency
- Database query latency

**Business Metrics:**
- Sessions created per day
- Messages per session (engagement)
- AI confidence scores (quality)
- Feedback ratio (thumbs up / thumbs down)

**Error Metrics:**
- API error rate (Gemini, Ollama)
- Database connection errors
- WebSocket disconnect rate
- Slow Path timeout rate

**Implementation:**
```python
from prometheus_client import Counter, Histogram

fast_path_latency = Histogram('fast_path_latency_seconds', 'Fast Path response time')
ai_confidence = Histogram('ai_confidence_score', 'AI confidence distribution')
error_counter = Counter('api_errors_total', 'Total API errors', ['service'])

@fast_path_latency.time()
def call_gemini_fast_path(prompt):
```

---

## 12. Scalability Considerations

### Current Limits
- **Concurrent Users:** ~10 (single backend instance)
- **Sessions:** Unlimited (PostgreSQL)
- **RAG Nuggets:** 581 (can scale to millions)
- **Message History:** 20 recent (smart truncation)

### Horizontal Scaling

**Stateless Backend:**
```python
# Current: Single global db_conn
db_conn = psycopg2.connect(...)

# Future: Connection pool per request
def get_db():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
```

**Load Balancing:**
```
User → Nginx Load Balancer → [Backend 1, Backend 2, Backend 3]
                           ↓
                     [PostgreSQL Read Replicas]
                     [Qdrant Cluster]
```

**WebSocket Scaling:**
- Use Redis Pub/Sub for cross-instance messaging
- Sticky sessions on load balancer
- Or: Replace WebSocket with Server-Sent Events (SSE)

---

## 13. Future Architecture Enhancements

### 1. Microservices Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Gateway   │────▶│ Fast Path   │────▶│  Gemini     │
│   Service   │     │  Service    │     │   API       │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ├─────────────▶┌─────────────┐     ┌─────────────┐
       │              │ Slow Path   │────▶│  Ollama     │
       │              │  Service    │     │   Cloud     │
       │              └─────────────┘     └─────────────┘
       │
       └─────────────▶┌─────────────┐     ┌─────────────┐
                      │   RAG       │────▶│  Qdrant     │
                      │  Service    │     │  Cluster    │
                      └─────────────┘     └─────────────┘
```

**Benefits:**
- Independent scaling (scale RAG service only)
- Technology diversity (Go for RAG service)
- Fault isolation (Slow Path failure doesn't crash Fast Path)

### 2. Event-Driven Architecture

**Message Queue:** RabbitMQ or AWS SQS

```python
# Publish event
event_bus.publish('conversation.message.received', {
    'session_id': session_id,
    'message': user_input,
    'timestamp': datetime.now()
})

# Multiple consumers
fast_path_service.subscribe('conversation.message.received')  # Fast Path
slow_path_service.subscribe('conversation.message.received')  # Slow Path
analytics_service.subscribe('conversation.message.received')  # Analytics
```

### 3. GraphQL API

**Alternative to REST:**
```graphql
query GetSession($sessionId: ID!) {
  session(id: $sessionId) {
    id
    journeyStage
    messages {
      role
      content
      timestamp
    }
    opusMagnum {
      dnaClient {
        holistic_summary
        main_motivation
      }
      tacticalIndicators {
        purchaseTemperature
        churnRisk
      }
    }
  }
}
```

**Benefits:**
- Client specifies exact data needed (no over-fetching)
- Single endpoint (no versioning issues)
- Strongly typed schema

---

**END OF ARCHITECTURE OVERVIEW**

For implementation details, see:
- [`PROJECT_STATUS_README.md`](PROJECT_STATUS_README.md) - Current status
- [`KEY_FILES_MANIFEST.md`](KEY_FILES_MANIFEST.md) - Critical files
- [`DEBUGGING_HISTORY.md`](DEBUGGING_HISTORY.md) - Bug fixes & lessons
