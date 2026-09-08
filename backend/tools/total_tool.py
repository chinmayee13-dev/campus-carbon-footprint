"""
Tool 4 — Total Carbon Calculator
Function: calculate_total_footprint(electricity, transportation, waste)
"""

from typing import Dict, Any
from backend.calculations.emission_calc import calc_total_footprint


def calculate_total_footprint(
    electricity: float,
    transportation: float,
    waste: float
) -> Dict[str, Any]:
    """
    Calculate combined total footprint, percentage contributions, and identify largest emitter.
    """
    try:
        e = float(electricity)
        t = float(transportation)
        w = float(waste)
    except (ValueError, TypeError) as err:
        return {"error": f"Invalid footprint argument: {err}"}

    result = calc_total_footprint(e, t, w)
    return {
        "tool": "calculate_total_footprint",
        **result,
        "status": "success"
    }
