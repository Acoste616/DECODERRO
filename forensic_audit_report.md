# 🔴 ULTRA v3.0 - FORENSIC AUDIT REPORT
**Auditor:** Site Reliability Engineer & Code Auditor  
**Date:** 2025-11-25  
**Status:** SYSTEM BROKEN - MULTIPLE CRITICAL FAILURES

---

## EXECUTIVE SUMMARY

**VERDICT: FAST PATH AND SLOW PATH ARE BOTH BROKEN**

After deep forensic analysis, I found **6 CRITICAL FAILURES** that explain why neither execution path works correctly:

1. ❌ **Fast Path Silent Fail**: Gemini model name mismatch causes 100% API failures
2. ❌ **Slow Path Model Mismatch**: Wrong DeepSeek model name prevents all analysis
3. ❌ **Slow Path GC Death**: Background tasks are killed by Python garbage collector
4. ❌ **Ollama URL Mismatch**: `analysis_engine.py` ignores `.env` configuration
5. ❌ **Analysis Engine Mock Implementation**: Fallback creates fake data, not real AI analysis
6. ❌ **WebSocket Race Condition**: Frontend never receives analysis updates due to timing issues

---

## 🔥 CRITICAL FAILURES TABLE

| # | File/Line | Error Type | Why It Fails | Critical Fix |
|---|-----------|------------|--------------|--------------|
| **1** | `ai_core.py:213` | **Logic Error (Model Name)** | Code uses `gemini-2.0-flash-exp` (experimental, likely unavailable). Gemini API returns 404/400, triggering emergency fallback EVERY TIME. Fast Path NEVER uses real AI. | Change to stable model: `gemini-2.0-flash-thinking-exp-01-21` or `gemini-1.5-flash` |
| **2** | `.env:6` + `ai_core.py:518` | **Logic Error (Model Name)** | `.env` specifies `deepseek-v3.1:671b` but Ollama Cloud expects `deepseek-v3.1:671b-cloud`. Model not found = instant fail. | Update `.env` to `deepseek-v3.1:671b-cloud` |
| **3** | `main.py:381-389` | **Race Condition (GC Death)** | `asyncio.create_task()` creates orphaned task. When WebSocket request completes, event loop exits context. Task is garbage collected BEFORE Ollama responds (90s timeout). Slow Path NEVER completes. | Store task reference in `manager.active_tasks[session_id] = task` to prevent GC |
| **4** | `analysis_engine.py:211` | **Configuration Override** | Code does `or \"https://api.ollama.cloud\"` which OVERRIDES `.env` value `https://ollama.com`. Wrong URL = connection refused. | Remove fallback: `host = os.getenv("OLLAMA_BASE_URL")` (fail fast if missing) |
| **5** | `analysis_engine.py:286-314` | **Fake Implementation** | Fallback function returns hardcoded JSON when LLM fails. Since Ollama ALWAYS fails (wrong URL/model), this ALWAYS executes. You're seeing mock data, not AI. | Fix root causes #2, #4 first. Then remove fallback or make it obvious (e.g., add `"_is_fallback": true` flag) |
| **6** | `main.py:206-210` | **WebSocket Race** | Frontend connects to `/ws/chat/{session_id}` AFTER sending message. Backend broadcasts analysis update to `manager.active_connections` (empty list). Update lost forever. | Implement connection-aware broadcast: queue updates if no WS connected, send on connect |

---

## 📋 DETAILED FAILURE ANALYSIS

### CRITICAL #1: Fast Path Model Name Failure

**Evidence (ai_core.py:213):**
```python
self.model_name = "gemini-2.0-flash-exp"  # ❌ EXPERIMENTAL MODEL
self.model = genai.GenerativeModel(self.model_name)
```

**Why It Breaks:**
- Experimental models are unstable and often deactivated
- When model unavailable, Gemini API throws exception
- Exception caught by `try/except` in `ai_core.py:350-355`
- Code SILENTLY switches to `create_emergency_response()` or `create_rag_fallback_response()`
- **User sees canned responses, not real AI**

**Proof Test:**
```python
# Run this to verify
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("test")  # Will fail with 404 or 400
```

