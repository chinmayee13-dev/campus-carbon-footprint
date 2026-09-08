"""
Tool 7 / Section 6 — What-If Tool
Function: simulate_reduction(category, reduction_percentage)
Simulate estimated footprint reduction from percentage reductions in electricity, transportation, or waste.
"""

from typing import Dict, Any, Optional
from backend.database.repository import get_latest_record


def simulate_reduction(
    category: str,
    reduction_percentage: float,
    current_electricity: Optional[float] = None,
    current_transportation: Optional[float] = None,
    current_waste: Optional[float] = None
) -> Dict[str, Any]:
    """
    Simulate the carbon impact of reducing a specific category (or all categories) by a target percentage.
    All calculations are deterministic and clearly flagged as estimates.
    """
    cat_clean = category.strip().lower()
    try:
        pct = float(reduction_percentage)
    except (ValueError, TypeError):
        return {"error": f"Invalid reduction percentage: {reduction_percentage}"}

    # Normalize percentage to 0 - 100
    if pct < 0:
        pct = 0.0
    elif pct > 100:
        pct = 100.0

    # Retrieve base emissions if not directly provided
    if current_electricity is None or current_transportation is None or current_waste is None:
        latest = get_latest_record()
        if latest:
            current_electricity = float(latest["electricity_emissions"])
            current_transportation = float(latest["transportation_emissions"])
            current_waste = float(latest["waste_emissions"])
        else:
            current_electricity = 20000.0
            current_transportation = 4000.0
            current_waste = 2000.0

    current_total = round(current_electricity + current_transportation + current_waste, 2)

    new_elec = current_electricity
    new_trans = current_transportation
    new_waste = current_waste

    if "elec" in cat_clean or "power" in cat_clean or "energy" in cat_clean:
        target_category = "Electricity"
        new_elec = round(current_electricity * (1.0 - pct / 100.0), 2)
    elif "trans" in cat_clean or "car" in cat_clean or "vehicle" in cat_clean or "commute" in cat_clean:
        target_category = "Transportation"
        new_trans = round(current_transportation * (1.0 - pct / 100.0), 2)
    elif "waste" in cat_clean or "trash" in cat_clean or "recycle" in cat_clean:
        target_category = "Waste"
        new_waste = round(current_waste * (1.0 - pct / 100.0), 2)
    elif "all" in cat_clean or "total" in cat_clean or "overall" in cat_clean:
        target_category = "All Categories"
        new_elec = round(current_electricity * (1.0 - pct / 100.0), 2)
        new_trans = round(current_transportation * (1.0 - pct / 100.0), 2)
        new_waste = round(current_waste * (1.0 - pct / 100.0), 2)
    else:
        # Default to electricity if unspecified
        target_category = "Electricity"
        new_elec = round(current_electricity * (1.0 - pct / 100.0), 2)

    new_total = round(new_elec + new_trans + new_waste, 2)
    estimated_reduction = round(current_total - new_total, 2)
    pct_total_reduction = round((estimated_reduction / current_total) * 100.0, 1) if current_total > 0 else 0.0

    return {
        "tool": "simulate_reduction",
        "category": target_category,
        "reduction_percentage": pct,
        "baseline": {
            "electricity_kg_co2e": current_electricity,
            "transportation_kg_co2e": current_transportation,
            "waste_kg_co2e": current_waste,
            "total_footprint_kg_co2e": current_total
        },
        "simulation": {
            "new_electricity_kg_co2e": new_elec,
            "new_transportation_kg_co2e": new_trans,
            "new_waste_kg_co2e": new_waste,
            "estimated_new_footprint_kg_co2e": new_total,
            "estimated_monthly_reduction_kg_co2e": estimated_reduction,
            "total_footprint_percentage_reduction": pct_total_reduction
        },
        "formatted_summary": (
            f"Current footprint: {current_total:,.1f} kg CO2e/month\n"
            f"{target_category} reduction: {pct}%\n"
            f"Estimated new footprint: {new_total:,.1f} kg CO2e/month\n"
            f"Estimated reduction: {estimated_reduction:,.1f} kg CO2e/month "
            f"({pct_total_reduction}% overall decrease)"
        ),
        "disclaimer": "SIMULATION ESTIMATE: Carbon footprint values are estimates. Actual emissions depend on regional emission factors, operational changes, and accounting methodology.",
        "status": "success"
    }
