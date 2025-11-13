# 🔐 ULTRA v3.0 - Przewodnik Panelu Administracyjnego

## Logowanie do Panelu Admin

### Krok 1: Dostęp do Panelu
Otwórz w przeglądarce: `http://localhost:5173/admin`

### Krok 2: Wprowadź Klucz Admin
W pole "Admin Key" wpisz klucz z pliku `backend/.env`:
```
ULTRA_DOJO_KEY_8a4f9b2c_qoder_ai_2025
```

### Krok 3: Zaloguj Się
Naciśnij **Enter** lub kliknij przycisk **Login**.

✅ **Sukces**: Zobaczysz panel z 4 zakładkami.

---

## 📊 Zakładki Panelu

### 1️⃣ **Tablica Feedbacku**
**Co pokazuje:** User feedback (thumbs up/down) z sesji sprzedażowych
- Grupowane automatycznie przez AI (Prompt 5)
- Analiza sentymentu
- Możliwość utworzenia Golden Standard z feedbacku

**Gdzie znajduje się:**
- Tab 1 (ikona 👍)
- Endpoint: `/api/v1/admin/feedback/grouped`

**Co zrobić jeśli pusty:**
Brak feedbacku oznacza, że użytkownicy nie używali jeszcze funkcji "thumbs up/down" w Conversation View.

---

### 2️⃣ **RAG Nuggets (Baza Wiedzy)**
**Co pokazuje:** Wszystkie "nuggets" wiedzy produktowej dla AI
- 101 istniejących nuggets ✅
- + 526 oczekujących na import (wymaga Gemini API key)

**Gdzie znajduje się:**
- Tab 2 (ikona 🧠)
- Endpoint: `/api/v1/admin/rag/list`
- Źródło danych: Qdrant vector database

**Jak importować:**
```bash
# 1. Wygeneruj nowy Gemini API key: https://aistudio.google.com/apikey
# 2. Zaktualizuj backend/.env:
GEMINI_API_KEY=YOUR_NEW_KEY_HERE

# 3. Uruchom import:
cd backend
python direct_import.py
```

**Oczekiwany rezultat:** 526 → 627 total nuggets

---

### 3️⃣ **Złote Standardy (Golden Standards)**
**Co pokazuje:** Przykładowe odpowiedzi sprzedażowe zatwierdzone przez ekspertów
- **370 Golden Standards** obecnie w bazie ✅
- Używane do treningu AI
- Zapisane w PostgreSQL + Qdrant

**Gdzie znajduje się:**
- Tab 3 (ikona ⭐)
- Endpoint: `/api/v1/admin/golden-standards/list`
- Źródło danych: PostgreSQL `golden_standards` table

**⚠️ WAŻNE:** To jest właściwy tab dla importowanych standardów!
(NIE "Tablica Feedbacku" - to różne rzeczy)

**Jak sprawdzić status:**
```bash
# Backend terminal:
psql -U ultra_user -d ultra_db
SELECT COUNT(*) FROM golden_standards;
# Wynik: 370 ✅
```

---

### 4️⃣ **Analityka (Analytics)**
**Co pokazuje:** 3 wykresy analityczne
- Playbook Effectiveness
- DISC Correlation
- Temperature Validation

**Gdzie znajduje się:**
- Tab 4 (ikona 📈)
- Endpoint: `/api/v1/admin/analytics/v1_dashboard`

---

## 🔧 Rozwiązywanie Problemów

### Problem: "Sesja wygasła" (401 Unauthorized)

**Objawy:**
- Czerwony komunikat 🔒 "Sesja wygasła"
- Dane nie ładują się w tabach

**Rozwiązanie:**
1. Kliknij przycisk **"Zaloguj ponownie"**
2. Wpisz ponownie klucz admin
3. Jeśli nie pomaga:
   ```javascript
   // W konsoli przeglądarki (F12):
   localStorage.clear();
   location.reload();
   ```

---

### Problem: "Brak feedbacku" w Tab 1

**To NIE błąd!**
Tab "Tablica Feedbacku" pokazuje **user feedback** (thumbs), nie Golden Standards.

**Gdzie są Golden Standards?**
➡️ **Tab 3: "Złote Standardy"** ⭐

---

### Problem: Slow Path się nie ładuje w Conversation

**Możliwe przyczyny:**
1. WebSocket nie zdążył się połączyć (fixed: wait time = 2.5s)
2. Ollama Cloud timeout
3. Gemini API key wygasł

**Sprawdzenie:**
```bash
# Backend logs:
# Szukaj linii:
✓ Ollama response received for S-XXX-XXX
📡 Sent Slow Path results via WebSocket
```

**Fallback:** Odśwież stronę - wyniki są w bazie danych i zostaną załadowane z `/api/v1/sessions/{id}`

---

## 📝 Kluczowe Komendy

### Backend Status
```bash
# Check PostgreSQL
psql -U ultra_user -d ultra_db -c "SELECT COUNT(*) FROM golden_standards;"

# Check Qdrant
curl http://localhost:6333/collections/ultra_rag_v1

# Restart backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Status
```bash
# Restart frontend
cd frontend
npm run dev

# Check localStorage (Browser Console F12)
localStorage.getItem('ultra_admin_key')
```

---

## 🎯 Szybki Test Po Naprawie

### ✅ Checklist:
1. [ ] Zalogować się do Admin Panel - klucz zapisany w localStorage
2. [ ] Odświeżyć stronę (F5) - nadal zalogowany ✅
3. [ ] Otworzyć Tab 1 "Feedback" - brak błędów ✅
4. [ ] Otworzyć Tab 2 "RAG" - pokazuje 101 nuggets ✅
5. [ ] Otworzyć Tab 3 "Złote Standardy" - pokazuje 370 wpisów ✅
6. [ ] Otworzyć Tab 4 "Analityka" - wykresy ładują się ✅
7. [ ] Wysłać wiadomość w Conversation - Slow Path się ładuje w ~30s ✅

---

## 📚 Dalsze Informacje

### API Endpoints Documentation
Pełna dokumentacja: `http://localhost:8000/docs` (Swagger UI)

### System Architecture
Zobacz: `FINAL_STATUS.md`, `SYSTEM_TEST_REPORT.md`

### Import Status
Zobacz: `IMPORT_STATUS.md`

---

## ⚡ Kontakt w Razie Problemów

Jeśli problem nadal występuje:
1. Sprawdź logi backendu (terminal Uvicorn)
2. Sprawdź konsolę przeglądarki (F12 → Console)
3. Wyślij screenshot błędu + logi

---

**Ostatnia aktualizacja:** 2025-01-11
**Wersja:** ULTRA v3.0
**Status:** ✅ Production Ready
