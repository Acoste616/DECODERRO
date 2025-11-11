# API Data Contract Generation Design

## 1. Overview

This design document defines the complete data schema generation for the ULTRA DOJO AI system (Step 2 of PEGT). The objective is to establish a "contracts-first" approach by generating two comprehensive files containing all type definitions and data models from Module 3 of 02_PEGT_FINAL.md.

### 1.1 Purpose

Generate type-safe data contracts that serve as the foundation for both backend (Python/Pydantic) and frontend (TypeScript) implementations, ensuring strict schema adherence across the entire API surface.

### 1.2 Scope

- **File 1**: `backend/app/models.py` - Pydantic models for Python backend
- **File 2**: `frontend/src/types.ts` - TypeScript interfaces for React frontend

### 1.3 Key Requirements

- Complete coverage of all Module 3 definitions from 02_PEGT_FINAL.md
- Strict adherence to all special annotations (W1, W25, K7, K12, W12, K2, etc.)
- Exact field name and data type mapping between backend and frontend
- Support for bi-directional language mapping (Polish ↔ English)

---

## 2. File Structure Overview

### 2.1 Backend File: `backend/app/models.py`

**Location**: `backend/app/models.py`

**Purpose**: Central repository for all Pydantic data models used across the FastAPI backend.

**Organization**:
1. Import statements (BaseModel, Field, validation types, datetime)
2. Base schemas (shared across multiple endpoints)
3. Opus Magnum module schemas (M1-M7)
4. Composite schemas (OpusMagnumModules, OpusMagnumJSON)
5. Logging schemas (ConversationLogEntry, SlowPathLogEntry)
6. Global API response wrapper
7. Endpoint-specific response schemas

### 2.2 Frontend File: `frontend/src/types.ts`

**Location**: `frontend/src/types.ts`

**Purpose**: Central repository for all TypeScript type definitions and interfaces.

**Organization**:
1. Base type literals (TConversationRole, TLanguage)
2. Base interfaces (IConversationLogEntry)
3. Opus Magnum module interfaces (IM1-IM7)
4. Composite interfaces (IOpusMagnumModules, IOpusMagnumJSON)
5. Logging interfaces (ISlowPathLogEntry)
6. Global API response wrapper (generic)
7. Endpoint-specific response interfaces
8. WebSocket message types

---

## 3. Base Schema Definitions

### 3.1 Conversation Log Schema

**Purpose**: Track all conversation exchanges between seller and AI system.

**Key Attributes**:

| Field | Type (Python) | Type (TypeScript) | Description | Special Notes |
|-------|---------------|-------------------|-------------|---------------|
| log_id | int | number | Unique log entry identifier | Auto-generated |
| session_id | str | string | Session reference | Foreign key |
| timestamp | datetime | string | Event timestamp | ISO 8601 format (W27) |
| role | Literal["Sprzedawca", "FastPath", "FastPath-Questions"] | TConversationRole | Message sender | Enum constraint |
| content | str | string | Message content | Required |
| language | Literal["pl", "en"] | TLanguage | Message language | Enum constraint |
| journey_stage | Optional[Literal["Odkrywanie", "Analiza", "Decyzja"]] | ... \| null | Current sales stage | **(W1) Accepts null** |

**Critical Design Decision (W1)**: 
- The `journey_stage` field must accept `None`/`null` to handle initial conversation states before stage classification.

### 3.2 Opus Magnum Module Base

**Purpose**: Shared confidence scoring mechanism across all AI analysis modules.

**Key Attributes**:

| Field | Type | Range | Interpretation |
|-------|------|-------|----------------|
| confidence_score | int | 0-100 | **(W25) 90-100: High confidence, 70-89: Medium, 0-69: Low** |

**Design Rationale**:
- Provides consistent quality metrics for AI-generated insights
- Enables frontend UI to display confidence indicators
- Guides user interpretation of AI recommendations

### 3.3 M1: DNA Client Schema

**Purpose**: Holistic client profile and psychological fingerprint.

**Structure**:

| Field | Type | Description |
|-------|------|-------------|
| holistic_summary | string | Comprehensive client overview |
| main_motivation | string | Primary purchase driver |
| communication_style | string | Preferred interaction pattern |
| key_levers | List[Dict[str, str]] | Persuasion arguments with rationale |
| red_flags | List[str] | Warning signals and objections |

**Critical Design Note (W3)**:
- Python `List[Dict[str, str]]` maps to TypeScript `Array<{ argument: string; rationale: string }>`
- Each lever contains two fields: `argument` and `rationale`

### 3.4 M2: Tactical Indicators Schema

**Purpose**: Real-time sales opportunity metrics.

**Structure**:

| Field | Type | Description |
|-------|------|-------------|
| purchase_temperature | Dict | Value (0-100) and label ("Zimny"/"Ciepły"/"Gorący") |
| churn_risk | Dict | Level, percentage, and reason |
| fun_drive_risk | Dict | Test drive abandonment risk |

**Design Pattern**:
- Each indicator uses composite dictionary structure for richer context
- Supports both quantitative (percentage) and qualitative (label) data

