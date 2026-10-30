# CIC-IDS2017 Dataset Audit

Generated: 2026-10-11T14:11:37.815884+00:00

## Summary

- Files: 8
- Rows: 2,313,810
- Compressed size: 258.1 MiB
- Columns: 78
- Duplicate rows by 64-bit fingerprint: 82,004
- Near-duplicates were not measured.

## Files

| File | Rows | Size |
|---|---:|---:|
| `Benign-Monday-no-metadata.parquet` | 458,831 | 54.1 MiB |
| `Botnet-Friday-no-metadata.parquet` | 176,038 | 18.9 MiB |
| `Bruteforce-Tuesday-no-metadata.parquet` | 389,714 | 44.0 MiB |
| `DDoS-Friday-no-metadata.parquet` | 221,264 | 24.1 MiB |
| `DoS-Wednesday-no-metadata.parquet` | 584,991 | 65.0 MiB |
| `Infiltration-Thursday-no-metadata.parquet` | 207,630 | 22.1 MiB |
| `Portscan-Friday-no-metadata.parquet` | 119,522 | 13.0 MiB |
| `WebAttacks-Thursday-no-metadata.parquet` | 155,820 | 16.8 MiB |

## Label distribution

| Label | Rows | Share |
|---|---:|---:|
| Benign | 1,977,318 | 85.46% |
| Bot | 1,437 | 0.06% |
| DDoS | 128,014 | 5.53% |
| DoS GoldenEye | 10,286 | 0.44% |
| DoS Hulk | 172,846 | 7.47% |
| DoS Slowhttptest | 5,228 | 0.23% |
| DoS slowloris | 5,385 | 0.23% |
| FTP-Patator | 5,931 | 0.26% |
| Heartbleed | 11 | 0.00% |
| Infiltration | 36 | 0.00% |
| PortScan | 1,956 | 0.08% |
| SSH-Patator | 3,219 | 0.14% |
| Web Attack � Brute Force | 1,470 | 0.06% |
| Web Attack � Sql Injection | 21 | 0.00% |
| Web Attack � XSS | 652 | 0.03% |

## Metadata availability

| Field | Column |
|---|---|
| Flow ID | Unavailable |
| Source IP | Unavailable |
| Source Port | Unavailable |
| Destination IP | Unavailable |
| Destination Port | Unavailable |
| Timestamp | Unavailable |

## Nulls and non-finite numeric values

Null values:

| Column | Count |
|---|---:|
| None | 0 |

NaN and infinity values in numeric columns:

| Column | Count |
|---|---:|
| None | 0 |

## Schema

| Column | Type |
|---|---|
| `Protocol` | `int8` |
| `Flow Duration` | `int32` |
| `Total Fwd Packets` | `int32` |
| `Total Backward Packets` | `int32` |
| `Fwd Packets Length Total` | `int32` |
| `Bwd Packets Length Total` | `int32` |
| `Fwd Packet Length Max` | `int16` |
| `Fwd Packet Length Min` | `int16` |
| `Fwd Packet Length Mean` | `float` |
| `Fwd Packet Length Std` | `float` |
| `Bwd Packet Length Max` | `int16` |
| `Bwd Packet Length Min` | `int16` |
| `Bwd Packet Length Mean` | `float` |
| `Bwd Packet Length Std` | `float` |
| `Flow Bytes/s` | `double` |
| `Flow Packets/s` | `double` |
| `Flow IAT Mean` | `float` |
| `Flow IAT Std` | `float` |
| `Flow IAT Max` | `int32` |
| `Flow IAT Min` | `int32` |
| `Fwd IAT Total` | `int32` |
| `Fwd IAT Mean` | `float` |
| `Fwd IAT Std` | `float` |
| `Fwd IAT Max` | `int32` |
| `Fwd IAT Min` | `int32` |
| `Bwd IAT Total` | `int32` |
| `Bwd IAT Mean` | `float` |
| `Bwd IAT Std` | `float` |
| `Bwd IAT Max` | `int32` |
| `Bwd IAT Min` | `int32` |
| `Fwd PSH Flags` | `int8` |
| `Bwd PSH Flags` | `int8` |
| `Fwd URG Flags` | `int8` |
| `Bwd URG Flags` | `int8` |
| `Fwd Header Length` | `int32` |
| `Bwd Header Length` | `int32` |
| `Fwd Packets/s` | `float` |
| `Bwd Packets/s` | `float` |
| `Packet Length Min` | `int16` |
| `Packet Length Max` | `int16` |
| `Packet Length Mean` | `float` |
| `Packet Length Std` | `float` |
| `Packet Length Variance` | `float` |
| `FIN Flag Count` | `int8` |
| `SYN Flag Count` | `int8` |
| `RST Flag Count` | `int8` |
| `PSH Flag Count` | `int8` |
| `ACK Flag Count` | `int8` |
| `URG Flag Count` | `int8` |
| `CWE Flag Count` | `int8` |
| `ECE Flag Count` | `int8` |
| `Down/Up Ratio` | `int8` |
| `Avg Packet Size` | `float` |
| `Avg Fwd Segment Size` | `float` |
| `Avg Bwd Segment Size` | `float` |
| `Fwd Avg Bytes/Bulk` | `int8` |
| `Fwd Avg Packets/Bulk` | `int8` |
| `Fwd Avg Bulk Rate` | `int8` |
| `Bwd Avg Bytes/Bulk` | `int8` |
| `Bwd Avg Packets/Bulk` | `int8` |
| `Bwd Avg Bulk Rate` | `int8` |
| `Subflow Fwd Packets` | `int32` |
| `Subflow Fwd Bytes` | `int32` |
| `Subflow Bwd Packets` | `int32` |
| `Subflow Bwd Bytes` | `int32` |
| `Init Fwd Win Bytes` | `int32` |
| `Init Bwd Win Bytes` | `int32` |
| `Fwd Act Data Packets` | `int32` |
| `Fwd Seg Size Min` | `int32` |
| `Active Mean` | `float` |
| `Active Std` | `float` |
| `Active Max` | `int32` |
| `Active Min` | `int32` |
| `Idle Mean` | `float` |
| `Idle Std` | `float` |
| `Idle Max` | `int32` |
| `Idle Min` | `int32` |
| `Label` | `dictionary<values=string, indices=int8, ordered=0>` |