"""
Verification script for Campus Carbon Management Agent tools and calculations.
"""

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from backend.database.db import init_db
from backend.database.repository import get_all_records, get_latest_record
from backend.calculations.emission_calc import (
    calc_electricity_emissions,
    calc_transport_emissions,
    calc_waste_emissions,
    calc_total_footprint
)
from backend.tools.electricity_tool import calculate_electricity_emissions
from backend.tools.transport_tool import calculate_transport_emissions
from backend.tools.waste_tool import calculate_waste_emissions
from backend.tools.total_tool import calculate_total_footprint
from backend.tools.history_tool import get_historical_data
from backend.tools.recommendation_tool import generate_reduction_plan
from backend.tools.whatif_tool import simulate_reduction
from backend.agent.agent import CarbonAgent


def test_all():
    print("1. Testing DB init and seeding...")
    init_db(force_reseed=True)
    records = get_all_records()
    print(f"   [OK] Seeded {len(records)} monthly records.")
    assert len(records) >= 6, f"Expected >=6 records, got {len(records)}"

    print("2. Testing Deterministic Calculations...")
    e = calc_electricity_emissions(1000)
    assert e["emissions_kg_co2e"] == 385.0, f"Expected 385.0, got {e['emissions_kg_co2e']}"
    print(f"   [OK] Electricity: 1000 kWh = {e['emissions_kg_co2e']} kg CO2e")

    t = calc_transport_emissions(cars=10, car_distance=10, motorcycles=5, motorcycle_distance=10, bus_fuel=20)
    print(f"   [OK] Transport emissions = {t['emissions_kg_co2e']} kg CO2e")

    w = calc_waste_emissions(organic_waste=100, plastic_waste=50, paper_waste=80)
    assert w["emissions_kg_co2e"] == 226.0, f"Expected 226.0, got {w['emissions_kg_co2e']}"
    print(f"   [OK] Waste emissions = {w['emissions_kg_co2e']} kg CO2e")

    tot = calc_total_footprint(e["emissions_kg_co2e"], t["emissions_kg_co2e"], w["emissions_kg_co2e"])
    print(f"   [OK] Total footprint: {tot['total_emissions_kg_co2e']} kg CO2e, Largest: {tot['largest_emission_source']}")

    print("3. Testing Tools...")
    h = get_historical_data(months=3)
    assert h["status"] == "success"
    print(f"   [OK] History tool returned {len(h['records'])} records.")

    plan = generate_reduction_plan()
    assert len(plan["recommendations"]) > 0
    print(f"   [OK] Recommendation tool returned {len(plan['recommendations'])} actions.")

    sim = simulate_reduction("electricity", 20.0)
    assert sim["status"] == "success"
    print(f"   [OK] Simulation tool: 20% reduction = -{sim['simulation']['estimated_monthly_reduction_kg_co2e']} kg CO2e")

    print("4. Testing Agent Intent Reasoning...")
    agent = CarbonAgent()
    import asyncio
    
    # Test What-If
    r1 = asyncio.run(agent.process_message("What if electricity consumption decreases by 15%?"))
    assert len(r1["tool_calls"]) > 0
    assert r1["tool_calls"][0]["tool"] == "simulate_reduction"
    print("   [OK] Agent What-If: Tool called ->", r1["tool_calls"][0]["tool"])

    # Test Historical Comparison
    r2 = asyncio.run(agent.process_message("Why did our emissions increase compared to previous month?"))
    assert len(r2["tool_calls"]) > 0
    assert r2["tool_calls"][0]["tool"] == "get_historical_data"
    print("   [OK] Agent Comparison: Tool called ->", r2["tool_calls"][0]["tool"])

    # Test Action Plan
    r3 = asyncio.run(agent.process_message("How can we reduce our emissions?"))
    assert len(r3["tool_calls"]) > 0
    assert r3["tool_calls"][0]["tool"] == "generate_reduction_plan"
    print("   [OK] Agent Reduction Plan: Tool called ->", r3["tool_calls"][0]["tool"])

    print("\nALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_all()
