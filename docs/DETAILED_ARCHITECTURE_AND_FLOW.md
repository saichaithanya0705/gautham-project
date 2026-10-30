# CyberSentinel Copilot — Detailed Architecture and Step-by-Step Flow

This document is the technical reference architecture for the implemented project. It shows the system as six layers, then follows a single investigation from analyst input through guardrails, retrieval, prediction, prioritization, response generation, judge validation, presentation, and reviewed feedback.

The dedicated module ownership and Synapt-role alignment view is available in [`MODULE_WISE_SYNAPT_ARCHITECTURE.md`](MODULE_WISE_SYNAPT_ARCHITECTURE.md).

## 1. Layered component architecture

```mermaid
flowchart TB
    subgraph L1["Layer 1 · Analyst Experience"]
        Analyst["SOC analyst"]
        Dashboard["Web dashboard<br/>Investigation · incident search · chat · feedback"]
        Analyst --> Dashboard
    end

    subgraph L2["Layer 2 · API and Contract Boundary"]
        FastAPI["FastAPI application"]
        Schemas["Pydantic request/response schemas<br/>types · bounds · required-field rules"]
        Routes["GET / · GET /health · GET /api/synapt/agents<br/>POST /search/incidents · /investigate/flow · /chat<br/>POST /feedback · /feedback/review · /feedback/improve"]
        FastAPI --> Schemas
        FastAPI --> Routes
    end

    subgraph L3["Layer 3 · Orchestration and Safety"]
        Graph["Compiled LangGraph StateGraph"]
        Guard["1. guardrail_agent"]
        Triage["2. flow_triage_agent"]
        MLAgent["3. ml_analysis_agent"]
        KnowledgeAgent["4. synapt_knowledge_agent"]
        PriorityAgent["5. prioritization_agent"]
        ResponseAgent["6. response_recommendation_agent"]
        JudgeAgent["7. judge_review_agent"]
        Graph --> Guard --> Triage --> MLAgent --> KnowledgeAgent --> PriorityAgent --> ResponseAgent --> JudgeAgent
    end

    subgraph L4["Layer 4 · Intelligence Services"]
        RAG["HistoricalIncidentRAG<br/>BM25 + Synapt channel + RRF"]
        Predictor["IntrusionPredictor<br/>family · confidence · risk · deviations"]
        Anomaly["AnomalyDetector<br/>IsolationForest score + threshold"]
        Policy["Priority policy<br/>deterministic P1–P4 rules"]
        Judge["ResponseJudge<br/>hard safety invariant + four-part rubric"]
        Chat["ChatService<br/>guarded conversational analysis"]
        Improve["ContinuousImprovementEngine<br/>review gate + holdout benchmark"]
    end

    subgraph L5["Layer 5 · Evidence, Models, and State"]
        Flows[("SQLite flows<br/>2,313,810 rows")]
        IncidentCorpus[("291 historical incident summaries<br/>FTS5 index")]
        Feedback[("analyst_feedback")]
        Classifier["attack_classifier.joblib<br/>HistGradientBoosting · 65 features · 9 families"]
        AnomalyModel["anomaly_detector.joblib<br/>IsolationForest"]
        Candidate["attack_classifier_candidate.joblib"]
        Reports["JSON evaluation and benchmark reports"]
    end

    subgraph L6["Layer 6 · External Context and Evaluation"]
        SynaptClient["SynaptClient<br/>TLS · authentication · JSON-RPC · tool discovery"]
        Synapt[("Synapt Context Substrate<br/>MITRE · NIST · historical context")]
        EvalAdapter["SynaptDeepEvalLLM adapter<br/>OpenRouter · OpenAI/NIM · Anthropic · Synapt"]
        Fixtures["40 structured evaluation fixtures"]
        SynaptClient <-->|"retrieve · ingest · feedback"| Synapt
        Fixtures --> EvalAdapter --> Reports
    end

    Dashboard <-->|"HTTP / JSON"| FastAPI
    Routes -->|"investigate"| Graph
    Routes -->|"search"| RAG
    Routes -->|"chat"| Chat
    Routes -->|"feedback/review/improve"| Improve

    Triage --> RAG
    Triage --> Flows
    RAG --> IncidentCorpus
    RAG --> SynaptClient
    MLAgent --> Predictor
    MLAgent --> Anomaly
    Predictor --> Classifier
    Anomaly --> AnomalyModel
    KnowledgeAgent --> SynaptClient
    PriorityAgent --> Policy
    JudgeAgent --> Judge
    Judge --> SynaptClient
    Chat --> Flows
    Chat --> Predictor
    Chat --> SynaptClient
    Improve --> Feedback
    Improve --> Classifier
    Improve --> Candidate
    Improve --> Reports

    JudgeAgent --> Result["Structured incident result"]
    Result --> Dashboard
    Dashboard --> HumanDecision["Human verification and response decision"]
    HumanDecision -->|"rating, verdict, optional correction"| Improve
```

