# Group 4 - Lab 04

This repository contains the implementation and report scaffold for Lab 04 on streaming Python source into Kafka, Neo4j, and MongoDB using the selected repository `huggingface/peft`.

## What is included

- Incremental Python parser for CPG-style events
- Kafka event model and publishers
- Neo4j sink config helpers
- MongoDB Spark streaming job and config helpers
- Docker Compose for local infrastructure
- Jupyter Book content for the final report
- Sample code and tests

## Main Commands

Install the package in editable mode:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[all]
```

Discover Python files:

```bash
group4-lab4 discover --repo <path-to-peft>
```

Parse one file:

```bash
group4-lab4 parse-file --file samples/example_module.py
```

Parse the whole repository incrementally:

```bash
group4-lab4 parse-repo --repo <path-to-peft>
```

Compare two versions of a file for replay verification:

```bash
group4-lab4 replay-file --before-file <original.py> --after-file <edited.py>
```

Write the config bundle for Kafka, Neo4j, MongoDB, and Spark:

```bash
group4-lab4 emit-configs --output configs/generated
```

Build the Jupyter Book skeleton:

```bash
group4-lab4 build-book --output docs/book
```

## Repo Layout

- `src/group4_lab/`: parser, publisher, replay, and helper modules
- `configs/`: topic, sink, and streaming configuration
- `jobs/`: executable Spark streaming job
- `docs/book/`: report chapters for Jupyter Book
- `samples/`: sample module used by tests and demos
- `tests/`: automated checks

## Notes

- The parser is incremental at the file level and emits deterministic IDs based on repository, file path, scope, and normalized node content.
- The replay command compares two parses and reports stable, added, and removed event IDs so the idempotence story can be demonstrated in the report.
- The MongoDB job expects Kafka metadata events on `peft.source.metadata`.

