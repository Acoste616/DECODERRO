# Plan Egzekucji i Gotowości Technicznej (PEGT) v1.0

Dokument ten uzupełnia SUPER-BLUEPRINT v1.1 o niskopoziomowe decyzje techniczne i sekwencję budowy, niezbędne do pomyślnej implementacji przez qoder.ai.

1. Moduł 1: Sekwencja Budowy (Instructional Flow)
qoder.ai otrzyma instrukcje budowy systemu w następującej, ścisłej kolejności, aby zapewnić stabilność i możliwość testowania na każdym etapie:

Krok 1: Infrastruktura i Zależności: Zdefiniowanie requirements.txt (Python), package.json (React) oraz plików konfiguracyjnych dla hostingu (Railway/Vercel).

Krok 2: Schematy Danych i API (Contracts First): Zbudowanie tylko modeli Pydantic (Backend) i interfejsów TypeScript (Frontend) dla wszystkich 10+ endpointów (zdefiniowanych w Module 3).

Krok 3: Inicjalizacja Danych ('Seeding'): Zbudowanie jednorazowego skryptu seed.py (zdefiniowanego w Module 2) do zasilenia baz danych danymi z plików .json.

Krok 4: Backend (Szkielet + Zaślepki 'Mocks'): Zbudowanie wszystkich endpointów API, które na tym etapie zwracają fałszywe (mockowane) dane, ale zgodne ze schematami z Kroku 2.

Krok 5: Frontend (UI + Logika Stanu): Zbudowanie kompletnego UI (Widoki 1, 2, 3) w oparciu o design_tokens.json i i18n_locales.json. Frontend łączy się z zaślepionym backendem z Kroku 4.

Krok 6: Integracja Logiki AI (Serce Systemu): Zastąpienie zaślepek z Kroku 4 prawdziwą logiką biznesową (Prompty 1-4, wywołania RAG, wywołania SOTA LLM).

2. Moduł 2: Inicjalizacja Danych (Problem 'Dnia Zero')
qoder.ai musi zbudować skrypt seed.py, który będzie odpowiedzialny za jednorazowe zasilenie baz danych.

Zależności skryptu: psycopg2-binary, qdrant-client, sentence-transformers

Model Embeddingu: paraphrase-multilingual-MiniLM-L12-v2 (Musi zostać pobrany przez skrypt).

Logika dla PostgreSQL: Skrypt połączy się z bazą (zmienne środowiskowe) i załaduje zawartość golden_standards_day_zero.json do tabeli golden_standards.

Logika dla Qdrant: Skrypt połączy się z Qdrant (zmienne środowiskowe). Następnie, dla każdego obiektu w rag_day_zero_tesla.json:

Wygeneruje embedding (wektor) z pola content używając ww. modelu.

Zapisze ten wektor w Qdrant wraz z całą resztą obiektu (w tym language: 'pl') jako metadane (payload).

### 2.1 Instrukcja Uruchomienia Seedingu

Aby zasilić bazy danych (PostgreSQL i Qdrant) danymi startowymi, `qoder.ai` musi zapewnić uruchomienie skryptu `seed.py`.

**Kroki:**
1.  Upewnij się, że pliki `DATA_01_RAG.md` i `DATA_02_Golden_Standards.md` znajdują się w tym samym katalogu co `seed.py`.
2.  Zainstaluj wymagane zależności Pythona: `psycopg2-binary`, `qdrant-client`, `sentence-transformers`.
3.  Ustaw następujące zmienne środowiskowe, aby wskazać na usługi bazodanowe (np. z Railway):
    * `POSTGRES_USER`
    * `POSTGRES_PASSWORD`
    * `POSTGRES_HOST`
    * `POSTGRES_PORT`
    * `POSTGRES_DB`
    * `QDRANT_HOST`
    * `QDRANT_PORT`
4.  Uruchom skrypt:
    ```bash
    python seed.py
    ```
5.  Skrypt jest idempotentny: bezpiecznie utworzy tabele (jeśli nie istnieją) i zignoruje duplikaty danych.

### 2.2 Algorytm generowania session_id (K8)

Python
import random, string
def generate_session_id():
    prefix = "S"
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{letters}-{numbers}"  # Przykład: "S-PYR-334"

3. Moduł 3: Kontrakty API (Ścisłe Schematy Danych)
To jest kręgosłup aplikacji. qoder.ai musi zaimplementować dokładnie te struktury Pydantic (Backend) i TypeScript (Frontend).

