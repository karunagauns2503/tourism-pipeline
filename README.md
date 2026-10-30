# Goa Tourism Analytics Pipeline

An end-to-end data engineering pipeline for tourism analytics, focused on Goa (2022–2023).

**Team:** Karuna, Saini, Janhavi, Disha

| Member | Responsibility |
|---|---|
| Karuna | Data collection and ingestion (Bronze layer) |
| Saini | Data cleaning and transformation (Silver and Gold layers) |
| Janhavi | Data warehouse design and loading |
| Disha | Orchestration (Airflow) and dashboards |

## Pipeline Overview

```
Data Sources  ->  Ingestion  ->  Bronze (raw)  ->  Silver (clean)  ->  Gold (star schema)  ->  Warehouse  ->  Dashboard
```

This repository currently contains the **ingestion stage**: it brings raw data into the Bronze layer exactly as received, with no cleaning. Cleaning and transformation happen in later stages.

## Data Sources

| Source | Type | Rows | Description |
|---|---|---|---|
| `goa_holidays_2022_2023.csv` | CSV | 45 | Public holidays in Goa, 2022–2023 |
| `goa_weather_2022_2023.csv` | CSV | 730 | Daily maximum temperature (°C) and rainfall (mm) for Goa |
| `Top_Indian_Places_to_Visit.csv` | CSV | 325 | Tourist places across India with ratings, fees and visit details (14 in Goa) |
| Open-Meteo Archive API | API (JSON) | 730 days | Daily max/min temperature and precipitation for Goa |

## Project Structure

```
tourism-pipeline/
├── config/
│   └── config.yaml              # paths and list of CSV sources
├── ingestion/
│   ├── ingest_csv.py            # loads CSV files into Bronze
│   └── ingest_weather_api.py    # pulls weather data from Open-Meteo into Bronze
├── source_data/                 # original CSV files
├── data/raw/                    # Bronze layer (generated, not tracked in Git)
├── logs/                        # ingestion logs (generated, not tracked in Git)
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.9 or later.

```bash
git clone https://github.com/karunagauns2503/tourism-pipeline.git
cd tourism-pipeline

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

## Usage

```bash
python ingestion/ingest_csv.py
python ingestion/ingest_weather_api.py
```

To ingest into a specific date partition:

```bash
python ingestion/ingest_csv.py --run-date 2026-10-29
```

Both scripts expose a `main(run_date=None)` function so they can be called from an Airflow task.

## Ingestion Details

**CSV ingestion** (`ingest_csv.py`) reads the source list from `config/config.yaml`. For each source it copies the file unchanged into the Bronze layer, writes a metadata file, and logs the result to `logs/ingestion.log`. Running it twice on the same date overwrites the same partition, so no duplicates are created.

**Weather API ingestion** (`ingest_weather_api.py`) calls the Open-Meteo archive API (no API key required) for Goa (latitude 15.4909, longitude 73.8278) from 2022-01-01 to 2023-12-31. It retries up to three times on failure and saves the response as-is.

## Bronze Layer

Data is stored in folders partitioned by source and ingestion date:

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

Each `_metadata.json` records the source name, file name, row count, column names, MD5 checksum, ingestion timestamp and Bronze path.

## Data Dictionary

### goa_holidays_2022_2023.csv

| Column | Description |
|---|---|
| `date` | Date of the holiday (YYYY-MM-DD) |
| `holiday_name` | Name of the holiday |
| `state` | State |
| `country` | Country |

### goa_weather_2022_2023.csv

| Column | Description |
|---|---|
| `date` | Date (YYYY-MM-DD) |
| `max_temp_c` | Daily maximum temperature in °C |
| `rainfall_mm` | Daily rainfall in mm |

### Top_Indian_Places_to_Visit.csv

| Column | Description |
|---|---|
| `Unnamed: 0` | Leftover index column |
| `Zone` | Region of India |
| `State` | State |
| `City` | City |
| `Name` | Name of the place |
| `Type` | Category of the place |
| `Establishment Year` | Year established (text, mixed formats) |
| `time needed to visit in hrs` | Typical visit duration in hours |
| `Google review rating` | Google rating |
| `Entrance Fee in INR` | Entry fee in rupees (0 = free) |
| `Airport with 50km Radius` | Whether an airport is within 50 km |
| `Weekly Off` | Weekly closing day |
| `Significance` | Historical, religious, environmental, etc. |
| `DSLR Allowed` | Whether DSLR cameras are allowed |
| `Number of google review in lakhs` | Number of Google reviews, in lakhs |
| `Best Time to visit` | Morning, afternoon or evening |

### goa_weather_api.json

JSON response with a `daily` object containing parallel arrays: `time`, `temperature_2m_max`, `temperature_2m_min` and `precipitation_sum` (730 values each).

## Known Data Issues

The raw data is stored unchanged. These issues are left for the cleaning stage:

| File | Issue |
|---|---|
| places | `Establishment Year` is text with values such as `Unknown`, `Ancient`, `12th century` and `1960s` |
| places | `Weekly Off` is empty in 293 of 325 rows and contains an unclear value `Yes` |
| places | State spelled `Maharastra` instead of `Maharashtra` |
| places | `Unnamed: 0` is a leftover index column |
| places | Typo in a place name: `Dr. Salim Ali Bird Santuary` |
| places | Column names contain spaces and mixed case |
| places | Review counts are in lakhs |
| all | Dates are stored as text |
| weather | CSV and API are two weather sources with slightly different fields and values |

## Scope and Limitations

- The scope is Goa, January 2022 to December 2023.
- The data does not include visitor counts or hotel data, so questions about peak months or domestic versus international trends cannot be answered directly. The Google review count in the places data can be used as a popularity proxy.
- The places data has one row per place and is not time-based, so it relates to the weather and holiday data by location rather than by date.

## Status

| Stage | Status |
|---|---|
| CSV ingestion | Done |
| Weather API ingestion | Done |
| Bronze layer with metadata and logging | Done |
| Cleaning (Silver) | In progress |
| Transformation (Gold) and star schema | Pending |
| Data warehouse loading | Pending |
| Airflow orchestration | Pending |
| Dashboard | Pending |
