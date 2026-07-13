from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, topic: str, key: str, value: dict[str, Any]) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


class ConsolePublisher(EventPublisher):
    def __init__(self, output: str | Path | None = None) -> None:
        self._path = Path(output) if output else None
        self._fh = self._path.open("a", encoding="utf-8") if self._path else None

    def publish(self, topic: str, key: str, value: dict[str, Any]) -> None:
        record = {"topic": topic, "key": key, "value": value}
        line = json.dumps(record, ensure_ascii=False)
        if self._fh:
            self._fh.write(line + "\n")
            self._fh.flush()
        else:
            print(line)

    def close(self) -> None:
        if self._fh:
            self._fh.close()


class KafkaPublisher(EventPublisher):
    def __init__(self, bootstrap_servers: str = "localhost:9092") -> None:
        try:
            from kafka import KafkaProducer
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Kafka support requires the 'kafka-python' package. Install with .[kafka]."
            ) from exc

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda payload: json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8"),
            acks="all",
            linger_ms=10,
            retries=5,
        )

    def publish(self, topic: str, key: str, value: dict[str, Any]) -> None:
        self._producer.send(topic, key=key, value=value)

    def flush(self) -> None:
        self._producer.flush()

    def close(self) -> None:
        self._producer.close()


def build_publisher(kind: str, output: str | Path | None = None, bootstrap_servers: str = "localhost:9092") -> EventPublisher:
    if kind == "console":
        return ConsolePublisher(output=output)
    if kind == "kafka":
        return KafkaPublisher(bootstrap_servers=bootstrap_servers)
    raise ValueError(f"Unsupported publisher kind: {kind}")

