"""Deterministic, auditable decision engine for air-quality guidance.

AQI is the US AQI scale supplied by Open-Meteo, NOT India's CPCB AQI.
"""
from __future__ import annotations
from typing import Any


def aqi_band(aqi: float | None) -> dict[str, str]:
    if aqi is None:
        return {"label": "Unavailable", "tone": "unknown", "message": "Live data unavailable; follow local official advisories."}
    if aqi <= 50:
        return {"label": "Good", "tone": "good", "message": "Outdoor activities are generally suitable for most people."}
    if aqi <= 100:
        return {"label": "Moderate", "tone": "moderate", "message": "Unusually sensitive people may wish to reduce prolonged exertion outdoors."}
    if aqi <= 150:
        return {"label": "Unhealthy for sensitive groups", "tone": "sensitive", "message": "Sensitive groups should limit long or strenuous outdoor activities."}
    if aqi <= 200:
        return {"label": "Unhealthy", "tone": "unhealthy", "message": "Reduce prolonged outdoor exertion; prioritize cleaner indoor activities."}
    if aqi <= 300:
        return {"label": "Very unhealthy", "tone": "very-unhealthy", "message": "Avoid unnecessary prolonged outdoor activity; follow official alerts."}
    return {"label": "Hazardous", "tone": "hazardous", "message": "Stay indoors where air is cleaner; follow emergency public health instructions."}


def _rec(title: str, detail: str, impact: str, category: str, why: str, priority: int) -> dict[str, Any]:
    return dict(title=title, detail=detail, impact=impact, category=category, why=why, priority=priority)


def recommendations(profile: dict, aqi: float | None, hours: list[dict]) -> list[dict]:
    """Safe rules first; LLM can rephrase, but cannot override these actions."""
    risk = aqi is None or aqi > 100
    severe = aqi is not None and aqi > 200
    vulnerable = profile.get("sensitive", False)
    commute = profile.get("commute", "public")
    budget = profile.get("budget", "low")
    household = profile.get("household", "family")
    items = []
    if risk:
        items.append(_rec("Make a cleaner-air room", "Close windows facing traffic during pollution peaks, seal obvious gaps, and prioritize filtration in the room used most.", "Exposure: may lower indoor particle infiltration; benefit depends on building and filtration.", "Indoor air", "Outdoor particles can enter homes through gaps and windows.", 1))
    else:
        items.append(_rec("Ventilate strategically", "Ventilate when local outdoor air is comparatively cleaner; avoid opening windows during roadside rush-hour spikes.", "Exposure: helps reduce indoor-source pollutants when outside conditions permit.", "Indoor air", "Indoor air quality also depends on cooking and cleaning sources.", 2))
    items.append(_rec("Remove indoor smoke sources", "Avoid incense, smoking, candles, and burning waste indoors; use exhaust ventilation while cooking when safely possible.", "Exposure: reduces pollution produced inside your home; no numeric reduction claimed.", "Indoor air", "Combustion indoors creates pollution even when outside air is clean.", 1))
    if risk:
        items.append(_rec("Move exercise indoors", "Replace long outdoor runs with indoor movement while pollution is elevated. Keep essential outdoor trips short.", "Exposure: reduces time and heavy breathing in polluted outdoor air.", "Daily routine", "Exercise increases the volume of air inhaled.", 1))
    if vulnerable:
        items.append(_rec("Plan for sensitive family members", "For children, older adults, pregnant people or those with heart/lung conditions, favor cleaner indoor activities and follow clinician/local-authority advice.", "Exposure: avoids unnecessary high-pollution activity; does not replace medical care.", "Family safety", "Sensitive groups can face greater risk during pollution episodes.", 1))
    if severe:
        items.append(_rec("High-pollution precautions", "Avoid discretionary outdoor trips. If an essential trip is unavoidable, consider a well-fitting certified particulate respirator appropriate to the wearer.", "Exposure: may reduce inhalation of particles when correctly fitted; does not remove gaseous pollutants.", "Family safety", "Very high AQI calls for stronger exposure reduction.", 1))
    if commute == "car":
        items.append(_rec("Combine car trips", "Group errands, avoid idling, and consider shared rides or public transport on cleaner-air routes.", "Emissions: fewer vehicle-kilometres can reduce tailpipe emissions; savings not quantified.", "Lower emissions", "Unnecessary driving and idling add to local emissions.", 2))
    elif commute == "bike":
        items.append(_rec("Choose a low-traffic route", "Cycle or walk on quieter streets when air quality allows; on polluted days choose low-exertion alternatives instead.", "Exposure: reduces proximity to traffic exhaust; route and AQI matter.", "Daily routine", "Traffic corridors often have elevated near-road pollution.", 2))
    else:
        items.append(_rec("Make shared journeys easier", "Combine errands and favor public transit or shared travel when it is safe and practical.", "Emissions: shared transport can reduce per-person emissions compared with solo driving; not a measured saving.", "Lower emissions", "Transport choices can reduce contributions to urban emissions.", 3))
    if budget == "low":
        items.append(_rec("Start with no-cost improvements", "Wet-mop dusty surfaces, reduce smoke sources, and use safe ventilation timing before considering equipment purchases.", "Cost: low or zero purchase cost; impact varies and wet-mopping alone cannot filter outdoor PM2.5.", "Budget tips", "Source control is often an accessible first intervention.", 2))
    else:
        items.append(_rec("Consider a sized HEPA purifier", "If affordable, select a properly sized HEPA air purifier with an appropriate clean air delivery rate; replace filters as directed.", "Exposure: filtration can reduce indoor particulate levels; effectiveness depends on room size and usage.", "Indoor air", "Particle filtration helps with infiltrated and indoor-generated particles.", 2))
    if household == "community":
        items.append(_rec("Organize a neighborhood clean-air plan", "Share official alerts, coordinate no-idling at school gates, and identify clean indoor spaces for vulnerable neighbors.", "Community: may reduce localized emissions and improve access to timely guidance.", "Community", "Coordinated behavior can reduce exposure for many households.", 2))
    candidates = [(h.get("aqi"), h.get("time")) for h in hours if isinstance(h.get("aqi"), (int, float))]
    if candidates:
        best_aqi, best_time = min(candidates)
        if best_aqi <= 100 and (aqi is None or best_aqi < aqi):
            items.append(_rec("Use the cleaner forecast window", f"If a trip is essential, consider {best_time} (forecast US AQI {round(best_aqi)}), while checking conditions again before leaving.", "Exposure: choosing a lower-AQI time may reduce outdoor exposure; forecasts are uncertain.", "Daily routine", "Pollution levels can change across the day.", 2))
    return sorted(items, key=lambda r: r["priority"])


def build_plan(profile: dict, data: dict) -> dict:
    aqi = data.get("aqi")
    hours = data.get("hours", [])
    band = aqi_band(aqi)
    return {"location": data.get("location", profile["city"]), "aqi": aqi, "pm25": data.get("pm25"), "updated": data.get("updated"), "data_status": data.get("data_status", "unavailable"), "aqi_scale": "US AQI (not CPCB India AQI)", "band": band, "hourly": hours, "recommendations": recommendations(profile, aqi, hours), "attribution": "Air quality: Open-Meteo / CAMS ENSEMBLE. Forecast model estimates, not street-level sensor readings."}
