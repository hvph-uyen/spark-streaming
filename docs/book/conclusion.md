# Conclusion

<div class="hero-panel">
  <p class="eyebrow">Closing Note</p>
  <h1>What the project demonstrates</h1>
  <p class="hero-copy">This lab shows a complete event-driven pipeline for Python source code: discover files, parse them into graph events, move the events through Kafka, and land them in Neo4j and MongoDB with replay-safe behavior.</p>
</div>

<div class="section-card">
  <h2>What worked well</h2>
  <ul>
    <li>The parser is stable enough to process the full PEFT checkout and produce deterministic events.</li>
    <li>Kafka topic separation keeps graph events, metadata, and errors easy to reason about.</li>
    <li>MongoDB streaming with checkpointing gives a clear file-level metadata store that can be replayed safely.</li>
  </ul>
</div>

<div class="section-card">
  <h2>What remains manual</h2>
  <ul>
    <li>Some screenshots and UI checks still depend on the local Docker environment.</li>
    <li>Neo4j live ingestion was validated on representative samples instead of pushing the entire graph into a small local instance.</li>
    <li>The final report still benefits from periodic evidence refreshes when a new run is executed.</li>
  </ul>
</div>

<div class="section-card">
  <h2>Next improvements</h2>
  <ul>
    <li>Add a few more parser tests around replay stability and repository iteration.</li>
    <li>Refine the Neo4j replay path to cover delete/tombstone behavior as well as MERGE-based upserts.</li>
    <li>Capture a fresh set of screenshots whenever the lab is rerun so the book stays current.</li>
  </ul>
</div>
