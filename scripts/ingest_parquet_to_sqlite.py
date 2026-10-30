"""Load the supplied CIC-IDS2017 flow rows into a local SQLite database."""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


SPECIAL_LABELS = {
    "benign": ("benign", "benign"),
    "bot": ("botnet", "botnet"),
    "ddos": ("ddos", "ddos"),
    "dos goldeneye": ("dos_goldeneye", "dos"),
    "dos hulk": ("dos_hulk", "dos"),
    "dos slowhttptest": ("dos_slowhttptest", "dos"),
    "dos slowloris": ("dos_slowloris", "dos"),
    "ftp-patator": ("brute_force_ftp", "brute_force"),
    "ssh-patator": ("brute_force_ssh", "brute_force"),
    "heartbleed": ("heartbleed", "rare_attack"),
    "infiltration": ("infiltration", "infiltration"),
    "portscan": ("port_scan", "port_scan"),
    "web attack � brute force": ("web_attack_brute_force", "web_attack"),
    "web attack � sql injection": ("web_attack_sql_injection", "web_attack"),
    "web attack � xss": ("web_attack_xss", "web_attack"),
}


def canonicalize_label(value: object) -> tuple[str, str]:
    raw = "" if value is None else str(value).strip()
    mapped = SPECIAL_LABELS.get(raw.casefold())
    if mapped:
        return mapped
    slug = re.sub(r"[^a-z0-9]+", "_", raw.casefold()).strip("_") or "unknown"
    return slug, "unknown"


def normalize_column(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return normalized or "unnamed_column"


def import_dataset(data_dir: Path, db_path: Path, batch_size: int) -> None:
    files = sorted(data_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No Parquet files found in {data_dir}")
    if db_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite {db_path}. Move or remove it deliberately before rebuilding."
        )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    first_file = pq.ParquetFile(files[0])
    source_names = list(first_file.schema_arrow.names)
    if "Label" not in source_names or "Protocol" not in source_names:
        raise ValueError("Expected CIC-IDS2017 Label and Protocol columns are missing")
    normalized = {name: normalize_column(name) for name in source_names if name != "Label"}
    if len(set(normalized.values())) != len(normalized):
        raise ValueError("Column normalization produced a name collision")

    feature_names = [normalized[name] for name in source_names if name != "Label"]
    reserved = {"record_id", "source_file", "source_row_number", "row_fingerprint", "label_raw", "attack_label", "attack_family"}
    collisions = reserved.intersection(feature_names)
    if collisions:
        raise ValueError(f"Normalized dataset columns collide with reserved names: {collisions}")

    column_defs = []
    for source_name in source_names:
        if source_name == "Label":
            continue
        arrow_type = first_file.schema_arrow.field(source_name).type
        sql_type = "INTEGER" if pa.types.is_integer(arrow_type) else "REAL"
        column_defs.append(f'"{normalized[source_name]}" {sql_type}')
    # Protocol is categorical even though this distribution encodes it as an integer.
    column_defs[feature_names.index("protocol")] = '"protocol" INTEGER NOT NULL'
    column_defs.extend([
        '"label_raw" TEXT NOT NULL',
        '"attack_label" TEXT NOT NULL',
        '"attack_family" TEXT NOT NULL',
        '"source_file" TEXT NOT NULL',
        '"source_row_number" INTEGER NOT NULL',
        '"row_fingerprint" TEXT NOT NULL',
    ])

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute(
            "CREATE TABLE flows (record_id INTEGER PRIMARY KEY, "
            + ", ".join(column_defs)
            + ", UNIQUE(source_file, source_row_number))"
        )
        connection.execute(
            "CREATE TABLE dataset_files (source_file TEXT PRIMARY KEY, rows INTEGER NOT NULL, size_bytes INTEGER NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE dataset_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )

        inserted_total = 0
        for path in files:
            parquet = pq.ParquetFile(path)
            if list(parquet.schema_arrow.names) != source_names:
                raise ValueError(f"Schema mismatch in {path.name}")
            row_offset = 0
            inserted_file = 0
            for batch in parquet.iter_batches(batch_size=batch_size):
                frame = batch.to_pandas()
                row_count = len(frame)
                labels_raw = frame.pop("Label").astype("string").fillna("<NULL>")
                mapped = labels_raw.map(canonicalize_label)
                frame["attack_label"] = mapped.map(lambda item: item[0])
                frame["attack_family"] = mapped.map(lambda item: item[1])
                frame["label_raw"] = labels_raw.astype(str)
                hashes = pd.util.hash_pandas_object(
                    batch.to_pandas(), index=False, categorize=True
                ).to_numpy(dtype=np.uint64, copy=False)
                frame["row_fingerprint"] = [f"{int(value):016x}" for value in hashes]
                frame["source_file"] = path.name
                frame["source_row_number"] = np.arange(
                    row_offset + 1, row_offset + row_count + 1, dtype=np.int64
                )
                frame.rename(columns=normalized, inplace=True)
                frame = frame[feature_names + [
                    "label_raw", "attack_label", "attack_family", "source_file",
                    "source_row_number", "row_fingerprint",
                ]]
                frame.to_sql(
                    "flows", connection, if_exists="append", index=False,
                    chunksize=5_000, method=None,
                )
                row_offset += row_count
                inserted_file += row_count
                inserted_total += row_count
                print(f"{path.name}: loaded {row_offset:,}/{parquet.metadata.num_rows:,}")

            connection.execute(
                "INSERT INTO dataset_files(source_file, rows, size_bytes) VALUES (?, ?, ?)",
                (path.name, inserted_file, path.stat().st_size),
            )
            connection.commit()

        indexes = [
            "CREATE INDEX idx_flows_attack_label ON flows(attack_label)",
            "CREATE INDEX idx_flows_attack_family ON flows(attack_family)",
            "CREATE INDEX idx_flows_protocol ON flows(protocol)",
            "CREATE INDEX idx_flows_label_protocol ON flows(attack_label, protocol)",
            "CREATE INDEX idx_flows_fingerprint ON flows(row_fingerprint)",
        ]
        for statement in indexes:
            connection.execute(statement)
        metadata = {
            "dataset": "CIC-IDS2017",
            "source_directory": str(data_dir.resolve()),
            "row_count": str(inserted_total),
            "source_columns": ",".join(source_names),
            "provenance_policy": "source_file + one-based source_row_number",
            "label_policy": "label_raw retained; attack_label and attack_family are canonical mappings",
            "synthetic_data_included": "false",
            "metadata_limitation": "Flow ID, source/destination IP, ports, and timestamp are absent",
        }
        connection.executemany(
            "INSERT INTO dataset_metadata(key, value) VALUES (?, ?)", metadata.items()
        )
        connection.execute("ANALYZE")
        connection.commit()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()

    print(f"Loaded {inserted_total:,} rows into {db_path} ({db_path.stat().st_size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("archive (1)"))
    parser.add_argument("--db", type=Path, default=Path("data/cicids2017.sqlite3"))
    parser.add_argument("--batch-size", type=int, default=20_000)
    args = parser.parse_args()
    import_dataset(args.data_dir, args.db, args.batch_size)


if __name__ == "__main__":
    main()
