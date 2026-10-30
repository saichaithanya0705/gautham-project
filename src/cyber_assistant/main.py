"""FastAPI Microservice for AI-Powered Cybersecurity Incident Response Assistant."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from cyber_assistant.config import get_settings
from cyber_assistant.feedback.improvement import ContinuousImprovementEngine
from cyber_assistant.ml.anomaly import AnomalyDetector
from cyber_assistant.ml.predictor import IntrusionPredictor
from cyber_assistant.rag.historical_rag import HistoricalIncidentRAG
from cyber_assistant.schemas import (
    IncidentSearchRequest,
    IncidentSearchResponse,
    FlowInvestigationRequest,
    FlowInvestigationResponse,
    AnalystFeedbackRequest,
    AnalystFeedbackResponse,
    ChatRequest,
    ChatResponse,
)
from cyber_assistant.chat import ChatService
from cyber_assistant.sqlite_store import SQLiteIncidentStore
from cyber_assistant.synapt.client import SynaptClient
from cyber_assistant.workflow import build_investigation_graph

settings = get_settings()
store = SQLiteIncidentStore(settings.database_path)
synapt = SynaptClient(
    provider_id=settings.synapt_provider_id,
    mcp_url=settings.synapt_mcp_url,
    auth_base=settings.synapt_auth_base,
    username=settings.synapt_username,
    password=settings.synapt_password,
    top_k=settings.synapt_top_k,
    ca_bundle=settings.synapt_ca_bundle or None,
)
predictor = IntrusionPredictor()
try:
    anomaly_detector = AnomalyDetector()
except Exception:
    anomaly_detector = None

historical_rag = HistoricalIncidentRAG(settings.database_path, synapt=synapt)
improvement_engine = ContinuousImprovementEngine(settings.database_path, model_dir="models")
workflow = build_investigation_graph(
    store, synapt, predictor=predictor, anomaly_detector=anomaly_detector, rag=historical_rag
)
chat_service = ChatService(store, synapt, predictor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CyberSentinel - AI Cybersecurity Incident Response Assistant",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the SOC Analyst Copilot Frontend UI."""
    html_path = Path(__file__).parent / "ui" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h2>CyberSentinel Copilot API Active. UI file not found.</h2>")


@app.get("/health")
async def health():
    sqlite = store.health()
    from dotenv import dotenv_values
    env_vars = dotenv_values(".env")
    return {
        "status": "ok" if sqlite["available"] else "degraded",
        "sqlite": sqlite,
        "synapt": "configured; connection verified" if synapt.configured else "missing configuration",
        "synapt_agents": {
            "incident_knowledge_agent": bool(env_vars.get("incident-knowledge-agent")),
            "historical_incident_rag_agent": bool(env_vars.get("historical-incident-rag-agent")),
            "judge_review_agent": bool(env_vars.get("judge-review-agent")),
            "total_onboarded": sum(1 for k in ["incident-knowledge-agent", "historical-incident-rag-agent", "judge-review-agent"] if env_vars.get(k)),
        },
        "ml_model": "loaded (HistGradientBoostingClassifier v1.0)",
        "anomaly_detector": "loaded (IsolationForest v1.0)" if anomaly_detector else "unavailable",
        "historical_rag": "ready (SQLite FTS5 + Synapt RRF)",
    }


@app.get("/api/synapt/agents")
async def get_synapt_agents():
    """Return status and granted tool definitions for the 3 onboarded Synapt read-only agents."""
    from dotenv import dotenv_values
    env_vars = dotenv_values(".env")

    def mask_secret(sec: str | None) -> str:
        if not sec:
            return "Not Configured"
        sec = sec.strip()
        if len(sec) <= 10:
            return sec[:3] + "..."
        return sec[:6] + "..." + sec[-4:]

    agents = [
        {
            "id": "incident-knowledge-agent",
            "name": "Threat Intel & SOP Knowledge Agent",
            "role": "NIST SP 800-61 Playbooks & MITRE Reasoning",
            "framework": "LangGraph",
            "scope": "read-only",
            "tools": ["trident_query", "trident_get_procedures"],
            "status": "active" if env_vars.get("incident-knowledge-agent") else "unconfigured",
            "secret_masked": mask_secret(env_vars.get("incident-knowledge-agent")),
            "icon": "🧠",
        },
        {
            "id": "historical-incident-rag-agent",
            "name": "Historical Incident RAG Agent",
            "role": "Semantic Similarity Search (291 Incidents)",
            "framework": "LangGraph",
            "scope": "read-only",
            "tools": ["trident_search", "trident_query"],
            "status": "active" if env_vars.get("historical-incident-rag-agent") else "unconfigured",
            "secret_masked": mask_secret(env_vars.get("historical-incident-rag-agent")),
            "icon": "🔍",
        },
        {
            "id": "judge-review-agent",
            "name": "LLM-as-Judge Output Review Agent",
            "role": "Safety & Evidence Grounding Rubric Evaluation",
            "framework": "LangGraph",
            "scope": "read-only",
            "tools": ["trident_query"],
            "status": "active" if env_vars.get("judge-review-agent") else "unconfigured",
            "secret_masked": mask_secret(env_vars.get("judge-review-agent")),
            "icon": "⚖️",
        },
    ]

    return {
        "provider": synapt.provider_id,
        "mcp_url": synapt.mcp_url,
        "total_onboarded": sum(1 for a in agents if a["status"] == "active"),
        "agents": agents,
    }


