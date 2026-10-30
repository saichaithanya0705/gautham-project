"""Streaming audit for the supplied CIC-IDS2017 Parquet archive."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


EXPECTED_METADATA = {
    "Flow ID": ("Flow ID", "Flow_ID", "FlowID"),
    "Source IP": ("Source IP", "Source IP Address", "Src IP"),
    "Source Port": ("Source Port", "Src Port"),
    "Destination IP": ("Destination IP", "Destination IP Address", "Dst IP"),
    "Destination Port": ("Destination Port", "Dst Port"),
    "Timestamp": ("Timestamp", "Flow Timestamp", "Date/Time"),
}


def json_safe(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def audit(data_dir: Path, report_dir: Path, batch_size: int) -> dict[str, Any]:
    files = sorted(data_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No Parquet files found in {data_dir}")

    report_dir.mkdir(parents=True, exist_ok=True)
    label_counts: Counter[str] = Counter()
    file_reports: list[dict[str, Any]] = []
    column_nulls: Counter[str] = Counter()
    column_infinities: Counter[str] = Counter()
    numeric_min: dict[str, float] = {}
    numeric_max: dict[str, float] = {}
    numeric_nonfinite: Counter[str] = Counter()
    protocols: Counter[str] = Counter()
    duplicate_rows = 0
    total_rows = 0
    common_schema: list[str] | None = None
    schema_types: dict[str, str] = {}
    observed_columns: set[str] = set()

    fingerprints_path = report_dir / ".dataset_audit_fingerprints.sqlite3"
    fingerprints_path.unlink(missing_ok=True)
    with sqlite3.connect(fingerprints_path) as fingerprint_db:
        fingerprint_db.execute(
            "CREATE TABLE fingerprints (value BLOB PRIMARY KEY) WITHOUT ROWID"
        )

        for path in files:
            parquet = pq.ParquetFile(path)
            names = list(parquet.schema_arrow.names)
            observed_columns.update(names)
            if common_schema is None:
                common_schema = names
                schema_types = {
                    field.name: str(field.type)
                    for field in parquet.schema_arrow
                }
            elif names != common_schema:
                raise ValueError(
                    f"Schema mismatch in {path.name}; normalize schemas before combining."
                )

            current_labels: Counter[str] = Counter()
            current_rows = 0
            file_nulls: Counter[str] = Counter()
            file_infinities: Counter[str] = Counter()
            file_min: dict[str, float] = {}
            file_max: dict[str, float] = {}

            for batch in parquet.iter_batches(batch_size=batch_size):
                frame = batch.to_pandas()
                rows = len(frame)
                current_rows += rows
                total_rows += rows

                missing = frame.isna().sum()
                for column, count in missing.items():
                    count = int(count)
                    if count:
                        column_nulls[column] += count
                        file_nulls[column] += count

                if "Label" in frame:
                    labels = frame["Label"].astype("string").str.strip()
                    counts = labels.fillna("<NULL>").value_counts(dropna=False)
                    for label, count in counts.items():
                        count = int(count)
                        label_counts[str(label)] += count
                        current_labels[str(label)] += count

                if "Protocol" in frame:
                    counts = frame["Protocol"].astype("string").fillna("<NULL>").value_counts()
                    protocols.update({str(k): int(v) for k, v in counts.items()})

                for column in frame.select_dtypes(include=[np.number]).columns:
                    values = frame[column].to_numpy(copy=False)
                    finite_mask = np.isfinite(values)
                    bad_count = int((~finite_mask).sum())
                    if bad_count:
                        numeric_nonfinite[column] += bad_count
                        if np.isinf(values).any():
                            inf_count = int(np.isinf(values).sum())
                            column_infinities[column] += inf_count
                            file_infinities[column] += inf_count
                    finite = values[finite_mask]
                    if finite.size:
                        low = float(finite.min())
                        high = float(finite.max())
                        numeric_min[column] = min(numeric_min.get(column, low), low)
                        numeric_max[column] = max(numeric_max.get(column, high), high)
                        file_min[column] = min(file_min.get(column, low), low)
                        file_max[column] = max(file_max.get(column, high), high)

                hashes = pd.util.hash_pandas_object(
                    frame, index=False, categorize=True
                ).to_numpy(dtype=np.uint64, copy=False)
                before = fingerprint_db.total_changes
                fingerprint_db.executemany(
                    "INSERT OR IGNORE INTO fingerprints(value) VALUES (?)",
                    ((int(value).to_bytes(8, "little"),) for value in hashes),
                )
                added = fingerprint_db.total_changes - before
                duplicate_rows += rows - added

            file_reports.append(
                {
                    "file": path.name,
                    "size_bytes": path.stat().st_size,
                    "rows": current_rows,
                    "row_groups": parquet.metadata.num_row_groups,
                    "labels": dict(sorted(current_labels.items())),
                    "nulls_by_column": dict(sorted(file_nulls.items())),
                    "infinities_by_column": dict(sorted(file_infinities.items())),
                    "numeric_min": dict(sorted(file_min.items())),
                    "numeric_max": dict(sorted(file_max.items())),
                }
            )
    fingerprint_db.close()
    fingerprints_path.unlink(missing_ok=True)
    columns = common_schema or []
    present_metadata = {
        logical_name: next((name for name in aliases if name in observed_columns), None)
        for logical_name, aliases in EXPECTED_METADATA.items()
    }
    audit_result: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "CIC-IDS2017 supplied Parquet archive",
        "data_directory": str(data_dir.resolve()),
        "files": file_reports,
        "total_files": len(files),
        "total_rows": total_rows,
        "total_size_bytes": sum(item["size_bytes"] for item in file_reports),
        "schema": [{"name": name, "type": schema_types[name]} for name in columns],
        "columns": columns,
        "label_counts": dict(sorted(label_counts.items())),
        "protocol_counts": dict(sorted(protocols.items())),
        "nulls_by_column": dict(sorted(column_nulls.items())),
        "infinities_by_column": dict(sorted(column_infinities.items())),
        "nonfinite_numeric_values_by_column": dict(sorted(numeric_nonfinite.items())),
        "numeric_min": dict(sorted(numeric_min.items())),
        "numeric_max": dict(sorted(numeric_max.items())),
        "duplicate_row_count_by_64_bit_fingerprint": duplicate_rows,
        "metadata_fields": present_metadata,
        "metadata_note": "Missing fields are not inferred from filenames or synthesized.",
        "duplicate_method_note": (
            "Duplicate candidates are counted with pandas 64-bit row fingerprints; "
            "hash collisions are theoretically possible. Near-duplicates are not measured."
        ),
    }

    json_path = report_dir / "dataset_audit.json"
    json_path.write_text(
        json.dumps(audit_result, indent=2, ensure_ascii=False, default=json_safe),
        encoding="utf-8",
    )
    markdown_path = report_dir / "dataset_audit.md"
    label_rows = "\n".join(
        f"| {label} | {count:,} | {count / total_rows:.2%} |"
        for label, count in sorted(label_counts.items())
    )
    metadata_rows = "\n".join(
        f"| {field} | {value or 'Unavailable'} |"
        for field, value in present_metadata.items()
    )
    file_rows = "\n".join(
        f"| `{item['file']}` | {item['rows']:,} | {item['size_bytes'] / (1024 * 1024):.1f} MiB |"
        for item in file_reports
    )
    nonfinite_rows = "\n".join(
        f"| {column} | {count:,} |"
        for column, count in sorted(numeric_nonfinite.items())
    ) or "| None | 0 |"
    null_rows = "\n".join(
        f"| {column} | {count:,} |"
        for column, count in sorted(column_nulls.items())
    ) or "| None | 0 |"
    markdown = f"""# CIC-IDS2017 Dataset Audit

