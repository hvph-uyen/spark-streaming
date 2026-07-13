from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MongoStreamingSpec:
    master: str = "local[*]"
    app_name: str = "group4-peft-mongo-streaming"
    connection_uri: str = "mongodb://localhost:27017"
    database: str = "lab4"
    collection: str = "peft_metadata"
    checkpoint_location: str = "checkpoints/mongo_streaming"
    input_topic: str = "peft.source.metadata"

    def to_dict(self) -> dict[str, Any]:
        return {
            "spark.master": self.master,
            "spark.app.name": self.app_name,
            "spark.mongodb.write.connection.uri": self.connection_uri,
            "spark.mongodb.write.database": self.database,
            "spark.mongodb.write.collection": self.collection,
            "checkpointLocation": self.checkpoint_location,
            "inputTopic": self.input_topic,
        }


def write_mongo_streaming_spec(path: str | Path, spec: MongoStreamingSpec | None = None) -> Path:
    import json

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps((spec or MongoStreamingSpec()).to_dict(), indent=2), encoding="utf-8")
    return target


def build_spark_streaming_job() -> str:
    return """\
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import *

schema = StructType([
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
])

spark = SparkSession.builder.appName("group4-peft-mongo-streaming").getOrCreate()
raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "peft.source.metadata")
    .option("startingOffsets", "latest")
    .load()
)

parsed = raw.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

(parsed.writeStream
    .format("mongodb")
    .option("uri", "mongodb://localhost:27017")
    .option("database", "lab4")
    .option("collection", "peft_metadata")
    .option("checkpointLocation", "checkpoints/mongo_streaming")
    .outputMode("append")
    .start()
    .awaitTermination())
"""


def spark_job_path(base_dir: str | Path) -> Path:
    base = Path(base_dir)
    target = base / "jobs" / "mongo_streaming_job.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_spark_streaming_job(), encoding="utf-8")
    return target
