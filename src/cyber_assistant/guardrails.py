"""Central Security Boundary & Guardrails Engine.

Enforces:
1. Prompt injection & unauthorized instruction detection.
2. Destructive command & automated containment prevention.
3. Telemetry contract validation (finite values, valid protocols, non-negative rates).
4. Evidence/instruction channel separation.
"""

from __future__ import annotations

import math
import re
from typing import Any


PROHIBITED_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*prompt\s*(leak|reveal|output|display)",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"jailbreak",
    r"drop\s+table",
    r"delete\s+from",
    r"truncate\s+table",
    r"rm\s+-rf",
    r"exec\s+xp_cmdshell",
    r"auto(mated)?\s+containment\s+(execute|enforce|run)",
    r"block\s+ip\s+(automatically|immediately\s+without\s+approval)",
    r"isolate\s+host\s+automatically",
]


class GuardrailViolation(ValueError):
    """Raised when an untrusted input breaches security policy."""


def check_input_guardrail(text: str | None) -> tuple[bool, str, str | None]:
    """Inspect analyst question or query string for prohibited instructions.
    
    Returns:
        (is_allowed, status_str, violation_reason)
    """
    if not text:
        return True, "passed", None

    clean_text = text.strip()
    for pattern in PROHIBITED_INJECTION_PATTERNS:
        if re.search(pattern, clean_text, re.IGNORECASE):
            return False, "rejected", f"Input triggered prohibited instruction pattern: {pattern}"

    return True, "passed", None


CYBER_RELEVANT_PATTERNS = [
    r"\b(cyber|security|soc|incident|breach|threat|compromise|vulnerab\w*|exploit\w*)\b",
    r"\b(flow|packet|traffic|network|telemetry|pcap|bandwidth|payload|session)\b",
    r"\b(ip|port|protocol|tcp|udp|icmp|http|https|dns|ssh|ftp|smtp|dhcp|arp)\b",
    r"\b(syn|ack|rst|fin|psh|urg|flag|handshake|header|inter-arrival|iat|duration)\b",
    r"\b(attack|malware|botnet|ransomware|trojan|virus|worm|spyware|rootkit)\b",
    r"\b(dos|ddos|hulk|slowloris|goldeneye|loic|hoic|flood|smurf|amplification)\b",
    r"\b(brute\s*force|password|credential|patator|hydra|dictionary\s*attack)\b",
    r"\b(scan\w*|recon\w*|nmap|probe|sweep|discovery|enumeration|fingerprint\w*)\b",
    r"\b(injection|sqli|xss|csrf|ssrf|rce|cross-site|web\s*attack|heartbleed)\b",
    r"\b(infiltration|lateral\s*movement|privilege\s*escalat\w*|c2|command\s*and\s*control)\b",
    r"\b(anomaly|deviat\w*|outlier|benign|malicious|suspicious|false\s*positive)\b",
    r"\b(mitre|att&ck|tactic|technique|sub-technique|t\d{4}(\.\d{3})?)\b",
    r"\b(nist|sp\s*800-61|playbook|containment|eradication|recovery|remediation)\b",
    r"\b(firewall|ids|ips|siem|edr|xdr|acls?|suricata|snort|zeek|wireshark)\b",
    r"\b(cic-ids|cicids|cicids2017|dataset|model|classifier|features?)\b",
    r"\b(record|flow)\s*#?\d+\b",
    r"\b(p[1-4]|priority|severity|critical|high|medium|low|triage)\b",
    r"\b(forensic\w*|log\w*|syslog|audit|event|alert\w*|rule\w*|indicator|ioc)\b",
    r"\b(hash|cve|zero-day|zeroday|phish\w*|spoof\w*|exfiltrat\w*|backdoor)\b",
]

CONVERSATIONAL_GREETING_PATTERNS = [
    r"^(hi|hello|hey|greetings|good\s*(morning|afternoon|evening))\b",
    r"\b(who\s+are\s+you|what\s+can\s+you\s+do|how\s+can\s+you\s+help|what\s+is\s+your\s+role)\b",
    r"\b(help|commands?|options?|capabilities)\b",
    r"\bwhat\s+(is|does)\s+this\s+(project|assistant|copilot|tool)\b",
    r"\b(thanks?|thank\s+you)\b",
]


