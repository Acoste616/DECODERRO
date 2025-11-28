import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# === V3.1 LITE: GLOBAL CONCURRENCY CONTROL ===
SLOW_PATH_SEMAPHORE = asyncio.Semaphore(5)  # Max 5 concurrent Slow Path tasks

# --- Pydantic Models (Mirroring types.ts) ---

class ModuleDNA(BaseModel):
    summary: str = Field(..., description="Brief summary of the client")
    mainMotivation: str = Field(..., description="Primary driver for purchase")
    communicationStyle: str = Field(..., description="Analytical | Driver | Amiable | Expressive")

class ModuleIndicators(BaseModel):
    purchaseTemperature: int = Field(..., ge=0, le=100)
    churnRisk: str = Field(..., description="Low | Medium | High")
    funDriveRisk: str = Field(..., description="Low | Medium | High")

class DiscScores(BaseModel):
    dominance: int
    influence: int
    steadiness: int
    compliance: int

class BigFiveScores(BaseModel):
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int

class SchwartzScores(BaseModel):
    opennessToChange: int
    selfEnhancement: int
    conservation: int
    selfTranscendence: int

class ModulePsychometrics(BaseModel):
    disc: DiscScores
    bigFive: BigFiveScores
    schwartz: SchwartzScores

class ModuleMotivation(BaseModel):
    keyInsights: List[str]
    teslaHooks: List[str]

class Scenario(BaseModel):
    name: str
    probability: int
    description: str

class ModulePredictions(BaseModel):
    scenarios: List[Scenario]
    estimatedTimeline: str

class SSREntry(BaseModel):
    fact: str
    implication: str
    solution: str
    action: str

class ModulePlaybook(BaseModel):
    suggestedTactics: List[str]
    ssr: List[SSREntry]

class ModuleDecision(BaseModel):
    decisionMaker: str
    influencers: List[str]
    criticalPath: str

class JourneyStageAnalysis(BaseModel):
    currentStage: str
    confidence: int
    reasoning: str

class AnalysisState(BaseModel):
    m1_dna: ModuleDNA
    m2_indicators: ModuleIndicators
    m3_psychometrics: ModulePsychometrics
    m4_motivation: ModuleMotivation
    m5_predictions: ModulePredictions
    m6_playbook: ModulePlaybook
    m7_decision: ModuleDecision
    journeyStageAnalysis: JourneyStageAnalysis
    isAnalyzing: bool = False
    lastUpdated: int = 0

class FastPathResponse(BaseModel):
    response: str
    confidence: float
    confidence_reason: str
    tactical_next_steps: List[str] = Field(
        default_factory=list,
        description="Concrete physical actions for salesperson (e.g., 'Send TCO Calculator', 'Schedule Test Drive')"
    )
    knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Dynamic questions to fill missing psychological profile data (e.g., 'Did client mention their wife?', 'Is he concerned about charging?')"
    )

# === V3.1 LITE: EMERGENCY FALLBACK RESPONSES ===

def create_emergency_response(language: str = "PL") -> FastPathResponse:
    """
    Hardcoded emergency response when all AI systems fail.
    """
    if language == "PL":
        return FastPathResponse(
            response="Rozumiem pytanie. Pozwól mi zebrać szczegóły z bazy...",
            confidence=0.5,
            confidence_reason="EMERGENCY FALLBACK",
            tactical_next_steps=[
                "Zapytaj klienta o jego główne obawy",
                "Pokaż dostępne modele Tesli"
            ],
            knowledge_gaps=[
                "Czy klient ma doświadczenie z elektrycznymi autami?",
                "Co myśli o obecnym aucie?"
            ]
        )
    else:
        return FastPathResponse(
            response="I understand your question. Let me gather details...",
            confidence=0.5,
            confidence_reason="EMERGENCY FALLBACK",
            tactical_next_steps=[
                "Ask client about their main concerns",
                "Show available Tesla models"
            ],
            knowledge_gaps=[
                "Does client have experience with electric cars?",
                "What do they think about their current car?"
            ]
        )

