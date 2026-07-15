# Task 1

## Repository discovery

The first step of the lab is to identify the scope of the selected repository and enumerate the Python files that will be parsed.

The implementation uses:

```bash
group4-lab4 discover --repo <path-to-peft>
```

This command walks the repository, skips common build and cache directories, and returns:

- the resolved repository root
- the total number of Python files discovered
- a breakdown by top-level directory
- a small sample of matching file paths

## Why the scope matters

The selected repository `huggingface/peft` is well suited for incremental parsing because it is split into many small modules and subpackages. That means the parser can process one file at a time instead of loading the entire repository into memory.

Recommended focus areas:

- `src/peft/`
- `src/peft/tuners/`
- `src/peft/utils/`
- `examples/`
- `tests/` if the report wants a fuller file count

## What to record in the report

- the discovery command
- the total Python file count
- the filtered file count, if tests or generated files are excluded
- a note explaining why the chosen scope is good for streaming and replay

