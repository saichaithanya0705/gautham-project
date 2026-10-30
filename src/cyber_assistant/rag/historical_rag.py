"""Historical Incident RAG and Fused Keyword + Semantic Hybrid Retrieval Engine.

Requirements:
- B1: Historical incident similarity search grounded in real SQLite records.
- B2: Fused keyword (SQLite FTS5 / BM25) and semantic (Synapt Trident) hybrid ranking with Reciprocal Rank Fusion (RRF).
- Self-exclusion: Excludes queried target flow from its own prior evidence.
- Paraphrase support: Resolves natural language security queries without literal label matching.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any
from pathlib import Path

from cyber_assistant.synapt.client import SynaptClient


class HistoricalIncidentRAG:
    def __init__(self, db_path: str | Path, synapt: SynaptClient | None = None):
        self.db_path = str(db_path)
        self.synapt = synapt
        self._ensure_fts_table()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_fts_table(self) -> None:
        """Create the FTS5 virtual table and incident mapping table if not present."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historical_incident_summaries (
                incident_id TEXT PRIMARY KEY,
                record_id INTEGER NOT NULL,
                attack_family TEXT NOT NULL,
                attack_label TEXT NOT NULL,
                protocol INTEGER,
                flow_duration INTEGER,
                summary_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS historical_incidents_fts USING fts5(
                incident_id,
                record_id UNINDEXED,
                attack_family,
                attack_label,
                summary_text
            )
        """)
        conn.commit()
        conn.close()

    def keyword_search(self, query: str, limit: int = 15) -> list[dict[str, Any]]:
        """Execute BM25 ranked keyword search over FTS5 incident summaries."""
        # Extract meaningful alphanumeric terms (length >= 3)
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query)]
        if not words:
            return []

        # Build FTS5 query string with OR fallback for flexible paraphrases
        fts_match_query = " OR ".join(words)

        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                SELECT incident_id, record_id, attack_family, attack_label, summary_text,
                       bm25(historical_incidents_fts) as bm25_score
                FROM historical_incidents_fts
                WHERE historical_incidents_fts MATCH ?
                ORDER BY bm25_score ASC
                LIMIT ?
            """
            cur.execute(sql, (fts_match_query, limit))
            rows = [dict(r) for r in cur.fetchall()]
        except sqlite3.OperationalError:
            rows = []
        finally:
            conn.close()

        results = []
        for rank, r in enumerate(rows, 1):
            r["keyword_rank"] = rank
            # Lower bm25 is higher relevance in sqlite; normalize to a positive score
            raw_bm25 = float(r.get("bm25_score", 0))
            r["keyword_score"] = round(1.0 / (1.0 + abs(raw_bm25)), 4)
            results.append(r)
        return results

    async def semantic_search(self, query: str, limit: int = 15) -> list[dict[str, Any]]:
        """Retrieve semantically relevant incidents via Synapt Trident knowledge substrate."""
        if not self.synapt or not self.synapt.configured:
            return []

        candidates: list[dict[str, Any]] = []
        try:
            raw_results = await self.synapt.retrieve(f"Find prior network security incidents matching: {query}")
            if raw_results and isinstance(raw_results[0], dict):
                structured = raw_results[0].get("structuredContent") or {}
                chunks = structured.get("chunks") or []
                conf = float(structured.get("confidence_score", 0.8))
                for idx, ch in enumerate(chunks[:limit], 1):
                    txt = ch.get("text", "")
                    candidates.append({
                        "semantic_rank": idx,
                        "semantic_text": txt,
                        "confidence": conf,
                    })
        except Exception:
            candidates = []

        return candidates

    async def hybrid_search(
        self,
        query: str,
        target_record_id: int | None = None,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute Reciprocal Rank Fusion (RRF) combining FTS5 keyword and Synapt semantic search."""
        filters = filters or {}
        kw_results = self.keyword_search(query, limit=limit * 3)
        sem_results = await self.semantic_search(query, limit=limit * 2)

        fused_candidates: dict[str, dict[str, Any]] = {}

        # 1. Ingest keyword candidates
        for item in kw_results:
            inc_id = item["incident_id"]
            rec_id = int(item["record_id"])
            if target_record_id and rec_id == target_record_id:
                continue  # Self-exclusion

            # Apply family filter if requested
            if filters.get("attack_family") and item["attack_family"].lower() != filters["attack_family"].lower():
                continue

            k_rank = item["keyword_rank"]
            fused_candidates[inc_id] = {
                "incident_id": inc_id,
                "record_id": rec_id,
                "attack_family": item["attack_family"],
                "attack_label": item["attack_label"],
                "summary": item["summary_text"],
                "keyword_rank": k_rank,
                "semantic_rank": None,
                "rrf_score": 1.0 / (60.0 + k_rank),
                "matched_channels": ["keyword_bm25"],
            }

        # 2. Correlate with semantic results
        for s_item in sem_results:
            s_rank = s_item.get("semantic_rank", 1)
            s_text = s_item.get("semantic_text", "").lower()
            for inc_id, cand in fused_candidates.items():
                if cand["attack_family"].lower() in s_text or inc_id.lower() in s_text:
                    cand["semantic_rank"] = s_rank
                    cand["rrf_score"] += 1.0 / (60.0 + s_rank)
                    if "semantic_synapt" not in cand["matched_channels"]:
                        cand["matched_channels"].append("semantic_synapt")

        # 3. Fallback padding if candidates are fewer than requested limit
        if len(fused_candidates) < limit:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT incident_id, record_id, attack_family, attack_label, summary_text
                FROM historical_incident_summaries
                ORDER BY RANDOM()
                LIMIT ?
            """, (limit - len(fused_candidates),))
            for r in cur.fetchall():
                inc_id = r["incident_id"]
                rec_id = int(r["record_id"])
                if inc_id not in fused_candidates and (not target_record_id or rec_id != target_record_id):
                    fused_candidates[inc_id] = {
                        "incident_id": inc_id,
                        "record_id": rec_id,
                        "attack_family": r["attack_family"],
                        "attack_label": r["attack_label"],
                        "summary": r["summary_text"],
                        "keyword_rank": 99,
                        "semantic_rank": None,
                        "rrf_score": 1.0 / (60.0 + 99),
                        "matched_channels": ["baseline_corpus"],
                    }
            conn.close()

        sorted_results = sorted(fused_candidates.values(), key=lambda x: x["rrf_score"], reverse=True)
        return sorted_results[:limit]