Uwaga dla qoder.ai (T9): Backend musi implementować middleware, który normalizuje wszystkie parametry query 'language' do lowercase (np. 'PL' -> 'pl') przed przekazaniem do logiki endpointu.

3.1 Schematy Bazowe (Współdzielone)
Python

# Backend: Pydantic (models.py)
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Union

class ConversationLogEntry(BaseModel):
    log_id: int
    session_id: str
    timestamp: datetime
    role: Literal["Sprzedawca", "FastPath", "FastPath-Questions"]
    content: str
    language: Literal["pl", "en"]
    journey_stage: Optional[Literal["Odkrywanie", "Analiza", "Decyzja"]] = None  # (W1) journey_stage akceptuje null

class OpusMagnumModuleBase(BaseModel):
    confidence_score: int = Field(..., ge=0, le=100)  # (W25) 90-100: Wysoka pewność, 70-89: Średnia, 0-69: Niska (zgodnie z instrukcją dla LLM)

class M1DnaClient(OpusMagnumModuleBase):
    holistic_summary: str
    main_motivation: str
    communication_style: str
    key_levers: List[Dict[str, str]] = Field(
        ..., description="e.g., [{'argument': 'TCO', 'rationale': 'Klient liczy koszty'}]"
    )  # (W3) Uwaga dla qoder.ai: Mapowania Pydantic List[Dict] są ekwiwalentne z TypeScript Array<{...}>.
    red_flags: List[str]

class M2TacticalIndicators(OpusMagnumModuleBase):
    purchase_temperature: Dict[str, Union[int, str]] = Field(
        ..., description="e.g., {'value': 80, 'label': 'Gorący'}"
    )
    churn_risk: Dict[str, Union[str, int, float]] = Field(
        ..., description="e.g., {'level': 'High', 'percentage': 75, 'reason': 'Wspomniał o Audi'}"
    )
    fun_drive_risk: Dict[str, Union[str, int, float]]

class M3PsychometricProfile(OpusMagnumModuleBase):
    dominant_disc: Dict[str, str] = Field(..., description="e.g., {'type': 'D', 'rationale': '...'}")
    big_five_traits: Dict[str, Dict[str, Union[str, int, float]]]
    schwartz_values: List[Dict[str, str]]

class M4DeepMotivation(OpusMagnumModuleBase):
    key_insight: str
    evidence_quotes: List[str]
    tesla_hook: str

class M5PredictivePaths(OpusMagnumModuleBase):
    paths: List[Dict[str, Union[str, int, float, List[str]]]] = Field(
        ..., description="e.g., [{'path': '...', 'probability': 60, 'recommendations': ['...']}]"
    )

class M6StrategicPlaybook(OpusMagnumModuleBase):
    plays: List[Dict[str, Union[str, List[str], int]]] = Field(
        ..., description="e.g., [{'title': '...', 'trigger': '...', 'content': ['Seller: ...'], 'confidence_score': 90}]"
    )

class M7DecisionVectors(OpusMagnumModuleBase):
    vectors: List[Dict[str, Union[str, int]]] = Field(
        ..., description="e.g., [{'stakeholder': 'Żona', 'influence': 'High', ...}]"
    )

class OpusMagnumModules(BaseModel):
    dna_client: M1DnaClient
    tactical_indicators: M2TacticalIndicators
    psychometric_profile: M3PsychometricProfile
    deep_motivation: M4DeepMotivation
    predictive_paths: M5PredictivePaths
    strategic_playbook: M6StrategicPlaybook
    decision_vectors: M7DecisionVectors

class OpusMagnumJSON(BaseModel):
    overall_confidence: int = Field(..., ge=0, le=100)
    suggested_stage: Literal["Odkrywanie", "Analiza", "Decyzja", "Discovery", "Analysis", "Decision"]
    modules: OpusMagnumModules

class SlowPathLogEntry(BaseModel):
    log_id: int
    session_id: str
    timestamp: datetime
    json_output: OpusMagnumJSON
    status: Literal["Success", "Error"]

class GlobalAPIResponse(BaseModel):
    status: Literal["success", "fail", "error"]
    data: Optional[dict] = None
    message: Optional[str] = None
TypeScript

