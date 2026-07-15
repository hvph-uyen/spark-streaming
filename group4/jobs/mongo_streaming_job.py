from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)


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
    spark = SparkSession.builder.appName("group4-peft-mongo-streaming").getOrCreate()
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "peft.source.metadata")
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = raw.select(from_json(col("value").cast("string"), SCHEMA).alias("data")).select("data.*")

    (
        parsed.writeStream.format("mongodb")
        .option("uri", "mongodb://localhost:27017")
        .option("database", "lab4")
        .option("collection", "peft_metadata")
        .option("checkpointLocation", "checkpoints/mongo_streaming")
        .outputMode("append")
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