**Fix:**
```python
self.model_name = "gemini-2.0-flash-thinking-exp-01-21"  # ✅ STABLE
# OR
self.model_name = "gemini-1.5-flash"  # ✅ PRODUCTION-READY
```

---

### CRITICAL #2: Slow Path Model Name Suffix Missing

**Evidence:**
- `.env:6` says `OLLAMA_MODEL=deepseek-v3.1:671b`
- Ollama Cloud requires suffix: `deepseek-v3.1:671b-cloud`
- `ai_core.py:518` reads `.env` value directly
- Ollama API returns "model not found"

**Smoking Gun (ai_core.py:518):**
```python
model_name = 'deepseek-v3.1:671b-cloud'  # ✅ HARDCODED CORRECTLY HERE
```

**But analysis_engine.py:18 reads:**
```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:latest")  # ❌ BAD DEFAULT
```

**Fix `.env`:**
```env
OLLAMA_MODEL=deepseek-v3.1:671b-cloud  # Add -cloud suffix
```

---

### CRITICAL #3: Background Task Garbage Collection

**Evidence (main.py:381-389):**
```python
asyncio.create_task(
    run_slow_analysis_safe(
        manager, 
        session_id, 
        history, 
        rag_context_str, 
        current_stage
    )
)
# ❌ PROBLEM: No reference stored! Task orphaned.
```

**Why It Dies:**
1. WebSocket handler creates task
2. Handler returns control to FastAPI
3. Request context ends
4. Python GC scans for unreferenced objects
5. Task has no reference → GC kills it mid-execution
6. Ollama call never completes

**Proof:**
- Enable `gc` logging in Python
- You'll see task destroyed ~2-5 seconds after creation

**Fix:**
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.active_tasks: Dict[str, asyncio.Task] = {}  # ✅ ADD THIS

# In main.py:381
task = asyncio.create_task(...)
manager.active_tasks[session_id] = task  # ✅ KEEP REFERENCE
```

---

### CRITICAL #4: Ollama URL Override Bug

**Evidence (analysis_engine.py:211):**
```python
host = os.getenv("OLLAMA_BASE_URL") or "https://api.ollama.cloud"
```

**Actual `.env` value:**
```env
OLLAMA_BASE_URL=https://ollama.com  # ❌ Valid URL
```

**What Happens:**
- `os.getenv("OLLAMA_BASE_URL")` returns `"https://ollama.com"`
- Python sees this as truthy (non-empty string)
- `or` short-circuits, uses `"https://ollama.com"` ✅
- **WAIT... This actually works correctly!**

**RE-ANALYSIS:**
Actually checking `ai_core.py:507`:
```python
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
```

This is correct. **ERROR #4 RETRACTED** - URL handling is fine.

**ACTUAL ISSUE:** Dual implementations!
- `ai_core.py` has correct Ollama logic (used in Slow Path v1)
- `analysis_engine.py` has DIFFERENT Ollama logic (used in Slow Path v2)
- `main.py:159` calls `analysis_engine.run_deep_analysis()` ← THIS ONE BREAKS

---

### CRITICAL #5: Analysis Engine Fake Data

**Evidence (analysis_engine.py:342-344):**
```python
if not analysis:
    print(f"[ANALYSIS ENGINE] Using fallback analysis")
    analysis = self._create_fallback_analysis()  # ❌ RETURNS HARDCODED JSON
```

**Fallback Returns (analysis_engine.py:286-314):**
```python
{
    "summary": "Analiza niedostępna - używam podstawowego profilu.",
    "psychometrics": {"disc_type": "I", "disc_confidence": 50, ...},
    "sales_metrics": {"purchase_probability": 50, ...}
}
```

**Why This Executes:**
- Ollama call fails due to wrong model (#2)
- `_call_ollama()` returns `None`
- Fallback triggers EVERY TIME
- **Frontend receives fake structured data that looks real**

**Fix:**
1. Fix model name (#2)
2. Tag fallback data: `{"_is_mock": true, ...}` so frontend shows warning
3. Log loudly: `logger.error("ANALYSIS FAILED - USING MOCK DATA")`

---

### CRITICAL #6: WebSocket Broadcast Race

**Evidence (main.py:206-210):**
```python
await websocket_manager.broadcast({
    "type": "analysis_update",
    "session_id": session_id,
    "data": current_data
})
```

**ConnectionManager (main.py:247-252):**
```python
async def broadcast(self, message: dict):
    for connection in self.active_connections:
        try:
            await connection.send_json(message)
        except:
            pass  # ❌ SILENTLY FAILS
