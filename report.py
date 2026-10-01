"""
report.py
Formats a TripPlan into a readable text summary. Kept separate from
the agents/orchestrator so presentation logic doesn't pollute the
planning logic.
"""

from models import TripPlan


def render_report(plan: TripPlan) -> str:
    r = plan.request
    lines = []
    lines.append("TRIP SUMMARY")
    lines.append(f"  Route: {r.origin} -> {' -> '.join(r.cities)} -> {r.origin}")
    lines.append(f"  Dates: {r.start_date} to {r.end_date} ({(r.end_date - r.start_date).days} days)")
    lines.append(f"  Travelers: {r.travelers}")
    lines.append("")

    lines.append("FLIGHTS")
    for f in plan.flights:
        lines.append(f"  {f.origin} -> {f.destination} | {f.airline} | ${f.price} | "
                     f"{f.duration_hours}h | {f.stops} stop(s)")
    lines.append("")

    lines.append("HOTELS")
    for h in plan.hotels:
        nights = (h.check_out - h.check_in).days
        lines.append(f"  {h.city}: {h.name} (★{h.rating}) | ${h.price_per_night}/night x {nights}n "
                     f"= ${h.total_price}")
    lines.append("")

    lines.append("BUDGET")
    b = plan.budget
    lines.append(f"  Total budget:     ${b.total_budget}")
    lines.append(f"  Flights cost:     ${b.flights_cost}")
    lines.append(f"  Hotels cost:      ${b.hotels_cost}")
    lines.append(f"  Contingency (10%):${b.contingency}")
    lines.append(f"  Daily spend:      ${b.daily_spend_estimate}/day x {b.daily_spend_days} days")
    lines.append(f"  Remaining:        ${b.remaining}")
    lines.append(f"  Status:           {'WITHIN BUDGET' if b.within_budget else 'OVER BUDGET'}")
    lines.append("")

    lines.append("DAY-BY-DAY ITINERARY")
    for day in plan.itinerary:
        w = day.weather
        weather_str = f" | {w.condition}, {w.temp_low_c}-{w.temp_high_c}°C" if w else ""
        advisory = f" ⚠ {w.advisory}" if (w and w.advisory) else ""
        lines.append(f"  Day {day.day_number} - {day.city} ({day.date}){weather_str}{advisory}")
        for act in day.activities:
            lines.append(f"      - {act}")
    lines.append("")

    if plan.warnings:
        lines.append("WARNINGS")
        for w in plan.warnings:
            lines.append(f"  ⚠ {w}")

    return "\n".join(lines)
