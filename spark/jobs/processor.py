"""
processor.py - Silver Layer Processing
=======================================
Reads raw Parquet from Bronze layer (MinIO),
applies validation rules (5+), joins, aggregations, window functions,
writes cleaned data to Silver layer as Hive tables, partitioned by date.

Usage:
    spark-submit /opt/spark-jobs/processor.py \
        --input s3a://datalake/raw \
        --output s3a://datalake/silver \
        --date 2024-01-15
"""

import argparse
import logging
import sys
from datetime import datetime

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("processor")


VALID_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY','DC'
}

VALID_NETWORK_TYPES = {'HMO', 'PPO', 'EPO', 'POS'}


def parse_args():
    parser = argparse.ArgumentParser(description="Silver layer processing")
    parser.add_argument("--input", required=True, help="Bronze input path (s3a://...)")
    parser.add_argument("--output", required=True, help="Silver output path (s3a://...)")
    parser.add_argument("--date", default=None, help="Processing date YYYY-MM-DD")
    return parser.parse_args()


def create_spark_session():
    return (
        SparkSession.builder
        .appName("Processor - Silver Processing")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.sql.warehouse.dir", "s3a://datalake/silver/")
        .config("hive.metastore.uris", "thrift://hive-metastore:9083")
        .enableHiveSupport()
        .getOrCreate()
    )


def apply_validation_rules(plans_df, costs_df):
    """
    Apply 5+ validation rules:
      1. PlanID must be unique and non-null
      2. StateCode must be a valid US state code
      3. IndividualDeductible & IndividualOutOfPocketMax must be positive,
         and IndividualDeductible <= IndividualOutOfPocketMax
      4. NetworkType must be in {HMO, PPO, EPO, POS}
      5. IssuerName must not be null/empty
      6. (bonus) MetalLevel must be a valid value
      7. (bonus) PlanYear must be reasonable (>= 2020)
    """
    log.info("=== Applying Validation Rules ===")

    initial_plans = plans_df.count()
    initial_costs = costs_df.count()
    log.info(f"Initial: plans={initial_plans}, costs={initial_costs}")

    # Rule 1: PlanID unique and non-null
    plans_df = plans_df.filter(F.col("PlanID").isNotNull())
    plans_df = plans_df.dropDuplicates(["PlanID"])
    after_r1 = plans_df.count()
    log.info(f"Rule 1 (PlanID unique/non-null): {initial_plans - after_r1} rejected -> {after_r1}")

    # Rule 2: StateCode valid
    valid_states_lit = F.array(*[F.lit(s) for s in VALID_STATES])
    plans_df = plans_df.filter(F.array_contains(valid_states_lit, F.col("StateCode")))
    after_r2 = plans_df.count()
    log.info(f"Rule 2 (StateCode valid): {after_r1 - after_r2} rejected -> {after_r2}")

    # Rule 4: NetworkType valid
    valid_net_lit = F.array(*[F.lit(n) for n in VALID_NETWORK_TYPES])
    plans_df = plans_df.filter(F.array_contains(valid_net_lit, F.col("NetworkType")))
    after_r4 = plans_df.count()
    log.info(f"Rule 4 (NetworkType valid): {after_r2 - after_r4} rejected -> {after_r4}")

    # Rule 5: IssuerName not null/empty
    plans_df = plans_df.filter(
        F.col("IssuerName").isNotNull() & (F.trim(F.col("IssuerName")) != "")
    )
    after_r5 = plans_df.count()
    log.info(f"Rule 5 (IssuerName non-empty): {after_r4 - after_r5} rejected -> {after_r5}")

    # Rule 6: MetalLevel valid
    valid_metals = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Catastrophic']
    valid_metals_lit = F.array(*[F.lit(m) for m in valid_metals])
    plans_df = plans_df.filter(F.array_contains(valid_metals_lit, F.col("MetalLevel")))
    after_r6 = plans_df.count()
    log.info(f"Rule 6 (MetalLevel valid): {after_r5 - after_r6} rejected -> {after_r6}")

    # Rule 7: PlanYear >= 2020
    plans_df = plans_df.filter(F.col("PlanYear") >= 2020)
    after_r7 = plans_df.count()
    log.info(f"Rule 7 (PlanYear >= 2020): {after_r6 - after_r7} rejected -> {after_r7}")

    # Rule 3: Cost validity (deductible positive, <= OOP max)
    costs_df = costs_df.filter(
        (F.col("IndividualDeductible") >= 0) &
        (F.col("IndividualOutOfPocketMax") > 0) &
        (F.col("IndividualDeductible") <= F.col("IndividualOutOfPocketMax"))
    )
    after_r3 = costs_df.count()
    log.info(f"Rule 3 (cost validity): {initial_costs - after_r3} rejected -> {after_r3}")

    return plans_df, costs_df


