"""
datamart.py - Gold Layer Datamarts
====================================
Reads cleaned data from Silver layer (Hive),
builds 3 datamarts using Spark SQL:
  - Datamart 1: Accessibilité Financière (Affordability)
  - Datamart 2: Structure de l'Offre (Market Structure)
  - Datamart 3: Compétitivité des Plans (Plan Competitiveness)
Writes results to PostgreSQL service database.

Usage:
    spark-submit /opt/spark-jobs/datamart.py \
        --input s3a://datalake/silver \
        --pg-host postgres-gold --pg-port 5432 --pg-db datamarts \
        --pg-user api --pg-password apipass \
        --date 2024-01-15
"""

import argparse
import logging
import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("datamart")


def parse_args():
    parser = argparse.ArgumentParser(description="Gold layer datamarts")
    parser.add_argument("--input", required=True, help="Silver input path (s3a://...)")
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", default="5432")
    parser.add_argument("--pg-db", required=True)
    parser.add_argument("--pg-user", default="api")
    parser.add_argument("--pg-password", default="apipass")
    parser.add_argument("--date", default=None, help="Processing date YYYY-MM-DD")
    return parser.parse_args()


def create_spark_session():
    return (
        SparkSession.builder
        .appName("Datamart - Gold Layer")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )


def write_to_postgres(df, table_name, pg_host, pg_port, pg_db, pg_user, pg_password):
    """Write DataFrame to PostgreSQL Gold service DB."""
    url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"
    log.info(f"Writing to PostgreSQL: {url} -> {table_name}")

    (df.write.format("jdbc")
        .option("url", url)
        .option("dbtable", table_name)
        .option("user", pg_user)
        .option("password", pg_password)
        .option("driver", "org.postgresql.Driver")
        .mode("overwrite")
        .save())

    log.info(f"Wrote {df.count()} rows to {table_name}")


def build_datamart_affordability(spark, silver_df, year, month, day):
    """
    Datamart 1: Accessibilité Financière
    - Franchise moyenne par état et niveau de plan
    - Coût maximum à charge moyen
    - Comparaison Bronze/Silver/Gold
    """
    log.info("=== Building Datamart 1: Affordability ===")

    silver_df.createOrReplaceTempView("plans_silver")

    df = spark.sql("""
        SELECT
            StateCode,
            MetalLevel,
            COUNT(DISTINCT PlanID) AS num_plans,
            ROUND(AVG(IndividualDeductible), 2) AS avg_individual_deductible,
            ROUND(AVG(FamilyDeductible), 2) AS avg_family_deductible,
            ROUND(AVG(IndividualOutOfPocketMax), 2) AS avg_individual_oop_max,
            ROUND(AVG(FamilyOutOfPocketMax), 2) AS avg_family_oop_max,
            ROUND(MIN(IndividualDeductible), 2) AS min_deductible,
            ROUND(MAX(IndividualDeductible), 2) AS max_deductible,
            ROUND(AVG(affordability_score), 2) AS avg_affordability_score
        FROM plans_silver
        WHERE IsActive = 1
        GROUP BY StateCode, MetalLevel
        ORDER BY StateCode, MetalLevel
    """)

    df = (df
          .withColumn("snapshot_date", F.lit(f"{year}-{month}-{day}"))
          .withColumn("datamart_id", F.lit("DM1_AFFORDABILITY")))

    log.info(f"Datamart 1 ready: {df.count()} rows")
    return df


def build_datamart_market_structure(spark, silver_df, year, month, day):
    """
    Datamart 2: Structure de l'Offre
    - Répartition HMO vs PPO par état
    - Nombre de plans par assureur
    - Diversité des offres par état
    """
    log.info("=== Building Datamart 2: Market Structure ===")

    silver_df.createOrReplaceTempView("plans_silver")

    df = spark.sql("""
        SELECT
            StateCode,
            NetworkType,
            IssuerName,
            COUNT(DISTINCT PlanID) AS num_plans,
            COUNT(DISTINCT MetalLevel) AS metal_diversity,
            ROUND(AVG(pct_network_type_in_state), 2) AS network_share_pct,
            ROUND(AVG(IndividualDeductible), 2) AS avg_deductible,
            COUNT(DISTINCT CountyName) AS county_coverage
        FROM plans_silver
        WHERE IsActive = 1
        GROUP BY StateCode, NetworkType, IssuerName
        HAVING COUNT(DISTINCT PlanID) > 0
        ORDER BY StateCode, NetworkType, num_plans DESC
    """)

    df = (df
          .withColumn("snapshot_date", F.lit(f"{year}-{month}-{day}"))
          .withColumn("datamart_id", F.lit("DM2_MARKET_STRUCTURE")))

    log.info(f"Datamart 2 ready: {df.count()} rows")
    return df


