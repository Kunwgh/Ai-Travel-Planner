"""
orchestrator.py
The coordination layer. Owns the pipeline order, passes outputs of one
agent as inputs to the next, resolves conflicts (e.g. over-budget trips),
and assembles the final TripPlan.

Pipeline:
    1. FlightAgent   -> cheapest flight per leg of the multi-city route
    2. HotelAgent    -> best-value hotel per city, sized to nights stayed
    3. WeatherAgent  -> forecast for every city/day on the trip
    4. BudgetAgent   -> reconcile flights+hotels against total budget,
                        derive a daily spend allowance
    5. ItineraryAgent-> build the day-by-day plan using preferences +
                        weather advisories, respecting the daily budget
"""

from datetime import timedelta
from typing import List

from models import TripRequest, TripPlan
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent
from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent


class TravelOrchestrator:
    def __init__(self, verbose: bool = True):
        self.flight_agent = FlightAgent(verbose=verbose)
        self.hotel_agent = HotelAgent(verbose=verbose)
        self.weather_agent = WeatherAgent(verbose=verbose)
        self.budget_agent = BudgetAgent(verbose=verbose)
        self.itinerary_agent = ItineraryAgent(verbose=verbose)
        self.verbose = verbose

    def _split_city_dates(self, request: TripRequest):
        """
        Evenly divide the total trip length across the requested cities,
        in order, producing per-city (start_date, end_date) stay windows.
        The last city absorbs any remainder day.
        """
        total_days = (request.end_date - request.start_date).days
        n_cities = len(request.cities)
        base = total_days // n_cities
        remainder = total_days % n_cities

        windows = []
        cursor = request.start_date
        for i, city in enumerate(request.cities):
            length = base + (1 if i < remainder else 0)
            length = max(length, 1)
            stay_end = cursor + timedelta(days=length)
            windows.append((city, cursor, stay_end))
            cursor = stay_end
        return windows

    def plan_trip(self, request: TripRequest) -> TripPlan:
        warnings: List[str] = []
        if self.verbose:
            print("=" * 60)
            print(f"Planning trip: {request.origin} -> {' -> '.join(request.cities)}")
            print(f"{request.start_date} to {request.end_date} | {request.travelers} traveler(s) "
                  f"| budget ${request.total_budget} {request.currency}")
            print("=" * 60)

        city_windows = self._split_city_dates(request)

        # ---- 1. Flights: origin -> city1 -> city2 -> ... -> last city -> origin
        route = [request.origin] + request.cities + [request.origin]
        legs = []
        for i in range(len(route) - 1):
            depart_date = city_windows[i][1] if i < len(city_windows) else city_windows[-1][2]
            legs.append((route[i], route[i + 1], depart_date))
        flights = self.flight_agent.timed_run(legs)

        # ---- 2. Hotels: one stay per city window
        stays = [(city, start, end) for city, start, end in city_windows]
        hotels = self.hotel_agent.timed_run(stays)

        # ---- 3. Weather: every (city, date) the traveler is present
        city_dates = []
        for city, start, end in city_windows:
            d = start
            while d < end:
                city_dates.append((city, d))
                d += timedelta(days=1)
        weather = self.weather_agent.timed_run(city_dates)
        weather_lookup = {(w.city, w.date): w for w in weather}

        # ---- 4. Budget reconciliation
        trip_days = (request.end_date - request.start_date).days
        budget = self.budget_agent.timed_run(
            total_budget=request.total_budget,
            flights=flights,
            hotels=hotels,
            trip_days=trip_days,
            travelers=request.travelers,
        )
        if not budget.within_budget:
            overage = (budget.flights_cost + budget.hotels_cost) - budget.total_budget
            warnings.append(
                f"Trip is over budget by ${overage:.2f}. Consider fewer cities, "
                f"cheaper hotels, or a higher budget."
            )

        # ---- 5. Itinerary synthesis
        itinerary = self.itinerary_agent.timed_run(
            city_day_ranges=city_windows,
            preferences=request.preferences,
            weather_by_city_date=weather_lookup,
        )

        plan = TripPlan(
            request=request,
            flights=flights,
            hotels=hotels,
            weather=weather,
            budget=budget,
            itinerary=itinerary,
            warnings=warnings,
        )

        if self.verbose:
            print("=" * 60)
            print("Trip planning complete.")
            if warnings:
                for w in warnings:
                    print(f"⚠ {w}")
            print("=" * 60)

        return plan
