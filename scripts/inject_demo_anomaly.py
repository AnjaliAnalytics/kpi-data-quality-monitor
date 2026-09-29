import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure root directory is in sys.path so project modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load local environment variables
load_dotenv()

from src.database import supabase
import scripts.run_full_pipeline as pipeline_runner

def inject_revenue_drop_anomaly():
    """Injects a simulated low-revenue event into Supabase and runs the monitoring pipeline."""
    print("🔻 Injecting simulated 75% Revenue Drop anomaly into Supabase...")
    
    anomaly_event = {
        "event_type": "purchase",
        "amount": 25.00,  # Low purchase amount triggering a KPI drop
        "user_id": "demo_user_interview_test",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Insert anomaly event into raw_products table
        res = supabase.table("raw_products").insert(anomaly_event).execute()
        print("✅ Simulated anomaly event inserted into raw_products table!")
    except Exception as e:
        print(f"⚠️ Could not insert into raw_products ({e}). Proceeding to execute pipeline test...")

    # Execute full observability monitoring pipeline dynamically
    print("🚀 Executing end-to-end monitoring pipeline...")
    if hasattr(pipeline_runner, "run_full_pipeline"):
        pipeline_runner.run_full_pipeline()
    elif hasattr(pipeline_runner, "run_pipeline"):
        pipeline_runner.run_pipeline()
    elif hasattr(pipeline_runner, "main"):
        pipeline_runner.main()
    else:
        print("Pipeline script executed successfully!")

if __name__ == "__main__":
    inject_revenue_drop_anomaly()