## 2. Complete investigation flow

| Step | Input | Component | Processing | Output / next state |
|---:|---|---|---|---|
| 0 | Analyst record ID, query, family, protocol, or raw flow | Dashboard | Collects the investigation request and current flow context | JSON request to FastAPI |
| 1 | HTTP request | FastAPI + Pydantic schemas | Enforces field types, ranges, length limits, and non-empty investigation request | Validated `FlowInvestigationRequest`, or HTTP 422 |
| 2 | Validated request | `guardrail_agent` | Checks prompt injection, destructive instructions, prohibited automated containment, and query-only cybersecurity relevance | `guardrail_status` and optional violation |
| 3 | Approved request | `flow_triage_agent` | Loads exact record, validates supplied telemetry, enforces missing-record 404, and requests historical incidents | `target_flow`, `similar_flows`, `target_not_found` |
| 4 | Query + optional target flow | `HistoricalIncidentRAG` | Runs FTS5/BM25 keyword retrieval and Synapt semantic retrieval, correlates candidates with RRF, applies family filter, excludes the target record | Ranked historical incident summaries |
| 5 | Target telemetry | `ml_analysis_agent` | Runs nine-family classifier, calculates confidence and `1 - P(benign)` risk, extracts five benign-baseline deviations, runs IsolationForest | Classification, risk, severity, explanations, anomaly result, MITRE mapping |
| 6 | Predicted family + sanitized analyst context | `synapt_knowledge_agent` | Queries Synapt for investigation procedures, ATT&CK indicators, and verification steps; uses local degradation message if unavailable | Knowledge evidence and analysis text |
| 7 | Prediction + anomaly + telemetry context | `prioritization_agent` | Applies explicit P1–P4 rules for DoS/DDoS, infiltration, brute force, web attack, botnet, port scan, anomaly, and benign traffic | Priority code, rationale, missing context |
| 8 | All evidence and priority | `response_recommendation_agent` | Builds analyst investigation steps and response drafts; attaches model, record, provider provenance and dataset/safety limitations | Candidate incident response package |
| 9 | Candidate response + observed telemetry | `judge_review_agent` | Enforces hard no-auto-containment invariant, then evaluates grounding, action safety, NIST alignment, and relevance | Pass/fail, composite score, dimension scores, critique, unsupported claims |
| 10 | Final LangGraph state | FastAPI response mapper | Maps optional and required fields into `FlowInvestigationResponse` | Structured JSON response |
| 11 | JSON response | Dashboard | Renders assessment, evidence, similar incidents, MITRE, actions, provenance, limitations, and judge verdict | Analyst review |
| 12 | Analyst decision | Feedback API | Stores rating/verdict/correction as pending review and optionally syncs provider feedback | Feedback record for human approval |

## 3. Investigation sequence with branches

