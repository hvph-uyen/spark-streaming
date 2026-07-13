from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .parser import PythonCPGParser
from .models import ParseResult


@dataclass
class ReplaySummary:
    before_events: int
    after_events: int
    added_events: int
    removed_events: int
    stable_event_ids: int
    changed_file: str
    before_file: str
    after_file: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "before_events": self.before_events,
            "after_events": self.after_events,
            "added_events": self.added_events,
            "removed_events": self.removed_events,
            "stable_event_ids": self.stable_event_ids,
            "changed_file": self.changed_file,
            "before_file": self.before_file,
            "after_file": self.after_file,
            "notes": list(self.notes),
        }


def _event_ids(result: ParseResult) -> set[str]:
    ids = {node.element_id for node in result.nodes}
    ids.update(edge.edge_id for edge in result.edges)
    if result.metadata is not None:
        ids.add(f"metadata:{result.metadata.file_path}")
    if result.error is not None:
        ids.add(f"error:{result.error.file_path}")
    return ids


def compare_parse_results(before: ParseResult, after: ParseResult, changed_file: str, before_file: str, after_file: str) -> ReplaySummary:
    before_ids = _event_ids(before)
    after_ids = _event_ids(after)
    notes: list[str] = []
    if before.error is not None:
        notes.append(f"baseline parse had error: {before.error.error_type}")
    if after.error is not None:
        notes.append(f"replay parse had error: {after.error.error_type}")

    return ReplaySummary(
        before_events=len(before_ids),
        after_events=len(after_ids),
        added_events=len(after_ids - before_ids),
        removed_events=len(before_ids - after_ids),
        stable_event_ids=len(before_ids & after_ids),
        changed_file=changed_file,
        before_file=before_file,
        after_file=after_file,
        notes=notes,
    )


def reprocess_single_file(
    file_path: str | Path,
    repo_root: str | Path | None = None,
    repo_name: str = "huggingface/peft",
    commit_sha: str = "HEAD",
    previous_file_path: str | Path | None = None,
) -> ReplaySummary:
    parser = PythonCPGParser(repo_name=repo_name, commit_sha=commit_sha)
    after_path = Path(file_path)
    before_path = Path(previous_file_path) if previous_file_path is not None else after_path
    if previous_file_path is not None and before_path != after_path:
        try:
            before_text = before_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            before_text = before_path.read_text(encoding="utf-8", errors="replace")
        before = parser.parse_text(before_text, file_path=after_path, repo_root=repo_root)
    else:
        before = parser.parse_file(before_path, repo_root=repo_root)
    after = parser.parse_file(after_path, repo_root=repo_root)
    return compare_parse_results(
        before=before,
        after=after,
        changed_file=str(after_path),
        before_file=str(before_path),
        after_file=str(after_path),
    )
