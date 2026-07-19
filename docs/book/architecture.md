# Architecture Diagram

## System Architecture

```mermaid
flowchart LR
    source["Source code files<br/>PEFT repository (*.py)"]
    discovery["File Discovery<br/>discover_python_files()"]
    cli["Parser CLI<br/>group4-lab4 parse-repo"]
    parser["Python CPG Parser<br/>parser.py<br/>AST / CFG / DFG / CALL extraction"]
    result["ParseResult<br/>nodes + edges + metadata + errors"]
    publisher["Kafka Publisher<br/>publisher.py"]

    subgraph kafka["Kafka"]
        topicNodes["Topic: peft.cpg.nodes<br/>CPG node events"]
        topicEdges["Topic: peft.cpg.edges<br/>AST_CHILD / CFG / DFG / CALLS"]
        topicMetadata["Topic: peft.source.metadata<br/>file metadata"]
        topicErrors["Topic: peft.parser.errors<br/>parser error events"]
    end

    subgraph neo4jPath["Graph Sink"]
        connect["Kafka Connect<br/>Neo4j Sink Connector"]
        neo4j["Neo4j<br/>CPGNode vertices<br/>CPG_EDGE relationships"]
    end

    subgraph sparkPath["Metadata Streaming Sink"]
        spark["Spark Structured Streaming<br/>jobs/mongo_streaming_job.py"]
        checkpoint["Checkpoint<br/>checkpoints/mongo_streaming"]
        mongo["MongoDB<br/>Database: lab4<br/>Collection: peft_metadata"]
    end

    source --> discovery --> cli --> parser --> result --> publisher

    publisher --> topicNodes
    publisher --> topicEdges
    publisher --> topicMetadata
    publisher --> topicErrors

    topicNodes --> connect
    topicEdges --> connect
    connect --> neo4j

    topicMetadata --> spark
    spark --> checkpoint
    spark --> mongo
```

## Data Flow

1. PEFT source code is scanned one Python file at a time.
2. The parser reads each file with Python `ast` and extracts CPG data: AST nodes, CFG edges, DFG edges, and call edges.
3. Events are published to Kafka by event type.
4. `peft.cpg.nodes` and `peft.cpg.edges` are consumed by Kafka Connect and written to Neo4j.
5. `peft.source.metadata` is consumed by Spark Structured Streaming and written to MongoDB.
6. `peft.parser.errors` stores parse failures for monitoring and debugging.
