"""
Tesla-Gotham ULTRA v4.0 - Burning House Score Calculator
=========================================================

Implements urgency scoring algorithm based on:
1. Fuel costs - monthly burn rate from combustion vehicle
2. NaszEauto subsidy expiration - government incentive deadline
3. Depreciation limits - 225k/100k business tax benefits
4. Vehicle age - optimal replacement timing

Returns BurningHouseScore with:
- Overall score (0-100)
- Fire level visualization (cold/warm/hot/burning)
- Monthly delay cost in PLN
- Individual factor breakdown
- Urgency message in client's language
"""

from typing import Dict, Union, Optional
from app.models import BurningHouseScore


def calculate_burning_house_score(
    current_fuel_consumption_l_100km: Optional[float] = None,
    monthly_distance_km: Optional[int] = None,
    fuel_price_pln_l: float = 6.50,  # Default: current avg fuel price in Poland (2025)
    vehicle_age_months: Optional[int] = None,
    purchase_type: str = "private",
    vehicle_price_planned: Optional[int] = None,
    subsidy_deadline_days: Optional[int] = None,
    language: str = "pl"
) -> BurningHouseScore:
    """
    Calculate Burning House Score for Tesla purchase urgency.

    Algorithm:
    - Score = weighted sum of 4 factors (0-100 scale)
    - Fire level = visual indicator based on score thresholds
    - Monthly delay cost = tangible financial loss from waiting

    Args:
        current_fuel_consumption_l_100km: Current car fuel usage (e.g., 8.5 for combustion, 0 for EV)
        monthly_distance_km: How many km driven per month
        fuel_price_pln_l: Current fuel price per liter (default: 6.50 PLN)
        vehicle_age_months: Age of current vehicle in months
        purchase_type: "private" or "business" (affects depreciation scoring)
        vehicle_price_planned: Planned Tesla price (for depreciation calculation)
        subsidy_deadline_days: Days until NaszEauto subsidy expires (None if not applicable)
        language: "pl" or "en" for urgency message

    Returns:
        BurningHouseScore with complete urgency analysis
    """

    # Initialize factors
    factors: Dict[str, Union[int, str, bool, float]] = {}
    score_components = []
    monthly_delay_cost = 0

    # ==================================================================
    # FACTOR 1: FUEL COST SAVINGS (Weight: 35%)
    # ==================================================================
    if current_fuel_consumption_l_100km and monthly_distance_km:
        # Calculate monthly fuel cost
        monthly_fuel_liters = (current_fuel_consumption_l_100km / 100) * monthly_distance_km
        monthly_fuel_cost = monthly_fuel_liters * fuel_price_pln_l

        # Tesla electricity cost estimate (assuming 0.80 PLN/kWh, 15 kWh/100km avg)
        monthly_electricity_kwh = (15 / 100) * monthly_distance_km
        monthly_electricity_cost = monthly_electricity_kwh * 0.80

        # Monthly savings
        monthly_fuel_savings = monthly_fuel_cost - monthly_electricity_cost

        # Score: 0 PLN savings = 0 points, 1000+ PLN savings = 35 points
        fuel_score = min(35, int((monthly_fuel_savings / 1000) * 35))

        factors["fuel_cost_monthly"] = int(monthly_fuel_cost)
        factors["fuel_savings_monthly"] = int(monthly_fuel_savings)
        factors["current_consumption_l_100km"] = current_fuel_consumption_l_100km
        monthly_delay_cost += int(monthly_fuel_savings)
        score_components.append(fuel_score)
    else:
        # No data - assume neutral (small score)
        score_components.append(10)
        factors["fuel_cost_monthly"] = 0
        factors["fuel_savings_monthly"] = 0

    # ==================================================================
    # FACTOR 2: SUBSIDY EXPIRATION (Weight: 30%)
    # ==================================================================
    if subsidy_deadline_days is not None:
        # Subsidy urgency curve:
        # - 0-30 days: CRITICAL (30 points)
        # - 31-60 days: HIGH (20 points)
        # - 61-90 days: MEDIUM (10 points)
        # - 90+ days: LOW (5 points)
        if subsidy_deadline_days <= 30:
            subsidy_score = 30
            subsidy_level = "critical"
        elif subsidy_deadline_days <= 60:
            subsidy_score = 20
            subsidy_level = "high"
        elif subsidy_deadline_days <= 90:
            subsidy_score = 10
            subsidy_level = "medium"
        else:
            subsidy_score = 5
            subsidy_level = "low"

        # Estimate subsidy value (NaszEauto: ~18,750 PLN for Tesla)
        subsidy_value_pln = 18750
        # If losing subsidy, add to monthly delay cost
        if subsidy_deadline_days <= 90:
            # Amortize subsidy loss over months until deadline
            monthly_subsidy_cost = subsidy_value_pln // max(1, subsidy_deadline_days // 30)
            monthly_delay_cost += monthly_subsidy_cost

        factors["subsidy_expires_days"] = subsidy_deadline_days
        factors["subsidy_urgency"] = subsidy_level
        factors["subsidy_value_pln"] = subsidy_value_pln
        score_components.append(subsidy_score)
    else:
        # No subsidy applicable - neutral score
        score_components.append(5)
        factors["subsidy_expires_days"] = None
        factors["subsidy_urgency"] = "not_applicable"

    # ==================================================================
    # FACTOR 3: DEPRECIATION TAX BENEFIT (Weight: 20%)
    # ==================================================================
    if purchase_type == "business" and vehicle_price_planned:
        # Polish tax law: businesses can depreciate vehicles
        # - Up to 225,000 PLN: 100% deductible
        # - Above 225,000 PLN: only 225,000 deductible
        # - Passenger cars (non-EV): max 150,000 PLN deductible

        # For Tesla (EV), full 225k is deductible
        if vehicle_price_planned <= 225000:
            depreciation_benefit = vehicle_price_planned * 0.19  # 19% CIT tax rate
            depreciation_score = 20  # Full benefit
            depreciation_risk = "none"
        else:
            # Only 225k deductible - losing benefit on excess amount
            depreciation_benefit = 225000 * 0.19
            lost_benefit = (vehicle_price_planned - 225000) * 0.19
            depreciation_score = 10  # Partial benefit
            depreciation_risk = "high"
            # Add lost benefit to urgency (amortized over 5 years)
            monthly_delay_cost += int(lost_benefit / 60)

        factors["has_business_benefit"] = True
        factors["depreciation_benefit_pln"] = int(depreciation_benefit)
        factors["depreciation_risk"] = depreciation_risk
        factors["vehicle_price_planned"] = vehicle_price_planned
        score_components.append(depreciation_score)
    else:
        # Private purchase or no price data - low score
        score_components.append(5)
        factors["has_business_benefit"] = False
        factors["depreciation_risk"] = "not_applicable"

    # ==================================================================
    # FACTOR 4: VEHICLE AGE / REPLACEMENT TIMING (Weight: 15%)
    # ==================================================================
    if vehicle_age_months:
        # Optimal replacement window: 36-60 months (3-5 years)
        # - 36-48 months: OPTIMAL (15 points) - leasing end, still good trade-in value
        # - 48-60 months: GOOD (10 points) - before major repairs
        # - 60-84 months: FAIR (5 points) - aging, losing value
        # - 84+ months: URGENT (12 points) - high repair risk

        if 36 <= vehicle_age_months <= 48:
            age_score = 15
            age_category = "optimal"
        elif 48 < vehicle_age_months <= 60:
            age_score = 10
            age_category = "good"
        elif 60 < vehicle_age_months <= 84:
            age_score = 5
            age_category = "fair"
        elif vehicle_age_months > 84:
            age_score = 12
            age_category = "urgent_aging"
            # Add estimated repair costs to urgency
            monthly_delay_cost += 300  # Avg monthly repair cost for 7+ year old cars
        else:
            # Too new (< 36 months) - low urgency
            age_score = 3
            age_category = "too_new"

        factors["vehicle_age_months"] = vehicle_age_months
        factors["age_category"] = age_category
        score_components.append(age_score)
    else:
        # No age data - neutral
        score_components.append(5)
        factors["vehicle_age_months"] = None
        factors["age_category"] = "unknown"

    # ==================================================================
    # CALCULATE OVERALL SCORE
    # ==================================================================
    overall_score = sum(score_components)

    # Determine fire level based on score
    if overall_score >= 75:
        fire_level = "burning"  # 🔥🔥🔥 CRITICAL
    elif overall_score >= 50:
        fire_level = "hot"      # 🔥🔥 HIGH
    elif overall_score >= 30:
        fire_level = "warm"     # 🔥 MEDIUM
    else:
        fire_level = "cold"     # ❄️ LOW

    # ==================================================================
    # GENERATE URGENCY MESSAGE
    # ==================================================================
    urgency_messages = {
        "pl": {
            "burning": f"⚠️ PILNE! Zwlekanie kosztuje Cię ~{monthly_delay_cost} PLN miesięcznie. Czas działać!",
            "hot": f"🔥 Wysoka pilność. Każdy miesiąc zwłoki to ~{monthly_delay_cost} PLN strat.",
            "warm": f"💡 Dobry moment na decyzję. Potencjalne oszczędności: ~{monthly_delay_cost} PLN/mies.",
            "cold": f"✅ Możesz spokojnie analizować. Koszt zwłoki: ~{monthly_delay_cost} PLN/mies."
        },
        "en": {
            "burning": f"⚠️ URGENT! Delaying costs you ~{monthly_delay_cost} PLN monthly. Time to act!",
            "hot": f"🔥 High urgency. Each month of delay = ~{monthly_delay_cost} PLN lost.",
            "warm": f"💡 Good timing for decision. Potential savings: ~{monthly_delay_cost} PLN/month.",
            "cold": f"✅ You can analyze calmly. Delay cost: ~{monthly_delay_cost} PLN/month."
        }
    }

    urgency_message = urgency_messages.get(language, urgency_messages["pl"]).get(fire_level, "")

    # ==================================================================
    # RETURN BURNING HOUSE SCORE
    # ==================================================================
    return BurningHouseScore(
        score=overall_score,
        fire_level=fire_level,
        monthly_delay_cost_pln=monthly_delay_cost,
        factors=factors,
        urgency_message=urgency_message
    )


# ==================================================================
# HELPER: Extract BHS parameters from conversation context
# ==================================================================
def extract_bhs_from_session_context(session_history: str, language: str = "pl") -> Optional[BurningHouseScore]:
    """
    Analyze conversation history and extract BHS-relevant parameters.

    This is a simplified heuristic extraction. In production, you might use:
    - NER (Named Entity Recognition) to extract numbers
    - LLM-based extraction with structured output
    - Form-based input from seller

    For now, returns None if insufficient data.
    In future iterations, integrate with Gotham Intelligence for automatic data enrichment.
    """
    # TODO: Implement intelligent extraction from conversation
    # For v4.0, we'll add a dedicated input form or structured questionnaire
    return None
