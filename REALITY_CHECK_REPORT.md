# 🛑 REALITY CHECK REPORT: ULTRA v3.1 Lite

**Data Audytu:** 2025-11-23
**Audytor:** Antigravity (Senior Code Auditor)
**Status:** PROTOTYPE (High Fidelity)

---

## 1. 🗺️ RZECZYWISTA MAPA ARCHITEKTURY

System działa w architekturze **Dual-Path** (Szybka/Wolna ścieżka) połączonej przez **WebSocket**. To nie jest tylko teoria, to faktycznie istnieje w kodzie.

### Przepływ Danych (The Happy Path):
1.  **User** wpisuje wiadomość w React (`Chat.tsx`).
2.  **WebSocket** (`main.py`) odbiera JSON.
3.  **Zapis**: Wiadomość trafia do SQLite (`ultra.db`).
4.  **Fast Path (Synchroniczna)**:
    *   Backend odpytuje "RAG" (patrz sekcja 3).
    *   Wysyła prompt do **Gemini 2.0 Flash**.
    *   Limit czasu: **2.8s** (sztywny `asyncio.wait_for`).
    *   Jeśli Gemini odpowie -> JSON leci do klienta.
    *   Jeśli timeout/błąd -> Leci hardcoded fallback ("Sprawdzam bazę...").
5.  **Slow Path (Asynchroniczna)**:
    *   Odpalana jako `BackgroundTasks`.
    *   Używa semafora (max 5 wątków).
    *   Wysyła potężny prompt do **DeepSeek v3.1** (przez Ollama/Proxy).
    *   Gdy (i jeśli) wróci -> Aktualizuje JSON w bazie i wysyła event `analysis_update` przez WebSocket.

### Frontend <-> Backend:
*   **Komunikacja**: WebSocket (`/ws/chat/{id}`) działa stabilnie.
*   **Stan**: React używa `zustand`.
*   **Feedback**: **FAKE**. Kliknięcie łapki w górę/dół robi `console.log`, nie wysyła nic do bazy ani nie doucza modelu.
*   **"Updating Models"**: **FAKE**. Animacja kończenia sesji to `setTimeout(1500ms)`. Nic się nie uczy.

---

## 2. 🧠 ANALIZA LOGIKI "AI" (BEZ ŚCIEMY)

### Fast Path (Gemini)
*   **Logika**: To jeden, dobrze napisany ("Ruthless") prompt w `ai_core.py`.
*   **Instrukcje**: Nakazuje zwracać JSON i zabrania "papugowania".
*   **Jakość**: Zależy w 100% od kontekstu (sliding window 10 wiadomości). Nie ma "pamięci długotrwałej".

### Slow Path (DeepSeek)
*   **Logika**: Jeden gigantyczny prompt proszący o wypełnienie 7 modułów (DNA, Psychometria, etc.).
*   **Ryzyko**: Jeśli model wypluje błędny JSON, cała analiza idzie do kosza (jest retry, ale to ryzykowne).
*   **Psychometria**: To halucynacja modelu na podstawie tekstu. Nie ma pod spodem żadnego silnika psychologicznego, po prostu LLM zgaduje "Ekstrawersja: 70" na podstawie tekstu.

### Pamięć (Memory)
*   **Typ**: Sliding Window (Ostatnie 10-20 wiadomości).
*   **Wady**: System nie pamięta niczego spoza bieżącej sesji. Nie ma Vector DB. Po przeładowaniu strony (jeśli nie ma ID w URL) tracisz wszystko.

---

## 3. 💾 FAKTYCZNY MODEL DANYCH I RAG

### RAG (Retrieval Augmented Generation) -> 🚨 FAKE / TOY
To największe rozczarowanie. Plik `rag.py`:
*   **Baza**: Hardcoded lista 6 słowników (`INITIAL_RAG_NUGGETS`) w kodzie Pythona.
*   **Szukanie**: `if keyword in query`. Proste dopasowanie tekstu.
*   **Embeddings**: **BRAK**. Nie ma wektorów, nie ma semantyki.
*   **Skutek**: Jeśli zapytasz o "koszty" a w bazie jest "cena", system tego nie znajdzie (chyba że LLM to naprawi z głowy).

### Baza Danych (SQLite)
*   **Schema**:
    *   `sessions`: ID, status.
    *   `messages`: Treść, rola, timestamp.
    *   `analysis_states`: **Jeden wielki JSON blob**.
*   **Walidacja**: Pydantic w kodzie, ale w bazie "wolna amerykanka".
*   **Zbieranie danych**: Zapisujemy wszystko, ale nie używamy tego do niczego (brak pętli zwrotnej/uczenia).

---

## 4. 🐛 JAKOŚĆ KODU I DŁUG TECHNICZNY

*   **Sekrety**: ✅ `GEMINI_API_KEY` i `OLLAMA_API_KEY` są w `.env`. Jest bezpiecznie.
*   **Spaghetti**:
    *   `main.py` (440 linii) robi się tłusty. Miesza routing, logikę biznesową i obsługę DB.
    *   Duplikacja: `ai.py` vs `ai_core.py`, `rag.py` vs `rag_engine.py`. Stary kod gnije obok nowego.
*   **Error Handling**:
    *   Fast Path: Solidny (`try...except` z fallbackiem).
    *   Slow Path: "Fire and forget". Jak padnie, to padnie cicho (z logiem w konsoli).
*   **Testy**: Są pliki `test_*.py`, ale wyglądają na skrypty do manualnego odpalania, a nie CI/CD.

---

## 5. 🚦 WERDYKT KOŃCOWY

**Słowem do kumpla przy piwie:**
> "Stary, frontend wygląda jak milion dolarów i gada szybko, bo Gemini robi robotę. Ale 'mózg' (RAG) to atrapa na sznurku – szuka po słowach kluczowych w liście 6 zdań. 'Analiza psychometryczna' to po prostu LLM zmyślający cyferki. To świetne demo dla inwestora, ale na produkcji przy 100 userach baza SQLite spuchnie, a brak prawdziwego RAG-a wyjdzie przy pierwszym trudnym pytaniu."

### Co działa? (✅)
*   Chat w czasie rzeczywistym (WebSocket).
*   Szybkie odpowiedzi (Gemini).
*   Piękny UI (React + Tailwind).
*   Podział na Fast/Slow path.

### Co wybuchnie? (💣)
*   **RAG**: Przy >10 dokumentach ten `if keyword in query` przestanie działać.
*   **Pamięć**: Brak kontekstu historycznego.
*   **Analiza**: DeepSeek jest wolny i drogi (jeśli to API), a JSON jest kruchy.

**Rekomendacja:** Natychmiastowa wymiana `rag.py` na prawdziwe Vector DB (nawet ChromaDB/FAISS) i posprzątanie duplikatów w `backend/`.
