# QUICK START - Uruchomienie Testu E2E

## 🚀 SZYBKIE URUCHOMIENIE (2 kroki)

### Terminal 1: Uruchom Backend
```powershell
cd c:\Users\barto\Downloads\copy-of-copy-of-copy-of-copy-of-copy-of-copy-of-copy-of-ultra-v3.0---cognitive-sales-engine\backend
python -m uvicorn main:app --reload --port 8000
```

Czekaj aż zobaczysz:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX]
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: Uruchom Test
```powershell
cd c:\Users\barto\Downloads\copy-of-copy-of-copy-of-copy-of-copy-of-copy-of-copy-of-ultra-v3.0---cognitive-sales-engine
python simulate_full_conversation.py
```

## ✅ SUKCES WYGLĄDA TAK:

```
🎉 SYSTEM ULTRA v3.1 DZIAŁA POPRAWNIE! 🎉

Fast Path (RAG): ✅ DZIAŁA
Slow Path (Psychometria): ✅ DZIAŁA

5. DOWÓD BAZY DANYCH
✅ Sesja zapisana w bazie danych
✅ Analysis state nie jest pusty
WERDYKT: Persistence działa poprawnie ✓
```

## ❌ PROBLEMY? Sprawdź:

1. **Backend nie uruchomiony:** `httpx.ConnectError`
   → Wykonaj "Terminal 1" powyżej

2. **Brak modułu websockets:** `ModuleNotFoundError`
   → `pip install websockets httpx`

3. **Slow Path timeout:** `⏳ Waiting for Slow Path analysis...`
   → Sprawdź `OLLAMA_API_KEY` w `.env`

4. **RAG nie działa:** `⚠️ Expected keywords NOT found`
   → Sprawdź Qdrant: `docker-compose up -d` lub `USE_MOCK_RAG=true`

---

**Czas trwania:** ~60 sekund (3 tury × ~20 sekund)
