import glob, logging, os

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


def season(month):
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Summer"
    if month in (6, 7, 8, 9):
        return "Monsoon"
    return "Post-monsoon"


def main(run_date=None):
    cfg = load_config()
    os.makedirs("logs", exist_ok=True)
    os.makedirs(cfg["silver_dir"], exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler("logs/transformation.log"), logging.StreamHandler()],
    )

    h = pd.read_csv(latest_bronze(cfg, "goa_holidays", "*.csv"))
    rows_in = len(h)
    h["date"] = pd.to_datetime(h["date"])
    h["holiday_name"] = h["holiday_name"].str.strip()
    h = h.drop_duplicates()
    logging.info("holidays: rows in=%d out=%d, rows with two holidays=%d",
                 rows_in, len(h), int(h["holiday_name"].str.contains(";").sum()))
    h.to_parquet(os.path.join(cfg["silver_dir"], "holidays_clean.parquet"), index=False)

    d = pd.DataFrame({"date": pd.date_range("2022-01-01", "2023-12-31")})
    d["year"] = d["date"].dt.year
    d["quarter"] = d["date"].dt.quarter
    d["month"] = d["date"].dt.month
    d["month_name"] = d["date"].dt.month_name()
    d["day"] = d["date"].dt.day
    d["weekday"] = d["date"].dt.day_name()
    d["is_weekend"] = d["date"].dt.dayofweek >= 5
    d["season"] = d["month"].apply(season)

    names = h.groupby("date")["holiday_name"].apply(lambda s: "; ".join(s)).reset_index()
    d = d.merge(names, on="date", how="left")
    d["is_holiday"] = d["holiday_name"].notna()

    d.to_parquet(os.path.join(cfg["silver_dir"], "dim_date.parquet"), index=False)
    logging.info("dim_date: rows=%d holiday days=%d", len(d), int(d["is_holiday"].sum()))


if __name__ == "__main__":
    main()
