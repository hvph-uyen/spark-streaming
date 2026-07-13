from __future__ import annotations

import ast
import hashlib
from pathlib import Path


def normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def stable_hash(*parts: object) -> str:
    hasher = hashlib.sha1()
    for part in parts:
        data = str(part).encode("utf-8", errors="replace")
        hasher.update(data)
        hasher.update(b"\0")
    return hasher.hexdigest()


def ast_fingerprint(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False, annotate_fields=True)


def path_module_name(file_path: Path, repo_root: Path | None = None) -> str:
    if repo_root is not None:
        rel = file_path.resolve().relative_to(repo_root.resolve())
        return ".".join(rel.with_suffix("").parts)
    return ".".join(file_path.with_suffix("").parts)


def canonical_name(*parts: str) -> str:
    return ".".join(p for p in parts if p)

