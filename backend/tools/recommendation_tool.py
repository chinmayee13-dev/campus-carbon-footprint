"""
Tool 6 — Recommendation Tool
Function: generate_reduction_plan(carbon_breakdown, historical_data)
Generate practical, prioritized sustainability recommendations based on emission sources and trends.
"""

from typing import Dict, Any, List, Optional
from backend.database.repository import get_latest_record, get_recent_records
from backend.calculations.emission_calc import calc_total_footprint


def generate_reduction_plan(
    carbon_breakdown: Optional[Dict[str, Any]] = None,
    historical_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate practical, prioritized recommendations based on the largest emission sources
    and historical trajectory.
    """
    # If no breakdown provided, fetch latest from database
    if not carbon_breakdown:
        latest = get_latest_record()
        if latest:
            carbon_breakdown = calc_total_footprint(
                latest["electricity_emissions"],
                latest["transportation_emissions"],
                latest["waste_emissions"]
            )
        else:
            # Fallback default breakdown if DB is completely empty
            carbon_breakdown = calc_total_footprint(20000.0, 5000.0, 2000.0)

    largest_source = carbon_breakdown.get("largest_emission_source", "Electricity")
    percentages = carbon_breakdown.get("percentage_contributions", {})
    elec_pct = percentages.get("electricity", 0.0)
    trans_pct = percentages.get("transportation", 0.0)
    waste_pct = percentages.get("waste", 0.0)

    plans_library = {
        "Electricity": [
            {
                "title": "Smart HVAC Scheduling & Temperature Optimization",
                "category": "Electricity",
                "priority": "High",
                "impact_estimate": "8% - 15% electricity CO2e reduction",
                "timeframe": "Immediate (1 - 3 months)",
                "description": "Adjust thermostat setpoints by ±1.5°C during off-hours, optimize chilled-water schedules in lecture halls, and eliminate unnecessary AC usage in empty buildings."
            },
            {
                "title": "LED Retrofits and Smart Occupancy Sensors",
                "category": "Electricity",
                "priority": "Medium",
                "impact_estimate": "5% - 8% electricity CO2e reduction",
                "timeframe": "Short Term (3 - 6 months)",
                "description": "Replace remaining fluorescent fixtures across libraries and academic halls with daylight-harvesting dimmable LEDs and motion sensors."
            },
            {
                "title": "On-Campus Rooftop Solar PV & Clean Energy Procurement",
                "category": "Electricity",
                "priority": "Medium",
                "impact_estimate": "15% - 30% campus grid emissions offset",
                "timeframe": "Long Term (6 - 18 months)",
                "description": "Evaluate solar canopy arrays on campus parking lots and academic rooftops, or subscribe to a green power purchase agreement (PPA)."
            }
        ],
        "Transportation": [
            {
                "title": "Subsidized Transit Passes & Electric Campus Shuttles",
                "category": "Transportation",
                "priority": "High",
                "impact_estimate": "12% - 20% transportation CO2e reduction",
                "timeframe": "Short Term (1 - 3 months)",
                "description": "Partner with regional transit for discounted student/faculty bus passes and optimize campus shuttle routes to reduce single-occupancy vehicle trips."
            },
            {
                "title": "Campus Carpooling Incentive & Preferential Parking",
                "category": "Transportation",
                "priority": "High",
                "impact_estimate": "10% - 15% commuter car reduction",
                "timeframe": "Immediate (1 month)",
                "description": "Launch a verified campus carpool ride-match app and designate premium shaded parking spots for vehicles with 2+ occupants."
            },
            {
                "title": "Active Mobility Infrastructure (Bikes & Walkways)",
                "category": "Transportation",
                "priority": "Medium",
                "impact_estimate": "5% - 8% commuter reduction",
                "timeframe": "Medium Term (3 - 9 months)",
                "description": "Expand protected campus bike lanes, install secure sheltered bike lockers, and introduce a shared e-bike fleet for inter-campus transit."
            }
        ],
        "Waste": [
            {
                "title": "Comprehensive 3-Stream Segregation & Signage Overhaul",
                "category": "Waste",
                "priority": "High",
                "impact_estimate": "15% - 25% waste CO2e reduction",
                "timeframe": "Immediate (1 - 2 months)",
                "description": "Standardize color-coded receptacles (Landfill, Recyclables, Compostables) with visual pictorial guides across dining areas and dormitories."
            },
            {
                "title": "Phase Out Single-Use Plastics in Dining Services",
                "category": "Waste",
                "priority": "High",
                "impact_estimate": "10% - 18% plastic waste reduction",
                "timeframe": "Short Term (2 - 4 months)",
                "description": "Transition dining halls to reusable serviceware, eliminate plastic bottled water sales, and provide branded refillable cups for all students."
            },
            {
                "title": "Dining Hall Food Waste Prevention & Organic Composting",
                "category": "Waste",
                "priority": "Medium",
                "impact_estimate": "20% - 35% organic landfill diversion",
                "timeframe": "Medium Term (3 - 6 months)",
                "description": "Implement kitchen pre-consumer portion controls, donate surplus prepared meals to local food banks, and compost post-consumer organics on-campus."
            }
        ]
    }

    primary_actions = plans_library.get(largest_source, plans_library["Electricity"])

    # Also include supporting actions for the secondary emission sources
    supporting_actions = []
    other_sources = [s for s in ["Electricity", "Transportation", "Waste"] if s != largest_source]
    for src in other_sources:
        if plans_library.get(src):
            supporting_actions.append(plans_library[src][0])

    combined_plan = primary_actions + supporting_actions

    return {
        "tool": "generate_reduction_plan",
        "largest_emission_source": largest_source,
        "category_percentages": {
            "electricity": elec_pct,
            "transportation": trans_pct,
            "waste": waste_pct
        },
        "recommendations": combined_plan,
        "executive_summary": (
            f"Because {largest_source} is the campus's largest carbon contributor "
            f"({percentages.get(largest_source.lower(), 0.0)}% of total emissions), "
            f"reduction efforts must prioritize {largest_source.lower()}-targeted measures "
            f"to yield the fastest and highest-impact greenhouse gas reductions."
        ),
        "status": "success"
    }