### 3.5 M3: Psychometric Profile Schema

**Purpose**: Deep psychological profiling using established frameworks.

**Frameworks Included**:
1. **DISC Model**: Dominant personality type (D/I/S/C)
2. **Big Five Traits**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
3. **Schwartz Values**: Universal human values

**Structure Example**:

```
dominant_disc: { type: "D", rationale: "Client shows directive behavior..." }
big_five_traits: {
  openness: { level: "High", score: 85 },
  conscientiousness: { level: "Medium", score: 72 },
  ...
}
schwartz_values: [
  { value: "Achievement", rationale: "Frequent success mentions" }
]
```

### 3.6 M4: Deep Motivation Schema

**Purpose**: Core psychological drivers and evidence.

**Structure**:

| Field | Type | Description |
|-------|------|-------------|
| key_insight | string | Central motivational finding |
| evidence_quotes | List[str] | Direct client quotes supporting insight |
| tesla_hook | string | Tesla-specific engagement angle |

### 3.7 M5: Predictive Paths Schema

**Purpose**: Forecasted customer journey trajectories.

**Path Structure**:

| Field | Type | Description |
|-------|------|-------------|
| path | string | Scenario description |
| probability | number | Likelihood percentage (0-100) |
| recommendations | List[str] | Suggested seller actions |

### 3.8 M6: Strategic Playbook Schema

**Purpose**: Situation-specific response templates.

**Play Structure**:

| Field | Type | Description |
|-------|------|-------------|
| title | string | Play identifier |
| trigger | string | Activation condition |
| content | List[str] | Step-by-step script lines |
| confidence_score | number | Play relevance confidence |

### 3.9 M7: Decision Vectors Schema

**Purpose**: Stakeholder influence mapping.

**Vector Structure**:

| Field | Type | Description |
|-------|------|-------------|
| stakeholder | string | Decision influencer (e.g., "Żona") |
| influence | string | Impact level (High/Medium/Low) |
| vector | string | Influence direction |
| focus | string | Key concern area |
| strategy | string | Engagement approach |
| confidence_score | number | Vector reliability |

---

## 4. Composite Schemas

### 4.1 OpusMagnumModules

**Purpose**: Aggregate container for all seven analysis modules.

**Structure**:
```
{
  dna_client: M1DnaClient,
  tactical_indicators: M2TacticalIndicators,
  psychometric_profile: M3PsychometricProfile,
  deep_motivation: M4DeepMotivation,
  predictive_paths: M5PredictivePaths,
  strategic_playbook: M6StrategicPlaybook,
  decision_vectors: M7DecisionVectors
}
```

### 4.2 OpusMagnumJSON

**Purpose**: Complete Slow Path AI analysis output.

**Structure**:

| Field | Type | Description |
|-------|------|-------------|
| overall_confidence | int (0-100) | Aggregate analysis confidence |
| suggested_stage | Literal | Recommended journey stage (PL/EN values) |
| modules | OpusMagnumModules | All seven module outputs |

**Critical Language Mapping (K3)**:
- Accepts both Polish ("Odkrywanie", "Analiza", "Decyzja") and English ("Discovery", "Analysis", "Decision") values
- Backend must implement bi-directional mapping dictionaries (detailed in Section 8)

### 4.3 SlowPathLogEntry

**Purpose**: Audit trail for asynchronous AI analysis.

**Structure**:

| Field | Type | Description |
|-------|------|-------------|
| log_id | int | Unique log identifier |
| session_id | string | Session reference |
| timestamp | datetime/string | Analysis completion time |
| json_output | OpusMagnumJSON | Complete analysis result |
| status | Literal["Success", "Error"] | Analysis outcome |

---

## 5. Global API Response Wrapper

### 5.1 GlobalAPIResponse Schema

**Purpose**: Standardized response format across all endpoints.

**Structure**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | Literal["success", "fail", "error"] | Yes | Response outcome |
| data | dict (Python) / T (TypeScript generic) | No | Payload data |
| message | string | No | Error/info message |

**Design Pattern**:
- **TypeScript**: Uses generic type parameter `IGlobalAPIResponse<T>` for type safety
- **Python**: Uses `Optional[dict]` for flexibility (Pydantic BaseModel)

**Status Values**:
- `"success"`: Request completed successfully, data present
- `"fail"`: Client error (4xx), validation failed
- `"error"`: Server error (5xx), unexpected failure

---

## 6. Endpoint-Specific Schemas

### 6.1 Endpoint 3 (POST /api/v1/sessions/send) - (K7)

**Purpose**: Fast Path response with AI-generated suggestions.

**SendResponseData Schema**:

| Field | Type | Description |
|-------|------|-------------|
| suggested_response | string | AI-generated seller response |
| suggested_questions | List[str] / string[] | Follow-up question suggestions |

**Response Wrapper**: `IGlobalAPIResponse<ISendResponseData>`

**Design Notes**:
- TypeScript interface name: `ISendResponseData`
- Python Pydantic model name: `SendResponseData`
- Delivered within 2-second P95 latency requirement (per UAT-1)

