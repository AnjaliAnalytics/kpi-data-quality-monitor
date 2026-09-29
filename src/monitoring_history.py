import os
import json
from datetime import datetime
from dotenv import load_dotenv
from src.database import supabase

load_dotenv()

def save_monitoring_run(data_quality_passed: bool, total_metrics: int, anomalies_count: int) -> str:
    """Inserts a top-level execution run record into `monitoring_runs` and returns the run_id."""
    run_payload = {
        "run_timestamp": datetime.utcnow().isoformat(),
        "data_quality_passed": data_quality_passed,
        "total_metrics_evaluated": total_metrics,
        "anomalies_detected": anomalies_count,
        "status": "COMPLETED"
    }
    response = supabase.table("monitoring_runs").insert(run_payload).execute()
    if response.data:
        run_id = response.data[0]["id"]
        print(f"💾 Logged Monitoring Run [ID: {run_id}]")
        return run_id
    else:
        raise RuntimeError("Failed to create monitoring_runs entry in Supabase.")

def save_data_quality_result(run_id: str, dq_results: dict):
    """Logs individual data quality suite outcomes into `data_quality_results`."""
    rows = []
    
    # Check for direct key lists or dictionaries in dq_results
    if "results" in dq_results and isinstance(dq_results["results"], list):
        for check in dq_results["results"]:
            rows.append({
                "run_id": run_id,
                "check_name": check.get("check_name", "Data Quality Check"),
                "passed": check.get("passed", False),
                "details": check
            })
    elif "checks" in dq_results:
        checks = dq_results["checks"]
        if isinstance(checks, dict):
            for check_name, check_data in checks.items():
                is_passed = check_data.get("passed", False) if isinstance(check_data, dict) else bool(check_data)
                rows.append({
                    "run_id": run_id,
                    "check_name": check_name,
                    "passed": is_passed,
                    "details": check_data if isinstance(check_data, dict) else {"details": check_data}
                })
        elif isinstance(checks, list):
            for check in checks:
                rows.append({
                    "run_id": run_id,
                    "check_name": check.get("check_name", "Data Quality Check"),
                    "passed": check.get("passed", False),
                    "details": check
                })
    else:
        # Fallback: Treat top-level dictionary items as individual checks
        for key, val in dq_results.items():
            if key != "run_id":
                is_passed = val.get("passed", False) if isinstance(val, dict) else bool(val)
                rows.append({
                    "run_id": run_id,
                    "check_name": key,
                    "passed": is_passed,
                    "details": val if isinstance(val, dict) else {"value": val}
                })

    if rows:
        supabase.table("data_quality_results").insert(rows).execute()
        print(f"💾 Successfully persisted {len(rows)} Data Quality check records into Supabase!")

def save_metric_result(run_id: str, metric_name: str, metric_date: str, current_val: float, baseline: float, pct_change: float, is_anomaly: bool, severity: str):
    """Inserts or updates a metric evaluation snapshot in `metric_results`."""
    row = {
        "run_id": run_id,
        "metric_name": metric_name,
        "metric_date": metric_date,
        "current_value": current_val,
        "expected_baseline": baseline,
        "percentage_change": pct_change,
        "is_anomaly": is_anomaly,
        "severity": severity
    }
    supabase.table("metric_results").upsert(row, on_conflict="run_id, metric_name, metric_date").execute()

def save_anomaly(run_id: str, metric_name: str, current_val: float, baseline: float, pct_change: float, severity: str, ai_explanation: dict, slack_alert_sent: bool):
    """Persists detailed anomaly incidents, AI summaries, and Slack delivery status into `anomalies`."""
    row = {
        "run_id": run_id,
        "metric_name": metric_name,
        "current_value": current_val,
        "expected_baseline": baseline,
        "percentage_change": pct_change,
        "severity": severity,
        "ai_explanation": ai_explanation,
        "slack_alert_sent": slack_alert_sent
    }
    supabase.table("anomalies").upsert(row, on_conflict="run_id, metric_name").execute()
    print(f"💾 Logged Anomaly incident for [{metric_name}] (Slack Sent: {slack_alert_sent}).")