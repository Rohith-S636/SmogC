# SmogWise — Air-Quality Copilot

**Vertical / persona:** Family and community urban-smog resilience. SmogWise helps households and neighborhood organizers reduce **exposure** during severe smog and choose practical, lower-emission habits.

## Features

- City-based **US AQI**, PM2.5 and hourly forecast from Open-Meteo/CAMS ENSEMBLE; no GPS needed.
- Personalized advice for family/community, commuting, budget and sensitive household members.
- Explicit **exposure** versus **emissions** impacts for every recommendation, without invented savings.
- Optional OpenAI Responses API chatbot; no-key rule-based fallback.
- Responsive, accessible, lightweight interface with no account or tracking.

## Run locally

Requires Python 3.11+. From the repository root:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000. Optionally set OPENAI_API_KEY in your shell; the core app works without one. FastAPI does not load .env automatically.

## Logic and architecture

1. Validate the city and household preferences (Pydantic).
2. Geocode the city and request the latest model-estimated US AQI and PM2.5.
3. Apply an auditable decision engine to the AQI band, commute, budget and sensitivity context.
4. Produce **action → reason → qualitative impact** cards, with weather/air-data fallback.
5. Ground optional GenAI answers in verified action facts only.

```text
Browser (HTML/CSS/JS)
  ├─ POST /api/plan ─→ FastAPI → Open-Meteo → rule engine → action cards
  └─ POST /api/chat ─→ FastAPI → optional OpenAI Responses API
                                   └→ deterministic fallback
```

## Safety and assumptions

- Open-Meteo outputs **US AQI**, NOT India's CPCB AQI. The scales are not interchangeable; follow official local guidance.
- Air values are forecast/model estimates, not readings from a street-level monitor.
- No precise CO₂ or medical outcome claims: route lengths, vehicle types, indoor monitors and controlled comparisons are unavailable.
- For high pollution, prioritize reducing exposure over encouraging outdoor active travel.
- The tool provides educational guidance, not diagnosis, treatment or emergency instructions.
- Sensitive-member preferences are voluntary and not persisted. No accounts, analytics, or precise location tracking.
- Outbound HTTP calls go to fixed HTTPS endpoints, with bounded timeouts. For internet deployment use HTTPS and rate limits.
- Live readings require internet; optional GenAI requires an API key. Without either, appropriate fallback is shown.

## Tests

```bash
pytest -q
```

Tests exercise AQI boundaries, sensitivity and severity rules, no-cost advice, cleaner-hour selection, API validation and AI fallback. GitHub Actions runs on main.

## Submission checklist

- [x] Public repository
- [x] One branch: main
- [x] Small source files, without virtual environments or model weights
- [x] Vertical, logic, instructions and assumptions documented
- [ ] Confirm CI run and browser flow after pushing

## Sources

- [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) — CAMS ENSEMBLE data
- [WHO air pollution personal interventions](https://www.who.int/news-room/questions-and-answers/item/air-pollution-personal-interventions-and-risk-communication)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)

MIT licensed. Educational prototype, not a regulatory alert service.
