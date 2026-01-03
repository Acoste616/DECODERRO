"""
Gotham Intelligence Module
===========================

Provides strategic market context and data enrichment for Tesla sales:

1. CEPiK Connector - Polish vehicle registration database
   - Identify premium leasing expirations (36-48 month old registrations)
   - Filter by region (e.g., Śląskie voivodeship)
   - Target high-value replacement opportunities

2. EIPA Connector - Charging infrastructure + wealth mapping
   - Map EV charging stations from UDT API
   - Correlate with municipal wealth data (BDL GUS)
   - Identify high-potential geographic markets

3. Strategic Context Engine
   - Fuel price trends
   - Subsidy program updates (NaszEauto, Mój Elektryk)
   - Competitive intelligence (new EV launches)
   - Seasonal buying patterns
"""

from .cepik_connector import fetch_leasing_expiry_candidates
from .eipa_connector import fetch_charging_infrastructure_wealth_map
from .context_engine import generate_strategic_context

__all__ = [
    "fetch_leasing_expiry_candidates",
    "fetch_charging_infrastructure_wealth_map",
    "generate_strategic_context"
]
