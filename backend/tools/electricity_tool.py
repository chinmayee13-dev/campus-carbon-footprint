"""
Tool 1: Electricity Calculator
Function: calculate_electricity_emissions(kwh)
"""

from typing import Dict, Any
from backend.calculations.emission_calc import calc_electricity_emissions


def calculate_electricity_emissions(kwh: float) -> Dict[str, Any]:
    """
    Calculate estimated CO2e emissions from campus electricity consumption.
    Formula: electricity emissions = kWh × electricity emission factor
    """
    try:
        val = float(kwh)
    except (ValueError, TypeError):
        return {"error": f"Invalid kWh value: {kwh}"}

    result = calc_electricity_emissions(val)
    return {
        "tool": "calculate_electricity_emissions",
        "input_kwh": result["kwh"],
        "emission_factor": result["emission_factor"],
        "electricity_emissions_kg_co2e": result["emissions_kg_co2e"],
        "unit": "kg CO2e",
        "status": "success"
    }
