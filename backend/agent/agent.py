"""
Campus Carbon Management AI Agent.
Coordinates autonomous OpenAI tool calling, deterministic calculation execution,
and intelligent fallback reasoning when no API key is present or when API quota is exhausted.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

import openai
from openai import OpenAI

from backend.agent.prompts import SYSTEM_PROMPT, TOOL_SCHEMAS
from backend.tools.electricity_tool import calculate_electricity_emissions
from backend.tools.transport_tool import calculate_transport_emissions
from backend.tools.waste_tool import calculate_waste_emissions
from backend.tools.total_tool import calculate_total_footprint
from backend.tools.history_tool import get_historical_data
from backend.tools.recommendation_tool import generate_reduction_plan
from backend.tools.whatif_tool import simulate_reduction
from backend.database.repository import get_latest_record, get_all_records, get_record_by_month

# Load environment variables securely from backend/.env first, then root .env
BACKEND_DIR = Path(__file__).resolve().parent.parent
BACKEND_ENV = BACKEND_DIR / ".env"
ROOT_ENV = BACKEND_DIR.parent / ".env"

if BACKEND_ENV.exists():
    load_dotenv(dotenv_path=BACKEND_ENV, override=True)
elif ROOT_ENV.exists():
    load_dotenv(dotenv_path=ROOT_ENV)
else:
    load_dotenv()

# Real Tool Registry - Maps function names to Python callables
TOOL_REGISTRY = {
    "calculate_electricity_emissions": calculate_electricity_emissions,
    "calculate_transport_emissions": calculate_transport_emissions,
    "calculate_waste_emissions": calculate_waste_emissions,
    "calculate_total_footprint": calculate_total_footprint,
    "get_historical_data": get_historical_data,
    "generate_reduction_plan": generate_reduction_plan,
    "simulate_reduction": simulate_reduction,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a real registered tool deterministically and log the trace."""
    tool_fn = TOOL_REGISTRY.get(tool_name)
    if not tool_fn:
        return {"error": f"Tool '{tool_name}' not found in registry."}

    try:
        if tool_name == "generate_reduction_plan" and not arguments:
            return tool_fn()
        return tool_fn(**arguments)
    except Exception as e:
        return {"error": f"Tool execution error: {str(e)}"}