### 6.2 Endpoint 7 (GET /api/v1/admin/feedback/grouped) - (K12)

**Purpose**: Thematic grouping of seller feedback.

**FeedbackGroupingResponse Schema**:

| Field | Type | Description |
|-------|------|-------------|
| groups | Array of objects | Feedback theme clusters |

**Group Object Structure**:

| Field | Type | Description |
|-------|------|-------------|
| theme_name | string | Cluster label (e.g., "zbyt łagodne") |
| count | number | Occurrences in cluster |
| representative_note | string | Example feedback text |

**Response Wrapper**: `IGlobalAPIResponse<FeedbackGroupingResponse>`

**Use Case**: Powers AI Dojo feedback analysis UI (F-3.1)

### 6.3 Endpoint 10 (GET /api/v1/admin/rag/list) - (W12)

**Purpose**: Retrieve all RAG knowledge nuggets for admin management.

**INuggetPayload Schema**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Nugget headline |
| content | string | Yes | Full nugget text |
| keywords | string | Yes | CSV keyword list (e.g., "leasing, vat, b2b") |
| language | TLanguage | Yes | Content language (pl/en) |
| type | string | No | Nugget category |
| tags | string[] | No | Additional metadata tags |
| archetype_filter | string[] | No | Applicable client archetypes |

**IRAGListResponse Schema**:

| Field | Type | Description |
|-------|------|-------------|
| nuggets | Array of objects | All RAG entries |

**Nugget Object Structure**:

| Field | Type | Description |
|-------|------|-------------|
| id | string | Qdrant point ID |
| payload | INuggetPayload | Nugget metadata and content |

**Response Wrapper**: `IGlobalAPIResponse<IRAGListResponse>`

**Design Notes**:
- Each nugget includes both Qdrant ID (for deletion operations) and full payload
- Supports language-filtered queries via query parameter

---

## 7. WebSocket Message Schema (K2)

### 7.1 WebSocketMessage Type

**Purpose**: Real-time Slow Path progress updates.

**Endpoint**: `wss://{domain}/api/v1/ws/sessions/{session_id}`

**Message Structure**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | Literal | Yes | Message category |
| status | Literal["Success", "Error"] | No | Final analysis status |
| data | IOpusMagnumJSON | No | Complete analysis result |
| message | string | No | Human-readable status text |
| progress | number (0-100) | No | Processing percentage |

**Message Types**:
- `"slow_path_update"`: Final analysis complete
- `"slow_path_error"`: Analysis failed
- `"slow_path_progress"`: Incremental progress update

**Design Pattern**:
- TypeScript discriminated union type for type safety
- Server→Client only (no client messages required)

**Authentication Requirement (W30)**:
- Backend must validate `session_id` exists in `sessions` table before accepting WebSocket connection
- Return 403 Forbidden if session invalid

**Example Messages**:

```
Success:
{
  "type": "slow_path_update",
  "status": "Success",
  "data": { /* OpusMagnumJSON */ },
  "message": "Processing completed"
}

Error:
{
  "type": "slow_path_error",
  "status": "Error",
  "message": "API connection failed"
}

Progress:
{
  "type": "slow_path_progress",
  "progress": 45,
  "message": "Analyzing psychometric profile..."
}
```

---

## 8. Language Mapping Logic (K3)

### 8.1 Purpose

Handle bi-directional conversion between Polish and English journey stage values, required due to:
- Frontend uses Polish labels in UI
- Slow Path AI (Prompt 4.4) may return English values
- API requests use Polish values

### 8.2 Backend Mapping Dictionaries

**Python Implementation** (to be included in `backend/app/models.py` or utility module):

```
STAGE_TO_EN = {
    'Odkrywanie': 'Discovery',
    'Analiza': 'Analysis',
    'Decyzja': 'Decision'
}

STAGE_TO_PL = {
    'Discovery': 'Odkrywanie',
    'Analysis': 'Analiza',
    'Decision': 'Decyzja'
}
```

**Usage Scenarios**:

1. **Before sending to Slow Path AI**:
   - Convert Polish stage from request to English for prompt consistency
   - Example: `stage_en = STAGE_TO_EN.get(journey_stage, journey_stage)`

2. **After receiving from Slow Path AI**:
   - Convert English `suggested_stage` back to Polish for frontend consumption
   - Example: `suggested_stage_pl = STAGE_TO_PL.get(opus_magnum_json["suggested_stage"], current_stage)`
   - Fallback to `current_stage` if mapping fails

### 8.3 Schema Flexibility

**OpusMagnumJSON.suggested_stage Field**:
- Must accept both Polish and English values in type definition
- Python: `Literal["Odkrywanie", "Analiza", "Decyzja", "Discovery", "Analysis", "Decision"]`
- TypeScript: `"Odkrywanie" | "Analiza" | "Decyzja" | "Discovery" | "Analysis" | "Decision"`

---

## 9. Data Type Mapping Reference

### 9.1 Primitive Type Equivalents