def build_datamart_competitiveness(spark, silver_df, year, month, day):
    """
    Datamart 3: Compétitivité des Plans
    - Taux de co-paiement moyen
    - Services exclus
    - Limites de visites annuelles
    """
    log.info("=== Building Datamart 3: Competitiveness ===")

    silver_df.createOrReplaceTempView("plans_silver")

    df = spark.sql("""
        SELECT
            StateCode,
            MetalLevel,
            NetworkType,
            BenefitCategory,
            COUNT(DISTINCT PlanID) AS num_plans,
            ROUND(AVG(CopayPrimaryCare), 2) AS avg_copay_primary,
            ROUND(AVG(CopaySpecialist), 2) AS avg_copay_specialist,
            ROUND(AVG(CopayER), 2) AS avg_copay_er,
            ROUND(AVG(CopayGenericDrug), 2) AS avg_copay_generic,
            ROUND(AVG(CoinsuranceRate), 4) AS avg_coinsurance_rate,
            SUM(CASE WHEN BenefitCovered = 0 THEN 1 ELSE 0 END) AS num_excluded,
            SUM(CASE WHEN HSAEligible = 1 THEN 1 ELSE 0 END) AS num_hsa_eligible,
            COUNT(DISTINCT Exclusions) AS distinct_exclusions
        FROM plans_silver
        WHERE IsActive = 1
        GROUP BY StateCode, MetalLevel, NetworkType, BenefitCategory
        ORDER BY StateCode, MetalLevel, NetworkType, BenefitCategory
    """)

    df = (df
          .withColumn("snapshot_date", F.lit(f"{year}-{month}-{day}"))
          .withColumn("datamart_id", F.lit("DM3_COMPETITIVENESS")))

    log.info(f"Datamart 3 ready: {df.count()} rows")
    return df


def main():
    args = parse_args()

    if args.date:
        proc_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        proc_date = datetime.now()

    year = proc_date.strftime("%Y")
    month = proc_date.strftime("%m")
    day = proc_date.strftime("%d")

    log.info(f"=== DATAMART - Gold Layer ===")
    log.info(f"Processing date: {year}-{month}-{day}")

    spark = create_spark_session()
    log.info("Spark session created")

    try:
        # Read from Silver
        silver_path = f"{args.input}/plans_enriched/year={year}/month={month}/day={day}"
        log.info(f"Reading silver from {silver_path}")
        silver_df = spark.read.parquet(silver_path)
        silver_df.cache()
        log.info(f"Silver loaded: {silver_df.count()} rows")

        # Build the 3 datamarts
        dm1 = build_datamart_affordability(spark, silver_df, year, month, day)
        dm2 = build_datamart_market_structure(spark, silver_df, year, month, day)
        dm3 = build_datamart_competitiveness(spark, silver_df, year, month, day)

        # Write to PostgreSQL Gold service DB
        write_to_postgres(dm1, "datamart_affordability",
                          args.pg_host, args.pg_port, args.pg_db,
                          args.pg_user, args.pg_password)
        write_to_postgres(dm2, "datamart_market_structure",
                          args.pg_host, args.pg_port, args.pg_db,
                          args.pg_user, args.pg_password)
        write_to_postgres(dm3, "datamart_competitiveness",
                          args.pg_host, args.pg_port, args.pg_db,
                          args.pg_user, args.pg_password)

        log.info("=== DATAMART COMPLETE ===")

    except Exception as e:
        log.error(f"Datamart failed: {str(e)}")
        raise
    finally:
        spark.stop()
        log.info("Spark session stopped")


if __name__ == "__main__":
    main()
