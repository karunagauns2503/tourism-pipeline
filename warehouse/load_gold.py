import duckdb
import pandas as pd
from common import read, rain_category, date_key, GOLD, DB

OUTDOOR = "beach|fort|waterfall|sanctuary|wildlife|park|garden|lake|island"

def main():
    w = read("fact_weather_daily")
    d = read("dim_date").copy()
    p = read("places_goa").copy()

    # ---- dim_date: Saini's table + key + long weekend flag ----
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date").reset_index(drop=True)
    off = d["is_weekend"].astype(bool) | d["is_holiday"].astype(bool)
    grp = (off != off.shift()).cumsum()
    d["is_long_weekend"] = (off & (off.groupby(grp).transform("sum") >= 3)
                            & d["is_holiday"].astype(bool).groupby(grp).transform("max"))
    d.insert(0, "date_key", date_key(d["date"]))

    # ---- dim_rain_category ----
    cat = pd.DataFrame({"category_key": [1, 2, 3],
                        "category_name": ["Dry", "Light Rain", "Heavy Monsoon"],
                        "min_mm": [0.0, 2.5, 30.0], "max_mm": [2.5, 30.0, None]})

    # ---- fact_daily_weather (CSV = main source, API kept as cross-check) ----
    w = w.copy()
    w["date"] = pd.to_datetime(w["date"])
    w["category_name"] = rain_category(w["csv_rainfall_mm"])
    f = w.merge(cat[["category_key", "category_name"]], on="category_name")
    f.insert(0, "date_key", date_key(f["date"]))
    fact = f.rename(columns={"csv_max_temp_c": "max_temp_c", "csv_rainfall_mm": "rainfall_mm"})
    fact["rain_diff_csv_vs_api_mm"] = (fact["rainfall_mm"] - fact["api_rainfall_mm"]).round(2)
    fact = fact[["date_key", "category_key", "max_temp_c", "rainfall_mm",
                 "api_max_temp_c", "api_min_temp_c", "api_rainfall_mm",
                 "rain_diff_csv_vs_api_mm"]].sort_values("date_key")

    # ---- dim_place (14 Goa places) ----
    p["is_outdoor"] = p["type"].astype(str).str.lower().str.contains(OUTDOOR)
    p = p.reset_index(drop=True)
    p.insert(0, "place_id", range(1, len(p) + 1))
    dim_place = p.rename(columns={
        "name": "place_name", "type": "place_type", "google_review_rating": "rating",
        "entrance_fee_in_inr": "entrance_fee_inr",
        "number_of_google_review_in_lakhs": "review_count_lakhs",
        "time_needed_to_visit_in_hrs": "visit_hours"})[
        ["place_id", "place_name", "city", "state", "place_type", "significance",
         "establishment_year", "rating", "review_count_lakhs", "entrance_fee_inr",
         "visit_hours", "weekly_off", "best_time_to_visit", "is_outdoor"]]

    GOLD.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()                        # full rebuild = repeatable runs
    con = duckdb.connect(str(DB))
    for name, df in [("dim_date", d), ("dim_rain_category", cat),
                     ("dim_place", dim_place), ("fact_daily_weather", fact)]:
        con.register("tmp", df)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM tmp")
        con.unregister("tmp")
        print(f"{name:20s} {len(df):5d} rows")

    # ---- analytical views ----
    con.execute("""CREATE VIEW v_monthly_weather AS
      SELECT d.year, d.month, d.month_name,
             round(sum(f.rainfall_mm),1) AS total_rain_mm,
             count(*) FILTER (WHERE f.rainfall_mm >= 2.5) AS rainy_days,
             round(avg(f.max_temp_c),1) AS avg_max_temp_c
      FROM fact_daily_weather f JOIN dim_date d USING (date_key)
      GROUP BY 1,2,3 ORDER BY 1,2""")
    con.execute("""CREATE VIEW v_season_weather AS
      SELECT d.season, count(*) AS days,
             round(avg(f.rainfall_mm),2) AS avg_daily_rain_mm,
             count(*) FILTER (WHERE c.category_name = 'Heavy Monsoon') AS heavy_rain_days,
             round(avg(f.max_temp_c),1) AS avg_max_temp_c
      FROM fact_daily_weather f JOIN dim_date d USING (date_key)
      JOIN dim_rain_category c USING (category_key)
      GROUP BY 1 ORDER BY 3 DESC""")
    con.execute("""CREATE VIEW v_holiday_weather AS
      SELECT d.date, d.holiday_name, d.is_long_weekend, d.season,
             f.rainfall_mm, c.category_name AS rain_category
      FROM fact_daily_weather f JOIN dim_date d USING (date_key)
      JOIN dim_rain_category c USING (category_key)
      WHERE d.is_holiday ORDER BY d.date""")
    con.execute("""CREATE VIEW v_holidays_by_rain AS
      SELECT c.category_name AS rain_category, count(*) AS holiday_days
      FROM fact_daily_weather f JOIN dim_date d USING (date_key)
      JOIN dim_rain_category c USING (category_key)
      WHERE d.is_holiday GROUP BY 1""")
    con.execute("""CREATE VIEW v_place_summary AS
      SELECT is_outdoor, count(*) AS places,
             round(avg(rating),2) AS avg_rating,
             round(avg(review_count_lakhs),2) AS avg_reviews_lakhs,
             round(avg(entrance_fee_inr),0) AS avg_fee_inr
      FROM dim_place GROUP BY is_outdoor""")
    con.close()
    print("Gold loaded:", DB)

if __name__ == "__main__":
    main()