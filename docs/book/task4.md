# Task 4

## Neo4j ingestion

Graph topology is written to Neo4j through the Kafka Connect sink configuration stored in `configs/neo4j/sink.properties`.

The sink is configured so that:

- node and edge topics are read separately
- stable IDs are used as merge keys
- repeated replay does not create duplicate graph objects

## Constraints

The repository also includes Cypher constraints in `configs/neo4j/constraints.cypher` so node and edge IDs remain unique.

## Why `MERGE` matters

The replay requirement in the lab means the same file may be parsed more than once.
Using `MERGE` instead of `CREATE` ensures that if the event IDs stay the same, Neo4j updates the existing graph elements rather than duplicating them.

## Report evidence to capture

- Neo4j Browser screenshot
- a query that counts nodes and edges
- a replay run showing the counts stay stable for unchanged events

