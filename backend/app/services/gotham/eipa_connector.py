"""
EIPA Connector - Charging Infrastructure & Wealth Mapping
==========================================================

Combines two data sources to identify high-potential Tesla markets:

1. UDT API (Urząd Dozoru Technicznego) - EV charging stations
   - Public charging station locations (AC/DC)
   - Charging capacity (kW)
   - Availability status

2. BDL GUS (Bank Danych Lokalnych - Główny Urząd Statystyczny)
   - Municipal income per capita
   - Business density
   - Population demographics

Strategic insight:
- Correlate charging infrastructure with wealth to identify underserved premium markets
- Example: High-income gmina with low charging density = expansion opportunity + sales target

API References:
- UDT: https://www.udt.gov.pl/
- BDL GUS: https://api.stat.gov.pl/Home/BdlApi

ENHANCED (v4.0): Added check_infrastructure function for city-specific queries
"""

import os
import logging
from typing import List, Dict, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

UDT_API_URL = os.getenv("UDT_API_URL", "https://www.udt.gov.pl/api/charging-stations")
GUS_API_URL = os.getenv("GUS_API_URL", "https://api.stat.gov.pl/")
GUS_API_KEY = os.getenv("GUS_API_KEY")  # Required for GUS API access


# =============================================================================
# MOCK DATA - Charging Infrastructure in Śląskie
# =============================================================================

# Tesla Superchargers (real locations + mock data)
SUPERCHARGERS_SLASKIE = [
    {
        "station_id": "SC-KAT-001",
        "name": "Tesla Supercharger Katowice - Silesia City Center",
        "address": "Chorzowska 107, 40-101 Katowice",
        "city": "Katowice",
        "county": "Katowice",
        "latitude": 50.2649,
        "longitude": 19.0238,
        "connectors": 12,
        "max_power_kw": 250,
        "operator": "Tesla",
        "status": "operational",
        "amenities": ["shopping", "restaurants", "restrooms"]
    },
    {
        "station_id": "SC-KAT-002",
        "name": "Tesla Supercharger Katowice - Galeria Katowicka",
        "address": "3 Maja 30, 40-097 Katowice",
        "city": "Katowice",
        "county": "Katowice",
        "latitude": 50.2579,
        "longitude": 19.0178,
        "connectors": 8,
        "max_power_kw": 250,
        "operator": "Tesla",
        "status": "operational",
        "amenities": ["shopping", "restaurants", "restrooms", "parking"]
    },
    {
        "station_id": "SC-GLI-001",
        "name": "Tesla Supercharger Gliwice - Forum",
        "address": "Lipowa 1, 44-100 Gliwice",
        "city": "Gliwice",
        "county": "Gliwice",
        "latitude": 50.2945,
        "longitude": 18.6714,
        "connectors": 8,
        "max_power_kw": 250,
        "operator": "Tesla",
        "status": "operational",
        "amenities": ["shopping", "restaurants"]
    },
    {
        "station_id": "SC-BB-001",
        "name": "Tesla Supercharger Bielsko-Biała - Sfera",
        "address": "Mostowa 5, 43-300 Bielsko-Biała",
        "city": "Bielsko-Biała",
        "county": "Bielsko-Biała",
        "latitude": 49.8224,
        "longitude": 19.0446,
        "connectors": 8,
        "max_power_kw": 250,
        "operator": "Tesla",
        "status": "operational",
        "amenities": ["shopping", "parking"]
    },
    {
        "station_id": "SC-CZE-001",
        "name": "Tesla Supercharger Częstochowa - Galeria Jurajska",
        "address": "Drogowców 3, 42-200 Częstochowa",
        "city": "Częstochowa",
        "county": "Częstochowa",
        "latitude": 50.8158,
        "longitude": 19.1202,
        "connectors": 8,
        "max_power_kw": 250,
        "operator": "Tesla",
        "status": "operational",
        "amenities": ["shopping", "restaurants", "restrooms"]
    },
]

