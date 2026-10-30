# CIC-IDS2017 SQLite Schema and Query Contract

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

- Dataset: `CIC-IDS2017`
- Rows: 2,313,810
- Files: 8
- Source columns: 78 (includes the source `Label`)
- SQLite table: `flows`
- Source label is preserved in `label_raw`; `attack_label` and
  `attack_family` are canonical derived fields.

## Source files

| File | Rows | Compressed size |
|---|---:|---:|
| `Benign-Monday-no-metadata.parquet` | 458,831 | 54.1 MiB |
| `Botnet-Friday-no-metadata.parquet` | 176,038 | 18.9 MiB |
| `Bruteforce-Tuesday-no-metadata.parquet` | 389,714 | 44.0 MiB |
| `DDoS-Friday-no-metadata.parquet` | 221,264 | 24.1 MiB |
| `DoS-Wednesday-no-metadata.parquet` | 584,991 | 65.0 MiB |
| `Infiltration-Thursday-no-metadata.parquet` | 207,630 | 22.1 MiB |
| `Portscan-Friday-no-metadata.parquet` | 119,522 | 13.0 MiB |
| `WebAttacks-Thursday-no-metadata.parquet` | 155,820 | 16.8 MiB |

## Flow table fields

| Field | SQLite type | Source mapping | Required | Meaning / handling |
|---|---|---|---|---|
| `record_id` | `INTEGER` | SQLite-generated | Yes | Local SQLite surrogate key; not present in the source dataset. |
| `protocol` | `INTEGER` | Protocol | Yes | Protocol number from the source dataset; treat categorically, not as an ordered magnitude. |
| `flow_duration` | `INTEGER` | Flow Duration | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `total_fwd_packets` | `INTEGER` | Total Fwd Packets | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `total_backward_packets` | `INTEGER` | Total Backward Packets | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_packets_length_total` | `INTEGER` | Fwd Packets Length Total | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_packets_length_total` | `INTEGER` | Bwd Packets Length Total | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_packet_length_max` | `INTEGER` | Fwd Packet Length Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_packet_length_min` | `INTEGER` | Fwd Packet Length Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_packet_length_mean` | `REAL` | Fwd Packet Length Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_packet_length_std` | `REAL` | Fwd Packet Length Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_packet_length_max` | `INTEGER` | Bwd Packet Length Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_packet_length_min` | `INTEGER` | Bwd Packet Length Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_packet_length_mean` | `REAL` | Bwd Packet Length Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_packet_length_std` | `REAL` | Bwd Packet Length Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `flow_bytes_s` | `REAL` | Flow Bytes/s | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `flow_packets_s` | `REAL` | Flow Packets/s | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `flow_iat_mean` | `REAL` | Flow IAT Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `flow_iat_std` | `REAL` | Flow IAT Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `flow_iat_max` | `INTEGER` | Flow IAT Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `flow_iat_min` | `INTEGER` | Flow IAT Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_iat_total` | `INTEGER` | Fwd IAT Total | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_iat_mean` | `REAL` | Fwd IAT Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_iat_std` | `REAL` | Fwd IAT Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_iat_max` | `INTEGER` | Fwd IAT Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_iat_min` | `INTEGER` | Fwd IAT Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_iat_total` | `INTEGER` | Bwd IAT Total | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_iat_mean` | `REAL` | Bwd IAT Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_iat_std` | `REAL` | Bwd IAT Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_iat_max` | `INTEGER` | Bwd IAT Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_iat_min` | `INTEGER` | Bwd IAT Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_psh_flags` | `INTEGER` | Fwd PSH Flags | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_psh_flags` | `INTEGER` | Bwd PSH Flags | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_urg_flags` | `INTEGER` | Fwd URG Flags | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_urg_flags` | `INTEGER` | Bwd URG Flags | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_header_length` | `INTEGER` | Fwd Header Length | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_header_length` | `INTEGER` | Bwd Header Length | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_packets_s` | `REAL` | Fwd Packets/s | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_packets_s` | `REAL` | Bwd Packets/s | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `packet_length_min` | `INTEGER` | Packet Length Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `packet_length_max` | `INTEGER` | Packet Length Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `packet_length_mean` | `REAL` | Packet Length Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `packet_length_std` | `REAL` | Packet Length Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `packet_length_variance` | `REAL` | Packet Length Variance | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fin_flag_count` | `INTEGER` | FIN Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `syn_flag_count` | `INTEGER` | SYN Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `rst_flag_count` | `INTEGER` | RST Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `psh_flag_count` | `INTEGER` | PSH Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `ack_flag_count` | `INTEGER` | ACK Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `urg_flag_count` | `INTEGER` | URG Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `cwe_flag_count` | `INTEGER` | CWE Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `ece_flag_count` | `INTEGER` | ECE Flag Count | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `down_up_ratio` | `INTEGER` | Down/Up Ratio | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `avg_packet_size` | `REAL` | Avg Packet Size | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `avg_fwd_segment_size` | `REAL` | Avg Fwd Segment Size | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `avg_bwd_segment_size` | `REAL` | Avg Bwd Segment Size | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_avg_bytes_bulk` | `INTEGER` | Fwd Avg Bytes/Bulk | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_avg_packets_bulk` | `INTEGER` | Fwd Avg Packets/Bulk | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_avg_bulk_rate` | `INTEGER` | Fwd Avg Bulk Rate | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_avg_bytes_bulk` | `INTEGER` | Bwd Avg Bytes/Bulk | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_avg_packets_bulk` | `INTEGER` | Bwd Avg Packets/Bulk | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `bwd_avg_bulk_rate` | `INTEGER` | Bwd Avg Bulk Rate | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `subflow_fwd_packets` | `INTEGER` | Subflow Fwd Packets | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `subflow_fwd_bytes` | `INTEGER` | Subflow Fwd Bytes | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `subflow_bwd_packets` | `INTEGER` | Subflow Bwd Packets | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `subflow_bwd_bytes` | `INTEGER` | Subflow Bwd Bytes | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `init_fwd_win_bytes` | `INTEGER` | Init Fwd Win Bytes | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `init_bwd_win_bytes` | `INTEGER` | Init Bwd Win Bytes | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_act_data_packets` | `INTEGER` | Fwd Act Data Packets | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `fwd_seg_size_min` | `INTEGER` | Fwd Seg Size Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `active_mean` | `REAL` | Active Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `active_std` | `REAL` | Active Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `active_max` | `INTEGER` | Active Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `active_min` | `INTEGER` | Active Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `idle_mean` | `REAL` | Idle Mean | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `idle_std` | `REAL` | Idle Std | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `idle_max` | `INTEGER` | Idle Max | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `idle_min` | `INTEGER` | Idle Min | No | Source flow measurement; consult the dataset feature documentation for units and calculation semantics. |
| `label_raw` | `TEXT` | Label | Yes | Original source Label string, preserved as read. |
| `attack_label` | `TEXT` | derived from Label | Yes | Canonicalized dataset ground-truth label; not an analyst-confirmed live incident. |
| `attack_family` | `TEXT` | derived from Label | Yes | Documented coarse grouping derived from the source label. |
| `source_file` | `TEXT` | derived provenance | Yes | Parquet source filename for provenance. |
| `source_row_number` | `INTEGER` | derived provenance | Yes | One-based row offset within source_file; stable only for this archive version. |
| `row_fingerprint` | `TEXT` | derived fingerprint | Yes | 64-bit fingerprint of original row values for duplicate-candidate grouping; not a unique event ID. |

## Canonical label counts

| Canonical label | Family | Rows |
|---|---|---:|
| `benign` | `benign` | 1,977,318 |
| `botnet` | `botnet` | 1,437 |
| `brute_force_ftp` | `brute_force` | 5,931 |
| `brute_force_ssh` | `brute_force` | 3,219 |
| `ddos` | `ddos` | 128,014 |
| `dos_goldeneye` | `dos` | 10,286 |
| `dos_hulk` | `dos` | 172,846 |
| `dos_slowhttptest` | `dos` | 5,228 |
| `dos_slowloris` | `dos` | 5,385 |
| `heartbleed` | `rare_attack` | 11 |
| `infiltration` | `infiltration` | 36 |
| `port_scan` | `port_scan` | 1,956 |
| `web_attack_brute_force` | `web_attack` | 1,470 |
| `web_attack_sql_injection` | `web_attack` | 21 |
| `web_attack_xss` | `web_attack` | 652 |

## Indexes

| Index | Definition |
|---|---|
| `idx_flows_attack_family` | `CREATE INDEX idx_flows_attack_family ON flows(attack_family)` |
| `idx_flows_attack_label` | `CREATE INDEX idx_flows_attack_label ON flows(attack_label)` |
| `idx_flows_fingerprint` | `CREATE INDEX idx_flows_fingerprint ON flows(row_fingerprint)` |
| `idx_flows_label_protocol` | `CREATE INDEX idx_flows_label_protocol ON flows(attack_label, protocol)` |
| `idx_flows_protocol` | `CREATE INDEX idx_flows_protocol ON flows(protocol)` |
| `sqlite_autoindex_flows_1` | `UNIQUE constraint index` |

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
