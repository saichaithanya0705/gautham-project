# Project Handoff Context

## Goal

Build an AI-powered cybersecurity incident investigation assistant for
CIC-IDS2017. It should help analysts retrieve relevant historical flows,
understand attack patterns, assess risk, and find evidence-backed response
guidance. It is an analyst aid; it must not perform automated containment.

## Architecture decisions

- **Synapt is the security knowledge and reasoning layer.** Ingest curated
  security concepts, feature explanations, reviewed procedures, and a safe
  description of the SQLite schema through supported MCP tools.
- **SQLite stores the flow records.** Exact filters and flow evidence remain in
  SQLite; do not ingest millions of flow rows into Synapt.
- **No separate vector database.** Synapt provides semantic/graph retrieval;
  SQLite handles structured flow queries.
- **LangGraph coordinates the workflow.** Keep SQLite evidence and Synapt
  evidence separate and preserve source provenance.
- Use Synapt's configured model for generative answers. Deterministic Python
  logic may validate input, compute risk indicators, and run local ML models.
- Synthetic data may be used for clearly labeled development examples, but
  must never be described as real CIC-IDS2017 observations.

## Dataset findings

The local archive contained eight Parquet files with 2,313,810 total rows,
15 attack labels, and 78 source columns including the label. The archive lacks
Flow ID, source/destination IP addresses, source/destination ports, and
timestamps. Do not invent these fields. Repeated feature fingerprints are
duplicate candidates, not proof of duplicate events.

The transfer ZIP includes a compact, deterministic sample database with up to
1,000 benign rows and up to 250 rows per other attack label. This supports a
local demo and is explicitly marked as a sample. The full database and source
Parquet files are not in the ZIP; see `README_TRANSFER.md` to rebuild the full
SQLite database from the original archive.

## Synapt/provider status

- Project provider ID: `assist_cyber` (the platform screenshot showed provider
  ID with underscore; do not substitute the hyphenated display slug).
- The platform UI showed 17 tools, including schema, search, query, stats,
  procedures, feedback, and ingestion. Another supplied guide lists 16, so the
  client discovers the actual tools dynamically.
- `SYNAPT_MCP_AGENT_CONNECTION.md` in the source workspace contains hard-coded
  credentials for a different example provider and is intentionally excluded
  from the transfer bundle. Never use those values; request a clean guide if
  needed and rotate them if they are real credentials.
- The project's MCP adapter follows form-encoded login, JSON-RPC initialize,
  dynamic `tools/list`, and `tools/call`. It does not use mock results.
- The connection check with the office CA bundle still failed TLS certificate
  chain verification before login. It did not reach MCP discovery, schema, or
  stats. On a personal PC it may connect without the office proxy CA; if not,
  ask the network owner for the correct CA chain. Do not disable TLS checks.
- `.env`, credentials, and the CA certificate are excluded. Create a local
  `.env` from `.env.example` on the destination PC.

## Current implementation status

- Full local SQLite loader, dataset audit, schema exporter, FastAPI endpoint
  scaffold, SQLite read-only query layer, and LangGraph workflow scaffold exist.
- `POST /search/incidents` supports label/family, protocol, source file,
  flow-duration ranges, and simple keyword matching on label/family/source.
- SQLite matching is not semantic similarity. Semantic retrieval depends on a
  live Synapt connection.
- `/health` reports SQLite readiness and Synapt configuration state.
- The API and MCP client have not been end-to-end verified because dependencies
  could not be installed in the prior environment and TLS blocked Synapt.
- ML training, risk policy, frontend, evaluation suite, feedback capture, and
  the final panel presentation are still planned work.

## Package contents and exclusions

The ZIP contains source code, setup instructions, planner and project brief,
dataset audit/schema documentation, and the small demo SQLite database. It
excludes `.env` files, the old connector project, private CA files, generated
Python caches, the 1 GB full SQLite database, and the 8 Parquet source files.

Start with `README_TRANSFER.md`.
