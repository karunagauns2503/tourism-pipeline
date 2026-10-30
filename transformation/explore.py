import glob, json
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

def latest(source, pattern):
    files = sorted(glob.glob(f"data/raw/{source}/ingestion_date=*/{pattern}"))
    return files[-1]

print("=== PLACES ===")
p = pd.read_csv(latest("places", "*.csv"))
print(p.head())
p.info()
print("Nulls:\n", p.isna().sum())
print("Duplicates:", p.duplicated().sum())
print("States:\n", p["State"].value_counts())
print("Establishment Year samples:", p["Establishment Year"].unique()[:30])

print("\n=== WEATHER CSV ===")
w = pd.read_csv(latest("goa_weather", "*.csv"))
w.info()
print(w.describe())

print("\n=== HOLIDAYS ===")
h = pd.read_csv(latest("goa_holidays", "*.csv"))
h.info()
print(h.head(10))

print("\n=== WEATHER API ===")
d = json.load(open(latest("weather_api", "*.json")))
print("Keys:", list(d.keys()))
a = pd.DataFrame(d["daily"])
a.info()
print(a.head())
