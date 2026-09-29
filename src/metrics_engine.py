import os
import yaml
import pandas as pd
from src.database import fetch_table_or_view, upsert_rows, supabase

class MetricEngine:
    def __init__(self, config_path: str = "config/metrics.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.metrics = self.config.get("metrics", [])

    def _load_config(self) -> dict:
        """Reads and parses the YAML metric configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"❌ Configuration file not found at {self.config_path}")
        with open(self.config_path, "r") as file:
            return yaml.safe_load(file)

    def get_metric_definition(self, metric_name: str) -> dict:
        """Retrieves metric configuration metadata by name."""
        for metric in self.metrics:
            if metric["name"] == metric_name:
                return metric
        raise ValueError(f"Metric '{metric_name}' not defined in {self.config_path}")

    def fetch_daily_kpis_from_view(self) -> pd.DataFrame:
        """Queries view_daily_kpi_summary via HTTP REST API."""
        return fetch_table_or_view("view_daily_kpi_summary")

    def calculate_and_store_daily_metrics(self) -> pd.DataFrame:
        """
        Extracts computed KPIs from analytical views and persists them 
        into the silver table `daily_kpi_metrics`.
        """
        print("📊 Fetching analytical view data from Supabase via HTTP...")
        df_summary = self.fetch_daily_kpis_from_view()
        
        if df_summary.empty:
            print("⚠️ No data found in view_daily_kpi_summary!")
            return pd.DataFrame()

        rows_to_insert = []
        for _, row in df_summary.iterrows():
            m_date = str(row['metric_date'])
            for metric in self.metrics:
                m_name = metric['name']
                sql_col = metric['sql_expression']
                
                if sql_col in row and row[sql_col] is not None:
                    val = float(row[sql_col])
                    rows_to_insert.append({
                        "metric_date": m_date,
                        "metric_name": m_name,
                        "metric_value": val
                    })

        print("💾 Storing aggregated daily KPIs into `daily_kpi_metrics`...")
        upsert_rows("daily_kpi_metrics", rows_to_insert)
        
        print(f"✅ Successfully calculated and stored {len(rows_to_insert)} KPI records!")
        return pd.DataFrame(rows_to_insert)

    def fetch_metric_history(self, metric_name: str, lookback_days: int = 30) -> pd.DataFrame:
        """Fetches historical time-series data for a single metric via HTTP REST API."""
        res = (
            supabase.table("daily_kpi_metrics")
            .select("metric_date, metric_name, metric_value")
            .eq("metric_name", metric_name)
            .order("metric_date", desc=True)
            .limit(lookback_days)
            .execute()
        )
        df = pd.DataFrame(res.data)
        if not df.empty:
            df = df.sort_values(by="metric_date", ascending=True).reset_index(drop=True)
        return df