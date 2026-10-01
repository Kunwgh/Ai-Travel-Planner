"""
main.py
Demo entry point for the AI Travel Planner multi-agent system.

Run:
    python main.py

Edit the TripRequest below (or wire up argparse / a web form) to plan
a different trip.
"""

from datetime import date

from models import TripRequest
from orchestrator import TravelOrchestrator
from report import render_report


def build_sample_request() -> TripRequest:
    return TripRequest(
        origin="New York",
        cities=["Paris", "Rome", "Barcelona"],
        start_date=date(2026, 9, 10),
        end_date=date(2026, 9, 22),
        travelers=2,
        total_budget=6000.0,
        currency="USD",
        preferences=["museums", "food", "history"],
    )


def main():
    request = build_sample_request()
    orchestrator = TravelOrchestrator(verbose=True)
    plan = orchestrator.plan_trip(request)

    print("\n\n" + render_report(plan))


if __name__ == "__main__":
    main()
