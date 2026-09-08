"""
Deterministic calculation engine for campus greenhouse gas emissions.
Calculations use standardized emission factors loaded from data/emission_factors.json.
No calculations are delegated to the LLM.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

FACTORS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "emission_factors.json"

DEFAULT_FACTORS = {
    "electricity": 0.385,          # kg CO2e / kWh
    "car": 0.171,                  # kg CO2e / km
    "motorcycle": 0.103,           # kg CO2e / km
    "bus_fuel": 2.680,             # kg CO2e / liter
    "organic_waste": 0.450,        # kg CO2e / kg
    "plastic_waste": 2.100,        # kg CO2e / kg
    "paper_waste": 0.950           # kg CO2e / kg
}


def load_emission_factors() -> Dict[str, Any]:
    """Load configurable emission factors with metadata and citations."""
    try:
        if FACTORS_FILE.exists():
            with open(FACTORS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning loading emission factors file: {e}. Falling back to defaults.")
    
    return {
        "disclaimer": "Carbon footprint values are estimates. Actual emissions depend on regional emission factors, data quality, and accounting methodology.",
        "factors": {
            "electricity": {"kwh_factor": DEFAULT_FACTORS["electricity"], "unit": "kg CO2e / kWh"},
            "transportation": {"car_km_factor": DEFAULT_FACTORS["car"], "unit": "kg CO2e / km"},
            "transportation_motorcycle": {"motorcycle_km_factor": DEFAULT_FACTORS["motorcycle"], "unit": "kg CO2e / km"},
            "transportation_bus": {"bus_fuel_liter_factor": DEFAULT_FACTORS["bus_fuel"], "unit": "kg CO2e / liter"},
            "waste_organic": {"kg_factor": DEFAULT_FACTORS["organic_waste"], "unit": "kg CO2e / kg"},
            "waste_plastic": {"kg_factor": DEFAULT_FACTORS["plastic_waste"], "unit": "kg CO2e / kg"},
            "waste_paper": {"kg_factor": DEFAULT_FACTORS["paper_waste"], "unit": "kg CO2e / kg"},
        }
    }


def get_factors_map() -> Dict[str, float]:
    """Extract flat mapping of factor names to numeric values."""
    factors_data = load_emission_factors().get("factors", {})
    return {
        "electricity": float(factors_data.get("electricity", {}).get("kwh_factor", DEFAULT_FACTORS["electricity"])),
        "car": float(factors_data.get("transportation", {}).get("car_km_factor", DEFAULT_FACTORS["car"])),
        "motorcycle": float(factors_data.get("transportation_motorcycle", {}).get("motorcycle_km_factor", DEFAULT_FACTORS["motorcycle"])),
        "bus_fuel": float(factors_data.get("transportation_bus", {}).get("bus_fuel_liter_factor", DEFAULT_FACTORS["bus_fuel"])),
        "organic_waste": float(factors_data.get("waste_organic", {}).get("kg_factor", DEFAULT_FACTORS["organic_waste"])),
        "plastic_waste": float(factors_data.get("waste_plastic", {}).get("kg_factor", DEFAULT_FACTORS["plastic_waste"])),
        "paper_waste": float(factors_data.get("waste_paper", {}).get("kg_factor", DEFAULT_FACTORS["paper_waste"])),
    }


def calc_electricity_emissions(kwh: float, factor: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate electricity emissions:
    electricity emissions = kWh × electricity emission factor
    """
    kwh = max(0.0, float(kwh))
    if factor is None:
        factor = get_factors_map()["electricity"]
    
    emissions = round(kwh * factor, 2)
    return {
        "kwh": kwh,
        "emission_factor": factor,
        "emissions_kg_co2e": emissions,
        "unit": "kg CO2e"
    }


