"""Ingest curated cybersecurity incident response knowledge into the live Synapt MCP provider."""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cyber_assistant.config import get_settings  # noqa: E402
from cyber_assistant.synapt.client import SynaptClient  # noqa: E402


KNOWLEDGE_DOCUMENTS = {
    "mitre_attack_mappings.txt": """
# MITRE ATT&CK Technique Mapping for CIC-IDS2017

## Reconnaissance & Discovery: Port Scanning
- MITRE ID: T1046 (Network Service Discovery)
- Tactic: Discovery / Reconnaissance
- Attack Signatures: Fast TCP SYN scans (half-open scanning), UDP sweeps, stealth null/fin scans.
- Telemetry Indicators in CIC-IDS2017: Short flow duration (microseconds), high SYN flag ratio, zero or single backward response packets, small average packet sizes (40-60 bytes).
- Investigation Guidance: Determine if the scanner is an internal compromised host or external scanning engine. Identify targeted destination ports (e.g., 22 SSH, 80 HTTP, 443 HTTPS, 3389 RDP). Check whether subsequent authentication or exploit attempts occurred.

## Impact: Denial of Service (DoS & DDoS)
- MITRE ID: T1498 (Network Denial of Service), T1499 (Endpoint Denial of Service)
- Tactic: Impact
- Attack Types in Dataset:
  - DoS Hulk: Obfuscated HTTP GET flooding designed to bypass caching servers and exhaust web server threads.
  - DoS GoldenEye: Keep-Alive HTTP flood exhausting worker pools using persistent connections.
  - DoS slowloris: Extremely slow HTTP header delivery holding socket connections open indefinitely.
  - DoS Slowhttptest: Slow HTTP POST bodies tying up server thread memory.
  - DDoS: Distributed high-volume volumetric flooding.
- Telemetry Indicators: Extreme packets/second, heavy forward packet volume, asymmetrical forward-to-backward byte ratios, or in slowloris, prolonged flow duration with near-zero throughput and high idle times.
- Investigation Guidance: Triage impact on service availability; distinguish application-layer thread exhaustion from volumetric transport congestion. Verify edge CDN/WAF rate-limiting rules.

## Credential Access: Brute Force Attacks
- MITRE ID: T1110 (Brute Force - Password Guessing)
- Tactic: Credential Access
- Attack Types in Dataset: FTP-Patator, SSH-Patator.
- Telemetry Indicators: Repeated moderate-duration flows, steady packet counts per exchange, high RST (Reset) flag count indicating server authentication rejection and session teardown.
- Investigation Guidance: Identify the targeted service accounts. Review authentication failure logs and check for successful login following credential spraying.

## Initial Access: Web Application Attacks
- MITRE ID: T1190 (Exploit Public-Facing Application)
- Tactic: Initial Access / Execution
- Attack Types in Dataset: SQL Injection, Cross-Site Scripting (XSS), Web Brute Force.
- Telemetry Indicators: Elevated forward packet lengths (injected queries or scripts in HTTP headers/parameters), PSH flag set for immediate application execution.
- Investigation Guidance: Inspect web server access logs for anomalous SQL keywords (UNION, SELECT, OR 1=1) or script tags (<script>). Confirm whether backend database errors were returned.
""",

    "incident_response_playbooks.txt": """
# SOC Incident Response Standard Operating Procedures (NIST SP 800-61 Aligned)

## Phase 1: Detection & Triage
1. Triage the initial flow anomaly against historical baselines.
2. Verify confidence score, estimated attack family, and top feature deviations (e.g., abnormal SYN ratio, extreme packet rate).
3. Determine scope: Is the alert an isolated scanning probe or active exploitation in progress?

## Phase 2: Evidence Collection & Correlation
1. Query SQLite historical flows for matching protocol, flow duration, and flag patterns.
2. Cross-reference with host asset criticality (e.g., domain controllers, database servers, DMZ web proxies).
3. Check for multi-stage behavior: Did a PortScan precede a Brute Force or Web Attack attempt?

## Phase 3: Containment Decision Criteria (Human-in-the-Loop)
- CRITICAL PRINCIPLE: The AI Assistant provides decision support only. Automated containment actions (such as blocking firewall ports or null-routing IP addresses) are prohibited without explicit human authorization.
- Containment Checklist:
  1. Confirm evidence of malicious intent vs. benign vulnerability scanner (e.g., Qualys, Nessus).
  2. Evaluate business impact of isolating targeted host or blocking traffic upstream.
  3. Prepare firewall or ACL change tickets with peer analyst review.

## Phase 4: Eradication & Recovery
1. Terminate unauthorized sessions and close unnecessary listening ports.
2. Patch exploited web vulnerabilities or enforce multi-factor authentication (MFA) on brute-forced services.
3. Validate restoration of normal traffic metrics (flow rates, error rates, latency).
""",

    "traffic_features_guide.txt": """
# CIC-IDS2017 Traffic Features & Anomaly Interpretation Guide

- Flow Duration: Total duration of the network connection in microseconds. Zero or near-zero duration indicates rapid scanning; multi-minute duration with minimal traffic indicates slowloris or persistent C2 beaconing.
- Flow Bytes/s and Flow Packets/s: Volume rate indicators. Volumetric DoS and DDoS exhibit spikes orders of magnitude above benign traffic baselines.
- SYN Flag Count & syn_ratio: Synchronize flag frequency. Elevated SYN ratios with missing ACK/FIN flags characterize TCP SYN flooding and port reconnaissance.
- RST Flag Count & rst_ratio: Reset flag frequency. High RST rates occur when connections are rejected, common in brute-force authentication failures and probing closed ports.
- Total Fwd Packets vs Total Backward Packets (fwd_bwd_packet_ratio): Measures conversational balance. Healthy HTTP/TLS flows exhibit bidirectional data exchange. Malicious scans and floods are heavily forward-dominant.
- Inter-Arrival Times (Flow IAT Mean/Std/Max/Min): Measures timing between packets. High consistency (low IAT variability) points to automated scripting or malware beaconing, whereas human interaction has high IAT variance.
- Active & Idle Statistics: Active/idle timers quantify burstiness. Abnormally high idle time inside an active flow indicates slow-rate denial-of-service tactics.
"""
}


