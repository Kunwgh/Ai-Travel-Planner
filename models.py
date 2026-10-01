"""
models.py
Shared data structures used across all agents and the orchestrator.
Using dataclasses keeps the agents decoupled from any particular
API's response shape -- each agent is responsible for mapping raw
provider data into these common models.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class TripRequest:
    """The user's raw trip request -- input to the whole system."""
    origin: str
    cities: List[str]                  # multi-city itinerary, in order
    start_date: date
    end_date: date
    travelers: int = 1
    total_budget: float = 2000.0
    currency: str = "USD"
    preferences: List[str] = field(default_factory=list)  # e.g. ["museums", "food", "budget-hotels"]


@dataclass
class Flight:
    origin: str
    destination: str
    depart_date: date
    airline: str
    price: float
    duration_hours: float
    stops: int = 0


@dataclass
class Hotel:
    city: str
    name: str
    check_in: date
    check_out: date
    price_per_night: float
    rating: float
    total_price: float = 0.0

    def __post_init__(self):
        nights = (self.check_out - self.check_in).days
        self.total_price = round(self.price_per_night * max(nights, 1), 2)


@dataclass
class WeatherForecast:
    city: str
    date: date
    condition: str
    temp_high_c: float
    temp_low_c: float
    advisory: Optional[str] = None


@dataclass
class BudgetBreakdown:
    total_budget: float
    flights_cost: float
    hotels_cost: float
    daily_spend_estimate: float
    daily_spend_days: int
    contingency: float
    remaining: float
    within_budget: bool


@dataclass
class ItineraryDay:
    day_number: int
    city: str
    date: date
    activities: List[str]
    weather: Optional[WeatherForecast] = None


@dataclass
class TripPlan:
    """The final, assembled output of the whole multi-agent pipeline."""
    request: TripRequest
    flights: List[Flight]
    hotels: List[Hotel]
    weather: List[WeatherForecast]
    budget: BudgetBreakdown
    itinerary: List[ItineraryDay]
    warnings: List[str] = field(default_factory=list)