# Other charging stations (Ionity, GreenWay, etc.)
OTHER_CHARGERS_SLASKIE = [
    {
        "station_id": "ION-GLI-001",
        "name": "Ionity Gliwice - A4 Highway",
        "address": "MOP Gliwice, Autostrada A4",
        "city": "Gliwice",
        "county": "Gliwice",
        "latitude": 50.3012,
        "longitude": 18.6890,
        "connectors": 6,
        "max_power_kw": 350,
        "operator": "Ionity",
        "status": "operational",
        "amenities": ["fuel", "shop", "restrooms"]
    },
    {
        "station_id": "GW-KAT-001",
        "name": "GreenWay Katowice - Spodek",
        "address": "Al. Korfantego 35, 40-005 Katowice",
        "city": "Katowice",
        "county": "Katowice",
        "latitude": 50.2650,
        "longitude": 19.0250,
        "connectors": 4,
        "max_power_kw": 50,
        "operator": "GreenWay",
        "status": "operational",
        "amenities": ["parking"]
    },
    {
        "station_id": "GW-BB-001",
        "name": "GreenWay Bielsko-Biała",
        "address": "Żywiecka 132, 43-316 Bielsko-Biała",
        "city": "Bielsko-Biała",
        "county": "Bielsko-Biała",
        "latitude": 49.8124,
        "longitude": 19.0346,
        "connectors": 4,
        "max_power_kw": 50,
        "operator": "GreenWay",
        "status": "operational",
        "amenities": []
    },
    {
        "station_id": "ORP-TYC-001",
        "name": "Orlen Charge Tychy",
        "address": "Towarowa 2, 43-100 Tychy",
        "city": "Tychy",
        "county": "Tychy",
        "latitude": 50.1312,
        "longitude": 18.9867,
        "connectors": 2,
        "max_power_kw": 150,
        "operator": "Orlen Charge",
        "status": "operational",
        "amenities": ["fuel", "shop", "restrooms"]
    },
    {
        "station_id": "ORP-SOS-001",
        "name": "Orlen Charge Sosnowiec",
        "address": "3 Maja 5, 41-200 Sosnowiec",
        "city": "Sosnowiec",
        "county": "Sosnowiec",
        "latitude": 50.2867,
        "longitude": 19.1234,
        "connectors": 2,
        "max_power_kw": 150,
        "operator": "Orlen Charge",
        "status": "operational",
        "amenities": ["fuel", "shop"]
    },
]

# Municipal wealth data (mock from GUS)
MUNICIPAL_WEALTH_DATA = {
    "Katowice": {
        "gmina": "Katowice",
        "income_per_capita_pln": 68000,
        "business_density": 155,
        "population": 290000,
        "wealth_tier": "premium",
        "ev_adoption_rate": 2.8,  # % of registered vehicles
    },
    "Gliwice": {
        "gmina": "Gliwice",
        "income_per_capita_pln": 58000,
        "business_density": 120,
        "population": 180000,
        "wealth_tier": "high",
        "ev_adoption_rate": 2.1,
    },
    "Bielsko-Biała": {
        "gmina": "Bielsko-Biała",
        "income_per_capita_pln": 52000,
        "business_density": 95,
        "population": 170000,
        "wealth_tier": "high",
        "ev_adoption_rate": 1.9,
    },
    "Tychy": {
        "gmina": "Tychy",
        "income_per_capita_pln": 48000,
        "business_density": 85,
        "population": 128000,
        "wealth_tier": "medium",
        "ev_adoption_rate": 1.5,
    },
    "Sosnowiec": {
        "gmina": "Sosnowiec",
        "income_per_capita_pln": 44000,
        "business_density": 70,
        "population": 200000,
        "wealth_tier": "medium",
        "ev_adoption_rate": 1.2,
    },
    "Częstochowa": {
        "gmina": "Częstochowa",
        "income_per_capita_pln": 46000,
        "business_density": 80,
        "population": 220000,
        "wealth_tier": "medium",
        "ev_adoption_rate": 1.4,
    },
    "Chorzów": {
        "gmina": "Chorzów",
        "income_per_capita_pln": 42000,
        "business_density": 65,
        "population": 108000,
        "wealth_tier": "medium",
        "ev_adoption_rate": 1.1,
    },
    "Rybnik": {
        "gmina": "Rybnik",
        "income_per_capita_pln": 45000,
        "business_density": 75,
        "population": 140000,
        "wealth_tier": "medium",
        "ev_adoption_rate": 1.3,
    },
}


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_charging_stations(voivodeship: str = "śląskie") -> List[Dict]:
    """
    Fetch EV charging stations from UDT registry.

    Args:
        voivodeship: Polish voivodeship to filter stations

    Returns:
        List of charging station records:
        - station_id: Unique identifier
        - name: Station name/location
        - county: County (powiat)
        - gmina: Municipality
        - latitude: GPS latitude
        - longitude: GPS longitude
        - connectors: Number of charging connectors
        - max_power_kw: Maximum charging power
        - operator: Station operator
    """
    try:
        logger.info(f"🔌 Fetching charging stations for {voivodeship}...")

        # MOCK DATA for demonstration
        # In production, replace with actual UDT API call
        all_stations = SUPERCHARGERS_SLASKIE + OTHER_CHARGERS_SLASKIE

        logger.info(f"✓ Found {len(all_stations)} charging stations in {voivodeship}")
        return all_stations

    except Exception as e:
        logger.error(f"✗ UDT API error: {e}")
        return []


