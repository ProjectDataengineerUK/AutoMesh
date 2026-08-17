from __future__ import annotations

import logging
import os

from delta.tables import DeltaTable
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

BRONZE_BASE_PATH = os.environ.get("BRONZE_BASE_PATH", "data/bronze")
SILVER_BASE_PATH = os.environ.get("SILVER_BASE_PATH", "data/silver")

MERGE_SOURCES = {
    "b3_quotes": "t.ticker = s.ticker AND t.quote_timestamp = s.quote_timestamp",
    "crm_lost_sales": "t.opportunity_id = s.opportunity_id",
}
APPEND_ONLY_SOURCES = ["infra_telemetry", "usage_logs"]
ALL_SOURCES = [*MERGE_SOURCES.keys(), *APPEND_ONLY_SOURCES]


def get_spark() -> SparkSession:
    return SparkSession.builder.appName("automesh-bronze-to-silver").getOrCreate()


def promote_to_silver(spark: SparkSession, source: str, bronze_path: str, silver_path: str) -> int:
    bronze_df = spark.read.format("delta").load(bronze_path)
    row_count = bronze_df.count()

    if source in MERGE_SOURCES:
        if not DeltaTable.isDeltaTable(spark, silver_path):
            bronze_df.write.format("delta").save(silver_path)
            return row_count

        target = DeltaTable.forPath(spark, silver_path)
        (target.alias("t")
            .merge(bronze_df.alias("s"), MERGE_SOURCES[source])
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
        return row_count

    if source in APPEND_ONLY_SOURCES:
        bronze_df.write.format("delta").mode("append").save(silver_path)
        return row_count

    raise ValueError(f"Unknown source for Silver promotion: {source}")


def run(sources: list[str] | None = None) -> dict[str, int]:
    spark = get_spark()
    results: dict[str, int] = {}

    for source in sources or ALL_SOURCES:
        bronze_path = f"{BRONZE_BASE_PATH}/{source}"
        silver_path = f"{SILVER_BASE_PATH}/{source}"
        try:
            results[source] = promote_to_silver(spark, source, bronze_path, silver_path)
        except Exception as e:
            logger.error("Failed to promote %s to Silver: %s", source, e)
            raise

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summary = run()
    logger.info("Bronze->Silver promotion complete: %s", summary)
