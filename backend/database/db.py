"""
SQLite database management for campus monthly carbon records.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from backend.calculations.emission_calc import (
    calc_electricity_emissions,
    calc_transport_emissions,
    calc_waste_emissions,
    calc_total_footprint
)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "campus_carbon.db"
SEED_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "seed_data.json"


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection with dictionary-like row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reseed: bool = False) -> None:
    """Initialize database tables and pre-populate with seed data if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthly_footprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT UNIQUE NOT NULL,
        electricity_kwh REAL NOT NULL,
        cars INTEGER NOT NULL,
        car_distance REAL NOT NULL,
        motorcycles INTEGER NOT NULL,
        motorcycle_distance REAL NOT NULL,
        bus_fuel REAL NOT NULL,
        organic_waste REAL NOT NULL,
        plastic_waste REAL NOT NULL,
        paper_waste REAL NOT NULL,
        electricity_emissions REAL NOT NULL,
        transportation_emissions REAL NOT NULL,
        waste_emissions REAL NOT NULL,
        total_emissions REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # Check if empty or forced reseed
    cursor.execute("SELECT COUNT(*) AS count FROM monthly_footprints")
    count = cursor.fetchone()["count"]

    if count == 0 or force_reseed:
        if SEED_FILE.exists():
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                seed_records = json.load(f)

            for item in seed_records:
                # Calculate emissions deterministically
                elec_res = calc_electricity_emissions(item["electricity_kwh"])
                trans_res = calc_transport_emissions(
                    item["cars"], item["car_distance"],
                    item["motorcycles"], item["motorcycle_distance"],
                    item["bus_fuel"]
                )
                waste_res = calc_waste_emissions(
                    item["organic_waste"], item["plastic_waste"], item["paper_waste"]
                )
                total_res = calc_total_footprint(
                    elec_res["emissions_kg_co2e"],
                    trans_res["emissions_kg_co2e"],
                    waste_res["emissions_kg_co2e"]
                )

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
                    item["month"],
                    float(item["electricity_kwh"]),
                    int(item["cars"]),
                    float(item["car_distance"]),
                    int(item["motorcycles"]),
                    float(item["motorcycle_distance"]),
                    float(item["bus_fuel"]),
                    float(item["organic_waste"]),
                    float(item["plastic_waste"]),
                    float(item["paper_waste"]),
                    elec_res["emissions_kg_co2e"],
                    trans_res["emissions_kg_co2e"],
                    waste_res["emissions_kg_co2e"],
                    total_res["total_emissions_kg_co2e"]
                ))
            conn.commit()

    conn.close()
