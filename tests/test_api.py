from fastapi.testclient import TestClient
from app.main import app
from app import main

client = TestClient(app)


def test_health():
    assert client.get('/api/health').json() == {"ok": True}


def test_profile_validation():
    response = client.post('/api/plan', json={"city": "a; bad"})
    assert response.status_code == 422


def test_plan_with_mocked_external(monkeypatch):
    async def stub(city):
        return {"location": "Delhi, India", "aqi": 187, "pm25": 75, "updated": "2026-11-23T12:00", "hours": [], "data_status": "live_forecast"}
    monkeypatch.setattr(main, 'fetch_air', stub)
    response = client.post('/api/plan', json={"city":"Delhi", "sensitive": True})
    assert response.status_code == 200
    data = response.json()
    assert data['aqi'] == 187
    assert any('sensitive' in r['title'].lower() for r in data['recommendations'])


def test_chat_without_key(monkeypatch):
    async def stub(city):
        return {"location":"Delhi", "aqi":90,"pm25":20,"hours":[],"data_status":"live_forecast"}
    async def no_ai(question,plan):
        return None
    monkeypatch.setattr(main,'fetch_air',stub)
    monkeypatch.setattr(main,'generate_explanation',no_ai)
    response=client.post('/api/chat',json={"profile":{"city":"Delhi"},"question":"What should I do?"})
    assert response.status_code==200
    assert response.json()['mode']=='rules_fallback'
