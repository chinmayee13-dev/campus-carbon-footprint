#  Campus Carbon Footprint Calculator

An AI-powered, autonomous carbon accounting, analytics, and reduction planning system tailored for college and university campus administrators.

The system goes far beyond a static carbon calculator: the AI agent understands natural-language requests, decides which deterministic tools it needs, invokes real backend functions, evaluates stored 6-month historical baselines in SQLite, identifies key emission drivers, runs What-If scenario simulations, and outputs prioritized, data-driven sustainability action plans.

---

##  Core Features

-  **Autonomous AI Tool Calling**: The agent determines and executes real backend Python tools (`calculate_electricity_emissions`, `calculate_transport_emissions`, `calculate_waste_emissions`, `calculate_total_footprint`, `get_historical_data`, `generate_reduction_plan`, `simulate_reduction`).
-  **Deterministic Calculation Integrity**: Carbon math is never left to LLM hallucination. Pure deterministic formulas convert activity data using validated emission factors from US EPA eGRID, UK DEFRA, and GHG Protocol.
-  **Zero-Crash Fallback Mode**: Works completely offline or without an API key. If no LLM key is configured, an intelligent semantic intent classifier triggers the identical real Python tools and provides structured analysis.
-  **Executive Administrator Dashboard**:
  - Current vs. Previous Month CO₂e & Month-over-Month % delta.
  - Largest emission source detection and scope percentage breakdowns.
  - 6-month historical stacked scope emissions trajectory chart (Chart.js).
  - Category share doughnut chart.
  - Prioritized sustainability interventions with estimated impact and timelines.
-  **What-If Scenario Sandbox**: Interactive simulation sliders allowing administrators to model reductions (e.g. *-20% electricity*, *-15% commuter traffic*) and view real-time avoided greenhouse gas calculations.
-  **Monthly Activity Logger**: Easy modal form to log monthly kWh, commuter cars/motorcycles, shuttle diesel, and waste weights with instant live calculations before saving to SQLite.
-  **Official Conversion Factors Reference**: Complete transparency into emission factors, regulatory units, and citations.

---

## 🏗️ Architecture & Project Structure

```
campus-carbon-agent/
│
├── frontend/                     # Modern eco-slate responsive web UI
│   ├── css/
│   │   └── style.css            # Dark/emerald design system & micro-animations
│   ├── js/
│   │   ├── api.js               # REST client for agent & calculations
│   │   ├── dashboard.js         # Chart.js visualizations & KPI renderers
│   │   ├── chat.js              # Chat interface & tool execution audit trace
│   │   └── data-entry.js        # Live calculation preview & modal manager
│   └── index.html               # Main single-page application
│
├── backend/                      # Python FastAPI application
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py             # Agent orchestrator & intent fallback engine
│   │   └── prompts.py           # System instructions & tool schemas
│   ├── tools/                   # The 7 Real Registered Agent Tools
│   │   ├── electricity_tool.py  # calculate_electricity_emissions(kwh)
│   │   ├── transport_tool.py    # calculate_transport_emissions(...)
│   │   ├── waste_tool.py        # calculate_waste_emissions(...)
│   │   ├── total_tool.py        # calculate_total_footprint(...)
│   │   ├── history_tool.py      # get_historical_data(months)
│   │   ├── recommendation_tool.py # generate_reduction_plan(...)
│   │   └── whatif_tool.py       # simulate_reduction(category, percentage)
│   ├── calculations/
│   │   ├── __init__.py
│   │   └── emission_calc.py     # Pure deterministic formulas
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                # SQLite connection & 6-month auto-seeding
│   │   └── repository.py        # Database CRUD operations
│   └── main.py                  # FastAPI server, REST routes & static mount
│
├── data/
│   ├── emission_factors.json    # Standard emission factors & EPA/DEFRA citations
│   └── seed_data.json           # 6 months of realistic campus activity records
│
├── .env.example                 # Environment configuration template
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation & setup guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### 1. Installation

Clone or navigate into the project directory:
```bash
cd "campus-carbon-agent"
```

Install the lightweight Python dependencies:
```bash
py -m pip install -r requirements.txt
# OR on Linux/macOS:
pip install -r requirements.txt
```

### 2. Configuration (OpenAI API Key)

The backend loads your API key securely from `backend/.env` using `python-dotenv`.

1. Check or create `backend/.env`:
   ```bash
   # In backend/.env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```
   A template is provided in `backend/.env.example`:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Security Guarantee:
   - `backend/.env` and `.env` are excluded by `.gitignore` so your key is never committed to git.
   - The API key is loaded strictly into backend memory and is **never** sent to the client/browser.
   - If the API key is missing or encounters a quota issue, the backend prints a clear message and seamlessly uses local deterministic calculations so the application never crashes.