def calc_transport_emissions(
    cars: int,
    car_distance: float,
    motorcycles: int,
    motorcycle_distance: float,
    bus_fuel: float,
    factors: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate transportation emissions from cars, motorcycles, and campus buses.
    """
    cars = max(0, int(cars))
    car_distance = max(0.0, float(car_distance))
    motorcycles = max(0, int(motorcycles))
    motorcycle_distance = max(0.0, float(motorcycle_distance))
    bus_fuel = max(0.0, float(bus_fuel))

    f = factors or get_factors_map()
    car_factor = f.get("car", DEFAULT_FACTORS["car"])
    motorcycle_factor = f.get("motorcycle", DEFAULT_FACTORS["motorcycle"])
    bus_factor = f.get("bus_fuel", DEFAULT_FACTORS["bus_fuel"])

    cars_co2e = round(cars * car_distance * car_factor, 2)
    motorcycles_co2e = round(motorcycles * motorcycle_distance * motorcycle_factor, 2)
    bus_co2e = round(bus_fuel * bus_factor, 2)
    total_transport_co2e = round(cars_co2e + motorcycles_co2e + bus_co2e, 2)

    return {
        "cars": {
            "count": cars,
            "avg_distance_km": car_distance,
            "factor": car_factor,
            "emissions_kg_co2e": cars_co2e
        },
        "motorcycles": {
            "count": motorcycles,
            "avg_distance_km": motorcycle_distance,
            "factor": motorcycle_factor,
            "emissions_kg_co2e": motorcycles_co2e
        },
        "buses": {
            "fuel_liters": bus_fuel,
            "factor": bus_factor,
            "emissions_kg_co2e": bus_co2e
        },
        "emissions_kg_co2e": total_transport_co2e,
        "unit": "kg CO2e"
    }


def calc_waste_emissions(
    organic_waste: float,
    plastic_waste: float,
    paper_waste: float,
    factors: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate estimated waste-related emissions for organic, plastic, and paper waste.
    """
    organic = max(0.0, float(organic_waste))
    plastic = max(0.0, float(plastic_waste))
    paper = max(0.0, float(paper_waste))

    f = factors or get_factors_map()
    org_factor = f.get("organic_waste", DEFAULT_FACTORS["organic_waste"])
    plas_factor = f.get("plastic_waste", DEFAULT_FACTORS["plastic_waste"])
    pap_factor = f.get("paper_waste", DEFAULT_FACTORS["paper_waste"])

    organic_co2e = round(organic * org_factor, 2)
    plastic_co2e = round(plastic * plas_factor, 2)
    paper_co2e = round(paper * pap_factor, 2)
    total_waste_co2e = round(organic_co2e + plastic_co2e + paper_co2e, 2)

    return {
        "organic": {
            "kg": organic,
            "factor": org_factor,
            "emissions_kg_co2e": organic_co2e
        },
        "plastic": {
            "kg": plastic,
            "factor": plas_factor,
            "emissions_kg_co2e": plastic_co2e
        },
        "paper": {
            "kg": paper,
            "factor": pap_factor,
            "emissions_kg_co2e": paper_co2e
        },
        "emissions_kg_co2e": total_waste_co2e,
        "unit": "kg CO2e"
    }


def calc_total_footprint(
    electricity: float,
    transportation: float,
    waste: float
) -> Dict[str, Any]:
    """
    Calculate combined total footprint, percentage contributions, and identify largest emitter.
    """
    elec = round(max(0.0, float(electricity)), 2)
    trans = round(max(0.0, float(transportation)), 2)
    wst = round(max(0.0, float(waste)), 2)
    total = round(elec + trans + wst, 2)

    if total > 0:
        pct_elec = round((elec / total) * 100.0, 1)
        pct_trans = round((trans / total) * 100.0, 1)
        pct_wst = round((wst / total) * 100.0, 1)
    else:
        pct_elec = 0.0
        pct_trans = 0.0
        pct_wst = 0.0

    sources = [
        ("Electricity", elec),
        ("Transportation", trans),
        ("Waste", wst)
    ]
    largest_source = max(sources, key=lambda s: s[1])[0] if total > 0 else "None"

    return {
        "total_emissions_kg_co2e": total,
        "electricity_emissions_kg_co2e": elec,
        "transportation_emissions_kg_co2e": trans,
        "waste_emissions_kg_co2e": wst,
        "percentage_contributions": {
            "electricity": pct_elec,
            "transportation": pct_trans,
            "waste": pct_wst
        },
        "largest_emission_source": largest_source,
        "unit": "kg CO2e",
        "disclaimer": "Carbon footprint values are estimates. Actual emissions depend on regional emission factors, data quality, and accounting methodology."
    }
