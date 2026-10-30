# Goa Tourism Analytics Pipeline: Data Collection and Ingestion

**Role in the project:** Data collection and ingestion (Bronze layer)

This is part of the team project *End-to-End Data Engineering Pipeline for Tourism Analytics*. This README covers only the data collection and ingestion stage, which brings raw tourism data into the Bronze (raw) layer of the data lake exactly as received, with no cleaning. Later stages of the pipeline (cleaning, transformation, warehouse, orchestration and dashboards) are handled by other team members.

## Contribution Summary

- Collected and organised the source datasets for Goa tourism (January 2022 to December 2023)
- Built a config-driven Python script that ingests CSV files into the Bronze layer
- Built a Python script that pulls daily weather data from the Open-Meteo API with retries and timeouts
- Designed the Bronze layer: folders partitioned by source and ingestion date, with a metadata file for every source
- Added logging for every run
- Wrote both scripts as functions (`main(run_date)`) so they can be scheduled by Airflow
- Profiled the raw data and documented its structure and quality issues for the cleaning stage
- Set up the GitHub repository and the project folder structure

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

## How the Ingestion Works

**CSV ingestion** (`ingestion/ingest_csv.py`)
1. Reads the list of sources from `config/config.yaml`.
2. Checks that each source file exists.
3. Copies the file unchanged into `data/raw/<source>/ingestion_date=<date>/`.
4. Writes a `_metadata.json` file next to it.
5. Logs the result to the console and to `logs/ingestion.log`.

Running it twice on the same date overwrites the same partition, so no duplicates are created. Adding a new CSV source only needs a new entry in the config file.

**Weather API ingestion** (`ingestion/ingest_weather_api.py`)
- Calls the Open-Meteo archive API (no API key required) for Goa (latitude 15.4909, longitude 73.8278) from 2022-01-01 to 2023-12-31.
- Requests daily `temperature_2m_max`, `temperature_2m_min` and `precipitation_sum`.
- Uses a 30-second timeout and up to three retries on failure.
- Saves the response as-is to `data/raw/weather_api/ingestion_date=<date>/goa_weather_api.json`.

## Bronze Layer

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

## Setup and Usage

Requires Python 3.9 or later.

```bash
git clone https://github.com/karunagauns2503/tourism-pipeline.git
cd tourism-pipeline

python -m venv venv
venv\Scripts\activate          # Windows

pip install -r requirements.txt

python ingestion/ingest_csv.py
python ingestion/ingest_weather_api.py
```

To ingest into a specific date partition:

```bash
python ingestion/ingest_csv.py --run-date 2026-10-29
```

Expected result: the CSV script reports 45, 730 and 325 rows for the three sources, and the API script reports 730 days.

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

## Data Quality Findings (Handed Over for Cleaning)

The raw data is stored unchanged. These issues were found while profiling the files and are left for the cleaning stage:

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
| weather | The CSV and the API are two weather sources with slightly different fields and values |

## Scope and Limitations

- The scope is Goa, January 2022 to December 2023.
- The data does not include visitor counts or hotel data, so questions about peak months or domestic versus international trends cannot be answered directly from it. The Google review count in the places data can be used as a popularity proxy.
- The places data has one row per place and is not time-based, so it relates to the weather and holiday data by location rather than by date.
