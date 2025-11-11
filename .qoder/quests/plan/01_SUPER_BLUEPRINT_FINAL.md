# SUPER-BLUEPRINT v1.1

# PROJEKT: ULTRA v3.0: Kognitywny Silnik Sprzedaży

# CEL: Kompletna specyfikacja dla qoder.ai (Koniec Fazy 1)

**Notatki Architekta (v1.2 – konsolidacja addendów v1.1–v1.6):**

- Wielojęzyczność (i18n) dla UI i danych (PL/EN) – utrzymane.
- Fast Path: Przejście na Google Gemini (`gemini-1.5-flash`) zamiast lokalnego Ollama (zgodnie z Addendum v1.1).
- Retry dla wywołań zewnętrznych (Gemini, Ollama Cloud) – mechanizm exponential backoff, maks. 3 próby.
- Admin Auth: Uproszczona autentykacja `X-Admin-Key` (zgodnie z decyzją Wizjonera).
- UI biblioteki referencyjne: wykresy `Recharts`, ikony `Heroicons`.
- Wchłonięto logikę AI Dojo Grouping (Prompt 5) oraz doprecyzowania analityki i i18n.

## SEKCJA 1: README.md / STRESZCZENIE PROJEKTU

### 1.1. Cel Projektu

Celem jest zbudowanie kompletnej, samodzielnej (standalone) aplikacji webowej "ULTRA v3.0". System ten działa jako kognitywny silnik wsparcia sprzedaży, zarządzający sesjami klientów i dostarczający sprzedawcy analizy AI w czasie rzeczywistym.

### 1.2. Nadrzędna Wizja

Aplikacja ma łączyć trzy metafory:

1. **"Mózg Bloomberga" (Logika):** Profesjonalne, szybkie, potężne narzędzie skupione na danych i wydajności.
2. **"Interfejs Tesli" (Estetyka):** Czysty, minimalistyczny, intuicyjny design (zgodny z `design_tokens.json`).
3. **"Komputer Star Trek" (AI):** Proaktywna, "magiczna" analitycznie sztuczna inteligencja.

### 1.3. Filary Architektoniczne

System opiera się na 4 Filarach, które muszą być zaimplementowane zgodnie z tą specyfikacją:

1. **Fast Path (Pętla <2s):** Natychmiastowe sugestie (Gemini 1.5‑flash + RAG).
2. **Slow Path (Pętla <20s):** Głęboka analiza (SOTA LLM 671B+).
3. **AI Dojo (Trening):** Interfejs Admina do trenowania AI na podstawie feedbacku.
4. **Dane (RAG):** Baza wektorowa (Qdrant) z wiedzą produktową i "Złotymi Standardami".

### 1.4. Stack Technologiczny (z Dok. 2)

- **Frontend:** React (lub Svelte)
- **Backend (Orkiestrator):** Python (FastAPI)
- **AI (Fast Path):** Google Gemini (`gemini-1.5-flash`), z logiką retry (tenacity)
- **AI (Slow Path):** Zewnętrzne API SOTA (np. Ollama Cloud dla DeepSeek 671B)
- **Baza Danych (Relacyjna):** PostgreSQL
- **Baza Danych (Wektorowa):** Qdrant

## SEKCJA 2: ARCHITEKTURA SYSTEMU I DANYCH

### 2.1. Nadrzędna Zasada: Separacja Ścieżek

KRYTYCZNE: Backend (Orkiestrator) nigdy nie wysyła odpowiedzi z "Fast Path" (Llama 8B) do "Slow Path" (DeepSeek 671B).

- **Przepływ Fast Path:** Frontend (Ostatnia Notatka) -> Backend -> Llama 8B (z RAG).
- **Przepływ Slow Path:** Frontend (Ostatnia Notatka) -> Backend (Zapis w PostgreSQL) -> Backend (Pobranie PEŁNEJ Historii z PostgreSQL) -> DeepSeek 671B.
Wniosek: "Mózg" (Slow Path) zawsze pracuje na czystej, pełnej i nie "zniekształconej" historii sesji.

### 2.2. Schemat Bazy Danych (PostgreSQL) - Wersja FINALNA (z Addendum v1.6)

`qoder.ai` musi zaimplementować następujące tabele:

`sessions`
- `session_id` (TEXT, Primary Key, np. 'S-PYR-334')
- `created_at` (TIMESTAMP WITH TIME ZONE)
- `ended_at` (TIMESTAMP WITH TIME ZONE, Nullable)
- `status` (TEXT, Nullable, 'Sprzedaż' / 'Utrata') -- (W7) Backend zapisuje status ('Sprzedaż'/'Utrata' lub 'Sale'/'Loss') w języku otrzymanym z frontendu.

`conversation_log`
- `log_id` (SERIAL, Primary Key)
- `session_id` (TEXT, Foreign Key -> sessions)
- `timestamp` (TIMESTAMP WITH TIME ZONE)
- `role` (TEXT, 'Sprzedawca' / 'FastPath' / 'FastPath-Questions')
- `content` (TEXT)
- `language` (TEXT, 'pl' / 'en')

`slow_path_logs`
- `log_id` (SERIAL, Primary Key)
- `session_id` (TEXT, Foreign Key -> sessions)
- `timestamp` (TIMESTAMP WITH TIME ZONE)
- `json_output` (JSONB)
- `status` (TEXT, 'Success' / 'Error')

