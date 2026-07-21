import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# --- Airports we're tracking (name, latitude, longitude) ---
AIRPORTS = [
    {"name": "JFK", "lat": 40.6413, "lon": -73.7781},
    {"name": "LAX", "lat": 33.9425, "lon": -118.4081},
    {"name": "ORD", "lat": 41.9742, "lon": -87.9073},
    {"name": "ATL", "lat": 33.6407, "lon": -84.4277},
    {"name": "DFW", "lat": 32.8998, "lon": -97.0403},
]

# --- Date range: yesterday and today ---
TODAY = datetime.utcnow().strftime("%Y-%m-%d")
YESTERDAY = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")


def fetch_weather(airport: dict) -> dict:
    """Fetch hourly weather data for a given airport."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": airport["lat"],
        "longitude": airport["lon"],
        "hourly": "temperature_2m,precipitation,windspeed_10m,visibility",
        "start_date": YESTERDAY,
        "end_date": TODAY,
        "timezone": "UTC"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # raises error if request fails

    return {
        "airport": airport["name"],
        "fetched_at": datetime.utcnow().isoformat(),
        "data": response.json()
    }


def save_raw(payload: dict, airport_name: str):
    """Save raw JSON response to data/raw/weather/"""
    folder = os.path.join("data", "raw", "weather", TODAY)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{airport_name}.json")
    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"✅ Saved: {filepath}")


def run():
    print(f"🌤️  Fetching weather data for {len(AIRPORTS)} airports...")
    for airport in AIRPORTS:
        try:
            payload = fetch_weather(airport)
            save_raw(payload, airport["name"])
        except Exception as e:
            print(f"❌ Failed for {airport['name']}: {e}")


if __name__ == "__main__":
    run()