// Frontend: TypeScript (types.ts)
type TConversationRole = "Sprzedawca" | "FastPath" | "FastPath-Questions";
type TLanguage = "pl" | "en";

interface IConversationLogEntry {
  log_id: number;
  session_id: string;
  timestamp: string; // (W27) Format ISO 8601
  role: TConversationRole;
  content: string;
  language: TLanguage;
  journey_stage: "Odkrywanie" | "Analiza" | "Decyzja" | null;  // (W1) journey_stage akceptuje null
}

// Definicje modułów dla IOpusMagnumJSON
interface IOpusMagnumModuleBase {
  confidence_score: number;  // (W25) 90-100: Wysoka pewność, 70-89: Średnia, 0-69: Niska (zgodnie z instrukcją dla LLM)
}

interface IM1DnaClient extends IOpusMagnumModuleBase {
  holistic_summary: string;
  main_motivation: string;
  communication_style: string;
  key_levers: Array<{ argument: string; rationale: string }>;
  red_flags: string[];
}

interface IM2TacticalIndicators extends IOpusMagnumModuleBase {
  purchase_temperature: { value: number; label: string };
  churn_risk: { level: "Low" | "Medium" | "High"; percentage: number; reason: string };
  fun_drive_risk: { level: "Low" | "Medium" | "High"; percentage: number; reason: string };
}

interface IM3PsychometricProfile extends IOpusMagnumModuleBase {
  dominant_disc: { type: "D" | "I" | "S" | "C"; rationale: string };
  big_five_traits: {
    openness: { level: string; score: number };
    conscientiousness: { level: string; score: number };
    extraversion: { level: string; score: number };
    agreeableness: { level: string; score: number };
    neuroticism: { level: string; score: number };
  };
  schwartz_values: Array<{ value: string; rationale: string }>;
}

interface IM4DeepMotivation extends IOpusMagnumModuleBase {
  key_insight: string;
  evidence_quotes: string[];
  tesla_hook: string;
}

interface IM5PredictivePaths extends IOpusMagnumModuleBase {
  paths: Array<{ path: string; probability: number; recommendations: string[] }>;
}

interface IM6StrategicPlaybook extends IOpusMagnumModuleBase {
  plays: Array<{ title: string; trigger: string; content: string[]; confidence_score: number }>;
}

interface IM7DecisionVectors extends IOpusMagnumModuleBase {
  vectors: Array<{ stakeholder: string; influence: string; vector: string; focus: string; strategy: string; confidence_score: number }>;
}

interface IOpusMagnumModules {
  dna_client: IM1DnaClient;
  tactical_indicators: IM2TacticalIndicators;
  psychometric_profile: IM3PsychometricProfile;
  deep_motivation: IM4DeepMotivation;
  predictive_paths: IM5PredictivePaths;
  strategic_playbook: IM6StrategicPlaybook;
  decision_vectors: IM7DecisionVectors;
}

// Główny Interfejs
interface IOpusMagnumJSON {
  overall_confidence: number;
  suggested_stage: "Odkrywanie" | "Analiza" | "Decyzja" | "Discovery" | "Analysis" | "Decision";
  modules: IOpusMagnumModules;
}

interface ISlowPathLogEntry {
  log_id: number;
  session_id: string;
  timestamp: string;
  json_output: IOpusMagnumJSON;
  status: "Success" | "Error";
}

interface IGlobalAPIResponse<T> {
  status: "success" | "fail" | "error";
  data?: T;
  message?: string;
}
3.2 Endpointy
1. [POST] /api/v1/sessions/new

Req (Body): (brak)

Res (Data): { session_id: string }

2. [GET] /api/v1/sessions/{session_id}

Req (Path): session_id: string

Res (Data): { conversation_log: IConversationLogEntry[], slow_path_log: ISlowPathLogEntry | null }

3. [POST] /api/v1/sessions/send (F-2.2)

Req (Body): { session_id: string, user_input: string, journey_stage: 'Odkrywanie' | 'Analiza' | 'Decyzja', language: TLanguage }

Res (Data): IGlobalAPIResponse<ISendResponseData> -- (K7) Response format (TypeScript):
```typescript
interface ISendResponseData {
  suggested_response: string;
  suggested_questions: string[];
}
Res (Data): IGlobalAPIResponse<ISendResponseData>
```

4. [POST] /api/v1/sessions/refine (F-2.3)

