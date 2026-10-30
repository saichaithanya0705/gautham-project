"""Seed the versioned Historical Incident RAG corpus into SQLite FTS5 and Synapt.

Extracts representative real flows across all 9 attack families and benign traffic,
generates structured incident summaries with record provenance, and populates
both the SQLite FTS5 index and the knowledge ingestion bundle.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cyber_assistant.config import get_settings
from cyber_assistant.synapt.client import SynaptClient
from cyber_assistant.rag.historical_rag import HistoricalIncidentRAG


INCIDENT_TEMPLATES = {
    "port_scan": "Reconnaissance incident involving rapid TCP SYN port scanning and service discovery across target host ports.",
    "dos": "Application-layer denial of service incident causing thread exhaustion, high connection persistence, and anomalous packet rate.",
    "ddos": "Volumetric distributed denial of service attack flooding network boundaries with extreme packet and byte volumes.",
    "brute_force": "Credential stuffing and password guessing attack exhibiting repeated authentication attempts and elevated connection reset (RST) flags.",
    "web_attack": "Web application exploit probe containing malicious SQL injection keywords, cross-site scripting tags, or directory traversal indicators.",
    "botnet": "Command & Control (C2) beaconing activity exhibiting consistent packet inter-arrival times and periodic outbound synchronization.",
    "infiltration": "Post-compromise network infiltration and lateral movement probe targeting internal services and privilege boundaries.",
    "benign": "Normal baseline corporate business traffic adhering to standard bidirectional HTTP/TLS conversational ratios and flow durations.",
}


def seed_sqlite_corpus(db_path: Path, samples_per_family: int = 35) -> int:
    rag = HistoricalIncidentRAG(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT attack_family FROM flows")
    families = [r[0] for r in cur.fetchall()]

    total_seeded = 0
    corpus_lines = []

    for fam in families:
        cur.execute(
            """
            SELECT record_id, attack_family, attack_label, protocol, flow_duration, flow_packets_s, flow_bytes_s,
                   syn_flag_count, rst_flag_count, source_file, source_row_number
            FROM flows
            WHERE attack_family = ?
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (fam, samples_per_family),
        )
        rows = cur.fetchall()
        for idx, r in enumerate(rows, 1):
            inc_id = f"INC-2017-{fam.upper()[:4]}-{r[0]}"
            template = INCIDENT_TEMPLATES.get(fam, "Network security incident observed in traffic flow.")
            summary_text = (
                f"Incident {inc_id} ({fam} - {r[2]}): {template} "
                f"Observed on protocol {r[3]}, duration {r[4]:,} µs, "
                f"packet rate {round(r[5] or 0):,} pkts/s, SYN flags: {r[7]}, RST flags: {r[8]}. "
                f"Source provenance: {r[9]} row {r[10]}."
            )

            # Insert into historical_incident_summaries
            cur.execute(
                """
                INSERT OR REPLACE INTO historical_incident_summaries
                (incident_id, record_id, attack_family, attack_label, protocol, flow_duration, summary_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (inc_id, r[0], r[1], r[2], r[3], r[4], summary_text),
            )

            # Insert into FTS5 virtual table
            cur.execute(
                """
                INSERT OR REPLACE INTO historical_incidents_fts
                (incident_id, record_id, attack_family, attack_label, summary_text)
                VALUES (?, ?, ?, ?, ?)
                """,
                (inc_id, r[0], fam, r[2], summary_text),
            )
            total_seeded += 1
            corpus_lines.append(f"## {inc_id}\n{summary_text}\n")

    conn.commit()
    conn.close()

    # Save compiled knowledge corpus for Synapt ingestion
    corpus_path = Path("docs/historical_incident_corpus_for_synapt.txt")
    corpus_path.write_text("\n".join(corpus_lines), encoding="utf-8")
    print(f"Successfully seeded {total_seeded} incident summaries into SQLite FTS5!")
    print(f"Wrote compiled incident knowledge corpus to {corpus_path}")
    return total_seeded


async def ingest_corpus_to_synapt():
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
        print("Synapt is not configured; skipping remote ingestion.")
        return

    corpus_file = Path("docs/historical_incident_corpus_for_synapt.txt")
    if corpus_file.exists():
        print(f"Connecting to Synapt and ingesting {corpus_file}...")
        try:
            content = corpus_file.read_text(encoding="utf-8")
            res = await client.ingest_content(content[:45000], "cicids2017_historical_incidents.txt")
            print(f"Ingestion accepted by Synapt: {res}")
        except Exception as exc:
            print(f"Synapt ingestion error: {exc}")


if __name__ == "__main__":
    db = Path("data/cicids2017.sqlite3")
    seeded = seed_sqlite_corpus(db, samples_per_family=35)
    asyncio.run(ingest_corpus_to_synapt())
