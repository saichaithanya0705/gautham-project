"""Multi-Agent LangGraph Orchestration Pipeline for Cybersecurity Incident Response.

Choreographs:
1. guardrail_agent: Validates telemetry contracts and sanitizes injection/unauthorized instructions.
2. flow_triage_agent: Fetches target flow (with 404 enforcement) and runs hybrid RAG for historical incidents.
3. ml_analysis_agent: Performs supervised intrusion classification and unsupervised anomaly detection.
4. synapt_knowledge_agent: Grounded knowledge retrieval from Synapt MCP Context Substrate.
5. prioritization_agent: Evaluates deterministic P1-P4 operational priority.
6. response_recommendation_agent: Synthesizes NIST SP 800-61 playbooks with evidence provenance.
7. judge_review_agent: Evaluates generated guidance using rubric-based LLM-as-Judge validation.
"""

from __future__ import annotations

from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END

from cyber_assistant.guardrails import (
    check_input_guardrail,
    is_cybersecurity_relevant,
    sanitize_analyst_context,
    validate_telemetry_flow,
)
from cyber_assistant.judge.evaluator import ResponseJudge, JudgeVerdict
from cyber_assistant.ml.anomaly import AnomalyDetector
from cyber_assistant.ml.predictor import IntrusionPredictor
from cyber_assistant.policy import determine_incident_priority
from cyber_assistant.rag.historical_rag import HistoricalIncidentRAG
from cyber_assistant.schemas import FlowInvestigationRequest
from cyber_assistant.sqlite_store import SQLiteIncidentStore
from cyber_assistant.synapt.client import SynaptClient, SynaptUnavailable


