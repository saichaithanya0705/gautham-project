"""Conversational SOC Analyst Copilot Service.

Combines multi-turn dialogue, real-time SQLite flow telemetry, ML intrusion predictions,
and Synapt Context Substrate reasoning.
"""

from __future__ import annotations

import re
from typing import Any

from cyber_assistant.guardrails import check_input_guardrail, is_cybersecurity_relevant
from cyber_assistant.ml.predictor import IntrusionPredictor
from cyber_assistant.schemas import ChatRequest, ChatResponse
from cyber_assistant.sqlite_store import SQLiteIncidentStore
from cyber_assistant.synapt.client import SynaptClient
from cyber_assistant.workflow import MITRE_TACTIC_MAP


class ChatService:
    def __init__(
        self,
        store: SQLiteIncidentStore,
        synapt: SynaptClient,
        predictor: IntrusionPredictor,
    ):
        self.store = store
        self.synapt = synapt
        self.predictor = predictor

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        if not request.messages:
            return ChatResponse(reply="Hello Analyst. How can I assist you with investigating network telemetry today?")

        last_msg = request.messages[-1].content.strip()
        
        # 1. Input Guardrails (Prompt Injections & Prohibited Actions)
        is_allowed, status_str, violation = check_input_guardrail(last_msg)
        injection_patterns = [
            r"ignore previous instructions",
            r"drop\s+table",
            r"delete\s+from",
            r"system\s*prompt",
            r"auto(mated)?\s+containment",
            r"block\s+ip\s+automatically",
        ]
        if not is_allowed or any(re.search(pat, last_msg, re.IGNORECASE) for pat in injection_patterns):
            return ChatResponse(
                reply=(
                    "⚠️ **Security Guardrail Triggered**: The requested instruction was blocked. "
                    "This assistant operates under read-only decision support guidelines and **strictly prohibits automated containment actions** "
                    "(such as automated firewall blocking or script execution). All containment decisions require verified human analyst authorization."
                )
            )

        # 2. Domain Relevance Guardrail (Reject off-topic or random questions)
        is_relevant, irrelevance_msg = is_cybersecurity_relevant(
            last_msg,
            has_flow_context=(request.record_id is not None)
        )
        if not is_relevant:
            return ChatResponse(reply=irrelevance_msg)

        # 3. Conversational Greeting & Capability Introduction
        greeting_pattern = r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|who\s+are\s+you|what\s+can\s+you\s+do|help|what\s+is\s+this)(\s+there|\s+assistant|\s+bot|[!?.]*)*$"
        if re.match(greeting_pattern, last_msg.strip(), re.IGNORECASE):
            return ChatResponse(
                reply=(
                    "👋 **Hello Analyst! Welcome to the CyberSentinel Incident Response Copilot.**\n\n"
                    "### 🛡️ What is the Scenario Here?\n"
                    "You are operating in a **Security Operations Center (SOC)** environment investigating suspicious enterprise network traffic. "
                    "This system serves as your **AI-Powered Incident Response Copilot**, analyzing **2,313,810 network telemetry flows** from the **CIC-IDS2017** benchmark dataset to detect intrusions, classify attack vectors, and recommend containment actions.\n\n"
                    "### 🔍 Key Capabilities You Can Test:\n"
                    "- **Investigate specific flow records**: Ask `Analyze flow #2039912` or `Inspect record #450000`.\n"
                    "- **Threat analysis**: Ask `What are the indicators of a DoS Hulk attack?` or `Explain PortScan MITRE T1046`.\n"
                    "- **Incident Response Playbooks**: Ask `What are the NIST containment steps for SSH brute force?`.\n"
                    "- **Loaded Flow Context**: Once an incident is loaded, ask `Why was this flagged?` or `What should I do next?`.\n\n"
                    "> ℹ️ *Safety Note: Decision support aid only. All containment actions require manual human review.*"
                )
            )

        # 3. Detect Flow Reference
        # Check if user explicitly asked about a specific record ID in this message
        explicit_rec_match = re.search(r"(?:flow|record|incident|id)\s*(?:#|\bid)?\s*(\d+)", last_msg, re.IGNORECASE)
        rec_id = int(explicit_rec_match.group(1)) if explicit_rec_match else None

        # If user did not name a flow explicitly, check if they asked a follow-up about the loaded record_id
        if rec_id is None and request.record_id is not None:
            user_refers_to_flow = bool(re.search(
                r"\b(this|it|that|these|the|current|loaded|investigat\w*|flow|record|alert|incident|telemetry|traffic|finding|connection|session|why|should|safe|dangerous|action)\b",
                last_msg,
                re.IGNORECASE
            ))
            if user_refers_to_flow:
                rec_id = request.record_id

        flow_context = None
        mitre_tactics = None
        flow_summary = ""

        if rec_id:
            flow = self.store.get_flow_by_id(rec_id)
            if flow:
                pred = self.predictor.predict_flow(flow)
                family = pred["predicted_family"]
                mitre_tactics = MITRE_TACTIC_MAP.get(family, [])
                flow_context = {
                    "record_id": rec_id,
                    "attack_label": flow.get("attack_label"),
                    "attack_family": family,
                    "protocol": flow.get("protocol"),
                    "flow_duration_us": flow.get("flow_duration"),
                    "risk_score": pred["risk_score"],
                    "severity": pred["severity"],
                    "confidence": pred["confidence"],
                    "top_deviations": pred["top_feature_attributions"],
                }
                dev_text = ", ".join([f"{d['feature']} ({d['observed_value']} vs baseline {d['benign_baseline']})" for d in pred["top_feature_attributions"][:3]])
                flow_summary = (
                    f"Referenced Flow #{rec_id} Telemetry:\n"
                    f"- Classified as: {family} ({flow.get('attack_label')}) with {pred['confidence']*100:.1f}% confidence\n"
                    f"- Risk Score: {pred['risk_score']*100:.1f}% ({pred['severity']} Severity)\n"
                    f"- Duration: {flow.get('flow_duration'):,} µs, Protocol: {flow.get('protocol')}\n"
                    f"- Key Anomalies: {dev_text}\n"
                )
            else:
                flow_summary = (
                    f"⚠️ **Target Flow Record #{rec_id} Not Found**: No telemetry record with ID #{rec_id} exists in the 2.31M SQLite flow dataset."
                )

        # 3. Query Synapt Context Substrate
        synapt_question = last_msg
        if flow_summary:
            synapt_question = f"{flow_summary}\nAnalyst Question: {last_msg}"

        synapt_reply = ""
        try:
            res = await self.synapt.retrieve(synapt_question)
            if res and isinstance(res[0], dict):
                structured = res[0].get("structuredContent") or {}
                synapt_reply = structured.get("answer") or res[0].get("answer") or ""
        except Exception:
            synapt_reply = ""

        # 4. Formulate Comprehensive Assistant Reply
        reply_parts = []
        if flow_summary:
            reply_parts.append(f"### 🔍 Telemetry Triage: Flow #{rec_id}\n{flow_summary}")

        if synapt_reply and synapt_reply != "The answer is not available in the provided context.":
            reply_parts.append(f"### 🛡️ Synapt Context Substrate Analysis\n{synapt_reply}")
        else:
            # Deterministic Fallback if Synapt answer is sparse
            if flow_context:
                family = flow_context["attack_family"]
                reply_parts.append(
                    f"### 🛡️ Security Analysis ({family.upper()})\n"
                    f"Based on the extracted telemetry, this flow exhibits patterns consistent with **{family}** activity.\n"
                    f"- **Intrusion Risk**: {flow_context['risk_score']*100:.1f}% ({flow_context['severity']})\n"
                    f"- **Recommended Verification**: Review whether repeated similar flows occurred around this session. "
                    f"Check internal firewall connection tracking logs for asymmetric half-open connections."
                )
            else:
                reply_parts.append(
                    "### 🛡️ Cybersecurity Analyst Guidance\n"
                    "I am analyzing the CIC-IDS2017 historical benchmark across 2.31M flow records alongside curated MITRE ATT&CK playbooks.\n\n"
                    "You can ask me to:\n"
                    "- Investigate specific flows: *'Analyze flow 2039912'*\n"
                    "- Explain traffic characteristics: *'What are the key indicators of a DoS Hulk flood?'*\n"
                    "- Review playbooks: *'What are the NIST containment steps for SSH brute force?'*"
                )

        if mitre_tactics:
            tactics_md = ", ".join([f"**{m['id']}** ({m['name']} - *{m['tactic']}*)" for m in mitre_tactics])
            reply_parts.append(f"**MITRE ATT&CK Mapping:** {tactics_md}")

        reply_parts.append(
            "\n> ℹ️ *Safety Note: Decision support aid only. All containment actions require manual human review.*"
        )

        return ChatResponse(
            reply="\n\n".join(reply_parts),
            flow_context=flow_context,
            mitre_tactics=mitre_tactics,
            provenance={
                "synapt_provider": self.synapt.provider_id,
                "dataset": "CIC-IDS2017 SQLite (data/cicids2017.sqlite3)",
                "ml_model": "HistGradientBoostingClassifier v1.0",
            }
        )
