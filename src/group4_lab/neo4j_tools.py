from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import CPGEdgeEvent, CPGNodeEvent


@dataclass
class Neo4jSinkSpec:
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password123"

    def to_properties(self) -> str:
        return "\n".join(
            [
                "name=group4-peft-neo4j-sink",
                "topics=peft.cpg.nodes,peft.cpg.edges",
                "connector.class=streams.kafka.connect.sink.Neo4jSinkConnector",
                "key.converter=org.apache.kafka.connect.storage.StringConverter",
                "value.converter=org.apache.kafka.connect.json.JsonConverter",
                "value.converter.schemas.enable=false",
                "errors.tolerance=all",
                "errors.log.enable=true",
                "errors.log.include.messages=true",
                f"neo4j.server.uri={self.uri}",
                f"neo4j.authentication.basic.username={self.username}",
                f"neo4j.authentication.basic.password={self.password}",
            ]
        )


def write_sink_properties(path: str | Path, spec: Neo4jSinkSpec | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text((spec or Neo4jSinkSpec()).to_properties(), encoding="utf-8")
    return target


def neo4j_constraints_cypher() -> str:
    return """\
CREATE CONSTRAINT cpg_node_id IF NOT EXISTS
FOR (n:CPGNode)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT cpg_edge_id IF NOT EXISTS
FOR ()-[r:CPG_EDGE]-()
REQUIRE r.id IS UNIQUE;
"""


def node_to_neo4j_record(node: CPGNodeEvent) -> dict[str, Any]:
    return {
        "event": {
            "element_id": node.element_id,
            "kind": node.kind,
            "file_path": node.file_path,
            "repo": node.repo,
            "commit_sha": node.commit_sha,
            "properties": node.properties,
        }
    }


def edge_to_neo4j_record(edge: CPGEdgeEvent) -> dict[str, Any]:
    return {
        "event": {
            "edge_id": edge.edge_id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "edge_type": edge.edge_type,
            "file_path": edge.file_path,
            "repo": edge.repo,
            "commit_sha": edge.commit_sha,
            "properties": edge.properties,
        }
    }
