"""Deterministic Incident Prioritization Policy Engine.

Translates:
- Supervised classification & confidence
- Intrusion risk (1 - P(benign))
- Unsupervised anomaly flag & score
- Traffic characteristics (volumetric rate, flags, duration)
into an operational P1-P4 triage priority level with explicit rationale and missing context disclosures.
"""

from __future__ import annotations

from typing import Any


def determine_incident_priority(
    predicted_family: str,
    confidence: float | None,
    risk_score: float | None,
    anomaly_score: float | None = None,
    is_anomaly: bool | None = None,
    flow_data: dict[str, Any] | None = None,
    asset_critical: bool | None = None,
) -> dict[str, Any]:
    """Compute operational triage priority level adhering to SOC policy guidelines."""
    # Handle unassessed / no telemetry cases
    if confidence is None or risk_score is None:
        return {
            "priority_level": "P4 - Low / Informational",
            "priority_code": "P4",
            "rationale": "No telemetry was evaluated; knowledge-only or informational request.",
            "missing_context": ["telemetry_measurements_unassessed", "asset_criticality_unknown"],
        }

    family = predicted_family.lower()
    missing_context = []
    if asset_critical is None:
        missing_context.append("asset_criticality_unknown")
    missing_context.append("internal_host_identity_unverified")

    # High-impact volumetric / destructive attacks
    if family in ("ddos", "dos", "infiltration") and risk_score >= 0.70:
        return {
            "priority_level": "P1 - Critical Priority",
            "priority_code": "P1",
            "rationale": f"High-confidence {family.upper()} attack with potential service availability disruption.",
            "missing_context": missing_context,
        }

    # Active exploitation / credential spraying
    if family in ("brute_force", "web_attack") and risk_score >= 0.60:
        return {
            "priority_level": "P2 - High Priority",
            "priority_code": "P2",
            "rationale": f"Active exploitation or credential access attempt ({family}) targeting service endpoints.",
            "missing_context": missing_context,
        }

    # Reconnaissance / Scans: Do NOT default to P1. Scans are P3 unless on verified critical assets
    if family == "port_scan":
        if asset_critical:
            return {
                "priority_level": "P2 - High Priority",
                "priority_code": "P2",
                "rationale": "Reconnaissance probing targeting verified high-value critical asset.",
                "missing_context": missing_context,
            }
        return {
            "priority_level": "P3 - Medium Priority",
            "priority_code": "P3",
            "rationale": "Service discovery reconnaissance (PortScan) observed without confirmed host compromise.",
            "missing_context": missing_context,
        }

    # Botnet C2 activity
    if family == "botnet" and risk_score >= 0.50:
        return {
            "priority_level": "P2 - High Priority",
            "priority_code": "P2",
            "rationale": "Suspected Botnet Command & Control beaconing or coordinated network action.",
            "missing_context": missing_context,
        }

    # Novel statistical anomaly on benign or low-risk traffic
    if is_anomaly and (risk_score < 0.50 or family == "benign"):
        return {
            "priority_level": "P3 - Medium Priority",
            "priority_code": "P3",
            "rationale": f"Traffic classified as benign or ambiguous, but exhibits statistical anomaly (score: {anomaly_score:.2f}).",
            "missing_context": missing_context,
        }

    # Baseline traffic
    return {
        "priority_level": "P4 - Low / Informational",
        "priority_code": "P4",
        "rationale": "Traffic characteristics are consistent with benign network baselines or low-severity events.",
        "missing_context": missing_context,
    }
