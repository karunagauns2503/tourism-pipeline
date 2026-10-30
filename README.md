# Transformation (Silver layer)

This is the second stage of our Goa tourism pipeline. Karuna's ingestion scripts drop raw files into the Bronze layer. The scripts in this folder read those files, clean them, and write tidy tables to the Silver layer. Janhavi builds the warehouse from these tables.

Bronze stays untouched. Everything here reads from `data/raw/` and writes to `data/silver/`.

## What goes in and what comes out

| Bronze source | Silver file | Rows |
|---|---|---|
| places (CSV) | `places_clean.parquet` | 325 |
| places (CSV) | `places_goa.parquet` (Goa only) | 14 |
| goa_weather (CSV) + weather_api (JSON) | `fact_weather_daily.parquet` | 730 |
| goa_holidays (CSV) | `holidays_clean.parquet` | 45 |
| goa_holidays (CSV) | `dim_date.parquet` | 730 |

## How to run it

Run the ingestion scripts first, because `data/` is not on GitHub.

```bash
git clone https://github.com/karunagauns2503/tourism-pipeline.git
cd tourism-pipeline
git checkout transformation

python -m venv venv
source venv/Scripts/activate      # Git Bash. In PowerShell: venv\Scripts\activate
pip install -r requirements.txt
pip install pyarrow

python ingestion/ingest_csv.py
python ingestion/ingest_weather_api.py

python transformation/clean_places.py
python transformation/clean_weather.py
python transformation/clean_holidays.py
python transformation/check_silver.py
```

`check_silver.py` should print `OK` for all five files. Every script writes to `logs/transformation.log`. Each one reads the newest `ingestion_date` folder in Bronze, and the Silver folder comes from `silver_dir` in `config/config.yaml`.

## What each script does

### clean_places.py

- Drops the leftover `Unnamed: 0` column.
- Renames every column to snake_case (`Google review rating` becomes `google_review_rating`).
- Trims extra spaces in the text columns.
- Fixes the spelling `Maharastra` to `Maharashtra`. This brought the state count from 33 down to 32.
- Fixes `Santuary` to `Sanctuary` in place names.
- Turns `establishment_year` into a number and keeps the original text in `establishment_year_raw`. Details below.
- Fills the empty `weekly_off` values with `Not specified`.
- Adds an `is_goa` flag and saves the 14 Goa places as a separate file.
- Removes duplicate rows. There were none, so 325 rows in and 325 out.

**Establishment year rules**

- Plain numbers become years, so `1572` is 1572.
- Negative numbers are BCE years, so `-400` means 400 BCE.
- `1960s` becomes 1960.
- These stay empty because they don't hold a single year: `Unknown`, `Ancient`, and the centuries (`6th century AD`, `7th century`, `10th century`, `11th century`, `12th century`, `14th century`, `16th century`).

### clean_weather.py

- Converts dates to a real date type and checks there is one row per day.
- Flags bad values (negative rain, max temperature under 10 or over 50). Those rows would go to `weather_rejects.csv` and not get deleted.
- Flattens the API JSON into one row per day.
- Joins the CSV and the API on date. Columns are prefixed `csv_` and `api_` so you can tell them apart.
- Logs how far apart the two sources are. The CSV has no minimum temperature, the API does.

The log says the average difference in max temperature is [fill in] C and in rainfall [fill in] mm per day.

### clean_holidays.py

- Converts dates and removes duplicates.
- Builds `dim_date`, one row for every day from 2022-01-01 to 2023-12-31.

`dim_date` columns: `date`, `year`, `quarter`, `month`, `month_name`, `day`, `weekday`, `is_weekend`, `season`, `holiday_name`, `is_holiday`.

Seasons are Winter (Dec to Feb), Summer (Mar to May), Monsoon (Jun to Sep) and Post-monsoon (Oct to Nov). If two holidays fall on the same date, the names are joined with a semicolon. There are 45 holiday days in total.

## Silver tables

### places_clean and places_goa (17 columns)

