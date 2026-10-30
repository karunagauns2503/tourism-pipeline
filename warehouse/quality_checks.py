import sys
import pandas as pd
from common import read, need, ROOT

def main():
    w = read("fact_weather_daily")
    d = read("dim_date")
    h = read("holidays_clean")
    p = read("places_goa")
    pa = read("places_clean")
    need(w, ["date", "csv_max_temp_c", "csv_rainfall_mm", "api_rainfall_mm"], "fact_weather_daily")
    need(d, ["date", "is_holiday", "holiday_name"], "dim_date")
    need(h, ["date", "holiday_name"], "holidays_clean")
    need(p, ["name", "state", "google_review_rating", "entrance_fee_in_inr"], "places_goa")

    if "--demo-fail" in sys.argv:   # inject bad data to show the pipeline stopping
        w = w.copy(); p = p.copy()
        w.loc[0, "csv_rainfall_mm"] = -5
        p.loc[p.index[0], "google_review_rating"] = 7

    wd = pd.to_datetime(w["date"], errors="coerce")
    dd = pd.to_datetime(d["date"], errors="coerce")
    hd = pd.to_datetime(h["date"], errors="coerce")
    rating = pd.to_numeric(p["google_review_rating"], errors="coerce")
    rating_all = pd.to_numeric(pa["google_review_rating"], errors="coerce")
    fee = pd.to_numeric(p["entrance_fee_in_inr"], errors="coerce")
    holiday_dates = set(hd.dropna())
    flagged = set(dd[d["is_holiday"].astype(bool)])

    checks = [
        ("Weather dates not empty", wd.notna().all()),
        ("Weather dates not duplicated", wd.is_unique),
        ("Weather has no missing days",
         wd.sort_values().diff().dropna().eq(pd.Timedelta(days=1)).all()),
        ("CSV rainfall not empty or negative",
         w["csv_rainfall_mm"].notna().all() and (w["csv_rainfall_mm"] >= 0).all()),
        ("API rainfall not empty or negative",
         w["api_rainfall_mm"].notna().all() and (w["api_rainfall_mm"] >= 0).all()),
        ("CSV max temperature between 10 and 50 C", w["csv_max_temp_c"].between(10, 50).all()),
        ("CSV and API rainfall agree (mean difference under 1 mm)",
         (w["csv_rainfall_mm"] - w["api_rainfall_mm"]).abs().mean() < 1.0),
        ("Date dimension dates not empty or duplicated", dd.notna().all() and dd.is_unique),
        ("Weather and date dimension cover the same dates", set(wd) == set(dd)),
        ("Holiday dates not empty", hd.notna().all()),
        ("Every holiday date is flagged in the date dimension", holiday_dates <= flagged),
        ("Holiday date+name not duplicated", not h.duplicated(["date", "holiday_name"]).any()),
        ("Goa places found", len(p) > 0),
        ("Goa place names not empty or duplicated", p["name"].notna().all() and p["name"].is_unique),
        ("Goa place ratings between 1.0 and 5.0", rating.between(1, 5).all()),
        ("All place ratings between 1.0 and 5.0", rating_all.between(1, 5).all()),
        ("Entrance fee not negative or empty", fee.notna().all() and (fee >= 0).all()),
    ]
    rep = pd.DataFrame(checks, columns=["rule", "passed"])
    rep["passed"] = rep["passed"].astype(bool)
    rep.to_csv(ROOT / "data" / "quality_report.csv", index=False)
    print(rep.to_string(index=False))
    if not rep["passed"].all():
        print("\nQUALITY CHECK FAILED - pipeline stopped, Gold not loaded")
        sys.exit(1)
    print("\nALL QUALITY CHECKS PASSED")

if __name__ == "__main__":
    main()