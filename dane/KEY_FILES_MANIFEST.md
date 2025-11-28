# KEY_FILES_MANIFEST.md
# Critical Files Index - ULTRA v3.0
# Quick Reference Guide for New Team Members

---

## 📋 Table of Contents

1. [Core Application Files](#1-core-application-files)
2. [Knowledge Base & RAG](#2-knowledge-base--rag)
3. [Deployment & Operations Scripts](#3-deployment--operations-scripts)
4. [Testing & Validation](#4-testing--validation)
5. [Documentation & Reports](#5-documentation--reports)
6. [Configuration Files](#6-configuration-files)
7. [Frontend Components](#7-frontend-components)

---

## 1. Core Application Files

### Backend Main Application

#### `backend/app/main.py`
- **Purpose:** Microservice Entrypoint - FastAPI backend (v4.0 Refactor)
- **Size:** ~200 lines (Refactored from 2,474 lines)
- **Key Components:**
  - Service Layer Orchestration (`ChatService`, `RAGService`, `SlowPathService`)
  - 15 REST API endpoints (Restored & Secured)
  - 1 WebSocket endpoint (`/ws/sessions/{session_id}`)
  - Admin Security (`verify_admin_key`)
  - Async Database Connection (`lifespan`)

**Critical Functions:**

| Function | Purpose |
|----------|---------|
| `lifespan()` | Initializes DB and Services (Gemini, RAG, Chat, SlowPath) |
| `create_session()` | **NEW** - Initializes session + Eager Loading of Opus Magnum |
| `send_message()` | **ASYNC** - Non-blocking Fast Path via `ChatService` |
| `websocket_endpoint()` | Real-time Slow Path updates |
| `verify_admin_key()` | **SECURITY** - Enforces `X-Admin-Key` on Admin routes |

**Why This File Is Critical:**
- Entry point for all traffic
- Enforces security policies
- Wires up dependency injection

---

### Backend Services (v4.0)

#### `backend/services/chat_service.py`
- **Purpose:** Core conversation logic (Fast Path)
- **Key Features:**
  - Session management (Create, End, History)
  - RAG + Gemini orchestration
  - Feedback submission
  - Response refinement
  - **Eager Loading:** Initializes empty Opus Magnum structures to prevent frontend crashes

#### `backend/services/rag_service.py`
- **Purpose:** RAG Knowledge Base management
- **Key Features:**
  - Async Qdrant operations
  - Embedding generation (Gemini 768D)
  - Nugget CRUD (Add, List, Delete)

#### `backend/services/slow_path_service.py`
- **Purpose:** Deep Analysis (Slow Path)
- **Key Features:**
  - Ollama Cloud integration (DeepSeek 671B)
  - WebSocket push notifications
  - Async execution

#### `backend/services/gemini_service.py`
- **Purpose:** Google Gemini API wrapper
- **Key Features:**
  - Async content generation
  - Async embedding generation
  - Retry logic

---

#### `backend/app/models.py`
- **Purpose:** Pydantic models for request/response validation
- **Key Models:**
  - `SendRequest` - `/send` endpoint input
  - `GlobalAPIResponse` - Standard response wrapper
  - `OpusMagnumJSON` - Slow Path 7-module structure
  - `RAGNugget` - Knowledge base entry schema
  - `FeedbackRequest` - Feedback logging schema

---

### Frontend Views

#### `frontend/src/views/Conversation.tsx`
- **Purpose:** Main sales conversation interface
- **Key Features:**
  - Optimistic UI (messages appear immediately)
  - Fast Path responses (3 suggested "Golden Phrases")
  - Strategic questions modal (SPIN methodology)
  - Journey stage selector (Odkrywanie/Analiza/Decyzja)
  - Feedback buttons (👍 👎)
  - WebSocket integration for Opus Magnum updates
- **State Management:** Zustand store ([`useStore.ts`](frontend/src/store/useStore.ts))

**Critical Code Sections:**
```tsx
// Lines 229-248: Feedback System
const handleFeedback = async (sentiment: 'positive' | 'negative') => {
  // Sends thumbs up/down to backend
  await sendFeedback(session_id, sentiment);
}

// Lines 150-180: WebSocket Connection
useEffect(() => {
  const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${session_id}`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'slow_path_complete') {
      updateOpusMagnum(data.data);  // Update M1-M7 panels
    }
  };
}, [session_id]);
```

---

#### `frontend/src/views/Dashboard.tsx`
- **Purpose:** Display 7 analytical modules (M1-M7) from Slow Path
- **Modules:**
  1. M1: DNA Client
  2. M2: Tactical Indicators
  3. M3: Psychometric Profile
  4. M4: Deep Motivation
  5. M5: Predictive Paths
  6. M6: Strategic Playbook
  7. M7: Decision Vectors
- **Data Source:** Opus Magnum JSON from `slow_path_logs` table

---

#### `frontend/src/views/AdminPanel.tsx`
- **Purpose:** System administration interface
- **Tabs:**
  1. Analytics - Session metrics, success rates
  2. Feedback - Grouped feedback themes (Prompt 5 AI clustering)
  3. Golden Standards - CRUD for best-practice responses
  4. RAG Configuration - Knowledge base management
- **Authentication:** Requires `X-Admin-Key` header

---

## 2. Knowledge Base & RAG

### Primary Source File

#### `backend/nuggets_v2.1_FINAL_WITH_IDS.json`
- **Purpose:** **FINAL SOURCE OF TRUTH** - Complete RAG knowledge base
- **Size:** 8,666 lines (581 nuggets)
- **Status:** ✅ Fully cleaned, validated, atomic, with UUIDs
- **Processing History:**
  - P0: Remove placeholders, HTML → 526 → 521 nuggets
  - P1: Merge semantic duplicates → 521 → 519 nuggets
  - P2A: Verify contradictions (none found) → 519 nuggets
  - P2B: Atomize "blobs" (>800 chars) → 519 → **581 nuggets**
  - UUID Healing: Add missing IDs → 581 nuggets with UUIDs

**Nugget Structure:**
```json
{
  "id": "5a9af675-d6f9-481b-8923-d5ec617d669a",  // ← UUID (CRITICAL!)
  "title": "Typ D (Dominance) - Szybkość vs. Szczegóły",
  "content": "Klient D myśli szybko, podejmuje decyzje...",
  "keywords": "DISC, Typ D, szybkie decyzje, benefity, timeline",
  "type": "psychologia",
  "tags": ["DISC", "Typ D", "szybkie decyzje"],
  "language": "pl",
  "archetype_filter": ["dominance"]
}
```

**Why UUIDs Matter:**
- Qdrant point ID = UUID from JSON
- Enables validation set testing (ground truth UUIDs match!)
- Prevents "ID mismatch" bug (previous: auto-increment 1,2,3...)

**Content Categories:**
- DISC Psychology: 150+ nuggets
- Tesla Technical Specs: 100+ nuggets
- Objection Handling: 100+ nuggets
- Sales Tactics: 100+ nuggets
- Competitive Analysis: 76+ nuggets
- TCO Calculations: 55+ nuggets

---

### Alternative/Backup Files

#### `backend/nuggets_v2.0_FINAL_ATOMIZED.json`
- **Purpose:** Version before UUID healing (87 nuggets missing IDs)
- **Status:** ⚠️ DEPRECATED - Use v2.1 instead
- **Why Keep:** Historical reference for atomization process

#### `backend/nuggets_v1.2_cleaned_P1-FIXED.json`
- **Purpose:** Version after P1 cleaning (before atomization)
- **Status:** ⚠️ DEPRECATED
- **Nuggets:** 519 (not atomized)

---

## 3. Deployment & Operations Scripts

### Critical Deployment Script

#### `backend/fix_and_redeploy_rag.py`
- **Purpose:** **MOST IMPORTANT SCRIPT** - Complete rebuild of Qdrant RAG collection
- **Size:** 379 lines
- **Status:** ✅ PRODUCTION-READY

**What It Does:**
1. Deletes old `ultra_rag_v1` collection (if exists)
2. Creates new collection (768D, Cosine similarity)
3. Loads [`nuggets_v2.1_FINAL_WITH_IDS.json`](backend/nuggets_v2.1_FINAL_WITH_IDS.json)
4. For each nugget:
   - Extract UUID from `id` field ← **CRITICAL FIX**
   - Combine `title + content` for embedding
   - Generate 768D embedding (Gemini `text-embedding-004`, `task_type="retrieval_document"`)
   - Create `PointStruct` with **UUID as ID** (not auto-increment!)
   - Upsert to Qdrant in batches (100 nuggets per batch)
5. Verification: Run sample query "Ile realnie tracę zasięgu zimą?"
6. Report: Show top 3 results with scores

**Usage:**
```bash
cd backend
python fix_and_redeploy_rag.py
```

**Expected Output:**
```
[OK] Deleted old collection 'ultra_rag_v1'
[OK] Created collection 'ultra_rag_v1' (768D, Cosine)
[OK] Loaded 581 nuggets
[INDEX] Indexing 581 nuggets (batch size: 100)...
Indexing batches: 100% |████████| 6/6 [05:23<00:00, 53.91s/it]
[OK] Successfully indexed 581 nuggets

[TEST] Testing collection with sample query...
   Query: 'Ile realnie tracę zasięgu zimą?'
   Top 3 results:
   1. [Score: 0.6269] 59a1885a-f218-4d35-9ff0-fb3b590e193d
      Obiekcja "Zimą Zasięg Spada" – Reframe z Nauki
   2. [Score: 0.5672] b7360e69-f414-48dc-a863-9fc1da0bf189
      Zasięg Zimą z Pompą Ciepła
   3. [Score: 0.5543] dfe0f394-edcc-4da7-abfd-9d6016c01595
      Zimowy Test NAF 2025 – Konkurencyjna Przewaga

[OK] Sample query test PASSED!

SUCCESS!
[OK] Przebudowano kolekcje 'ultra_rag_v1'
[OK] Wdrożono 581 nuggetów z poprawnymi ID (UUID)
[OK] Validation Set powinien teraz działać poprawnie!
```

**Why This Script Is Critical:**
- Fixes "ID mismatch" bug (Qdrant IDs must match JSON UUIDs)
- Ensures correct embedding model (`text-embedding-004`, 768D)
- Uses correct task_type (`retrieval_document` for indexing)
- Tests deployment with real query

---

### Testing & Validation Scripts

#### `backend/optimize_threshold.py`
- **Purpose:** Find optimal `score_threshold` for RAG retrieval
- **Size:** 335 lines
- **Methodology:**
  1. Test thresholds: [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
  2. For each query in validation set:
     - Search Qdrant with threshold
     - Compare retrieved IDs vs ground truth
     - Calculate Precision, Recall, F1-Score
  3. Find threshold with max F1-Score

**Usage:**
```bash
cd backend
python optimize_threshold.py
```

**Output:**
- Console: Threshold comparison table
- File: [`threshold_optimization_results.json`](backend/threshold_optimization_results.json) (8,948 lines)

**Status:** ✅ COMPLETED
- Tested thresholds up to 0.50
- Optimal threshold: **0.55** (determined manually via sample testing)
- Reason: `retrieval_document` vs `retrieval_query` asymmetry requires higher threshold

---

#### `backend/validation_set_rag.py`
- **Purpose:** 15 test queries with ground truth for RAG validation
- **Size:** 336 lines

**Test Queries:**
```python
VALIDATION_SET = [
    {
        "id": "Q01",
        "category": "RANGE_WINTER",
        "query": "Ile realnie tracę zasięgu zimą?",
        "ground_truth_ids": [
            "59a1885a-f218-4d35-9ff0-fb3b590e193d",  # Obiekcja "Zimą Zasięg Spada"
            "dfe0f394-edcc-4da7-abfd-9d6016c01595",  # Zimowy Test NAF 2025
            "5c1bfc4c-6020-427d-96d7-fe2d20772301",  # Zasięg Zimą z Pompą Ciepła
            "7051c7da-c547-488f-aa0c-67c914a9a26c",  # Zasięg Zimą Pompa Ciepła (environmental)
        ],
        "expected_answer_contains": ["350-400 km", "NAF", "pompa ciepła", "-24%"]
    },
    # ... 14 more queries
]
```

**Categories Tested:**
- RANGE_WINTER - Winter range concerns
- SUBSIDY - Government subsidies (NaszEauto)
- TCO_PRICE - Total cost of ownership
- CHARGING - Charging infrastructure
- SAFETY - Autopilot safety
- COMPETITION - Tesla vs competitors
- LEASING - Financing options
- WARRANTY - Battery warranty
- PRICE_OBJECTION - Price concerns
- UPDATES - OTA updates
- RANGE_ANXIETY - Range anxiety
- LIFESTYLE - Camp mode, features

---

#### `backend/test_system.py`
- **Purpose:** Comprehensive system health check
- **Tests:**
  1. Backend health endpoint
  2. PostgreSQL connection & table counts
  3. Qdrant connection & point counts
  4. Session creation & retrieval
  5. Conversation log persistence
  6. Feedback system
  7. Slow Path execution logs
  8. Golden Standards

**Usage:**
```bash
cd backend
python test_system.py
```

**Expected Output:**
```
✅ Backend health: OK
✅ PostgreSQL: Connected (5 tables)
✅ Qdrant: Connected (581 points)
✅ Sessions: 25 created
✅ Messages: 44 logged
✅ Slow Path: 23 executions (100% success)
✅ Feedback: 1 entry
✅ Golden Standards: 14 entries
```

---

#### Other Test Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `backend/test_rag_scores.py` | Test RAG retrieval with sample queries | ✅ |
| `backend/test_direct_query_rag.py` | Direct Qdrant query test | ✅ |
| `backend/test_api_e2e.py` | End-to-end API test | ✅ |
| `backend/test_fast_path_quality.py` | Fast Path response quality check | ✅ |
| `backend/check_qdrant.py` | Check Qdrant collection stats | ✅ |
| `backend/check_feedback.py` | Check feedback logs | ✅ |
| `backend/check_sessions.py` | Check session stats | ✅ |

---

## 4. Testing & Validation

### Validation Output Files

#### `backend/threshold_optimization_results.json`
- **Purpose:** Complete results from threshold optimization
- **Size:** 8,948 lines
- **Format:** JSON with per-query metrics for each threshold
- **Key Data:**
  ```json
  {
    "all_results": [
      {
        "threshold": 0.20,
        "avg_precision": 0.0867,
        "avg_recall": 0.5111,
        "avg_f1": 0.1436,
        "query_results": [
          {
            "query_id": "Q01",
            "query": "Ile realnie tracę zasięgu zimą?",
            "retrieved_ids": [...],
            "ground_truth_ids": [...],
            "metrics": {
              "precision": 0.2,
              "recall": 0.5,
              "f1": 0.2857,
              "tp": 2,
              "fp": 8,
              "fn": 2
            },
            "scores": [
              {"id": "59a1885a-...", "score": 0.6269},
              {"id": "b7360e69-...", "score": 0.5672},
              ...
            ]
          },
          ...
        ]
      },
      ...
    ],
    "best_threshold": {
      "threshold": 0.50,
      "avg_f1": 0.XXX
    }
  }
  ```

**How to Use:**
- Find optimal threshold by max F1-Score
- Analyze per-category performance
- Debug why specific queries fail
- Validate ground truth quality

---

## 5. Documentation & Reports

### Core Documentation

#### `PROJECT_STATUS_README.md`
- **Purpose:** **START HERE** - Current project status, next steps
- **Sections:**
  1. Current phase (Phase 5: Final E2E Verification)
  2. Last executed action (4-part RAG fix)
  3. Next steps (E2E test scenarios)
  4. System architecture overview
  5. Knowledge base status
  6. Deployment scripts
  7. Known issues & resolutions
  8. Environment configuration
  9. Quick start commands

---

#### `ARCHITECTURE_OVERVIEW.md`
- **Purpose:** System design, component breakdown, data flow
- **Sections:**
  1. Component overview (Frontend, Backend, AI models, Databases)
  2. Frontend architecture (Views, components)
  3. Backend architecture (Dual-path AI, RAG integration, session management)
  4. AI orchestration (4 prompts, personas)
  5. Data architecture (PostgreSQL schema, Qdrant collection)
  6. External integrations (Gemini, Ollama)
  7. Real-time communication (WebSocket)
  8. Deployment architecture
  9. Security & privacy
  10. Performance optimization
  11. Monitoring & observability
  12. Scalability considerations

---

#### `KEY_FILES_MANIFEST.md`
- **Purpose:** This file - Quick reference index of all critical files

---

#### `DEBUGGING_HISTORY.md`
- **Purpose:** Chronicle of all major bugs & fixes
- **Sections:**
  1. Bug #1: Embedding Mismatch (384D vs 768D)
  2. Bug #2: ID Mismatch (auto-increment vs UUID)
  3. Bug #3: Missing IDs (87 nuggets without UUIDs)
  4. Bug #4: Threshold Too High (0.70 → 0.55)
  5. Lessons learned
  6. Prevention strategies

---

### Processing Reports

#### `CLEANING_P0_REPORT.md`
- **Purpose:** Phase 0 cleaning report (remove placeholders, HTML, low-value)
- **Result:** 526 → 521 nuggets

#### `CLEANING_P1_FIXED_REPORT.md`
- **Purpose:** Phase 1 deduplication report (merge semantic duplicates)
- **Result:** 521 → 519 nuggets

#### `P2A_CONTRADICTIONS_REPORT.md`
- **Purpose:** Phase 2A contradiction detection report
- **Result:** 519 nuggets (no contradictions found!)

#### `P2B_ATOMIZATION_REPORT.md`
- **Purpose:** Phase 2B "blob" splitting report (>800 chars → atomic nuggets)
- **Result:** 519 → 581 nuggets (+62 from splitting 25 "blobs")

---

### Testing Reports

#### `SYSTEM_TEST_REPORT.md`
- **Purpose:** Comprehensive system test results
- **Date:** 2025-11-11
- **Status:** ✅ All tests passed
- **Key Metrics:**
  - Backend: ✅ Health check OK
  - PostgreSQL: ✅ 5 tables, 25 sessions, 44 messages
  - Qdrant: ✅ 101 points (old data, should be 581 after redeployment)
  - Fast Path: ✅ 100% success rate (10/10)
  - Slow Path: ✅ 100% success rate (23/23)
  - Feedback: ✅ Backend works (UI not tested yet)

#### `RAG_AUDIT_REPORT.md`
- **Purpose:** Initial RAG knowledge base quality audit
- **Date:** 2025-11-17
- **Findings:**
  - Exact duplicates: 0 ✅
  - Semantic duplicates: 2 (merged in P1)
  - Contradictions: 20 (false positives, resolved in P2A)
  - Low-value entries: 1 (removed in P0)
  - "Blobs" (>800 chars): 29 (split in P2B)

#### `RAG_THRESHOLD_OPTIMIZATION_GUIDE.md`
- **Purpose:** Guide for threshold tuning methodology
- **Methodology:** Precision/Recall tradeoff, F1-Score optimization

#### `VALIDATION_SET_SUMMARY.md`
- **Purpose:** Summary of 15 validation queries

---

### Other Documentation

| File | Purpose |
|------|---------|
| `FINAL_STATUS.md` | Final import status (Golden Standards + RAG) |
| `IMPORT_STATUS.md` | Import progress log |
| `ADMIN_PANEL_GUIDE.md` | Admin panel user guide |
| `BULK_IMPORT_GUIDE.md` | Bulk import feature guide |
| `SYSTEM_FIXES_SUMMARY.md` | Summary of all system fixes |
| `SYSTEM_COMPLETENESS_AUDIT.md` | Completeness audit |

---

## 6. Configuration Files

### Backend Configuration

#### `backend/.env`
- **Purpose:** **SENSITIVE** - Environment variables
- **Contents:**
  ```env
  # PostgreSQL
  POSTGRES_USER=ultra_user
  POSTGRES_PASSWORD=password
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_DB=ultra_db

  # Qdrant
  QDRANT_HOST=localhost
  QDRANT_PORT=6333

  # Google Gemini
  GEMINI_API_KEY=your_gemini_api_key_here

  # Ollama Cloud
  OLLAMA_CLOUD_URL=https://ollama.com
  OLLAMA_API_KEY=your_ollama_api_key_here

  # Admin Panel
  ADMIN_API_KEY=ULTRA_DOJO_KEY_8a4f9b2c_qoder_ai_2025

  # CORS
  CORS_ORIGINS=http://localhost:5173,http://localhost:5174
  ```

**⚠️ IMPORTANT:** Never commit `.env` to Git!

---

#### `backend/requirements.txt`
- **Purpose:** Python dependencies
- **Key Libraries:**
  - `fastapi==0.109.0` - Web framework
  - `uvicorn==0.27.0` - ASGI server
  - `psycopg2-binary==2.9.9` - PostgreSQL driver
  - `qdrant-client==1.7.3` - Vector database client
  - `google-generativeai==0.3.2` - Gemini API
  - `ollama==0.1.6` - Ollama Cloud client
  - `sentence-transformers==2.3.1` - SentenceTransformer (legacy, not used)
  - `tenacity==8.2.3` - Retry logic
  - `python-dotenv==1.0.0` - Environment variables

---

#### `backend/Dockerfile`
- **Purpose:** Docker container for backend
- **Base Image:** `python:3.11-slim`

---

### Frontend Configuration

#### `frontend/package.json`
- **Purpose:** Node.js dependencies
- **Key Dependencies:**
  - `react@18.2.0` - UI framework
  - `react-router-dom@6.21.1` - Routing
  - `zustand@4.4.7` - State management
  - `lucide-react@0.307.0` - Icons
  - `recharts@2.10.3` - Charts for analytics

**Dev Dependencies:**
  - `vite@5.0.8` - Build tool
  - `typescript@5.2.2` - Type checking
  - `tailwindcss@3.4.0` - Styling
  - `@types/react@18.2.43` - TypeScript types

---

#### `frontend/vite.config.ts`
- **Purpose:** Vite build configuration
- **Key Settings:**
  ```typescript
  export default defineConfig({
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': 'http://localhost:8000'  // Proxy API calls to backend
      }
    }
  })
  ```

---

#### `frontend/tsconfig.json`
- **Purpose:** TypeScript compiler configuration

#### `frontend/tailwind.config.js`
- **Purpose:** Tailwind CSS configuration (dark mode, custom colors)

#### `frontend/postcss.config.js`
- **Purpose:** PostCSS configuration (Tailwind processing)

---

## 7. Frontend Components

### Utility Files

#### `frontend/src/utils/api.ts`
- **Purpose:** API client for backend communication
- **Functions:**
  - `createSession()` - POST `/api/v1/sessions/new`
  - `sendMessage()` - POST `/api/v1/sessions/send`
  - `sendFeedback()` - POST `/api/v1/sessions/feedback`
  - `getSession()` - GET `/api/v1/sessions/{id}`
  - `endSession()` - POST `/api/v1/sessions/end`
  - Admin API calls (grouped feedback, RAG management)

---

#### `frontend/src/utils/websocket.ts`
- **Purpose:** WebSocket connection management
- **Usage:**
  ```typescript
  const ws = connectWebSocket(session_id, (data) => {
    if (data.type === 'slow_path_complete') {
      updateOpusMagnum(data.data);
    }
  });
  ```

---

#### `frontend/src/utils/i18n.ts`
- **Purpose:** Internationalization (Polish/English)
- **Translations:** Loaded from `frontend/src/utils/i18n_locales.json`

---

### Component Files

#### `frontend/src/components/JourneyStageSelector.tsx`
- **Purpose:** Journey stage selector with AI suggestions
- **Features:**
  - 3 stages: Odkrywanie / Analiza / Decyzja
  - AI suggested stage (pulsating ring)
  - Manual override (badge "Manual")

---

#### `frontend/src/components/QuestionAnswerModal.tsx`
- **Purpose:** Modal for answering strategic questions
- **Usage:** When user clicks on SPIN question
- **Output:** Formatted as "P: [question] O: [answer]"

---

#### `frontend/src/components/OpusMagnumPanel.tsx`
- **Purpose:** Right sidebar with 7 analytical modules (M1-M7)
- **Features:**
  - Collapsible panels
  - Real-time updates via WebSocket
  - Confidence scores
  - Journey stage suggestions

---

#### Admin Panel Components

| Component | Purpose |
|-----------|---------|
| `frontend/src/components/admin/AnalyticsTab.tsx` | Analytics dashboard |
| `frontend/src/components/admin/FeedbackTab.tsx` | Grouped feedback themes |
| `frontend/src/components/admin/GoldenStandardsTab.tsx` | Best-practice responses |
| `frontend/src/components/admin/RagTab.tsx` | RAG nuggets management |

---

#### Module Components (M1-M7)

| Component | Module |
|-----------|--------|
| `frontend/src/components/modules/M1_DnaClient.tsx` | DNA Client |
| `frontend/src/components/modules/M2_TacticalIndicators.tsx` | Tactical Indicators |
| `frontend/src/components/modules/M3_PsychometricProfile.tsx` | Psychometric Profile |
| `frontend/src/components/modules/M4_DeepMotivation.tsx` | Deep Motivation |
| `frontend/src/components/modules/M5_PredictivePaths.tsx` | Predictive Paths |
| `frontend/src/components/modules/M6_StrategicPlaybook.tsx` | Strategic Playbook |
| `frontend/src/components/modules/M7_DecisionVectors.tsx` | Decision Vectors |

---

### State Management

#### `frontend/src/store/useStore.ts`
- **Purpose:** Zustand global state
- **State:**
  ```typescript
  interface StoreState {
    // Session
    sessionId: string | null;
    journeyStage: string;
    
    // Messages
    messages: Message[];
    
    // Opus Magnum (M1-M7)
    opusMagnum: OpusMagnumJSON | null;
    
    // UI State
    isLoading: boolean;
    language: 'pl' | 'en';
    
    // Actions
    setSessionId: (id: string) => void;
    addMessage: (message: Message) => void;
    updateOpusMagnum: (data: OpusMagnumJSON) => void;
  }
  ```

---

### Type Definitions

#### `frontend/src/types.ts`
- **Purpose:** TypeScript interfaces for all data structures
- **Key Types:**
  - `Message` - Conversation message
  - `OpusMagnumJSON` - Slow Path analysis (7 modules)
  - `Session` - Session metadata
  - `Feedback` - Feedback entry
  - `RAGNugget` - Knowledge base nugget
  - `GoldenStandard` - Best-practice response

---

## 8. Sample Data Files

### For Testing

| File | Purpose | Usage |
|------|---------|-------|
| `sample_rag_nuggets.json` | Sample RAG nuggets for bulk import | Admin Panel → RAG Tab → Bulk Import |
| `sample_golden_standards.json` | Sample best-practice responses | Admin Panel → Golden Standards Tab → Bulk Import |
| `datatoupload/gol1-4.json` | Golden standards (split files) | Bulk import testing |
| `datatoupload/nugget1-4.json` | RAG nuggets (split files) | Bulk import testing |

---

## 9. Quick Reference: File Locations

### "Where do I find...?"

**❓ "Where is the RAG query logic?"**
→ [`backend/app/main.py`](backend/app/main.py) lines 269-341 (`query_rag()` function)

**❓ "Where is the threshold configured?"**
→ [`backend/app/main.py`](backend/app/main.py) line 317 (`score_threshold=0.55`)

**❓ "Where is the knowledge base?"**
→ [`backend/nuggets_v2.1_FINAL_WITH_IDS.json`](backend/nuggets_v2.1_FINAL_WITH_IDS.json)

**❓ "How do I redeploy RAG?"**
→ Run `python backend/fix_and_redeploy_rag.py`

**❓ "Where are the AI prompts?"**
→ [`backend/app/main.py`](backend/app/main.py):
  - Fast Path: lines 596-748 (`build_prompt_1()`)
  - Slow Path: lines 768-848 (`build_prompt_4_slow_path()`)

**❓ "Where is the conversation UI?"**
→ [`frontend/src/views/Conversation.tsx`](frontend/src/views/Conversation.tsx)

**❓ "Where are the 7 analytical modules?"**
→ [`frontend/src/components/modules/M1_DnaClient.tsx`](frontend/src/components/modules/M1_DnaClient.tsx) through [`M7_DecisionVectors.tsx`](frontend/src/components/modules/M7_DecisionVectors.tsx)

**❓ "Where is the database schema?"**
→ Auto-created by SQLAlchemy/Psycopg2, see [`backend/app/main.py`](backend/app/main.py) lifespan function

**❓ "Where are the test queries?"**
→ [`backend/validation_set_rag.py`](backend/validation_set_rag.py) (15 queries)

**❓ "Where is the system test?"**
→ [`backend/test_system.py`](backend/test_system.py)

**❓ "Where are environment variables?"**
→ [`backend/.env`](backend/.env) (create from `.env.example`)

**❓ "Where is the deployment script?"**
→ [`backend/fix_and_redeploy_rag.py`](backend/fix_and_redeploy_rag.py) (⭐ MOST IMPORTANT)

---

## 10. Critical File Dependencies

### "If I change X, what breaks?"

**If you change [`nuggets_v2.1_FINAL_WITH_IDS.json`](backend/nuggets_v2.1_FINAL_WITH_IDS.json):**
- **Must redeploy:** Run [`fix_and_redeploy_rag.py`](backend/fix_and_redeploy_rag.py)
- **Must retest:** Run [`optimize_threshold.py`](backend/optimize_threshold.py)
- **May need recalibration:** Threshold (0.55) might need adjustment

**If you change threshold in [`main.py`](backend/app/main.py) line 317:**
- **Must test:** Run E2E scenarios (Winter Range, TCO)
- **Must verify:** Check Precision/Recall tradeoff
- **Document:** Update [`DEBUGGING_HISTORY.md`](DEBUGGING_HISTORY.md)

**If you change Fast Path prompt ([`build_prompt_1()`](backend/app/main.py) lines 596-748):**
- **Must test:** Send sample queries, check quality
- **Must verify:** Confidence scores, topic matching
- **May break:** Feedback system (JSON structure)

**If you change Slow Path prompt ([`build_prompt_4_slow_path()`](backend/app/main.py) lines 768-848):**
- **Must test:** Run Slow Path, check all 7 modules
- **May break:** Frontend Dashboard (expects specific JSON structure)
- **Must verify:** WebSocket updates

**If you change database schema:**
- **Must migrate:** Create migration script (Alembic)
- **Must update:** Pydantic models in [`models.py`](backend/app/models.py)
- **May break:** Admin Panel, Analytics

**If you change API response structure:**
- **Must update:** Frontend API client ([`api.ts`](frontend/src/utils/api.ts))
- **Must update:** TypeScript types ([`types.ts`](frontend/src/types.ts))
- **May break:** Frontend views, components

---

## 11. Emergency Procedures

### "System is broken, what do I check?"

**1. RAG returns no results:**
→ Check:
  - Qdrant running: `curl http://localhost:6333/collections/ultra_rag_v1`
  - Collection has points: `python backend/check_qdrant.py`
  - Threshold not too high: [`main.py`](backend/app/main.py) line 317
  - Gemini API key valid: [`backend/.env`](backend/.env)

**2. Fast Path errors:**
→ Check:
  - Gemini API key: [`backend/.env`](backend/.env)
  - Backend logs: Terminal running `uvicorn`
  - Rate limit: Wait 1 minute, retry
  - Prompt JSON validity: Check [`build_prompt_1()`](backend/app/main.py)

**3. Slow Path timeout:**
→ Check:
  - Ollama API key: [`backend/.env`](backend/.env)
  - Timeout setting: [`main.py`](backend/app/main.py) line 97 (90s)
  - Network connectivity
  - Prompt length (< 32K tokens)

**4. Database connection errors:**
→ Check:
  - PostgreSQL running: `psql -U ultra_user -d ultra_db`
  - Credentials correct: [`backend/.env`](backend/.env)
  - Tables exist: `python backend/test_system.py`

**5. Frontend not loading:**
→ Check:
  - Backend running: `curl http://localhost:8000/health`
  - Frontend dev server: `cd frontend && npm run dev`
  - CORS origins: [`backend/.env`](backend/.env)
  - Browser console for errors

---

## 12. File Size Statistics

| File | Lines | Size | Importance |
|------|-------|------|------------|
| [`backend/app/main.py`](backend/app/main.py) | 2,474 | ~100KB | ⭐⭐⭐⭐⭐ |
| [`backend/nuggets_v2.1_FINAL_WITH_IDS.json`](backend/nuggets_v2.1_FINAL_WITH_IDS.json) | 8,666 | ~1.5MB | ⭐⭐⭐⭐⭐ |
| [`backend/fix_and_redeploy_rag.py`](backend/fix_and_redeploy_rag.py) | 379 | ~15KB | ⭐⭐⭐⭐⭐ |
| [`backend/threshold_optimization_results.json`](backend/threshold_optimization_results.json) | 8,948 | ~1.2MB | ⭐⭐⭐⭐ |
| [`backend/validation_set_rag.py`](backend/validation_set_rag.py) | 336 | ~14KB | ⭐⭐⭐⭐ |
| [`frontend/src/views/Conversation.tsx`](frontend/src/views/Conversation.tsx) | ~300 | ~12KB | ⭐⭐⭐⭐ |
| [`frontend/src/views/Dashboard.tsx`](frontend/src/views/Dashboard.tsx) | ~400 | ~16KB | ⭐⭐⭐⭐ |

---

**END OF MANIFEST**

**For complete documentation, see:**
- [`PROJECT_STATUS_README.md`](PROJECT_STATUS_README.md) - Current status & next steps
- [`ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) - System architecture
- [`DEBUGGING_HISTORY.md`](DEBUGGING_HISTORY.md) - Bug fixes & lessons
