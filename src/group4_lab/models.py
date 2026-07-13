from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class SourceSpan:
    lineno: int | None = None
    col_offset: int | None = None
    end_lineno: int | None = None
    end_col_offset: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CPGNodeEvent:
    schema_version: int
    event_time: str
    repo: str
    commit_sha: str
    file_path: str
    element_id: str
    kind: str
    qualname: str
    label: str
    span: SourceSpan
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["span"] = self.span.to_dict()
        return data


@dataclass
class CPGEdgeEvent:
    schema_version: int
    event_time: str
    repo: str
    commit_sha: str
    file_path: str
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MetadataEvent:
    schema_version: int
    event_time: str
    repo: str
    commit_sha: str
    file_path: str
    file_size_bytes: int
    line_count: int
    content_hash: str
    ast_node_count: int
    ast_edge_count: int
    cfg_edge_count: int
    dfg_edge_count: int
    call_edge_count: int
    class_count: int
    function_count: int
    import_count: int
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParserErrorEvent:
    schema_version: int
    event_time: str
    repo: str
    commit_sha: str
    file_path: str
    error_type: str
    message: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParseResult:
    nodes: list[CPGNodeEvent] = field(default_factory=list)
    edges: list[CPGEdgeEvent] = field(default_factory=list)
    metadata: MetadataEvent | None = None
    error: ParserErrorEvent | None = None

    def all_events(self) -> list[tuple[str, str, dict[str, Any]]]:
        events: list[tuple[str, str, dict[str, Any]]] = []
        for node in self.nodes:
            events.append(("peft.cpg.nodes", node.element_id, node.to_dict()))
        for edge in self.edges:
            events.append(("peft.cpg.edges", edge.edge_id, edge.to_dict()))
        if self.metadata is not None:
            events.append(("peft.source.metadata", self.metadata.file_path, self.metadata.to_dict()))
        if self.error is not None:
            events.append(("peft.parser.errors", self.error.file_path, self.error.to_dict()))
        return events
