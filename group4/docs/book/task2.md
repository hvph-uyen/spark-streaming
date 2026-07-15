# Task 2

## Parser design

The parser is implemented with Python's standard `ast` module and runs on one file at a time.

Core entry points:

- `PythonCPGParser.parse_file(...)`
- `PythonCPGParser.parse_repository_iter(...)`
- `parse_repository_to_results(...)`

The parser emits four event families:

- AST nodes
- CFG edges
- DFG edges
- CALL edges

It also emits file-level metadata and parser error events.

## Deterministic identifiers

Replay safety depends on stable identifiers. The implementation builds node IDs from:

- repository name
- file path
- lexical scope
- node kind
- semantic name or label
- AST fingerprint
- normalized source text

Edge IDs are derived from the repository, file, edge type, source ID, target ID, and edge properties.

This avoids using raw line numbers as the primary identity source, which would make IDs drift whenever code is inserted above an unchanged block.

## Incremental behavior

The parser works incrementally at the file level:

1. discover one Python file
2. parse that file
3. emit its events
4. move on to the next file

That keeps memory usage bounded and makes it easy to replay only the file that changed.

## Example event families

- `Module`, `ClassDef`, `FunctionDef`, `AsyncFunctionDef`
- `Import`, `ImportFrom`, `Assign`, `Return`
- `If`, `For`, `While`, `Try`, `With`
- `Call`, `Name`, `Attribute`, `Constant`

