# Conclusion

## What the project demonstrates

This repository now provides a complete lab-style streaming pipeline:

- repository discovery
- incremental parsing
- Kafka publishing
- Neo4j ingestion
- Spark to MongoDB metadata streaming
- replay verification
- report structure for Jupyter Book

## Remaining manual work

The only part that still depends on a real run is the evidence collection for the report:

- screenshots
- actual discovery counts for the chosen PEFT checkout
- Neo4j and MongoDB browser views

## Next improvements

- run the parser on the full selected repository and record counts
- capture screenshots and insert them into the book
- add a few more parser tests for replay stability and repository iteration