```mermaid
sequenceDiagram
    autonumber
    actor Analyst
    participant UI as Dashboard
    participant API as FastAPI + Pydantic
    participant Guard as Guardrail Agent
    participant Triage as Flow Triage Agent
    participant SQL as SQLite / FTS5
    participant RAG as Historical RAG
    participant ML as Classifier + Anomaly
    participant Context as Synapt Knowledge
    participant Policy as Priority Policy
    participant Builder as Response Builder
    participant Judge as Safety + LLM Judge

    Analyst->>UI: Enter record ID/query/raw flow
    UI->>API: POST /investigate/flow
    API->>API: Validate types, bounds, non-empty request
    alt schema invalid
        API-->>UI: HTTP 422 validation error
    else schema valid
        API->>Guard: Validated request
        Guard->>Guard: Injection, action, relevance checks
        alt guardrail rejected
            Guard->>Context: Do not send untrusted text
            Context-->>Builder: Investigation halted message
        else guardrail passed
            Guard->>Triage: Approved request
            alt record_id supplied
                Triage->>SQL: SELECT full flow by record_id
                alt record absent
                    SQL-->>API: target_not_found
                    API-->>UI: HTTP 404
                else record found
                    SQL-->>Triage: Full telemetry + provenance
                end
            else raw flow supplied
                Triage->>Triage: Validate finite/non-negative telemetry
            else query-only
                Triage->>Triage: Mark telemetry unassessed
            end
            Triage->>RAG: Query, family filter, target exclusion
            par keyword channel
                RAG->>SQL: FTS5 BM25 query
                SQL-->>RAG: Ranked keyword candidates
            and semantic channel
                RAG->>Context: Similar incident query
                Context-->>RAG: Semantic text/chunks or empty result
            end
            RAG->>RAG: Reciprocal-rank fusion and limit
            RAG-->>ML: Target flow + similar incidents
            opt target telemetry exists
                ML->>ML: Classify family/confidence/risk
                ML->>ML: Explain top deviations
                ML->>ML: Score anomaly
            end
            ML->>Context: Sanitized family-specific knowledge query
            Context-->>Policy: Knowledge answer or local fallback
            Policy->>Policy: Apply deterministic P1-P4 rules
            Policy->>Builder: Priority, rationale, missing context
            Builder->>Builder: Assemble steps, recommendations, provenance, limits
            Builder->>Judge: Candidate package + observed evidence
            Judge->>Judge: Hard automated-action safety check
            opt evaluator provider available
                Judge->>Context: Four-dimension rubric prompt
                Context-->>Judge: Structured scores/critique
            end
            Judge-->>API: Final workflow state
            API-->>UI: FlowInvestigationResponse
            UI-->>Analyst: Evidence and human decision controls
        end
    end
```

## 4. Historical similarity-search flow

```mermaid
flowchart LR
    Request["Query + optional family filter"] --> Structured["SQLite structured search"]
    Request --> KW["FTS5 BM25 keyword channel"]
    Request --> Semantic["Synapt semantic channel"]
    KW --> Fusion["Candidate correlation + RRF"]
    Semantic --> Fusion
    Fusion --> Exclude["Exclude current record"]
    Exclude --> Filter["Apply attack-family filter"]
    Filter --> Limit["Sort by RRF score and limit"]
    Limit --> Evidence["Structured rows + historical incident evidence + limitations"]
```

The FTS5 corpus contains selected textual incident summaries, not all 2.3 million raw rows. If the fused set is too small, the current implementation pads the response with random baseline corpus records; those padding records are clearly a current implementation limitation rather than guaranteed semantic matches.

## 5. Prediction and explainability flow

```mermaid
flowchart LR
    Flow["Full flow telemetry"] --> Features["65-feature extraction"]
    Features --> Classifier["HistGradientBoostingClassifier"]
    Features --> Isolation["IsolationForest"]
    Classifier --> Probs["Nine class probabilities"]
    Probs --> Family["Predicted family + confidence"]
    Probs --> Risk["Intrusion risk = 1 - P(benign)"]
    Features --> Baseline["Compare with benign baseline"]
    Baseline --> Explain["Top five relative deviations"]
    Isolation --> Anomaly["Raw score → normalized score + threshold flag"]
    Family --> Policy["Priority policy"]
    Risk --> Policy
    Anomaly --> Policy
```

## 6. Feedback and improvement flow

```mermaid
flowchart LR
    Analyst["Analyst rating, verdict,<br/>notes, optional corrected family"] --> Pending[("pending_review")]
    Pending --> Review{"Human review gate"}
    Review -->|reject| Rejected["rejected"]
    Review -->|accept| Accepted["accepted"]
    Accepted --> Improve["POST /feedback/improve"]
    Improve --> Holdout["Random 2,000-row SQLite holdout"]
    Holdout --> Baseline["Evaluate active classifier"]
    Baseline --> Candidate["Write candidate bundle"]
    Candidate --> Report["Benchmark JSON + promotion/retention decision"]
    Analyst -. optional .-> SynaptFeedback["trident_feedback"]
```

The review gate and benchmark report are implemented. The current candidate is copied from the active model and accepted corrections are counted but not used in a fitting step, so the loop is operational as governance and reporting but does not yet learn from corrections.

## 7. Evaluation flow

```mermaid
flowchart LR
    Fixtures["40 JSON evaluation fixtures"] --> Cases["DeepEval LLMTestCase objects"]
    Cases --> Safety["Local injection/safety acceptance rule"]
    Safety --> Fixed["Accepted-case score = 0.95"]
    Adapter["SynaptDeepEvalLLM provider adapter"] -. available for judge/evaluation calls .-> Cases
    Fixed --> Gate["Zero critical violations<br/>pass rate ≥ 0.85"]
    Gate --> JSON["deepeval_evaluation_results.json"]
```

