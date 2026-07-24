# Group 4 Lab 04

<div class="hero-panel">
  <p class="eyebrow">Published Jupyter Book</p>
  <h1>Spark Streaming on <code>huggingface/peft</code></h1>
  <p class="hero-copy">This book documents the lab as a structured narrative: we discover the repository, parse Python source into CPG-style events, publish through Kafka, ingest graph data into Neo4j, stream metadata into MongoDB, and verify replay idempotency.</p>
  <div class="hero-meta">
    <span><strong>Repository</strong><br/>huggingface/peft</span>
    <span><strong>Scope</strong><br/>6 tasks + architecture</span>
    <span><strong>Evidence</strong><br/>Notebook outputs, DB screenshots, logs</span>
  </div>
</div>

<div class="section-card">
  <h2>Reading Guide</h2>
  <p>Start with the main report for the step-by-step narrative. The supporting chapters provide the architecture summary and closing reflection so the submission reads like a clean story instead of a pile of artifacts.</p>
  <div class="task-grid">
    <div class="task-card">
      <h3>Main Report</h3>
      <p><a href="report.html">Open the task-by-task notebook</a> with executed outputs and screenshots.</p>
    </div>
    <div class="task-card">
      <h3>Architecture</h3>
      <p><a href="architecture.html">Review the pipeline diagram</a> and the design decisions behind each sink.</p>
    </div>
    <div class="task-card">
      <h3>Conclusion</h3>
      <p><a href="conclusion.html">Read the final reflection</a> and the remaining improvement notes.</p>
    </div>
  </div>
</div>

<div class="section-card">
  <h2>What to expect</h2>
  <div class="metric-grid">
    <div class="metric-card">
      <span class="metric-value">Task 1</span>
      <span class="metric-label">Repository discovery</span>
      <span class="metric-note">File counting and scope selection for the PEFT checkout.</span>
    </div>
    <div class="metric-card">
      <span class="metric-value">Task 2</span>
      <span class="metric-label">Incremental parser</span>
      <span class="metric-note">AST, CFG, DFG, and call-event generation with stable IDs.</span>
    </div>
    <div class="metric-card">
      <span class="metric-value">Task 3-5</span>
      <span class="metric-label">Kafka to databases</span>
      <span class="metric-note">Topic design, Neo4j ingestion, and Spark-to-MongoDB metadata streaming.</span>
    </div>
    <div class="metric-card">
      <span class="metric-value">Task 6</span>
      <span class="metric-label">Replay verification</span>
      <span class="metric-note">Before/after comparisons, counts, and idempotency checks.</span>
    </div>
  </div>
</div>
