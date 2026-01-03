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

ENHANCED (v4.0): 50 companies mock data for Śląsk region
"""

import os
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

CEPIK_API_URL = os.getenv("CEPIK_API_URL", "https://api.cepik.gov.pl/")
CEPIK_API_KEY = os.getenv("CEPIK_API_KEY")  # Optional: if API requires authentication


# =============================================================================
# MOCK DATA GENERATOR - 50 Companies in Śląsk
# =============================================================================

# Premium brands typical for B2B leasing
PREMIUM_BRANDS = [
    {"brand": "BMW", "models": ["X5", "X3", "530d", "520d", "X6", "740d", "M3"], "avg_value": 280000},
    {"brand": "Audi", "models": ["Q7", "Q5", "A6", "A8", "Q8", "e-tron", "A4"], "avg_value": 260000},
    {"brand": "Mercedes-Benz", "models": ["GLE", "GLC", "E-Class", "S-Class", "GLS", "C-Class"], "avg_value": 300000},
    {"brand": "Volvo", "models": ["XC90", "XC60", "S90", "V90", "XC40"], "avg_value": 240000},
    {"brand": "Porsche", "models": ["Cayenne", "Macan", "Panamera", "Taycan"], "avg_value": 450000},
    {"brand": "Lexus", "models": ["RX", "NX", "LS", "ES"], "avg_value": 220000},
]

# Śląskie counties (powiaty) with business density
SLASKIE_COUNTIES = [
    {"name": "Katowice", "business_density": "very_high", "companies": 15},
    {"name": "Gliwice", "business_density": "high", "companies": 8},
    {"name": "Bielsko-Biała", "business_density": "high", "companies": 7},
    {"name": "Tychy", "business_density": "medium", "companies": 5},
    {"name": "Sosnowiec", "business_density": "medium", "companies": 4},
    {"name": "Chorzów", "business_density": "medium", "companies": 3},
    {"name": "Częstochowa", "business_density": "high", "companies": 5},
    {"name": "Rybnik", "business_density": "medium", "companies": 3},
]

# Company name patterns for realistic mock data
COMPANY_PATTERNS = [
    "{industry} {surname} Sp. z o.o.",
    "{industry} Group Poland",
    "{surname} & Partners",
    "{industry} Solutions",
    "{surname} Consulting",
    "Pro{industry}",
    "{industry}Tech",
    "{surname} Import-Export",
]

INDUSTRIES = ["Auto", "Tech", "Med", "Build", "Trans", "Logis", "Finance", "Trade", "Invest", "Service"]
SURNAMES = ["Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski",
            "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski", "Jankowski", "Mazur"]


def _generate_company_name() -> str:
    """Generate realistic Polish company name"""
    pattern = random.choice(COMPANY_PATTERNS)
    return pattern.format(
        industry=random.choice(INDUSTRIES),
        surname=random.choice(SURNAMES)
    )


def _generate_mock_50_companies(voivodeship: str = "śląskie") -> List[Dict]:
    """
    Generate 50 mock companies in Śląsk that registered premium vehicles 36 months ago.
    These represent potential Tesla buyers with expiring leases.
    """
    companies = []
    company_id = 1

    # Calculate target date (36 months ago = leasing about to end)
    target_date = datetime.now() - timedelta(days=36 * 30)

    for county in SLASKIE_COUNTIES:
        for _ in range(county["companies"]):
            # Select random brand
            brand_info = random.choice(PREMIUM_BRANDS)
            model = random.choice(brand_info["models"])

            # Calculate value with some variance
            base_value = brand_info["avg_value"]
            value_variance = random.randint(-30000, 50000)
            estimated_value = base_value + value_variance

            # Registration date (around 36 months ago with some variance)
            reg_variance_days = random.randint(-60, 60)
            registration_date = target_date + timedelta(days=reg_variance_days)

            # Lease end date (36 months after registration)
            lease_end = registration_date + timedelta(days=36 * 30)

            # Days until lease end
            days_until_end = (lease_end - datetime.now()).days

            # Generate company data
            company = {
                "id": f"CEP-SL-{company_id:04d}",
                "company_name": _generate_company_name(),
                "nip": f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(100, 999)}",
                "vin": f"W{random.choice(['BA', 'DD', 'AU', 'VG', 'P0'])}{''.join(random.choices('0123456789ABCDEFGHJKLMNPRSTUVWXYZ', k=11))}",
                "brand": brand_info["brand"],
                "model": model,
                "registration_date": registration_date.strftime("%Y-%m-%d"),
                "estimated_lease_end": lease_end.strftime("%Y-%m-%d"),
                "days_until_lease_end": days_until_end,
                "county": county["name"],
                "voivodeship": voivodeship,
                "estimated_value_pln": estimated_value,
                "business_type": random.choice(["IT", "Handel", "Usługi", "Produkcja", "Transport", "Finanse"]),
                "fleet_size": random.randint(1, 15),
                "contact_priority": "high" if days_until_end <= 90 else "medium" if days_until_end <= 180 else "low"
            }

            companies.append(company)
            company_id += 1

    # Sort by days until lease end (most urgent first)
    companies.sort(key=lambda x: x["days_until_lease_end"])

    return companies


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

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
        - company_name: Business name (for B2B leasing)
    """

    if premium_brands is None:
        premium_brands = ["BMW", "Mercedes-Benz", "Audi", "Volvo", "Lexus", "Porsche"]

    try:
        logger.info(f"🔍 Fetching CEPiK data for {voivodeship}, lookback: {lookback_months} months")

        # IMPORTANT: This is a placeholder implementation
        # Real CEPiK API requires:
        # 1. Official API access credentials
        # 2. GDPR-compliant data handling
        # 3. Proper authentication flow

        # For MVP/demo, return mock data (50 companies)
        all_candidates = _generate_mock_50_companies(voivodeship)

        # Filter by premium brands if specified
        if premium_brands:
            candidates = [c for c in all_candidates if c["brand"] in premium_brands]
        else:
            candidates = all_candidates

        logger.info(f"✓ Found {len(candidates)} leasing expiry candidates in {voivodeship}")
        return candidates

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ CEPiK API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"✗ CEPiK connector error: {e}")
        return []


