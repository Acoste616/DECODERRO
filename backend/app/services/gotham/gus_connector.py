"""
GUS API Connector - Polish Statistical Office Data
===================================================

Connects to GUS (Główny Urząd Statystyczny) API to access:
- TERYT - Territorial division data (województwa, powiaty, gminy)
- BDL - Local Data Bank (thousands of statistical indicators)
- REGON - Business entity registry
- SDG - Sustainable Development Goals tracking

Use case:
- Enrich sales intelligence with demographic and economic data
- Identify high-potential regions for Tesla sales
- Analyze market size and purchasing power
- Track EV adoption trends

API Reference: https://api.stat.gov.pl/
Available APIs:
1. API TERYT - territorial.stat.gov.pl
2. API BDL - bdl.stat.gov.pl/api/v1
3. API REGON - api.stat.gov.pl/Home/RegonApi
4. API SDP - api.stat.gov.pl/Home/SdpApi

All GUS APIs are public and do not require authentication keys.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# GUS API URLs
GUS_BDL_API_URL = "https://bdl.stat.gov.pl/api/v1"
GUS_TERYT_API_URL = "https://api.stat.gov.pl/Home/TerytApi"
GUS_REGON_API_URL = "https://api.stat.gov.pl/Home/RegonApi"


# =============================================================================
# API BDL - Bank Danych Lokalnych (Local Data Bank)
# =============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_bdl_subjects() -> Dict:
    """
    Get available subject areas from BDL API.

    Subject areas organize statistical data by topic (e.g., demographics, economy, environment).

    Returns:
        JSON response with available subjects
    """
    try:
        url = f"{GUS_BDL_API_URL}/subjects"
        logger.info(f"📚 Fetching BDL subjects from {url}")

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✓ Found {len(data.get('results', []))} subjects")

        return data

    except Exception as e:
        logger.error(f"✗ Failed to fetch BDL subjects: {e}")
        return {"results": []}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_bdl_variables(subject_id: Optional[str] = None) -> Dict:
    """
    Get available statistical variables from BDL API.

    Args:
        subject_id: Optional subject ID to filter variables

    Returns:
        JSON response with available variables
    """
    try:
        url = f"{GUS_BDL_API_URL}/variables"
        params = {}

        if subject_id:
            params["subject-id"] = subject_id

        logger.info(f"📊 Fetching BDL variables from {url}")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✓ Found {len(data.get('results', []))} variables")

        return data

    except Exception as e:
        logger.error(f"✗ Failed to fetch BDL variables: {e}")
        return {"results": []}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_bdl_data(
    variable_id: str,
    unit_level: int = 2,  # 1=country, 2=voivodeship, 3=powiat, 4=gmina
    unit_parent_id: Optional[str] = None,
    year: Optional[int] = None
) -> Dict:
    """
    Get statistical data from BDL API.

    Args:
        variable_id: Statistical variable ID (e.g., "72330" for population)
        unit_level: Administrative level (1=country, 2=voivodeship, 3=powiat, 4=gmina)
        unit_parent_id: Parent unit ID for filtering (e.g., voivodeship TERYT code)
        year: Year for data (optional, defaults to latest available)

    Returns:
        JSON response with statistical data
    """
    try:
        url = f"{GUS_BDL_API_URL}/data/by-variable/{variable_id}"
        params = {"unit-level": unit_level}

        if unit_parent_id:
            params["unit-parent-id"] = unit_parent_id
        if year:
            params["year"] = year

        logger.info(f"📈 Fetching BDL data for variable {variable_id}")

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.info(f"✓ BDL data fetched: {len(data.get('results', []))} records")

        return data

    except Exception as e:
        logger.error(f"✗ Failed to fetch BDL data: {e}")
        return {"results": []}


def get_regional_demographics(voivodeship_teryt: str) -> Dict:
    """
    Get demographic data for a voivodeship.

    Useful variables:
    - 72330: Population (total)
    - 459749: Average monthly gross salary
    - 60270: GDP per capita
    - 415612: Number of registered businesses

    Args:
        voivodeship_teryt: TERYT code for voivodeship (e.g., "24" for Śląskie)

    Returns:
        Dictionary with demographic indicators
    """
    try:
        demographics = {}

        # Population
        pop_data = get_bdl_data("72330", unit_level=2)
        for record in pop_data.get("results", []):
            if record.get("id") == voivodeship_teryt:
                values = record.get("values", [])
                if values:
                    demographics["population"] = values[0].get("val")
                    demographics["population_year"] = values[0].get("year")

        # Average salary (if available)
        salary_data = get_bdl_data("459749", unit_level=2)
        for record in salary_data.get("results", []):
            if record.get("id") == voivodeship_teryt:
                values = record.get("values", [])
                if values:
                    demographics["avg_salary_pln"] = values[0].get("val")
                    demographics["salary_year"] = values[0].get("year")

        logger.info(f"✓ Demographics fetched for voivodeship {voivodeship_teryt}")
        return demographics

    except Exception as e:
        logger.error(f"✗ Failed to fetch demographics: {e}")
        return {}


# =============================================================================
# API TERYT - Territorial Division
# =============================================================================

def get_teryt_voivodeships() -> List[Dict]:
    """
    Get list of all Polish voivodeships.

    Note: TERYT API requires special authorization. For public data,
    we use hardcoded reference data that matches official TERYT codes.

    Returns:
        List of voivodeships with TERYT codes and names
    """
    voivodeships = [
        {"teryt": "02", "name": "dolnośląskie", "en": "Lower Silesian"},
        {"teryt": "04", "name": "kujawsko-pomorskie", "en": "Kuyavian-Pomeranian"},
        {"teryt": "06", "name": "lubelskie", "en": "Lublin"},
        {"teryt": "08", "name": "lubuskie", "en": "Lubusz"},
        {"teryt": "10", "name": "łódzkie", "en": "Łódź"},
        {"teryt": "12", "name": "małopolskie", "en": "Lesser Poland"},
        {"teryt": "14", "name": "mazowieckie", "en": "Masovian"},
        {"teryt": "16", "name": "opolskie", "en": "Opole"},
        {"teryt": "18", "name": "podkarpackie", "en": "Subcarpathian"},
        {"teryt": "20", "name": "podlaskie", "en": "Podlaskie"},
        {"teryt": "22", "name": "pomorskie", "en": "Pomeranian"},
        {"teryt": "24", "name": "śląskie", "en": "Silesian"},
        {"teryt": "26", "name": "świętokrzyskie", "en": "Świętokrzyskie"},
        {"teryt": "28", "name": "warmińsko-mazurskie", "en": "Warmian-Masurian"},
        {"teryt": "30", "name": "wielkopolskie", "en": "Greater Poland"},
        {"teryt": "32", "name": "zachodniopomorskie", "en": "West Pomeranian"},
    ]

    logger.info(f"✓ Returned {len(voivodeships)} voivodeships")
    return voivodeships


def get_teryt_code_for_voivodeship(voivodeship_name: str) -> Optional[str]:
    """
    Get TERYT code for a voivodeship name.

    Args:
        voivodeship_name: Name of voivodeship (e.g., "śląskie", "Silesian")

    Returns:
        TERYT code or None if not found
    """
    voivodeships = get_teryt_voivodeships()

    name_lower = voivodeship_name.lower()
    for voi in voivodeships:
        if name_lower in [voi["name"].lower(), voi["en"].lower()]:
            return voi["teryt"]

    return None


# =============================================================================
# HIGH-LEVEL INTELLIGENCE FUNCTIONS
# =============================================================================

def get_market_intelligence_for_voivodeship(voivodeship_name: str) -> Dict:
    """
    Get comprehensive market intelligence for a voivodeship.

    Combines multiple GUS data sources to provide:
    - Population and demographics
    - Economic indicators
    - Business activity
    - Market potential score

    Args:
        voivodeship_name: Name of voivodeship (e.g., "śląskie")

    Returns:
        Dictionary with market intelligence data
    """
    try:
        teryt_code = get_teryt_code_for_voivodeship(voivodeship_name)

        if not teryt_code:
            logger.warning(f"⚠️ Could not find TERYT code for {voivodeship_name}")
            return {"error": "Voivodeship not found"}

        # Get demographics
        demographics = get_regional_demographics(teryt_code)

        # Calculate market potential score (simplified)
        market_score = 0
        if demographics.get("population"):
            # Higher population = more potential
            pop_millions = demographics["population"] / 1_000_000
            market_score += min(pop_millions * 10, 30)  # Max 30 points

        if demographics.get("avg_salary_pln"):
            # Higher salary = more premium car buyers
            salary_thousands = demographics["avg_salary_pln"] / 1000
            market_score += min(salary_thousands / 2, 40)  # Max 40 points

        intelligence = {
            "voivodeship": voivodeship_name,
            "teryt_code": teryt_code,
            "demographics": demographics,
            "market_potential_score": min(int(market_score), 100),
            "data_source": "GUS API (BDL)",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✓ Market intelligence generated for {voivodeship_name}: score={intelligence['market_potential_score']}")
        return intelligence

    except Exception as e:
        logger.error(f"✗ Failed to generate market intelligence: {e}")
        return {"error": str(e)}


def get_gus_summary_for_prompt(voivodeship_name: str = "śląskie") -> str:
    """
    Generate human-readable GUS intelligence summary for AI prompt injection.

    Args:
        voivodeship_name: Name of voivodeship

    Returns:
        Formatted string with key insights for sales context
    """
    try:
        intelligence = get_market_intelligence_for_voivodeship(voivodeship_name)

        if "error" in intelligence:
            return f"Brak danych GUS dla województwa {voivodeship_name}"

        demographics = intelligence.get("demographics", {})
        population = demographics.get("population", 0)
        avg_salary = demographics.get("avg_salary_pln", 0)
        market_score = intelligence.get("market_potential_score", 0)

        # Format population with spaces as thousands separator (Polish style)
        pop_formatted = f"{population:,}".replace(",", " ")
        salary_formatted = f"{avg_salary:,}".replace(",", " ") if avg_salary else "brak danych"

        summary = f"""
