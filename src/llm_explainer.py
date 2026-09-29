import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiExplainer:
    def __init__(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_actual_gemini_api_key_here":
            raise ValueError("❌ GEMINI_API_KEY is missing or invalid in your .env file!")
        # Initialize Google GenAI Client
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def explain_anomaly(
        self,
        anomaly_payload: dict,
        metric_definition: dict,
        related_kpis: list = None,
        data_quality_status: dict = None
    ) -> dict:
        """
        Sends structured anomaly context to Gemini API and receives a strictly formatted JSON explanation.
        Includes automatic retry logic and uses valid production models (gemini-3.8-flash, gemini-3.5-flash).
        """
        related_kpis = related_kpis or []
        data_quality_status = data_quality_status or {}

        # Build prompt payload
        prompt_data = {
            "anomaly_detected_by_engine": {
                "metric_name": metric_definition.get("display_name", anomaly_payload.get("metric_name")),
                "unit": metric_definition.get("unit", ""),
                "description": metric_definition.get("description", ""),
                "owner": metric_definition.get("owner", ""),
                "current_value": anomaly_payload.get("current_value"),
                "expected_baseline": anomaly_payload.get("expected_value"),
                "change_percent": anomaly_payload.get("change_percent"),
                "z_score": anomaly_payload.get("z_score"),
                "severity": anomaly_payload.get("severity")
            },
            "related_kpi_signals": related_kpis,
            "data_quality_checks": data_quality_status
        }

        system_instruction = (
            "You are an expert Data Observability AI Analyst. "
            "You DO NOT decide if an anomaly exists — Python has already mathematically flagged it. "
            "Your job is to analyze the provided metric metadata, numerical deviations, and data quality checks to explain the anomaly concisely. "
            "STRICT RULES:\n"
            "1. Do NOT invent facts, imaginary marketing campaigns, or unsupplied external events.\n"
            "2. Rely ONLY on the provided JSON data.\n"
            "3. If the provided data does NOT contain enough context to determine a root cause, you MUST explicitly state in the summary or possible_contributing_signals: 'Cause cannot be determined from the available data.'\n"
            "4. Output MUST be valid JSON matching the schema."
        )

        user_prompt = f"Analyze this anomaly incident and produce an executive explanation in JSON format:\n{json.dumps(prompt_data, indent=2)}"

        # Valid active 2026 production models
        candidate_models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
        last_error = None

        for model_name in candidate_models:
            for attempt in range(1, 4):
                try:
                    # Using chats API to avoid AFC warning and handle high volume cleanly
                    chat = self.client.chats.create(
                        model=model_name,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            temperature=0.2
                        )
                    )
                    response = chat.send_message(user_prompt)
                    return json.loads(response.text)
                except Exception as e:
                    last_error = str(e)
                    if "503" in last_error or "UNAVAILABLE" in last_error or "429" in last_error:
                        print(f"⏳ Server busy on {model_name} (Attempt {attempt}/3). Retrying in {attempt * 3}s...")
                        time.sleep(attempt * 3)
                    else:
                        # Move to next valid model if not a temporary capacity error
                        break

        print(f"⚠️ All Gemini API attempts failed: {last_error}")
        return {
            "summary": f"Automated explanation temporarily unavailable due to Google API server demand.",
            "severity_explanation": f"Metric deviated by {anomaly_payload.get('change_percent')}%",
            "possible_contributing_signals": ["Cause cannot be determined from the available data."],
            "recommended_investigation": ["Check raw database logs manually."],
            "confidence_score": "LOW"
        }