`feedback_logs` (FINALNA DEFINICJA z Modułu O)
- `feedback_id` SERIAL PRIMARY KEY
- `session_id` TEXT NOT NULL REFERENCES sessions(session_id)
- `log_id_ref` INT NULL -- (W4) log_id_ref (INT NULL) to referencja do conversation_log.log_id (ID ocenionej sugestii AI)
- `feedback_type` TEXT NOT NULL CHECK (feedback_type IN ('up','down')) -- (Kluczowe dla F-3.1)
- `original_input` TEXT NOT NULL -- (Notatka sprzedawcy)
- `bad_suggestion` TEXT NOT NULL -- (Oceniona sugestia AI)
- `feedback_note` TEXT NOT NULL -- (Komentarz "Co było nie tak?")
- `language` TEXT NOT NULL CHECK (language IN ('pl','en'))
- `journey_stage` TEXT NULL CHECK (journey_stage IN ('Odkrywanie','Analiza','Decyzja'))
- `refined_suggestion` TEXT NULL -- (Nowa, poprawiona sugestia z F-2.3)
- `created_at` TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
- Indeksy: (`session_id`), (`language`), (`created_at` DESC)

`golden_standards` (FINALNA DEFINICJA z Modułu P)
- `gs_id` SERIAL PRIMARY KEY
- `category` TEXT NOT NULL -- (np. "Cena i Finansowanie")
- `trigger_context` TEXT NOT NULL -- (np. "Obiekcja: Elektryki są za drogie...")
- `golden_response` TEXT NOT NULL -- (Treść "złotej" odpowiedzi)
- `language` TEXT NOT NULL DEFAULT 'pl'
- `created_at` TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
- `updated_at` TIMESTAMP WITH TIME ZONE NULL
- Unikalność: `UNIQUE(trigger_context, language)`
- Indeksy: (`language`), (`category`), (`created_at` DESC)
- *(Instrukcja dla Qoder.ai: Skrypt seed.py musi mapować dane z `DATA_02_Golden_Standards.md` do tej struktury).*

### 2.3. Architektura Wielojęzyczności (i18n) *(NOWOŚĆ v1.1)*

1. **Statyczne UI:** Cały interfejs użytkownika (przyciski, etykiety) musi być renderowany z pliku `i18n_locales.json`. Frontend musi posiadać przełącznik (PL/EN).
2. **Dynamiczne Dane (RAG):** Baza Qdrant musi przechowywać dane z pliku `DATA_01_RAG.md`. Każdy "nugget" musi mieć metadane `language: 'pl'`.
3. **Dynamiczne Dane (Golden Standards):** Tabela `golden_standards` w PostgreSQL (patrz 2.2) przechowuje dane z `golden_standards_day_zero.json` z `language: 'pl'`.
4. **Logika API:** Wszystkie endpointy (zwłaszcza `/api/v1/sessions/send`) muszą przyjmować parametr `language` od frontendu.
5. **Logika Backendu:** Backend musi używać parametru `language` do filtrowania zapytań do Qdrant i PostgreSQL, aby Fast Path (Prompty 1, 2, 3) używał wiedzy i standardów w odpowiednim języku.
6. **AI Dojo:** Interfejs Admina (F-3.1, F-3.2) musi pozwalać na dodawanie/edycję wpisów RAG i Golden Standards *wraz z wyborem ich języka*.

### 2.4. Kontrakt API (Endpointy FastAPI)

`qoder.ai` musi zaimplementować następujące endpointy:

**Sesje Użytkownika (Widok 1 i 2):**

- `[POST] /api/v1/sessions/new` (z F-1.1): Tworzy nową sesję. Zwraca `session_id`.
- `[GET] /api/v1/sessions/{session_id}` (z F-1.2): Pobiera historię `conversation_log` i ostatni `slow_path_logs` dla danej sesji.
- `[POST] /api/v1/sessions/send` (z F-2.2): Główny endpoint Pętli. Odbiera (`session_id`, `user_input`, `journey_stage`, **`language`**). Zwraca natychmiast Fast Path JSON (z Prompt 1 i 2). Asynchronicznie uruchamia "Slow Path".
- `[POST] /api/v1/sessions/refine` (z F-2.3): Odbiera (`session_id`, `original_input`, `bad_suggestion`, `feedback_note`, **`language`**). Zapisuje w `feedback_logs`. Wywołuje "Prompt 3" i zwraca `refined_suggestion`.
- `[POST] /api/v1/sessions/retry_slowpath` (z F-2.5): Odbiera (`session_id`). Ręcznie uruchamia ponowienie "Slow Path" dla ostatniej notatki.
- `[POST] /api/v1/sessions/end` (z F-2.6): Odbiera (`session_id`, `final_status`). Aktualizuje `sessions.status`. -- (W26) Auth: Brak klucza Admina. Dostęp publiczny dla znanego ID sesji

**Panel Admina (Widok 3):**

- `[GET] /api/v1/admin/feedback/grouped` (z F-3.1): Zwraca JSON z pogrupowanymi `feedback_logs`.
  - Req (Query): `{ language: TLanguage }` -- (W2) Potwierdzenie: Req (Query): { language: TLanguage }
- `[GET] /api/v1/admin/feedback/details` (z F-3.1): Zwraca szczegóły dla danej grupy feedbacku.
  - Req (Query): `{ note: string, language: TLanguage }` -- (W5) Parametr to note (np. ?note=zbyt%20agresywne)
