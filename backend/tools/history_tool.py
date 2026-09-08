"""
Tool 5 — Historical Data Tool
Function: get_historical_data(months)
Retrieve previous campus carbon-footprint records from SQLite with comparison metrics.
"""

from typing import Dict, Any, List, Optional
from backend.database.repository import get_recent_records, get_record_by_month, get_all_records


def get_historical_data(months: int = 6, specific_month: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve previous campus carbon-footprint records from SQLite.
    Computes comparative trends, month-over-month deltas, and category changes.
    """
    if specific_month:
        record = get_record_by_month(specific_month)
        if not record:
            return {
                "tool": "get_historical_data",
                "status": "error",
                "message": f"No record found for month {specific_month}"
            }
        return {
            "tool": "get_historical_data",
            "status": "success",
            "single_month": record
        }

    records = get_recent_records(months=months)
    if not records:
        return {
            "tool": "get_historical_data",
            "status": "empty",
            "records": [],
            "message": "No historical carbon records found."
        }

    # Calculate MoM analysis between the last two recorded months
    mom_analysis = None
    if len(records) >= 2:
        prev = records[-2]
        curr = records[-1]
        diff_total = round(curr["total_emissions"] - prev["total_emissions"], 2)
        pct_change = round((diff_total / prev["total_emissions"]) * 100.0, 2) if prev["total_emissions"] > 0 else 0.0

        diff_elec = round(curr["electricity_emissions"] - prev["electricity_emissions"], 2)
        diff_trans = round(curr["transportation_emissions"] - prev["transportation_emissions"], 2)
        diff_waste = round(curr["waste_emissions"] - prev["waste_emissions"], 2)

        # Identify driver of change
        deltas = [
            ("Electricity", diff_elec),
            ("Transportation", diff_trans),
            ("Waste", diff_waste)
        ]
        primary_driver = max(deltas, key=lambda d: abs(d[1]))

        mom_analysis = {
            "current_month": curr["month"],
            "previous_month": prev["month"],
            "current_total_kg_co2e": curr["total_emissions"],
            "previous_total_kg_co2e": prev["total_emissions"],
            "absolute_change_kg_co2e": diff_total,
            "percentage_change": pct_change,
            "trend": "increased" if diff_total > 0 else ("decreased" if diff_total < 0 else "steady"),
            "category_changes": {
                "electricity_delta": diff_elec,
                "transportation_delta": diff_trans,
                "waste_delta": diff_waste
            },
            "primary_driver": {
                "category": primary_driver[0],
                "delta_kg_co2e": primary_driver[1]
            }
        }

    return {
        "tool": "get_historical_data",
        "record_count": len(records),
        "records": records,
        "mom_analysis": mom_analysis,
        "status": "success"
    }
