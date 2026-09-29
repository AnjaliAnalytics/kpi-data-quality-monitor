import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.monitoring_history import (
    save_monitoring_run,
    save_data_quality_result,
    save_metric_result,
    save_anomaly
)
from src.data_quality import run_data_quality_checks

def main():
    print("🌱 Seeding Demo Anomaly & Data Quality Audit Records...")

    dq_results = run_data_quality_checks()
    
    # Create Monitoring Run
    run_id = save_monitoring_run(
        data_quality_passed=False,
        total_metrics=5,
        anomalies_count=1
    )

    # Save DQ Results
    save_data_quality_result(run_id, dq_results)

    # Save Sample Metric
    save_metric_result(
        run_id=run_id,
        metric_name="refund_rate",
        metric_date="2026-09-29",
        current_val=48.5,
        baseline=5.2,
        pct_change=832.69,
        is_anomaly=True,
        severity="CRITICAL"
    )

    # Save Sample Anomaly
    mock_ai = {
        "summary": "Refund rate experienced a severe critical spike exceeding normal baselines by 832.69%.",
        "possible_contributing_signals": [
            "completed_orders dropped by 45.0%",
            "daily_revenue dropped by 50.2%"
        ],
        "recommended_investigation": [
            "Check payment gateway callback logs for repeated automated refunds.",
            "Inspect raw customer order timestamps for duplicate processing."
        ]
    }

    save_anomaly(
        run_id=run_id,
        metric_name="refund_rate",
        current_val=48.5,
        baseline=5.2,
        pct_change=832.69,
        severity="CRITICAL",
        ai_explanation=mock_ai,
        slack_alert_sent=True
    )

    print("✅ Demo audit records successfully seeded into Supabase!")

if __name__ == "__main__":
    main()