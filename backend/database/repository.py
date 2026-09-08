"""
Repository for database access operations.
"""

from typing import List, Dict, Any, Optional
from backend.database.db import get_connection
from backend.calculations.emission_calc import (
    calc_electricity_emissions,
    calc_transport_emissions,
    calc_waste_emissions,
    calc_total_footprint
)


def row_to_dict(row) -> Dict[str, Any]:
    """Convert SQLite Row to dictionary with formatted numeric types."""
    if row is None:
        return {}
    d = dict(row)
    # Ensure rounded floats
    for k in ["electricity_kwh", "car_distance", "motorcycle_distance", "bus_fuel",
              "organic_waste", "plastic_waste", "paper_waste",
              "electricity_emissions", "transportation_emissions", "waste_emissions", "total_emissions"]:
        if k in d and d[k] is not None:
            d[k] = round(float(d[k]), 2)
    return d


def get_all_records(sort_asc: bool = True) -> List[Dict[str, Any]]:
    """Retrieve all monthly carbon footprint records ordered by month."""
    conn = get_connection()
    cursor = conn.cursor()
    order = "ASC" if sort_asc else "DESC"
    cursor.execute(f"SELECT * FROM monthly_footprints ORDER BY month {order}")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_recent_records(months: int = 6) -> List[Dict[str, Any]]:
    """Retrieve the most recent N records, ordered chronologically (oldest to newest)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM monthly_footprints ORDER BY month DESC LIMIT ?",
        (max(1, months),)
    )
    rows = cursor.fetchall()
    conn.close()
    # Reverse to return chronological order
    return [row_to_dict(r) for r in reversed(rows)]


def get_record_by_month(month: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single month's record by YYYY-MM string."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monthly_footprints WHERE month = ?", (month.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def get_latest_record() -> Optional[Dict[str, Any]]:
    """Retrieve the most recent month's record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monthly_footprints ORDER BY month DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def get_previous_record(month: str) -> Optional[Dict[str, Any]]:
    """Retrieve the record immediately preceding the given month."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM monthly_footprints WHERE month < ? ORDER BY month DESC LIMIT 1",
        (month.strip(),)
    )
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def save_or_update_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate emissions and save or update a monthly record in SQLite.
    Returns the saved record dictionary.
    """
    month = data["month"].strip()
    kwh = float(data.get("electricity_kwh", 0))
    cars = int(data.get("cars", 0))
    car_dist = float(data.get("car_distance", 0))
    motos = int(data.get("motorcycles", 0))
    moto_dist = float(data.get("motorcycle_distance", 0))
    bus_fuel = float(data.get("bus_fuel", 0))
    org_waste = float(data.get("organic_waste", 0))
    plas_waste = float(data.get("plastic_waste", 0))
    pap_waste = float(data.get("paper_waste", 0))

    # Calculate emissions deterministically
    elec_res = calc_electricity_emissions(kwh)
    trans_res = calc_transport_emissions(cars, car_dist, motos, moto_dist, bus_fuel)
    waste_res = calc_waste_emissions(org_waste, plas_waste, pap_waste)
    total_res = calc_total_footprint(
        elec_res["emissions_kg_co2e"],
        trans_res["emissions_kg_co2e"],
        waste_res["emissions_kg_co2e"]
    )

    elec_co2e = elec_res["emissions_kg_co2e"]
    trans_co2e = trans_res["emissions_kg_co2e"]
    waste_co2e = waste_res["emissions_kg_co2e"]
    total_co2e = total_res["total_emissions_kg_co2e"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO monthly_footprints (
        month,
        electricity_kwh,
        cars,
        car_distance,
        motorcycles,
        motorcycle_distance,
        bus_fuel,
        organic_waste,
        plastic_waste,
        paper_waste,
        electricity_emissions,
        transportation_emissions,
        waste_emissions,
        total_emissions
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        month, kwh, cars, car_dist, motos, moto_dist, bus_fuel,
        org_waste, plas_waste, pap_waste,
        elec_co2e, trans_co2e, waste_co2e, total_co2e
    ))
    conn.commit()
    conn.close()

    return get_record_by_month(month)
