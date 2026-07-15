# Task 3

## Kafka topic design

The pipeline uses four Kafka topics:

| Topic | Purpose |
| --- | --- |
| `peft.cpg.nodes` | AST and semantic nodes |
| `peft.cpg.edges` | CFG, DFG, and call edges |
| `peft.source.metadata` | File-level metadata for Spark and MongoDB |
| `peft.parser.errors` | Parse failures and invalid file events |

## Message shape

Each event includes:

- `schema_version`
- `event_time`
- `repo`
- `commit_sha`
- `file_path`
- payload-specific fields such as IDs, counts, or error messages

## Publishing strategy

The repository provides two publisher implementations:

- `ConsolePublisher` for local debugging and tests
- `KafkaPublisher` for real message delivery

The CLI can switch between the two, so the same parser logic works in local development and in the full streaming pipeline.

## Topic creation helper

The script `scripts/create_topics.py` prints `kafka-topics` commands from `configs/kafka/topics.json`, which keeps the topic definitions versioned with the code.

