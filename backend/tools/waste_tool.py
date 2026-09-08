"""
Tool 3: Waste Calculator
Function: calculate_waste_emissions(organic_waste, plastic_waste, paper_waste)
"""

from typing import Dict, Any
from backend.calculations.emission_calc import calc_waste_emissions


def calculate_waste_emissions(
    organic_waste: float,
    plastic_waste: float,
    paper_waste: float
) -> Dict[str, Any]:
    """
    Calculate estimated waste-related emissions for organic, plastic, and paper waste.
    """
    try:
        org = float(organic_waste)
        pla = float(plastic_waste)
        pap = float(paper_waste)
    except (ValueError, TypeError) as e:
        return {"error": f"Invalid waste parameter: {e}"}

    result = calc_waste_emissions(org, pla, pap)
    return {
        "tool": "calculate_waste_emissions",
        "breakdown": result,
        "waste_emissions_kg_co2e": result["emissions_kg_co2e"],
        "unit": "kg CO2e",
        "status": "success"
    }