- `[POST] /api/v1/admin/feedback/create_standard` (z F-3.1): Odbiera (`trigger_context`, `golden_response`, **`language`**, **`category`**). Zapisuje w `golden_standards` ORAZ w Qdrant.
- `[GET] /api/v1/admin/rag/list` (z F-3.2): Zwraca listę nuggetów z Qdrant.
  - Req (Query): `{ language: TLanguage }`
- `[POST] /api/v1/admin/rag/add` (z F-3.2): Odbiera (formularz: Tytuł, Treść, Słowa Kluczowe, **`language`**). Tworzy embedding i zapisuje nowy nugget w Qdrant.
- `[DELETE] /api/v1/admin/rag/delete/{nugget_id}` (z F-3.2): Usuwa nugget z Qdrant.
- `[GET] /api/v1/admin/analytics/v1_dashboard` (z F-3.3): Zwraca JSON z danymi dla 3 wykresów v1.0.
  - Req (Query): `{ date_from?: string, date_to?: string, language?: TLanguage }` -- (W18) Req (Query): { date_from?: string, date_to?: string, language?: TLanguage }

**Walidacja Długości Inputu (Wymaganie Robustness):** -- (W11) Upewnij się, że walidacja (max 5000 znaków) jest jasno zdefiniowana.
Wszystkie endpointy przyjmujące `user_input` lub `feedback_note` (np. `/send`, `/refine`) muszą walidować długość po stronie backendu.
- Max długość: **5000 znaków**.
- W przypadku przekroczenia, zwróć błąd `400 Bad Request`: "Input too long. Maximum 5000 characters."

Wymóg autoryzacji Admin: wszystkie endpointy `/api/v1/admin/*` wymagają nagłówka `X-Admin-Key`. Klucz jest przechowywany w zmiennej środowiskowej `ADMIN_API_KEY` i porównywany z nagłówkiem przesyłanym przez frontend.

### 2.5. Zarządzanie Błędami (doprecyzowanie)

- Fast Path: gdy lokalny LLM/Gemini nie zwróci odpowiedzi lub wystąpi błąd, frontend **nie blokuje** pracy. Wyświetla komunikat w miejscu sugestii (z `i18n_locales.json`) i pozwala kontynuować wpisy.
- Slow Path: w razie błędu API SOTA panel przełącza się w stan komunikatu „Błąd Połączenia z AI” z przyciskiem `[ 🔄 ]` (patrz F‑2.5). Ponowienie wywołuje `POST /api/v1/sessions/retry_slowpath`.

## SEKCJA 3: SZCZEGÓŁOWA SPECYFIKACJA FUNKCJONALNA (Logika z Dok. 5)

*(Instrukcja* dla Qoder.ai: Zaimplementuj przełącznik Języka (PL/EN) i przełącznik Motywu (Jasny/Ciemny) w głównym layoutu aplikacji. Cały statyczny tekst musi pochodzić z `i18n_locales.json`. Wszystkie style muszą *pochodzić z `design_tokens.json`.)*

### SEKCJA 3.1: WIDOK 1 - DASHBOARD SESJI

Cel: Brama do systemu, "Panel Roboczy" minimalizujący tarcie.

