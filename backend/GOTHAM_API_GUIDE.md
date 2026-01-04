# Tesla-Gotham v4.5 - CEPiK & GUS API Integration Guide

## Overview

Tesla-Gotham v4.5 introduces real-time integration with two major Polish government data sources:

1. **CEPiK API** - Centralna Ewidencja Pojazdów i Kierowców (Central Vehicle and Driver Registry)
2. **GUS API** - Główny Urząd Statystyczny (Polish Central Statistical Office)

Both APIs are **publicly accessible** and **require no authentication keys**.

---

## CEPiK API Integration

### What is CEPiK?

CEPiK maintains the official registry of all vehicles and drivers in Poland. It provides:
- Vehicle registration data
- Technical specifications (brand, model, engine, emissions)
- Registration dates and locations
- Statistical aggregations

### API Endpoints

#### 1. Get Available Dictionaries
**Endpoint:** `GET /api/v1/gotham/cepik/dictionaries`

**Description:** Retrieves list of available reference dictionaries for vehicle data lookups.

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "data": [
      {"name": "marki-pojazdow"},
      {"name": "paliwa"},
      {"name": "kategorie-pojazdow"}
    ]
  }
}
```

#### 2. Get Specific Dictionary
**Endpoint:** `GET /api/v1/gotham/cepik/dictionary/{dictionary_name}`

**Parameters:**
- `dictionary_name` (path): Name of dictionary (e.g., "marki-pojazdow", "paliwa")

**Useful Dictionaries:**
- `marki-pojazdow` - Vehicle brands
- `paliwa` - Fuel types
- `kategorie-pojazdow` - Vehicle categories

**Example Request:**
```bash
GET /api/v1/gotham/cepik/dictionary/marki-pojazdow
```

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "data": [
      {"name": "BMW", "count": 125430},
      {"name": "Mercedes-Benz", "count": 98765},
      {"name": "Audi", "count": 87654}
    ]
  }
}
```

#### 3. Get Daily Statistics
**Endpoint:** `GET /api/v1/gotham/cepik/statistics`

**Query Parameters:**
- `date` (required): Date in YYYYMMDD format
- `voivodeship` (optional): TERYT code for voivodeship filtering

**Example Request:**
```bash
GET /api/v1/gotham/cepik/statistics?date=20250104&voivodeship=24
```

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "date": "20250104",
    "voivodeship": "24",
    "total_searches": 1523
  }
}
```

### Use Cases for CEPiK Data

1. **Market Analysis**
   - Track vehicle brand popularity by region
   - Analyze fuel type distribution
   - Identify EV adoption trends

2. **Competitive Intelligence**
   - Monitor premium vehicle registrations
   - Identify leasing expiration patterns
   - Target high-value replacement opportunities

3. **Sales Targeting**
   - Geographic focus based on premium vehicle density
   - Timing outreach to leasing expiration windows
   - Competitive brand analysis

---

## GUS API Integration

### What is GUS?

GUS (Główny Urząd Statystyczny) is Poland's Central Statistical Office, providing comprehensive socio-economic data through multiple APIs:

- **BDL** - Bank Danych Lokalnych (Local Data Bank): demographic and economic indicators
- **TERYT** - Territorial division data (voivodeships, counties, municipalities)
- **REGON** - Business entity registry
- **SDG** - Sustainable Development Goals tracking

### API Endpoints

#### 1. Get Voivodeships List
**Endpoint:** `GET /api/v1/gotham/gus/voivodeships`

**Description:** Returns all 16 Polish voivodeships with TERYT codes.

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "voivodeships": [
      {"teryt": "24", "name": "śląskie", "en": "Silesian"},
      {"teryt": "14", "name": "mazowieckie", "en": "Masovian"},
      {"teryt": "30", "name": "wielkopolskie", "en": "Greater Poland"}
    ]
  }
}
```

#### 2. Get Regional Demographics
**Endpoint:** `GET /api/v1/gotham/gus/demographics/{voivodeship}`

