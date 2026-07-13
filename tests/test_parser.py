from pathlib import Path

from group4_lab.discovery import discover_python_files
from group4_lab.parser import PythonCPGParser
from group4_lab.replay import reprocess_single_file


def test_discovery_skips_tests() -> None:
    files = discover_python_files(Path("."), include_tests=False)
    assert all("tests" not in path.parts for path in files)


def test_parse_sample_module() -> None:
    parser = PythonCPGParser(repo_name="group4/sample", commit_sha="test")
    result = parser.parse_file(Path("samples/example_module.py"))
    assert result.metadata is not None
    assert len(result.nodes) > 0
    assert len(result.edges) > 0
    assert result.metadata.function_count >= 2


def test_repository_iter_matches_list() -> None:
    parser = PythonCPGParser(repo_name="group4/sample", commit_sha="test")
    list_results = parser.parse_repository(Path("."), include_tests=False)
    iter_results = list(parser.parse_repository_iter(Path("."), include_tests=False))
    assert len(list_results) == len(iter_results)


def test_replay_same_file_is_stable() -> None:
    summary = reprocess_single_file(Path("samples/example_module.py"), repo_root=Path("."))
    assert summary.before_events == summary.after_events
    assert summary.added_events == 0
    assert summary.removed_events == 0
    assert summary.stable_event_ids == summary.before_events
