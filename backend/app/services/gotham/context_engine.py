"""
Gotham Strategic Context Engine
================================

Aggregates intelligence from multiple sources to provide real-time market context:

1. CEPiK - Leasing expiry candidates
2. EIPA - Charging infrastructure + wealth mapping
3. External APIs - Fuel prices, subsidy updates, news
4. Tesla internal - Inventory, promotions, delivery timelines

Output:
- Strategic context string for AI prompt injection
- Enables "Bloomberg Brain" - AI sees market dynamics, not just client conversation
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from .cepik_connector import get_leasing_expiry_summary
from .eipa_connector import get_infrastructure_summary

logger = logging.getLogger(__name__)


def get_fuel_price_context() -> str:
    """
    Get current fuel price trends.

    In production, fetch from:
    - e-petrol.pl API
    - Orlen API
    - Government fuel monitoring system

    For MVP, use static data with manual updates.
    """
    # MOCK DATA - update manually or integrate real API
    current_date = datetime.now().strftime("%Y-%m-%d")
    fuel_price_pb95 = 6.49  # PLN per liter
    fuel_price_diesel = 6.35
    electricity_price = 0.80  # PLN per kWh (avg home charging)

    # Calculate TCO advantage
    # Example: 20,000 km/year, combustion 8L/100km vs Tesla 15kWh/100km
    annual_km = 20000
    combustion_fuel_cost = (annual_km / 100) * 8 * fuel_price_pb95
    tesla_electricity_cost = (annual_km / 100) * 15 * electricity_price
    annual_savings = combustion_fuel_cost - tesla_electricity_cost

    context = f"""
⛽ Aktualne Ceny Paliw ({current_date}):
- Pb95: {fuel_price_pb95} PLN/l
- Diesel: {fuel_price_diesel} PLN/l
- Energia elektryczna (dom): {electricity_price} PLN/kWh

💰 TCO Advantage (20,000 km/rok):
- Spalinowy (8L/100km): {int(combustion_fuel_cost):,} PLN/rok
- Tesla (15kWh/100km): {int(tesla_electricity_cost):,} PLN/rok
- **Oszczędność: {int(annual_savings):,} PLN/rok**

💡 Sales Angle: "Każdy rok z benzyniakiem to {int(annual_savings):,} PLN strat. Tesla się sama spłaca."
"""
    return context.strip()


def get_subsidy_context() -> str:
    """
    Get current EV subsidy program status.

    In production, integrate with:
    - gov.pl APIs
    - NFOŚiGW (National Fund for Environmental Protection)
    - Monitor program deadlines and budget availability

    For MVP, use manual updates.
    """
    # MOCK DATA - update manually
    context = f"""
🎁 Programy Dotacji (stan na {datetime.now().strftime("%Y-%m-%d")}):

1. **Mój Elektryk** (osoby prywatne)
   - Dotacja: do 18,750 PLN
   - Warunki: tylko nowe EV, cena max 225,000 PLN
   - Dostępność: ⚠️ OGRANICZONA (30% budżetu pozostało)
   - Deadline: 2025-12-31 lub wcześniej przy wyczerpaniu środków

2. **NaszEauto** (firmy)
   - Dotacja: do 27,000 PLN
   - Warunki: leasing/kredyt, pojazd do 225k PLN
   - Status: ✅ AKTYWNY

💡 Sales Angle: "Dotacje wyczerpują się szybko. Im wcześniej decyzja, tym większa pewność otrzymania."
"""
    return context.strip()


def generate_strategic_context(
    voivodeship: str = "śląskie",
    include_leasing_intel: bool = True,
    include_infrastructure: bool = True,
    include_fuel_prices: bool = True,
    include_subsidies: bool = True
) -> str:
    """
    Generate complete strategic context for AI prompt injection.

    This context is injected into Slow Path Opus Magnum analysis to provide
    real-time market intelligence beyond client conversation.

    Args:
        voivodeship: Geographic focus area
        include_leasing_intel: Include CEPiK leasing expiry data
        include_infrastructure: Include EIPA charging/wealth analysis
        include_fuel_prices: Include current fuel price TCO comparison
        include_subsidies: Include subsidy program status

    Returns:
        Formatted strategic context string for AI prompt
    """
    context_blocks = []

    context_blocks.append(f"""
╔════════════════════════════════════════════════════════════════╗
║ GOTHAM INTELLIGENCE - Kontekst Strategiczny                   ║
║ Region: {voivodeship.capitalize():50} ║
║ Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S"):47} ║
╚════════════════════════════════════════════════════════════════╝
""".strip())

    if include_fuel_prices:
        try:
            fuel_context = get_fuel_price_context()
            context_blocks.append(fuel_context)
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch fuel price context: {e}")

    if include_subsidies:
        try:
            subsidy_context = get_subsidy_context()
            context_blocks.append(subsidy_context)
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch subsidy context: {e}")

    if include_leasing_intel:
        try:
            leasing_context = get_leasing_expiry_summary(voivodeship)
            context_blocks.append(leasing_context)
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch leasing intelligence: {e}")

    if include_infrastructure:
        try:
            infra_context = get_infrastructure_summary(voivodeship)
            context_blocks.append(infra_context)
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch infrastructure context: {e}")

    # Final strategic note
    context_blocks.append("""
═══════════════════════════════════════════════════════════════════
🧠 AI INSTRUCTION: Użyj powyższego kontekstu strategicznego do:
1. Identyfikacji ukrytych punktów bólu klienta (np. wysokie koszty paliwa)
2. Personalizacji argumentów sprzedażowych (TCO, dotacje, infrastruktura)
3. Stworzenia poczucia pilności (wygasające dotacje, wzrost cen paliw)
4. Pozycjonowania Tesli jako rozwiązania finansowego, nie tylko auta

Pamiętaj: Klient może nie być świadomy wszystkich korzyści. Twoja rola:
edukować i pokazywać KONKRETNE liczby z jego regionu/sytuacji.
═══════════════════════════════════════════════════════════════════
""".strip())

    full_context = "\n\n".join(context_blocks)
    logger.info(f"✓ Generated strategic context: {len(full_context)} chars")
    return full_context
