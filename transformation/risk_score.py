import pandas as pd

def compute_risk_score(df_weather: pd.DataFrame, df_flights: pd.DataFrame) -> pd.DataFrame:
    weather_agg = df_weather.groupby(["airport", "date"]).agg(
        avg_windspeed  = ("windspeed",     "mean"),
        max_windspeed  = ("windspeed",     "max"),
        total_precip   = ("precipitation", "sum"),
        avg_visibility = ("visibility",    "mean"),
        min_visibility = ("visibility",    "min"),
    ).reset_index()

    weather_agg["wind_risk"]       = (weather_agg["max_windspeed"] / 100).clip(0, 1)
    weather_agg["precip_risk"]     = (weather_agg["total_precip"]  / 20).clip(0, 1)
    weather_agg["visibility_risk"] = (1 - weather_agg["min_visibility"] / 10000).clip(0, 1)

    flight_agg = df_flights.groupby("ORIGIN").agg(
        delay_rate         = ("is_delayed",         "mean"),
        weather_delay_rate = ("is_weather_delayed",  "mean"),
        avg_dep_delay      = ("DEP_DELAY",           "mean"),
    ).reset_index().rename(columns={"ORIGIN": "airport"})

    flight_agg["historical_risk"] = flight_agg["weather_delay_rate"].clip(0, 1)

    df_risk = weather_agg.merge(
        flight_agg[["airport", "historical_risk", "delay_rate", "avg_dep_delay"]],
        on="airport", how="left"
    )

    df_risk["risk_score"] = (
        0.25 * df_risk["wind_risk"]       +
        0.30 * df_risk["precip_risk"]     +
        0.25 * df_risk["visibility_risk"] +
        0.20 * df_risk["historical_risk"]
    ).round(3)

    def label(score):
        if score < 0.2: return "Low"
        if score < 0.4: return "Moderate"
        if score < 0.6: return "High"
        return "Severe"

    df_risk["risk_label"] = df_risk["risk_score"].apply(label)

    return df_risk[["airport", "date", "risk_score", "risk_label",
                     "avg_windspeed", "total_precip", "avg_visibility",
                     "delay_rate", "avg_dep_delay"]]