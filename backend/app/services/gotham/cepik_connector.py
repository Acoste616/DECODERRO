"""
CEPiK Connector - Vehicle Registration Intelligence
====================================================

Connects to CEPiK (Centralna Ewidencja Pojazdów i Kierowców) API to identify:
- Premium vehicle registrations from 36-48 months ago
- Leasing expiration windows (typical 3-4 year contracts)
- Geographic distribution (targeting high-wealth regions)

Use case:
- Sales team identifies potential Tesla buyers whose current leasing contracts are ending
- Proactive outreach during decision window (3-6 months before expiration)

API Reference: https://api.cepik.gov.pl/
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

CEPIK_API_URL = os.getenv("CEPIK_API_URL", "https://api.cepik.gov.pl/")
CEPIK_API_KEY = os.getenv("CEPIK_API_KEY")  # Optional: if API requires authentication


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_leasing_expiry_candidates(
    voivodeship: str = "śląskie",
    lookback_months: int = 36,
    premium_brands: Optional[List[str]] = None
) -> List[Dict]:
    """
    Fetch vehicle registrations likely to have expiring leases.

    Args:
        voivodeship: Polish voivodeship (województwo) to filter by (e.g., "śląskie", "mazowieckie")
        lookback_months: How many months back to search (36 = 3 years, typical lease duration)
        premium_brands: List of premium brands to filter (e.g., ["BMW", "Mercedes", "Audi", "Volvo"])

    Returns:
        List of vehicle registration records with metadata:
        - vin: Vehicle identification number (partial, anonymized)
        - brand: Vehicle brand
        - model: Vehicle model
        - registration_date: Original registration date
        - estimated_lease_end: Calculated lease expiration date
        - county: County (powiat) within voivodeship
    """

    if premium_brands is None:
        premium_brands = ["BMW", "Mercedes-Benz", "Audi", "Volvo", "Lexus", "Porsche"]

    try:
        # Calculate date range for leasing expiry window
        # Example: if lookback_months=36, search registrations from 36-48 months ago
        target_date_start = datetime.now() - timedelta(days=lookback_months * 30)
        target_date_end = datetime.now() - timedelta(days=(lookback_months - 12) * 30)

        logger.info(f"🔍 Fetching CEPiK data for {voivodeship}, date range: {target_date_start.date()} to {target_date_end.date()}")

        # IMPORTANT: This is a placeholder implementation
        # Real CEPiK API requires:
        # 1. Official API access credentials
        # 2. GDPR-compliant data handling
        # 3. Proper authentication flow

        # For MVP/demo, return mock data
        # In production, replace with actual API calls:
        # response = requests.get(
        #     f"{CEPIK_API_URL}/vehicles",
        #     params={
        #         "voivodeship": voivodeship,
        #         "date_from": target_date_start.strftime("%Y-%m-%d"),
        #         "date_to": target_date_end.strftime("%Y-%m-%d"),
        #         "brands": ",".join(premium_brands)
        #     },
        #     headers={"Authorization": f"Bearer {CEPIK_API_KEY}"},
        #     timeout=10
        # )
        # response.raise_for_status()
        # data = response.json()

        # MOCK DATA for demonstration
        mock_candidates = [
            {
                "vin": "WBA***********123",  # Anonymized VIN
                "brand": "BMW",
                "model": "X5",
                "registration_date": (target_date_start + timedelta(days=30)).strftime("%Y-%m-%d"),
                "estimated_lease_end": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "county": "Katowice",
                "estimated_value_pln": 250000
            },
            {
                "vin": "WDD***********456",
                "brand": "Mercedes-Benz",
                "model": "GLE",
                "registration_date": (target_date_start + timedelta(days=60)).strftime("%Y-%m-%d"),
                "estimated_lease_end": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
                "county": "Gliwice",
                "estimated_value_pln": 280000
            },
            {
                "vin": "WAU***********789",
                "brand": "Audi",
                "model": "Q7",
                "registration_date": (target_date_start + timedelta(days=45)).strftime("%Y-%m-%d"),
                "estimated_lease_end": (datetime.now() + timedelta(days=105)).strftime("%Y-%m-%d"),
                "county": "Bielsko-Biała",
                "estimated_value_pln": 260000
            }
        ]

        logger.info(f"✓ Found {len(mock_candidates)} leasing expiry candidates in {voivodeship}")
        return mock_candidates

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ CEPiK API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"✗ CEPiK connector error: {e}")
        return []


def get_leasing_expiry_summary(voivodeship: str = "śląskie") -> str:
    """
    Generate human-readable summary of leasing expiry opportunities.

    Returns:
        Formatted string with key insights for sales context injection
    """
    candidates = fetch_leasing_expiry_candidates(voivodeship=voivodeship)

    if not candidates:
        return f"Brak danych o wygasających leasingach w województwie {voivodeship}."

    total_count = len(candidates)
    avg_value = sum(c.get("estimated_value_pln", 0) for c in candidates) // total_count
    brands = set(c["brand"] for c in candidates)

    summary = f"""
📊 Analiza Leasing Expiry - {voivodeship.capitalize()}:
- {total_count} premium pojazdy z leasingiem wygasającym w ciągu 3-6 miesięcy
- Średnia wartość: {avg_value:,} PLN
- Marki: {', '.join(brands)}
- Główne powiaty: {', '.join(set(c['county'] for c in candidates[:3]))}

💡 Strategia: Klienci z tych segmentów są w oknie decyzyjnym. Podkreśl TCO i zero-emission benefit.
"""
    return summary.strip()