Generated: {audit_result['generated_at_utc']}

## Summary

- Files: {len(files)}
- Rows: {total_rows:,}
- Compressed size: {audit_result['total_size_bytes'] / (1024 * 1024):.1f} MiB
- Columns: {len(columns)}
- Duplicate rows by 64-bit fingerprint: {duplicate_rows:,}
- Near-duplicates were not measured.

## Files

| File | Rows | Size |
|---|---:|---:|
{file_rows}

## Label distribution

| Label | Rows | Share |
|---|---:|---:|
{label_rows}

## Metadata availability

| Field | Column |
|---|---|
{metadata_rows}

## Nulls and non-finite numeric values

Null values:

| Column | Count |
|---|---:|
{null_rows}

NaN and infinity values in numeric columns:

| Column | Count |
|---|---:|
{nonfinite_rows}

## Schema

| Column | Type |
|---|---|
""" + "\n".join(f"| `{item['name']}` | `{item['type']}` |" for item in audit_result["schema"])
    markdown_path.write_text(markdown, encoding="utf-8")
    return audit_result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("archive (1)"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/dataset_audit"))
    parser.add_argument("--batch-size", type=int, default=65_536)
    args = parser.parse_args()
    result = audit(args.data_dir, args.report_dir, args.batch_size)
    print(json.dumps({
        "total_rows": result["total_rows"],
        "total_files": result["total_files"],
        "label_counts": result["label_counts"],
        "duplicate_row_count_by_64_bit_fingerprint": result["duplicate_row_count_by_64_bit_fingerprint"],
        "nulls_by_column": result["nulls_by_column"],
        "nonfinite_numeric_values_by_column": result["nonfinite_numeric_values_by_column"],
        "metadata_fields": result["metadata_fields"],
        "reports": [str(args.report_dir / "dataset_audit.json"), str(args.report_dir / "dataset_audit.md")],
    }, indent=2, default=json_safe))


if __name__ == "__main__":
    main()
