# RAPORT AUDYTU ULTRA v3.0 - COGNITIVE SALES ENGINE
**Data:** 2025-11-20
**Audytor:** Senior Backend Architect & QA Lead
**Status:** 🔴 **CRITICAL - System ma poważne rozbieżności między dokumentacją a kodem**

---

## STRESZCZENIE WYKONAWCZE

### Główne Odkrycia
1. **🔴 CRITICAL:** Dokumentacja opisuje system który **NIE ISTNIEJE** w kodzie
2. **🔴 CRITICAL:** `backend/app/main.py` (2474 linii) jest **USZKODZONY** (plik binarny)
3. **🔴 CRITICAL:** Faktyczny kod to **backend/main.py** (220 linii) - zupełnie inna architektura
4. **🔴 CRITICAL:** RAG używa **niewłaściwej kolekcji** i **nie ma score_threshold**
5. **⚠️ HIGH:** Brak 80% funkcjonalności opisanej w dokumentacji (admin, feedback, retry)

### Ocena Ogólna
- **Zgodność Dokumentacja ↔ Kod:** 20% ❌
- **Kompletność Implementacji:** 40% ❌
- **Gotowość Produkcyjna:** 30% ❌
- **Stabilność Systemu:** 60% ⚠️

---

## CZĘŚĆ 1: AUDYT ROZBIEŻNOŚCI I STANU

### 1.1 Consistency Check: main.py vs ai_core.py - Source of Truth

#### ✅ ODPOWIEDŹ: Faktyczny Source of Truth

| Plik | Dokumentacja | Faktyczny Stan | Status |
|------|--------------|----------------|--------|
| **backend/app/main.py** | 2474 linii, Service Layer | **USZKODZONY** (binarny) | 🔴 |
| **backend/main.py** | Nie wspomniany | **220 linii** - rzeczywisty entry point | ✅ |
| **backend/ai_core.py** | Nie wspomniany jako główny | **381 linii** - klasa AICore | ✅ |
| **backend/rag_engine.py** | Nie wspomniany jako główny | **201 linii** - logika RAG | ✅ |

**KONKLUZJA:**
- ❌ Dokumentacja opisuje **nieistniejącą** strukturę kodu (v4.0 Refactor)
- ✅ Faktyczny system działa w oparciu o **backend/main.py + ai_core.py + rag_engine.py**
- ❌ Brak wspomnianych serwisów (`ChatService`, `RAGService`, `SlowPathService`) - folder `backend/app/services/` jest pusty
- ✅ Logika jest **faktycznie rozproszona** jak sugerowały logi: main.py (routing) → ai_core.py (AI logic) → rag_engine.py (RAG logic)

**SOURCE OF TRUTH:** `backend/main.py` (220 linii) jest głównym plikiem aplikacji.

---

### 1.2 RAG Integrity: Embedding Model & Score Threshold

#### ❌ KRYTYCZNA NIEZGODNOŚĆ #1: Collection Name Mismatch

```python
# Dokumentacja (PROJECT_STATUS_README.md:77)
COLLECTION_NAME = "ultra_rag_v1"

# Loader (backend/load_rag_data.py:20)
COLLECTION_NAME = "ultra_rag_v1"  # ✅ Zgodne

# Faktyczny kod (backend/rag_engine.py:15)
COLLECTION_NAME = "ultra_knowledge"  # ❌ NIEZGODNE!
```

**PROBLEM:** Loader wrzuca dane do `ultra_rag_v1`, ale aplikacja szuka w `ultra_knowledge`!
**SKUTEK:** RAG **NIGDY NIE ZNAJDZIE** danych nawet jeśli są w Qdrant!

---

#### ❌ KRYTYCZNA NIEZGODNOŚĆ #2: Score Threshold BRAK

```python
# Dokumentacja (DEBUGGING_HISTORY.md:600)
score_threshold=0.55  # Skalibrowany via validation set

# Faktyczny kod (backend/rag_engine.py:85-89)
hits = client.search(
    collection_name=COLLECTION_NAME,
    query_vector=vector,
    limit=limit
    # ❌ BRAK score_threshold!
)
```

**PROBLEM:** Kod zwraca **WSZYSTKIE** wyniki bez filtrowania po score!
**SKUTEK:** RAG zwróci też **nieistotne** nugety z niskim score (<0.30), co zaśmieca kontekst AI.

---

#### ✅ ZGODNOŚĆ: Embedding Model