class CarbonAgent:
    """
    Campus Carbon Management Agent.
    Handles user intent understanding, tool selection, real execution, and reasoning.
    Initializes OpenAI client securely from environment variables.
    """

    def __init__(self):
        self._load_config()

    def _load_config(self):
        """Reload configuration from environment variables."""
        if BACKEND_ENV.exists():
            load_dotenv(dotenv_path=BACKEND_ENV, override=True)
        elif ROOT_ENV.exists():
            load_dotenv(dotenv_path=ROOT_ENV)

        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

        # Initialize OpenAI client if key is configured
        self.client: Optional[OpenAI] = None
        if self.openai_key:
            try:
                self.client = OpenAI(api_key=self.openai_key, max_retries=1)
            except Exception as e:
                print(f"[Backend Warning] Failed to initialize OpenAI client: {e}")
                self.client = None

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Check active AI provider or fallback status.
        NEVER expose the raw API key to the frontend.
        """
        self._load_config()
        has_key = bool(self.openai_key and self.client is not None)

        if has_key:
            return {
                "active_mode": "llm_openai",
                "provider_name": "OpenAI",
                "model": self.openai_model,
                "is_fallback": False,
                "has_api_key": True,
                "message": f"AI Provider: OpenAI ({self.openai_model}) active with autonomous tool calling."
            }
        else:
            return {
                "active_mode": "fallback_rule_based",
                "provider_name": "Deterministic Fallback Agent",
                "model": "Rule-Based Intent Classifier & Real Tool Execution Engine",
                "is_fallback": True,
                "has_api_key": False,
                "message": "OPENAI_API_KEY not configured. Running in local Fallback Mode with deterministic tool calling."
            }

    async def process_message(self, user_prompt: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Main reasoning entry point:
        1. Receive user query.
        2. If OpenAI client is initialized, attempt OpenAI tool-calling chat completions.
        3. If key is missing or OpenAI API call fails (e.g. quota exhausted or invalid key),
           seamlessly fall back to deterministic tool calling without crashing.
        4. Return answer + real tool execution audit trace.
        """
        self._load_config()

        if self.client:
            try:
                return self._call_openai_agent(user_prompt, chat_history)
            except openai.AuthenticationError as e:
                print(f"[Backend Error] OpenAI Authentication Failed: {e}")
                fallback = self._run_fallback_agent(user_prompt)
                fallback["response"] = (
                    "> ⚠️ **Notice**: OpenAI Authentication Failed (Invalid API Key). "
                    "The agent seamlessly executed local deterministic tools to compute this response.\n\n"
                    + fallback["response"]
                )
                return fallback
            except openai.RateLimitError as e:
                print(f"[Backend Error] OpenAI Quota/Rate Limit: {e}")
                fallback = self._run_fallback_agent(user_prompt)
                fallback["response"] = (
                    "> ⚠️ **Notice**: OpenAI API Quota Exceeded (No remaining credits on your OpenAI account). "
                    "The agent seamlessly switched to local deterministic tool execution so all campus carbon calculations remain 100% functional.\n\n"
                    + fallback["response"]
                )
                return fallback
            except Exception as e:
                print(f"[Backend Error] OpenAI Call Exception: {e}")
                fallback = self._run_fallback_agent(user_prompt)
                fallback["response"] = (
                    f"> ⚠️ **Notice**: OpenAI API call failed ({type(e).__name__}). "
                    "Running in deterministic Fallback Mode.\n\n"
                    + fallback["response"]
                )
                return fallback

        # Fallback Engine (No API key provided)
        print("[Backend Info] OPENAI_API_KEY is not configured. Running in Fallback Mode.")
        return self._run_fallback_agent(user_prompt)

    def _call_openai_agent(self, prompt: str, chat_history: Optional[List[Dict[str, str]]]) -> Dict[str, Any]:
        """
        Execute OpenAI chat completion with function/tool calling.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        tool_trace: List[Dict[str, Any]] = []

        # Turn 1: Send request to OpenAI with registered tool schemas
        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Append assistant's tool calling response to conversation
            messages.append(response_message)

            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except Exception:
                    fn_args = {}

                # Execute the real Python tool deterministically
                tool_result = execute_tool(fn_name, fn_args)
                tool_trace.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": tool_result
                })

                # Append tool result message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result)
                })

            # Turn 2: Follow-up completion to reason over real tool outputs
            followup_response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=messages
            )
            final_text = followup_response.choices[0].message.content or ""
        else:
            final_text = response_message.content or ""

        return {
            "response": final_text,
            "tool_calls": tool_trace,
            "mode": "llm_openai"
        }

    def _run_fallback_agent(self, prompt: str) -> Dict[str, Any]:
        """
        Deterministic Rule-Based Tool Calling Agent:
        Identifies required tools, executes them against SQLite and calculation modules,
        and generates comprehensive analytical responses.
        """
        p_lower = prompt.lower().strip()
        tool_trace = []

        # 1. WHAT-IF / SIMULATION INTENT
        if any(w in p_lower for w in ["what if", "simulate", "decrease by", "reduce by", "if we reduce", "if electricity"]):
            pct_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", p_lower)
            percentage = float(pct_match.group(1)) if pct_match else 15.0

            category = "electricity"
            if "trans" in p_lower or "car" in p_lower or "vehicle" in p_lower or "commute" in p_lower:
                category = "transportation"
            elif "waste" in p_lower or "trash" in p_lower or "plastic" in p_lower or "paper" in p_lower:
                category = "waste"
            elif "all" in p_lower or "total" in p_lower or "campus" in p_lower:
                category = "all"

            sim_args = {"category": category, "reduction_percentage": percentage}
            sim_result = execute_tool("simulate_reduction", sim_args)
            tool_trace.append({
                "tool": "simulate_reduction",
                "arguments": sim_args,
                "result": sim_result
            })

            baseline = sim_result["baseline"]
            sim = sim_result["simulation"]

            response_text = (
                f"### 🔬 What-If Scenario Analysis: {category.title()} -{percentage}%\n\n"
                f"I simulated the carbon impact of achieving a **{percentage}% reduction** in campus **{category}** emissions:\n\n"
                f"| Metric | Baseline | Simulated Scenario | Net Change |\n"
                f"| :--- | :--- | :--- | :--- |\n"
                f"| **{category.title()} Emissions** | {baseline.get(category + '_kg_co2e', baseline['electricity_kg_co2e']):,.1f} kg CO₂e | {sim.get('new_' + category + '_kg_co2e', sim['new_electricity_kg_co2e']):,.1f} kg CO₂e | -{sim['estimated_monthly_reduction_kg_co2e']:,.1f} kg CO₂e |\n"
                f"| **Total Campus Footprint** | **{baseline['total_footprint_kg_co2e']:,.1f} kg CO₂e** | **{sim['estimated_new_footprint_kg_co2e']:,.1f} kg CO₂e** | **-{sim['total_footprint_percentage_reduction']}%** |\n\n"
                f"**Key Takeaways:**\n"
                f"- Reducing {category} by {percentage}% yields an estimated **{sim['estimated_monthly_reduction_kg_co2e']:,.1f} kg CO₂e monthly reduction** (≈ {round(sim['estimated_monthly_reduction_kg_co2e'] * 12 / 1000, 2)} metric tonnes CO₂e/year).\n"
                f"- This single initiative lowers the campus's overall greenhouse gas profile by **{sim['total_footprint_percentage_reduction']}%**.\n\n"
                f"> ℹ️ *{sim_result['disclaimer']}*"
            )

            return {
                "response": response_text,
                "tool_calls": tool_trace,
                "mode": "fallback_rule_based",
                "disclaimer": sim_result["disclaimer"]
            }

        # 2. HISTORICAL COMPARISON / TREND / WHY INCREASED INTENT
        elif any(w in p_lower for w in ["why did", "increase", "decrease", "compare", "trend", "history", "last month", "improved", "versus", "vs"]):
            hist_args = {"months": 6}
            hist_result = execute_tool("get_historical_data", hist_args)
            tool_trace.append({
                "tool": "get_historical_data",
                "arguments": hist_args,
                "result": hist_result
            })

            mom = hist_result.get("mom_analysis")
            if not mom:
                return {
                    "response": "Historical data record is currently limited to fewer than 2 months. Please record more campus monthly data to perform comparative trend analysis.",
                    "tool_calls": tool_trace,
                    "mode": "fallback_rule_based"
                }

            curr_m = mom["current_month"]
            prev_m = mom["previous_month"]
            diff = mom["absolute_change_kg_co2e"]
            pct = mom["percentage_change"]
            direction = mom["trend"]
            driver = mom["primary_driver"]

            reasoning = ""
            if direction == "increased":
                reasoning = (
                    f"Our analysis indicates emissions **increased by {abs(pct)}%** (+{diff:,.1f} kg CO₂e) from {prev_m} to {curr_m}. "
                    f"The primary driver of this increase was **{driver['category']}**, which shifted by {driver['delta_kg_co2e']:+,.1f} kg CO₂e. "
                    f"On college campuses, this typically corresponds to seasonal weather demands (heightened HVAC heating/cooling) "
                    f"or intensified in-person campus activities."
                )
            elif direction == "decreased":
                reasoning = (
                    f"Great news: Campus emissions **decreased by {abs(pct)}%** (-{abs(diff):,.1f} kg CO₂e) from {prev_m} to {curr_m}! "
                    f"The largest contributor to this reduction was **{driver['category']}** with a reduction of {abs(driver['delta_kg_co2e']):,.1f} kg CO₂e, "
                    f"reflecting campus conservation measures and schedule adjustments."
                )
            else:
                reasoning = f"Emissions remained stable between {prev_m} and {curr_m} ({curr_m}: {mom['current_total_kg_co2e']:,.1f} kg CO₂e)."

            response_text = (
                f"### 📊 Month-over-Month Historical Analysis ({prev_m} vs. {curr_m})\n\n"
                f"{reasoning}\n\n"
                f"| Category | {prev_m} (kg CO₂e) | {curr_m} (kg CO₂e) | Net Delta |\n"
                f"| :--- | :--- | :--- | :--- |\n"
                f"| **Electricity** | {round(hist_result['records'][-2]['electricity_emissions'], 1):,} | {round(hist_result['records'][-1]['electricity_emissions'], 1):,} | {mom['category_changes']['electricity_delta']:+,.1f} kg CO₂e |\n"
                f"| **Transportation** | {round(hist_result['records'][-2]['transportation_emissions'], 1):,} | {round(hist_result['records'][-1]['transportation_emissions'], 1):,} | {mom['category_changes']['transportation_delta']:+,.1f} kg CO₂e |\n"
                f"| **Waste** | {round(hist_result['records'][-2]['waste_emissions'], 1):,} | {round(hist_result['records'][-1]['waste_emissions'], 1):,} | {mom['category_changes']['waste_delta']:+,.1f} kg CO₂e |\n"
                f"| **Total Footprint** | **{mom['previous_total_kg_co2e']:,}** | **{mom['current_total_kg_co2e']:,}** | **{diff:+,.1f} kg CO₂e ({pct:+}%)** |\n\n"
                f"**Recommended Follow-Up:**\n"
                f"To reverse or accelerate this trend, focus on the primary driver (**{driver['category']}**). "
                f"You can type *'Give me an action plan'* or ask *'What if {driver['category'].lower()} decreases by 15%?'* to model solutions."
            )

            return {
                "response": response_text,
                "tool_calls": tool_trace,
                "mode": "fallback_rule_based"
            }

        # 3. REDUCTION PLAN / SUSTAINABILITY RECOMMENDATIONS INTENT
        elif any(w in p_lower for w in ["reduce", "reduction", "action plan", "recommend", "how can we", "sustainability plan"]):
            plan_result = execute_tool("generate_reduction_plan", {})
            tool_trace.append({
                "tool": "generate_reduction_plan",
                "arguments": {},
                "result": plan_result
            })

            src = plan_result["largest_emission_source"]
            recs = plan_result["recommendations"]

            recs_formatted = []
            for i, r in enumerate(recs, 1):
                badge = "🔴 HIGH" if r["priority"] == "High" else "🟡 MEDIUM"
                recs_formatted.append(
                    f"#### {i}. {r['title']} ({badge} Priority)\n"
                    f"- **Category:** {r['category']} | **Timeframe:** {r['timeframe']}\n"
                    f"- **Projected Impact:** {r['impact_estimate']}\n"
                    f"- **Implementation:** {r['description']}"
                )

            recs_text = "\n\n".join(recs_formatted)

            response_text = (
                f"### 🌱 Campus Carbon Reduction Action Plan\n\n"
                f"**Executive Diagnostic:**\n"
                f"{plan_result['executive_summary']}\n\n"
                f"### 📋 Prioritized Interventions\n\n"
                f"{recs_text}\n\n"
                f"💡 **Next Step:** You can simulate any of these actions by asking: *'What if electricity decreases by 15%?'*"
            )

            return {
                "response": response_text,
                "tool_calls": tool_trace,
                "mode": "fallback_rule_based"
            }

        # 4. BIGGEST SOURCE / BREAKDOWN INTENT
        elif any(w in p_lower for w in ["biggest", "largest", "main source", "contributor", "breakdown", "pie"]):
            latest = get_latest_record()
            if not latest:
                return {
                    "response": "No campus carbon records found. Please enter data for the current month first.",
                    "tool_calls": tool_trace,
                    "mode": "fallback_rule_based"
                }

            total_args = {
                "electricity": latest["electricity_emissions"],
                "transportation": latest["transportation_emissions"],
                "waste": latest["waste_emissions"]
            }
            total_res = execute_tool("calculate_total_footprint", total_args)
            tool_trace.append({
                "tool": "calculate_total_footprint",
                "arguments": total_args,
                "result": total_res
            })

            pcts = total_res["percentage_contributions"]
            largest = total_res["largest_emission_source"]

            response_text = (
                f"### 🏆 Campus Emission Sources Breakdown ({latest['month']})\n\n"
                f"The **largest emission source** for campus operations is **{largest}**, accounting for "
                f"**{pcts.get(largest.lower(), 0)}%** of the campus's total footprint ({total_res[largest.lower() + '_emissions_kg_co2e']:,.1f} kg CO₂e).\n\n"
                f"| Category | Emissions (kg CO₂e) | Share of Footprint |\n"
                f"| :--- | :--- | :--- |\n"
                f"| ⚡ **Electricity** | {total_res['electricity_emissions_kg_co2e']:,.1f} kg CO₂e | {pcts['electricity']}% |\n"
                f"| 🚗 **Transportation** | {total_res['transportation_emissions_kg_co2e']:,.1f} kg CO₂e | {pcts['transportation']}% |\n"
                f"| 🗑️ **Waste** | {total_res['waste_emissions_kg_co2e']:,.1f} kg CO₂e | {pcts['waste']}% |\n"
                f"| **Total** | **{total_res['total_emissions_kg_co2e']:,.1f} kg CO₂e** | **100.0%** |\n\n"
                f"Targeting **{largest}** delivers the greatest return on campus sustainability investments."
            )

            return {
                "response": response_text,
                "tool_calls": tool_trace,
                "mode": "fallback_rule_based"
            }

        # 5. GENERAL CALCULATION / LATEST FOOTPRINT / DEFAULT INTENT
        else:
            latest = get_latest_record()
            if not latest:
                return {
                    "response": "Welcome to the Campus Carbon Management Agent! No records exist yet. Use the 'Enter Campus Data' button to log your first month.",
                    "tool_calls": [],
                    "mode": "fallback_rule_based"
                }

            # Run total calculator tool
            total_args = {
                "electricity": latest["electricity_emissions"],
                "transportation": latest["transportation_emissions"],
                "waste": latest["waste_emissions"]
            }
            total_res = execute_tool("calculate_total_footprint", total_args)
            tool_trace.append({
                "tool": "calculate_total_footprint",
                "arguments": total_args,
                "result": total_res
            })

            # Also pull history for context
            hist_res = execute_tool("get_historical_data", {"months": 2})
            tool_trace.append({
                "tool": "get_historical_data",
                "arguments": {"months": 2},
                "result": hist_res
            })

            pcts = total_res["percentage_contributions"]
            mom = hist_res.get("mom_analysis")
            mom_str = f" ({mom['trend'].title()} by {abs(mom['percentage_change'])}% MoM)" if mom else ""

            response_text = (
                f"### 🏫 Campus Carbon Footprint Summary ({latest['month']})\n\n"
                f"- **Total Monthly Carbon Footprint:** **{total_res['total_emissions_kg_co2e']:,.1f} kg CO₂e**{mom_str}\n"
                f"- **Primary Emitter:** **{total_res['largest_emission_source']}** ({pcts.get(total_res['largest_emission_source'].lower(), 0)}% of total)\n\n"
                f"**Component Breakdown:**\n"
                f"- ⚡ **Electricity:** {total_res['electricity_emissions_kg_co2e']:,.1f} kg CO₂e ({pcts['electricity']}%)\n"
                f"- 🚗 **Transportation:** {total_res['transportation_emissions_kg_co2e']:,.1f} kg CO₂e ({pcts['transportation']}%)\n"
                f"- 🗑️ **Waste:** {total_res['waste_emissions_kg_co2e']:,.1f} kg CO₂e ({pcts['waste']}%)\n\n"
                f"**Suggested Questions You Can Ask Me:**\n"
                f"1. *'Why did our emissions increase compared to previous month?'*\n"
                f"2. *'What if electricity consumption decreases by 20%?'*\n"
                f"3. *'How can we reduce our emissions?'*\n"
                f"4. *'Compare historical trends over the last 6 months.'*"
            )

            return {
                "response": response_text,
                "tool_calls": tool_trace,
                "mode": "fallback_rule_based"
            }
