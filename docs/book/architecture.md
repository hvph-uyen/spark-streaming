# Architecture

<div class="hero-panel">
  <p class="eyebrow">System Design</p>
  <h1>End-to-end flow from parser to storage</h1>
  <p class="hero-copy">The pipeline keeps the graph topology and the file-level metadata separate on purpose. That makes the ingestion simpler to reason about, easier to replay, and much easier to verify in the final report.</p>
</div>

## End-to-end flow

![End-to-end architecture diagram](assets/architecture.svg)

<div class="section-card">
  <h2>Component summary</h2>
  <div class="task-grid">
    <div class="task-card">
      <h3>Discovery</h3>
      <p><code>src/group4_lab/discovery.py</code> finds the Python files that should enter the pipeline.</p>
    </div>
    <div class="task-card">
      <h3>Parsing</h3>
      <p><code>src/group4_lab/parser.py</code> extracts AST nodes, CFG edges, DFG edges, call edges, and metadata.</p>
    </div>
    <div class="task-card">
      <h3>Publishing</h3>
      <p><code>src/group4_lab/publisher.py</code> sends events either to Kafka or to a console/jsonl output.</p>
    </div>
    <div class="task-card">
      <h3>Neo4j</h3>
      <p><code>src/group4_lab/neo4j_tools.py</code> prepares the sink config and the uniqueness constraints.</p>
    </div>
    <div class="task-card">
      <h3>MongoDB</h3>
      <p><code>src/group4_lab/mongo_streaming.py</code> defines the Spark Structured Streaming job and checkpoint path.</p>
    </div>
    <div class="task-card">
      <h3>Replay</h3>
      <p><code>src/group4_lab/replay.py</code> compares before/after parses and summarizes event stability.</p>
    </div>
  </div>
</div>

## Design choices

<div class="section-card">
  <ul>
    <li>The parser is file-oriented so it can run incrementally and replay a single file when changes occur.</li>
    <li>Stable hashes make node and edge IDs deterministic, which keeps downstream sinks idempotent.</li>
    <li>Graph topology is separated from file metadata so Neo4j and MongoDB can each consume a focused payload.</li>
    <li>The report stays in Jupyter Book so evidence can be published as a static GitHub Pages site.</li>
  </ul>
</div>

## Evidence slots

<div class="section-card">
  <ul>
    <li>Neo4j Browser screenshots: <code>assets/neo4j-node-count.jpg</code> and <code>assets/neo4j-relationship-count.jpg</code></li>
    <li>MongoDB screenshot: <code>assets/mongo-compass-peft-metadata.jpg</code></li>
    <li>Architecture asset: <code>assets/architecture.svg</code></li>
  </ul>
</div>