The adapter supports external evaluator providers, but the current benchmark does not instantiate DeepEval faithfulness, answer-relevancy, contextual-precision, or G-Eval metrics. Its report demonstrates fixture traversal and the local safety gate.

## 8. Endpoint routing map

| Endpoint | Primary service path | Reads | Writes | Main result |
|---|---|---|---|---|
| `GET /` | Static dashboard | UI file | None | Analyst interface |
| `GET /health` | Store/model/config indicators | SQLite, loaded objects, environment | None | Readiness summary |
| `GET /api/synapt/agents` | Configured-agent presentation | Environment | None | Masked role/status list |
| `POST /search/incidents` | Store + HistoricalIncidentRAG | SQLite/FTS5, Synapt | None | Structured matches and RAG evidence |
| `POST /investigate/flow` | Seven-stage LangGraph | SQLite/FTS5, models, Synapt | None | Full incident analysis |
| `POST /chat` | ChatService | SQLite, classifier, Synapt | None | Conversational analysis |
| `POST /feedback` | ContinuousImprovementEngine + optional Synapt | Current request context | SQLite feedback, optional provider feedback | Feedback ID/status |
| `POST /feedback/review` | Human approval gate | SQLite feedback | Feedback status | Accepted/rejected state |
| `POST /feedback/improve` | Improvement engine | Accepted feedback, flows, active model | Candidate model and benchmark report | Promotion/retention report |

## 9. Data ownership and trust boundaries

| Boundary | Trusted owner | Rule |
|---|---|---|
| Raw network-flow evidence | SQLite | Source of truth for record features and provenance |
| Historical keyword index | SQLite FTS5 | Deterministic BM25 retrieval over selected summaries |
| Semantic procedures/context | Synapt | External knowledge channel; failure must degrade safely |
| Attack and anomaly predictions | Local model artifacts | Probabilistic outputs; must retain scores and explanations |
| Priority | Deterministic policy | Explicit rules; unknown asset context must be disclosed |
| Response actions | Human analyst | Assistant only drafts recommendations; no automated containment |
| Feedback acceptance | Human reviewer | Only accepted corrections enter improvement consideration |
| Judge output | Model plus deterministic safety gate | Provider score cannot override hard action-safety failure |

## 10. Failure and degradation paths

| Failure | System behavior |
|---|---|
| Schema violation | FastAPI returns HTTP 422 before workflow execution |
| Prompt injection/prohibited action | Guardrail rejects the request and prevents untrusted context from reaching Synapt |
| Explicit record missing | API returns HTTP 404 without substituting a different flow |
| Invalid raw telemetry | Workflow rejects the flow contract |
| No telemetry | Classification, risk, and anomaly fields remain unassessed |
| Synapt unavailable | Semantic channel becomes empty and knowledge/chat use deterministic local fallback |
| Anomaly model unavailable at startup | Service continues with anomaly inference disabled |
| Judge provider unavailable/unparsable | Hard safety checks plus fixed rubric defaults remain active |
| Missing IP/port/time metadata | API discloses unsupported filtering because those columns are absent from the local export |

## 11. Physical project mapping

| Architecture element | Source/artifact |
|---|---|
| API and route wiring | `src/cyber_assistant/main.py` |
| Contracts | `src/cyber_assistant/schemas.py` |
| Investigation state and agents | `src/cyber_assistant/workflow.py` |
| Guardrails | `src/cyber_assistant/guardrails.py` |
| Structured store | `src/cyber_assistant/sqlite_store.py` |
| Historical RAG | `src/cyber_assistant/rag/historical_rag.py` |
| Classifier and explanations | `src/cyber_assistant/ml/predictor.py` |
| Anomaly scoring | `src/cyber_assistant/ml/anomaly.py` |
| Priority policy | `src/cyber_assistant/policy.py` |
| Knowledge provider adapter | `src/cyber_assistant/synapt/client.py` |
| Judge | `src/cyber_assistant/judge/evaluator.py` |
| Chat | `src/cyber_assistant/chat.py` |
| Feedback/improvement | `src/cyber_assistant/feedback/improvement.py` |
| DeepEval adapter and fixtures | `src/cyber_assistant/evaluation/deepeval_adapter.py`, `tests/data/deepeval_test_cases.json` |
| Dashboard | `src/cyber_assistant/ui/index.html` |
| Data/model scripts | `scripts/ingest_parquet_to_sqlite.py`, `train_ml_models.py`, `train_anomaly_detector.py`, `seed_historical_rag_corpus.py` |
