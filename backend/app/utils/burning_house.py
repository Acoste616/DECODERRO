"""
Tesla-Gotham ULTRA v4.0 - Burning House Score Calculator
=========================================================

ENHANCED (2026 Edition) - Implements urgency scoring algorithm based on:
1. TAX PENALTY (B2B + ICE) - Most critical factor for 2026!
   - ICE limit dropped to 100k PLN (was 150k)
   - EV limit remains 225k PLN
   - Penalty = (vehicle_price - 100k) * 19% CIT

2. Fuel vs Electricity costs (Diesel 6.03 PLN/l @ 8.5l vs G12 Night 0.46 PLN/kWh @ 16kWh)
3. NaszEauto subsidy expiration (<90 days = +20 points bonus)
4. Vehicle age - optimal replacement window (36-84 months)

Returns BurningHouseScore with:
- Overall score (0-100%)
- Fire level visualization (cold/warm/hot/burning)
- Monthly delay cost in PLN
- Individual factor breakdown
- Sales arguments list
- Urgency message in client's language
"""

from typing import Dict, Union, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel


# =============================================================================
# 2026 HARDCODED CONSTANTS
# =============================================================================

# Tax Amortization Limits (2026)
ICE_AMORTIZATION_LIMIT_2026 = 100_000  # PLN - dropped from 150k!
EV_AMORTIZATION_LIMIT_2026 = 225_000   # PLN - remains unchanged
CIT_TAX_RATE = 0.19  # 19% Corporate Income Tax

# Fuel Prices (2026 Q1)
DIESEL_PRICE_PLN_L = 6.03  # PLN per liter
DIESEL_CONSUMPTION_L_100KM = 8.5  # liters per 100km (avg premium sedan)

# Electricity - G12 Night Tariff (2026)
G12_NIGHT_PRICE_PLN_KWH = 0.46  # PLN per kWh
EV_CONSUMPTION_KWH_100KM = 16.0  # kWh per 100km (Tesla avg)

# NaszEauto Subsidy Program
NASZ_EAUTO_SUBSIDY_PLN = 18_750  # Base subsidy amount
NASZ_EAUTO_CRITICAL_DAYS = 90  # Critical threshold for bonus points
NASZ_EAUTO_BONUS_POINTS = 20  # Bonus score if < 90 days


# =============================================================================
# BURNING HOUSE CALCULATOR CLASS
# =============================================================================

@dataclass
class BurningHouseResult:
    """Result from BurningHouseCalculator"""
    score: int  # 0-100%
    monthly_loss: int  # PLN per month
    messages: List[str]  # Sales arguments
    fire_level: str  # cold/warm/hot/burning
    factors: Dict[str, any]  # Detailed breakdown
    urgency_message: str  # Human-readable summary


