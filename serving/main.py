import os
import boto3
import pandas as pd
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI(
    title="Weather Delay Risk API",
    description="Returns daily flight delay risk scores based on weather data",
    version="1.0.0"
)

AIRPORTS = ["JFK", "LAX", "ORD", "ATL", "DFW"]


def get_s3():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )


def load_risk_scores(date: str) -> pd.DataFrame:
    """Load risk scores parquet from S3 for a given date."""
    s3     = get_s3()
    BUCKET = os.getenv("AWS_BUCKET_NAME")
    key    = f"serving/risk_scores/{date}/risk_scores.parquet"

    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        buffer   = BytesIO(response["Body"].read())
        return pd.read_parquet(buffer)
    except s3.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail=f"No risk scores found for date {date}")


# ── Routes ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Weather Delay Risk API is running 🚀"}


@app.get("/airports")
def list_airports():
    """List all tracked airports."""
    return {"airports": AIRPORTS}


@app.get("/risk")
def get_risk(airport: str, date: str = None):
    """
    Get delay risk score for a specific airport.
    - airport: IATA code (e.g. JFK, LAX)
    - date: optional, defaults to today (YYYY-MM-DD)
    """
    # Default to today
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    # Validate airport
    airport = airport.upper()
    if airport not in AIRPORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Airport {airport} not supported. Choose from {AIRPORTS}"
        )

    # Load data from S3
    df = load_risk_scores(date)

    # Filter for requested airport
    result = df[df["airport"] == airport]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {airport} on {date}"
        )

    # Return latest row as JSON
    row = result.iloc[0].to_dict()

    # Convert date to string if needed
    if hasattr(row.get("date"), "isoformat"):
        row["date"] = row["date"].isoformat()

    return JSONResponse(content=row)


@app.get("/risk/all")
def get_all_risks(date: str = None):
    """
    Get delay risk scores for all airports.
    - date: optional, defaults to today (YYYY-MM-DD)
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    df = load_risk_scores(date)

    results = []
    for _, row in df.iterrows():
        r = row.to_dict()
        if hasattr(r.get("date"), "isoformat"):
            r["date"] = r["date"].isoformat()
        results.append(r)

    return JSONResponse(content={"date": date, "airports": results})