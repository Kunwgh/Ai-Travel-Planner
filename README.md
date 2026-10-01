# AI Travel Planner — Multi-Agent System

A multi-agent trip-planning system in pure Python. Five specialized agents
(flights, hotels, weather, budget, itinerary) each own one job; an
**orchestrator** coordinates them into a single optimized multi-city
itinerary that respects the traveler's budget and preferences.

No API keys are required to run it — every agent ships with a deterministic
mock data provider, and every provider is a swappable interface so you can
plug in real APIs later without touching the agents' logic.

## Architecture

```
                        ┌─────────────────────┐
                        │   TravelOrchestrator │
                        └──────────┬───────────┘
                                   │
        ┌───────────┬─────────────┼─────────────┬────────────┐
        ▼           ▼             ▼              ▼            ▼
  FlightAgent  HotelAgent   WeatherAgent   BudgetAgent  ItineraryAgent
        │           │             │              │            │
        ▼           ▼             ▼              │            │
  FlightProvider HotelProvider WeatherProvider    │            │
   (mock/real)   (mock/real)   (mock/real)        │            │
        │           │             │               │            │
        └─────┬─────┴──────┬──────┘               │            │
              ▼            ▼                      ▼            ▼
          flights[]    hotels[]  ─────────►  BudgetBreakdown ─► ItineraryDay[]
                          weather[] ─────────────────────────────────┘
```

**Pipeline order** (`orchestrator.py`):
1. **FlightAgent** — prices every leg of the multi-city route (origin → city 1
   → city 2 → ... → origin) and picks the cheapest option per leg.
2. **HotelAgent** — picks a best-value hotel (rating-filtered, then cheapest)
   for each city, sized to the correct number of nights.
3. **WeatherAgent** — forecasts every city/date on the trip and raises
   advisories (rain, extreme heat, cold).
4. **BudgetAgent** — reconciles flights + hotels against the total budget,
   sets aside a 10% contingency, and derives a daily spend allowance from
   what's left.
5. **ItineraryAgent** — builds the day-by-day plan from the user's stated
   preferences (museums, food, nature, ...), automatically swapping in
   indoor activities on days with a bad-weather advisory.

Every agent inherits from `BaseAgent` (`agents/base_agent.py`), which gives
them a uniform `.run()` contract plus timing/error-handling via
`.timed_run()` — this is what lets the orchestrator treat all five agents
identically.

## Project structure

```
ai_travel_planner/
├── main.py                  # demo entry point
├── orchestrator.py          # coordination layer
├── models.py                 # shared dataclasses (TripRequest, Flight, Hotel, ...)
├── report.py                 # renders a TripPlan as readable text
├── requirements.txt
└── agents/
    ├── base_agent.py         # abstract base class all agents implement
    ├── flight_agent.py       # + MockFlightProvider
    ├── hotel_agent.py        # + MockHotelProvider
    ├── weather_agent.py      # + MockWeatherProvider
    ├── budget_agent.py
    └── itinerary_agent.py
```

## Running it

Requires only the Python standard library:

```bash
python main.py
```

This plans a sample 12-day New York → Paris → Rome → Barcelona → New York
trip for 2 travelers on a $6,000 budget, prints each agent's reasoning as
it runs, then prints a final formatted report.

To plan your own trip, edit `build_sample_request()` in `main.py`:

```python
TripRequest(
    origin="New York",
    cities=["Paris", "Rome", "Barcelona"],
    start_date=date(2026, 9, 10),
    end_date=date(2026, 9, 22),
    travelers=2,
    total_budget=6000.0,
    currency="USD",
    preferences=["museums", "food", "history"],  # see ACTIVITY_BANK in itinerary_agent.py
)
```

## Going live: swapping in real APIs

Every data source is defined as a `Protocol` (structural interface) with a
mock implementation. To use real data, write a class matching the same
method signature and pass it into the agent's constructor — nothing else
changes.

| Agent | Interface | Example real providers |
|---|---|---|
| `FlightAgent` | `search(origin, destination, depart_date) -> list[Flight]` | Amadeus Self-Service API, Skyscanner (RapidAPI), Kiwi Tequila |
| `HotelAgent` | `search(city, check_in, check_out) -> list[Hotel]` | Booking.com (RapidAPI), Expedia Rapid API |
| `WeatherAgent` | `forecast(city, date) -> WeatherForecast` | OpenWeatherMap, WeatherAPI.com |

Example:

```python
class AmadeusFlightProvider:
    def search(self, origin, destination, depart_date):
        # call the real Amadeus API, map the JSON response into Flight objects
        ...

orchestrator = TravelOrchestrator()
orchestrator.flight_agent = FlightAgent(provider=AmadeusFlightProvider())
```

Put real API keys in a `.env` file (see the commented-out `python-dotenv`
line in `requirements.txt`) — never hardcode them.

## Extending the system

- **New agent**: subclass `BaseAgent`, implement `run()`, wire it into
  `TravelOrchestrator.plan_trip()`.
- **New preference / activity type**: add an entry to `ACTIVITY_BANK` in
  `agents/itinerary_agent.py`.
- **LLM-personalized itinerary text**: add an `LLMNarratorAgent` at the end
  of the pipeline that takes the assembled `TripPlan` and asks an LLM (e.g.
  the Anthropic API) to turn it into flowing prose / a shareable write-up.
- **Web UI**: `TravelOrchestrator.plan_trip(request) -> TripPlan` is a clean
  functional boundary — wrap it in a FastAPI/Flask endpoint and serialize
  `TripPlan` (it's plain dataclasses) to JSON for a frontend.
