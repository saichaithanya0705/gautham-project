"""Create a compact, stratified demo SQLite DB from the full local DB."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def create_demo(source: Path, target: Path, benign_rows: int, rows_per_other_label: int) -> int:
    if not source.is_file():
        raise FileNotFoundError(source)
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    source_uri = f"file:{source.resolve().as_posix()}?mode=ro"
    src = sqlite3.connect(source_uri, uri=True)
    dst = sqlite3.connect(target)
    try:
        for table in ("flows", "dataset_metadata", "dataset_files"):
            ddl = src.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not ddl or not ddl[0]:
                raise ValueError(f"Source database is missing table {table}")
            dst.execute(ddl[0])

        metadata = dict(src.execute("SELECT key,value FROM dataset_metadata"))
        source_columns = [row[1] for row in src.execute("PRAGMA table_info(flows)")]
        quoted_columns = ",".join('"' + name.replace('"', '""') + '"' for name in source_columns)
        labels = [row[0] for row in src.execute(
            "SELECT DISTINCT attack_label FROM flows ORDER BY attack_label"
        )]
        selected_total = 0
        for label in labels:
            cap = benign_rows if label == "benign" else rows_per_other_label
            rows = src.execute(
                f"SELECT {quoted_columns} FROM flows WHERE attack_label=? ORDER BY record_id LIMIT ?",
                (label, cap),
            ).fetchall()
            if rows:
                placeholders = ",".join("?" for _ in source_columns)
                dst.executemany(
                    f"INSERT INTO flows ({quoted_columns}) VALUES ({placeholders})", rows
                )
                selected_total += len(rows)

        file_counts = dst.execute(
            "SELECT source_file,COUNT(*) FROM flows GROUP BY source_file ORDER BY source_file"
        ).fetchall()
        dst.executemany(
            "INSERT INTO dataset_files(source_file,rows,size_bytes) VALUES(?,?,0)", file_counts
        )
        metadata.update({
            "dataset": "CIC-IDS2017 stratified demo sample",
            "source_directory": "External Parquet archive; not included in transfer bundle",
            "row_count": str(selected_total),
            "demo_sample": "true",
            "sample_policy": (
                f"Deterministic first {benign_rows} benign rows and up to "
                f"{rows_per_other_label} rows per other attack label, ordered by record_id"
            ),
            "source_file_size_bytes": "not recorded for compact demo sample",
        })
        dst.executemany(
            "INSERT INTO dataset_metadata(key,value) VALUES(?,?)", metadata.items()
        )
        indexes = src.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='flows' AND sql IS NOT NULL"
        ).fetchall()
        for (statement,) in indexes:
            dst.execute(statement)
        dst.execute("ANALYZE")
        dst.commit()
    finally:
        src.close()
        dst.close()
    return selected_total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/cicids2017.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("data/cicids2017_demo.sqlite3"))
    parser.add_argument("--benign-rows", type=int, default=1000)
    parser.add_argument("--rows-per-other-label", type=int, default=250)
    args = parser.parse_args()
    total = create_demo(args.source, args.output, args.benign_rows, args.rows_per_other_label)
    print(f"Created {args.output}: {total:,} stratified rows ({args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
