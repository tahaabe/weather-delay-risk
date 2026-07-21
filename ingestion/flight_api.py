import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

AIRPORTS = ["JFK", "LAX", "ORD", "ATL", "DFW"]


def fetch_flights(airport: str) -> dict:
    """Fetch real-time flight data for a given airport."""
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "dep_iata": airport,
        "flight_status": "landed",
        "limit": 10  # keep it low to save free tier requests
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return {
        "airport": airport,
        "fetched_at": datetime.utcnow().isoformat(),
        "data": response.json()
    }


def save_raw(payload: dict, airport_name: str):
    """Save raw JSON response to data/raw/flights/"""
    folder = os.path.join("data", "raw", "flights", TODAY)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{airport_name}.json")
    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"✅ Saved: {filepath}")


def run():
    print(f"✈️  Fetching flight data for {len(AIRPORTS)} airports...")
    for airport in AIRPORTS:
        try:
            payload = fetch_flights(airport)
            save_raw(payload, airport)
        except Exception as e:
            print(f"❌ Failed for {airport}: {e}")


if __name__ == "__main__":
    run()