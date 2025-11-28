# 🚀 ULTRA v3.0 - INSTRUKCJA URUCHOMIENIA
## "Dla Opornych" - Krok po Kroku

---

## ✅ WYMAGANIA WSTĘPNE

Przed uruchomieniem upewnij się że masz:
- [x] Python 3.11+ zainstalowany
- [x] Docker Desktop uruchomiony
- [x] Node.js 18+ zainstalowany
- [x] Plik `.env` z kluczami API (już skonfigurowany)

---

## 🔧 URUCHOMIENIE (4 KROKI)

### KROK 1: Uruchom Qdrant (baza wektorowa)

```powershell
# W głównym katalogu projektu
docker-compose up -d
```

Sprawdź czy działa:
```powershell
# Powinno pokazać "ultra_qdrant" jako Running
docker ps
```

---

### KROK 2: Uruchom Backend (FastAPI)

```powershell
# W głównym katalogu projektu
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Oczekiwany output:**
```
[RAG] OK - Embedding model loaded successfully
[RAG] OK - Connected to collection 'ultra_knowledge'
[AI CORE] OK - Gemini model initialized: models/gemini-2.0-flash
[ANALYSIS ENGINE] Initialized with model: 'deepseek-v3.1:671b-cloud'
INFO:     Application startup complete.
```

⚠️ **Zostaw to okno otwarte!**

---

### KROK 3: Uruchom Frontend (React)

**Otwórz NOWY terminal:**

```powershell
# W głównym katalogu projektu
npm install  # (tylko za pierwszym razem)
npm run dev
```

**Oczekiwany output:**
```
VITE v6.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
```

---

### KROK 4: Otwórz przeglądarkę

```
http://localhost:5173
```

---

## 🧪 TEST SYSTEMU

1. Kliknij **"START NEW SESSION"**
2. Wpisz: `Klient pyta o zasięg zimowy Tesli i porównuje do diesla`
3. Sprawdź:
   - ✅ **Fast Path** (Gemini) - odpowiedź w ~2-3s
   - ✅ **Slow Path** (DeepSeek) - 7 modułów w ~60-90s

---

## 📊 KONFIGURACJA (.env)

Twój plik `.env` powinien zawierać:

```env
# Gemini (Fast Path)
GEMINI_API_KEY=AIzaSy...

# Ollama Cloud (Slow Path)
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_API_KEY=f95f4...
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

# Qdrant (RAG)
QDRANT_URL=http://localhost:6333
```

---

## 🔴 ROZWIĄZYWANIE PROBLEMÓW

### Problem: Port 8000 zajęty
```powershell
# Zabij wszystkie procesy Python
taskkill /F /IM python.exe

# Lub użyj innego portu
python -m uvicorn backend.main:app --port 8001
```

### Problem: Qdrant nie działa
```powershell
docker-compose down
docker-compose up -d
```

### Problem: Brak danych RAG (puste wyniki)
```powershell
python backend/ingest_knowledge.py
```

### Problem: Emoji w logach (Windows)
```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m uvicorn backend.main:app --port 8000
```

---

## 📈 ARCHITEKTURA

```
┌─────────────────────────────────────────────────────────────┐
│                      ULTRA v3.0                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Frontend: React]  ◄──WebSocket──►  [Backend: FastAPI]     │
│       :5173                               :8000             │
│                                              │              │
│                        ┌─────────────────────┼──────────┐   │
│                        │                     │          │   │
│                        ▼                     ▼          ▼   │
│              ┌─────────────────┐   ┌──────────────┐         │
│              │   FAST PATH     │   │  SLOW PATH   │         │
│              │  Gemini 2.0     │   │  DeepSeek    │         │
│              │   < 3s          │   │   ~60s       │         │
│              └─────────────────┘   └──────────────┘         │
│                        │                                    │
│                        ▼                                    │
│              ┌─────────────────┐                            │
│              │     QDRANT      │                            │
│              │   886 vectors   │                            │
│              │     :6333       │                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ WERYFIKACJA GOTOWOŚCI

| Komponent | Jak sprawdzić | Oczekiwany wynik |
|-----------|---------------|------------------|
| **Qdrant** | `docker ps` | `ultra_qdrant` Running |
| **Backend** | `http://localhost:8000/docs` | Swagger UI |
| **Frontend** | `http://localhost:5173` | UI ładuje się |
| **Gemini** | Wyślij wiadomość | Odpowiedź w <3s |
| **DeepSeek** | Czekaj ~60s | 7 modułów w panelu |

---

## 🎉 SYSTEM GOTOWY DO WDROŻENIA!

**Data audytu:** 26.11.2025  
**Wersja:** ULTRA v3.0 (gemini-2.0-flash + deepseek-v3.1:671b-cloud)  
**Status:** ✅ PRODUKCYJNY

---

*Wygenerowano automatycznie przez ULTRA System Auditor*

