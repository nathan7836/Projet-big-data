"""
insurance_pipeline.py - DAG Airflow pour le pipeline Big Data
==============================================================
Orchestre les 3 etapes du pipeline Medallion :
  1. Feeder   (Bronze) : MySQL + PostgreSQL -> MinIO (Parquet)
  2. Processor (Silver) : Validation + Jointures + Window -> MinIO
  3. Datamart  (Gold)   : Aggregations -> PostgreSQL Gold

Execution quotidienne a 6h UTC.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# ── Config ──────────────────────────────────────────────────
SPARK_SUBMIT = (
    "docker exec spark-master /opt/spark/bin/spark-submit "
    "--master spark://spark-master:7077 "
)

TODAY = "{{ ds }}"  # Airflow macro: YYYY-MM-DD

default_args = {
    "owner": "bigdata-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ── DAG ─────────────────────────────────────────────────────
with DAG(
    dag_id="insurance_pipeline",
    default_args=default_args,
    description="Pipeline Medallion : Bronze -> Silver -> Gold pour US Health Insurance",
    schedule_interval="0 6 * * *",  # Quotidien a 6h UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["bigdata", "insurance", "medallion"],
) as dag:

    # ── Bronze: Feeder ──────────────────────────────────────
    feeder = BashOperator(
        task_id="feeder_bronze",
        bash_command=(
            f"{SPARK_SUBMIT} "
            "/opt/spark-jobs/feeder.py "
            "--mysql-host mysql-source --mysql-port 3306 --mysql-db insurance_plans "
            "--mysql-user spark --mysql-password sparkpass "
            "--pg-host postgres-source --pg-port 5432 --pg-db insurance_costs "
            "--pg-user spark --pg-password sparkpass "
            f"--output s3a://datalake/raw --date {TODAY} "
        ),
        doc="Ingestion Bronze : lecture JDBC MySQL + PostgreSQL, ecriture Parquet dans MinIO",
    )

    # ── Silver: Processor ───────────────────────────────────
    processor = BashOperator(
        task_id="processor_silver",
        bash_command=(
            f"{SPARK_SUBMIT} "
            "/opt/spark-jobs/processor.py "
            f"--input s3a://datalake/raw --output s3a://datalake/silver --date {TODAY} "
        ),
        doc="Traitement Silver : 7 regles de validation, jointures, fonctions de fenetre",
    )

    # ── Gold: Datamart ──────────────────────────────────────
    datamart = BashOperator(
        task_id="datamart_gold",
        bash_command=(
            f"{SPARK_SUBMIT} "
            "/opt/spark-jobs/datamart.py "
            "--input s3a://datalake/silver "
            "--pg-host postgres-gold --pg-port 5432 --pg-db datamarts "
            f"--pg-user api --pg-password apipass --date {TODAY} "
        ),
        doc="Couche Gold : 3 datamarts (Affordability, Market Structure, Competitiveness) -> PostgreSQL",
    )

    # ── Dependencies ────────────────────────────────────────
    feeder >> processor >> datamart
