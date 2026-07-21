import pandas as pd

def clean_weather(payload: dict) -> pd.DataFrame:
    airport = payload["airport"]
    hourly  = payload["data"]["hourly"]

    df = pd.DataFrame({
        "timestamp":     hourly["time"],
        "temperature":   hourly["temperature_2m"],
        "precipitation": hourly["precipitation"],
        "windspeed":     hourly["windspeed_10m"],
        "visibility":    hourly["visibility"],
    })
    df["airport"]   = airport
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"]      = df["timestamp"].dt.date
    df = df.dropna(subset=["temperature", "precipitation", "windspeed", "visibility"], how="all")
    return df