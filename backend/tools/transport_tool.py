"""
Tool 2: Transportation Calculator
Function: calculate_transport_emissions(cars, car_distance, motorcycles, motorcycle_distance, bus_fuel)
"""

from typing import Dict, Any
from backend.calculations.emission_calc import calc_transport_emissions


def calculate_transport_emissions(
    cars: int,
    car_distance: float,
    motorcycles: int,
    motorcycle_distance: float,
    bus_fuel: float
) -> Dict[str, Any]:
    """
    Calculate estimated transportation emissions from cars, motorcycles, and campus buses.
    """
    try:
        c = int(cars)
        cd = float(car_distance)
        m = int(motorcycles)
        md = float(motorcycle_distance)
        bf = float(bus_fuel)
    except (ValueError, TypeError) as e:
        return {"error": f"Invalid transportation parameter: {e}"}

    result = calc_transport_emissions(c, cd, m, md, bf)
    return {
        "tool": "calculate_transport_emissions",
        "breakdown": result,
        "transportation_emissions_kg_co2e": result["emissions_kg_co2e"],
        "unit": "kg CO2e",
        "status": "success"
    }
