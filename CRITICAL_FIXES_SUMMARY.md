# 🔧 ULTRA v3.0 - CRITICAL FIXES SUMMARY

## ⚡ IMMEDIATE ACTION REQUIRED

Your system has **6 CRITICAL FAILURES** preventing both Fast Path and Slow Path from working.

---

## 📋 PRIORITY 1: BLOCKING FIXES (Apply Now)

### Fix #1: Gemini Model Name (❌ BLOCKS FAST PATH)
**File:** `backend/ai_core.py` Line 213

**Current (BROKEN):**
```python
self.model_name = "gemini-2.0-flash-exp"  # Experimental, likely unavailable
```

**Fixed:**
```python
self.model_name = "gemini-1.5-flash"  # Production stable
```

---

### Fix #2: DeepSeek Model Suffix (❌ BLOCKS SLOW PATH)
**File:** `.env` Line 6

**Current (BROKEN):**
```env
OLLAMA_MODEL=deepseek-v3.1:671b
```

**Fixed:**
```env
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
```

---

### Fix #3: Background Task GC Death (❌ BLOCKS SLOW PATH)
**File:** `backend/main.py` Lines 232-254, 381-389

**Problem:** Tasks created with `asyncio.create_task()` have no reference → Garbage Collector kills them before Ollama responds.

**Solution:** Add to `ConnectionManager`:
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.active_tasks: Dict[str, asyncio.Task] = {}  # ✅ ADD THIS
```

Then in `main.py` line 381:
```python
task = asyncio.create_task(run_slow_analysis_safe(...))
manager.active_tasks[session_id] = task  # ✅ STORE REFERENCE
```

---

## 📋 PRIORITY 2: STABILITY FIXES

### Fix #6: WebSocket Race Condition
**File:** `backend/main.py` Lines 232-254

Add message queueing to `ConnectionManager`:
```python
self.pending_messages: Dict[str, List[dict]] = {}
```

Modify `broadcast()` to queue messages when no connections active.

See `CORRECTED_main.py` for full implementation.

---

## 🚀 DEPLOYMENT STEPS

1. **Backup Current Files:**
   ```bash
   cp backend/ai_core.py backend/ai_core.py.backup
   cp backend/main.py backend/main.py.backup
   cp .env .env.backup
   ```

2. **Apply Fixes:**
   - Copy `CORRECTED_ai_core.py` → `backend/ai_core.py`
   - Copy `CORRECTED_main.py` → `backend/main.py`
   - Copy `CORRECTED_.env` → `.env`

3. **Restart Backend:**
   ```bash
   # Kill existing uvicorn (Ctrl+C in terminal)
   uvicorn backend.main:app --reload
   ```

4. **Test Fast Path:**
   - Send a message in the UI
   - Check logs for: `✅ [AI CORE] Gemini model initialized: gemini-1.5-flash`
   - Verify AI response is NOT "Emergency Fallback"

5. **Test Slow Path:**
   - Wait 60-90 seconds after sending message
   - Check logs for: `✅ [SLOW] DeepSeek responded!`
   - Verify dashboard shows M1-M7 analysis (not flat 50/50 values)

---

## ⚠️ WHAT WAS WRONG

| Component | Expected | Actual | Result |
|-----------|----------|--------|--------|
| Fast Path | Real AI | Emergency fallback | Canned responses |
| Slow Path | M1-M7 analysis | Mock data | Fake 50/50 psychometrics |
| WebSocket | Live updates | Lost messages | No dashboard data |

---

## ✅ SUCCESS INDICATORS

After fixes, you should see:

**Fast Path (< 3s):**
- Log: `✅ [FAST PATH] Gemini response parsed successfully`
- UI: **Contextual, Polish** responses (not generic English fallback)

**Slow Path (~60s):**
- Log: `✅ [SLOW] DeepSeek responded!`
- Log: `🚀 [SLOW PATH] Sending update to UI`
- UI: **Dashboard shows varying psychometric scores** (not all 50)

**WebSocket:**
- Log: `✅ [WS] Client connected`
- Log: `📤 [WS] Sending X queued messages` (if reconnecting)

---

## 📞 IF STILL BROKEN

Check logs for:

1. **Gemini API Key Invalid:**
   ```
   ❌ [AI CORE] CRITICAL: Failed to initialize Gemini model
   ```
   → Verify `GEMINI_API_KEY` in `.env`

2. **Ollama Cloud Auth Fail:**
   ```
   ❌ Slow Path Error: Unauthorized
   ```
   → Verify `OLLAMA_API_KEY` in `.env`

3. **Model Not Available:**
   ```
   ❌ [RETRY] Attempting Ollama call (model: deepseek-v3.1:671b-cloud)...
   Error: model not found
   ```
   → Check model name in Ollama Cloud dashboard

---

## 📚 FILES PROVIDED

- `forensic_audit_report.md` - Full technical analysis
- `CORRECTED_ai_core.py` - Fixed AI core (Fixes #1, #2)
- `CORRECTED_main.py` - Fixed main (Fixes #3, #6)
- `CORRECTED_.env` - Fixed config (Fix #2)

**Replace the originals with these corrected versions.**