FLOW_INVESTIGATION_CONTEXT_PATTERNS = [
    r"\b(this|it|that|these|the)\s+(flow|record|alert|incident|telemetry|traffic|finding|connection|session)\b",
    r"\b(what\s+does\s+this\s+mean|explain\s+this|why\s+was\s+this\s+flagged|is\s+this\s+(safe|malicious|bad|dangerous))\b",
    r"\b(what\s+should\s+i\s+do|next\s+steps?|how\s+to\s+contain|how\s+to\s+investigate|recommendations?)\b",
    r"\b(can\s+you\s+summarize|summarize\s+this|break\s+this\s+down)\b",
]


def is_cybersecurity_relevant(text: str | None, has_flow_context: bool = False) -> tuple[bool, str | None]:
    """Verify if a user question is relevant to the cybersecurity project.
    
    Args:
        text: The user's query or message.
        has_flow_context: Whether an active telemetry flow is currently loaded in the session.
        
    Returns:
        (is_relevant, explanation_if_irrelevant)
    """
    if not text or not text.strip():
        return True, None

    clean = text.strip()

    # Check for direct record/flow references like flow 2039912 or #500000
    if re.search(r"\b(?:flow|record|case|alert|incident|id)\s*#?\s*\d+\b", clean, re.IGNORECASE) or re.search(r"#\d{4,8}\b", clean):
        return True, None

    # Check conversational greetings / role inquiries
    for pat in CONVERSATIONAL_GREETING_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            return True, None

    # Check cybersecurity domain keywords
    for pat in CYBER_RELEVANT_PATTERNS:
        if re.search(pat, clean, re.IGNORECASE):
            return True, None

    # If an active flow is loaded in the session context, allow conversational triage follow-up phrases
    if has_flow_context:
        for pat in FLOW_INVESTIGATION_CONTEXT_PATTERNS:
            if re.search(pat, clean, re.IGNORECASE):
                return True, None

    return False, (
        "⚠️ **Relevance Guardrail**: This question is not relevant to the project. "
        "I am a specialized Cybersecurity Incident Response Assistant for analyzing network telemetry, "
        "investigating CIC-IDS2017 flows, classifying cyber threats, and guiding NIST/MITRE incident response. "
        "Please ask a question related to cybersecurity or network traffic analysis."
    )


def sanitize_analyst_context(query: str | None) -> str:
    """Isolate untrusted analyst context into a structured XML boundary to prevent prompt leakage."""
    if not query:
        return ""
    # Strip potential delimiter escapes
    safe_query = query.replace("</analyst_context>", "").replace("<analyst_context>", "")
    return f"<analyst_context>\n{safe_query.strip()}\n</analyst_context>"


def validate_telemetry_flow(flow: dict[str, Any]) -> tuple[bool, dict[str, float | int], str | None]:
    """Validate raw/synthetic flow telemetry against typed bounds and finite numbers.
    
    Returns:
        (is_valid, cleaned_features, error_message)
    """
    if not isinstance(flow, dict) or not flow:
        return False, {}, "Flow telemetry must be a non-empty dictionary of measurements."

    cleaned: dict[str, float | int] = {}

    # Check protocol if present
    if "protocol" in flow and flow["protocol"] is not None:
        try:
            proto = int(flow["protocol"])
            if proto < 0 or proto > 255:
                return False, {}, f"Protocol {proto} is out of valid range [0, 255]."
            cleaned["protocol"] = proto
        except (ValueError, TypeError):
            return False, {}, f"Invalid non-integer protocol: {flow['protocol']}."

    # Validate numeric feature values
    non_numeric_fields = {"source_file", "source_row_number", "attack_label", "attack_family", "record_id"}
    for k, v in flow.items():
        if k in non_numeric_fields or k == "protocol":
            continue
        if v is None:
            continue
        try:
            num = float(v)
            if math.isnan(num) or math.isinf(num):
                return False, {}, f"Feature '{k}' contains non-finite value ({v})."
            # Non-negative checks for duration and counts
            if any(term in k.lower() for term in ["duration", "packet", "byte", "flag_count", "header_length"]) and num < 0:
                return False, {}, f"Feature '{k}' cannot be negative ({num})."
            cleaned[k] = num
        except (ValueError, TypeError):
            return False, {}, f"Feature '{k}' must be numeric, got: {v!r}."

    if len(cleaned) < 2 and not ("record_id" in flow):
        return False, {}, "Insufficient telemetry measurements provided for feature evaluation."

    return True, cleaned, None