class BurningHouseCalculator:
    """
    Burning House Score Calculator v2026

    Calculates purchase urgency based on:
    - Tax penalties (B2B + ICE vehicles)
    - Fuel cost differential
    - Subsidy expiration
    - Vehicle age

    Usage:
        calc = BurningHouseCalculator(
            fuel_cost_monthly=800,
            vehicle_age_months=42,
            client_type="B2B",
            vehicle_value_pln=180000,
            is_ice=True,
            subsidy_days_remaining=60,
            monthly_distance_km=2000
        )
        result = calc.calculate()
        print(result.score, result.monthly_loss, result.messages)
    """

    def __init__(
        self,
        fuel_cost_monthly: Optional[float] = None,
        vehicle_age_months: Optional[int] = None,
        client_type: str = "B2C",  # "B2B" or "B2C"
        vehicle_value_pln: Optional[int] = None,
        is_ice: bool = True,  # Internal Combustion Engine
        subsidy_days_remaining: Optional[int] = None,
        monthly_distance_km: Optional[int] = None,
        language: str = "pl"
    ):
        self.fuel_cost_monthly = fuel_cost_monthly
        self.vehicle_age_months = vehicle_age_months
        self.client_type = client_type.upper()
        self.vehicle_value_pln = vehicle_value_pln
        self.is_ice = is_ice
        self.subsidy_days_remaining = subsidy_days_remaining
        self.monthly_distance_km = monthly_distance_km or 2000  # Default 2000 km/month
        self.language = language

        # Internal accumulators
        self._score = 0
        self._monthly_loss = 0
        self._messages: List[str] = []
        self._factors: Dict[str, any] = {}

    def calculate(self) -> BurningHouseResult:
        """
        Main calculation entry point.
        Runs all factor calculations and aggregates results.
        """
        # Reset accumulators
        self._score = 0
        self._monthly_loss = 0
        self._messages = []
        self._factors = {}

        # Calculate each factor
        self._calculate_tax_penalty()      # MOST IMPORTANT for 2026
        self._calculate_fuel_savings()      # Diesel vs G12
        self._calculate_subsidy_urgency()   # NaszEauto
        self._calculate_vehicle_age()       # Replacement timing

        # Cap score at 100
        final_score = min(100, self._score)

        # Determine fire level
        fire_level = self._get_fire_level(final_score)

        # Generate urgency message
        urgency_message = self._generate_urgency_message(final_score, fire_level)

        return BurningHouseResult(
            score=final_score,
            monthly_loss=self._monthly_loss,
            messages=self._messages,
            fire_level=fire_level,
            factors=self._factors,
            urgency_message=urgency_message
        )

    def _calculate_tax_penalty(self) -> None:
        """
        CRITICAL FACTOR (2026): B2B ICE Amortization Penalty

        If client is B2B and vehicle is ICE (spalinowe) > 100k PLN:
        - ICE limit dropped from 150k to 100k PLN
        - Penalty = (price - 100k) * 19% CIT
        - This is LOST TAX DEDUCTION = real money lost

        For EV: limit is 225k PLN - much more favorable!
        """
        if self.client_type != "B2B" or self.vehicle_value_pln is None:
            self._factors["tax_penalty"] = {
                "applicable": False,
                "reason": "Not B2B or no vehicle value"
            }
            return

        if self.is_ice and self.vehicle_value_pln > ICE_AMORTIZATION_LIMIT_2026:
            # Calculate lost deduction
            excess_amount = self.vehicle_value_pln - ICE_AMORTIZATION_LIMIT_2026
            lost_deduction = int(excess_amount * CIT_TAX_RATE)
            monthly_tax_loss = lost_deduction // 60  # Amortized over 5 years

            # This is a MAJOR factor - up to 30 points
            tax_score = min(30, int((excess_amount / 100_000) * 30))
            self._score += tax_score
            self._monthly_loss += monthly_tax_loss

            self._factors["tax_penalty"] = {
                "applicable": True,
                "vehicle_type": "ICE",
                "vehicle_value": self.vehicle_value_pln,
                "limit_2026": ICE_AMORTIZATION_LIMIT_2026,
                "excess_amount": excess_amount,
                "lost_deduction_pln": lost_deduction,
                "monthly_loss_pln": monthly_tax_loss,
                "score_added": tax_score
            }

            if self.language == "pl":
                self._messages.append(
                    f"KARA PODATKOWA 2026: Limit amortyzacji dla ICE spadł do {ICE_AMORTIZATION_LIMIT_2026//1000}k PLN! "
                    f"Przy wartości {self.vehicle_value_pln//1000}k PLN tracisz {lost_deduction:,} PLN odliczenia "
                    f"({monthly_tax_loss:,} PLN/mies). Tesla EV ma limit 225k!"
                )
            else:
                self._messages.append(
                    f"TAX PENALTY 2026: ICE amortization limit dropped to {ICE_AMORTIZATION_LIMIT_2026//1000}k PLN! "
                    f"At {self.vehicle_value_pln//1000}k PLN you lose {lost_deduction:,} PLN deduction "
                    f"({monthly_tax_loss:,} PLN/month). Tesla EV has 225k limit!"
                )
        else:
            # No penalty or already EV
            self._factors["tax_penalty"] = {
                "applicable": False,
                "vehicle_type": "EV" if not self.is_ice else "ICE",
                "vehicle_value": self.vehicle_value_pln,
                "within_limit": True
            }

    def _calculate_fuel_savings(self) -> None:
        """
        Fuel Cost Comparison: Diesel vs G12 Night Tariff

        Diesel: 6.03 PLN/l @ 8.5l/100km = 51.26 PLN/100km
        EV G12: 0.46 PLN/kWh @ 16kWh/100km = 7.36 PLN/100km

        Savings per 100km: ~44 PLN = 86% reduction!
        """
        # Calculate monthly costs
        monthly_km = self.monthly_distance_km

        # Diesel cost
        diesel_monthly = (monthly_km / 100) * DIESEL_CONSUMPTION_L_100KM * DIESEL_PRICE_PLN_L

        # EV cost (G12 night tariff - optimal for home charging)
        ev_monthly = (monthly_km / 100) * EV_CONSUMPTION_KWH_100KM * G12_NIGHT_PRICE_PLN_KWH

        # Monthly savings
        monthly_savings = int(diesel_monthly - ev_monthly)

        # Use provided fuel cost if available, otherwise use calculated
        if self.fuel_cost_monthly:
            actual_fuel_cost = self.fuel_cost_monthly
            monthly_savings = int(actual_fuel_cost - ev_monthly)
        else:
            actual_fuel_cost = diesel_monthly

        # Score: up to 25 points based on savings
        # 1000 PLN/month savings = 25 points
        fuel_score = min(25, int((monthly_savings / 1000) * 25))
        self._score += fuel_score
        self._monthly_loss += monthly_savings

        self._factors["fuel_savings"] = {
            "monthly_distance_km": monthly_km,
            "diesel_cost_monthly": int(diesel_monthly),
            "actual_fuel_cost_monthly": int(actual_fuel_cost),
            "ev_cost_monthly_g12": int(ev_monthly),
            "monthly_savings_pln": monthly_savings,
            "diesel_price_l": DIESEL_PRICE_PLN_L,
            "g12_price_kwh": G12_NIGHT_PRICE_PLN_KWH,
            "score_added": fuel_score
        }

        if monthly_savings > 0:
            if self.language == "pl":
                self._messages.append(
                    f"OSZCZĘDNOŚĆ PALIWA: Diesel {DIESEL_PRICE_PLN_L} PLN/l vs G12 nocna {G12_NIGHT_PRICE_PLN_KWH} PLN/kWh. "
                    f"Przy {monthly_km} km/mies. oszczędzasz {monthly_savings:,} PLN miesięcznie!"
                )
            else:
                self._messages.append(
                    f"FUEL SAVINGS: Diesel {DIESEL_PRICE_PLN_L} PLN/l vs G12 night {G12_NIGHT_PRICE_PLN_KWH} PLN/kWh. "
                    f"At {monthly_km} km/month you save {monthly_savings:,} PLN monthly!"
                )

    def _calculate_subsidy_urgency(self) -> None:
        """
        NaszEauto Subsidy Expiration Bonus

        If < 90 days remaining: +20 points bonus!
        This creates FOMO (Fear Of Missing Out)
        """
        if self.subsidy_days_remaining is None:
            self._factors["subsidy"] = {
                "applicable": False,
                "reason": "No subsidy deadline provided"
            }
            return

        days = self.subsidy_days_remaining

        if days <= NASZ_EAUTO_CRITICAL_DAYS:
            # CRITICAL: Add bonus points
            self._score += NASZ_EAUTO_BONUS_POINTS

            # Calculate monthly impact of losing subsidy
            if days > 0:
                monthly_subsidy_cost = NASZ_EAUTO_SUBSIDY_PLN // max(1, days // 30)
                self._monthly_loss += monthly_subsidy_cost
            else:
                monthly_subsidy_cost = NASZ_EAUTO_SUBSIDY_PLN  # Already expired - full loss

            urgency = "critical" if days <= 30 else "high"

            self._factors["subsidy"] = {
                "applicable": True,
                "days_remaining": days,
                "subsidy_value_pln": NASZ_EAUTO_SUBSIDY_PLN,
                "urgency_level": urgency,
                "bonus_points_added": NASZ_EAUTO_BONUS_POINTS,
                "monthly_impact_pln": monthly_subsidy_cost
            }

            if self.language == "pl":
                self._messages.append(
                    f"PILNE - NaszEauto: Tylko {days} dni do końca programu! "
                    f"Dotacja {NASZ_EAUTO_SUBSIDY_PLN:,} PLN przepada. Działaj teraz!"
                )
            else:
                self._messages.append(
                    f"URGENT - NaszEauto: Only {days} days until program ends! "
                    f"Subsidy of {NASZ_EAUTO_SUBSIDY_PLN:,} PLN expires. Act now!"
                )
        else:
            # Subsidy exists but not critical
            base_score = 5  # Small base score for having subsidy available
            self._score += base_score

            self._factors["subsidy"] = {
                "applicable": True,
                "days_remaining": days,
                "subsidy_value_pln": NASZ_EAUTO_SUBSIDY_PLN,
                "urgency_level": "low",
                "bonus_points_added": 0,
                "base_score_added": base_score
            }

    def _calculate_vehicle_age(self) -> None:
        """
        Vehicle Age / Replacement Timing Factor

        Optimal window: 36-48 months (leasing end, good trade-in)
        Good: 48-60 months
        Fair: 60-84 months
        Urgent: 84+ months (repair risk)
        """
        if self.vehicle_age_months is None:
            self._factors["vehicle_age"] = {
                "applicable": False,
                "reason": "No vehicle age provided"
            }
            return

        age = self.vehicle_age_months

        if 36 <= age <= 48:
            # OPTIMAL - leasing end window
            age_score = 15
            category = "optimal"
            repair_risk = 0

            if self.language == "pl":
                self._messages.append(
                    f"IDEALNY MOMENT: {age} miesięcy - koniec typowego leasingu. "
                    f"Maksymalna wartość trade-in, minimalne ryzyko napraw."
                )
            else:
                self._messages.append(
                    f"PERFECT TIMING: {age} months - typical leasing end. "
                    f"Maximum trade-in value, minimal repair risk."
                )

        elif 48 < age <= 60:
            age_score = 10
            category = "good"
            repair_risk = 0

        elif 60 < age <= 84:
            age_score = 5
            category = "fair"
            repair_risk = 200  # Estimated monthly repair cost
            self._monthly_loss += repair_risk

        elif age > 84:
            # URGENT - high repair risk
            age_score = 12
            category = "urgent"
            repair_risk = 400  # Higher repair costs for 7+ year old cars
            self._monthly_loss += repair_risk

            if self.language == "pl":
                self._messages.append(
                    f"RYZYKO NAPRAW: {age} miesięcy ({age//12} lat). "
                    f"Szacowany koszt napraw: ~{repair_risk} PLN/mies. Czas na wymianę!"
                )
            else:
                self._messages.append(
                    f"REPAIR RISK: {age} months ({age//12} years). "
                    f"Estimated repair cost: ~{repair_risk} PLN/month. Time for replacement!"
                )
        else:
            # Too new (< 36 months)
            age_score = 3
            category = "too_new"
            repair_risk = 0

        self._score += age_score

        self._factors["vehicle_age"] = {
            "applicable": True,
            "age_months": age,
            "age_years": age // 12,
            "category": category,
            "repair_risk_monthly": repair_risk,
            "score_added": age_score
        }

    def _get_fire_level(self, score: int) -> str:
        """Determine fire level based on score"""
        if score >= 75:
            return "burning"  # Red pulsing
        elif score >= 50:
            return "hot"      # Orange
        elif score >= 30:
            return "warm"     # Yellow
        else:
            return "cold"     # Green/Blue

    def _generate_urgency_message(self, score: int, fire_level: str) -> str:
        """Generate human-readable urgency message"""
        messages = {
            "pl": {
                "burning": f"POŻAR! Zwlekanie kosztuje Cię ~{self._monthly_loss:,} PLN miesięcznie. DZIAŁAJ TERAZ!",
                "hot": f"GORĄCO! Każdy miesiąc zwłoki = ~{self._monthly_loss:,} PLN strat.",
                "warm": f"Dobry moment na decyzję. Potencjalne oszczędności: ~{self._monthly_loss:,} PLN/mies.",
                "cold": f"Możesz spokojnie analizować. Koszt zwłoki: ~{self._monthly_loss:,} PLN/mies."
            },
            "en": {
                "burning": f"FIRE! Delaying costs you ~{self._monthly_loss:,} PLN monthly. ACT NOW!",
                "hot": f"HOT! Each month of delay = ~{self._monthly_loss:,} PLN lost.",
                "warm": f"Good timing for decision. Potential savings: ~{self._monthly_loss:,} PLN/month.",
                "cold": f"You can analyze calmly. Delay cost: ~{self._monthly_loss:,} PLN/month."
            }
        }

        lang_messages = messages.get(self.language, messages["pl"])
        return lang_messages.get(fire_level, "")


