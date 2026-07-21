import pandas as pd

AIRPORTS = ["JFK", "LAX", "ORD", "ATL", "DFW"]

def clean_flights(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["ORIGIN"].isin(AIRPORTS)].copy()
    df["FL_DATE"]            = pd.to_datetime(df["FL_DATE"], errors="coerce")
    df["is_delayed"]         = df["DEP_DELAY"] > 15
    df["is_weather_delayed"] = df["WEATHER_DELAY"] > 0
    df["is_cancelled"]       = df["CANCELLED"] == 1.0
    df = df.dropna(subset=["FL_DATE"])
    return df