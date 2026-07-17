# Task 4

## Neo4j ingestion

Graph topology is written to Neo4j through the Kafka Connect sink configuration stored in `configs/neo4j/sink.properties`.

The sink is configured so that:

- node and edge topics are read separately
- stable IDs are used as merge keys
- repeated replay does not create duplicate graph objects

## Constraints

The repository also includes Cypher constraints in `configs/neo4j/constraints.cypher` so node and edge IDs remain unique.

## Visual evidence

Hai ảnh dưới đây là bằng chứng trực tiếp cho Task 4. Ảnh đầu cho thấy Neo4j đã nhận được các event của graph, còn ảnh thứ hai cho thấy số lượng node/relationship đã thay đổi sau khi Kafka Connect consume dữ liệu từ topic sink. Đây là phần chứng minh rằng nhóm đã thiết lập và chạy được luồng Kafka Connect -> Neo4j thành công.

### Node count

![Neo4j node count query](assets/neo4j-node-count.jpg)

### Relationship count

![Neo4j relationship count query](assets/neo4j-relationship-count.jpg)

Together they show that the graph was populated with real data and that the Neo4j side is receiving the parsed CPG events correctly.

## Why `MERGE` matters

The replay requirement in the lab means the same file may be parsed more than once.
Using `MERGE` instead of `CREATE` ensures that if the event IDs stay the same, Neo4j updates the existing graph elements rather than duplicating them.