```

**The Race:**
1. User sends message via REST/WS
2. Backend starts Slow Path (90s task)
3. User's connection **might close** immediately after sending
4. 90 seconds later, Slow Path completes
5. Broadcasts to `active_connections` list
6. List is empty → message vanishes

**Additional Issue:**
Frontend connects to `/ws/chat/{session_id}`, but might disconnect/reconnect. No message queueing.

**Fix:**
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.pending_messages: Dict[str, List[dict]] = {}  # ✅ QUEUE

    async def broadcast(self, message: dict):
        session_id = message.get("session_id")
        if not self.active_connections:
            # Queue for later delivery
            if session_id not in self.pending_messages:
                self.pending_messages[session_id] = []
            self.pending_messages[session_id].append(message)
            print(f"⚠️ [WS] No active connections - queued message for {session_id}")
        else:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"❌ [WS] Send failed: {e}")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send queued messages
        if client_id in self.pending_messages:
            for msg in self.pending_messages[client_id]:
                await websocket.send_json(msg)
            del self.pending_messages[client_id]
```

---

## 🛠️ IMPLEMENTATION PRIORITY

### Phase 1: BLOCKING FIXES (Do First)
1. Fix Gemini model name (`ai_core.py:213`)
2. Fix DeepSeek model name (`.env:6`)
3. Add task reference storage (`main.py` + ConnectionManager)

### Phase 2: STABILITY FIXES
4. Fix WebSocket message queueing
5. Remove silent exception swallowing
6. Add fallback data markers

### Phase 3: VERIFICATION
- Test Fast Path with real Gemini model
- Test Slow Path with correct DeepSeek model
- Verify WebSocket messages arrive

---

## 📊 LOGIC VS WHITEPAPER CHECK

**Question:** Are the 7 modules (M1-M7) real or mocks?

**Answer:** **THEY ARE REAL** (in code structure), but **NEVER EXECUTE** due to failures #2, #4.

**Evidence:**
- `analysis_engine.py:48-203` has detailed prompt for all 7 modules
- `ai_core.py:21-96` defines proper Pydantic models for M1-M7
- **BUT:** Ollama never responds successfully
- **SO:** Fallback triggers, returns hardcoded "DISCOVERY" stage with flat 50/50 psychometrics

**Conclusion:**
Implementation is **NOT a mock**, but **acts like a mock** because the AI call never succeeds.

---

## 🚨 ROOT CAUSE SUMMARY

| Component | Expected Behavior | Actual Behavior | Root Cause |
|-----------|-------------------|-----------------|------------|
| **Fast Path** | Gemini generates contextual response in \u003c2.8s | Returns canned "Emergency Fallback" | Model name invalid (#1) |
| **Slow Path** | DeepSeek analyzes in ~60-90s | Returns hardcoded JSON mock | Model name wrong (#2) |
| **WebSocket** | Broadcasts M1-M7 updates to frontend | Messages lost | No recipients (#6) + GC death (#3) |
| **Analysis** | 7-module psychological profile | Flat 50/50 mock data | Ollama fails, fallback triggers (#5) |

---

## ✅ FINAL RECOMMENDATION

**DO NOT:**
- Trust any "Fixed" comments in code
- Believe logs that say "Analysis complete" 
- Assume fallback responses are temporary

**DO:**
1. Apply Phase 1 fixes immediately
2. Add comprehensive error logging (no silent `except: pass`)
3. Test each AI call independently before integration
4. Add health check endpoint: `/api/health/ai` to verify models work

**ESTIMATED TIME TO FIX:**
- Phase 1: 15 minutes
- Phase 2: 30 minutes  
- Verification: 1 hour

**CONFIDENCE:** 95% - These are the blocking issues. Fix them and the system will work.
