"""
feeder.py - Bronze Layer Ingestion
===================================
Reads data from MySQL (plans) and PostgreSQL (costs) via JDBC,
writes to MinIO (S3) as Parquet files partitioned by ingestion date.

Usage:
    spark-submit --jars /opt/spark-jars/mysql-connector-j.jar,/opt/spark-jars/postgresql.jar \
        /opt/spark-jobs/feeder.py \
        --mysql-host mysql-source --mysql-port 3306 --mysql-db insurance_plans \
        --pg-host postgres-source --pg-port 5432 --pg-db insurance_costs \
        --output s3a://datalake/raw \
        --date 2024-01-15
"""

import argparse
import logging
import sys
from datetime import datetime

from pyspark.sql import SparkSession

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("feeder")


def parse_args():
    parser = argparse.ArgumentParser(description="Bronze layer ingestion")
    parser.add_argument("--mysql-host", required=True)
    parser.add_argument("--mysql-port", default="3306")
    parser.add_argument("--mysql-db", required=True)
    parser.add_argument("--mysql-user", default="spark")
    parser.add_argument("--mysql-password", default="sparkpass")
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", default="5432")
    parser.add_argument("--pg-db", required=True)
    parser.add_argument("--pg-user", default="spark")
    parser.add_argument("--pg-password", default="sparkpass")
    parser.add_argument("--output", required=True, help="Output path (e.g. s3a://datalake/raw)")
    parser.add_argument("--date", default=None, help="Ingestion date YYYY-MM-DD (default: today)")
    return parser.parse_args()


def create_spark_session():
    return (
        SparkSession.builder
        .appName("Feeder - Bronze Ingestion")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )


def read_mysql(spark, host, port, db, user, password):
    """Read plans table from MySQL via JDBC."""
    url = f"jdbc:mysql://{host}:{port}/{db}?useSSL=false&allowPublicKeyRetrieval=true"
    log.info(f"Reading from MySQL: {url}")

    df = (
        spark.read.format("jdbc")
        .option("url", url)
        .option("dbtable", "plans")
        .option("user", user)
        .option("password", password)
        .option("driver", "com.mysql.cj.jdbc.Driver")
        .load()
    )

    row_count = df.count()
    log.info(f"MySQL plans: {row_count} rows read")
    return df


def read_postgres(spark, host, port, db, user, password):
    """Read costs table from PostgreSQL via JDBC."""
    url = f"jdbc:postgresql://{host}:{port}/{db}"
    log.info(f"Reading from PostgreSQL: {url}")

    df = (
        spark.read.format("jdbc")
        .option("url", url)
        .option("dbtable", "costs")
        .option("user", user)
        .option("password", password)
        .option("driver", "org.postgresql.Driver")
        .load()
    )

    row_count = df.count()
    log.info(f"PostgreSQL costs: {row_count} rows read")
    return df


def write_parquet(df, output_path, table_name, year, month, day):
    """Write DataFrame as Parquet with date partitioning."""
    path = f"{output_path}/{table_name}/year={year}/month={month}/day={day}"
    log.info(f"Writing {table_name} to {path}")

    df.write.mode("overwrite").parquet(path)

    log.info(f"Successfully wrote {table_name} to Bronze layer")


def main():
    args = parse_args()

    # Parse ingestion date
    if args.date:
        ing_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        ing_date = datetime.now()

    year = ing_date.strftime("%Y")
    month = ing_date.strftime("%m")
    day = ing_date.strftime("%d")

    log.info(f"=== FEEDER - Bronze Ingestion ===")
    log.info(f"Ingestion date: {year}-{month}-{day}")

    spark = create_spark_session()
    log.info("Spark session created")

    try:
        # Read from MySQL (Source A: Plans)
        plans_df = read_mysql(
            spark, args.mysql_host, args.mysql_port,
            args.mysql_db, args.mysql_user, args.mysql_password
        )

        # Read from PostgreSQL (Source B: Costs)
        costs_df = read_postgres(
            spark, args.pg_host, args.pg_port,
            args.pg_db, args.pg_user, args.pg_password
        )

        # Write to Bronze layer (MinIO/S3 as Parquet)
        write_parquet(plans_df, args.output, "plans", year, month, day)
        write_parquet(costs_df, args.output, "costs", year, month, day)

        log.info("=== FEEDER COMPLETE ===")

    except Exception as e:
        log.error(f"Feeder failed: {str(e)}")
        raise
    finally:
        spark.stop()
        log.info("Spark session stopped")


if __name__ == "__main__":
    main()