Req (Body): { session_id: string, original_input: string, bad_suggestion: string, feedback_note: string, language: TLanguage }

Res (Data): IGlobalAPIResponse<{ refined_suggestion: string }> -- (K15) Res (Data): IGlobalAPIResponse<{ refined_suggestion: string }>

5. [POST] /api/v1/sessions/retry_slowpath (F-2.5) -- (W8) Upewnij się, że endpoint 5 to [POST] /api/v1/sessions/retry_slowpath

Req (Body): { session_id: string }

Res (Data): { message: string } (Np. "Slow path retry triggered")

6. [POST] /api/v1/sessions/end (F-2.6)

Req (Body): { session_id: string, final_status: 'Sprzedaż' | 'Utrata' }

Res (Data): { message: "Session ended" }

7. [GET] /api/v1/admin/feedback/grouped (F-3.1)

Req (Query): { language: TLanguage } (dodano language)

Res (Data): IGlobalAPIResponse<FeedbackGroupingResponse> -- (K12) Dodaj schematy Pydantic i TypeScript dla FeedbackGroupingResponse:
```typescript
interface FeedbackGroupingResponse {
  groups: Array<{ theme_name: string; count: number; representative_note: string }>;
}
```

8. [GET] /api/v1/admin/feedback/details (F-3.1)

Req (Query): { note: string, language: TLanguage } (dodano language)

Res (Data): { details: Array<{ feedback_id: int, original_input: string, bad_suggestion: string }> }

9. [POST] /api/v1/admin/feedback/create_standard (F-3.1)

Req (Body): { trigger_context: string, golden_response: string, language: TLanguage, category: string } (dodano category)

Res (Data): { message: "Golden standard created" }

10. [GET] /api/v1/admin/rag/list (F-3.2) -- (W12) Dodaj schemat odpowiedzi

Req (Query): { language: TLanguage } (dodano language)

Res (Data): IGlobalAPIResponse<IRAGListResponse> -- (W12) Schemat odpowiedzi:
```typescript
interface INuggetPayload { 
  title: string;
  content: string;
  keywords: string;
  language: TLanguage;
  type?: string;
  tags?: string[];
  archetype_filter?: string[];
}
interface IRAGListResponse {
  nuggets: Array<{ id: string; payload: INuggetPayload; }>;
}
Res (Data): IGlobalAPIResponse<IRAGListResponse>
```

11. [POST] /api/v1/admin/rag/add (F-3.2)

Req (Body): { title: string, content: string, keywords: string, language: TLanguage } -- (W24) keywords: string // (Keywords jako pojedynczy string CSV, np. "leasing, vat, b2b")

Res (Data): { message: "Nugget added" }

12. [DELETE] /api/v1/admin/rag/delete/{nugget_id} (F-3.2) -- (T11) Logika: Usuwa nugget tylko z Qdrant. Nie dotyka tabeli golden_standards.

Req (Path): nugget_id: string

Res (Data): { message: "Nugget deleted" }

13. [GET] /api/v1/admin/analytics/v1_dashboard (F-3.3) -- (W18) Dodaj Req (Query)

Req (Query): { date_from?: string, date_to?: string, language?: TLanguage } -- (W18) Req (Query): { date_from?: string, date_to?: string, language?: TLanguage }

Res (Data): { chart1_data: [...], chart2_data: [...], chart3_data: [...] } (Struktury danych dla wykresów)

14. [WebSocket] /api/v1/ws/sessions/{session_id} (F-2.4) -- (K2) Zastąp definicję WebSocket nową, precyzyjną definicją
Req (Path): session_id: string
Server→Client Messages: -- (K2) Precyzyjna definicja WebSocket:
```typescript
type WebSocketMessage = {
  type: "slow_path_update" | "slow_path_error" | "slow_path_progress";
  status?: "Success" | "Error";
  data?: IOpusMagnumJSON;
  message?: string; // np. "Processing completed" lub "API connection failed"
  progress?: number; // 0-100, opcjonalnie
}
```
Client→Server: (Brak – tylko odbieranie)
Auth: (W30) WYMAGANE. Backend musi zweryfikować, czy session_id w URL istnieje w tabeli sessions przed akceptacją połączenia.

Uwaga dla qoder.ai (W3): journey_stage w requescie używa wartości polskich ('Odkrywanie', 'Analiza', 'Decyzja'), ale Slow Path (Prompt 4.4) może zwrócić wartości angielskie ('Discovery', 'Analysis', 'Decision'). Backend musi mapować: -- (K3) Zastąp pełnym algorytmem mapowania

