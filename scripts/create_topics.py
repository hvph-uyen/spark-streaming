from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_topic_spec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Kafka topic creation commands")
    parser.add_argument("--spec", type=Path, default=Path("configs/kafka/topics.json"))
    args = parser.parse_args()

    spec = load_topic_spec(args.spec)
    for topic in spec["topics"]:
        name = topic["name"]
        partitions = topic["partitions"]
        replication_factor = topic["replication_factor"]
        print(
            "kafka-topics --create --topic "
            f"{name} --bootstrap-server localhost:9092 "
            f"--partitions {partitions} --replication-factor {replication_factor}"
        )


if __name__ == "__main__":
    main()

