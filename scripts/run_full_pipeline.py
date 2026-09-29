import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.metrics_engine import MetricEngine
from src.anomaly_detector import detect_anomaly
from src.data_quality import run_data_quality_checks
from src.llm_explainer import GeminiExplainer
from notifications.slack import send_slack_alert
from src.monitoring_history import (
    save_monitoring_run,
    save_data_quality_result,
    save_metric_result,
    save_anomaly
)

def main():
    print("=========================================================")
    print("🚀 RUNNING END-TO-END KPI DATA QUALITY & OBSERVABILITY PIPELINE")
    print("=========================================================\n")

    # 1. Run Data Quality Checks
    print("Step 1: Running Data Quality & Freshness Checks...")
    dq_results = run_data_quality_checks()
    dq_passed = dq_results.get("passed", False)
    print(f"  • Data Quality Suite Passed: {dq_passed}")

    # 2. Sync Daily Metrics
    print("\nStep 2: Syncing Daily Metrics from Views...")
    metric_engine = MetricEngine()
    metric_engine.calculate_and_store_daily_metrics()

    # 3. Detect Anomalies & Collect Evaluations
    print("\nStep 3: Running Statistical Anomaly Detection & AI Root Cause Engine...")
    explainer = GeminiExplainer()

    evaluations = []
    anomalies_to_process = []

    for metric in metric_engine.metrics:
        m_name = metric["name"]
        m_config = metric["anomaly_config"]
        
        df_hist = metric_engine.fetch_metric_history(m_name, lookback_days=30)
        if df_hist.empty:
            continue
            
        latest_row = df_hist.iloc[-1]
        history_baseline = df_hist.iloc[:-1]
        metric_date = str(latest_row["metric_date"])
        
        eval_result = detect_anomaly(
            current_value=float(latest_row["metric_value"]),
            history_df=history_baseline,
            anomaly_config=m_config
        )
        eval_result["metric_name"] = m_name
        eval_result["metric_date"] = metric_date
        eval_result["metric_definition"] = metric
        
        evaluations.append(eval_result)
        if eval_result["is_anomaly"]:
            anomalies_to_process.append(eval_result)

    # 4. Save Top-Level Monitoring Run to Supabase
    print("\nStep 4: Persisting Monitoring History into Supabase...")
    run_id = save_monitoring_run(
        data_quality_passed=dq_passed,
        total_metrics=len(evaluations),
        anomalies_count=len(anomalies_to_process)
    )

    # Save Data Quality Checks
    save_data_quality_result(run_id, dq_results)

    # Save Metric Results & Process Anomalies
    for ev in evaluations:
        m_name = ev["metric_name"]
        is_anom = ev["is_anomaly"]
        
        save_metric_result(
            run_id=run_id,
            metric_name=m_name,
            metric_date=ev["metric_date"],
            current_val=ev["current_value"],
            baseline=ev["expected_value"],
            pct_change=ev["change_percent"],
            is_anomaly=is_anom,
            severity=ev["severity"]
        )

        if is_anom:
            print(f"\n🚨 ANOMALY FLAGGED for [{m_name}]!")
            print(f"  • Deviation: {ev['change_percent']}% | Severity: {ev['severity']}")
            
            # AI Explanation
            print("  • Requesting Gemini AI Incident Interpretation...")
            ai_explanation = explainer.explain_anomaly(
                anomaly_payload=ev,
                metric_definition=ev["metric_definition"],
                data_quality_status=dq_results
            )
            
            # Dispatch Slack Alert
            print("  • Dispatching Alert to Slack Channel...")
            slack_sent = send_slack_alert(ev, ai_explanation)

            # Persist Anomaly Record
            save_anomaly(
                run_id=run_id,
                metric_name=m_name,
                current_val=ev["current_value"],
                baseline=ev["expected_value"],
                pct_change=ev["change_percent"],
                severity=ev["severity"],
                ai_explanation=ai_explanation,
                slack_alert_sent=slack_sent
            )

    if len(anomalies_to_process) == 0:
        print("\n✅ All KPIs are operating within normal statistical limits. No anomalies detected.")

    print("\n=========================================================")
    print("🏁 PIPELINE EXECUTION COMPLETE & HISTORICAL AUDIT SAVED")
    print("=========================================================")

if __name__ == "__main__":
    main()