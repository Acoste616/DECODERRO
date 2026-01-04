"""
Gotham Intelligence Module
===========================

Provides strategic market context and data enrichment for Tesla sales:

1. CEPiK Connector - Polish vehicle registration database
   - Identify premium leasing expirations (36-48 month old registrations)
   - Filter by region (e.g., Śląskie voivodeship)
   - Target high-value replacement opportunities
   - Real API integration with fallback to mock data

2. GUS Connector - Polish Statistical Office (Główny Urząd Statystyczny)
   - BDL API - Local Data Bank (demographic and economic indicators)
   - TERYT API - Territorial division data
   - Regional market intelligence and purchasing power analysis
   - No authentication required - public data

3. EIPA Connector - Charging infrastructure + wealth mapping
   - Map EV charging stations from UDT API
   - Correlate with municipal wealth data (BDL GUS)
   - Identify high-potential geographic markets

4. Strategic Context Engine
   - Fuel price trends
   - Subsidy program updates (NaszEauto, Mój Elektryk)
   - Competitive intelligence (new EV launches)
   - Seasonal buying patterns

ENHANCED (v4.5): Added GUS API integration for regional market intelligence
"""

from .cepik_connector import (
    fetch_leasing_expiry_candidates,
    get_leasing_opportunities,
    get_leasing_expiry_summary,
    get_leasing_stats_for_prompt,
    fetch_vehicles_from_cepik,
    get_cepik_dictionaries,
    get_cepik_dictionary,
    get_cepik_statistics,
)
from .gus_connector import (
    get_bdl_subjects,
    get_bdl_variables,
    get_bdl_data,
    get_regional_demographics,
    get_teryt_voivodeships,
    get_teryt_code_for_voivodeship,
    get_market_intelligence_for_voivodeship,
    get_gus_summary_for_prompt,
    get_gus_stats_for_prompt,
)
from .eipa_connector import (
    fetch_charging_infrastructure_wealth_map,
    fetch_charging_stations,
    fetch_municipal_wealth_data,
    check_infrastructure,
    get_infrastructure_summary,
    get_city_infrastructure_for_prompt,
)
from .context_engine import generate_strategic_context

__all__ = [
    # CEPiK
    "fetch_leasing_expiry_candidates",
    "get_leasing_opportunities",
    "get_leasing_expiry_summary",
    "get_leasing_stats_for_prompt",
    "fetch_vehicles_from_cepik",
    "get_cepik_dictionaries",
    "get_cepik_dictionary",
    "get_cepik_statistics",
    # GUS
    "get_bdl_subjects",
    "get_bdl_variables",
    "get_bdl_data",
    "get_regional_demographics",
    "get_teryt_voivodeships",
    "get_teryt_code_for_voivodeship",
    "get_market_intelligence_for_voivodeship",
    "get_gus_summary_for_prompt",
    "get_gus_stats_for_prompt",
    # EIPA
    "fetch_charging_infrastructure_wealth_map",
    "fetch_charging_stations",
    "fetch_municipal_wealth_data",
    "check_infrastructure",
    "get_infrastructure_summary",
    "get_city_infrastructure_for_prompt",
    # Context Engine
    "generate_strategic_context",
]
