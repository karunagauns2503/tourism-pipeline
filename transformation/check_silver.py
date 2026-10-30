import os
import pandas as pd

expected = {
    "places_clean.parquet": 325,
    "places_goa.parquet": 14,
    "fact_weather_daily.parquet": 730,
    "holidays_clean.parquet": 45,
    "dim_date.parquet": 730,
}

for name, want in expected.items():
    path = os.path.join("data/silver", name)
    if not os.path.exists(path):
        print(f"MISSING  {name}")
        continue
    df = pd.read_parquet(path)
    status = "OK" if len(df) == want else "CHECK"
    print(f"{status:8} {name}: rows={len(df)} (expected {want}), columns={len(df.columns)}")

if os.path.exists("data/silver/places_clean.parquet"):
    p = pd.read_parquet("data/silver/places_clean.parquet")
    print("Maharastra left:", (p["state"] == "Maharastra").sum())
    print("States:", p["state"].nunique())
    print("Years not parsed:", p["establishment_year"].isna().sum())

if os.path.exists("data/silver/dim_date.parquet"):
    d = pd.read_parquet("data/silver/dim_date.parquet")
    print("Holiday days:", int(d["is_holiday"].sum()))
