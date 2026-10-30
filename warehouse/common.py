from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
DB = GOLD / "goa_tourism.duckdb"

def read(name):
    f = SILVER / f"{name}.parquet"
    if not f.exists():
        raise FileNotFoundError(f"{f} not found. Run the transformation scripts first.")
    return pd.read_parquet(f)

def need(df, cols, name):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"{name} is missing columns {missing}. Found: {list(df.columns)}")

def rain_category(mm):
    # Dry < 2.5 mm, Light Rain 2.5 to 30 mm, Heavy Monsoon 30 mm and above
    return pd.cut(mm, [-np.inf, 2.5, 30, np.inf],
                  labels=["Dry", "Light Rain", "Heavy Monsoon"], right=False).astype(str)

def date_key(s):
    return pd.to_datetime(s).dt.strftime("%Y%m%d").astype(int)