# ULTRA v3.0 — Wizja Strategiczna (FINAL)

Status: Zatwierdzony • Wersja: 3.0 • Dokument Matka Wizji

## 1. Streszczenie Zarządcze

ULTRA v3.0 to samodzielny, kognitywny silnik wsparcia sprzedaży. System zarządza trwałymi, anonimowymi sesjami klientów, analizuje naturalny język w czasie rzeczywistym i generuje głębokie wglądy w 7‑modułowym „Panelu Strategicznym (Opus Magnum)”.

- Fast Path (<2s): natychmiastowe sugestie odpowiedzi i pytań (lokalny LLM + RAG).
- Slow Path (<20s): pełna synteza kontekstu sesji (SOTA LLM) w jednym spójnym JSON dla 7 modułów panelu.

System łączy trzy metafory:
- „Mózg Bloomberga” — szybkość, dane, profesjonalna ergonomia.
- „Interfejs Tesli” — czystość, minimalizm, subtelne sygnały stanu.
- „Komputer Star Trek” — proaktywna, holistyczna inteligencja.

## 2. Model Operacyjny: Płynna Pętla Konwersacyjna

1. Inicjalizacja: rozpocznij nową sesję lub wznowienie po ID (anonimowe).
2. Kontekst: ustaw „Etap Podróży Klienta” (Odkrywanie/Analiza/Decyzja); AI może sugerować zmianę.
3. Input: sprzedawca wpisuje notatki w dzienniku konwersacji.
4. Fast Path: w <2s pojawia się „Sugerowana Odpowiedź” oraz „Pytania Pogłębiające”.
5. Slow Path: w tle powstaje kompletny JSON „Opus Magnum” (7 modułów).
6. Aktualizacja UI: panel odświeża się subtelną animacją; brak nachalnych banerów.
7. Zakończenie: status sesji (Sprzedaż/Utrata) zasila AI Dojo 2.0.

## 3. Panel Strategiczny „Opus Magnum” (Wyjście Slow Path)

Warstwa 1 (Fundament):
- M1: DNA Klienta — esencja, motywacja, styl komunikacji, dźwignie, red flags.
- M2: Wskaźniki Taktyczne (SSR 2.0) — temperatura zakupu, ryzyko churn, ryzyko „fun drive”.
- M3: Profil Psychometryczny — DISC, Big Five, wartości Schwartza.

Warstwa 2 (Wyrocznia):
- M4: Głębinowa Motywacja („WHY”) — kluczowy wgląd + cytaty dowodowe.
- M5: Predykcyjne Ścieżki — scenariusze z prawdopodobieństwem i rekomendacjami.
- M6: Strategiczny Playbook — krótkie „zagrania” (dialogi) powiązane z kontekstem.
- M7: Dynamiczne Wektory Decyzyjne — interesariusze, wpływ, wektor, fokus, strategia.

Każdy moduł posiada „confidence_score”, a całość „overall_confidence”.

## 4. Architektura Technologiczna (High‑Level)

- Frontend: React/Svelte; i18n (PL/EN) i design tokens dla spójności UI.
- Backend: FastAPI/Python; orkiestracja sesji, RAG i wywołań AI.
- AI:
  - Fast Path: szybki model (Gemini 1.5-flash) z kontekstem RAG.
  - Slow Path: SOTA LLM (np. DeepSeek 671B przez Ollama Cloud).
- Wiedza (RAG): Qdrant (10k+ nuggetów), filtrowanie po języku.
- Baza danych: PostgreSQL (sesje, logi, JSON Slow Path, feedback Dojo, golden standards).
- Hosting: Frontend na Vercel, Backend + DB + Qdrant na Railway (zero‑banerowe przejścia, Optimistic UI).

## 5. Interfejs UI/UX (Kluczowe Widoki)

Widok 1 — Dashboard Sesji:
- „+ Rozpocznij Nową Sesję”, pole „Wznów po ID”, „Twoje Ostatnie Sesje”.

Widok 2 — Live Conversation:
- Dziennik konwersacji z 👍/👎 dla Fast Path (👎 otwiera pole „co było nie tak?”).
- Selektor Etapu Podróży Klienta; sugestia AI może „delikatnie podświetlać” opcję.
- Panel Strategiczny (7 modułów) z subtelnym odświeżeniem i przyciskiem „🔄”.

Widok 3 — Panel Admina (AI Dojo 2.0):
- Tablica Feedbacku (grupowanie, standardy), Zarządzanie RAG (CRUD), Analityka Korelacji.

## 6. Zasady Priorytetu i Spójności

- Jedna synteza — wszystkie moduły i odpowiedzi muszą wynikać z tej samej
  spójnej analizy sesji (brak sprzeczności stylu vs playbook).
- Priorytet: SUPER‑BLUEPRINT i PEGT są nadrzędne wobec starszych zapisów.
- Konflikty: w przypadku rozbieżności, obowiązuje specyfikacja z dokumentów nadrzędnych.

## 7. Ewolucja i Dojrzałość

- Stan „Dnia Zero”: dane RAG i „Złote Standardy” w języku PL; system wspiera i18n.
- Rozbudowa: AI Dojo pozwala dodawać wiedzę (PL/EN) i podnosić jakość „Fast Path”.
- Testy UAT: weryfikują szybkość Fast Path, spójność Slow Path i pętle korekcyjne.

—
Dokument powstał przez konsolidację treści z BIG1.md i BIG2.md, ujednolicony i zsynchronizowany
z nadrzędnymi specyfikacjami: 01_SUPER_BLUEPRINT_FINAL.md oraz 02_PEGT_FINAL.md.