### 3. Launch the Backend Server

Start the FastAPI server:
```bash
py -m uvicorn backend.main:app --reload --port 8000
# OR on Linux/macOS:
uvicorn backend.main:app --reload --port 8000
```

Open your browser at:
```
http://127.0.0.1:8000
```

The database `campus_carbon.db` will automatically initialize and pre-populate with 6 months of historical campus data on the first run.

---

##  The 7 Agent Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `calculate_electricity_emissions` | `kwh: float` | Computes electricity CO₂e ($kWh \times factor$). |
| `calculate_transport_emissions` | `cars, car_dist, motos, moto_dist, bus_fuel` | Computes commuter vehicle and shuttle fuel emissions. |
| `calculate_waste_emissions` | `organic, plastic, paper` | Computes landfill and disposal GHG impact. |
| `calculate_total_footprint` | `elec, trans, waste` | Computes combined total, scope shares (%), and largest emitter. |
| `get_historical_data` | `months: int = 6, specific_month = None` | Queries SQLite records, computes MoM changes and delta drivers. |
| `generate_reduction_plan` | `carbon_breakdown, historical_data` | Produces prioritized sustainability interventions (HVAC, solar, transit, composting). |
| `simulate_reduction` | `category: str, reduction_percentage: float` | Models What-If scenarios with avoided CO₂e and new totals. |

---

##  Sample Inquiries to Ask the Agent

Try asking the agent in the **Carbon Agent** chat interface:

1. **Calculate Footprint:**
   > *"Calculate this month's footprint."*
2. **Historical Comparison:**
   > *"Why did our emissions increase compared to previous month?"*
3. **Largest Contributor:**
   > *"What is our biggest source of emissions?"*
4. **What-If Simulation:**
   > *"What if electricity consumption decreases by 20%?"*
   > *"What if we reduce commuter car traffic by 15%?"*
5. **Sustainability Action Plan:**
   > *"How can we reduce our emissions?"*
   > *"Give me a sustainability action plan."*

---

##  Emission Factors Reference

All calculations use verified baseline coefficients:

| Category | Emission Factor | Unit | Source |
| :--- | :--- | :--- | :--- |
| **Grid Electricity** | `0.385` | kg CO₂e / kWh | US EPA eGRID Subregion Average |
| **Passenger Cars** | `0.171` | kg CO₂e / km | UK DEFRA / US EPA GHGRP |
| **Motorcycles / Scooters** | `0.103` | kg CO₂e / km | UK DEFRA GHG Conversion Factors |
| **Campus Bus Diesel** | `2.680` | kg CO₂e / liter | GHG Protocol Cross-Sector Fuel Tools |
| **Organic Food Waste** | `0.450` | kg CO₂e / kg | US EPA WARM v15 (Food Waste Landfill) |
| **Mixed Plastics** | `2.100` | kg CO₂e / kg | US EPA WARM v15 (Plastics Lifecycle) |
| **Paper & Cardboard** | `0.950` | kg CO₂e / kg | US EPA WARM v15 (Mixed Paper) |

*Disclaimer: Carbon footprint values are estimates. Actual emissions depend on regional emission factors, data quality, and accounting methodology.*

---

##  Running Verification Tests

Run the included automated test suite to verify tool accuracy and deterministic calculations:
```bash
py test_backend.py
```

---

## 🚢Production Deployment

To run in a production environment:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or deploy via Docker container:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