| Python (Pydantic) | TypeScript | Notes |
|-------------------|------------|-------|
| str | string | Direct mapping |
| int | number | No distinction in TS |
| float | number | No distinction in TS |
| bool | boolean | Direct mapping |
| datetime | string | ISO 8601 format (W27) |
| Optional[T] | T \| null / undefined | Nullable types |
| Literal["A", "B"] | "A" \| "B" | Enum-like literals |

### 9.2 Collection Type Equivalents

| Python (Pydantic) | TypeScript | Notes |
|-------------------|------------|-------|
| List[T] | T[] or Array<T> | Direct mapping |
| Dict[str, str] | { [key: string]: string } | String-keyed objects |
| Dict[str, Union[str, int]] | { [key: string]: string \| number } | Mixed value types |
| List[Dict[str, str]] | Array<{ [key: string]: string }> | (W3) List of dictionaries |

### 9.3 Complex Structure Equivalents

**Example: M1DnaClient.key_levers**

Python:
```
List[Dict[str, str]]
Field(..., description="e.g., [{'argument': 'TCO', 'rationale': '...'}]")
```

TypeScript:
```
Array<{ argument: string; rationale: string }>
```

**Critical Design Note (W3)**:
- Avoid generic string-keyed dictionaries in TypeScript when structure is known
- Use typed object shapes for better IDE support and type safety

---

## 10. Validation Rules and Constraints

### 10.1 Pydantic Field Validators

**Confidence Score Validation (W25)**:
```
confidence_score: int = Field(..., ge=0, le=100)
```
- Enforces 0-100 range
- Used in `OpusMagnumModuleBase` and inherited by all modules

**Literal Type Constraints**:
```
language: Literal["pl", "en"]
role: Literal["Sprzedawca", "FastPath", "FastPath-Questions"]
status: Literal["success", "fail", "error"]
```
- Provides compile-time and runtime validation
- Prevents invalid enum values

**Optional Fields with Defaults**:
```
journey_stage: Optional[Literal[...]] = None
```
- Explicitly handles null case (W1)

### 10.2 TypeScript Type Safety

**Union Types for Nullability**:
```
journey_stage: "Odkrywanie" | "Analiza" | "Decyzja" | null
```
- Forces null-check handling in frontend code

**Generic Response Types**:
```
IGlobalAPIResponse<T>
```
- Provides end-to-end type safety for API responses
- Example: `IGlobalAPIResponse<ISendResponseData>` ensures data field matches expected structure

**Discriminated Unions for WebSocket**:
```
type WebSocketMessage = 
  | { type: "slow_path_update"; status: "Success" | "Error"; data?: IOpusMagnumJSON }
  | { type: "slow_path_error"; message: string }
  | { type: "slow_path_progress"; progress: number }
```
- Enables TypeScript to narrow types based on `type` field

---

## 11. Import Dependencies

### 11.1 Backend (Python) Imports

**Required Packages**:
```
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Union
from datetime import datetime
```

**Rationale**:
- `BaseModel`: Pydantic schema base class
- `Field`: Validation and metadata
- Type hints: Runtime validation and IDE support
- `datetime`: Timestamp handling

### 11.2 Frontend (TypeScript) Imports

**No External Imports Required**:
- Pure TypeScript types and interfaces
- No runtime dependencies
- Can be used throughout React application with simple `import type` statements

---

## 12. File Generation Strategy

### 12.1 Python File Organization

**Section Order**:
1. Module docstring and metadata
2. Import statements
3. Base schemas (ConversationLogEntry, OpusMagnumModuleBase)
4. M1-M7 module schemas (in numerical order)
5. Composite schemas (OpusMagnumModules, OpusMagnumJSON)
6. Logging schemas (SlowPathLogEntry)
7. Global response wrapper (GlobalAPIResponse)
8. Endpoint-specific schemas (SendResponseData, FeedbackGroupingResponse, etc.)
9. Utility dictionaries (STAGE_TO_EN, STAGE_TO_PL)

**Naming Conventions**:
- Class names: PascalCase (e.g., `SendResponseData`)
- Field names: snake_case (e.g., `suggested_response`)
- Follow PEP 8 standards

### 12.2 TypeScript File Organization

**Section Order**:
1. File header comment
2. Base type literals (TConversationRole, TLanguage)
3. Base interfaces (IConversationLogEntry)
4. Base module interface (IOpusMagnumModuleBase)
5. IM1-IM7 module interfaces (in numerical order)
6. Composite interfaces (IOpusMagnumModules, IOpusMagnumJSON)
7. Logging interfaces (ISlowPathLogEntry)
8. Global response wrapper (IGlobalAPIResponse<T>)
9. Endpoint-specific interfaces (ISendResponseData, FeedbackGroupingResponse, etc.)
10. WebSocket message types (WebSocketMessage)

**Naming Conventions**:
- Interface names: PascalCase with "I" prefix (e.g., `ISendResponseData`)
- Type names: PascalCase with "T" prefix for literals (e.g., `TLanguage`)
- Field names: camelCase (e.g., `suggestedResponse`)
- Follow TypeScript/React best practices