Both files have the same columns. `places_goa` only keeps the rows where `is_goa` is true.

| Column | Type | Description | Changed from Bronze |
|---|---|---|---|
| `zone` | text | Region of India (Northern, Southern, etc.) | Renamed, spaces trimmed |
| `state` | text | State | `Maharastra` fixed to `Maharashtra` |
| `city` | text | City | Spaces trimmed |
| `name` | text | Name of the place | `Santuary` fixed to `Sanctuary` |
| `type` | text | Category (Temple, Beach, Fort, etc.) | Spaces trimmed |
| `establishment_year` | integer, can be empty | Year built. Negative means BCE | Was text, now numeric |
| `time_needed_to_visit_in_hrs` | decimal | Usual visit time in hours | Renamed only |
| `google_review_rating` | decimal | Google rating | Renamed only |
| `entrance_fee_in_inr` | integer | Entry fee in rupees, 0 means free | Renamed only |
| `airport_with_50km_radius` | text | Yes or No, airport within 50 km | Renamed only |
| `weekly_off` | text | Day the place is closed | Empty values became `Not specified` |
| `significance` | text | Historical, Religious, Environmental, etc. | Renamed only |
| `dslr_allowed` | text | Yes or No | Renamed only |
| `number_of_google_review_in_lakhs` | decimal | Review count in lakhs (1 lakh = 100,000) | Renamed only |
| `best_time_to_visit` | text | Morning, Afternoon or Evening | Renamed only |
| `establishment_year_raw` | text | The original year text, kept as received | New column |
| `is_goa` | true/false | True when the state is Goa | New column |

The Bronze column `Unnamed: 0` is dropped, so 16 columns become 15, plus the two new ones.

### fact_weather_daily (6 columns)

One row per day.

| Column | Type | Description |
|---|---|---|
| `date` | date | Day. Joins to `dim_date` |
| `csv_max_temp_c` | decimal | Max temperature in C, from the weather CSV |
| `csv_rainfall_mm` | decimal | Rainfall in mm, from the weather CSV |
| `api_max_temp_c` | decimal | Max temperature in C, from Open-Meteo |
| `api_min_temp_c` | decimal | Min temperature in C, from Open-Meteo |
| `api_rainfall_mm` | decimal | Rainfall in mm, from Open-Meteo |

### holidays_clean (4 columns)

| Column | Type | Description |
|---|---|---|
| `date` | date | Date of the holiday |
| `holiday_name` | text | Name of the holiday. Some rows hold two names separated by a semicolon |
| `state` | text | Goa |
| `country` | text | India |

### dim_date (11 columns)

One row for every day from 2022-01-01 to 2023-12-31.

| Column | Type | Description |
|---|---|---|
| `date` | date | Day. Primary key |
| `year` | integer | 2022 or 2023 |
| `quarter` | integer | 1 to 4 |
| `month` | integer | 1 to 12 |
| `month_name` | text | January, February, etc. |
| `day` | integer | Day of the month |
| `weekday` | text | Monday to Sunday |
| `is_weekend` | true/false | True for Saturday and Sunday |
| `season` | text | Winter, Summer, Monsoon or Post-monsoon |
| `holiday_name` | text | Holiday on that day, empty if none |
| `is_holiday` | true/false | True when there is a holiday |

## Things to know

- `date` is the join key between the weather table, the holidays and `dim_date`.
- The places table has no date. It only connects to the rest through the state, so Goa places are the ones where `is_goa` is true.
- `weekly_off` still contains one odd value, `Yes`. I left it as it was.
- Some places have no usable year, so `establishment_year` has nulls. Use `establishment_year_raw` if you need the original text.
- There is still no visitor or hotel data. Until we find some, `number_of_google_review_in_lakhs` is the closest thing to a popularity measure.
- `data/` and `logs/` are in `.gitignore`. Run the scripts to regenerate everything.

## Folder

```
transformation/
├── clean_places.py
├── clean_weather.py
├── clean_holidays.py
└── check_silver.py
```
