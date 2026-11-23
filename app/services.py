"""External HTTP calls are centralized, bounded and never trusted blindly."""
import os
import httpx

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
AIR = "https://air-quality-api.open-meteo.com/v1/air-quality"
AI_URL = "https://api.openai.com/v1/responses"


async def fetch_air(city: str) -> dict:
    async with httpx.AsyncClient(timeout=8.0) as client:
        geo = (await client.get(GEOCODE, params={"name": city, "count": 1, "language": "en", "format": "json"})).raise_for_status().json()
        found = geo.get("results") or []
        if not found:
            raise ValueError("Location not found. Try a larger nearby city.")
        place = found[0]
        params = {"latitude": place["latitude"], "longitude": place["longitude"], "current": "us_aqi,pm2_5", "hourly": "us_aqi", "forecast_days": 2, "timezone": "auto"}
        payload = (await client.get(AIR, params=params)).raise_for_status().json()
    current = payload.get("current") or {}
    hourly = payload.get("hourly") or {}
    times, aqis = hourly.get("time", []), hourly.get("us_aqi", [])
    hours = [{"time": t.replace("T", " "), "aqi": a} for t, a in zip(times, aqis) if a is not None][:48]
    name = ", ".join(filter(None, [place.get("name"), place.get("admin1"), place.get("country")]))
    return {"location": name, "aqi": current.get("us_aqi"), "pm25": current.get("pm2_5"), "updated": current.get("time"), "hours": hours, "data_status": "live_forecast"}


async def generate_explanation(question: str, plan: dict) -> str | None:
    """Optional AI narrative grounded only in plan facts; fail closed to local answer."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    import json
    facts = {"location": plan["location"], "aqi": plan["aqi"], "scale": plan["aqi_scale"], "status": plan["data_status"], "recommendations": plan["recommendations"][:7]}
    instructions = ("You are SmogWise, an air-quality education assistant. Use ONLY the supplied facts. "
                    "Never invent live measurements, numeric emissions/health impacts, or guarantee protection. "
                    "Do not give diagnoses. For symptoms, refer to medical professionals. "
                    "If data is unavailable, acknowledge it. Keep answer under 130 words; offer concrete low-cost steps.")
    body = {"model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "instructions": instructions, "input": f"User question: {question}\nVerified planning facts: {json.dumps(facts)}", "max_output_tokens": 230, "store": False}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            res = (await client.post(AI_URL, headers={"Authorization": f"Bearer {key}"}, json=body)).raise_for_status().json()
        parts = [c.get("text", "") for item in res.get("output", []) for c in item.get("content", []) if c.get("type") == "output_text"]
        return "\n".join(parts).strip() or None
    except (httpx.HTTPError, ValueError, KeyError):
        return None
