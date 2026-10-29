# Goa Tourism Analytics Pipeline: Data Collection & Ingestion (Bronze Layer)

This README documents the **data collection and ingestion** stage of the team project *End-to-End Data Engineering Pipeline for Tourism Analytics*. It explains what was built, how to run it, what the raw data looks like, and what the next stage (cleaning) should watch out for.

---

## 1. What this stage does

The goal of ingestion is to get raw data from every source into the **Bronze layer** (the raw data lake) **reliably, repeatably and untouched**.

> **Rule of this layer: no cleaning.** Bad rows, typos, nulls and odd values are kept exactly as received. Cleaning happens in the Silver layer (Saini's part). This way the original data is always available for reprocessing.

```
Sources                    Ingestion scripts                 Bronze (data lake)
-----------------------    ------------------------------    -----------------------------------
3 CSV files           -->  ingestion/ingest_csv.py       -->  data/raw/<source>/ingestion_date=YYYY-MM-DD/
Open-Meteo weather API -->  ingestion/ingest_weather_api.py -->  data/raw/weather_api/ingestion_date=YYYY-MM-DD/
```

---

## 2. Project scope

- **Region:** Goa (weather and holidays are Goa-only). The places dataset covers all of India and includes 14 Goa places.
- **Time range:** 1 Jan 2022 to 31 Dec 2023.
- **Storage:** local folder that mimics a data lake. The layout can be moved to S3 / Azure Blob later without changes to the folder structure.

---

## 3. Repository structure

```
tourism-pipeline/
├── config/
│   └── config.yaml              # source folder, bronze folder, log file, list of CSV sources
├── ingestion/
│   ├── ingest_csv.py            # copies the 3 CSVs into Bronze + writes metadata
│   └── ingest_weather_api.py    # pulls Goa daily weather from Open-Meteo into Bronze
├── source_data/                 # the original CSV files (starting point)
│   ├── goa_holidays_2022_2023.csv
│   ├── goa_weather_2022_2023.csv
│   └── Top_Indian_Places_to_Visit.csv
├── data/raw/                    # BRONZE layer (generated; not in Git)
├── logs/                        # ingestion.log (generated; not in Git)
├── requirements.txt
├── .gitignore
└── README.md
```

`data/`, `logs/`, `venv/` and `.env` are listed in `.gitignore`, so they are not uploaded to GitHub. Anyone can regenerate `data/` by running the ingestion scripts.

---

## 4. Step-by-step: what was done

### Step 1: Created the project folder
Created `tourism-pipeline` inside the user's Documents folder (**not** in `C:\Windows\System32`, which is protected and gives "Access denied") with subfolders `ingestion`, `config`, `logs`, `source_data` and `data\raw`.

### Step 2: Placed the source CSVs in `source_data/`
Copied the three provided datasets into `source_data/`. The places file arrived as `Top Indian Places to Visit.csv` (with spaces) and was renamed to `Top_Indian_Places_to_Visit.csv` so the file name matches the config.

### Step 3: Set up the Python environment
```powershell
python -m venv venv
venv\Scripts\activate
pip install pyyaml pandas requests
pip freeze > requirements.txt
```
A virtual environment keeps this project's packages separate from the rest of the machine. `requirements.txt` lets teammates install the same packages.

### Step 4: Wrote the config file (`config/config.yaml`)
All paths and file names live in one config file instead of being hardcoded in the script. Adding a new CSV source later only needs a new entry under `sources:`.

```yaml
source_dir: source_data
bronze_dir: data/raw
log_file: logs/ingestion.log

sources:
  goa_holidays:
    file: goa_holidays_2022_2023.csv
  goa_weather:
    file: goa_weather_2022_2023.csv
  places:
    file: Top_Indian_Places_to_Visit.csv
```

### Step 5: Wrote the CSV ingestion script (`ingestion/ingest_csv.py`)
For each source listed in the config, the script:

1. Checks the source file exists (fails with a clear error if not).
2. Creates the Bronze folder `data/raw/<source>/ingestion_date=<run date>/`.
3. **Copies the file as-is** (the file is not re-saved through pandas, so the raw layer stays truly raw).
4. Reads the copy only to count rows and columns for the log.
5. Writes a `_metadata.json` next to the file (see section 6).
6. Logs the result to the console and to `logs/ingestion.log`.

Design points:
- **Idempotent:** running it twice on the same day overwrites the same folder, so no duplicates are created.
- **Airflow-ready:** the logic is in `main(run_date=None)`, so Disha can call it from an Airflow task and pass a run date. Nothing is hardcoded.
- **Fails loudly:** if any source fails, the error is logged with a traceback and the script stops.

### Step 6: Ran the CSV ingestion and verified it
```powershell
python ingestion\ingest_csv.py
```
Result:

| Source | Rows | Columns |
|---|---|---|
| goa_holidays | 45 | 4 |
| goa_weather | 730 | 3 |
| places | 325 | 16 |

Verified with `tree data /F` that each source has its own folder containing the CSV and `_metadata.json`.

### Step 7: Wrote and ran the weather API script (`ingestion/ingest_weather_api.py`)
Pulls daily historical weather for Goa from the free **Open-Meteo archive API** (no API key needed).

- **Endpoint:** `https://archive-api.open-meteo.com/v1/archive`
- **Location:** latitude 15.4909, longitude 73.8278 (Goa)
- **Date range:** 2022-01-01 to 2023-12-31
- **Daily fields:** `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`
- **Timezone:** `Asia/Kolkata`
- **Reliability:** 30-second timeout and up to 3 retries with increasing wait time.

Result: 730 days of data saved to `data/raw/weather_api/ingestion_date=<date>/goa_weather_api.json` (about 23 KB).

This gives the project its **API source** and also provides a second weather source to cross-check the weather CSV against.

### Step 8: Pushed the code to GitHub
Initialised a Git repo in the project folder, committed the scripts, config, `requirements.txt` and the three CSVs, and pushed to the `main` branch. Raw/generated folders are excluded by `.gitignore`.

---

## 5. How to run everything from scratch

**Prerequisites:** Python 3.9+ and Git.

```powershell
# 1. Get the code
git clone https://github.com/karunagauns2503/tourism-pipeline.git
cd tourism-pipeline

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. Run ingestion (creates data/raw/ and logs/)
python ingestion\ingest_csv.py
python ingestion\ingest_weather_api.py
```

Expected output: `OK` lines for goa_holidays (45 rows), goa_weather (730 rows), places (325 rows) and weather_api (730 days).

To use a specific partition date: `python ingestion\ingest_csv.py --run-date 2026-10-29`

> Open PowerShell **normally** (not as Administrator) or from inside the project folder; otherwise it starts in `C:\Windows\System32`.

---

## 6. Bronze layer layout

```
data/raw/
├── goa_holidays/ingestion_date=YYYY-MM-DD/
│   ├── goa_holidays_2022_2023.csv
│   └── _metadata.json
├── goa_weather/ingestion_date=YYYY-MM-DD/
│   ├── goa_weather_2022_2023.csv
│   └── _metadata.json
├── places/ingestion_date=YYYY-MM-DD/
│   ├── Top_Indian_Places_to_Visit.csv
│   └── _metadata.json
└── weather_api/ingestion_date=YYYY-MM-DD/
    └── goa_weather_api.json
```

Each folder is **partitioned by ingestion date**, the standard Bronze convention. `_metadata.json` contains:

| Field | Meaning |
|---|---|
| `source` | source name from the config |
| `file` | original file name |
| `rows` | number of data rows |
| `columns` | list of column names |
| `md5` | checksum of the file, to detect changes or corruption |
| `ingested_at` | timestamp of ingestion |
| `bronze_path` | where the file was stored |

---

## 7. Data dictionary (raw data)

### 7.1 `goa_holidays_2022_2023.csv`: 45 rows, 4 columns
Public holidays in Goa. Covers 2022-01-26 to 2023-12-25, 25 distinct holiday names.

| Column | Type | Description |
|---|---|---|
| `date` | text (YYYY-MM-DD) | Date of the holiday |
| `holiday_name` | text | Name of the holiday |
| `state` | text | State (Goa) |
| `country` | text | Country (India) |

Quality: no nulls, no duplicates.

### 7.2 `goa_weather_2022_2023.csv`: 730 rows, 3 columns
One row per day, 2022-01-01 to 2023-12-31.

| Column | Type | Description |
|---|---|---|
| `date` | text (YYYY-MM-DD) | Date |
| `max_temp_c` | decimal | Daily maximum temperature in °C (range about 24.6 to 38.1) |
| `rainfall_mm` | decimal | Daily rainfall in mm (max about 102) |

Quality: no nulls, no duplicates. The two years have exactly 730 days, so there are no missing dates.

### 7.3 `Top_Indian_Places_to_Visit.csv`: 325 rows, 16 columns
Tourist places across India (14 of them in Goa), with Google review data. Coverage is by zone: Southern 98, Northern 89, Eastern 45, Western 40, Central 39, North Eastern 14.

| Column | Type | Description |
|---|---|---|
| `Unnamed: 0` | integer | Leftover index column from a previous export |
| `Zone` | text | Region of India (Northern, Southern, etc.) |
| `State` | text | State |
| `City` | text | City |
| `Name` | text | Name of the place |
| `Type` | text | Category (War Memorial, Temple, Theme Park, etc.) |
| `Establishment Year` | **text** | Year built; mixed formats (see issues) |
| `time needed to visit in hrs` | decimal | Typical visit duration in hours |
| `Google review rating` | decimal | Rating on Google |
| `Entrance Fee in INR` | integer | Entry fee in rupees (0 = free) |
| `Airport with 50km Radius` | text | Yes/No: airport within 50 km |
| `Weekly Off` | text | Day the place is closed |
| `Significance` | text | Historical, Religious, Environmental, etc. |
| `DSLR Allowed` | text | Yes/No |
| `Number of google review in lakhs` | decimal | Review count in lakhs (1 lakh = 100,000) |
| `Best Time to visit` | text | Morning / Afternoon / Evening |

The 14 Goa places: Calangute Beach, Basilica of Bom Jesus, Fort Aguada, Dudhsagar Falls, Anjuna Beach, Chapora Fort, Se Cathedral, Baga Beach, Arambol Beach, Palolem Beach, Colva Beach, Miramar Beach, Aguada Beach, Dr. Salim Ali Bird Santuary.

### 7.4 `goa_weather_api.json`: Open-Meteo API response
JSON with a `daily` object holding parallel arrays of 730 values: `time`, `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`. It is stored exactly as the API returned it.

---

## 8. Known data issues (for Saini: found, but NOT fixed in Bronze)

These were found while profiling the raw files. They are intentionally left untouched in Bronze and should be handled in the Silver (cleaning) layer.

| # | File | Issue | Suggested handling |
|---|---|---|---|
| 1 | places | `Establishment Year` is text with values like `Unknown`, `Ancient`, `12th century`, `6th century AD`, `1960s` mixed with plain years | Convert to a numeric year where possible; keep a separate flag/column for approximate or unknown values |
| 2 | places | `Weekly Off` is empty in 293 of 325 rows. Values: Monday 23, Friday 5, Sunday 2, Tuesday 1, and `Yes` 1 | Decide whether empty means "open every day"; treat `Yes` as unclear and flag it |
| 3 | places | State spelled `Maharastra` (missing an "h") | Standardise to `Maharashtra` |
| 4 | places | `Unnamed: 0` is a leftover index column | Drop it |
| 5 | places | Typo in a name: `Dr. Salim Ali Bird Santuary` | Correct to `Sanctuary` |
| 6 | places | Column names have spaces and mixed case | Rename to snake_case, e.g. `google_review_rating` |
| 7 | places | `Number of google review in lakhs` is in lakhs | Convert to a plain count if needed (× 100,000) |
| 8 | all | Dates are plain text | Convert to a proper date type |
| 9 | weather CSV vs API | Two weather sources with different fields and slightly different values | Pick one as the main source, or compare them as a validation check |

Also worth checking in Silver: duplicates and category spelling variations in `Type`, `Significance` and `State`.

---

## 9. Hand-off notes for Saini (Silver layer)

**Where to read from:** `data/raw/<source>/ingestion_date=<date>/` after running the two ingestion scripts. Use the latest `ingestion_date` folder.

**Join keys available:**
- `date` joins weather and holidays (and any future visitor data).
- `State` / `City` joins places to the Goa data. In the places file, Goa places have `City = Goa`.

**Important limitations of the current data:**
- **There is no visitor-count data** and **no hotel data** yet. Without visitor counts, questions about peak season and "do higher-rated places attract more tourists?" cannot be answered directly. `Number of google review in lakhs` can serve as a popularity proxy until a visitor-arrivals dataset is found.
- The places data is **not time-based** (one row per place), so it joins to weather and holidays by Goa location, not by date.

---

## 10. Troubleshooting (problems hit while building this)

| Problem | Cause | Fix |
|---|---|---|
| `mkdir : Access to the path is denied` | PowerShell opened in `C:\Windows\System32` | `cd $HOME\Documents` first, and open PowerShell normally (not as Administrator) |
| `source_dir: : The term ... is not recognized` | YAML text was pasted into the terminal | Create the file with `notepad config\config.yaml` and paste the content there |
| `FileNotFoundError: Source file missing` | CSV name did not match the config (spaces vs underscores) | Rename the file to match the config exactly |
| `git add .` failed with `tourism-pipeline/ does not have a commit checked out` | `git clone` created a nested empty repo inside the project | Delete the nested folder, then use `git init` |
| `src refspec main does not match any` | No commit existed yet | Set `git config user.name/user.email`, commit, then push |

**Git rule of thumb:** `git init` for a project that exists only on your computer; `git clone` for copying an existing GitHub repo.

---

## 11. Team workflow

- Each teammate clones the repo once: `git clone https://github.com/karunagauns2503/tourism-pipeline.git`
- Each person adds their own folder: `transformation/` (Saini), `warehouse/` (Janhavi), `dags/` (Disha).
- Run `git pull` before starting work and before pushing, to avoid conflicts.
- Never commit API keys. Keep them in a `.env` file, which is already git-ignored. (Open-Meteo needs no key.)

---

## 12. Status and next steps

| Item | Status |
|---|---|
| CSV ingestion (3 sources) | Done |
| Weather API ingestion | Done |
| Bronze layer with metadata and logging | Done |
| Code on GitHub | Done |
| Web-scraping source (third source type in the project plan) | **To do** |
| Goa visitor-arrivals dataset | **To find** (needed to answer the core business questions) |
| Hotel data (optional) | To find |
| Airflow wrapper around `main(run_date)` | Disha |
