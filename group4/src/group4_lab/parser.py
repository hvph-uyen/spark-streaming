from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .discovery import discover_python_files
from .hashing import ast_fingerprint, canonical_name, normalize_text, path_module_name, stable_hash
from .models import CPGEdgeEvent, CPGNodeEvent, MetadataEvent, ParseResult, ParserErrorEvent, SourceSpan, utc_now_iso


@dataclass
class ScopeState:
    qualname: str
    defs: dict[str, str] = field(default_factory=dict)
    symbols: dict[str, str] = field(default_factory=dict)
    parent: ScopeState | None = None

    def child(self, name: str) -> "ScopeState":
        return ScopeState(
            qualname=canonical_name(self.qualname, name),
            defs=dict(self.defs),
            symbols=dict(self.symbols),
            parent=self,
        )

    def lookup_def(self, name: str) -> str | None:
        if name in self.defs:
            return self.defs[name]
        if self.parent is not None:
            return self.parent.lookup_def(name)
        return None

    def lookup_symbol(self, name: str) -> str | None:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.lookup_symbol(name)
        return None

    def bind(self, name: str, node_id: str) -> None:
        self.defs[name] = node_id
        self.symbols[name] = node_id
        self.symbols[self.qualname_and(name)] = node_id

    def qualname_and(self, name: str) -> str:
        return canonical_name(self.qualname, name)


@dataclass
class NodeContext:
    repo: str
    commit_sha: str
    file_path: str
    module_name: str
    event_time: str


