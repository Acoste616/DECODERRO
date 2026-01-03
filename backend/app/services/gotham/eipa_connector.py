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
        mock_stations = [
            {
                "station_id": "UDT-SL-001",
                "name": "Supercharger Katowice - Park Handlowy",
                "county": "Katowice",
                "gmina": "Katowice",
                "latitude": 50.2649,
                "longitude": 19.0238,
                "connectors": 8,
                "max_power_kw": 250,
                "operator": "Tesla"
            },
            {
                "station_id": "UDT-SL-002",
                "name": "Ionity Gliwice - A4",
                "county": "Gliwice",
                "gmina": "Gliwice",
                "latitude": 50.2945,
                "longitude": 18.6714,
                "connectors": 6,
                "max_power_kw": 350,
                "operator": "Ionity"
            },
            {
                "station_id": "UDT-SL-003",
                "name": "GreenWay Bielsko-Biała",
                "county": "Bielsko-Biała",
                "gmina": "Bielsko-Biała",
                "latitude": 49.8224,
                "longitude": 19.0446,
                "connectors": 4,
                "max_power_kw": 50,
                "operator": "GreenWay"
            }
        ]

        logger.info(f"✓ Found {len(mock_stations)} charging stations in {voivodeship}")
        return mock_stations

    except Exception as e:
        logger.error(f"✗ UDT API error: {e}")
        return []


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
        mock_wealth = [
            {
                "gmina": "Katowice",
                "income_per_capita_pln": 65000,
                "business_density": 145,
                "population": 290000,
                "wealth_tier": "premium"
            },
            {
                "gmina": "Gliwice",
                "income_per_capita_pln": 58000,
                "business_density": 120,
                "population": 180000,
                "wealth_tier": "high"
            },
            {
                "gmina": "Bielsko-Biała",
                "income_per_capita_pln": 52000,
                "business_density": 95,
                "population": 170000,
                "wealth_tier": "high"
            },
            {
                "gmina": "Tychy",
                "income_per_capita_pln": 48000,
                "business_density": 85,
                "population": 128000,
                "wealth_tier": "medium"
            },
            {
                "gmina": "Sosnowiec",
                "income_per_capita_pln": 44000,
                "business_density": 70,
                "population": 200000,
                "wealth_tier": "medium"
            }
        ]

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
    for station in stations:
        gmina = station["gmina"]
        station_count_by_gmina[gmina] = station_count_by_gmina.get(gmina, 0) + 1

    # Identify opportunities: high wealth + low infrastructure
    opportunities = []
    for w in wealth:
        gmina = w["gmina"]
        stations_count = station_count_by_gmina.get(gmina, 0)
        wealth_tier = w["wealth_tier"]

        # Opportunity score: high wealth + few stations = expansion potential
        if wealth_tier in ["high", "premium"] and stations_count < 3:
            opportunities.append({
                "gmina": gmina,
                "wealth_tier": wealth_tier,
                "income_per_capita": w["income_per_capita_pln"],
                "stations_count": stations_count,
                "opportunity_score": (w["income_per_capita_pln"] // 1000) - (stations_count * 5),
                "rationale": f"Premium market ({w['income_per_capita_pln']:,} PLN/capita) with only {stations_count} charging stations"
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
- Stacje ładowania: {top_opportunity['stations_count']}
- Tier zamożności: {top_opportunity['wealth_tier']}
- Opportunity Score: {top_opportunity['opportunity_score']}/100

💡 Insight: {top_opportunity['rationale']}

Rekomendacja: Klienci z {top_opportunity['gmina']} mają wysoki potencjał zakupowy, ale brakuje infrastruktury.
Podkreśl możliwość ładowania w domu (Tesla Wall Connector) + Supercharger network jako alternatywę.
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