---

## 13. Quality Assurance Criteria

### 13.1 Completeness Checklist

**Backend (models.py) must include**:
- [ ] All imports (BaseModel, Field, List, Optional, Literal, Dict, Union, datetime)
- [ ] ConversationLogEntry with journey_stage accepting None (W1)
- [ ] OpusMagnumModuleBase with confidence_score 0-100 validation (W25)
- [ ] M1DnaClient with key_levers as List[Dict[str, str]] (W3)
- [ ] M2TacticalIndicators through M7DecisionVectors
- [ ] OpusMagnumModules and OpusMagnumJSON
- [ ] SlowPathLogEntry with OpusMagnumJSON field
- [ ] GlobalAPIResponse with Optional[dict]
- [ ] SendResponseData (K7)
- [ ] FeedbackGroupingResponse (K12)
- [ ] INuggetPayload and IRAGListResponse as Pydantic models (W12)
- [ ] STAGE_TO_EN and STAGE_TO_PL dictionaries (K3)

**Frontend (types.ts) must include**:
- [ ] TConversationRole and TLanguage type literals
- [ ] IConversationLogEntry with timestamp: string and journey_stage: ... | null (W1, W27)
- [ ] IOpusMagnumModuleBase with confidence_score: number (W25)
- [ ] IM1DnaClient with key_levers: Array<{ argument: string; rationale: string }> (W3)
- [ ] IM2TacticalIndicators through IM7DecisionVectors
- [ ] IOpusMagnumModules and IOpusMagnumJSON
- [ ] ISlowPathLogEntry
- [ ] IGlobalAPIResponse<T> generic interface
- [ ] ISendResponseData (K7)
- [ ] FeedbackGroupingResponse (K12)
- [ ] INuggetPayload and IRAGListResponse (W12)
- [ ] WebSocketMessage discriminated union (K2)

### 13.2 Accuracy Verification

**Field-Level Validation**:
- [ ] All field names match exactly between Python and TypeScript (accounting for snake_case vs camelCase)
- [ ] All data types map correctly per Section 9
- [ ] All special annotations (W1, W25, K7, K12, W12, K2, W3) are addressed
- [ ] Language mapping supports both PL and EN values (K3)

**Structural Validation**:
- [ ] Nested structures maintain consistency (e.g., OpusMagnumModules contains all M1-M7)
- [ ] Generic types properly implemented (IGlobalAPIResponse<T>)
- [ ] Discriminated unions use correct TypeScript patterns (WebSocketMessage)

### 13.3 Standards Compliance

**Python Standards**:
- [ ] PEP 8 formatting (line length, spacing, naming)
- [ ] Pydantic best practices (Field validators, model Config if needed)
- [ ] Type hints for all fields
- [ ] Docstrings for complex models

**TypeScript Standards**:
- [ ] Consistent interface naming (I prefix)
- [ ] Type vs Interface usage (types for unions/literals, interfaces for objects)
- [ ] Proper generic type syntax
- [ ] Export statements for all public types

---

## 14. Usage Examples

### 14.1 Backend Usage Example

**Validating Request Data**:
```
# In FastAPI endpoint
@app.post("/api/v1/sessions/send")
async def send_message(request: SendRequest):
    # Pydantic automatically validates against schema
    session_id = request.session_id
    user_input = request.user_input
    language = request.language  # Guaranteed to be "pl" or "en"
```

**Creating Response**:
```
from models import GlobalAPIResponse, SendResponseData

response_data = SendResponseData(
    suggested_response="Rozumiem Twoje obawy...",
    suggested_questions=["Czy test drive...?", "Jak często...?"]
)

return GlobalAPIResponse(
    status="success",
    data=response_data.dict()
)
```

### 14.2 Frontend Usage Example

**Type-Safe API Call**:
```
import type { IGlobalAPIResponse, ISendResponseData } from './types';

async function sendMessage(input: string) {
  const response = await fetch('/api/v1/sessions/send', {
    method: 'POST',
    body: JSON.stringify({ session_id, user_input: input, ... })
  });
  
  const data: IGlobalAPIResponse<ISendResponseData> = await response.json();
  
  if (data.status === 'success' && data.data) {
    // TypeScript knows data.data has suggestedResponse and suggestedQuestions
    setSuggestion(data.data.suggested_response);
    setQuestions(data.data.suggested_questions);
  }
}
```

**WebSocket Type Safety**:
```
import type { WebSocketMessage } from './types';

ws.onmessage = (event) => {
  const msg: WebSocketMessage = JSON.parse(event.data);
  
  switch (msg.type) {
    case 'slow_path_update':
      if (msg.status === 'Success' && msg.data) {
        setOpusMagnum(msg.data);
      }
      break;
    case 'slow_path_error':
      setError(msg.message);
      break;
    case 'slow_path_progress':
      setProgress(msg.progress);
      break;
  }
};
```

---

## 15. Maintenance and Evolution

### 15.1 Adding New Fields

