# CyberSentinel Copilot — Full Project Architecture

This document describes the architecture implemented in the current workspace. It separates offline preparation, runtime request handling, the seven-stage investigation workflow, supporting API paths, external knowledge retrieval, evaluation, and analyst-controlled improvement.

For the full layer-by-layer design, numbered input/processing/output matrix, branch sequence, endpoint map, trust boundaries, and failure paths, see [`DETAILED_ARCHITECTURE_AND_FLOW.md`](DETAILED_ARCHITECTURE_AND_FLOW.md).

For the module ownership view with the historical RAG, incident-knowledge, and judge-review Synapt roles aligned to their consuming workflow stages, see [`MODULE_WISE_SYNAPT_ARCHITECTURE.md`](MODULE_WISE_SYNAPT_ARCHITECTURE.md).

For the panel-ready narrative that starts with analyst input, continues through the frontend, backend, seven agents, aligned Synapt roles/tools, and ends with the final frontend result and reviewed feedback, see [`PRESENTATION_END_TO_END_ARCHITECTURE.md`](PRESENTATION_END_TO_END_ARCHITECTURE.md).

## Overall architecture

```mermaid
flowchart TB
    Analyst["Security analyst"] --> UI["SOC dashboard<br/>HTML · CSS · JavaScript"]
    UI <-->|"HTTP / JSON"| API["FastAPI microservice<br/>src/cyber_assistant/main.py"]

    subgraph Offline["A · Offline data and model preparation"]
        Raw["CIC-IDS2017<br/>8 Parquet files · 78 source columns"]
        Ingest["Dataset audit, normalization, label mapping,<br/>provenance capture, indexed ingestion"]
        DB[("SQLite<br/>2,313,810 flows")]
        Corpus["Historical incident corpus seeding<br/>291 summaries"]
        FTS[("SQLite FTS5<br/>BM25 keyword index")]
        TrainC["Supervised training<br/>65 features · 9 attack families"]
        Classifier["HistGradientBoostingClassifier<br/>attack_classifier.joblib"]
        TrainA["Benign-only anomaly training<br/>threshold calibration"]
        Anomaly["IsolationForest<br/>anomaly_detector.joblib"]
        Knowledge["Curated MITRE, NIST, feature guidance,<br/>historical incident summaries"]
        KnowledgeIngest["Synapt ingestion scripts<br/>trident_ingest"]
        Raw --> Ingest --> DB
        DB --> Corpus --> FTS
        DB --> TrainC --> Classifier
        DB --> TrainA --> Anomaly
        Knowledge --> KnowledgeIngest
    end

    subgraph SynaptLayer["B · External knowledge and semantic retrieval"]
        MCP["SynaptClient<br/>TLS · auth · JSON-RPC · dynamic tool discovery"]
        Synapt[("Synapt Context Substrate<br/>provider: assist_cyber")]
        Agents["Configured read-only roles<br/>knowledge · historical RAG · judge review"]
        KnowledgeIngest --> Synapt
        MCP <-->|"query, search, feedback"| Synapt
        Agents --- Synapt
    end

    subgraph Investigation["C · POST /investigate/flow — sequential LangGraph workflow"]
        G1["1 · Guardrail agent<br/>schema, relevance, prompt-injection and action checks"]
        G2["2 · Flow triage agent<br/>load record/raw telemetry; 404 enforcement;<br/>historical hybrid retrieval"]
        G3["3 · ML analysis agent<br/>attack classification, intrusion risk,<br/>feature deviations, anomaly score"]
        G4["4 · Knowledge agent<br/>sanitized domain query to Synapt;<br/>deterministic local degradation path"]
        G5["5 · Prioritization agent<br/>deterministic P1–P4 policy"]
        G6["6 · Response agent<br/>investigation steps, response guidance,<br/>provenance and limitations"]
        G7["7 · Judge agent<br/>hard safety invariant + four-dimension rubric;<br/>provider-backed judge when available"]
        G1 --> G2 --> G3 --> G4 --> G5 --> G6 --> G7
    end

    API -->|"investigate"| G1
    DB -->|"flow lookup"| G2
    FTS -->|"BM25 candidates"| G2
    MCP -->|"semantic candidates"| G2
    Classifier --> G3
    Anomaly --> G3
    G4 <-->|"knowledge query"| MCP
    G7 <-->|"optional judge query"| MCP

    subgraph Supporting["D · Supporting runtime paths"]
        Search["POST /search/incidents<br/>structured SQLite search + historical RAG"]
        RAG["HistoricalIncidentRAG<br/>FTS5 BM25 + Synapt semantic channel + RRF"]
        Chat["POST /chat<br/>guardrails, optional record lookup,<br/>classifier context, Synapt/local response"]
        Feedback["POST /feedback<br/>persist analyst verdict; optional trident_feedback"]
        Review["POST /feedback/review<br/>human accept/reject gate"]
        Improve["POST /feedback/improve<br/>holdout benchmark and candidate decision"]
        FeedbackDB[("analyst_feedback<br/>SQLite")]
        Health["GET /health and /api/synapt/agents<br/>component/configuration status"]
        Search --> RAG
        Feedback --> FeedbackDB --> Review --> Improve
    end

    API --> Search
    API --> Chat
    API --> Feedback
    API --> Review
    API --> Improve
    API --> Health
    Search --> DB
    RAG --> FTS
    RAG --> MCP
    Chat --> DB
    Chat --> Classifier
    Chat --> MCP
    Feedback -.-> MCP
    Improve --> Candidate["attack_classifier_candidate.joblib"]

    subgraph Evaluation["E · Evaluation and quality evidence"]
        Cases["40 structured evaluation fixtures"]
        Adapter["SynaptDeepEvalLLM adapter<br/>OpenRouter · OpenAI/NIM · Anthropic · Synapt"]
        EvalReport["DeepEval-labelled JSON report"]
        ModelReports["Classifier/anomaly/improvement reports"]
        Cases --> Adapter --> EvalReport
        TrainC --> ModelReports
        TrainA --> ModelReports
        Improve --> ModelReports
    end

    G7 --> Result["Investigation response<br/>classification · risk · anomaly · priority<br/>similar incidents · MITRE · guidance<br/>judge verdict · provenance · limitations"]
    Search --> Result
    Chat --> Result
    Feedback --> Result
    Improve --> Result
    Result --> UI --> Decision["Human analyst verification and decision<br/>No automated containment"]

    classDef data fill:#e8f7f5,stroke:#168393,color:#172e45;
    classDef model fill:#f1edfa,stroke:#7960af,color:#172e45;
    classDef external fill:#fff5df,stroke:#ad7a1f,color:#172e45;
    classDef runtime fill:#edf5ff,stroke:#3679bf,color:#172e45;
    classDef feedback fill:#f8eff9,stroke:#9b5c9e,color:#172e45;
    class Raw,Ingest,DB,Corpus,FTS,FeedbackDB data;
    class TrainC,Classifier,TrainA,Anomaly,Candidate,Cases,Adapter,EvalReport,ModelReports model;
    class Knowledge,KnowledgeIngest,MCP,Synapt,Agents external;
    class Analyst,UI,API,G1,G2,G3,G4,G5,G6,G7,Search,RAG,Chat,Health,Result,Decision runtime;
    class Feedback,Review,Improve feedback;
```

