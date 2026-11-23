"""FastAPI entry point: no tracking, API keys, or precise GPS needed."""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import httpx
from .logic import build_plan
from .services import fetch_air, generate_explanation

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="SmogWise", version="1.0.0", docs_url="/api/docs")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class Profile(BaseModel):
    city: str = Field(min_length=2, max_length=80)
    commute: str = Field(default="public", pattern="^(public|car|bike)$")
    household: str = Field(default="family", pattern="^(family|community|individual)$")
    budget: str = Field(default="low", pattern="^(low|medium)$")
    sensitive: bool = False

    @field_validator("city")
    @classmethod
    def city_safe(cls, value: str) -> str:
        if not all(c.isalpha() or c.isspace() or c in "-.'" for c in value):
            raise ValueError("Use a city name with letters only")
        return value.strip()


class ChatRequest(BaseModel):
    profile: Profile
    question: str = Field(min_length=2, max_length=500)


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


async def safe_plan(profile: Profile) -> dict:
    try:
        data = await fetch_air(profile.city)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (httpx.HTTPError, KeyError, TypeError):
        data = {"location": profile.city, "aqi": None, "pm25": None, "hours": [], "updated": None, "data_status": "unavailable"}
    return build_plan(profile.model_dump(), data)


@app.post("/api/plan")
async def plan(profile: Profile):
    return await safe_plan(profile)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    result = await safe_plan(request.profile)
    generated = await generate_explanation(request.question, result)
    if generated:
        return {"answer": generated, "mode": "genai", "plan": result}
    top = result["recommendations"][:3]
    intro = "Live AQI is unavailable right now. " if result["aqi"] is None else f"For {result['location']} (US AQI {result['aqi']}), "
    answer = intro + "here are practical steps: " + " ".join(f"{x['title']}: {x['detail']}" for x in top) + " These are qualitative impacts, not measured personal savings."
    return {"answer": answer, "mode": "rules_fallback", "plan": result}
