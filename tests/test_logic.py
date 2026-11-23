from app.logic import aqi_band, recommendations, build_plan

BASE = {"city":"Delhi", "commute":"car", "household":"family", "budget":"low", "sensitive":False}


def test_boundaries():
    assert aqi_band(50)["label"] == "Good"
    assert aqi_band(100)["label"] == "Moderate"
    assert aqi_band(101)["tone"] == "sensitive"
    assert aqi_band(301)["tone"] == "hazardous"
    assert aqi_band(None)["tone"] == "unknown"


def test_severe_sensitive_includes_precautions():
    titles = [r["title"] for r in recommendations({**BASE, "sensitive":True}, 250, [])]
    assert "High-pollution precautions" in titles
    assert "Plan for sensitive family members" in titles
    assert "Move exercise indoors" in titles


def test_low_budget_no_purchase_requirement():
    names = [r["title"] for r in recommendations(BASE, 190, [])]
    assert "Start with no-cost improvements" in names
    assert "Consider a sized HEPA purifier" not in names


def test_no_false_precision():
    plan = build_plan(BASE, {"aqi":None,"location":"Delhi","data_status":"unavailable"})
    assert plan["aqi"] is None
    assert plan["data_status"] == "unavailable"
    assert "US AQI" in plan["aqi_scale"]


def test_cleaner_hour_included():
    recs = recommendations(BASE, 150, [{"time":"2026-11-24 11:00", "aqi":80}])
    assert any(r["title"] == "Use the cleaner forecast window" for r in recs)


def test_good_air_does_not_trigger_severe():
    titles = [r["title"] for r in recommendations(BASE, 35, [])]
    assert "High-pollution precautions" not in titles
    assert "Ventilate strategically" in titles
