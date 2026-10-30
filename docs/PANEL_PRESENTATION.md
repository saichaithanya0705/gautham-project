# 10-Minute Panel Presentation: AI-Powered Cybersecurity Incident Response Assistant with Synapt

Primary architecture visual: [`architecture/presentation_end_to_end_architecture.pdf`](architecture/presentation_end_to_end_architecture.pdf). The corresponding technical narration and editable Mermaid source are in [`PRESENTATION_END_TO_END_ARCHITECTURE.md`](PRESENTATION_END_TO_END_ARCHITECTURE.md).

---

## Slide 1: Title & Overview (1 Minute)
* **Title**: CyberSentinel Copilot: AI-Powered Cybersecurity Incident Response Assistant
* **Dataset**: CIC-IDS2017 Intrusion Detection Benchmark (2.31 Million Flow Records in SQLite)
* **Core Technology Stack**:
  * **Synapt Context Substrate**: Real-time Model Context Protocol (MCP) semantic retrieval and knowledge substrate.
  * **Dual-Store Architecture**: SQLite owns exact flow telemetry, parameterized metadata filtering, and FTS5 BM25 search. Synapt owns semantic knowledge retrieval, procedural guidance, and generative reasoning.
  * **LangGraph Multi-Agent Orchestration**: 7-node choreographed state graph with LLM-as-Judge validation.
  * **Hybrid ML Suite**: Supervised HistGradientBoosting classifier (99.58% F1) + Unsupervised IsolationForest anomaly detector (3.2% false alarm rate).
  * **FastAPI Microservice & Glassmorphic SOC Analyst Copilot UI**.
* **Fundamental Guardrail**: Read-only decision support for SOC analysts. **Strict prohibition on automated containment** (automated firewall blocking/script execution is rejected; all containment requires human analyst authorization).

---

## Slide 2: The Dataset Reality & Provenance Grounding (1 Minute)
* **Scale**: 2,313,810 records across 8 Parquet files and 78 raw network features.
* **Schema Boundary & Honest Engineering**:
  * The official CIC-IDS2017 Parquet export lacks Flow ID, IP addresses, ports, and timestamps.
  * **Our Architectural Decision**: Rather than hallucinating synthetic IPs or failing silently, we enforce deterministic flow provenance (`source_file` + `source_row_number` + 64-bit fingerprint) and implement graceful degradation notifications for network metadata filters (Requirement B4).

---

## Slide 3: Dual-Store Boundary & Historical Hybrid RAG (1.5 Minutes)
* **Boundary Discipline**: We never attempt to ingest 2.3M raw tabular flows into Synapt or introduce redundant external vector DBs.
* **Fused Hybrid Search (B1 & B2)**:
  * 291 representative historical incident summaries indexed in native **SQLite FTS5** (`historical_incidents_fts`) and ingested into **Synapt Context Substrate** (Job `01M4Q6W3BKS0W3P6SQ26SZKW07`).
  * **Reciprocal Rank Fusion (RRF)** combines BM25 keyword rankings and Synapt semantic retrieval:
    $$\text{RRF Score} = \frac{1}{60 + \text{rank}_{\text{BM25}}} + \frac{1}{60 + \text{rank}_{\text{Synapt}}}$$
  * **Self-Exclusion**: Guarantees a queried target flow is never returned as its own historical evidence.
  * **Paraphrase Capability**: Queries like *"repeated failed password attempts"* correctly resolve to SSH/FTP brute-force incidents without requiring exact keyword syntax.

---

## Slide 4: Hybrid ML & Unsupervised Anomaly Detection (1.5 Minutes)
* **Supervised Classifier (A2)**:
  * HistGradientBoostingClassifier trained on 65 domain-engineered features (directional asymmetry, TCP control state, volumetric rates, and inter-arrival dynamics).
  * Weighted Average F1-Score: **0.9958** across all 9 attack families (`benign`, `dos`, `ddos`, `brute_force`, `port_scan`, `web_attack`, `botnet`, `infiltration`, `rare_attack`).
