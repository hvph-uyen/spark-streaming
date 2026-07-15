from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .discovery import discover_python_files, summarize_python_files
from .mongo_streaming import MongoStreamingSpec, spark_job_path, write_mongo_streaming_spec
from .neo4j_tools import Neo4jSinkSpec, neo4j_constraints_cypher, write_sink_properties
from .parser import PythonCPGParser
from .replay import reprocess_single_file
from .publisher import build_publisher


def _write_jsonl(path: Path, records: list[tuple[str, str, dict]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for topic, key, value in records:
            fh.write(json.dumps({"topic": topic, "key": key, "value": value}, ensure_ascii=False) + "\n")


def _emit_json(payload: object) -> None:
    sys.stdout.buffer.write(json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8") + b"\n")


def cmd_discover(args: argparse.Namespace) -> None:
    files = discover_python_files(args.repo, include_tests=args.include_tests)
    summary = summarize_python_files(files, args.repo)
    _emit_json(summary)


def cmd_parse_file(args: argparse.Namespace) -> None:
    parser = PythonCPGParser(repo_name=args.repo_name, commit_sha=args.commit_sha)
    result = parser.parse_file(args.file, repo_root=args.repo_root)
    records = result.all_events()
    if args.output:
        _write_jsonl(Path(args.output), records)
    else:
        publisher = build_publisher(args.publisher, output=args.publisher_output, bootstrap_servers=args.bootstrap_servers)
        try:
            for topic, key, value in records:
                publisher.publish(topic, key, value)
            publisher.flush()
        finally:
            publisher.close()
    _emit_json(
        {
            "nodes": len(result.nodes),
            "edges": len(result.edges),
            "has_metadata": result.metadata is not None,
            "has_error": result.error is not None,
        }
    )


def cmd_parse_repo(args: argparse.Namespace) -> None:
    publisher = build_publisher(args.publisher, output=args.publisher_output, bootstrap_servers=args.bootstrap_servers)
    parser = PythonCPGParser(repo_name=args.repo_name, commit_sha=args.commit_sha)
    total = {"files": 0, "nodes": 0, "edges": 0, "metadata": 0, "errors": 0}
    try:
        for result in parser.parse_repository_iter(args.repo, include_tests=args.include_tests, exclude_patterns=args.exclude_pattern):
            total["files"] += 1
            total["nodes"] += len(result.nodes)
            total["edges"] += len(result.edges)
            if result.metadata is not None:
                total["metadata"] += 1
            if result.error is not None:
                total["errors"] += 1
            for topic, key, value in result.all_events():
                publisher.publish(topic, key, value)
        publisher.flush()
    finally:
        publisher.close()
    _emit_json(total)


def cmd_replay_file(args: argparse.Namespace) -> None:
    summary = reprocess_single_file(
        file_path=args.after_file,
        previous_file_path=args.before_file,
        repo_root=args.repo_root,
        repo_name=args.repo_name,
        commit_sha=args.commit_sha,
    )
    _emit_json(summary.to_dict())


def cmd_build_book(args: argparse.Namespace) -> None:
    base = Path(args.output)
    base.mkdir(parents=True, exist_ok=True)
    (base / "_config.yml").write_text(
        """\
title: Group 4 Lab 04
author: Group 4
logo: ""
""",
        encoding="utf-8",
    )
    (base / "_toc.yml").write_text(
        """\
format: jb-book
root: intro
chapters:
  - file: task1
  - file: task2
  - file: task3
  - file: task4
  - file: task5
  - file: task6
  - file: architecture
  - file: conclusion
""",
        encoding="utf-8",
    )
    pages = {
        "intro.md": "# Introduction\n\nThis report documents the Lab 04 streaming pipeline built around the selected repository `huggingface/peft`.\n",
        "task1.md": "# Task 1\n\nShow repository discovery, file counting, and the scope chosen for incremental parsing.\n",
        "task2.md": "# Task 2\n\nExplain the parser architecture, stable ID strategy, and how AST, CFG, DFG, and call edges are extracted.\n",
        "task3.md": "# Task 3\n\nDocument Kafka topic design, event shape, and publishing strategy.\n",
        "task4.md": "# Task 4\n\nDocument Neo4j ingestion, constraint setup, and replay-safe MERGE semantics.\n",
        "task5.md": "# Task 5\n\nDocument Spark Structured Streaming, checkpointing, and MongoDB sink configuration.\n",
        "task6.md": "# Task 6\n\nShow the replay workflow, before/after diffs, and idempotence checks.\n",
        "architecture.md": "# Architecture\n\nSummarize the end-to-end pipeline from repository scan to Kafka, Neo4j, and MongoDB.\n",
        "conclusion.md": "# Conclusion\n\nSummarize what the pipeline proves, what remains manual, and the next improvements.\n",
    }
    for name, content in pages.items():
        (base / name).write_text(content, encoding="utf-8")
    _emit_json({"book_skeleton_written_to": str(base)})


def cmd_emit_configs(args: argparse.Namespace) -> None:
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    write_sink_properties(out / "neo4j" / "sink.properties", Neo4jSinkSpec())
    (out / "neo4j" / "constraints.cypher").write_text(neo4j_constraints_cypher(), encoding="utf-8")
    write_mongo_streaming_spec(out / "mongo" / "streaming.json", MongoStreamingSpec())
    spark_job_path(out)
    _emit_json({"config_bundle_written_to": str(out)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="group4-lab4")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("discover", help="Discover Python files")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--include-tests", action="store_true")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("parse-file", help="Parse one Python file")
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--repo-root", type=Path, default=None)
    p.add_argument("--repo-name", default="huggingface/peft")
    p.add_argument("--commit-sha", default="HEAD")
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--publisher", choices=["console", "kafka"], default="console")
    p.add_argument("--publisher-output", type=Path, default=None)
    p.add_argument("--bootstrap-servers", default="localhost:9092")
    p.set_defaults(func=cmd_parse_file)

    p = sub.add_parser("parse-repo", help="Parse an entire repository incrementally")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--repo-name", default="huggingface/peft")
    p.add_argument("--commit-sha", default="HEAD")
    p.add_argument("--include-tests", action="store_true")
    p.add_argument("--exclude-pattern", action="append", default=[])
    p.add_argument("--publisher", choices=["console", "kafka"], default="console")
    p.add_argument("--publisher-output", type=Path, default=None)
    p.add_argument("--bootstrap-servers", default="localhost:9092")
    p.set_defaults(func=cmd_parse_repo)

    p = sub.add_parser("replay-file", help="Compare two versions of one Python file")
    p.add_argument("--after-file", type=Path, required=True)
    p.add_argument("--before-file", type=Path, default=None)
    p.add_argument("--repo-root", type=Path, default=None)
    p.add_argument("--repo-name", default="huggingface/peft")
    p.add_argument("--commit-sha", default="HEAD")
    p.set_defaults(func=cmd_replay_file)

    p = sub.add_parser("build-book", help="Build a Jupyter Book skeleton")
    p.add_argument("--output", type=Path, required=True)
    p.set_defaults(func=cmd_build_book)

    p = sub.add_parser("emit-configs", help="Write config bundle for Kafka, Neo4j, MongoDB and Spark")
    p.add_argument("--output", type=Path, required=True)
    p.set_defaults(func=cmd_emit_configs)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