def get_leasing_opportunities(voivodeship: str = "SL") -> List[Dict]:
    """
    Get leasing expiry opportunities for a voivodeship.

    Args:
        voivodeship: Voivodeship code (e.g., "SL" for Śląskie, "MZ" for Mazowieckie)

    Returns:
        List of companies with expiring leases, sorted by urgency
    """
    # Map codes to full names
    voivodeship_map = {
        "SL": "śląskie",
        "MZ": "mazowieckie",
        "WP": "wielkopolskie",
        "MP": "małopolskie",
        "DS": "dolnośląskie",
        "PM": "pomorskie",
    }

    full_name = voivodeship_map.get(voivodeship.upper(), "śląskie")

    candidates = fetch_leasing_expiry_candidates(voivodeship=full_name)

    # Enrich with urgency scores
    for c in candidates:
        days = c["days_until_lease_end"]
        if days <= 30:
            c["urgency_score"] = 100
            c["urgency_label"] = "CRITICAL"
        elif days <= 60:
            c["urgency_score"] = 80
            c["urgency_label"] = "HIGH"
        elif days <= 90:
            c["urgency_score"] = 60
            c["urgency_label"] = "MEDIUM"
        else:
            c["urgency_score"] = 40
            c["urgency_label"] = "LOW"

    return candidates


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

    # Count by urgency
    critical = len([c for c in candidates if c["days_until_lease_end"] <= 30])
    high = len([c for c in candidates if 30 < c["days_until_lease_end"] <= 90])

    # Calculate stats
    avg_value = sum(c.get("estimated_value_pln", 0) for c in candidates) // total_count
    brands = set(c["brand"] for c in candidates)
    counties = set(c["county"] for c in candidates)

    # Top 3 companies by urgency
    top_3 = candidates[:3]
    top_3_str = "\n".join([
        f"  • {c['company_name']} ({c['brand']} {c['model']}) - {c['days_until_lease_end']} dni"
        for c in top_3
    ])

    summary = f"""
📊 GOTHAM Intelligence: Leasing Expiry Analysis - {voivodeship.capitalize()}
══════════════════════════════════════════════════════════════

🔥 PILNE OKAZJE:
  • {critical} firm z leasingiem kończącym się w ciągu 30 dni (CRITICAL)
  • {high} firm z leasingiem kończącym się w ciągu 90 dni (HIGH)
  • {total_count} łącznie premium pojazdów do wymiany

📈 STATYSTYKI:
  • Średnia wartość pojazdu: {avg_value:,} PLN
  • Marki: {', '.join(brands)}
  • Regiony: {', '.join(list(counties)[:5])}

🎯 TOP 3 NAJBARDZIEJ PILNE:
{top_3_str}

💡 STRATEGIA:
Klienci z wygasającymi leasingami są w oknie decyzyjnym.
Podkreśl: TCO vs spalinowe, limit amortyzacji EV (225k vs 100k ICE),
dotację NaszEauto, oraz zero-emission benefit dla B2B.
"""
    return summary.strip()


def get_leasing_stats_for_prompt(voivodeship: str = "śląskie") -> Dict:
    """
    Get structured leasing stats for AI prompt injection.

    Returns:
        Dictionary with key metrics for AI context
    """
    candidates = fetch_leasing_expiry_candidates(voivodeship=voivodeship)

    if not candidates:
        return {
            "total_opportunities": 0,
            "critical_count": 0,
            "high_count": 0,
            "avg_vehicle_value": 0,
            "top_brands": [],
            "summary": "Brak danych"
        }

    critical = [c for c in candidates if c["days_until_lease_end"] <= 30]
    high = [c for c in candidates if 30 < c["days_until_lease_end"] <= 90]

    return {
        "total_opportunities": len(candidates),
        "critical_count": len(critical),
        "high_count": len(high),
        "avg_vehicle_value": sum(c["estimated_value_pln"] for c in candidates) // len(candidates),
        "top_brands": list(set(c["brand"] for c in candidates)),
        "regions": list(set(c["county"] for c in candidates)),
        "summary": f"{len(candidates)} firm w {voivodeship} z wygasającymi leasingami, {len(critical)} krytycznych"
    }