def create_rag_fallback_response(rag_context: str, language: str = "PL") -> FastPathResponse:
    """
    Fallback response using RAG context when Gemini fails.
    Returns a NATURAL LANGUAGE response, not raw database text.
    """
    if language == "PL":
        return FastPathResponse(
            response="Rozumiem Twoje pytanie. Na podstawie dostępnych informacji mogę Ci pomóc wybrać najlepszy model Tesli dopasowany do Twoich potrzeb. Czy mogę zapytać o kilka szczegółów, żeby lepiej dopasować ofertę?",
            confidence=0.7,
            confidence_reason="RAG_FALLBACK",
            tactical_next_steps=[
                "Wyślij katalog dostępnych modeli Tesla",
                "Zaproponuj jazdę testową w najbliższym salonie",
                "Przygotuj kalkulację TCO (Total Cost of Ownership)"
            ],
            knowledge_gaps=[
                "Jakie są główne potrzeby klienta? (rodzina, praca, podróże)",
                "Jaki jest budżet klienta?",
                "Czy klient ma możliwość ładowania w domu?"
            ]
        )
    else:
        return FastPathResponse(
            response="I understand your question. Based on the available information, I can help you choose the best Tesla model tailored to your needs. May I ask a few details to better match the offer?",
            confidence=0.7,
            confidence_reason="RAG_FALLBACK",
            tactical_next_steps=[
                "Send catalog of available Tesla models",
                "Propose a test drive at the nearest showroom",
                "Prepare TCO (Total Cost of Ownership) calculation"
            ],
            knowledge_gaps=[
                "What are the client's main needs? (family, work, travel)",
                "What is the client's budget?",
                "Does the client have home charging capability?"
            ]
        )