**Process**:
1. Update schema definition in 02_PEGT_FINAL.md (source of truth)
2. Modify both `backend/app/models.py` and `frontend/src/types.ts` simultaneously
3. Ensure data type mapping follows Section 9 conventions
4. Update API documentation and integration tests
5. Run type checker (mypy for Python, tsc for TypeScript)

### 15.2 Deprecation Strategy

**For removing fields**:
1. Mark as deprecated in both files with comments
2. Make field optional with default value
3. Update consuming code to handle absence
4. Remove after deprecation period

**For changing field types**:
1. Avoid breaking changes where possible
2. If unavoidable, version the schema (e.g., `SendResponseDataV2`)
3. Maintain backward compatibility during transition

### 15.3 Validation Updates

**When business rules change**:
- Update Pydantic `Field()` validators in Python
- Add runtime validation in TypeScript if needed (e.g., Zod library)
- Document validation changes in this design document

---

## 16. Integration Points

### 16.1 Backend Integration

**FastAPI Endpoint Usage**:
- Import models from `backend/app/models.py`
- Use as type hints for request bodies and responses
- Leverage automatic Pydantic validation and OpenAPI schema generation

**Database Integration**:
- Use Pydantic models as intermediary between SQLAlchemy ORM and API
- Serialize to/from JSON for PostgreSQL JSONB columns (OpusMagnumJSON storage)

### 16.2 Frontend Integration

**React Component Usage**:
- Import types from `frontend/src/types.ts`
- Use in component props, state, and API call return types
- Integrate with state management (Zustand store definitions)

**API Client Library**:
- Define typed API client functions using these interfaces
- Example: `async function sendMessage(req: SendRequest): Promise<IGlobalAPIResponse<ISendResponseData>>`

### 16.3 Testing Integration

**Backend Testing**:
- Use Pydantic models to generate test fixtures
- Validate test responses match schemas
- Mock objects using model factory patterns

**Frontend Testing**:
- Create mock data conforming to TypeScript interfaces
- Type-check test code against schema definitions
- Use interfaces for Jest mock types

---

## 17. Security and Validation

### 17.1 Input Validation

**Pydantic Automatic Validation**:
- All request bodies validated before handler execution
- Invalid data returns 422 Unprocessable Entity
- Type coercion where safe (e.g., "123" → 123)

**Explicit Constraints**:
- String length limits (add via Field(max_length=...) if needed)
- Enum validation via Literal types
- Numeric range validation (e.g., confidence_score: 0-100)

### 17.2 Output Sanitization

