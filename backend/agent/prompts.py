"""
Prompts and tool schema specifications for the Campus Carbon Management Agent.
"""

SYSTEM_PROMPT = """You are the official Campus Carbon Management AI Agent for a college university campus.
Your mission is to help college and campus administrators monitor, analyze, understand, and reduce the campus carbon footprint.

CRITICAL INSTRUCTIONS & RULES:
1. DETERMINISTIC CALCULATIONS ONLY: NEVER invent, hallucinate, or approximate numerical carbon calculations yourself. You MUST ALWAYS call the appropriate calculation tool to compute emissions, totals, percentages, historical trends, or what-if scenario reductions.
2. REASON OVER TOOL RESULTS: After executing tools, clearly interpret the real numerical results. Highlight the largest emission sources, quantify month-over-month shifts, and explain the physical campus drivers (e.g. winter HVAC heating, commuter patterns, cafeteria food waste).
3. ACTIONABLE RECOMMENDATIONS: Provide prioritized, realistic sustainability interventions suited for a college campus environment (e.g., HVAC setback schedules, LED retrofit, student transit subsidies, dining hall waste segregation).
4. CLEAR COMMUNICATION: Use concise markdown tables, bullet points, and highlight metrics with units (kg CO2e or MT CO2e).
5. MANDATORY ESTIMATE DISCLAIMER: Remind administrators that all carbon footprint values are estimates based on regional emission factors (EPA eGRID, DEFRA, GHG Protocol).
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_electricity_emissions",
            "description": "Calculate estimated CO2e emissions from campus electricity consumption (kWh) using standard regional grid emission factors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kwh": {
                        "type": "number",
                        "description": "Electricity consumed in kilowatt-hours (kWh)"
                    }
                },
                "required": ["kwh"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_transport_emissions",
            "description": "Calculate estimated transportation emissions from commuter cars, motorcycles, and campus diesel shuttle buses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cars": {"type": "integer", "description": "Number of commuter passenger cars"},
                    "car_distance": {"type": "number", "description": "Average daily or monthly commute distance per car in km"},
                    "motorcycles": {"type": "integer", "description": "Number of commuter motorcycles/scooters"},
                    "motorcycle_distance": {"type": "number", "description": "Average commute distance per motorcycle in km"},
                    "bus_fuel": {"type": "number", "description": "Liters of diesel fuel consumed by campus transit buses"}
                },
                "required": ["cars", "car_distance", "motorcycles", "motorcycle_distance", "bus_fuel"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_waste_emissions",
            "description": "Calculate estimated greenhouse gas emissions from campus organic, plastic, and paper waste.",
            "parameters": {
                "type": "object",
                "properties": {
                    "organic_waste": {"type": "number", "description": "Weight of organic/food waste in kilograms (kg)"},
                    "plastic_waste": {"type": "number", "description": "Weight of plastic waste in kilograms (kg)"},
                    "paper_waste": {"type": "number", "description": "Weight of paper and cardboard waste in kilograms (kg)"}
                },
                "required": ["organic_waste", "plastic_waste", "paper_waste"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_total_footprint",
            "description": "Calculate campus total carbon footprint, category percentage contributions, and identify the single largest emission source.",
            "parameters": {
                "type": "object",
                "properties": {
                    "electricity": {"type": "number", "description": "Electricity emissions in kg CO2e"},
                    "transportation": {"type": "number", "description": "Transportation emissions in kg CO2e"},
                    "waste": {"type": "number", "description": "Waste emissions in kg CO2e"}
                },
                "required": ["electricity", "transportation", "waste"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_historical_data",
            "description": "Retrieve historical campus carbon footprint records and month-over-month comparative analysis from SQLite database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "months": {
                        "type": "integer",
                        "description": "Number of recent months to retrieve (default: 6)"
                    },
                    "specific_month": {
                        "type": "string",
                        "description": "Optional specific month in YYYY-MM format (e.g. '2026-03') or month name"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_reduction_plan",
            "description": "Generate a practical, prioritized sustainability action plan based on the campus's largest emission source and historical data.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_reduction",
            "description": "Perform What-If simulation to estimate carbon footprint reduction if electricity, transportation, or waste consumption is reduced by a target percentage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["electricity", "transportation", "waste", "all"],
                        "description": "Category to simulate reduction on"
                    },
                    "reduction_percentage": {
                        "type": "number",
                        "description": "Percentage reduction (e.g. 15 for 15% reduction)"
                    }
                },
                "required": ["category", "reduction_percentage"]
            }
        }
    }
]