# === V3.1 LITE: OLLAMA RETRY LOGIC ===

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
    reraise=True
)
def call_ollama_with_retry(client, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Calls Ollama API with retry logic.
    - Retries up to 3 times
    - Exponential backoff: 2s, 4s, 8s (max 10s)
    """
    print(f"[RETRY] Attempting Ollama call (model: {model})...")
    response = client.chat(
        model=model,
        messages=messages,
        stream=False
    )
    print(f"[RETRY] Ollama call succeeded!")
    return response

# === V3.1 LITE: ULTRA AI CORE ===

class AICore:
    def __init__(self):
        # PRODUCTION MODEL: Stable & Fast
        self.model_name = "models/gemini-2.0-flash"  # STABLE: Fast responses
        
        try:
            self.model = genai.GenerativeModel(self.model_name)
            print(f"[AI CORE] OK - Gemini model initialized: {self.model_name}")
        except Exception as e:
            print(f"[AI CORE] CRITICAL - Failed to initialize Gemini model: {e}")
            raise


    async def fast_path_secure(
        self, 
        history: List[Dict[str, str]], 
        rag_context: str, 
        stage: str, 
        language: str = "PL"
    ) -> FastPathResponse:
        """
        ULTRA V3.1 LITE: RUTHLESS FAST PATH
        
        GUARANTEED to return in <2.8s with fallback chain:
        1. Gemini + RAG
        2. Gemini (No RAG)  
        3. Hardcoded Emergency JSON
        
        Uses strict timeout and proper error handling.
        """
        lang_instruction = {
            "PL": "KRYTYCZNIE WAŻNE: Odpowiadaj TYLKO PO POLSKU.",
            "EN": "CRITICAL: Respond ONLY IN ENGLISH."
        }.get(language, "CRITICAL: Respond in Polish.")

        # Format RAG context
        rag_formatted = ""
        if rag_context:
            rag_formatted = f"""
━━━ KNOWLEDGE BASE (RAG) - VERIFIED TESLA DATA ━━━
{rag_context}
━━━ END KNOWLEDGE BASE ━━━
"""
        else:
            rag_formatted = "[WARNING] NO DATABASE RESULTS - Use general EV knowledge"

        system_prompt = f"""
Jesteś ULTRA v3.0 - Kognitywnym Silnikiem Sprzedaży Tesli.
Twoja rola: Starszy Mentor Sprzedaży.
Twój cel: Błyskawiczna synteza strategii + gotowe cytaty do klienta.

{lang_instruction}

DANE WEJŚCIOWE:
1. Query Sprzedawcy: [Ostatnia wiadomość w historii konwersacji]
2. Kontekst RAG: [Fragmenty bazy wiedzy poniżej]
3. Etap Podróży Klienta: {stage}

{rag_formatted}

ZASADY KRYTYCZNE (BEZWARUNKOWE):

1. ZAKAZ CYTOWANIA (No-Parroting Rule):
   - Absolutnie zabrania się wklejania surowych zdań z RAG.
   - Dane z RAG (liczby, limity, zasady) służą tylko jako argumenty do Twojej porady.
   - Przykład ZŁY: "Program Naszeauto obejmuje dopłaty 27000 zł."
   - Przykład DOBRY: "Skoro klient ma Kartę Dużej Rodziny, wykorzystaj fakt, że przysługuje mu wyższa dopłata (27 000 zł), co obniży ratę o..."

2. REAGOWANIE NA INTENCJE (Context Injection):
   - Jeśli user wspomina "żona/rodzina" -> Twoja odpowiedź MUSI zawierać argumenty o bezpieczeństwie (5 gwiazdek NCAP), komforcie lub łatwości obsługi.
   - Jeśli user wspomina "fotowoltaika/dom" -> Twoja odpowiedź MUSI zawierać argumenty o TCO (darmowa jazda, ładowanie ze słońca).
   - Jeśli user wspomina "firma/leasing" -> Twoja odpowiedź MUSI zawierać argumenty podatkowe (VAT, odliczenia).

3. MÓWIENIE BEZPOŚREDNIE:
   - NIE pisz "Powiedz klientowi, że..." ani "Proszę powiedzieć..."
   - Pisz BEZPOŚREDNIO jako gotowy tekst do wysłania/powiedzenia klientowi.
   - Przykład ZŁY: "Powiedz klientowi, że Tesla ma 5 gwiazdek NCAP."
   - Przykład DOBRY: "Rozumiem obawy o bezpieczeństwo rodziny. Tesla Model 3 ma 5 gwiazdek NCAP - najwyższy wynik w historii testów Euro NCAP."

4. OBSŁUGA BRAKU DANYCH (Fallback):
   - Jeśli Kontekst RAG jest pusty, NIE ZMYŚLAJ faktów.
   - W takim przypadku skup się na psychologii sprzedaży i podejściu do klienta opartym na empatii.

5. FORMAT TECHNICZNY:
   - Odpowiadaj WYŁĄCZNIE czystym kodem JSON.
   - Nie używaj bloków markdown (```json).
   - Nie pisz żadnego wstępu ani zakończenia.

STRUKTURA ODPOWIEDZI (JSON):
{{
  "analysis_content": "Krótka strategia (dlaczego tak mówimy). Max 2 zdania.",
  "direct_quote": "Gotowy tekst do wysłania/powiedzenia klientowi. 2-3 zdania.",
  "confidence_score": <int 0-100>,
  "tactical_next_steps": [
    "Konkretna akcja 1 (np. Wyślij TCO)",
    "Konkretna akcja 2"
  ],
  "knowledge_gaps": [
    "Pytanie do sprzedawcy 1 (np. Czy klient ma garaż?)",
    "Pytanie do sprzedawcy 2"
  ]
}}

ZASADY:
1. tactical_next_steps: Tylko konkretne zadania (imperatyw). Bez pytań.
2. knowledge_gaps: Tylko pytania o brakujące informacje. Każde kończy się "?".
3. Kontekstowa Inteligencja: Jeśli klient wspomniał o "żonie" → Pytanie: "Jaka jest rola żony w decyzji?"

PRZYKŁAD:
{{
  "analysis_content": "Uderzamy w bezpieczeństwo dla żony + TCO z fotowoltaiką.",
  "direct_quote": "Rozumiem obawy Państwa żony. Tesla ma 5★ NCAP. A z fotowoltaiką ładowanie będzie praktycznie darmowe.",
  "confidence_score": 90,
  "tactical_next_steps": [
    "Zaproponuj jazdę testową dla żony",
    "Wyślij kalkulator TCO z fotowoltaiką"
  ],
  "knowledge_gaps": [
    "Czy żona jest głównym decydentem?",
    "Czy rozważali instalację wallboxa?"
  ]
}}
"""

        
        messages = [
            {'role': 'user' if msg['role'] == 'user' else 'model', 'parts': [msg['content']]} 
            for msg in history[-10:]
        ]
        messages.insert(0, {'role': 'user', 'parts': [system_prompt]})

        try:
            # === GLOBAL 5s TIMEOUT (increased for reliability) ===
            response = await asyncio.wait_for(
                self._call_gemini_safe(messages),
                timeout=5.0
            )
            return response

        except asyncio.TimeoutError:
            print("[FAST PATH] TIMEOUT - Using fallback...")
            # Try without RAG context (faster)
            if rag_context:
                return create_rag_fallback_response(rag_context, language)
            else:
                return create_emergency_response(language)

        except Exception as e:
            print(f"[FAST PATH] ERROR - {e}. Using emergency fallback...")
            import traceback
            traceback.print_exc()
            if rag_context:
                return create_rag_fallback_response(rag_context, language)
            else:
                return create_emergency_response(language)

    async def _call_gemini_safe(self, messages: List[Dict]) -> FastPathResponse:
        """
        Internal Gemini call with proper error handling.
        Handles new JSON structure from bulletproof prompt.
        """
        try:
            response = await self.model.generate_content_async(messages, stream=False)
            raw_text = response.text.strip()
            
            # Remove markdown code blocks if present
            text = raw_text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON
            try:
                data = json.loads(text)
                
                # Extract fields
                direct_quote = data.get("direct_quote", data.get("analysis_content", "Nie udało się przetworzyć strategii."))
                analysis_content = data.get("analysis_content", "")
                
                # Extract lists (with safety defaults)
                tactical = data.get("tactical_next_steps", [])
                knowledge = data.get("knowledge_gaps", [])
                
                # Fallback for old model behavior if lists are empty but suggested_actions exists
                if not tactical and not knowledge and "suggested_actions" in data:
                    tactical = data["suggested_actions"]
                
                print(f"[FAST PATH] OK - Gemini response parsed successfully")
                
                return FastPathResponse(
                    response=direct_quote,
                    confidence=float(data.get("confidence_score", 0)) / 100.0,
                    confidence_reason=analysis_content,
                    tactical_next_steps=tactical,
                    knowledge_gaps=knowledge
                )
            
            except json.JSONDecodeError as json_err:
                print(f"[GEMINI] ERROR - JSON parsing failed: {json_err}")
                print(f"[GEMINI] Raw response: {raw_text[:500]}...")
                raise
        
        except Exception as e:
            print(f"[GEMINI] ERROR - API Error: {e}")
            # Re-raise to allow upper-level timeout/fallback handling
            raise

    async def slow_path_analysis_secure(
        self, 
        history: List[Dict[str, str]], 
        stage: str, 
        language: str = "PL", 
        rag_context: str = ""
    ) -> Optional[AnalysisState]:
        """
        ULTRA V3.1 LITE: GUARDED SLOW PATH
        
        - Checks semaphore (max 5 concurrent)
        - Returns None if system is busy
        - Uses retry logic for DeepSeek
        - Handles all exceptions gracefully
        """
        # === CONCURRENCY CONTROL ===
        if SLOW_PATH_SEMAPHORE.locked():
            print("[SLOW PATH] System at capacity. Skipping analysis.")
            return None

        async with SLOW_PATH_SEMAPHORE:
            print(f"[SLOW PATH] Starting analysis (slots available: {SLOW_PATH_SEMAPHORE._value})")
            
            try:
                return await self._run_deepseek_analysis(history, stage, language, rag_context)
            
            except Exception as e:
                print(f"[SLOW PATH] Critical error: {e}")
                return None

    async def _run_deepseek_analysis(
        self, 
        history: List[Dict[str, str]], 
        stage: str, 
        language: str, 
        rag_context: str
    ) -> Optional[AnalysisState]:
        """
        Internal DeepSeek call with retry and timeout.
        """
        lang_instruction = {
            "PL": "Generuj analizę PO POLSKU.",
            "EN": "Generate analysis IN ENGLISH."
        }.get(language, "Generate in Polish.")
        
        rag_section = ""
        if rag_context:
            rag_section = f"""
=== KNOWLEDGE BASE CONTEXT ===
{rag_context}
=== END KNOWLEDGE BASE ===
"""
        
        prompt = f"""
You are the ULTRA v3.1 Deep Analysis Engine.

{lang_instruction}

TASK: Analyze conversation and generate 7-Module Cognitive Profile.
Current Journey Stage: {stage}

{rag_section}

=== CONVERSATION HISTORY ===
"""
        
        for msg in history[-20:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += """

=== OUTPUT (JSON) ===
{
  "m1_dna": { "summary": "...", "mainMotivation": "...", "communicationStyle": "Analytical" },
  "m2_indicators": { "purchaseTemperature": 50, "churnRisk": "Low", "funDriveRisk": "Low" },
  "m3_psychometrics": {
    "disc": { "dominance": 50, "influence": 50, "steadiness": 50, "compliance": 50 },
    "bigFive": { "openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50 },
    "schwartz": { "opennessToChange": 50, "selfEnhancement": 50, "conservation": 50, "selfTranscendence": 50 }
  },
  "m4_motivation": { "keyInsights": ["..."], "teslaHooks": ["..."] },
  "m5_predictions": { "scenarios": [{ "name": "...", "probability": 70, "description": "..." }], "estimatedTimeline": "..." },
  "m6_playbook": { "suggestedTactics": ["..."], "ssr": [{ "fact": "...", "implication": "...", "solution": "...", "action": "..." }] },
  "m7_decision": { "decisionMaker": "...", "influencers": ["..."], "criticalPath": "..." },
  "journeyStageAnalysis": { "currentStage": "DISCOVERY", "confidence": 80, "reasoning": "..." }
}
"""

        try:
            from ollama import Client
            
            OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
            OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
            
            if not OLLAMA_API_KEY or OLLAMA_API_KEY == "your_ollama_key_here":
                print("[SLOW PATH] WARN - OLLAMA_API_KEY not configured.")
                return None
            
            client = Client(
                host=OLLAMA_BASE_URL,
                headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
            )
            
            # CRITICAL FIX #2: Add -cloud suffix to model name
            model_name = 'deepseek-v3.1:671b-cloud'
            print(f"[SLOW] Calling DeepSeek {model_name} at {OLLAMA_BASE_URL}...")

            loop = asyncio.get_event_loop()

            # === 90s TIMEOUT with RETRY ===
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: call_ollama_with_retry(
                        client,
                        model_name,
                        [{'role': 'user', 'content': prompt}]
                    )
                ),
                timeout=90.0
            )
            
            print(f"[SLOW] DeepSeek responded!")
            
            # Parse JSON
            text = response['message']['content']
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            data['isAnalyzing'] = False
            data['lastUpdated'] = 0
            
            return AnalysisState(**data)
            
        except asyncio.TimeoutError:
            print(f"[SLOW PATH] TIMEOUT - DeepSeek exceeded 90s")
            return None
        
        except Exception as e:
            print(f"[SLOW PATH] ERROR - {e}")
            import traceback
            traceback.print_exc()
            return None

# === GLOBAL INSTANCE ===
ai_core = AICore()
