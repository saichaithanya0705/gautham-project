"""Export a safe schema/data contract document for later Synapt ingestion."""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path


def normalize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower() or "unnamed_column"


def export(db_path: Path, output: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        metadata = dict(connection.execute("SELECT key,value FROM dataset_metadata"))
        original_columns = metadata["source_columns"].split(",")
        rows = connection.execute("SELECT COUNT(*) FROM flows").fetchone()[0]
        label_counts = connection.execute(
            "SELECT attack_label, attack_family, COUNT(*) "
            "FROM flows GROUP BY attack_label, attack_family ORDER BY attack_label"
        ).fetchall()
        fields = connection.execute("PRAGMA table_info(flows)").fetchall()
        indexes = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='flows' ORDER BY name"
        ).fetchall()
        data_files = connection.execute(
            "SELECT source_file, rows, size_bytes FROM dataset_files ORDER BY source_file"
        ).fetchall()
    finally:
        connection.close()

    field_notes = {
        "record_id": "Local SQLite surrogate key; not present in the source dataset.",
        "protocol": "Protocol number from the source dataset; treat categorically, not as an ordered magnitude.",
        "label_raw": "Original source Label string, preserved as read.",
        "attack_label": "Canonicalized dataset ground-truth label; not an analyst-confirmed live incident.",
        "attack_family": "Documented coarse grouping derived from the source label.",
        "source_file": "Parquet source filename for provenance.",
        "source_row_number": "One-based row offset within source_file; stable only for this archive version.",
        "row_fingerprint": "64-bit fingerprint of original row values for duplicate-candidate grouping; not a unique event ID.",
    }
    field_rows = []
    source_mapping = {normalize(name): name for name in original_columns if name != "Label"}
    source_mapping.update({
        "label_raw": "Label",
        "attack_label": "derived from Label",
        "attack_family": "derived from Label",
        "source_file": "derived provenance",
        "source_row_number": "derived provenance",
        "row_fingerprint": "derived fingerprint",
        "record_id": "SQLite-generated",
    })
    for _, name, sql_type, not_null, default, primary_key in fields:
        field_rows.append(
            f"| `{name}` | `{sql_type}` | {source_mapping.get(name, 'derived')} | "
            f"{'Yes' if not_null or primary_key else 'No'} | "
            f"{field_notes.get(name, 'Source flow measurement; consult the dataset feature documentation for units and calculation semantics.')} |"
        )

    label_rows = "\n".join(
        f"| `{label}` | `{family}` | {count:,} |"
        for label, family, count in label_counts
    )
    file_rows = "\n".join(
        f"| `{name}` | {count:,} | {size / (1024 * 1024):.1f} MiB |"
        for name, count, size in data_files
    )
    index_rows = "\n".join(
        f"| `{name}` | `{sql or 'UNIQUE constraint index'}` |"
        for name, sql in indexes
    )
    markdown = f"""# CIC-IDS2017 SQLite Schema and Query Contract

## Purpose and boundaries

This document describes the local SQLite flow database for the Synapt
Context Substrate. Synapt may ingest this schema/data dictionary and
curated security knowledge through its supported MCP ingestion tool.
Ingesting this document does not give Synapt direct access to SQLite;
the application runs SQL queries and preserves SQLite provenance.

The full benchmark rows remain in SQLite. They are not copied into
Synapt as prose and no external vector database is used. Synthetic rows
are not included.

## Dataset summary

- Dataset: `{metadata['dataset']}`
- Rows: {rows:,}
- Files: {len(data_files)}
- Source columns: {len(original_columns)} (includes the source `Label`)
- SQLite table: `flows`
- Source label is preserved in `label_raw`; `attack_label` and
  `attack_family` are canonical derived fields.

## Source files

| File | Rows | Compressed size |
|---|---:|---:|
{file_rows}

## Flow table fields

| Field | SQLite type | Source mapping | Required | Meaning / handling |
|---|---|---|---|---|
{chr(10).join(field_rows)}

## Canonical label counts

| Canonical label | Family | Rows |
|---|---|---:|
{label_rows}

## Indexes

| Index | Definition |
|---|---|
{index_rows}

## Available and unavailable filters

Available: canonical attack label/family, protocol, source file, and
flow measurement fields. Numeric flow filters require documented units
and validated bounds. Flow ID, source/destination IP, source/destination
port, and timestamp are absent from this archive and must be reported
as unavailable. Do not synthesize values for these fields.

## Provenance and interpretation

Every row points to `source_file` and a one-based `source_row_number`.
`attack_label` is the CIC-IDS2017 dataset label and must remain distinct
from a model prediction or analyst conclusion. Repeated row fingerprints
are duplicate candidates, not proof that two rows describe one event.
The source archive is divided across day/attack files; never use
`source_file` as a model feature.

## Example parameterized query

```sql
SELECT record_id, attack_label, protocol, flow_duration,
       total_fwd_packets, total_backward_packets,
       source_file, source_row_number
FROM flows
WHERE attack_label = ? AND protocol = ?
ORDER BY record_id
LIMIT ?;
```

Use parameterized SQL only. Query results are structured evidence from
SQLite; Synapt evidence must retain its own document/chunk provenance.
The application may combine both in a report. Do not claim Synapt's LLM
used SQL rows as context unless the live MCP query contract and behavior
have been verified.
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output} ({output.stat().st_size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/cicids2017.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("docs/sqlite_schema_for_synapt.md"))
    args = parser.parse_args()
    export(args.db, args.output)


if __name__ == "__main__":
    main()