class PythonCPGParser:
    def __init__(
        self,
        repo_name: str = "huggingface/peft",
        commit_sha: str = "HEAD",
        schema_version: int = 1,
    ) -> None:
        self.repo_name = repo_name
        self.commit_sha = commit_sha
        self.schema_version = schema_version

    def parse_file(self, file_path: str | Path, repo_root: str | Path | None = None) -> ParseResult:
        path = Path(file_path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError as exc:
            return ParseResult(
                error=ParserErrorEvent(
                    schema_version=self.schema_version,
                    event_time=utc_now_iso(),
                    repo=self.repo_name,
                    commit_sha=self.commit_sha,
                    file_path=str(path),
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
        return self.parse_text(text=text, file_path=path, repo_root=repo_root)

    def parse_text(self, text: str, file_path: str | Path, repo_root: str | Path | None = None) -> ParseResult:
        path = Path(file_path)
        module_name = path_module_name(path, Path(repo_root) if repo_root else None)
        ctx = NodeContext(
            repo=self.repo_name,
            commit_sha=self.commit_sha,
            file_path=str(path),
            module_name=module_name,
            event_time=utc_now_iso(),
        )
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            return ParseResult(
                error=ParserErrorEvent(
                    schema_version=self.schema_version,
                    event_time=ctx.event_time,
                    repo=self.repo_name,
                    commit_sha=self.commit_sha,
                    file_path=str(path),
                    error_type=type(exc).__name__,
                    message=str(exc),
                    properties={"lineno": exc.lineno, "offset": exc.offset},
                )
            )

        builder = _CPGBuilder(ctx, self.schema_version, text)
        return builder.build(tree)

    def parse_repository(
        self,
        repo_root: str | Path,
        include_tests: bool = False,
        exclude_patterns: list[str] | None = None,
    ) -> list[ParseResult]:
        return list(self.parse_repository_iter(repo_root, include_tests=include_tests, exclude_patterns=exclude_patterns))

    def parse_repository_iter(
        self,
        repo_root: str | Path,
        include_tests: bool = False,
        exclude_patterns: list[str] | None = None,
    ) -> Iterable[ParseResult]:
        for file_path in discover_python_files(repo_root, include_tests=include_tests, exclude_patterns=exclude_patterns):
            yield self.parse_file(file_path, repo_root=repo_root)


def parse_file(file_path: str | Path, repo_root: str | Path | None = None, **kwargs: Any) -> ParseResult:
    parser = PythonCPGParser(
        repo_name=kwargs.get("repo_name", "huggingface/peft"),
        commit_sha=kwargs.get("commit_sha", "HEAD"),
        schema_version=kwargs.get("schema_version", 1),
    )
    return parser.parse_file(file_path=file_path, repo_root=repo_root)


class _CPGBuilder:
    def __init__(self, ctx: NodeContext, schema_version: int, source_text: str) -> None:
        self.ctx = ctx
        self.schema_version = schema_version
        self.source_text = source_text
        self.lines = source_text.splitlines()
        self.nodes: list[CPGNodeEvent] = []
        self.edges: list[CPGEdgeEvent] = []
        self.node_by_ast: dict[int, str] = {}
        self.scope_stack: list[ScopeState] = [ScopeState(qualname=ctx.module_name)]

    @property
    def scope(self) -> ScopeState:
        return self.scope_stack[-1]

    def build(self, tree: ast.AST) -> ParseResult:
        self._walk(tree, parent_id=None)
        metadata = self._build_metadata(tree)
        return ParseResult(nodes=self.nodes, edges=self.edges, metadata=metadata)

    def _build_metadata(self, tree: ast.AST) -> MetadataEvent:
        class_count = 0
        function_count = 0
        import_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
        return MetadataEvent(
            schema_version=self.schema_version,
            event_time=self.ctx.event_time,
            repo=self.ctx.repo,
            commit_sha=self.ctx.commit_sha,
            file_path=self.ctx.file_path,
            file_size_bytes=len(self.source_text.encode("utf-8")),
            line_count=len(self.lines) or 1,
            content_hash=stable_hash(self.ctx.file_path, normalize_text(self.source_text)),
            ast_node_count=len(self.nodes),
            ast_edge_count=sum(1 for edge in self.edges if edge.edge_type == "AST_CHILD"),
            cfg_edge_count=sum(1 for edge in self.edges if edge.edge_type.startswith("CFG_")),
            dfg_edge_count=sum(1 for edge in self.edges if edge.edge_type == "DFG"),
            call_edge_count=sum(1 for edge in self.edges if edge.edge_type == "CALLS"),
            class_count=class_count,
            function_count=function_count,
            import_count=import_count,
        )

    def _emit_node(self, node: ast.AST, label: str | None = None, extra: dict[str, Any] | None = None) -> str:
        cached = self.node_by_ast.get(id(node))
        if cached is not None:
            return cached

        lineno = getattr(node, "lineno", None)
        col_offset = getattr(node, "col_offset", None)
        end_lineno = getattr(node, "end_lineno", None)
        end_col_offset = getattr(node, "end_col_offset", None)
        kind = type(node).__name__
        fingerprint = ast_fingerprint(node)
        base_name = getattr(node, "name", None) or getattr(node, "id", None) or label or ""
        node_source = self._normalized_node_source(node, lineno)
        node_id = stable_hash(
            self.ctx.repo,
            self.ctx.file_path,
            self.scope.qualname,
            kind,
            base_name,
            fingerprint,
            node_source,
        )
        self.node_by_ast[id(node)] = node_id
        properties: dict[str, Any] = {
            "node_type": kind,
            "line_text": self._snippet(lineno),
            "fingerprint": fingerprint[:1200],
        }
        if extra:
            properties.update(extra)
        self.nodes.append(
            CPGNodeEvent(
                schema_version=self.schema_version,
                event_time=self.ctx.event_time,
                repo=self.ctx.repo,
                commit_sha=self.ctx.commit_sha,
                file_path=self.ctx.file_path,
                element_id=node_id,
                kind=kind,
                qualname=self.scope.qualname,
                label=base_name or kind,
                span=SourceSpan(
                    lineno=lineno,
                    col_offset=col_offset,
                    end_lineno=end_lineno,
                    end_col_offset=end_col_offset,
                ),
                properties=properties,
            )
        )
        return node_id

    def _normalized_node_source(self, node: ast.AST, lineno: int | None) -> str:
        segment = ast.get_source_segment(self.source_text, node)
        if segment:
            return normalize_text(segment)
        snippet = self._snippet(lineno)
        if snippet:
            return normalize_text(snippet)
        return ast_fingerprint(node)

    def _snippet(self, lineno: int | None) -> str:
        if lineno is None or lineno <= 0 or lineno > len(self.lines):
            return ""
        return self.lines[lineno - 1].strip()

    def _add_edge(self, source_id: str, target_id: str, edge_type: str, **properties: Any) -> None:
        edge_id = stable_hash(self.ctx.repo, self.ctx.file_path, edge_type, source_id, target_id, json.dumps(properties, sort_keys=True))
        self.edges.append(
            CPGEdgeEvent(
                schema_version=self.schema_version,
                event_time=self.ctx.event_time,
                repo=self.ctx.repo,
                commit_sha=self.ctx.commit_sha,
                file_path=self.ctx.file_path,
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                properties=properties,
            )
        )

    def _walk(self, node: ast.AST, parent_id: str | None) -> str:
        node_id = self._emit_node(node)
        if parent_id is not None:
            self._add_edge(parent_id, node_id, "AST_CHILD")

        if isinstance(node, ast.Module):
            self._walk_block(node.body, node_id)
            return node_id

        if isinstance(node, ast.ClassDef):
            self.scope.bind(node.name, node_id)
            child = self.scope.child(node.name)
            self.scope_stack.append(child)
            for decorator in node.decorator_list:
                self._walk(decorator, node_id)
            for base in node.bases:
                self._walk(base, node_id)
            for keyword in node.keywords:
                self._walk(keyword, node_id)
            self._walk_block(node.body, node_id)
            self.scope_stack.pop()
            return node_id

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.scope.bind(node.name, node_id)
            child = self.scope.child(node.name)
            self.scope_stack.append(child)
            for decorator in node.decorator_list:
                self._walk(decorator, node_id)
            for default in node.args.defaults:
                self._walk(default, node_id)
            for default in node.args.kw_defaults:
                if default is not None:
                    self._walk(default, node_id)
            for arg in self._iter_args(node.args):
                arg_id = self._emit_node(arg, label=arg.arg, extra={"arg": arg.arg})
                self.scope.bind(arg.arg, arg_id)
                self._add_edge(node_id, arg_id, "AST_CHILD")
            if node.returns is not None:
                self._walk(node.returns, node_id)
            self._walk_block(node.body, node_id)
            self.scope_stack.pop()
            return node_id

        if isinstance(node, ast.If):
            self._walk(node.test, node_id)
            self._walk_block(node.body, node_id, cfg_kind="CFG_TRUE")
            self._walk_block(node.orelse, node_id, cfg_kind="CFG_FALSE")
            return node_id

        if isinstance(node, (ast.For, ast.AsyncFor)):
            self._walk(node.target, node_id)
            self._walk(node.iter, node_id)
            self._walk_block(node.body, node_id, cfg_kind="CFG_LOOP")
            self._walk_block(node.orelse, node_id, cfg_kind="CFG_ELSE")
            return node_id

        if isinstance(node, ast.While):
            self._walk(node.test, node_id)
            self._walk_block(node.body, node_id, cfg_kind="CFG_LOOP")
            self._walk_block(node.orelse, node_id, cfg_kind="CFG_ELSE")
            return node_id

        if isinstance(node, ast.Try):
            self._walk_block(node.body, node_id, cfg_kind="CFG_TRY")
            for handler in node.handlers:
                self._walk(handler, node_id)
            self._walk_block(node.orelse, node_id, cfg_kind="CFG_ELSE")
            self._walk_block(node.finalbody, node_id, cfg_kind="CFG_FINALLY")
            return node_id

        if isinstance(node, ast.ExceptHandler):
            if node.type is not None:
                self._walk(node.type, node_id)
            if node.name:
                self.scope.bind(node.name, node_id)
            self._walk_block(node.body, node_id, cfg_kind="CFG_EXCEPT")
            return node_id

        if isinstance(node, ast.With):
            for item in node.items:
                self._walk(item, node_id)
            self._walk_block(node.body, node_id)
            return node_id

        if isinstance(node, ast.withitem):
            self._walk(node.context_expr, node_id)
            if node.optional_vars is not None:
                self._walk(node.optional_vars, node_id)
            return node_id

        if isinstance(node, ast.Assign):
            self._walk(node.value, node_id)
            for target in node.targets:
                self._bind_assignment_target(target, node_id)
            return node_id

        if isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self._walk(node.value, node_id)
            if node.annotation is not None:
                self._walk(node.annotation, node_id)
            self._bind_assignment_target(node.target, node_id)
            return node_id

        if isinstance(node, ast.AugAssign):
            self._walk(node.target, node_id)
            self._walk(node.value, node_id)
            self._bind_assignment_target(node.target, node_id)
            return node_id

        if isinstance(node, ast.Return):
            if node.value is not None:
                self._walk(node.value, node_id)
            return node_id

        if isinstance(node, ast.Expr):
            self._walk(node.value, node_id)
            return node_id

        if isinstance(node, ast.Call):
            self._handle_call(node, node_id)
            for child in ast.iter_child_nodes(node):
                if child is not node.func:
                    self._walk(child, node_id)
            return node_id

        if isinstance(node, ast.Name):
            ctx_type = type(node.ctx).__name__
            if isinstance(node.ctx, ast.Load):
                source = self.scope.lookup_def(node.id)
                if source:
                    self._add_edge(source, node_id, "DFG", name=node.id)
            elif isinstance(node.ctx, (ast.Store, ast.Param)):
                self.scope.bind(node.id, node_id)
            elif isinstance(node.ctx, ast.Del):
                self.scope.bind(node.id, node_id)
            return node_id

        if isinstance(node, ast.arg):
            self.scope.bind(node.arg, node_id)
            return node_id

        if isinstance(node, ast.Attribute):
            self._walk(node.value, node_id)
            return node_id

        if isinstance(node, ast.keyword):
            if node.value is not None:
                self._walk(node.value, node_id)
            return node_id

        if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict, ast.BinOp, ast.BoolOp, ast.Compare, ast.UnaryOp, ast.Subscript, ast.JoinedStr, ast.FormattedValue, ast.Lambda, ast.IfExp, ast.Await, ast.Yield, ast.YieldFrom, ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp, ast.comprehension, ast.Constant)):
            for child in ast.iter_child_nodes(node):
                self._walk(child, node_id)
            return node_id

        for child in ast.iter_child_nodes(node):
            self._walk(child, node_id)
        return node_id

    def _walk_block(self, statements: Iterable[ast.AST], parent_id: str, cfg_kind: str = "CFG_NEXT") -> None:
        prev_stmt_id: str | None = None
        for stmt in statements:
            stmt_id = self._walk(stmt, parent_id)
            if prev_stmt_id is not None:
                self._add_edge(prev_stmt_id, stmt_id, cfg_kind)
            prev_stmt_id = stmt_id

    def _iter_args(self, args: ast.arguments) -> Iterable[ast.arg]:
        yield from args.posonlyargs
        yield from args.args
        if args.vararg is not None:
            yield args.vararg
        yield from args.kwonlyargs
        if args.kwarg is not None:
            yield args.kwarg

    def _bind_assignment_target(self, target: ast.AST, source_id: str) -> None:
        if isinstance(target, ast.Name):
            target_id = self._emit_node(target, label=target.id, extra={"role": "assignment_target"})
            self.scope.bind(target.id, source_id)
            self._add_edge(source_id, target_id, "DFG", name=target.id, role="definition")
            self._add_edge(source_id, target_id, "AST_CHILD")
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._bind_assignment_target(elt, source_id)
            return
        if isinstance(target, ast.Attribute):
            self._walk(target, source_id)
            return
        self._walk(target, source_id)

    def _handle_call(self, node: ast.Call, call_node_id: str) -> None:
        callee_name = self._resolve_callable_name(node.func)
        if callee_name is None:
            callee_name = "external.call"
        target_id = self.scope.lookup_symbol(callee_name)
        if target_id is None and "." in callee_name:
            target_id = self.scope.lookup_symbol(callee_name.split(".")[-1])
        if target_id is None:
            ext_node = ast.Constant(value=callee_name)
            target_id = self._emit_node(ext_node, label=callee_name, extra={"role": "external_symbol"})
        self._add_edge(call_node_id, target_id, "CALLS", callee=callee_name)

    def _resolve_callable_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            value = self._resolve_callable_name(node.value)
            if value:
                return canonical_name(value, node.attr)
            return node.attr
        if isinstance(node, ast.Call):
            return self._resolve_callable_name(node.func)
        return None


def parse_repository_to_results(
    repo_root: str | Path,
    repo_name: str = "huggingface/peft",
    commit_sha: str = "HEAD",
    include_tests: bool = False,
    exclude_patterns: list[str] | None = None,
) -> list[ParseResult]:
    parser = PythonCPGParser(repo_name=repo_name, commit_sha=commit_sha)
    return parser.parse_repository(repo_root, include_tests=include_tests, exclude_patterns=exclude_patterns)