async def main() -> int:
    settings = get_settings()
    client = SynaptClient(
        provider_id=settings.synapt_provider_id,
        mcp_url=settings.synapt_mcp_url,
        auth_base=settings.synapt_auth_base,
        username=settings.synapt_username,
        password=settings.synapt_password,
        top_k=settings.synapt_top_k,
    )
    if not client.configured:
        print("Synapt configuration is incomplete in .env.")
        return 1

    print("Connecting to Synapt MCP provider...")
    await client.connect_and_discover()
    print("Synapt provider connected. Ingesting curated knowledge documents...")

    for filename, text in KNOWLEDGE_DOCUMENTS.items():
        print(f"Ingesting {filename} ({len(text):,} chars)...")
        try:
            res = await client.ingest_content(text.strip(), filename)
            print(f"  -> Accepted by Synapt: {res.get('structuredContent', res)}")
        except Exception as exc:
            print(f"  -> Failed to ingest {filename}: {exc}")

    # Also ingest SQLite schema description
    schema_file = Path("docs/sqlite_schema_for_synapt.md")
    if schema_file.exists():
        print(f"Ingesting SQLite schema reference from {schema_file}...")
        schema_text = schema_file.read_text(encoding="utf-8")
        try:
            res = await client.ingest_content(schema_text, "cicids2017_sqlite_schema.md")
            print(f"  -> Schema accepted by Synapt: {res.get('structuredContent', res)}")
        except Exception as exc:
            print(f"  -> Failed to ingest schema: {exc}")

    print("\nKnowledge ingestion completed!")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