def check_infrastructure(city: str) -> Dict:
    """
    Check charging infrastructure for a specific city.

    This is the main function for quick infrastructure lookup.

    Args:
        city: City name (e.g., "Katowice", "Gliwice")

    Returns:
        Dictionary with:
        - superchargers: List of Tesla Supercharger locations
        - other_chargers: List of other DC fast chargers
        - total_chargers: Total number of charging stations
        - total_connectors: Total number of connectors
        - coverage_rating: Infrastructure coverage rating (poor/fair/good/excellent)
        - nearest_supercharger: Details of the closest Supercharger
    """
    city_normalized = city.strip().title()

    # Filter stations by city
    superchargers = [s for s in SUPERCHARGERS_SLASKIE if s["city"].lower() == city_normalized.lower()]
    other_chargers = [s for s in OTHER_CHARGERS_SLASKIE if s["city"].lower() == city_normalized.lower()]

    all_chargers = superchargers + other_chargers
    total_connectors = sum(s["connectors"] for s in all_chargers)

    # Determine coverage rating
    if len(superchargers) >= 2 and total_connectors >= 20:
        coverage_rating = "excellent"
    elif len(superchargers) >= 1 and total_connectors >= 10:
        coverage_rating = "good"
    elif total_connectors >= 4:
        coverage_rating = "fair"
    else:
        coverage_rating = "poor"

    # Get nearest supercharger (for this city or closest)
    nearest_sc = superchargers[0] if superchargers else None

    # If no superchargers in city, find the closest one
    if not nearest_sc:
        # For simplicity, return Katowice as fallback (biggest hub)
        nearest_sc = next((s for s in SUPERCHARGERS_SLASKIE if s["city"] == "Katowice"), SUPERCHARGERS_SLASKIE[0])

    # Get wealth data for context
    wealth_data = MUNICIPAL_WEALTH_DATA.get(city_normalized, {})

    return {
        "city": city_normalized,
        "superchargers": superchargers,
        "supercharger_count": len(superchargers),
        "other_chargers": other_chargers,
        "other_charger_count": len(other_chargers),
        "total_chargers": len(all_chargers),
        "total_connectors": total_connectors,
        "coverage_rating": coverage_rating,
        "nearest_supercharger": nearest_sc,
        "wealth_data": wealth_data,
        "summary": f"{city_normalized}: {len(superchargers)} Superchargerów, {len(other_chargers)} innych stacji DC, łącznie {total_connectors} złączy. Ocena: {coverage_rating}."
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_municipal_wealth_data(voivodeship: str = "śląskie") -> List[Dict]:
    """
    Fetch wealth indicators from GUS (Polish Central Statistical Office).

    Args:
        voivodeship: Polish voivodeship

    Returns:
        List of municipal wealth records:
        - gmina: Municipality name
        - income_per_capita_pln: Average annual income per capita
        - business_density: Registered businesses per 1000 residents
        - population: Total population
        - wealth_tier: Categorization (low/medium/high/premium)
    """
    try:
        logger.info(f"💰 Fetching wealth data for {voivodeship}...")

        # MOCK DATA for demonstration
        # In production, use GUS BDL API with proper authentication
        mock_wealth = list(MUNICIPAL_WEALTH_DATA.values())

        logger.info(f"✓ Retrieved wealth data for {len(mock_wealth)} municipalities")
        return mock_wealth

    except Exception as e:
        logger.error(f"✗ GUS API error: {e}")
        return []


def fetch_charging_infrastructure_wealth_map(voivodeship: str = "śląskie") -> Dict:
    """
    Correlate charging infrastructure with municipal wealth.

    Returns:
        Strategic market analysis combining infrastructure and demographics:
        - stations: List of charging stations
        - municipalities: List of wealth data
        - opportunities: High-wealth / low-infrastructure gaps
        - summary: Human-readable strategic insight
    """
    stations = fetch_charging_stations(voivodeship)
    wealth = fetch_municipal_wealth_data(voivodeship)

    # Map stations to municipalities
    station_count_by_gmina = {}
    connector_count_by_gmina = {}
    for station in stations:
        gmina = station.get("city", station.get("county", "Unknown"))
        station_count_by_gmina[gmina] = station_count_by_gmina.get(gmina, 0) + 1
        connector_count_by_gmina[gmina] = connector_count_by_gmina.get(gmina, 0) + station.get("connectors", 0)

    # Identify opportunities: high wealth + low infrastructure
    opportunities = []
    for w in wealth:
        gmina = w["gmina"]
        stations_count = station_count_by_gmina.get(gmina, 0)
        connectors_count = connector_count_by_gmina.get(gmina, 0)
        wealth_tier = w["wealth_tier"]

        # Opportunity score: high wealth + few stations = expansion potential
        if wealth_tier in ["high", "premium"] and connectors_count < 15:
            opportunity_score = (w["income_per_capita_pln"] // 1000) - (connectors_count * 2)
            opportunities.append({
                "gmina": gmina,
                "wealth_tier": wealth_tier,
                "income_per_capita": w["income_per_capita_pln"],
                "population": w["population"],
                "stations_count": stations_count,
                "connectors_count": connectors_count,
                "ev_adoption_rate": w.get("ev_adoption_rate", 0),
                "opportunity_score": opportunity_score,
                "rationale": f"Premium market ({w['income_per_capita_pln']:,} PLN/capita, {w['population']:,} pop) with {connectors_count} connectors"
            })

    # Sort by opportunity score
    opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)

    # Generate summary
    if opportunities:
        top_opportunity = opportunities[0]
        summary = f"""
🎯 Strategiczna Analiza Rynku - {voivodeship.capitalize()}:

Top Opportunity: {top_opportunity['gmina']}
- Dochód/mieszkańca: {top_opportunity['income_per_capita']:,} PLN
- Populacja: {top_opportunity['population']:,}
- Stacje ładowania: {top_opportunity['stations_count']}
- Złącza łącznie: {top_opportunity['connectors_count']}
- Tier zamożności: {top_opportunity['wealth_tier']}
- EV adoption: {top_opportunity['ev_adoption_rate']}%
- Opportunity Score: {top_opportunity['opportunity_score']}/100

💡 Insight: {top_opportunity['rationale']}

Rekomendacja: Klienci z {top_opportunity['gmina']} mają wysoki potencjał zakupowy.
Podkreśl możliwość ładowania w domu (Tesla Wall Connector) + Supercharger network.
"""
    else:
        summary = f"Brak zidentyfikowanych luk rynkowych w {voivodeship}. Wszystkie regiony premium mają dobrą infrastrukturę."

    return {
        "stations": stations,
        "municipalities": wealth,
        "opportunities": opportunities,
        "summary": summary.strip()
    }


def get_infrastructure_summary(voivodeship: str = "śląskie") -> str:
    """
    Get concise infrastructure summary for context injection.

    Returns:
        String summary for AI prompt context
    """
    data = fetch_charging_infrastructure_wealth_map(voivodeship)
    return data["summary"]


def get_city_infrastructure_for_prompt(city: str) -> str:
    """
    Get city-specific infrastructure summary for AI prompt injection.

    Args:
        city: City name

    Returns:
        Formatted string with infrastructure details
    """
    infra = check_infrastructure(city)

    if infra["supercharger_count"] == 0:
        sc_info = f"Brak Superchargerów bezpośrednio w {city}. Najbliższy: {infra['nearest_supercharger']['name']}"
    else:
        sc_names = ", ".join([s["name"] for s in infra["superchargers"]])
        sc_info = f"Superchargery ({infra['supercharger_count']}): {sc_names}"

    wealth = infra.get("wealth_data", {})
    wealth_info = ""
    if wealth:
        wealth_info = f"Dochód: {wealth.get('income_per_capita_pln', 'N/A'):,} PLN/mieszkańca, EV adoption: {wealth.get('ev_adoption_rate', 'N/A')}%"

    return f"""
🔌 Infrastruktura EV w {city}:
  • {sc_info}
  • Inne stacje DC: {infra['other_charger_count']}
  • Łączna liczba złączy: {infra['total_connectors']}
  • Ocena pokrycia: {infra['coverage_rating']}
  • {wealth_info}
""".strip()