def transform_silver(plans_df, costs_df):
    """Join plans and costs, apply window functions, enrichments."""
    log.info("=== Transforming for Silver Layer ===")

    # Cache for reuse (visible in Spark UI)
    plans_df = plans_df.cache()
    costs_df = costs_df.cache()
    log.info(f"Cached plans ({plans_df.count()}) and costs ({costs_df.count()})")

    # Inner join on PlanID
    joined = plans_df.join(costs_df, on="PlanID", how="inner")
    joined = joined.persist()
    log.info(f"Joined dataset: {joined.count()} rows")

    # Window functions
    state_window = Window.partitionBy("StateCode")
    state_metal_window = Window.partitionBy("StateCode", "MetalLevel")
    state_network_window = Window.partitionBy("StateCode", "NetworkType")
    state_deduct_rank = Window.partitionBy("StateCode").orderBy(F.col("IndividualDeductible").asc())

    enriched = (
        joined
        # Rank plans by deductible within each state (cheapest first)
        .withColumn("rank_deductible_state",
                    F.rank().over(state_deduct_rank))
        # Difference from state average deductible
        .withColumn("avg_deductible_state",
                    F.avg("IndividualDeductible").over(state_window))
        .withColumn("diff_from_avg_state_deductible",
                    F.col("IndividualDeductible") - F.col("avg_deductible_state"))
        # Plan count per state
        .withColumn("plan_count_state",
                    F.count("PlanID").over(state_window))
        # Plan count per state and network type
        .withColumn("plan_count_state_network",
                    F.count("PlanID").over(state_network_window))
        # Percentage of network type within state
        .withColumn("pct_network_type_in_state",
                    F.round(
                        F.col("plan_count_state_network") * 100.0 / F.col("plan_count_state"),
                        2
                    ))
        # Average OOP max per state and metal level
        .withColumn("avg_oop_max_state_metal",
                    F.avg("IndividualOutOfPocketMax").over(state_metal_window))
        # Affordability score (lower is more affordable)
        .withColumn("affordability_score",
                    F.col("IndividualDeductible") + F.col("IndividualOutOfPocketMax") * 0.3)
    )

    log.info("Window functions applied")
    return enriched


def write_to_silver(df, output_path, table_name, year, month, day, spark):
    """Write to Silver layer as Hive table partitioned by date."""
    path = f"{output_path}/{table_name}/year={year}/month={month}/day={day}"
    log.info(f"Writing {table_name} to {path}")

    # Add partition columns to dataframe
    df_partitioned = (
        df.withColumn("year", F.lit(year))
          .withColumn("month", F.lit(month))
          .withColumn("day", F.lit(day))
    )

    # Write as Parquet partitioned by date
    (df_partitioned.write
        .mode("overwrite")
        .partitionBy("year", "month", "day")
        .parquet(f"{output_path}/{table_name}"))

    # Register as Hive table
    try:
        spark.sql(f"CREATE DATABASE IF NOT EXISTS silver")
        spark.sql(f"DROP TABLE IF EXISTS silver.{table_name}")
        spark.sql(f"""
            CREATE EXTERNAL TABLE silver.{table_name}
            USING PARQUET
            LOCATION '{output_path}/{table_name}'
        """)
        spark.sql(f"MSCK REPAIR TABLE silver.{table_name}")
        log.info(f"Hive table silver.{table_name} created")
    except Exception as e:
        log.error(f"Hive registration failed (non-fatal): {e}")

    log.info(f"Successfully wrote {table_name} to Silver layer")


def main():
    args = parse_args()

    if args.date:
        proc_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        proc_date = datetime.now()

    year = proc_date.strftime("%Y")
    month = proc_date.strftime("%m")
    day = proc_date.strftime("%d")

    log.info(f"=== PROCESSOR - Silver Processing ===")
    log.info(f"Processing date: {year}-{month}-{day}")

    spark = create_spark_session()
    log.info("Spark session created")

    try:
        # Read from Bronze
        plans_path = f"{args.input}/plans/year={year}/month={month}/day={day}"
        costs_path = f"{args.input}/costs/year={year}/month={month}/day={day}"

        log.info(f"Reading plans from {plans_path}")
        plans_df = spark.read.parquet(plans_path)
        log.info(f"Reading costs from {costs_path}")
        costs_df = spark.read.parquet(costs_path)

        # Apply validation rules
        plans_clean, costs_clean = apply_validation_rules(plans_df, costs_df)

        # Transform with joins/aggregations/window functions
        enriched = transform_silver(plans_clean, costs_clean)

        # Write to Silver
        write_to_silver(enriched, args.output, "plans_enriched", year, month, day, spark)

        log.info("=== PROCESSOR COMPLETE ===")

    except Exception as e:
        log.error(f"Processor failed: {str(e)}")
        raise
    finally:
        spark.stop()
        log.info("Spark session stopped")


if __name__ == "__main__":
    main()