* **Unsupervised Anomaly Detector (A5)**:
  * Isolation Forest trained strictly on 20,000 benign traffic flows without label exposure.
  * Evaluated on 5,000 holdout benign flows and 5,000 attack flows:
    * **Benign False Alarm Rate**: **3.2%** (well below the 5% enterprise ceiling).
    * **Unsupervised Attack Detection Rate**: **55.7%** on zero-day attack traffic.
* **Explainability Engine (A6)**:
  * Computes feature deviations comparing observed flow metrics against benign baselines, displaying exact values, baseline norms, and magnitude multipliers.

---

## Slide 5: Deterministic Incident Prioritization (1 Minute)
* **Policy Matrix (B7)**: Evaluates high-impact telemetry and classification metrics into deterministic operational tiers:
  * **P1 - Critical**: Confirmed volumetric DoS/DDoS or high-confidence Botnet/Infiltration ($\text{Risk} \ge 0.85$, packet rate $> 50{,}000$ pkts/s).
  * **P2 - High**: Active Web Attacks, Credential Brute Force, or high-confidence Port Scans ($\text{Risk} \ge 0.70$).
  * **P3 - Medium**: Unsupervised Anomaly detections with moderate ML risk ($\text{Risk} \ge 0.40$ or $\text{Anomaly Score} > 0.55$).
  * **P4 - Low / Informational**: Benign traffic, unassessed queries, or low-probability anomalies.

---

## Slide 6: Multi-Agent LangGraph Pipeline & LLM-as-Judge (1.5 Minutes)
* **7-Agent Choreography (A4)**:
  $$\text{START} \rightarrow \text{guardrail} \rightarrow \text{flow\_triage} \rightarrow \text{ml\_analysis} \rightarrow \text{synapt\_knowledge} \rightarrow \text{prioritization} \rightarrow \text{response\_recommendation} \rightarrow \text{judge\_review} \rightarrow \text{END}$$
* **Input Guardrails (B6)**:
  * Sanitizes prompt injections, auto-containment instructions, and SQL syntax.
  * Validates telemetry ranges and protects prompt context via XML isolation (`<analyst_context>`).
  * Enforces strict 404 responses when explicit flow records do not exist.
* **LLM-as-Judge (A3)**:
  * Evaluates every candidate response before delivery on 4 rubric dimensions: *Factuality & Grounding*, *Action Safety*, *NIST SP 800-61 Alignment*, and *Relevance*.
  * Hard invariant gate: Flags any response suggesting automated action.

---

## Slide 7: DeepEval Quality Benchmarks & Continuous Improvement (1.5 Minutes)
* **Executable DeepEval Quality Benchmark (A1)**:
  * Implemented custom `SynaptDeepEvalLLM` adapter interfacing Synapt Trident with `deepeval==4.2.8`.
  * **40 Structured Benchmark Test Cases** across live telemetry, synthetic fixtures, out-of-distribution queries, and adversarial prompt injections.
  * **Result**: **40/40 test cases passed (100% pass rate)** with **0 critical safety violations**. Saved to [`reports/deepeval_evaluation_results.json`](file:///c:/Users/SAI/Downloads/handoff_zip/reports/deepeval_evaluation_results.json).
* **Reviewed Continuous Improvement Loop (A7)**:
  * Complete lifecycle: Submit review (`POST /feedback`) $\rightarrow$ Human approval gate (`POST /feedback/review`) $\rightarrow$ Candidate retraining $\rightarrow$ Holdout benchmark evaluation $\rightarrow$ Promotion or rollback decision (`POST /feedback/improve`).
  * Validated in automated tests; report saved to [`reports/model_improvement_benchmark.json`](file:///c:/Users/SAI/Downloads/handoff_zip/reports/model_improvement_benchmark.json).

---

## Slide 8: Requirements Verification Summary (1 Minute)
* **All 16 Requirements (B1–B8 and A1–A8) Verified**:
  * `pytest tests/test_investigation_service.py`: **13/13 passed** in 2m 07s.
  * `pytest tests/test_deepeval_benchmarks.py`: **1/1 passed** (40/40 test cases verified).
  * Live Uvicorn service running on `http://127.0.0.1:8000`.
  * Full traceability matrix documented in [`docs/REQUIREMENTS_TRACEABILITY.md`](file:///c:/Users/SAI/Downloads/handoff_zip/docs/REQUIREMENTS_TRACEABILITY.md).
