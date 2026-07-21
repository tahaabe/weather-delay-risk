import os
import sys
import json
import boto3
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from dotenv import load_dotenv

from airflow import DAG
from airflow.operators.python import PythonOperator

# Make transformation modules importable inside Airflow
sys.path.insert(0, "/opt/airflow")

load_dotenv()

# --- Shared config ---
AIRPORTS = ["JFK", "LAX", "ORD", "ATL", "DFW"]

default_args = {
    "owner": "taha",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def get_s3():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )


def get_today():
    return datetime.utcnow().strftime("%Y-%m-%d")


# ── Task 1: Fetch weather ──────────────────────────────────────────
def fetch_weather():
    import requests
    from ingestion.weather_api import AIRPORTS, fetch_weather as _fetch, save_raw
    print("🌤️ Fetching weather data...")
    for airport in AIRPORTS:
        payload = _fetch(airport)
        save_raw(payload, airport["name"])
    print("✅ Weather fetched")


# ── Task 2: Fetch flights ──────────────────────────────────────────
def fetch_flights():
    from ingestion.flight_api import AIRPORTS, fetch_flights as _fetch, save_raw
    print("✈️ Fetching flight data...")
    for airport in AIRPORTS:
        payload = _fetch(airport)
        save_raw(payload, airport)
    print("✅ Flights fetched")


# ── Task 3: Upload raw data to S3 ─────────────────────────────────
def upload_to_s3():
    from ingestion.upload_to_s3 import run
    print("🚀 Uploading raw data to S3...")
    run()
    print("✅ Upload done")


# ── Task 4: Transform weather ──────────────────────────────────────
def transform_weather():
    from transformation.clean_weather import clean_weather

    s3     = get_s3()
    BUCKET = os.getenv("AWS_BUCKET_NAME")
    TODAY  = get_today()

    print("🔄 Transforming weather data...")
    all_dfs = []
    for airport in AIRPORTS:
        key     = f"raw/weather/{TODAY}/{airport}.json"
        resp    = s3.get_object(Bucket=BUCKET, Key=key)
        payload = json.loads(resp["Body"].read().decode("utf-8"))
        df      = clean_weather(payload)          # ← imported function
        all_dfs.append(df)
        print(f"   {airport}: {len(df)} rows")

    combined = pd.concat(all_dfs, ignore_index=True)
    buffer   = BytesIO()
    combined.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.put_object(
        Bucket=BUCKET,
        Key=f"processed/weather/{TODAY}/all_airports.parquet",
        Body=buffer.getvalue()
    )
    print(f"✅ Weather transformed: {len(combined)} rows")


# ── Task 5: Transform flights ──────────────────────────────────────
def transform_flights():
    from transformation.clean_flights import clean_flights

    s3     = get_s3()
    BUCKET = os.getenv("AWS_BUCKET_NAME")
    TODAY  = get_today()

    print("🔄 Transforming flight data...")
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix="raw/bts/")
    files    = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".csv")]

    all_dfs = []
    for key in files:
        resp    = s3.get_object(Bucket=BUCKET, Key=key)
        content = resp["Body"].read().decode("utf-8")
        df      = pd.read_csv(StringIO(content), low_memory=False)
        df      = clean_flights(df)               # ← imported function
        all_dfs.append(df)
        print(f"   {key}: {len(df)} rows")

    combined = pd.concat(all_dfs, ignore_index=True)
    buffer   = BytesIO()
    combined.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.put_object(
        Bucket=BUCKET,
        Key=f"processed/flights/{TODAY}/all_airports.parquet",
        Body=buffer.getvalue()
    )
    print(f"✅ Flights transformed: {len(combined)} rows")


# ── Task 6: Compute risk score ─────────────────────────────────────
def compute_risk():
    from transformation.risk_score import compute_risk_score

    s3     = get_s3()
    BUCKET = os.getenv("AWS_BUCKET_NAME")
    TODAY  = get_today()

    print("🧮 Computing risk scores...")

    def read_parquet(key):
        resp   = s3.get_object(Bucket=BUCKET, Key=key)
        buffer = BytesIO(resp["Body"].read())
        return pd.read_parquet(buffer)

    df_weather = read_parquet(f"processed/weather/{TODAY}/all_airports.parquet")
    df_flights = read_parquet(f"processed/flights/{TODAY}/all_airports.parquet")

    output = compute_risk_score(df_weather, df_flights)  # ← imported function

    buffer = BytesIO()
    output.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.put_object(
        Bucket=BUCKET,
        Key=f"serving/risk_scores/{TODAY}/risk_scores.parquet",
        Body=buffer.getvalue()
    )
    print(f"✅ Risk scores saved: {len(output)} rows")


# ── DAG definition ─────────────────────────────────────────────────
with DAG(
    dag_id="weather_delay_risk_pipeline",
    default_args=default_args,
    description="Daily weather delay risk pipeline",
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["weather", "flights", "risk"],
) as dag:

    t1 = PythonOperator(task_id="fetch_weather",      python_callable=fetch_weather)
    t2 = PythonOperator(task_id="fetch_flights",      python_callable=fetch_flights)
    t3 = PythonOperator(task_id="upload_to_s3",       python_callable=upload_to_s3)
    t4 = PythonOperator(task_id="transform_weather",  python_callable=transform_weather)
    t5 = PythonOperator(task_id="transform_flights",  python_callable=transform_flights)
    t6 = PythonOperator(task_id="compute_risk_score", python_callable=compute_risk)

    # Task order
    [t1, t2] >> t3 >> [t4, t5] >> t6