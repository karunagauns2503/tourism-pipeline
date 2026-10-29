import json, logging, os, time
from datetime import date

import requests

GOA = {"lat": 15.4909, "lon": 73.8278}


def fetch(start="2022-01-01", end="2023-12-31", retries=3):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": GOA["lat"], "longitude": GOA["lon"],
        "start_date": start, "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
    }
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logging.warning("Attempt %d failed: %s", attempt, e)
            time.sleep(2 * attempt)
    raise RuntimeError("Open-Meteo API failed after retries")


def main(run_date=None):
    run_date = run_date or date.today().isoformat()
    data = fetch()
    out_dir = f"data/raw/weather_api/ingestion_date={run_date}"
    os.makedirs(out_dir, exist_ok=True)
    path = f"{out_dir}/goa_weather_api.json"
    with open(path, "w") as f:
        json.dump(data, f)
    logging.info("OK weather_api | days=%d | %s", len(data["daily"]["time"]), path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()