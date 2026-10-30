"""Parameterized access to CIC-IDS2017 SQLite records and analyst feedback storage."""

from pathlib import Path
import sqlite3
from typing import Any


FLOW_FIELDS = (
    "record_id, attack_label, attack_family, protocol, flow_duration, flow_bytes_s, "
    "flow_packets_s, total_fwd_packets, total_backward_packets, packet_length_mean, "
    "syn_flag_count, rst_flag_count, source_file, source_row_number"
)


class SQLiteIncidentStore:
    def __init__(self, path: Path):
        self.path = path

    def _connect_ro(self) -> sqlite3.Connection:
        if not self.path.is_file():
            raise FileNotFoundError(f"SQLite dataset not found: {self.path}")
        conn = sqlite3.connect(f"file:{self.path.resolve().as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        return conn

    def _connect_rw(self) -> sqlite3.Connection:
        if not self.path.is_file():
            raise FileNotFoundError(f"SQLite dataset not found: {self.path}")
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_flow_by_id(self, record_id: int) -> dict[str, Any] | None:
        """Fetch all 78+ columns for a specific flow record to feed ML feature extractor."""
        sql = "SELECT * FROM flows WHERE record_id = ?"
        with self._connect_ro() as conn:
            row = conn.execute(sql, (record_id,)).fetchone()
            return dict(row) if row else None

    def search(self, request: Any) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for column in ("attack_label", "attack_family", "protocol", "source_file"):
            value = getattr(request, column, None)
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if getattr(request, "min_flow_duration", None) is not None:
            clauses.append("flow_duration >= ?")
            params.append(request.min_flow_duration)
        if getattr(request, "max_flow_duration", None) is not None:
            clauses.append("flow_duration <= ?")
            params.append(request.max_flow_duration)
        if getattr(request, "query", None):
            clauses.append("(attack_label LIKE ? ESCAPE '\\' OR attack_family LIKE ? ESCAPE '\\' OR source_file LIKE ? ESCAPE '\\')")
            term = request.query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.extend([f"%{term}%"] * 3)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (f"SELECT {FLOW_FIELDS} FROM flows {where} "
               "ORDER BY record_id LIMIT ?")
        params.append(getattr(request, "limit", 20))
        with self._connect_ro() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def save_feedback(self, feedback: dict[str, Any]) -> int:
        """Store analyst review and verdict for continuous improvement feedback loop."""
        with self._connect_rw() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyst_feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER,
                    query TEXT,
                    predicted_family TEXT NOT NULL,
                    analyst_verdict TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur = conn.execute("""
                INSERT INTO analyst_feedback (record_id, query, predicted_family, analyst_verdict, rating, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                feedback.get("record_id"),
                feedback.get("query"),
                feedback["predicted_family"],
                feedback["analyst_verdict"],
                feedback["rating"],
                feedback.get("notes"),
            ))
            conn.commit()
            return cur.lastrowid

    def health(self) -> dict[str, Any]:
        try:
            with self._connect_ro() as conn:
                count = conn.execute("SELECT COUNT(*) FROM flows").fetchone()[0]
            return {"available": True, "rows": count}
        except (sqlite3.Error, FileNotFoundError) as exc:
            return {"available": False, "error": str(exc)}