MITRE_TACTIC_MAP = {
    "port_scan": [
        {"id": "T1046", "name": "Network Service Discovery", "tactic": "Discovery"},
        {"id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance"},
    ],
    "dos": [
        {"id": "T1498", "name": "Network Denial of Service", "tactic": "Impact"},
        {"id": "T1499", "name": "Endpoint Denial of Service", "tactic": "Impact"},
    ],
    "ddos": [
        {"id": "T1498.001", "name": "Direct Network Flood", "tactic": "Impact"},
        {"id": "T1499.001", "name": "OS Exhaustion Flood", "tactic": "Impact"},
    ],
    "brute_force": [
        {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"},
        {"id": "T1110.001", "name": "Password Guessing", "tactic": "Credential Access"},
    ],
    "web_attack": [
        {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
        {"id": "T1059.007", "name": "JavaScript Execution", "tactic": "Execution"},
    ],
    "botnet": [
        {"id": "T1071", "name": "Application Layer Protocol C2", "tactic": "Command and Control"},
        {"id": "T1573", "name": "Encrypted Channel", "tactic": "Command and Control"},
    ],
    "infiltration": [
        {"id": "T1021", "name": "Remote Services", "tactic": "Lateral Movement"},
        {"id": "T1078", "name": "Valid Accounts", "tactic": "Defense Evasion"},
    ],
    "benign": [],
}


class InvestigationState(TypedDict, total=False):
    request: FlowInvestigationRequest
    guardrail_status: str
    guardrail_violation: str | None
    target_flow: dict[str, Any] | None
    target_not_found: bool
    similar_flows: list[dict[str, Any]]
    ml_prediction: dict[str, Any]
    anomaly_prediction: dict[str, Any]
    synapt_evidence: list[dict[str, Any]]
    synapt_analysis: str
    mitre_tactics: list[dict[str, str]]
    priority_level: str
    priority_assessment: dict[str, Any]
    investigation_steps: list[str]
    recommended_response: list[str]
    judge_verdict: dict[str, Any]
    source_provenance: dict[str, Any]
    limitations: list[str]


def build_investigation_graph(
    store: SQLiteIncidentStore,
    synapt: SynaptClient,
    predictor: IntrusionPredictor | None = None,
    anomaly_detector: AnomalyDetector | None = None,
    rag: HistoricalIncidentRAG | None = None,
    judge: ResponseJudge | None = None,
):
    if predictor is None:
        predictor = IntrusionPredictor()
    if anomaly_detector is None:
        try:
            anomaly_detector = AnomalyDetector()
        except FileNotFoundError:
            anomaly_detector = None
    if rag is None:
        rag = HistoricalIncidentRAG(store.db_path, synapt=synapt)
    if judge is None:
        judge = ResponseJudge(synapt=synapt)

    # 1. Guardrail Agent
    def guardrail_agent(state: InvestigationState) -> dict[str, Any]:
        req = state["request"]
        is_allowed, status_str, violation = check_input_guardrail(req.query)
        if not is_allowed:
            return {
                "guardrail_status": status_str,
                "guardrail_violation": violation,
            }

        # Check relevance if this is a query-only investigation (no flow records supplied)
        if not req.record_id and not req.flow_data and req.query:
            is_rel, rel_err = is_cybersecurity_relevant(req.query)
            if not is_rel:
                return {
                    "guardrail_status": "rejected",
                    "guardrail_violation": rel_err or "Query is not relevant to cybersecurity or network telemetry.",
                }

        return {
            "guardrail_status": status_str,
            "guardrail_violation": violation,
        }

    # 2. Flow Triage & Retrieval Agent
    async def flow_triage_agent(state: InvestigationState) -> dict[str, Any]:
        req = state["request"]
        target_flow = None
        target_not_found = False

        if req.record_id is not None:
            target_flow = store.get_flow_by_id(req.record_id)
            if target_flow is None:
                # Explicit record was requested and does not exist: do NOT silently fallback!
                return {
                    "target_flow": None,
                    "target_not_found": True,
                    "similar_flows": [],
                }
        elif req.flow_data:
            is_valid, cleaned, err = validate_telemetry_flow(req.flow_data)
            if is_valid:
                target_flow = cleaned
            else:
                return {
                    "target_flow": None,
                    "target_not_found": False,
                    "similar_flows": [],
                    "guardrail_status": "rejected",
                    "guardrail_violation": err,
                }

        # Hybrid search for similar historical incidents
        query_text = req.query or req.attack_family or "network security anomaly"
        similar = await rag.hybrid_search(
            query=query_text,
            target_record_id=req.record_id,
            limit=req.limit_similar_flows,
            filters={"attack_family": req.attack_family} if req.attack_family else None,
        )

        return {
            "target_flow": target_flow,
            "target_not_found": False,
            "similar_flows": similar,
        }

    # 3. ML Analysis & Anomaly Detection Agent
    def ml_analysis_agent(state: InvestigationState) -> dict[str, Any]:
        target = state.get("target_flow")
        if target:
            prediction = predictor.predict_flow(target)
            anomaly_res = (
                anomaly_detector.score_flow(target)
                if anomaly_detector
                else {"anomaly_score": 0.0, "is_anomaly": False}
            )
        else:
            # Query-only or no-telemetry investigation: explicit unassessed fields
            prediction = {
                "predicted_family": state["request"].attack_family or "unassessed",
                "confidence": None,
                "risk_score": None,
                "severity": "Informational",
                "class_probabilities": {},
                "top_feature_attributions": [],
            }
            anomaly_res = {"anomaly_score": None, "is_anomaly": None}

        family = prediction["predicted_family"]
        mitre = MITRE_TACTIC_MAP.get(family, MITRE_TACTIC_MAP.get("benign", []))
        return {
            "ml_prediction": prediction,
            "anomaly_prediction": anomaly_res,
            "mitre_tactics": mitre,
        }

    # 4. Synapt Knowledge Retrieval Agent
    async def synapt_knowledge_agent(state: InvestigationState) -> dict[str, Any]:
        pred = state.get("ml_prediction", {})
        family = pred.get("predicted_family", "security incident")
        user_query = state["request"].query or ""

        # Enforce boundary: do not send rejected/prohibited inputs to Synapt
        if state.get("guardrail_status") == "rejected":
            return {
                "synapt_evidence": [],
                "synapt_analysis": f"Investigation halted: {state.get('guardrail_violation', 'Guardrail triggered')}",
            }

        safe_context = sanitize_analyst_context(user_query)
        question = (
            f"What are the investigation procedures, MITRE ATT&CK indicators, "
            f"and analyst verification steps for a {family} attack in network traffic?"
        )
        if safe_context:
            question += f"\n\n{safe_context}"

        analysis_text = "Synapt knowledge layer unavailable."
        evidence = []
        try:
            res = await synapt.retrieve(question)
            evidence = res
            if res and isinstance(res[0], dict):
                structured = res[0].get("structuredContent") or {}
                analysis_text = structured.get("answer") or res[0].get("answer") or ""
        except SynaptUnavailable:
            analysis_text = "Synapt Context Substrate is disconnected. Proceeding with deterministic local security procedures."

        return {"synapt_evidence": evidence, "synapt_analysis": analysis_text}

    # 5. Incident Prioritization Agent
    def prioritization_agent(state: InvestigationState) -> dict[str, Any]:
        pred = state.get("ml_prediction", {})
        anom = state.get("anomaly_prediction", {})
        target = state.get("target_flow")

        p_result = determine_incident_priority(
            predicted_family=pred.get("predicted_family", "unassessed"),
            confidence=pred.get("confidence"),
            risk_score=pred.get("risk_score"),
            anomaly_score=anom.get("anomaly_score"),
            is_anomaly=anom.get("is_anomaly"),
            flow_data=target,
        )

        return {
            "priority_level": p_result["priority_level"],
            "priority_assessment": p_result,
        }

    # 6. Response Recommendation & Provenance Synthesis Agent
    def response_recommendation_agent(state: InvestigationState) -> dict[str, Any]:
        pred = state.get("ml_prediction", {})
        target = state.get("target_flow")
        family = pred.get("predicted_family", "benign")

        investigation_steps = [
            f"Review flow feature deviations: Verify if observed telemetry matches known {family} anomaly profiles.",
            "Cross-reference destination protocol and target service against internal asset inventory.",
            "Determine scope: Query historical traffic records to verify whether this is an isolated probe or a distributed campaign.",
            "Inspect upstream perimeter firewalls and server logs for corresponding connection drop or error spikes.",
        ]

        recommended_response = [
            "Maintain observation: Automated containment is prohibited without human analyst verification.",
            "Prepare targeted firewall ACL rule draft if active flooding or unauthorized authentication persists.",
            "If credential brute force is suspected, audit the targeted service accounts and review authentication telemetry.",
            "Submit analyst review to the continuous improvement feedback loop.",
        ]

        provenance = {
            "sqlite_source_file": target.get("source_file") if target else None,
            "sqlite_row_number": target.get("source_row_number") if target else None,
            "sqlite_record_id": target.get("record_id") if target else None,
            "synapt_mcp_provider": synapt.provider_id,
            "ml_model": "HistGradientBoostingClassifier v1.0",
        }

        limitations = [
            "Dataset Limitation: Raw CIC-IDS2017 Parquet records omit Flow ID, IP addresses, ports, and timestamps.",
            "Analyst Safety: All containment recommendations require manual human review; automated actions are disabled.",
            "Structured queries in SQLite reflect exact parameter matching; semantic reasoning is provided by Synapt.",
        ]

        return {
            "investigation_steps": investigation_steps,
            "recommended_response": recommended_response,
            "source_provenance": provenance,
            "limitations": limitations,
        }

    # 7. LLM-as-Judge Output Review Agent
    async def judge_review_agent(state: InvestigationState) -> dict[str, Any]:
        verdict: JudgeVerdict = await judge.evaluate_response(
            candidate_analysis=state.get("synapt_analysis", ""),
            investigation_steps=state.get("investigation_steps", []),
            recommended_response=state.get("recommended_response", []),
            observed_telemetry=state.get("target_flow"),
            predicted_family=state.get("ml_prediction", {}).get("predicted_family", "unassessed"),
        )
        return {"judge_verdict": verdict.model_dump()}

    # Assemble LangGraph
    graph = StateGraph(InvestigationState)
    graph.add_node("guardrail_agent", guardrail_agent)
    graph.add_node("flow_triage_agent", flow_triage_agent)
    graph.add_node("ml_analysis_agent", ml_analysis_agent)
    graph.add_node("synapt_knowledge_agent", synapt_knowledge_agent)
    graph.add_node("prioritization_agent", prioritization_agent)
    graph.add_node("response_recommendation_agent", response_recommendation_agent)
    graph.add_node("judge_review_agent", judge_review_agent)

    # Edge choreography
    graph.add_edge(START, "guardrail_agent")
    graph.add_edge("guardrail_agent", "flow_triage_agent")
    graph.add_edge("flow_triage_agent", "ml_analysis_agent")
    graph.add_edge("ml_analysis_agent", "synapt_knowledge_agent")
    graph.add_edge("synapt_knowledge_agent", "prioritization_agent")
    graph.add_edge("prioritization_agent", "response_recommendation_agent")
    graph.add_edge("response_recommendation_agent", "judge_review_agent")
    graph.add_edge("judge_review_agent", END)

    return graph.compile()