- **Funkcja ID: F-1.1: Rozpocznij Nową Sesję**
    - Wizja: Natychmiastowe przejście (jak w "Tesli"). Kliknięcie `[ + Rozpocznij Nową Sesję ]` musi być błyskawiczne.
    - Logika: Frontend nie czeka na API. Używa "Optimistic UI":
        1. Frontend natychmiast generuje `session_id` po stronie klienta (np. `TEMP-12345`).
        2. Natychmiast przechodzi do "Widoku 2" z tym tymczasowym ID.
        3. W tle wysyła żądanie `POST /api/v1/sessions/new` (bez ID).
        4. Backend tworzy prawdziwe ID (np. `S-PYR-334`), zapisuje w `sessions` i odsyła je.
        5. Frontend w locie zamienia `TEMP-12345` na `S-PYR-334`.
    - Instrukcja dla Qoder.ai: Zaimplementuj "Optimistic UI". Przejście do Widoku 2 musi nastąpi przed otrzymaniem odpowiedzi z API.
    
    **Algorytm Tymczasowego ID (Frontend):**
    ```javascript
    const tempId = `TEMP-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    // Przykład: "TEMP-1699545678123-a3f9k"
    ```
    Walidacja Backendu: Endpoint `POST /api/v1/sessions/send` musi sprawdzać `session_id`. Jeśli `session_id` zaczyna się od `TEMP-`, backend wykonuje logikę F-1.1 (zamiana ID na docelowe, np. `S-PYR-334`) i kontynuuje. Wszystkie inne endpointy (np. `GET /api/v1/sessions/{id}`) muszą odrzucać ID zaczynające się od `TEMP-` z błędem `400 Bad Request`: "Temporary session ID not allowed."
    
    **Walidacja session_id (Logika TEMP-*)** -- (K8)
    - /api/v1/sessions/send: Musi akceptować ID zaczynające się od `TEMP-` (i zamieniać je na docelowe ID przy pierwszym zapisie).
    - /api/v1/sessions/retry_slowpath: Musi odrzucać `TEMP-` (błąd 400 "Temporary session ID not allowed").
    - /api/v1/sessions/end: Musi odrzucać `TEMP-` (błąd 400).
    - /api/v1/sessions/{session_id} (GET): Musi odrzucać `TEMP-` (błąd 400).
- **Funkcja ID: F-1.2: Wznów Sesję**
    - Wizja: Również natychmiastowe. Błąd: czerwona ramka + tekst.
    - Logika:
        1. Użytkownik wpisuje `S-PYR-334` i klika `[ Wznów ]`.
        2. Frontend natychmiast przechodzi do "Widoku 2" (z "Optimistic UI"), pokazując ekran ładowania wewnątrz "Dziennika Konwersacji".
        3. Wysyła `GET /api/v1/sessions/S-PYR-334`.
        4. Po otrzymaniu danych, wypełnia "Dziennik" i "Panel Strategiczny".
    - Obsługa Błędu: Jeśli GET zwróci 404, nie pokazuje modala. Natychmiast wraca do "Widoku 1", ustawia czerwoną ramkę (`border-red-500`) na polu input i pokazuje tekst błędu (z `i18n_locales.json`) pod spodem.
    - Instrukcja dla Qoder.ai: Zaimplementuj "Optimistic UI" dla przejścia ORAZ logikę obsługi błędu (powrót + czerwona ramka).
- **Funkcja ID: F-1.3: Lista "Twoje Ostatnie Sesje"**
    - Wizja: Opcja 2 (ID + Kontekst).
    - Logika:
        1. Gdy użytkownik jest w "Widoku 2", po wysłaniu pierwszej notatki (F-2.2), frontend zapisuje w `localStorage` obiekt: `{ id: 'S-PYR-334', context: 'Klient martwi się o zasięg...', timestamp: 1699545678123 }`. -- (W20) Format localStorage: { id: 'S-PYR-334', context: 'Klient martwi się...', timestamp: 1699545678123 }
        2. `localStorage` przechowuje listę (np. 10) takich obiektów.
        3. W "Widoku 1", frontend czyta `localStorage` i wyświetla listę klikalnych linków (np. `S-PYR-334 (Klient martwi się...)`).
        4. Kliknięcie linku wywołuje logikę F-1.2.
    - Instrukcja dla Qoder.ai: Użyj `localStorage` do przechowywania listy ostatnio używanych ID sesji wraz z pierwszą notatką jako kontekstem.

### SEKCJA 3.2: WIDOK 2 - LIVE CONVERSATION

Cel: Serce aplikacji. Pętla Konwersacyjna.

- **Funkcja ID: F-2.1: Etap Podróży Klienta**
    - Wizja: Logika "Star Trek" (Opcjonalny + Sugestia AI).
    - Logika:
        1. Po wejściu, etap domyślnie ustawia się na "Odkrywanie". Pole czatu jest od razu aktywne (zero tarcia).
        2. Sprzedawca może ręcznie zmienić etap w dowolnym momencie (klikając przyciski "Odkrywanie" / "Analiza" / "Decyzja"). Zmiana ta aktualizuje stan `journey_stage` wysyłany w F-2.2.
        3. Sugestia AI: JSON ze "Slow Path" (z F-2.2) będzie zawierał pole `suggested_stage`.
        4. Jeśli `suggested_stage` (np. "Analiza") różni się od aktywnego etapu (np. "Odkrywanie"), przycisk "Analiza" zaczyna minimalistycznie pulsować lub otrzymuje delikatne podświetlenie (użyj koloru `accent` z `design_tokens.json`). Kliknięcie go akceptuje sugestię.
    - Instrukcja dla Qoder.ai: Zaimplementuj domyślny stan, ręczną zmianę ORAZ logikę "podświetlenia" przycisku, gdy sugestia AI różni się od stanu frontendu.
- **Funkcja ID: F-2.2: Pętla Konwersacyjna (Send)**
    - Wizja: Opcja B (Natychmiastowość). System nigdy nie blokuje użytkownika.
    - Logika:
        1. Sprzedawca wpisuje notatkę i klika `[ SEND > ]`.
        2. Frontend (Optimistic UI):
            - Notatka natychmiast pojawia się w "Dzienniku Konwersacji" (z ikonką "analizowanie...").
            - Pole tekstowe natychmiast się czyści i jest gotowe na kolejny wpis.
        3. Backend (Równolegle): Frontend wysyła `POST /api/v1/sessions/send` z (`session_id`, `user_input`, `journey_stage`, `language`).
        4. Fast Path: Backend natychmiast zwraca Fast Path JSON (sugestie z Prompt 1 i 2). Frontend wyświetla je pod notatką sprzedawcy (zamieniając ikonkę "analizowanie...").
        5. Slow Path: Backend w tle uruchamia pełną analizę "Slow Path" (zapis do bazy, pobranie historii, wysłanie do SOTA LLM).
    - Instrukcja dla Qoder.ai: To jest kluczowy przepływ. Frontend musi użyć "Optimistic UI". Backend musi zwrócić odpowiedź "Fast Path" synchronicznie, jednocześnie uruchamiając "Slow Path" asynchronicznie.
    
    **Logika Rollback (Obsługa Błędu):** -- (K11)
    Jeśli frontend dodał notatkę do UI (Optimistic UI), ale żądanie `/send` zwróci błąd, frontend musi:
    1. Usunąć tymczasowy wpis (notatkę sprzedawcy) z Dziennika Konwersacji.
    2. Wyświetlić komunikat błędu (np. "Błąd wysyłania notatki" z i18n).
    3. (Opcjonalnie) Wypełnić pole czatu usuniętą treścią, aby użytkownik nie stracił wpisu.
- **Funkcja ID: F-2.3: Pętla Korekcyjna (Feedback 👎)**
    - Wizja: Opcja B + Pętla Korekcyjna.
    - Logika:
        1. Obok każdej sugestii AI (z "Fast Path") są ikony 👍/👎.
        2. Kliknięcie 👎 podświetla ikonę i natychmiast otwiera małe, opcjonalne pole tekstowe "Co było nie tak?".
        3. Gdy sprzedawca wpisze tam notatkę (np. "zbyt agresywne") i naciśnie Enter:
            - Frontend wysyła `POST /api/v1/sessions/refine` z (`session_id`, `original_input`, `bad_suggestion`, `feedback_note`, `language`).
            - Backend zapisuje to w `feedback_logs` (dla F-3.1) ORAZ wywołuje "Prompt 3 (Refinement)". -- (W17) Backend zapisuje to w feedback_logs (wraz z nową sugestią w polu refined_suggestion)
            - Backend natychmiast zwraca `refined_suggestion`.
        4. Frontend wyświetla tę nową, poprawioną sugestię w Dzienniku Konwersacji. -- (W29) Backend NIE zapisuje tej poprawionej sugestii w conversation_log, tylko w feedback_logs.refined_suggestion
    - Instrukcja dla Qoder.ai: Zaimplementuj pełną pętlę: Pokaż pole input po 👎, wyślij do endpointu /refine i wyświetl nową sugestię zwróconą z API.
- **Funkcja ID: F-2.4: Aktualizacja "Opus Magnum" (Slow Path)**
    - Wizja: Hybryda A+B. Subtelna, minimalistyczna animacja w stylu "Tesla".
    - Logika:
        1. Po 15-20 sekundach od F-2.2, "Slow Path" kończy pracę. Backend (przez WebSocket lub polling `GET /api/v1/sessions/{session_id}`) wysyła nowy `json_output` do frontendu.
        2. ZERO wyskakujących okienek i banerów.
        3. Panel Strategiczny (7 modułów) natychmiast aktualizuje swoje dane (paski postępu, tekst, wykresy).
        4. Cały kontener "Panelu Strategicznego" wykonuje jedną, subtelną animację (np. `transition: opacity` lub delikatny rozbłysk ramki), aby wizualnie zasygnalizować, że "wpłynęły nowe dane".
    - Instrukcja dla Qoder.ai: Użyj WebSocket (preferowane) lub pollingu do odbierania aktualizacji "Slow Path". Zaimplementuj subtelną animację CSS na kontenerze panelu po otrzymaniu nowych danych.
- **Funkcja ID: F-2.5: Błąd "Slow Path"**
    - Wizja: Opcja B (Przejrzysta).
    - Logika:
        1. Jeśli "Slow Path" zwróci błąd (API SOTA padło), backend zapisuje w `slow_path_logs` status `Error`.
        2. Frontend (przez WebSocket/polling) otrzymuje ten status.
        3. Cała zawartość "Panelu Strategicznego" (7 modułów) zostaje zastąpiona przez elegancki, ale wyraźny komunikat (z `i18n_locales.json`) o treści: "Błąd Połączenia z AI. [ 🔄 Spróbuj Ponownie ]".
        4. Przycisk `[ 🔄 ]` jest klikalny.
        5. Kliknięcie `[ 🔄 ]` wywołuje `POST /api/v1/sessions/retry_slowpath`.
    - Instrukcja dla Qoder.ai: Zaimplementuj stan błędu dla "Panelu Strategicznego" i podłącz przycisk ponowienia do nowego endpointu /retry_slowpath.
- **Funkcja ID: F-2.6: Zakończ Sesję**
    - Wizja: Opcja B (Minimalistyczny Modal "Tesli").
    - Logika:
        1. Użytkownik klika `[ 🗂️ Zakończ i Zapisz Sesję ]`.
        2. Pojawia się minimalistyczny modal (styl "Tesla/iPhone", użyj kolorów `surface` i `text_primary` z `design_tokens.json`).
        3. Modal ma tytuł (z `i18n_locales.json`) i dwa przyciski (z `i18n_locales.json`): `[ Sprzedaż Zakończona ]` / `[ Kontakt Utracony ]`.
        4. Kliknięcie przycisku (np. Sprzedaż Zakończona) wysyła `POST /api/v1/sessions/end` z (`session_id`, `final_status: 'Sprzedaż'`).
        5. Po pomyślnej odpowiedzi API, modal znika, a frontend natychmiast wraca do "Widoku 1 (Dashboard Sesji)".
    - Instrukcja dla Qoder.ai: Zaimplementuj modal z dwoma przyciskami. Przejście do Widoku 1 następuje dopiero po pomyślnym zapisaniu statusu przez API.

#### Wizualizacja modułów (UI/UX)

- M1: listy tekstowe (podsumowanie, dźwignie, red flags).
- M2: paski postępu (temperatura), etykiety kolorystyczne (ryzyko), przyciski etapu.
- M3: tekst + wykres radarowy (DISC).
- M4: wyróżniony blok „Kluczowy Wgląd”.
- M5: klikalne karty scenariuszy z prawdopodobieństwem i rekomendacjami.
- M6: karty „Playbook” z ikoną kopiowania.
- M7: lista wektorów decyzyjnych (ikony interesariuszy).

### SEKCJA 3.3: WIDOK 3 - PANEL ADMINA (AI DOJO 2.0)

Cel: Centrum treningowe dla "Mistrza Sprzedaży" (Admina).

- **Funkcja ID: F-3.1: Tablica Feedbacku**
    - Wizja: Opcja A (Styl "Inbox"). Profesjonalny interfejs do pracy z danymi.
    - Logika:
        1. Admin wchodzi na stronę. Frontend wywołuje `GET /api/v1/admin/feedback/grouped`.
        2. Wyświetla listę pogrupowanych błędów (np. `[5] "Zbyt agresywne"`).
        3. Kliknięcie grupy wywołuje `GET /api/v1/admin/feedback/details?note=zbyt agresywne`.
        4. Wyświetla listę 5 konkretnych przypadków (kontekst, zła sugestia, feedback).
        5. Admin klika przypadek, widzi pole `[ Wpisz "Złoty Standard" ]`, `[ Wybierz Język (PL/EN) ]` wpisuje idealną odpowiedź i klika `[ Zatwierdź ]`. -- (W13) Formularz zawiera pole Category (np. dropdown: "Cena", "Zasięg", "Inne").
        6. Frontend wysyła `POST /api/v1/admin/feedback/create_standard` z (`trigger_context`, `golden_response`, `language`). -- (W28) Backend musi obsłużyć to transakcyjnie: jeśli zapis do Qdrant się nie powiedzie, zapis do PostgreSQL musi zostać wycofany (rollback).
    - Instrukcja dla Qoder.ai: Zaimplementuj interfejs Master-Detail (3-kolumnowy) do obsługi tej logiki. Dodaj pole wyboru języka. Backendowy endpoint /create_standard musi zapisywać zarówno w PostgreSQL (`golden_standards`) jak i w Qdrant (aby natychmiast zasilić Filar 4).
- **Funkcja ID: F-3.2: Zarządzanie Wiedzą RAG**
    - Wizja: v1.0 Opcja B (Interfejs "Bloomberg"). Solidny formularz.
    - Logika:
        1. Admin wchodzi do zakładki "Zarządzanie Wiedzą".
        2. Frontend wywołuje `GET /api/v1/admin/rag/list` i wyświetla tabelę nuggetów z Qdrant (z opcją DELETE).
        3. Admin klika `[ + Dodaj Nowy Nugget ]`. Otwiera się modal (styl "Tesla").
        4. Modal zawiera formularz: Tytuł, Treść (JSON/Markdown), Słowa Kluczowe, **Wybór Języka (PL/EN)**.
        5. Kliknięcie `[ Zapisz ]` wysyła `POST /api/v1/admin/rag/add` z danymi formularza.
        6. Backend (FastAPI) tworzy embedding z Treści i zapisuje go w Qdrant (wraz z metadaną `language`).
    - Instrukcja dla Qoder.ai: Zaimplementuj pełny interfejs CRUD dla bazy Qdrant. Backendowy endpoint /add musi zawierać logikę generowania embeddingów (np. przy użyciu `sentence-transformers`). Dodaj pole wyboru języka do formularza.
    - *(Instrukcja dla Qoder.ai: Przy pierwszym uruchomieniu załaduj dane z `rag_day_zero_tesla.json` do Qdrant, ustawiając `language`='pl' dla każdego wpisu.)*
- **Funkcja ID: F-3.3: Analiza Korelacji**
    - Wizja: v1.0 Fazowe podejście do Opcji B.
    - Logika:
        1. Admin wchodzi do zakładki "Analityka".
        2. Frontend wywołuje jeden endpoint: `GET /api/v1/admin/analytics/v1_dashboard`.
        3. Backend (FastAPI) wykonuje 3 złożone zapytania do PostgreSQL, analizując dane JSONB z `slow_path_logs` i korelując je ze statusem z tabeli `sessions`. -- (K13) Backend musi wykonać 3 zapytania SQL (lub ekwiwalenty ORM) do analizy JSONB:
        
        **Wykres 1 (Efektywność Playbooków):**
        `SELECT jsonb_array_elements(json_output->'modules'->'strategic_playbook'->'plays')->>'title' as playbook_title, COUNT(*) as usage_count FROM slow_path_logs ... GROUP BY playbook_title ...`
        
        **Wykres 2 (Korelacja DISC):**
        `SELECT json_output->'modules'->'psychometric_profile'->'dominant_disc'->>'type' as disc_type, sessions.status, COUNT(*) as count FROM slow_path_logs JOIN sessions ... WHERE sessions.status IS NOT NULL GROUP BY disc_type, sessions.status ...`
        
        **Wykres 3 (Walidacja Temperatury):**
        `SELECT (json_output->'modules'->'tactical_indicators'->'purchase_temperature'->>'value')::int as temperature, sessions.status, COUNT(*) as count FROM slow_path_logs JOIN sessions ... WHERE sessions.status IS NOT NULL GROUP BY temperature, sessions.status ...`
        
        Zwracany JSON:
        ```json
        {
          "chart1_data": [ ... ], // Wynik Query 1
          "chart2_data": [ ... ], // Wynik Query 2
          "chart3_data": [ ... ]  // Wynik Query 3
        }
        ```
        4. Backend zwraca jeden duży JSON sformatowany dla 3 wykresów.
        5. Frontend (React) używa biblioteki (np. Recharts) do narysowania 3 predefiniowanych wykresów (Efektywność Playbooków, Korelacja DISC, Walidacja Temperatury).
    - Instrukcja dla Qoder.ai: Frontend musi użyć biblioteki do wykresów. Backend musi zaimplementować złożoną logikę agregacji danych z PostgreSQL (analiza JSONB). Rozważ cache'owanie tego endpointu.

## SEKCJA 4: STRATEGIA PROMPTÓW AI (AIPS) (z Dok. 4)

`qoder.ai` musi zaimplementować logikę wywoływania poniższych promptów. Prompty są celowo po angielsku dla maksymalnej kompatybilności z LLM, ale `language` w kontekście (PL/EN) poinformuje je, w jakim języku mają odpowiadać.

### 4.1. Prompt 1 (Fast Path - Sugerowana Odpowiedź z RAG)

 - **Model:** Gemini 1.5‑flash
- **Treść:**
    
    ```
    You are a world-class Tesla sales ambassador. Your task is to generate one concise "Suggested Response" based on the seller's last note, using the provided "Relevant Facts". Be empathetic and weave in the fact naturally. Respond ONLY in JSON format. Respond in the language defined by the 'language' tag.
    
    Context:
    - Language: {{language}} (e.g., 'pl' or 'en')
    - Last Seller Note: {{last_seller_input}}
    - Relevant Fact (from RAG): {{relevant_nugget_content}}
    
    Respond ONLY in this JSON format:
    { "suggested_response": "string (Your generated response in the correct language)" }
    
    ```
    

### 4.2. Prompt 2 (Fast Path - Pytania Pogłębiające - SPIN)

 - **Model:** Gemini 1.5‑flash
- **Treść:**
    
    ```
    You are a SPIN methodology sales analyst. Your task is to generate 3 open-ended follow-up questions based on the last note. The questions should aim to uncover "Problems" (P) and "Implications" (I). Respond ONLY in JSON format. Respond in the language defined by the 'language' tag.
    
    Context:
    - Language: {{language}}
    - Last Seller Note: {{last_seller_input}}
    
    Respond ONLY in this JSON format:
    { "suggested_questions": ["string (Question 1)", "string (Question 2)", "string (Question 3)"] }
    
    ```
    

### 4.2.1. Logika Łączenia Fast Path (Kluczowe) -- (W14 i K1)

Backend (Orkiestrator) musi wywołać Prompt 1 i Prompt 2 *równolegle* (lub sekwencyjnie). Następnie musi scalić ich wyniki w JEDEN JSON zgodny z definicją Endpointu 3 (PEGT Moduł 3.2):

```json
{
  "status": "success",
  "data": {
    "suggested_response": prompt_1_result["suggested_response"],
    "suggested_questions": prompt_2_result["suggested_questions"]
  }
}
```

### 4.3. Prompt 3 (Fast Path - Refinement / Korekta) (z F-2.3)

 - **Model:** Gemini 1.5‑flash
- **Treść:**
    
    ```
    You are a Sales Assistant who just made a mistake. Your task is to IMMEDIATELY correct your suggestion based on the seller's feedback. Be humble and precise. Respond ONLY in JSON format. Respond in the language defined by the 'language' tag.
    
    Context:
    - Language: {{language}}
    - Original Seller Note: {{original_seller_input}}
    - Your Bad Suggestion: {{bad_suggestion}}
    - Seller Feedback (Criticism): {{feedback_note}}
    
    Task: Generate a new, refined "Suggested Response" that addresses the criticism.
    
    Respond ONLY in this JSON format:
    { "refined_suggestion": "string (Your new, refined suggestion in the correct language)" }
    
    ```
    

### 4.4. Meta-Prompt "Slow Path" v1.1 (z Dok. 4)

- **Model:** SOTA LLM (np. DeepSeek 671B)
- **Treść:**
    
    ```
    You are the "Opus Magnum" Oracle – a holistic sales psychologist and strategist for Tesla sales. Your mission: Analyze the entire client session in ONE cohesive synthesis, then generate a complete Strategic Panel for the seller. Ensure ALL modules derive from this single, unified client understanding – no contradictions.
    
    Core Principles:
    - Base everything on linguistic patterns, objections, and intents in the history.
    - Tailor to Tesla context: Emphasize TCO, innovation, safety, ecosystem.
    - Incorporate Journey Stage to filter outputs.
    - Output MUST be ONE complete, valid JSON object. Self-validate.
    
    Context:
    - Language: {{language}} (Respond in this language)
    - Session History: {{session_history}} (Full chat log from PostgreSQL).
    - Journey Stage: {{journey_stage}} (W9) Pobierz ostatni journey_stage zapisany w conversation_log dla tej sesji (e.g., "Analysis").
    - Relevant Knowledge: {{nuggets_context}} (W21) Top 3 trafienia z RAG, połączone "---", max 2000 znaków (Key Tesla facts from RAG, filtered by language).
    
    Output ONLY this exact JSON structure. No additional text.
    {
      "overall_confidence": number (0-100),
      "suggested_stage": "string (Odkrywanie/Analiza/Decyzja or Discovery/Analysis/Decision)",
      "modules": {
        "dna_client": {
          "holistic_summary": "string",
          "main_motivation": "string",
          "communication_style": "string",
          "key_levers": [{"argument": "string", "rationale": "string"}],
          "red_flags": ["string"],
          "confidence_score": number
        },
        "tactical_indicators": {
          "purchase_temperature": {"value": number, "label": "string"},
          "churn_risk": {"level": "Low/Medium/High", "percentage": number, "reason": "string"},
          "fun_drive_risk": {"level": "Low/Medium/High", "percentage": number, "reason": "string"},
          "confidence_score": number
        },
        "psychometric_profile": {
          "dominant_disc": {"type": "string (one of: D, I, S, C)", "rationale": "string"},
          "big_five_traits": {
            "openness": {"level": "High/Medium/Low", "score": number},
            "conscientiousness": {"level": "High/Medium/Low", "score": number},
            "extraversion": {"level": "High/Medium/Low", "score": number},
            "agreeableness": {"level": "High/Medium/Low", "score": number},
            "neuroticism": {"level": "High/Medium/Low", "score": number}
          },
          "schwartz_values": [{"value": "string", "rationale": "string"}],
          "confidence_score": number
        },
        "deep_motivation": {
          "key_insight": "string",
          "evidence_quotes": ["string"],
          "tesla_hook": "string",
          "confidence_score": number
        },
        "predictive_paths": {
          "paths": [{"path": "string", "probability": number, "recommendations": ["string"]}],
          "confidence_score": number
        },
        "strategic_playbook": {
          "plays": [{"title": "string", "trigger": "string", "content": ["Seller: string"], "confidence_score": number}],
          "confidence_score": number
        },
        "decision_vectors": {
          "vectors": [{"stakeholder": "string", "influence": "string", "vector": "string", "focus": "string", "strategy": "string", "confidence_score": number}],
          "confidence_score": number
        }
      }
    }

    IMPORTANT: You MUST always include "suggested_stage" in your response, even if confidence is low. -- (W23)

    ```

### 4.5. Prompt 5 (Fast Path – AI Dojo Feedback Grouping)

- **Model:** Gemini 1.5‑flash
- **Treść:**

    ```
    You are a world-class Sales Master Analyst. Your task is to analyze a raw list of feedback notes from sellers and group them into logical themes. Keep theme names short (2–3 words). Respond ONLY in JSON. Respond in the language defined by 'language'.

    Context:
    - Language: {{language}}
    - Feedback Notes: [{{list_of_feedback_notes}}]

    Respond ONLY in this JSON format:
    {
      "groups": [
        { "theme_name": "string", "count": number, "representative_note": "string" }
      ]
    }
    ```
    
*(W15) Ten prompt jest wywoływany synchronicznie przez endpoint [GET] /api/v1/admin/feedback/grouped. Backend pobiera listę feedback_note z bazy, wysyła do Gemini (Prompt 5) i zwraca pogrupowane wyniki.*
    

## SEKCJA 5: PLAN HOSTINGU I WDROŻENIA (z Dok. 2)

`qoder.ai` musi wygenerować kod zoptymalizowany pod kątem następującego planu wdrożenia na darmowych planach PaaS:

- **Krok 1 (Frontend):**
    - Kod React zostanie umieszczony w repozytorium GitHub.
    - Repozytorium zostanie połączone z **Vercel**.
    - Vercel automatycznie zbuduje i wdroży aplikację.
- **Krok 2 (Backend, Bazy Danych):**
    - Użyjemy platformy **Railway.app**.
    - W jednym projekcie Railway uruchomimy 3 usługi:
        1. Usługa Backendu (FastAPI): Wdrożona z repozytorium GitHub.
        2. Usługa Bazy Danych: Dodatek "PostgreSQL".
        3. Usługa Bazy Wektorowej: Dodatek "Qdrant".
- **Krok 3 (Konfiguracja):**
    - Frontend (Vercel) zostanie skonfigurowany (poprzez zmienne środowiskowe) tak, aby wysyłał zapytania API do publicznego adresu URL Backendu (Railway).
    - Backend (Railway) zostanie skonfigurowany (poprzez zmienne środowiskowe) aby łączyć się z PostgreSQL i Qdrant (używając ich wewnętrznych adresów w Railway).
    - Klucze API (Gemini: `GEMINI_API_KEY`, Ollama Cloud: `OLLAMA_API_KEY`) oraz token Admina (`ADMIN_API_TOKEN`) muszą być zarządzane wyłącznie przez zmienne środowiskowe.

## SEKCJA 6: KRYTYCZNE PLIKI ZALEŻNOŚCI

`qoder.ai` musi użyć następujących 4 plików .json jako danych startowych (Day Zero) dla aplikacji.

1. **DATA_01_RAG.md** (zawiera `rag_day_zero_tesla.json`) -> Do załadowania do bazy Qdrant (z metadaną `language: 'pl'`). **Krytyczne:** Plik musi być czystym JSON (zaczynać się od `[`), bez żadnych nagłówków Markdown.
2. **`golden_standards_day_zero.json`** -> Do załadowania do bazy PostgreSQL, tabela `golden_standards` (z `language: 'pl'`).
3. **`design_tokens.json`** -> Do użycia jako źródło stylów (kolory, czcionki, motywy) dla frontendu.
4. **`i18n_locales.json`** -> Do użycia jako źródło dla *całego* statycznego tekstu w interfejsie.