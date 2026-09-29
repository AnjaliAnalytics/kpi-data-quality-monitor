import sys
import os

# Add the project root directory (D:\kpi-data-quality-monitor) to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.metrics_engine import MetricEngine

def main():
    print("--- 🛠️ TESTING YAML SEMANTIC METRIC ENGINE ---")
    engine = MetricEngine()
    
    print(f"\nLoaded {len(engine.metrics)} metric definitions from YAML:")
    for m in engine.metrics:
        print(f"  • [{m['name']}] -> {m['display_name']} ({m['unit']})")

    print("\nCalculating and synchronizing daily metrics from analytical view...")
    df_stored = engine.calculate_and_store_daily_metrics()
    
    print("\nFetching sample history for 'daily_revenue':")
    df_rev = engine.fetch_metric_history("daily_revenue", lookback_days=5)
    print(df_rev.to_string(index=False))

if __name__ == "__main__":
    main()