# Task 6

## Replay verification

The replay helper compares two parses of a file and reports:

- event count before and after
- stable event IDs
- added and removed event IDs

The CLI command is:

```bash
group4-lab4 replay-file --before-file <original.py> --after-file <edited.py>
```

## What changed in the parser

The ID strategy avoids depending on raw line numbers, so code that stays semantically the same keeps the same stable identity.
That is the foundation for replay-safe Kafka publishing and Neo4j `MERGE` behavior.

## How to demonstrate the lab requirement

Choose one small file, make a narrow edit, and rerun the parser.

Good edits:

- add a helper function
- change a function body
- add an import
- add a parameter to a small function

Then show:

- the events that remain stable
- the new events added by the edit
- the absence of duplicate graph entities in Neo4j

