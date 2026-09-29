import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm_explainer import GeminiExplainer
from src.metrics_engine import MetricEngine

def main():
    print("--- 🛠️ TESTING GEMINI AI ANOMALY EXPLANATION ENGINE ---")
    
    # Initialize Engine & Explainer
    metric_engine = MetricEngine()
    explainer = GeminiExplainer()
    
    # Simulate an anomaly payload (e.g., Refund Rate Spike anomaly)
    refund_metric_def = metric_engine.get_metric_definition("refund_rate")
    
    simulated_anomaly = {
        "metric_name": "refund_rate",
        "current_value": 48.5,
        "expected_value": 5.2,
        "change_percent": 832.69,
        "z_score": 4.85,
        "is_anomaly": True,
        "severity": "CRITICAL"
    }

    related_signals = [
        {"metric": "completed_orders", "change_percent": -45.0, "status": "DROPPED"},
        {"metric": "daily_revenue", "change_percent": -50.2, "status": "DROPPED"}
    ]

    dq_checks = {
        "passed": True,
        "freshness_days_lag": 0,
        "failures": []
    }

    print("\n🤖 Sending Anomaly Payload to Gemini API...")
    ai_response = explainer.explain_anomaly(
        anomaly_payload=simulated_anomaly,
        metric_definition=refund_metric_def,
        related_kpis=related_signals,
        data_quality_status=dq_checks
    )

    print("\n✨ GEMINI AI STRUCTURED RESPONSE:")
    print(json.dumps(ai_response, indent=2))

if __name__ == "__main__":
    main()