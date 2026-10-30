from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


PROJECT_DIR = "/opt/airflow/tourism-pipeline"


with DAG(
    dag_id="tourism_pipeline",
    start_date=datetime(2026, 10, 30),
    schedule=None,
    catchup=False,
    tags=["tourism", "data-engineering"],
) as dag:

    ingest_csv = BashOperator(
        task_id="ingest_csv",
        bash_command=f"cd {PROJECT_DIR} && python ingestion/ingest_csv.py",
    )

    ingest_weather_api = BashOperator(
        task_id="ingest_weather_api",
        bash_command=f"cd {PROJECT_DIR} && python ingestion/ingest_weather_api.py",
    )

    clean_holidays = BashOperator(
        task_id="clean_holidays",
        bash_command=f"cd {PROJECT_DIR} && python transformation/clean_holidays.py",
    )

    clean_weather = BashOperator(
        task_id="clean_weather",
        bash_command=f"cd {PROJECT_DIR} && python transformation/clean_weather.py",
    )

    clean_places = BashOperator(
        task_id="clean_places",
        bash_command=f"cd {PROJECT_DIR} && python transformation/clean_places.py",
    )

    load_gold = BashOperator(
        task_id="load_gold",
        bash_command=f"cd {PROJECT_DIR}/warehouse && python load_gold.py",
    )

    quality_checks = BashOperator(
        task_id="quality_checks",
        bash_command=f"cd {PROJECT_DIR}/warehouse && python quality_checks.py",
    )

    ingest_csv >> ingest_weather_api
    ingest_weather_api >> [clean_holidays, clean_weather, clean_places]
    [clean_holidays, clean_weather, clean_places] >> load_gold
    load_gold >> quality_checks