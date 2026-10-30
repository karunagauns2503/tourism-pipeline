import glob, json, logging, os

import pandas as pd
import yaml


def load_config(path="config/config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def latest_bronze(cfg, source, pattern):
    files = sorted(glob.glob(os.path.join(cfg["bronze_dir"], source, "ingestion_date=*", pattern)))
    if not files:
        raise FileNotFoundError(f"No Bronze file found for {source}")
    return files[-1]


def main(run_date=None):
    cfg = load_config()
    os.makedirs("logs", exist_ok=True)
    os.makedirs(cfg["silver_dir"], exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler("logs/transformation.log"), logging.StreamHandler()],
    )

    csv_df = pd.read_csv(latest_bronze(cfg, "goa_weather", "*.csv"))
    csv_df["date"] = pd.to_datetime(csv_df["date"])
    if not csv_df["date"].is_unique:
        raise ValueError("weather csv has repeated dates")

    bad = csv_df[(csv_df["rainfall_mm"] < 0) | (csv_df["max_temp_c"] < 10) | (csv_df["max_temp_c"] > 50)]
    if len(bad):
        bad.to_csv(os.path.join(cfg["silver_dir"], "weather_rejects.csv"), index=False)
        csv_df = csv_df.drop(bad.index)
    logging.info("weather_csv: rows=%d rejected=%d", len(csv_df), len(bad))

    with open(latest_bronze(cfg, "weather_api", "*.json")) as f:
        d = json.load(f)
    api_df = pd.DataFrame(d["daily"]).rename(columns={
        "time": "date",
        "temperature_2m_max": "api_max_temp_c",
        "temperature_2m_min": "api_min_temp_c",
        "precipitation_sum": "api_rainfall_mm",
    })
    api_df["date"] = pd.to_datetime(api_df["date"])
    logging.info("weather_api: rows=%d nulls=%d", len(api_df), int(api_df.isna().sum().sum()))

    csv_df = csv_df.rename(columns={"max_temp_c": "csv_max_temp_c", "rainfall_mm": "csv_rainfall_mm"})
    fact = csv_df.merge(api_df, on="date", how="outer").sort_values("date")

    temp_diff = (fact["csv_max_temp_c"] - fact["api_max_temp_c"]).abs().mean()
    rain_diff = (fact["csv_rainfall_mm"] - fact["api_rainfall_mm"]).abs().mean()
    logging.info("weather compare: avg max temp difference=%.2f C, avg rain difference=%.2f mm", temp_diff, rain_diff)
    logging.info("weather compare: total rain csv=%.0f mm, api=%.0f mm",
                 fact["csv_rainfall_mm"].sum(), fact["api_rainfall_mm"].sum())

    fact.to_parquet(os.path.join(cfg["silver_dir"], "fact_weather_daily.parquet"), index=False)
    logging.info("fact_weather_daily: rows=%d", len(fact))


if __name__ == "__main__":
    main()
