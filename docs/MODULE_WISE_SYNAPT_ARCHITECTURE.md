# CyberSentinel Copilot — Module-Wise Architecture with Synapt Agent Flow

This view groups the project by executable module and aligns each Synapt role with the investigation stage that consumes it. The three Synapt agents shown in the dashboard are logical read-only roles; the current Python runtime sends their retrieval requests through one shared `SynaptClient` and one configured Synapt provider.

## Module-wise architecture

```mermaid
flowchart TB
    subgraph Presentation["1 · Presentation Module"]
        Analyst["SOC analyst"]
        UI["ui/index.html<br/>investigation · search · chat · feedback"]
        Analyst --> UI
    end

    subgraph API["2 · API and Contract Module"]
        Main["main.py · FastAPI route composition"]
        Schemas["schemas.py · Pydantic contracts"]
        Mapper["Workflow-state → response mapper"]
        Main --> Schemas
        Main --> Mapper
    end

    subgraph Orchestration["3 · Investigation Orchestration Module · workflow.py"]
        Guard["1. guardrail_agent"]
        Triage["2. flow_triage_agent"]
        ML["3. ml_analysis_agent"]
        Knowledge["4. synapt_knowledge_agent"]
        Priority["5. prioritization_agent"]
        Response["6. response_recommendation_agent"]
        Judge["7. judge_review_agent"]
        Guard --> Triage --> ML --> Knowledge --> Priority --> Response --> Judge
    end

    subgraph Services["4 · Domain Service Modules"]
        Guardrails["guardrails.py<br/>injection · relevance · telemetry validation"]
        Store["sqlite_store.py<br/>exact flow lookup and structured search"]
        HistRAG["rag/historical_rag.py<br/>BM25 + semantic channel + RRF"]
        Predictor["ml/predictor.py<br/>classification · risk · explanations"]
        Anomaly["ml/anomaly.py<br/>IsolationForest scoring"]
        Policy["policy.py<br/>deterministic P1–P4 rules"]
        JudgeService["judge/evaluator.py<br/>hard safety + rubric evaluation"]
        Chat["chat.py<br/>conversational SOC copilot"]
        Improvement["feedback/improvement.py<br/>review and benchmark lifecycle"]
        EvalAdapter["evaluation/deepeval_adapter.py<br/>provider adapter"]
    end

    subgraph SynaptRoles["5 · Synapt Logical Agent Roles — aligned to consuming stages"]
        HistoricalAgent["historical-incident-rag-agent<br/>role: semantic incident similarity<br/>declared tools: trident_search, trident_query"]
        KnowledgeAgent["incident-knowledge-agent<br/>role: NIST/MITRE/SOP reasoning<br/>declared tools: trident_query, trident_get_procedures"]
        JudgeAgent["judge-review-agent<br/>role: safety and grounding review<br/>declared tool: trident_query"]
    end

    subgraph SynaptRuntime["6 · Shared Synapt Runtime Boundary"]
        Client["synapt/client.py · SynaptClient<br/>TLS · authentication · initialize · tools/list · tools/call"]
        Select["retrieve() tool selection<br/>prefer trident_query; fallback trident_search"]
        Provider[("Synapt Context Substrate<br/>provider: assist_cyber")]
        Client --> Select --> Provider
    end

    subgraph State["7 · Data, Model, and Report Module"]
        Flows[("SQLite flows<br/>2,313,810 rows")]
        FTS[("291 summaries + FTS5 index")]
        Feedback[("analyst_feedback")]
        Classifier["attack_classifier.joblib<br/>65 features · 9 families"]
        AnomalyModel["anomaly_detector.joblib"]
        Candidate["attack_classifier_candidate.joblib"]
        Reports["JSON benchmark/evaluation reports"]
    end

    UI <-->|"HTTP / JSON"| Main
    Main -->|"POST /investigate/flow"| Guard
    Guard --> Guardrails
    Triage --> Store
    Triage --> HistRAG
    Store --> Flows
    HistRAG --> FTS
    ML --> Predictor
    ML --> Anomaly
    Predictor --> Classifier
    Anomaly --> AnomalyModel
    Priority --> Policy
    Judge --> JudgeService
    JudgeService --> EvalAdapter
    Judge --> Mapper --> UI

    Triage -->|"similar-incident request"| HistoricalAgent
    Knowledge -->|"procedure/context request"| KnowledgeAgent
    Judge -->|"rubric request"| JudgeAgent
    HistoricalAgent -. "logical role" .-> Client
    KnowledgeAgent -. "logical role" .-> Client
    JudgeAgent -. "logical role" .-> Client

    Main -->|"POST /search/incidents"| HistRAG
    Main -->|"POST /chat"| Chat
    Chat --> Store
    Chat --> Predictor
    Chat --> KnowledgeAgent
    Main -->|"feedback routes"| Improvement
    Improvement --> Feedback
    Improvement --> Candidate
    Improvement --> Reports
    Main -. "optional trident_feedback" .-> Client

    UI --> Human["Human analyst verification and response decision"]
    Human -->|"rating, verdict, correction"| Improvement
```