📊 GUS Intelligence: Dane Regionalne - {voivodeship_name.capitalize()}
══════════════════════════════════════════════════════════════

📍 DEMOGRAFIA:
  • Populacja: {pop_formatted} mieszkańców
  • Średnie wynagrodzenie: {salary_formatted} PLN/mies.
  • Kod TERYT: {intelligence.get('teryt_code')}

🎯 POTENCJAŁ RYNKU:
  • Market Score: {market_score}/100
  • Segmentacja: {"Premium Market" if market_score > 60 else "Mid-Market" if market_score > 40 else "Entry Market"}

💡 STRATEGIA SPRZEDAŻOWA:
{"Wysoki potencjał nabywczy - skup się na premium features i TCO." if market_score > 60 else
 "Średni potencjał - podkreślaj oszczędności i ROI." if market_score > 40 else
 "Niższy potencjał - focus na basic models i finansowanie."}

📈 Źródło danych: GUS (Główny Urząd Statystyczny)
"""
        return summary.strip()

    except Exception as e:
        logger.error(f"✗ Failed to generate GUS summary: {e}")
        return f"Błąd generowania danych GUS: {str(e)}"


def get_gus_stats_for_prompt(voivodeship_name: str = "śląskie") -> Dict:
    """
    Get structured GUS stats for AI prompt injection.

    Args:
        voivodeship_name: Name of voivodeship

    Returns:
        Dictionary with key metrics for AI context
    """
    try:
        intelligence = get_market_intelligence_for_voivodeship(voivodeship_name)

        if "error" in intelligence:
            return {
                "voivodeship": voivodeship_name,
                "error": intelligence["error"],
                "market_score": 0
            }

        demographics = intelligence.get("demographics", {})

        return {
            "voivodeship": voivodeship_name,
            "teryt_code": intelligence.get("teryt_code"),
            "population": demographics.get("population", 0),
            "avg_salary_pln": demographics.get("avg_salary_pln", 0),
            "market_potential_score": intelligence.get("market_potential_score", 0),
            "summary": f"Region {voivodeship_name}: {intelligence.get('market_potential_score', 0)}/100 market score"
        }

    except Exception as e:
        logger.error(f"✗ Failed to get GUS stats: {e}")
        return {
            "voivodeship": voivodeship_name,
            "error": str(e),
            "market_score": 0
        }