**Prevent Injection Attacks**:
- Pydantic serialization escapes dangerous characters
- Frontend must still sanitize before rendering HTML (use React's default escaping)

**Data Leakage Prevention**:
- Ensure sensitive fields not included in response models
- Use separate schemas for different security contexts if needed

### 17.3 Type Safety as Security

**Compile-Time Guarantees**:
- TypeScript prevents undefined field access
- Pydantic prevents runtime type mismatches
- Reduces entire classes of bugs (null pointer exceptions, type errors)

---

## 18. Performance Considerations

### 18.1 Schema Complexity

**Impact**:
- Deeply nested schemas (OpusMagnumJSON) require more parsing time
- Acceptable for Slow Path (15-20s total latency)
- Fast Path schemas kept simple (SendResponseData) for <2s target

### 18.2 Validation Overhead

**Pydantic Performance**:
- Modern Pydantic v2 uses Rust core for fast validation
- Negligible overhead for typical request sizes (<10KB)

**Optimization Strategies**:
- Use `model_validate_json()` for direct JSON parsing (faster than dict intermediate)
- Cache compiled validators if dynamically generating schemas

### 18.3 Serialization Optimization

**Frontend**:
- Avoid unnecessary deep clones of large OpusMagnumJSON objects
- Use immutable state updates for performance (Zustand best practices)

**Backend**:
- Use `.model_dump()` instead of deprecated `.dict()` for Pydantic v2
- Consider `exclude_unset=True` for partial updates

---

## 19. Error Handling Patterns

### 19.1 Schema Validation Failures

**Backend Behavior**:
```
Request with invalid data
  ↓
Pydantic raises ValidationError
  ↓
FastAPI catches and returns:
{
  "status": "fail",
  "message": "Validation error: journey_stage must be one of ['Odkrywanie', 'Analiza', 'Decyzja']",
  "data": null
}
```

**Frontend Handling**:
```
if (response.status === 'fail') {
  showValidationError(response.message);
}
```

### 19.2 Language Mapping Failures

**Scenario**: Slow Path returns unexpected stage value

**Backend Strategy**:
```
suggested_stage_pl = STAGE_TO_PL.get(
    opus_magnum_json["suggested_stage"], 
    current_stage  # Fallback to current stage
)
```

**Rationale**:
- Graceful degradation instead of error
- Logs warning for debugging
- System remains functional

### 19.3 WebSocket Schema Violations

**Scenario**: Server sends malformed WebSocketMessage

**Frontend Strategy**:
```
try {
  const msg: WebSocketMessage = JSON.parse(event.data);
  // TypeScript validates at compile time, but runtime check needed:
  if (!msg.type || !['slow_path_update', 'slow_path_error', 'slow_path_progress'].includes(msg.type)) {
    throw new Error('Invalid message type');
  }
  // Process message
} catch (error) {
  console.error('WebSocket message parsing failed:', error);
  // Continue listening, don't crash UI
}
```

---

## 20. Documentation and Comments

### 20.1 Python Model Documentation

**Required Elements**:
- Module-level docstring explaining file purpose
- Class-level docstrings for complex models
- Field descriptions using `Field(description="...")`
- Special annotation comments (e.g., `# (W1) journey_stage accepts null`)

**Example**:
```
class SendResponseData(BaseModel):
    """
    Response schema for Fast Path AI suggestions.
    
    Returned by POST /api/v1/sessions/send (Endpoint 3, F-2.2).
    Must deliver within 2-second P95 latency (per UAT-1).
    """
    suggested_response: str = Field(
        ..., 
        description="AI-generated seller response text"
    )
    suggested_questions: List[str] = Field(
        ..., 
        description="Follow-up question suggestions (typically 2-3)"
    )
```

### 20.2 TypeScript Interface Documentation

**Required Elements**:
- File header explaining purpose and usage
- JSDoc comments for complex interfaces
- Inline comments for special annotations
- Usage examples in comments for non-obvious patterns

**Example**:
```
/**
 * Response data for Fast Path AI suggestions.
 * 
 * Returned by POST /api/v1/sessions/send (Endpoint 3, F-2.2).
 * Must deliver within 2-second P95 latency (per UAT-1).
 * 
 * @see GlobalAPIResponse for wrapper structure
 */
interface ISendResponseData {
  /** AI-generated seller response text */
  suggested_response: string;
  
  /** Follow-up question suggestions (typically 2-3) */
  suggested_questions: string[];
}
```

### 20.3 Special Annotation Documentation

**All W* and K* annotations from 02_PEGT_FINAL.md must be preserved in comments**:
- (W1): journey_stage accepts null
- (W3): List[Dict] mapping guidance
- (W12): RAG list response schemas
- (W25): Confidence score interpretation
- (W27): ISO 8601 timestamp format
- (K2): WebSocket message definition
- (K3): Language mapping algorithm
- (K7): SendResponseData schema
- (K12): FeedbackGroupingResponse schema

---

## 21. Success Metrics

### 21.1 Functional Completeness

**Measurement**:
- [ ] All 14 endpoints have corresponding request/response schemas
- [ ] All special annotations addressed
- [ ] Both files compile/validate without errors
- [ ] End-to-end type safety verified (API call from TS frontend to Python backend)

### 21.2 Development Experience

**Indicators**:
- IDE autocomplete works for all schema fields
- Type errors caught at development time (before runtime)
- API documentation auto-generated from schemas (FastAPI OpenAPI)
- Frontend developers can work independently with clear type contracts

### 21.3 Maintenance Efficiency

**Target**:
- Schema changes can be made in <30 minutes (both files updated)
- No runtime type errors in production (after proper testing)
- New developers can understand schema structure in <2 hours

---

## 22. Deliverables

### 22.1 File 1: backend/app/models.py

**Contents**:
- Complete Pydantic model definitions
- All imports and dependencies
- Language mapping dictionaries
- Inline documentation with special annotations

**Acceptance Criteria**:
- Passes `mypy` type checking
- Pydantic validation works for sample data
- Can be imported by FastAPI endpoints without errors

### 22.2 File 2: frontend/src/types.ts

**Contents**:
- Complete TypeScript type and interface definitions
- All base types and complex structures
- JSDoc documentation with special annotations

**Acceptance Criteria**:
- Passes `tsc --noEmit` type checking
- Can be imported by React components without errors
- Provides full IDE autocomplete support

### 22.3 Validation Artifacts

**To be provided**:
- Sample JSON request/response payloads for each endpoint
- Type validation test results (Python and TypeScript)
- Checklist verification (Section 13.1) completed

---

## 23. Dependencies and Prerequisites

### 23.1 Backend Dependencies

**Required Python Packages**:
- `pydantic>=2.0` (for BaseModel, Field, validators)
- `python>=3.10` (for modern type hints support)

**Installation**:
```
pip install pydantic
```

### 23.2 Frontend Dependencies

**Required TypeScript Version**:
- `typescript>=4.5` (for template literal types and advanced unions)

**Installation**:
```
npm install typescript --save-dev
```

### 23.3 Development Tools

**Recommended**:
- Python: `mypy` for static type checking
- TypeScript: Built-in `tsc` compiler
- IDE: VSCode with Pylance and TypeScript language server

---

## 24. Risk Assessment

### 24.1 Schema Drift Risk

**Risk**: Backend and frontend schemas diverge over time.

**Mitigation**:
- Maintain 02_PEGT_FINAL.md as single source of truth
- Automated tests comparing schema fields
- Code review checklist for schema changes

**Impact**: Medium | **Likelihood**: Medium | **Mitigation Priority**: High

### 24.2 Type Mapping Errors

**Risk**: Incorrect Python ↔ TypeScript type mappings cause runtime failures.

**Mitigation**:
- Follow Section 9 mapping reference strictly
- Integration tests with real API calls
- Sample data validation in both environments

**Impact**: High | **Likelihood**: Low | **Mitigation Priority**: High

### 24.3 Missing Validation

**Risk**: Invalid data passes schema validation.

**Mitigation**:
- Add explicit Field() validators for business rules
- Comprehensive unit tests for edge cases
- Security review of validation rules

**Impact**: Medium | **Likelihood**: Low | **Mitigation Priority**: Medium

---

## 25. Future Enhancements

### 25.1 Schema Versioning

**Potential Need**: Breaking changes require multiple schema versions.

**Approach**:
- Suffix with version (e.g., `SendResponseDataV2`)
- Maintain both versions during transition period
- Deprecation warnings in API responses

### 25.2 Code Generation

**Opportunity**: Auto-generate TypeScript from Pydantic models.

**Tools to Explore**:
- `pydantic-to-typescript` package
- Custom script using Pydantic schema export
- OpenAPI TypeScript generator (from FastAPI's generated spec)

**Benefits**:
- Guaranteed schema synchronization
- Reduced manual maintenance
- Single source of truth enforcement

### 25.3 Runtime Validation (Frontend)

**Opportunity**: Add Zod or similar for runtime TS validation.

**Use Cases**:
- Validating external API responses
- User input validation before submit
- Enhanced error messages

**Tradeoff**: Added bundle size vs. type safety

---

## Appendix A: Special Annotation Reference

| Annotation | Description | Location |
|------------|-------------|----------|
| W1 | journey_stage accepts null | ConversationLogEntry |
| W3 | List[Dict] mapping to TypeScript Array<{...}> | M1DnaClient.key_levers |
| W12 | RAG list response schemas | INuggetPayload, IRAGListResponse |
| W25 | Confidence score interpretation (90-100 High, 70-89 Medium, 0-69 Low) | OpusMagnumModuleBase |
| W27 | ISO 8601 timestamp format | IConversationLogEntry.timestamp |
| K2 | WebSocket message type definition | WebSocketMessage |
| K3 | Language mapping algorithm (PL ↔ EN) | STAGE_TO_EN, STAGE_TO_PL |
| K7 | SendResponseData schema | Endpoint 3 response |
| K12 | FeedbackGroupingResponse schema | Endpoint 7 response |

---

## Appendix B: Complete Endpoint Schema Mapping

| Endpoint | Method | Request Schema | Response Schema |
|----------|--------|----------------|-----------------|
| 1. /api/v1/sessions/new | POST | (none) | { session_id: string } |
| 2. /api/v1/sessions/{session_id} | GET | Path: session_id | { conversation_log: [], slow_path_log: ... } |
| 3. /api/v1/sessions/send | POST | { session_id, user_input, journey_stage, language } | IGlobalAPIResponse<ISendResponseData> |
| 4. /api/v1/sessions/refine | POST | { session_id, original_input, bad_suggestion, feedback_note, language } | IGlobalAPIResponse<{ refined_suggestion: string }> |
| 5. /api/v1/sessions/retry_slowpath | POST | { session_id } | { message: string } |
| 6. /api/v1/sessions/end | POST | { session_id, final_status } | { message: string } |
| 7. /api/v1/admin/feedback/grouped | GET | Query: { language } | IGlobalAPIResponse<FeedbackGroupingResponse> |
| 8. /api/v1/admin/feedback/details | GET | Query: { note, language } | { details: [...] } |
| 9. /api/v1/admin/feedback/create_standard | POST | { trigger_context, golden_response, language, category } | { message: string } |
| 10. /api/v1/admin/rag/list | GET | Query: { language } | IGlobalAPIResponse<IRAGListResponse> |
| 11. /api/v1/admin/rag/add | POST | { title, content, keywords, language } | { message: string } |
| 12. /api/v1/admin/rag/delete/{nugget_id} | DELETE | Path: nugget_id | { message: string } |
| 13. /api/v1/admin/analytics/v1_dashboard | GET | Query: { date_from?, date_to?, language? } | { chart1_data, chart2_data, chart3_data } |
| 14. /api/v1/ws/sessions/{session_id} | WebSocket | Path: session_id | WebSocketMessage types |

---

## Appendix C: Confidence Score Interpretation Guide (W25)

**Used in**: All OpusMagnum modules (M1-M7) and OpusMagnumJSON

| Range | Level | Interpretation | UI Recommendation |
|-------|-------|----------------|-------------------|
| 90-100 | High | AI is highly confident in analysis | Green indicator, display prominently |
| 70-89 | Medium | AI has moderate confidence | Yellow indicator, display with caution note |
| 0-69 | Low | AI has low confidence, human review recommended | Red indicator, suggest manual review |

**Usage in Prompts**:
- LLM instructions must include confidence score calculation guidance
- Scores should reflect data quality, conversation depth, and pattern clarity
- Low scores should trigger suggestions for more seller questions
