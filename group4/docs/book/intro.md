# Introduction

This report documents the Lab 04 streaming pipeline built around the selected repository `huggingface/peft`.

The goal of the project is to process Python source code one file at a time, extract a code property graph-style event stream, and route the results into:

- Kafka for event transport
- Neo4j for graph topology
- MongoDB for file-level metadata
- Jupyter Book for the final write-up

The implementation in this repository is intentionally organized around small, testable pieces:

- a parser that can run per file
- a publisher abstraction that can target console output or Kafka
- config helpers for Neo4j and MongoDB
- a replay helper for idempotence checks

The rest of this book explains how those parts fit together and how to run them.

