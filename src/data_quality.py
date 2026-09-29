import pandas as pd
from datetime import datetime
from src.database import fetch_table_or_view, supabase

def run_data_quality_checks() -> Dict[str, Any]:
    """
    Executes automated data quality checks across raw tables:
    1. Freshness Check (Are new orders arriving today?)
    2. Null Values Check
    3. Duplicate Check
    4. Invalid Status/Amount Check
    """
    print("🔍 Executing Data Quality & Freshness Verification Suite...")
    
    # 1. Fetch Orders
    df_orders = fetch_table_or_view("orders")
    
    results = {
        "check_timestamp": datetime.now().isoformat(),
        "total_records_analyzed": len(df_orders),
        "passed": True,
        "failures": []
    }

    if df_orders.empty:
        results["passed"] = False
        results["failures"].append({"check": "Table Freshness", "issue": "Orders table is completely empty!"})
        return results

    # Data Quality Check 1: Missing values in essential fields
    null_counts = df_orders[["order_id", "customer_id", "total_amount", "status"]].isnull().sum().to_dict()
    has_nulls = any(count > 0 for count in null_counts.values())
    if has_nulls:
        results["passed"] = False
        results["failures"].append({"check": "Missing Values", "issue": f"Nulls found: {null_counts}"})

    # Data Quality Check 2: Duplicate Order IDs
    duplicate_count = int(df_orders.duplicated(subset=["order_id"]).sum())
    if duplicate_count > 0:
        results["passed"] = False
        results["failures"].append({"check": "Uniqueness", "issue": f"Found {duplicate_count} duplicate order IDs!"})

    # Data Quality Check 3: Invalid order values or amounts
    invalid_amounts = int((df_orders["total_amount"] <= 0).sum())
    if invalid_amounts > 0:
        results["passed"] = False
        results["failures"].append({"check": "Business Rule Integrity", "issue": f"Found {invalid_amounts} orders with <= $0 amount!"})

    # Data Quality Check 4: Data Freshness
    df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
    latest_order_date = df_orders["order_date"].max()
    days_since_last_order = (datetime.now() - latest_order_date).days
    
    results["latest_order_timestamp"] = latest_order_date.isoformat()
    results["freshness_days_lag"] = days_since_last_order

    if days_since_last_order > 3:
        results["passed"] = False
        results["failures"].append({"check": "Data Freshness", "issue": f"Data lag detected! Latest transaction is {days_since_last_order} days old."})

    return results