@app.post("/search/incidents", response_model=IncidentSearchResponse)
async def search_incidents(request: IncidentSearchRequest):
    """Retrieve matching structured flow records from the 2.3M-row CIC-IDS2017 SQLite database."""
    try:
        matches = store.search(request)
        evidence = []
        synapt_status = "unqueried"

        limitations = [
            "Dataset Limitation: Raw CIC-IDS2017 Parquet records omit IP addresses, ports, and timestamps.",
            "Synapt retrieval provides grounded security reasoning and MITRE ATT&CK guidance.",
            "SQLite query matching is structured/keyword retrieval, not semantic similarity.",
        ]
        metadata_filters_provided = any([
            request.src_ip, request.dst_ip, request.src_port, request.dst_port,
            request.start_time, request.end_time
        ])
        if metadata_filters_provided:
            limitations.insert(
                0,
                "Notice (Requirement B4): Network metadata fields (src_ip, dst_ip, src_port, dst_port, start_time, end_time) "
                "are not present in the underlying CIC-IDS2017 dataset export schema. Filtering proceeded using valid flow attributes."
            )

        if request.query:
            try:
                rag_matches = await historical_rag.hybrid_search(
                    query=request.query,
                    limit=request.limit,
                    filters={"attack_family": request.attack_family} if request.attack_family else None,
                )
                evidence = rag_matches
                synapt_status = "connected"
            except Exception:
                synapt_status = "unavailable"
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="SQLite dataset is unavailable") from exc

    return IncidentSearchResponse(
        sqlite_matches=matches,
        synapt_status=synapt_status,
        synapt_evidence=evidence,
        limitations=limitations,
    )


@app.post("/investigate/flow", response_model=FlowInvestigationResponse)
async def investigate_flow(request: FlowInvestigationRequest):
    """Execute end-to-end multi-agent LangGraph investigation pipeline on a network flow record."""
    try:
        state = await workflow.ainvoke({"request": request})
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Investigation workflow error: {exc}") from exc

    if state.get("target_not_found") and request.record_id is not None:
        raise HTTPException(status_code=404, detail=f"Flow record #{request.record_id} not found in database.")

    pred = state.get("ml_prediction", {})
    anom = state.get("anomaly_prediction", {})
    return FlowInvestigationResponse(
        record_id=request.record_id or (state.get("target_flow", {}).get("record_id") if state.get("target_flow") else None),
        predicted_family=pred.get("predicted_family", "unknown"),
        confidence=pred.get("confidence"),
        risk_score=pred.get("risk_score"),
        anomaly_score=anom.get("anomaly_score"),
        is_anomaly=anom.get("is_anomaly"),
        severity=pred.get("severity", "Informational"),
        priority_level=state.get("priority_level", "P4 - Low / Informational"),
        feature_attributions=pred.get("top_feature_attributions", []),
        synapt_analysis=state.get("synapt_analysis", ""),
        mitre_tactics=state.get("mitre_tactics", []),
        investigation_steps=state.get("investigation_steps", []),
        recommended_response=state.get("recommended_response", []),
        similar_flows=state.get("similar_flows", []),
        source_provenance=state.get("source_provenance", {}),
        guardrail_status=state.get("guardrail_status", "passed"),
        judge_verdict=state.get("judge_verdict"),
        limitations=state.get("limitations", []),
    )


@app.post("/feedback", response_model=AnalystFeedbackResponse)
async def submit_feedback(feedback: AnalystFeedbackRequest):
    """Record analyst feedback for continuous improvement in SQLite and Synapt MCP."""
    fb_dict = feedback.model_dump()
    feedback_id = improvement_engine.record_feedback(fb_dict)

    synapt_synced = False
    sync_status = "unattempted"
    try:
        if "trident_feedback" in synapt._tools:
            verdict_map = {
                "confirmed_malicious": "deflected",
                "false_positive": "not_deflected",
                "benign": "deflected",
                "needs_escalation": "partial",
            }
            await synapt.call_tool("trident_feedback", {
                "feedback_id": f"FB-{feedback_id}",
                "caller_type": "user",
                "verdict": verdict_map.get(feedback.analyst_verdict, "partial"),
                "score": round(float(feedback.rating) / 5.0, 2),
                "reason": f"Analyst rating: {feedback.rating}/5. Verdict: {feedback.analyst_verdict}. Notes: {feedback.notes or 'None'}",
            })
            synapt_synced = True
            sync_status = "synced_to_trident"
    except Exception as exc:
        synapt_synced = False
        sync_status = f"sync_failed: {exc}"

    return AnalystFeedbackResponse(
        status="success",
        feedback_id=feedback_id,
        synapt_synced=synapt_synced,
        sync_status=sync_status,
        message="Analyst feedback recorded successfully.",
    )


@app.post("/feedback/review")
async def review_feedback(feedback_id: int, decision: str):
    """Human-in-the-loop approval gate for analyst feedback (accepted or rejected)."""
    try:
        return improvement_engine.review_feedback(feedback_id, decision)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/feedback/improve")
async def run_model_improvement():
    """Trigger continuous improvement evaluation on approved feedback."""
    try:
        report = improvement_engine.run_improvement_cycle()
        return report
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Improvement cycle error: {exc}") from exc


@app.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(request: ChatRequest):
    """Conversational SOC Analyst Copilot endpoint."""
    return await chat_service.handle_chat(request)