Python
# Backend: Mapowanie PL → EN (przed wysłaniem do Slow Path)
STAGE_TO_EN = { 'Odkrywanie': 'Discovery', 'Analiza': 'Analysis', 'Decyzja': 'Decision' }
# Backend: Mapowanie EN → PL (po otrzymaniu z Slow Path)
STAGE_TO_PL = { 'Discovery': 'Odkrywanie', 'Analysis': 'Analiza', 'Decision': 'Decyzja' }
# Użycie:
suggested_stage_pl = STAGE_TO_PL.get(opus_magnum_json["suggested_stage"], current_stage)
przed porównaniem z current_stage frontendu.

4. Moduł 4: Zarządzanie Stanem (Frontend)
Narzędzie: Zustand (preferowany) lub React Context API (jeśli qoder.ai ma problemy z Zustand).

Struktura Głównego Store'a: qoder.ai musi zaimplementować globalny store zawierający co najmniej:

session_id: string | null

current_stage: 'Odkrywanie' | 'Analiza' | 'Decyzja'

conversation_log: IConversationLogEntry[]

slow_path_data: IOpusMagnumJSON | null

app_status: 'idle' | 'fast_path_loading' | 'slow_path_loading' | 'error'

slow_path_error: string | null

current_language: TLanguage

5. Moduł 5: Uwierzytelnianie i Autoryzacja (Wersja FINALNA z Addendum v1.5)
Strategia: Prosty klucz API (zgodnie z decyzją Wizjonera).

Backend (Zmienna Środowiskowa): Wymagana jest tylko jedna zmienna:
ADMIN_API_KEY: Ustawiona na wartość ULTRA_DOJO_KEY_8a4f9b2c_qoder_ai_2025.

