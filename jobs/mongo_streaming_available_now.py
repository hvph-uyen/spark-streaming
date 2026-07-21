from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import IntegerType, LongType, StringType, StructField, StructType


SCHEMA = StructType(
    [
        StructField("schema_version", IntegerType()),
        StructField("event_time", StringType()),
        StructField("repo", StringType()),
        StructField("commit_sha", StringType()),
        StructField("file_path", StringType()),
        StructField("file_size_bytes", LongType()),
        StructField("line_count", LongType()),
        StructField("content_hash", StringType()),
        StructField("ast_node_count", LongType()),
        StructField("ast_edge_count", LongType()),
        StructField("cfg_edge_count", LongType()),
        StructField("dfg_edge_count", LongType()),
        StructField("call_edge_count", LongType()),
        StructField("class_count", LongType()),
        StructField("function_count", LongType()),
        StructField("import_count", LongType()),
    ]
)


def main() -> None:
    checkpoint_location = os.getenv("GROUP4_SPARK_CHECKPOINT", "checkpoints/mongo_streaming_available_now")
    collection = os.getenv("GROUP4_MONGO_COLLECTION", "peft_metadata_spark")
    spark = SparkSession.builder.appName("group4-peft-mongo-available-now").getOrCreate()
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "peft.source.metadata")
        .option("startingOffsets", "earliest")
        .load()
    )
    parsed = raw.select(from_json(col("value").cast("string"), SCHEMA).alias("data")).select("data.*")
    query = (
        parsed.writeStream.format("mongodb")
        .option("checkpointLocation", checkpoint_location)
        .option("spark.mongodb.connection.uri", "mongodb://localhost:27017")
        .option("spark.mongodb.database", "lab4")
        .option("spark.mongodb.collection", collection)
        .option("spark.mongodb.idFieldList", "repo,file_path")
        .option("spark.mongodb.operationType", "replace")
        .option("spark.mongodb.upsertDocument", "true")
        .outputMode("append")
        .trigger(availableNow=True)
        .start()
    )
    query.awaitTermination()
    spark.stop()


if __name__ == "__main__":
    main()
