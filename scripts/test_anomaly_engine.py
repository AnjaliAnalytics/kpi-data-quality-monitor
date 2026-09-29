import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.metrics_engine import MetricEngine
from src.anomaly_detector import detect_anomaly
from src.data_quality import run_data_quality_checks

def main():
    print("--- 🛠️ TESTING STATISTICAL ANOMALY & DATA QUALITY ENGINE ---")
    
    # 1. Run Data Quality Checks
    dq_results = run_data_quality_checks()
    print("\n📋 DATA QUALITY SUITE RESULT:")
    print(json.dumps(dq_results, indent=2))

    # 2. Test Anomaly Detection against seeded dataset anomalies
    print("\n📊 ANOMALY DETECTION EVALUATION:")
    engine = MetricEngine()
    
    for metric in engine.metrics:
        m_name = metric["name"]
        m_config = metric["anomaly_config"]
        
        # Fetch 30-day history for the metric
        df_hist = engine.fetch_metric_history(m_name, lookback_days=30)
        
        if df_hist.empty:
            continue
            
        # Evaluate today's latest metric value against historical baseline
        latest_row = df_hist.iloc[-1]
        history_baseline = df_hist.iloc[:-1] # excludes target evaluation day
        
        eval_result = detect_anomaly(
            current_value=float(latest_row["metric_value"]),
            history_df=history_baseline,
            anomaly_config=m_config
        )
        
        status_flag = "🚨 ANOMALY FLAGGED!" if eval_result["is_anomaly"] else "✅ NORMAL"
        print(f"\nMetric: [{m_name}] -> {status_flag}")
        print(f"  • Date: {latest_row['metric_date']}")
        print(f"  • Current Value: {eval_result['current_value']} {metric['unit']}")
        print(f"  • Expected Baseline: {eval_result['expected_value']}")
        print(f"  • Change: {eval_result['change_percent']}% | Z-Score: {eval_result['z_score']}")
        print(f"  • Severity: {eval_result['severity']}")

if __name__ == "__main__":
    main()