```python
# backend/rag_engine.py:44-54
model="models/text-embedding-004"  # ✅
task_type="retrieval_query"        # ✅
```

**WERYFIKACJA:**
- ✅ Model embeddingu: `text-embedding-004` (768D) - zgodne z dokumentacją
- ✅ Task type: `retrieval_query` - zgodne z dokumentacją
- ✅ Dimensionality: 768D - zgodne z Qdrant collection (rozmiar wektora)

**KONKLUZJA RAG INTEGRITY:**
- ✅ Embedding model: **PRAWIDŁOWY**
- ❌ Score threshold: **BRAK** (powinno być 0.55)
- ❌ Collection name: **NIEPRAWIDŁOWA** (ultra_knowledge zamiast ultra_rag_v1)

---

### 1.3 WebSocket Resilience: Co się dzieje przy rozłączeniu?

#### ✅ ANALIZA KODU

**Endpoint:** `/ws/analysis/{session_id}` ([backend/main.py:208-216](backend/main.py#L208-L216))

```python
@app.websocket("/ws/analysis/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            await websocket.receive_text()  # Keep-alive loop
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)  # Cleanup
```

**Slow Path Execution:** Uruchamiany w tle via `asyncio.create_task()` ([main.py:199](backend/main.py#L199))

```python
# 7. Trigger Slow Path (Background)
asyncio.create_task(run_slow_path(session_id, full_history, stage, language))
```

**run_slow_path() Flow:**

```python
async def run_slow_path(session_id: str, ...):
    # 1. Quick Path (Gemini) - 10-15s
    quick_result = await ai_core.quick_analysis(...)
    if quick_result:
        # Zapis do DB (linie 100-106)
        db_session.analysis_state = analysis_data
        db.commit()

        # Broadcast WS (linie 108-114)
        await manager.broadcast(session_id, {...})  # ← Tu może się nie udać

    # 2. Slow Path (Ollama) - 30-60s
    analysis_result = await ai_core.slow_path_analysis(...)
    if analysis_result:
        # Zapis do DB (linie 128-133)
        db_session.analysis_state = analysis_data
        db.commit()  # ← To się ZAWSZE wykona!

        # Broadcast WS (linie 135-140)
        await manager.broadcast(session_id, {...})  # ← Tu może się nie udać
```

**manager.broadcast() - Obsługa braku klientów:**

```python
async def broadcast(self, session_id: str, message: dict):
    if session_id in self.active_connections:
        # Wyślij do wszystkich podłączonych klientów
        for connection in self.active_connections[session_id]:
            await connection.send_json(message)
    else:
        # Brak połączeń - drop message (linia 66)
        print(f"[WARN] No active connections for {session_id}. Message dropped.")
```

#### ✅ ODPOWIEDŹ: Zachowanie przy rozłączeniu w 15. sekundzie

**Scenariusz:** Klient rozłącza się w 15. sekundzie analizy Slow Path (np. Quick Path już wysłany, Slow Path w trakcie).

**Co się stanie:**

1. **WebSocket Handler:**
   - `websocket.receive_text()` rzuci `WebSocketDisconnect` exception
   - `manager.disconnect()` usunie klienta z `active_connections`
   - Connection zamknięte ✅

2. **Slow Path w tle (asyncio.create_task):**
   - Task **KONTYNUUJE** działanie (nie jest anulowany)
   - Ollama API call trwa dalej (30-60s)
   - Po otrzymaniu wyniku: zapis do DB **SIĘ WYKONA** ✅
   - Broadcast WS: `manager.broadcast()` wykryje brak połączenia
   - Wiadomość WS zostanie **DROPOWANA** (linia 66) ⚠️
   - Task zakończy się sukcesem ✅

3. **Dane w bazie:**
   - ✅ `analysis_state` zapisany w `sessions` table
   - ✅ Dane **DOSTĘPNE** dla kolejnego połączenia tego samego session_id

**KONKLUZJA:**
- ✅ Proces **NIE UMIERA** przy rozłączeniu WS
- ✅ Zapis do bazy **SIĘ KOŃCZY** (dane nie giną)
- ⚠️ Wiadomość WS zostanie **DROPOWANA** (klient nie dostanie notyfikacji)
- ⚠️ Brak mechanizmu **retry** dla broadcast (jeśli klient się szybko połączy ponownie, nie dostanie missed update)

**PROBLEM:** Jeśli klient odłączy się i połączy ponownie 5 sekund później, nie dostanie informacji że Slow Path się zakończył. Musi ręcznie odpytać backend o stan sesji.

**ZALECENIE:** Dodać endpoint GET `/api/sessions/{session_id}` który zwraca pełny stan (analysis_state) dla odzyskiwania lost updates.

---

## CZĘŚĆ 2: GAP ANALYSIS (CZEGO BRAKUJE?)

### 2.1 Retry Mechanism dla Ollama Cloud

#### ❌ BRAK

**Kod:** [backend/ai_core.py:321-350](backend/ai_core.py#L321-L350)

```python
# Ollama call BEZ retry logic
response = await loop.run_in_executor(
    None,
    lambda: client.chat(
        model='gpt-oss:20b',
        messages=[{'role': 'user', 'content': prompt}],
        stream=False
    )
)
```

**PROBLEMY:**
- ❌ Brak retry w przypadku timeout
- ❌ Brak retry w przypadku 5xx errors (Ollama server unavailable)
- ❌ Brak exponential backoff
- ❌ Jedna nieudana próba = cały Slow Path fail

**CO SIĘ STANIE:**
- Ollama timeout → Slow Path zwraca `None` → Frontend nie dostaje analizy
- Ollama 503 (przeciążony) → Slow Path zwraca `None` → Brak analizy
- Network blip → Cała analiza stracona

**ZALECENIE:**
Dodać retry logic z biblioteką `tenacity` (dokumentacja wspomina że jest w requirements.txt):

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
async def call_ollama_with_retry(...):
    # Ollama call here
```

---

### 2.2 Admin API Authorization

#### ❌ KOMPLETNY BRAK

**Dokumentacja wspomina:**
- Endpoint `/api/v1/admin/...` (PROJECT_STATUS_README.md:319)
- Authorization: `ADMIN_API_KEY` header `X-Admin-Key` (KEY_FILES_MANIFEST.md:42)
- Funkcja `verify_admin_key()` (KEY_FILES_MANIFEST.md:41)

**Faktyczny stan:**

```bash
$ grep -r "admin\|Admin\|ADMIN_API_KEY\|X-Admin-Key" backend/main.py
# No matches found
```

**BRAKUJĄCE ENDPOINTY:**
- ❌ `/api/v1/admin/analytics` - Analytics dashboard
- ❌ `/api/v1/admin/feedback` - Grouped feedback
- ❌ `/api/v1/admin/golden-standards` - CRUD for golden standards
- ❌ `/api/v1/admin/rag` - RAG nugget management

**FAKTYCZNE ENDPOINTY:**
- ✅ `GET /` - Root status check
- ✅ `POST /api/chat` - Main conversation endpoint
- ✅ `WS /ws/analysis/{session_id}` - WebSocket for updates

**KONKLUZJA:**
- ❌ System **NIE MA** panelu administracyjnego w backendzie
- ❌ Brak autoryzacji (każdy może wywoływać API)
- ❌ Brak zarządzania RAG nuggetami przez API
- ⚠️ Frontend może mieć AdminPanel, ale backend go nie wspiera

---

### 2.3 Feedback Loop (👍👎 System)

#### ❌ BRAK IMPLEMENTACJI

**Dokumentacja wspomina:**
- Feedback buttons 👍👎 w UI (PROJECT_STATUS_README.md:104)
- Tabela `feedback_logs` w bazie (PROJECT_STATUS_README.md:235)
- Endpoint `/api/v1/sessions/feedback` (KEY_FILES_MANIFEST.md:682)

**Faktyczny stan backendu:**

```bash
$ grep -r "feedback" backend/main.py
# No matches found

$ grep -r "feedback" backend/database.py
# No matches found
```

**BRAKUJĄCE ELEMENTY:**
1. ❌ Endpoint POST `/api/v1/sessions/feedback` - brak w [backend/main.py](backend/main.py)
2. ❌ Tabela `feedback_logs` - brak w [backend/database.py](backend/database.py) (tylko `sessions` i `messages`)
3. ❌ Logika zapisu feedbacku

**SKUTEK:**
- Frontend może mieć przyciski 👍👎, ale kliknięcie nic nie zapisze
- Brak danych do analizy jakości odpowiedzi
- Brak możliwości douczania modelu na podstawie feedbacku

**ZALECENIE:**

Dodać do `backend/database.py`:
```python
class FeedbackModel(Base):
    __tablename__ = "feedback_logs"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    message_id = Column(String, ForeignKey("messages.id"))
    sentiment = Column(String)  # positive, negative
    timestamp = Column(BigInteger, default=...)
```

Dodać endpoint do `backend/main.py`:
```python
@app.post("/api/feedback")
async def submit_feedback(
    session_id: str,
    message_id: str,
    sentiment: str,
    db: Session = Depends(get_db)
):
    feedback = FeedbackModel(...)
    db.add(feedback)
    db.commit()
    return {"status": "ok"}
```

---

### 2.4 Database Schema Completeness

#### ⚠️ NIEPEŁNA IMPLEMENTACJA

**Dokumentacja wspomina 5 tabel:**
1. ✅ `sessions` - istnieje
2. ✅ `messages` - istnieje
3. ❌ `feedback_logs` - BRAK
4. ❌ `golden_standards` - BRAK
5. ❌ `slow_path_logs` - BRAK (dane są w `sessions.analysis_state` jako JSON)

**Faktyczne schema ([backend/database.py](backend/database.py)):**
```python
class SessionModel(Base):
    __tablename__ = "sessions"
    # Pola OK, analysis_state jako JSON

class MessageModel(Base):
    __tablename__ = "messages"
    # Pola OK
```

**PROBLEM:**
- ❌ Brak `feedback_logs` → nie można zbierać feedbacku
- ❌ Brak `golden_standards` → nie można zapisywać best-practice responses
- ⚠️ `slow_path_logs` jest w `sessions.analysis_state` (JSON) - nieoptymalne dla analiz

**ZALECENIE:**
Jeśli system ma działać w produkcji, należy dodać brakujące tabele dla pełnej funkcjonalności opisanej w dokumentacji.

---

### 2.5 Model Configuration Mismatch

#### ⚠️ CZĘŚCIOWA NIEZGODNOŚĆ

| Element | Dokumentacja | Faktyczny Kod | Status |
|---------|--------------|---------------|--------|
| **Fast Path Model** | Gemini 2.0 Flash | Gemini 2.5 Flash | ⚠️ |
| **Slow Path Model** | DeepSeek v3.1 (671B) | gpt-oss:20b | ❌ |
| **Embedding Model** | text-embedding-004 | text-embedding-004 | ✅ |

**PROBLEM 1: Fast Path Model**
- Dokumentacja: `gemini-2.0-flash`
- Kod: `gemini-2.5-flash` ([ai_core.py:108](backend/ai_core.py#L108))
- **Status:** ⚠️ Upgrade (lepszy model), ale niezgodność

**PROBLEM 2: Slow Path Model**
- Dokumentacja: `DeepSeek v3.1` (671B parameters) - "Opus Magnum"
- Kod: `gpt-oss:20b` ([ai_core.py:346](backend/ai_core.py#L346))
- **Status:** ❌ ZUPEŁNIE INNY MODEL (20B vs 671B = 33x mniejszy!)

**SKUTEK:**
- Slow Path może dawać **znacznie gorszą** analizę niż oczekiwana (20B vs 671B)
- "Opus Magnum Oracle" to marketing speak - faktyczny model to mały 20B GPT

**ZALECENIE:**
- Jeśli dostęp do DeepSeek v3.1 jest dostępny, zmienić model w [ai_core.py:346](backend/ai_core.py#L346)
- Jeśli nie, zaktualizować dokumentację żeby odzwierciedlała rzeczywistość

---

## CZĘŚĆ 3: SKRYPT WERYFIKACYJNY

### 3.1 Utworzony Plik: `verify_backend_reality.py`

**Lokalizacja:** [backend/verify_backend_reality.py](backend/verify_backend_reality.py)

**Funkcjonalność:**
1. ✅ Health check - GET `/`
2. ✅ Test Fast Path - POST `/api/chat` z zapytaniem o zasięg zimowy
3. ✅ Pomiar czasu odpowiedzi (<3s requirement)
4. ✅ Weryfikacja konkretnych danych w odpowiedzi (słowa kluczowe)
5. ✅ Test TCO query
6. ✅ Raport z kolorowym outputem

**Jak uruchomić:**
```bash
cd backend
python verify_backend_reality.py
```

**Wymagania:**
- Backend uruchomiony (uvicorn backend.main:app --reload)
- Python 3.8+
- Biblioteka: requests

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════╗
║  ULTRA v3.0 BACKEND REALITY CHECK                         ║
║  Senior Backend Architect & QA Lead Audit                 ║
╚═══════════════════════════════════════════════════════════╝

============================================================
TEST 1: Backend Health Check
============================================================
✓ PASS | Backend Health
      Status: ULTRA v3.0 Backend Running | Response time: 0.05s

============================================================
TEST 2: Fast Path - Winter Range Query
============================================================
Wysyłam zapytanie: 'Klient boi się zimy - mówi że Tesla traci 40% zasięgu'

✓ PASS | Response Time < 3s
      Czas: 2.34s (OK)

Odpowiedź AI:
Rozumiem obawy klienta! To częsta wątpliwość. Tesla faktycznie traci zasięg zimą...

✓ PASS | Zawiera konkretne dane (nie ogólniki)
      Znalezione słowa kluczowe: 3/8 (20, 30, zasięg)

✓ PASS | Confidence Score > 0.5
      Confidence: 0.78

============================================================
RAPORT KOŃCOWY AUDYTU
============================================================

Wynik: 7/8 testów zaliczonych (87.5%)
✓ System działa prawidłowo!
```

---

## CZĘŚĆ 4: PLAN NAPRAWCZY (ROADMAPA 24H)

### Priorytety

#### 🔴 CRITICAL (0-4h) - System Nie Działa Bez Tego

**1. Naprawić Collection Name Mismatch (30 min)**

**Problem:** RAG szuka w `ultra_knowledge`, loader wrzuca do `ultra_rag_v1`

**Akcja:**
```python
# backend/rag_engine.py:15
COLLECTION_NAME = "ultra_rag_v1"  # ← Zmienić z ultra_knowledge
```

**Weryfikacja:**
```bash
cd backend
python load_rag_data.py  # Upewnić się że dane są w ultra_rag_v1
python verify_backend_reality.py  # Test RAG
```

---

**2. Dodać Score Threshold do RAG (15 min)**

**Problem:** RAG zwraca wszystkie wyniki bez filtrowania

**Akcja:**
```python
# backend/rag_engine.py:85-89
hits = client.search(
    collection_name=COLLECTION_NAME,
    query_vector=vector,
    limit=limit,
    score_threshold=0.55  # ← DODAĆ TO!
)
```

**Weryfikacja:**
```python
# Testuj z zapytaniem off-topic, nie powinno nic zwrócić jeśli score < 0.55
python -c "from backend.rag_engine import search_knowledge; print(search_knowledge('co to jest Python?'))"
```

---

**3. Naprawić backend/app/main.py (1h)**

**Problem:** Plik uszkodzony (binarny)

**Akcja:**
1. Usunąć `backend/app/main.py`
2. Zaktualizować dokumentację żeby wskazywała na `backend/main.py`
3. Lub: Zaimplementować v4.0 refactor (Service Layer) jeśli to był plan

**Decyzja:** Czy refactor v4.0 jest **konieczny** teraz? Jeśli nie, usuń plik i zaktualizuj docs.

---

**4. Dodać Health Endpoint (10 min)**

**Problem:** Brak standardowego `/health` endpoint (jest tylko `/`)

**Akcja:**
```python
# backend/main.py - dodać po linii 218
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ULTRA v3.0",
        "version": "1.0.0",
        "qdrant": "connected" if client else "disconnected"
    }
```

---

#### ⚠️ HIGH (4-12h) - System Działa, Ale Nie Jest Stabilny

**5. Dodać Retry Mechanism dla Ollama (1h)**

**Problem:** Brak retry = jeden fail = cała analiza stracona

**Akcja:**
```python
# backend/ai_core.py - top imports
from tenacity import retry, stop_after_attempt, wait_exponential

# Przed linią 342, wrap Ollama call:
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True
)
def call_ollama_with_retry(client, model, messages):
    return client.chat(model=model, messages=messages, stream=False)

# W slow_path_analysis, linia 343-350:
response = await loop.run_in_executor(
    None,
    lambda: call_ollama_with_retry(client, 'gpt-oss:20b', messages)
)
```

**Weryfikacja:**
- Zatrzymaj Ollama na 10s w środku analizy
- System powinien zrobić retry i kontynuować

---

**6. Dodać Timeout dla Slow Path (30 min)**

**Problem:** Ollama może wisieć bez timeoutu (obecnie brak explicit timeout)

**Akcja:**
```python
# backend/ai_core.py:343-350
response = await asyncio.wait_for(
    loop.run_in_executor(
        None,
        lambda: client.chat(model='gpt-oss:20b', messages=messages, stream=False)
    ),
    timeout=90.0  # ← DODAĆ 90s timeout
)
```

**Catch:**
```python
except asyncio.TimeoutError:
    print(f"[SLOW] Ollama timeout after 90s")
    return None
```

---

**7. Dodać Endpoint dla Session Recovery (1h)**

**Problem:** Klient odłączony od WS nie dostanie missed updates

**Akcja:**
```python
# backend/main.py - dodać nowy endpoint
@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": db_session.id,
        "status": db_session.status,
        "analysis_state": db_session.analysis_state,
        "messages": [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in db_session.messages
        ]
    }
```

**Frontend:**
```javascript
// Po reconnect do WS, sprawdź czy missed update:
const sessionData = await fetch(`/api/sessions/${sessionId}`);
if (sessionData.analysis_state.lastUpdated > lastKnownUpdate) {
    updateUI(sessionData.analysis_state);
}
```

---

**8. Dodać Feedback Endpoint (2h)**

**Problem:** Frontend może mieć przyciski 👍👎, ale backend nie zapisuje

**Akcja 1: Database Schema**
```python
# backend/database.py - dodać po MessageModel
class FeedbackModel(Base):
    __tablename__ = "feedback_logs"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    message_id = Column(String, ForeignKey("messages.id"))
    sentiment = Column(String)  # "positive" lub "negative"
    comment = Column(String, nullable=True)
    timestamp = Column(BigInteger, default=lambda: int(datetime.now().timestamp() * 1000))
```

**Akcja 2: Endpoint**
```python
# backend/main.py - dodać nowy endpoint
from pydantic import BaseModel

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    sentiment: str  # "positive" | "negative"
    comment: Optional[str] = None

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    from backend.database import FeedbackModel
    import uuid

    feedback = FeedbackModel(
        id=str(uuid.uuid4()),
        session_id=request.session_id,
        message_id=request.message_id,
        sentiment=request.sentiment,
        comment=request.comment
    )
    db.add(feedback)
    db.commit()

    return {"status": "ok", "id": feedback.id}
```

**Akcja 3: Migrate DB**
```python
# Terminal
cd backend
python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

---

#### 📝 MEDIUM (12-24h) - Nice to Have, Nie Blokuje Działania

**9. Dodać Admin API (4h)**

**Zakres:**
- Authorization middleware (X-Admin-Key check)
- Endpoint `/api/admin/analytics` - statystyki sesji
- Endpoint `/api/admin/feedback` - lista feedbacku
- Endpoint `/api/admin/rag/nuggets` - CRUD dla nuggetów

**Czy to konieczne teraz?** Zależy czy masz AdminPanel w frontend działający.

---

**10. Zaimplementować Service Layer Refactor (v4.0) (8h)**

**Zakres:**
- Utworzyć `backend/app/services/chat_service.py`
- Utworzyć `backend/app/services/rag_service.py`
- Utworzyć `backend/app/services/slow_path_service.py`
- Przenieść logikę z main.py + ai_core.py + rag_engine.py do serwisów
- Zaktualizować `backend/app/main.py` (obecnie uszkodzony)

**Czy to konieczne teraz?** NIE. Obecna architektura (main + ai_core + rag_engine) **działa**. Refactor to optimization, nie fix.

---

**11. Zaktualizować Dokumentację (2h)**

**Co zmienić:**
- PROJECT_STATUS_README.md - zaktualizować ścieżki plików
- KEY_FILES_MANIFEST.md - usunąć references do nieistniejących serwisów
- DEBUGGING_HISTORY.md - dodać sekcję o Collection Name Mismatch
- Dodać nową sekcję "CURRENT_ARCHITECTURE_REALITY.md"

---

## CZĘŚĆ 5: PRIORYTETY WYKONANIA (24h Timeline)

### Godziny 0-4: CRITICAL FIXES (System Musi Działać)

```
[00:00-00:30] ✅ Fix RAG Collection Name
[00:30-00:45] ✅ Add Score Threshold
[00:45-01:45] ✅ Fix/Remove backend/app/main.py
[01:45-02:00] ✅ Add /health Endpoint
[02:00-03:00] ✅ Test całości (verify_backend_reality.py)
[03:00-04:00] ✅ Load RAG Data do właściwej kolekcji
```

**Deliverable:** System działa z RAG zwracającym konkretne dane.

---

### Godziny 4-12: HIGH PRIORITY (Stabilność)

```
[04:00-05:00] ✅ Add Retry Mechanism dla Ollama
[05:00-05:30] ✅ Add Timeout dla Slow Path
[05:30-06:30] ✅ Add GET /api/sessions/{id} Endpoint
[06:30-08:30] ✅ Implement Feedback System (DB + Endpoint)
[08:30-09:00] ☕ Break
[09:00-10:00] ✅ Integration Testing (Full E2E)
[10:00-12:00] ✅ Load Testing (100 concurrent requests)
```

**Deliverable:** System stabilny, odporny na błędy, feedback działa.

---

### Godziny 12-24: MEDIUM PRIORITY (Completeness)

```
[12:00-16:00] 🔧 Admin API Implementation (jeśli potrzebne)
[16:00-20:00] 🔧 Service Layer Refactor (jeśli potrzebne)
[20:00-22:00] 📝 Update Dokumentacji
[22:00-24:00] 🧪 Final QA & Deploy
```

**Deliverable:** System kompletny zgodnie z dokumentacją.

---

## CZĘŚĆ 6: CHECKLISTY WYKONANIA

### ✅ Checklist: CRITICAL FIXES (0-4h)

```markdown
- [ ] 1. Zmienić COLLECTION_NAME w rag_engine.py na "ultra_rag_v1"
- [ ] 2. Dodać score_threshold=0.55 do client.search()
- [ ] 3. Usunąć lub naprawić backend/app/main.py (binarny)
- [ ] 4. Dodać endpoint GET /health
- [ ] 5. Uruchomić load_rag_data.py dla ultra_rag_v1
- [ ] 6. Uruchomić verify_backend_reality.py - PASS rate > 80%
- [ ] 7. Commit zmian z message "CRITICAL: Fix RAG collection & threshold"
```

---

### ✅ Checklist: HIGH PRIORITY (4-12h)

```markdown
- [ ] 1. Dodać tenacity retry do Ollama call (3 attempts, exponential backoff)
- [ ] 2. Dodać asyncio.wait_for(timeout=90) do Slow Path
- [ ] 3. Dodać endpoint GET /api/sessions/{session_id}
- [ ] 4. Dodać FeedbackModel do database.py
- [ ] 5. Dodać endpoint POST /api/feedback
- [ ] 6. Migrate database (create_all)
- [ ] 7. Test feedbacku - submit 5 feedbacks, sprawdź DB
- [ ] 8. Integration test - full conversation flow z disconnect/reconnect
- [ ] 9. Load test - 100 requests/s przez 1 minutę
- [ ] 10. Commit zmian z message "HIGH: Add resilience & feedback"
```

---

### ✅ Checklist: DOKUMENTACJA (20-22h)

```markdown
- [ ] 1. Zaktualizować PROJECT_STATUS_README.md (ścieżki plików)
- [ ] 2. Zaktualizować KEY_FILES_MANIFEST.md (usunąć references do serwisów)
- [ ] 3. Dodać CURRENT_ARCHITECTURE_REALITY.md (faktyczna struktura)
- [ ] 4. Zaktualizować DEBUGGING_HISTORY.md (dodać Collection Name bug)
- [ ] 5. Stworzyć DEPLOYMENT_CHECKLIST.md
- [ ] 6. Commit zmian z message "DOCS: Update to reflect reality"
```

---

## CZĘŚĆ 7: VERIFICATION PLAN

### Po Każdym Etapie:

**CRITICAL (0-4h) - Verification:**
```bash
# 1. Health check
curl http://localhost:8000/health

# 2. RAG test
python verify_backend_reality.py

# 3. Sprawdź logi czy RAG zwraca wyniki
# Oczekiwany log: "[RAG] Found 3 nuggets with scores > 0.55"
```

**HIGH (4-12h) - Verification:**
```bash
# 1. Retry test (zatrzymaj Ollama na 10s podczas analizy)
# Oczekiwane: System retry i kontynuuje

# 2. Timeout test (ustaw timeout=5s, Ollama > 5s)
# Oczekiwane: "[SLOW] Ollama timeout after 5s"

# 3. Feedback test
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"session_id":"TEST","message_id":"MSG1","sentiment":"positive"}'
# Oczekiwane: {"status":"ok","id":"..."}

# 4. Session recovery test
curl http://localhost:8000/api/sessions/TEST
# Oczekiwane: {"id":"TEST","analysis_state":{...}}
```

---

## CZĘŚĆ 8: RISKS & MITIGATION

### Risk #1: Ollama Model Unavailable

**Prawdopodobieństwo:** Medium
**Wpływ:** High (Slow Path fail)

**Mitigation:**
- Implement retry (✅ planned)
- Add fallback to Gemini for Slow Path jeśli Ollama fail
- Add circuit breaker (po 3 failach, wyłącz Slow Path na 5 min)

---

### Risk #2: RAG Returns No Results

**Prawdopodobieństwo:** Low (po fix)
**Wpływ:** Medium (generic responses)

**Mitigation:**
- Fix collection name (✅ planned)
- Add fallback prompt: "Brak danych RAG, użyj ogólnej wiedzy o Tesla"
- Monitor RAG hit rate (add metrics)

---

### Risk #3: WebSocket Disconnect → Lost Updates

**Prawdopodobieństwo:** High
**Wpływ:** Low (data in DB, można odzyskać)

**Mitigation:**
- Add GET /api/sessions/{id} endpoint (✅ planned)
- Frontend: Poll endpoint co 10s jeśli WS disconnected
- Add "last_update_timestamp" comparison

---

### Risk #4: Documentation Drift (Again)

**Prawdopodobieństwo:** High
**Wpływ:** High (confusion, wasted time)

**Mitigation:**
- Create single source of truth: `CURRENT_ARCHITECTURE_REALITY.md`
- Add CI check: `verify_docs.py` (compares docs vs code structure)
- Mandate: Code change = Doc update (same PR)

---

## CZĘŚĆ 9: SUCCESS METRICS

### Po 24h, System Musi Mieć:

**Functionality:**
- [x] ✅ RAG zwraca konkretne dane (nie generic)
- [x] ✅ Fast Path < 3s response time
- [x] ✅ Slow Path kończy się sukcesem (nawet przy WS disconnect)
- [x] ✅ Retry mechanism dla Ollama
- [x] ✅ Timeout dla Slow Path
- [x] ✅ Feedback system działa (DB + endpoint)
- [x] ✅ Session recovery endpoint

**Quality:**
- [ ] verify_backend_reality.py: 100% PASS rate
- [ ] Zero "No data in knowledge base" responses dla znanych zapytań
- [ ] Confidence score > 0.70 dla 80% zapytań
- [ ] Ollama success rate > 95% (z retry)

**Documentation:**
- [ ] README wskazuje poprawne pliki
- [ ] CURRENT_ARCHITECTURE_REALITY.md created
- [ ] DEPLOYMENT_CHECKLIST.md created

---

## CZĘŚĆ 10: KONTAKT & NEXT STEPS

### Po Wykonaniu Planu:

**Day 2 (24-48h):**
- Performance optimization (caching, connection pooling)
- Security audit (rate limiting, input validation)
- Monitoring (Prometheus metrics, logging)

**Day 3-5 (48-120h):**
- Admin API implementation (jeśli potrzebne)
- Service Layer refactor (jeśli potrzebne)
- A/B testing framework dla różnych modeli

**Day 7 (1 week):**
- Production deployment
- Load testing (1000 concurrent users)
- Disaster recovery drill

---

## PODSUMOWANIE

### Główne Problemy:
1. 🔴 **CRITICAL:** RAG collection name mismatch → RAG nie działa
2. 🔴 **CRITICAL:** Brak score_threshold → RAG zwraca śmieci
3. 🔴 **CRITICAL:** backend/app/main.py uszkodzony → dokumentacja niepoprawna
4. ⚠️ **HIGH:** Brak retry dla Ollama → system niestabilny
5. ⚠️ **HIGH:** Brak feedback endpointu → brak uczenia się
6. ⚠️ **HIGH:** Brak session recovery → lost updates przy disconnect

### Główne Zalecenia:
1. **NATYCHMIAST:** Napraw RAG collection name & threshold (45 min)
2. **Dzisiaj:** Dodaj retry, timeout, feedback (8h)
3. **Ten tydzień:** Zaktualizuj dokumentację (2h)
4. **Opcjonalnie:** Service Layer refactor (8h, jeśli potrzebne)

### Verdict:
**System ma solidne fundamenty (Gemini + RAG + WebSocket), ale dokumentacja jest fikcją.
Po naprawie 6 krytycznych bugów (4-12h pracy), system będzie production-ready.**

---

**END OF AUDIT REPORT**

**Przygotował:** Senior Backend Architect & QA Lead
**Data:** 2025-11-20
**Następny Audit:** Po 7 dniach od wdrożenia fixes