## Main request flow by module

| Order | Orchestration stage | Python module/service | Synapt alignment | Data/model dependency | Output |
|---:|---|---|---|---|---|
| 1 | API entry | `main.py`, `schemas.py` | None | Request contracts | Validated investigation request |
| 2 | `guardrail_agent` | `guardrails.py` | Provider call blocked for rejected text | Regex and telemetry policy | Passed/rejected state |
| 3 | `flow_triage_agent` | `sqlite_store.py`, `rag/historical_rag.py` | `historical-incident-rag-agent` logical role | Flows, incident summaries, FTS5 | Target flow and ranked similar incidents |
| 4 | `ml_analysis_agent` | `ml/predictor.py`, `ml/anomaly.py` | None | Classifier and anomaly bundles | Family, risk, deviations, anomaly, MITRE |
| 5 | `synapt_knowledge_agent` | `synapt/client.py` | `incident-knowledge-agent` logical role | Synapt provider knowledge corpus | Procedures, ATT&CK context, verification steps |
| 6 | `prioritization_agent` | `policy.py` | None | Prediction/anomaly state | P1–P4 priority, rationale, missing context |
| 7 | `response_recommendation_agent` | `workflow.py` response builder | Uses previously retrieved knowledge | State, provenance, limitations | Investigation and response package |
| 8 | `judge_review_agent` | `judge/evaluator.py`, `evaluation/deepeval_adapter.py` | `judge-review-agent` logical role | Candidate package and observed telemetry | Safety/quality verdict |
| 9 | Response mapping | `main.py`, `schemas.py` | None | Final LangGraph state | `FlowInvestigationResponse` |
| 10 | Human review | `ui/index.html`, feedback routes | Optional provider feedback tool | `analyst_feedback` | Analyst decision and reviewed feedback |

## Aligned Synapt agent flow

```mermaid
sequenceDiagram
    participant Triage as flow_triage_agent
    participant Hist as historical-incident-rag-agent role
    participant Knowledge as synapt_knowledge_agent
    participant Intel as incident-knowledge-agent role
    participant JudgeStage as judge_review_agent
    participant JudgeRole as judge-review-agent role
    participant Client as Shared SynaptClient
    participant Provider as Synapt assist_cyber

    par Similarity path
        Triage->>Hist: Natural-language incident query
        Hist->>Client: Logical role handoff
        Client->>Provider: retrieve(): trident_query preferred, otherwise trident_search
        Provider-->>Client: Structured content/chunks
        Client-->>Triage: Semantic candidate text
    and Knowledge path
        Knowledge->>Intel: Family-specific procedure question
        Intel->>Client: Logical role handoff
        Client->>Provider: retrieve(): trident_query preferred
        Provider-->>Client: NIST/MITRE/context answer
        Client-->>Knowledge: Evidence and analysis
    and Judge path
        JudgeStage->>JudgeRole: Four-dimension rubric prompt
        JudgeRole->>Client: Logical role handoff
        Client->>Provider: retrieve(): trident_query preferred
        Provider-->>Client: Judge JSON/text
        Client-->>JudgeStage: Parsed scores or fallback
    end
```

## Important runtime alignment note

`/api/synapt/agents` reads three environment entries and presents their names, status, scope, and declared tools. The investigation code does not currently select a different credential or MCP connection for each role. `HistoricalIncidentRAG`, `synapt_knowledge_agent`, `ResponseJudge`, and `ChatService` all use the same `SynaptClient.retrieve()` method, which discovers provider tools and prefers `trident_query` whenever it is available. The diagram therefore distinguishes logical role alignment from the physical shared-client/provider flow.

## Supporting module flows

| API path | Modules | Synapt role/path | Local dependencies |
|---|---|---|---|
| `/search/incidents` | `main.py` → `sqlite_store.py` + `HistoricalIncidentRAG` | Historical RAG role through shared client | Flows + FTS5 summaries |
| `/chat` | `main.py` → `ChatService` | Knowledge role through shared client | Flow store + classifier + MITRE map |
| `/feedback` | `main.py` → `ContinuousImprovementEngine` | Direct optional `trident_feedback`; not one of the read-only role flows | Feedback table |
| `/feedback/review` | `ContinuousImprovementEngine` | None | Feedback status |
| `/feedback/improve` | `ContinuousImprovementEngine` | None | Accepted feedback + flows + active model |
| `/health` | `main.py`, `SQLiteIncidentStore` | Configuration status only | SQLite + loaded model objects |
| `/api/synapt/agents` | `main.py` | Displays the three logical roles | Environment entries |

## Module boundaries

- `workflow.py` owns sequencing and state movement; it does not own database access, model fitting, or provider transport.
- `sqlite_store.py` owns exact record evidence; `HistoricalIncidentRAG` owns selected-summary retrieval.
- Local ML produces probabilistic predictions. `policy.py` converts those outputs into deterministic priority.
- The Synapt roles supply read-only context and review. They do not execute containment or mutate infrastructure.
- The response module drafts actions, and the analyst owns the final decision.
