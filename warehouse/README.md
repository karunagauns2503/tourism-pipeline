\# Data Warehouse Design and Loading (Gold Layer)



Part of the Goa Tourism Analytics Pipeline. This stage loads the cleaned Silver data into a DuckDB star schema, checks data quality before loading, and creates SQL views for the dashboard.



\## 1. What this stage does

Reads the Silver files made by the transformation stage, runs 17 quality rules, and builds the Gold database `data/gold/goa\_tourism.duckdb`. If any rule fails, the pipeline stops and Gold is not loaded.



\## 2. Files

| File | Purpose |

|---|---|

| `warehouse/common.py` | shared paths, rain categories, date key |

| `warehouse/quality\_checks.py` | 17 data quality rules |

| `warehouse/load\_gold.py` | builds the star schema and the views |

| `sql/analysis\_queries.sql` | the 5 analysis views as SQL |



\## 3. How to run

Run the ingestion and transformation scripts first, then:

```

python warehouse/quality\_checks.py

python warehouse/load\_gold.py

```

Failure demo (injects bad data, the pipeline must stop):

```

python warehouse/quality\_checks.py --demo-fail

```



\## 4. Star schema

!\[Star schema](images/star\_schema.drawio.png)



| Table | Rows | Description |

|---|---|---|

| `fact\_daily\_weather` | 730 | one row per day: temperature and rainfall (CSV is the main source, API kept as a cross-check) |

| `dim\_date` | 730 | year, month, season, weekend, holiday and long-weekend flags |

| `dim\_rain\_category` | 3 | Dry (below 2.5 mm), Light Rain (2.5 to 30 mm), Heavy Monsoon (30 mm and above) |

| `dim\_place` | 14 | Goa places with rating, fee, review count, outdoor flag |



Grain of the fact table: one row per day. `dim\_place` has no date, so it stands alone until visitor data is added.



\## 5. Data quality

17 rules, including: dates not empty, duplicated or missing; rainfall not negative; temperature between 10 and 50 C; CSV and API rainfall agree; holidays flagged in the date table; place names unique; ratings between 1 and 5; entrance fee not negative.



Passing run:

!\[Quality pass](images/1_warehouse_quality_checks.png)



Failure demo (rainfall of -5 and a rating of 7 were caught):

!\[Quality fail](images/2_demo_fail.png)



\## 6. Loading

!\[Gold load](images/3_Gold_load_output.png)



The database is rebuilt on every run, so runs are repeatable and create no duplicates.



\## 7. Analysis views

`v\_monthly\_weather`, `v\_season\_weather`, `v\_holiday\_weather`, `v\_holidays\_by\_rain`, `v\_place\_summary`



!\[Views](images/4_four_view_outputs.png)



Key results:

\- Monsoon days average 18.4 mm of rain, against 0.15 mm in winter.

\- July 2023 was the wettest month (1,268 mm).

\- 29 of 45 holiday days were dry, 13 had light rain and 3 fell on heavy-rain days.

\- 12 of 14 Goa places are outdoor (average rating 4.37); the 2 indoor places average 4.50 (too few to compare).



\## 8. Version control

Work is on branch `janhavi-gold` (pull request #1).



!\[Pull request](images/5_GitHub_pull_request_page.png)



\## 9. Limitations

There is no visitor or hotel data yet, so this warehouse describes weather, holidays and places, not demand. A visitor fact table can be added later and joined to `dim\_date`.