# =============================================================================
# PYDANTIC MODEL (for API compatibility)
# =============================================================================

class BurningHouseScore(BaseModel):
    """Pydantic model for API responses"""
    score: int
    fire_level: str
    monthly_delay_cost_pln: int
    factors: Dict[str, any] = {}
    urgency_message: str = ""
    messages: List[str] = []


# =============================================================================
# LEGACY FUNCTION (Backwards Compatibility)
# =============================================================================

def calculate_burning_house_score(
    current_fuel_consumption_l_100km: Optional[float] = None,
    monthly_distance_km: Optional[int] = None,
    fuel_price_pln_l: float = DIESEL_PRICE_PLN_L,
    vehicle_age_months: Optional[int] = None,
    purchase_type: str = "private",
    vehicle_price_planned: Optional[int] = None,
    subsidy_deadline_days: Optional[int] = None,
    language: str = "pl"
) -> BurningHouseScore:
    """
    Legacy function for backwards compatibility.
    Wraps BurningHouseCalculator class.
    """
    # Calculate fuel cost if consumption provided
    fuel_cost_monthly = None
    if current_fuel_consumption_l_100km and monthly_distance_km:
        fuel_cost_monthly = (current_fuel_consumption_l_100km / 100) * monthly_distance_km * fuel_price_pln_l

    # Map purchase_type to client_type
    client_type = "B2B" if purchase_type == "business" else "B2C"

    # Create calculator
    calc = BurningHouseCalculator(
        fuel_cost_monthly=fuel_cost_monthly,
        vehicle_age_months=vehicle_age_months,
        client_type=client_type,
        vehicle_value_pln=vehicle_price_planned,
        is_ice=True,  # Assume ICE if using this legacy function
        subsidy_days_remaining=subsidy_deadline_days,
        monthly_distance_km=monthly_distance_km or 2000,
        language=language
    )

    # Calculate
    result = calc.calculate()

    # Convert to Pydantic model
    return BurningHouseScore(
        score=result.score,
        fire_level=result.fire_level,
        monthly_delay_cost_pln=result.monthly_loss,
        factors=result.factors,
        urgency_message=result.urgency_message,
        messages=result.messages
    )


# =============================================================================
# HELPER: Extract BHS parameters from conversation context
# =============================================================================

def extract_bhs_from_session_context(session_history: str, language: str = "pl") -> Optional[BurningHouseScore]:
    """
    Analyze conversation history and extract BHS-relevant parameters.

    This is a simplified heuristic extraction. In production, you might use:
    - NER (Named Entity Recognition) to extract numbers
    - LLM-based extraction with structured output
    - Form-based input from seller

    For now, returns None if insufficient data.
    """
    # TODO: Implement intelligent extraction from conversation
    return None