Backend (Logika):
qoder.ai musi zaimplementować prostą zależność (FastAPI Depends) sprawdzającą nagłówek X-Admin-Key.
Wszystkie endpointy /api/v1/admin/* muszą wymagać, aby nagłówek X-Admin-Key był obecny i zgodny z wartością zmiennej ADMIN_API_KEY.
W przypadku braku lub niezgodności klucza, API musi zwrócić błąd 401 Unauthorized.

Frontend (UI):
Strona /admin (Widok 3) musi wyświetlać prosty formularz logowania (1 pole: "Klucz Admina").
Po wpisaniu, klucz jest zapisywany w localStorage.
Przy każdym kolejnym żądaniu do /admin/*, frontend musi dołączać ten klucz jako nagłówek X-Admin-Key.

6. Moduł 6: Strategia Obsługi Błędów
Format API: qoder.ai musi używać globalnego formatu odpowiedzi zfinionego w Module 3 (z polem status: 'success' | 'fail' | 'error').

Błąd F-1.1 (Optimistic UI Fail): Jeśli POST /api/v1/sessions/new zwróci błąd po przejściu do Widoku 2, frontend musi natychmiast wyrzucić użytkownika do Widoku 1 i wyświetlić komunikat błędu (np. "Nie można utworzyć sesji").

Błąd F-2.2 (Fast Path Fail): Jeśli POST /api/v1/sessions/send zwróci błąd, frontend nie może się zawiesić. Musi wyświetlić komunikat błędu (z i18n_locales.json) pod notatką sprzedawcy, zamiast sugestii AI.

Błąd F-2.4 (Slow Path Fail): Zgodnie z SUPER-BLUEPRINT (F-2.5) – panel musi wyświetlić stan błędu z przyciskiem ponowienia.

 Dodatkowe doprecyzowanie (UI/UX):
 - Fast Path: w przypadku braku odpowiedzi w czasie P95 lub błędu, aplikacja utrzymuje płynność pętli — znika stan "analizowanie..." i pojawia się czytelny komunikat (i18n), użytkownik może natychmiast wprowadzić kolejną notatkę.
 - Slow Path: przycisk `[ 🔄 ]` musi wywołać `/api/v1/sessions/retry_slowpath`; panel po ponowieniu wraca do normalnego widoku z subtelną animacją.

7. Moduł 7: Orkiestracja AI (Hosting Modeli)
qoder.ai musi zaimplementować wywołania AI w następujący sposób (scalenie addendów v1.1–v1.6):

Slow Path (SOTA, np. DeepSeek 671B): Wywołanie zewnętrznego Ollama Cloud API.
- Zmienne: -- (W22) Upewnij się, że zmienne to OLLAMA_CLOUD_URL i OLLAMA_API_KEY
  - `OLLAMA_CLOUD_URL`: Domyślnie `https://ollama.com` (zgodnie z BIGD12.md)
  - `OLLAMA_API_KEY`: Klucz użytkownika z ollama.com
- Model: `deepseek-v3.1:671b-cloud`
- Retry: `tenacity` – maks. 3 próby, exponential backoff.

Fast Path (Szybki): Google Gemini (`gemini-1.5-flash`).
- Zależność: `google-generativeai`.
- Zmienne: `GEMINI_API_KEY`.
- Retry: `tenacity` – maks. 3 próby, exponential backoff.
- Prompty: używać treści z SUPER-BLUEPRINT (4.1, 4.2, 4.3, 4.5).

 

8. Moduł 8: Scenariusze Testowe (UAT)
Są to instrukcje testowe dla Ciebie (Wizjonera) do weryfikacji gotowej aplikacji.

UAT-1: Pełna Pętla (F-2.2 + F-2.4) -- (W16) PONIŻEJ 2 sekund (mierzony czas od kliknięcia [SEND] do wyświetlenia sugestii w UI)

Otwórz nową sesję (Widok 2).

Wybierz język PL. Wpisz notatkę: "Klient pytał o Model Y. Mówił, że Audi Q4 e-tron ma 'bardziej luksusowe wnętrze'." Kliknij [ SEND > ].

Oczekiwany Rezultat (Fast Path): PONIŻEJ 2 sekund pojawiają się "Szybka Odpowiedź" i "Pytania Pogłębiające" w języku polskim.

Oczekiwany Rezultat (Slow Path): Po ok. 15-20 sekundach "Panel Strategiczny" po prawej stronie subtelnie mruga/aktualizuje się, a jego treść (np. "DNA Klienta") odzwierciedla obiekcję dot. Audi.

UAT-2: Pętla Korekcyjna (F-2.3)

Wykonaj kroki 1-3 z UAT-1.

Kliknij ikonę 👎 pod "Szybką Odpowiedzią".

W polu "Co było nie tak?" wpisz: "zbyt łagodne". Naciśnij Enter.

Oczekiwany Rezultat: Natychmiast pojawia się nowa, "Poprawiona sugestia", która jest bardziej asertywna.

UAT-3: AI Dojo (F-3.1)

Wykonaj UAT-2.

Przejdź do "/admin" (Widok 3) i zaloguj się (kluczem z Modułu 5).

Przejdź do "Tablicy Feedbacku".

Oczekiwany Rezultat: Widoczna jest nowa grupa feedbacku [1] "zbyt łagodne". Można ją kliknąć, zobaczyć szczegóły i utworzyć "Złoty Standard".

UAT-4: Autoryzacja Admin (Bearer)

Wejdź na `/admin`. Spróbuj wywołać `GET /api/v1/admin/rag/list` bez nagłówka `Authorization` – oczekuj `401 Unauthorized`.
W formularzu wpisz poprawny token i wywołaj ponownie – oczekuj `200 OK` z listą.

UAT-5: i18n + brak danych EN (fallback)

W Widoku 2 ustaw język EN. Wyślij notatkę. Backend filtruje RAG po `language='en'` (brak danych) – Fast Path generuje odpowiedź tylko na podstawie notatki (bez faktu RAG), w języku EN. Oczekuj poprawnej odpowiedzi i pytań.

UAT-6: Retry i stan błędu Slow Path

Zasymuluj błąd połączenia z API SOTA (np. czasowe 5xx). Backend wykona do 3 prób (`tenacity`). W przypadku niepowodzenia – zapisz `Error` w `slow_path_logs`. Frontend pokaże stan „Błąd Połączenia z AI” z przyciskiem `[ 🔄 ]`. Kliknięcie wywoła `/api/v1/sessions/retry_slowpath` i przy sukcesie panel wróci do normalnego widoku.

9. Moduł 9: Rekomendacje UI

- Wykresy: `Recharts` (RadarChart dla DISC, BarChart/LineChart dla analityki).
- Ikony: `Heroicons` (statusy, akcje, feedback 👍/👎, [🔄]).
- Styl: korzystać z `design_tokens.json` (kolory, czcionki, promienie) i `i18n_locales.json` (teksty).

10. Moduł 10: Doprecyzowanie Schematów Baz Danych

Tabele wymagają korekt, indeksów i walidacji (zgodnie z addendum v1.4–v1.6 oraz skonsolidowanym audytem):

`feedback_logs`
- `feedback_id` SERIAL PRIMARY KEY
- `session_id` TEXT NOT NULL REFERENCES sessions(session_id)
- `log_id_ref` INT NULL -- (Referencja do `conversation_log.log_id` ocenionej sugestii)
- `feedback_type` TEXT NOT NULL CHECK (feedback_type IN ('up','down')) -- (Kluczowe dla F-3.1)
- `original_input` TEXT NOT NULL -- (Notatka sprzedawcy)
- `bad_suggestion` TEXT NOT NULL -- (Oceniona sugestia AI)
- `feedback_note` TEXT NOT NULL -- (Komentarz "Co było nie tak?")
- `language` TEXT NOT NULL CHECK (language IN ('pl','en'))
- `journey_stage` TEXT NULL CHECK (journey_stage IN ('Odkrywanie','Analiza','Decyzja'))
- `refined_suggestion` TEXT NULL -- (Nowa, poprawiona sugestia z F-2.3)
- `created_at` TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
- Indeksy: (`session_id`), (`language`), (`created_at` DESC)

`golden_standards`
- `gs_id` SERIAL PRIMARY KEY
- `category` TEXT NOT NULL -- (Kluczowe pole dodane z audytu, np. "Cena i Finansowanie")
- `trigger_context` TEXT NOT NULL
- `golden_response` TEXT NOT NULL
- `language` TEXT NOT NULL DEFAULT 'pl' CHECK (language IN ('pl','en'))
- `created_at` TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
- `updated_at` TIMESTAMP WITH TIME ZONE NULL
- Unikalność: `UNIQUE(trigger_context, language)`
- Indeksy: (`language`), (`category`), (`created_at` DESC)

11. Moduł 11: Doprecyzowanie Logiki AI i Danych (FINAL)

**11.1 Logika Zapytań RAG (dla Promptów 1-4)**
- Model embeddingu dla zapytań: `paraphrase-multilingual-MiniLM-L12-v2` (ten sam co seed.py)
- Liczba pobieranych nuggetów (top-k): **3**
- Próg podobieństwa (score_threshold): **0.75**
- Metoda łączenia kontekstu:
```python
  kontekst = "\n---\n".join([nugget.payload['content'] for nugget in results[:3]])
```
- Filtrowanie: `filter=models.Filter(must=[models.FieldCondition(key="language", match=models.MatchValue(value=language))])` -- (W10) Upewnij się, że filtr language jest poprawnie zdefiniowany (już obecny).
- (T12) Jeśli RAG zwróci 0 wyników (np. brak danych w danym języku), backend musi użyć fallback: relevant_context = "No specific product knowledge available. Use general sales principles."

**11.2 Parametry Wywołań AI**
Fast Path (Gemini 1.5-flash, Prompty 1, 2, 3, 5):
- `temperature`: **0.5**
- `max_tokens`: **1024**
- `stream`: **False**

**Timeouty (Wymaganie Robustness):** -- (W6) Doprecyzuj: Timeouty (całkowity czas odpowiedzi API, np. requests.post(..., timeout=X))
- Fast Path (Gemini): **10 sekund** (całkowity czas odpowiedzi API)
- Slow Path (Ollama Cloud): **60 sekund** (całkowity czas odpowiedzi API)
(Po przekroczeniu timeoutu, logikę `tenacity` traktuje to jako błąd i ponawia zgodnie z Modułem 11.4).

Slow Path (Ollama Cloud `deepseek-v3.1:671b-cloud`, Prompt 4.4):
- `temperature`: **0.3**
- `max_tokens`: **4096**
- `stream`: **False**

**11.3 Logika Komunikacji Real-time (F-2.4)**
- Metoda: **WebSocket** (preferowana)
- Endpoint: `wss://{TWOJA_DOMENA_RAILWAY}/api/v1/ws/sessions/{session_id}`
- Format wiadomości (Server→Client):
```json
  {
    "type": "slow_path_update",
    "status": "Success" | "Error",
    "data": IOpusMagnumJSON | null,
    "message": string | null
  }
```
- Fallback: Polling `GET /api/v1/sessions/{session_id}` co **7 sekund** (max 20 prób = 140s) -- (K14) Jeśli po 20 próbach (140s) status 'Success' nie nadejdzie, frontend musi przestać pollować i wyświetlić stan błędu (ten sam co F-2.5) z komunikatem "Przekroczono limit czasu oczekiwania na analizę."
- (T10) Backend musi zapewnić, że timeout WebSocket (np. 120s) jest dłuższy niż timeout Slow Path (60s).

**11.4 Logika Retry (dla Gemini i Ollama Cloud)**
- Biblioteka: `tenacity`
- Parametry:
```python
  @retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential(multiplier=2, min=1, max=10),
      retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)) |
            retry_if_result(lambda response: response.status_code >= 500)
  )
```
 - **Obsługa Błędów 4xx (Krytyczne):**
   - **NIE** ponawiaj błędów 4xx (np. 400 Bad Request).
   - **Obsługa 401 (Unauthorized):** -- (K4) W przypadku błędu 401, backend musi zapisać w slow_path_logs status="Error" z message="Invalid API Key for [service]". Frontend musi przechwycić ten komunikat (przez WebSocket/Polling) i wyświetlić: "Błąd autoryzacji AI. Skontaktuj się z administratorem." W przypadku błędu 401 z Gemini lub Ollama: **NIE ponawiaj**. Zapisz w `slow_path_logs` status=`Error` z `message="Invalid API Key for [service]"`. Zaloguj krytyczny błąd (`logging.critical()`). Frontend musi wyświetlić stan błędu z komunikatem: "Błąd autoryzacji AI. Skontaktuj się z administratorem."

**11.5 Logika `seed.py` (K5)**
- Potwierdzone: `seed.py` używa `sentence-transformers` (`SentenceTransformer`) z modelem `paraphrase-multilingual-MiniLM-L12-v2` do generowania embeddingów (wymiar 384) i seedowania kolekcji `ultra_rag_v1` w Qdrant.

12. Moduł 12: Rekomendacje Audytowe (Post-v1.0)

Ta sekcja zawiera rekomendacje opcjonalne z Finałowego Raportu Audytowego, które należy rozważyć w przyszłych iteracjach projektu (post-v1.0). Rekomendacje te nie są krytyczne dla wersji 1.0, ale mogą znacząco poprawić jakość, wydajność i funkcjonalność systemu.

**O1-O12: Lista Rekomendacji Opcjonalnych**

*(Uwaga: Pełna lista rekomendacji O1-O12 powinna być wklejona tutaj z Finałowego Raportu Audytowego. Poniżej znajduje się struktura przykładowa, którą należy uzupełnić zgodnie z raportem audytowym.)*

- **O1:** [Rekomendacja opcjonalna 1 - do uzupełnienia z raportu audytowego]
- **O2:** [Rekomendacja opcjonalna 2 - do uzupełnienia z raportu audytowego]
- **O3:** [Rekomendacja opcjonalna 3 - do uzupełnienia z raportu audytowego]
- **O4:** [Rekomendacja opcjonalna 4 - do uzupełnienia z raportu audytowego]
- **O5:** [Rekomendacja opcjonalna 5 - do uzupełnienia z raportu audytowego]
- **O6:** [Rekomendacja opcjonalna 6 - do uzupełnienia z raportu audytowego]
- **O7:** [Rekomendacja opcjonalna 7 - do uzupełnienia z raportu audytowego]
- **O8:** [Rekomendacja opcjonalna 8 - do uzupełnienia z raportu audytowego]
- **O9:** [Rekomendacja opcjonalna 9 - do uzupełnienia z raportu audytowego]
- **O10:** [Rekomendacja opcjonalna 10 - do uzupełnienia z raportu audytowego]
- **O11:** [Rekomendacja opcjonalna 11 - do uzupełnienia z raportu audytowego]
- **O12:** [Rekomendacja opcjonalna 12 - do uzupełnienia z raportu audytowego]

**Instrukcja dla qoder.ai:**
Rekomendacje O1-O12 są oznaczone jako opcjonalne i nie muszą być implementowane w wersji 1.0. Powinny być rozważone w przyszłych iteracjach projektu, gdy podstawowa funkcjonalność będzie już w pełni działająca i przetestowana.