**Parameters:**
- `voivodeship` (path): Voivodeship name (e.g., "śląskie", "mazowieckie")

**Example Request:**
```bash
GET /api/v1/gotham/gus/demographics/śląskie
```

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "voivodeship": "śląskie",
    "teryt_code": "24",
    "population": 4492330,
    "population_year": 2023,
    "avg_salary_pln": 6842.50,
    "salary_year": 2023
  }
}
```

#### 3. Get Market Intelligence
**Endpoint:** `GET /api/v1/gotham/gus/market-intelligence/{voivodeship}`

**Description:** Comprehensive market analysis combining multiple GUS data sources.

**Example Request:**
```bash
GET /api/v1/gotham/gus/market-intelligence/śląskie
```

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "voivodeship": "śląskie",
    "teryt_code": "24",
    "demographics": {
      "voivodeship": "śląskie",
      "teryt_code": "24",
      "population": 4492330,
      "avg_salary_pln": 6842.50
    },
    "market_potential_score": 78,
    "data_source": "GUS API (BDL)",
    "timestamp": "2025-01-04T10:30:00"
  }
}
```

**Market Potential Score (0-100):**
- **90-100**: Premium market - focus on high-end features
- **70-89**: Upper mid-market - emphasize TCO and technology
- **40-69**: Mid-market - highlight savings and financing
- **0-39**: Entry market - focus on basic models and affordability

#### 4. Get GUS Summary
**Endpoint:** `GET /api/v1/gotham/gus/summary/{voivodeship}`

**Description:** Human-readable summary formatted for AI prompts and dashboards.

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "voivodeship": "śląskie",
    "summary": "📊 GUS Intelligence: Dane Regionalne - Śląskie\n\n📍 DEMOGRAFIA:\n  • Populacja: 4 492 330 mieszkańców\n  • Średnie wynagrodzenie: 6 842.50 PLN/mies.\n\n🎯 POTENCJAŁ RYNKU:\n  • Market Score: 78/100\n  • Segmentacja: Premium Market"
  }
}
```

### Use Cases for GUS Data

1. **Regional Market Analysis**
   - Identify high-potential sales territories
   - Prioritize resource allocation by market score
   - Understand demographic purchasing power

2. **Sales Strategy**
   - Tailor messaging based on regional income levels
   - Adjust product mix recommendations
   - Set realistic sales targets

3. **Competitive Positioning**
   - Compare regional performance metrics
   - Identify underserved markets
   - Benchmark against national averages

4. **AI Context Enrichment**
   - Inject regional intelligence into sales AI prompts
   - Personalize recommendations based on local economics
   - Provide data-driven urgency signals

---

## Integration with GOTHAM Intelligence

Both CEPiK and GUS data are automatically integrated into the **GOTHAM Strategic Context Engine**.

### How It Works

The `generate_strategic_context()` function (in `context_engine.py`) now includes:

```python
generate_strategic_context(
    voivodeship="śląskie",
    include_fuel_prices=True,      # Static/manual data
    include_subsidies=True,         # Government program data
    include_gus_intel=True,         # 🆕 GUS regional intelligence
    include_leasing_intel=True,     # CEPiK leasing data
    include_infrastructure=True     # Charging infrastructure
)
```

This context is automatically injected into:
- **Slow Path AI** (Opus Magnum analysis)
- **Fast Path AI** (quick response generation)
- **Dashboard analytics**
- **Sales team briefings**

---

## Configuration

### Environment Variables

```bash
# CEPiK API Configuration
CEPIK_API_URL=https://api.cepik.gov.pl
CEPIK_USE_MOCK=true  # Set to 'false' to use real API

