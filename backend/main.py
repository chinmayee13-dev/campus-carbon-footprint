"""
Main FastAPI application entry point.
Exposes REST APIs for campus carbon management, AI agent chat, what-if simulations,
and serves frontend static files.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.database.db import init_db
from backend.database.repository import (
    get_all_records,
    get_recent_records,
    get_latest_record,
    get_previous_record,
    save_or_update_record,
    get_record_by_month
)
from backend.calculations.emission_calc import load_emission_factors, calc_total_footprint
from backend.agent.agent import CarbonAgent
from backend.tools.whatif_tool import simulate_reduction
from backend.tools.recommendation_tool import generate_reduction_plan

# Initialize FastAPI app
app = FastAPI(
    title="Campus Carbon Management Agent API",
    description="AI-powered campus carbon monitoring, deterministic calculations, historical analytics, and reduction planning.",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent and Database on startup
agent = CarbonAgent()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.on_event("startup")
def on_startup():
    """Ensure database schema is created and seeded with 6 months of data."""
    init_db()


# -------------------------------------------------------------
# Pydantic Request Models
# -------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., description="Administrator natural language question or prompt")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="Previous conversation turns")


class CampusDataInput(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format (e.g. '2026-04')")
    electricity_kwh: float = Field(..., ge=0, description="Monthly electricity in kWh")
    cars: int = Field(default=0, ge=0, description="Number of commuter passenger cars")
    car_distance: float = Field(default=0.0, ge=0, description="Average commute distance per car in km")
    motorcycles: int = Field(default=0, ge=0, description="Number of commuter motorcycles/scooters")
    motorcycle_distance: float = Field(default=0.0, ge=0, description="Average distance per motorcycle in km")
    bus_fuel: float = Field(default=0.0, ge=0, description="Diesel fuel in liters for campus transit shuttles")
    organic_waste: float = Field(default=0.0, ge=0, description="Organic/food waste in kg")
    plastic_waste: float = Field(default=0.0, ge=0, description="Plastic waste in kg")
    paper_waste: float = Field(default=0.0, ge=0, description="Paper/cardboard waste in kg")


class SimulationRequest(BaseModel):
    category: str = Field(default="electricity", description="Category: electricity, transportation, waste, or all")
    reduction_percentage: float = Field(default=15.0, ge=0, le=100, description="Target reduction percentage")


# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.get("/api/status")
def get_status() -> Dict[str, Any]:
    """Check agent operational mode and AI provider status."""
    return agent.get_agent_status()


@app.post("/api/agent/chat")
async def chat_with_agent(req: ChatRequest) -> Dict[str, Any]:
    """
    Process natural-language administrator queries.
    Agent autonomously selects and calls deterministic tools, reasons over results,
    and returns answer + tool audit trace.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    result = await agent.process_message(req.message, req.history)
    return result


@app.get("/api/dashboard")
def get_dashboard_summary() -> Dict[str, Any]:
    """Retrieve full dashboard KPI cards, historical trend data, and breakdowns."""
    records = get_recent_records(months=12)
    latest = get_latest_record()
    factors = load_emission_factors()

    if not latest:
        return {
            "has_data": False,
            "disclaimer": factors.get("disclaimer"),
            "message": "No campus carbon footprint data recorded yet."
        }

    # Month over month metrics
    prev = get_previous_record(latest["month"])
    mom_change_pct = 0.0
    mom_change_abs = 0.0
    trend = "steady"

    if prev and prev.get("total_emissions", 0) > 0:
        mom_change_abs = round(latest["total_emissions"] - prev["total_emissions"], 2)
        mom_change_pct = round((mom_change_abs / prev["total_emissions"]) * 100.0, 1)
        trend = "increased" if mom_change_abs > 0 else ("decreased" if mom_change_abs < 0 else "steady")

    # Category breakdown for latest month
    breakdown = calc_total_footprint(
        latest["electricity_emissions"],
        latest["transportation_emissions"],
        latest["waste_emissions"]
    )

    # Reduction plan based on latest breakdown
    reduction_plan = generate_reduction_plan(carbon_breakdown=breakdown, historical_data=records)

    return {
        "has_data": True,
        "latest": latest,
        "previous": prev,
        "mom_metrics": {
            "absolute_change_kg_co2e": mom_change_abs,
            "percentage_change": mom_change_pct,
            "trend": trend
        },
        "breakdown": breakdown,
        "records": records,
        "recommendations": reduction_plan.get("recommendations", [])[:3],
        "disclaimer": factors.get("disclaimer"),
        "agent_status": agent.get_agent_status()
    }


@app.post("/api/campus-data")
def record_campus_data(payload: CampusDataInput) -> Dict[str, Any]:
    """Log or update monthly campus activity data and recalculate emissions."""
    data = payload.dict()
    saved = save_or_update_record(data)
    return {
        "status": "success",
        "message": f"Successfully recorded carbon footprint data for {saved['month']}",
        "record": saved
    }


@app.get("/api/emission-factors")
def get_factors() -> Dict[str, Any]:
    """Retrieve emission factors with documentation, units, and regulatory citations."""
    return load_emission_factors()


@app.post("/api/simulate")
def run_simulation(req: SimulationRequest) -> Dict[str, Any]:
    """Execute on-demand What-If scenario simulation."""
    return simulate_reduction(req.category, req.reduction_percentage)


# -------------------------------------------------------------
# Static Files & Frontend Serving
# -------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend_root():
        """Serve main frontend single-page application."""
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Campus Carbon Management Agent API is active. Frontend index.html not found."}
