import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Please set SUPABASE_URL and SUPABASE_KEY in your .env file!")

# Initialize HTTP REST Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_table_or_view(name: str) -> pd.DataFrame:
    """Fetches data from a Supabase table or view via HTTP REST API."""
    response = supabase.table(name).select("*").execute()
    return pd.DataFrame(response.data)

def upsert_rows(table_name: str, rows: list, batch_size: int = 200, on_conflict: str = "metric_date, metric_name"):
    """Upserts list of dictionaries into a Supabase table via HTTP REST API."""
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        supabase.table(table_name).upsert(batch, on_conflict=on_conflict).execute()