# No GUS API keys needed - public data
```

### Mock Data vs Real API

By default, CEPiK uses mock data (`CEPIK_USE_MOCK=true`) for development. To enable real API:

```bash
CEPIK_USE_MOCK=false
```

GUS API always uses real data (no mock).

---

## Technical Architecture

### Data Flow

```
┌─────────────────┐
│   Frontend      │
│   Dashboard     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Endpoints     │
└────────┬────────┘
         │
         ├──────────────┬─────────────┐
         ▼              ▼             ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ CEPiK        │ │ GUS         │ │ Context      │
│ Connector    │ │ Connector   │ │ Engine       │
└──────┬───────┘ └──────┬──────┘ └──────┬───────┘
       │                │               │
       ▼                ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ api.cepik    │ │ bdl.stat    │ │ Strategic    │
│ .gov.pl      │ │ .gov.pl     │ │ Context      │
└──────────────┘ └─────────────┘ └──────┬───────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │ AI Prompts   │
                                  │ (Gemini,     │
                                  │  DeepSeek)   │
                                  └──────────────┘
```

### Code Structure

```
backend/app/services/gotham/
├── __init__.py              # Module exports
├── cepik_connector.py       # CEPiK API integration
├── gus_connector.py         # GUS API integration
├── eipa_connector.py        # Charging infrastructure
└── context_engine.py        # Intelligence aggregation
```

---

## Error Handling

All endpoints follow the standard `GlobalAPIResponse` format:

**Success:**
```json
{
  "status": "success",
  "data": { ... }
}
```

**Client Error:**
```json
{
  "status": "fail",
  "message": "Voivodeship 'invalid' not found"
}
```

**Server Error:**
```json
{
  "status": "error",
  "message": "API request failed: timeout"
}
```

---

## Rate Limiting

- **CEPiK API**: Returns `X-Rate-Limit-Remaining` header
- **GUS API**: No documented rate limits (public data)

Both connectors include:
- Automatic retry with exponential backoff (3 attempts)
- Timeout protection (10-30 seconds)
- Error logging and graceful degradation

---

## Example: Building a Regional Dashboard

```python
# 1. Get voivodeship list
voivodeships = requests.get('/api/v1/gotham/gus/voivodeships').json()

# 2. For each voivodeship, get market intelligence
for voi in voivodeships['data']['voivodeships']:
    name = voi['name']

    # Get GUS intelligence
    gus_data = requests.get(f'/api/v1/gotham/gus/market-intelligence/{name}').json()
    market_score = gus_data['data']['market_potential_score']

    # Get CEPiK statistics (last 30 days)
    today = datetime.now().strftime('%Y%m%d')
    cepik_stats = requests.get(
        f'/api/v1/gotham/cepik/statistics',
        params={'date': today, 'voivodeship': voi['teryt']}
    ).json()

    # Display on dashboard
    print(f"{name}: Market Score {market_score}/100, {cepik_stats['data']['total_searches']} searches")
```

---

## Future Enhancements

### Planned Features

1. **CEPiK Vehicle Search**
   - Direct vehicle lookup by filters (brand, date range, region)
   - Premium leasing opportunity identification
   - Competitive brand analysis

2. **GUS Advanced Analytics**
   - GDP per capita trends
   - Business registration growth
   - Employment and income forecasting

3. **Real-Time Alerts**
   - Subsidy program changes
   - High-value leasing expirations
   - Regional market shifts

4. **Predictive Modeling**
   - EV adoption forecasting
   - Regional demand prediction
   - Competitive market share analysis

---

## Support & Documentation

### Official API Documentation

- **CEPiK API**: https://api.cepik.gov.pl/swagger/apicepik.json
- **GUS API Portal**: https://api.stat.gov.pl/

### Internal Documentation

- Main API docs: `/docs` (FastAPI Swagger UI)
- Health check: `/health`
- Version info: `/` (root endpoint)

### Contact

For questions or issues with the GOTHAM Intelligence module, check:
- Backend logs for detailed error messages
- API response `message` field for specific failures
- GOTHAM connector test scripts in `/backend/app/services/gotham/`

---

**Version:** 4.5.0
**Last Updated:** 2025-01-04
**Status:** Production Ready 🚀