## Architectural responsibilities

| Layer | Responsibility | Primary implementation |
|---|---|---|
| Analyst interface | Collect investigation/search/chat input and render results | `src/cyber_assistant/ui/index.html` |
| API boundary | Validate request bodies, dispatch routes, shape responses | `src/cyber_assistant/main.py`, `schemas.py` |
| Orchestration | Run the seven investigation stages in order | `workflow.py` |
| Structured evidence | Preserve full flow telemetry and provenance; perform exact filters | `sqlite_store.py`, SQLite |
| Historical retrieval | BM25 keyword retrieval, Synapt semantic retrieval, reciprocal-rank fusion | `rag/historical_rag.py` |
| Prediction | Classify attack family, compute intrusion risk, explain deviations, score anomalies | `ml/predictor.py`, `ml/anomaly.py` |
| Knowledge | Retrieve security procedures and contextual guidance | `synapt/client.py`, Synapt MCP |
| Decision policy | Assign operational P1–P4 priority using explicit rules | `policy.py` |
| Output validation | Enforce hard action-safety rules and score the response rubric | `judge/evaluator.py` |
| Continuous improvement | Store feedback, require review, benchmark a candidate, record decision | `feedback/improvement.py` |
| Evaluation | Provide the DeepEval model adapter, fixtures, and JSON quality reports | `evaluation/deepeval_adapter.py`, `tests/test_deepeval_benchmarks.py` |

## Verified implementation boundaries

- The local CIC-IDS2017 export has no source/destination IP, source/destination port, Flow ID, or timestamp columns. Those request fields are accepted for interface compatibility but cannot filter this dataset; the API returns an explicit limitation.
- The RAG path fuses semantic scores only when Synapt text can be correlated with a keyword candidate. If too few candidates remain, the implementation pads results with random corpus records, so every returned fallback record is not guaranteed to be semantically similar.
- The judge uses an external model when configured and parseable; otherwise it falls back to fixed rubric defaults plus deterministic safety checks.
- The evaluation test creates `LLMTestCase` objects, but its stored score is currently a fixed `0.95` for locally accepted cases. The report proves fixture execution and the safety gate, not live DeepEval faithfulness or relevancy measurement.
- The improvement cycle creates a candidate artifact by copying the active bundle and compares equal predictions. It counts accepted corrections but does not fit those corrections into a new model, so “promoted” currently means candidate packaging and benchmark completion rather than learned model improvement.
- `/health` verifies SQLite availability. Its Synapt text is based on configuration presence and is not a live provider request.

## Safety and data boundaries

SQLite remains the source of truth for the 2.3 million network-flow records. Synapt receives questions, curated context, and selected summaries rather than the full raw flow corpus. The application produces decision support only: containment steps are drafts, automated blocking/isolation is prohibited, and a human analyst owns the final decision.
