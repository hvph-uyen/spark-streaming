from __future__ import annotations

from collections import Counter
from pathlib import Path


DEFAULT_EXCLUDES = {
    "__pycache__",
    ".venv",
    ".git",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    "checkpoints",
    "evidence",
    "logs",
    "output",
    "screenshots",
}


def discover_python_files(
    repo_root: str | Path,
    include_tests: bool = False,
    exclude_patterns: list[str] | None = None,
) -> list[Path]:
    root = Path(repo_root).resolve()
    patterns = set(exclude_patterns or [])
    files: list[Path] = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        parts = set(rel.parts)
        if parts & DEFAULT_EXCLUDES:
            continue
        if rel.parts and rel.parts[0] == "peft":
            continue
        if patterns and any(pattern in str(rel) for pattern in patterns):
            continue
        if not include_tests and ("tests" in rel.parts or rel.name.startswith("test_")):
            continue
        files.append(path)
    return sorted(files)


def summarize_python_files(files: list[Path], repo_root: str | Path) -> dict[str, object]:
    root = Path(repo_root).resolve()
    counter: Counter[str] = Counter()
    for path in files:
        rel = path.resolve().relative_to(root)
        top = rel.parts[0] if rel.parts else "."
        counter[top] += 1
    return {
        "repo_root": str(root),
        "total_files": len(files),
        "by_top_level_dir": dict(sorted(counter.items())),
        "sample_files": [str(path.relative_to(root)) for path in files[:10]],
    }
