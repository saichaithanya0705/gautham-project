# Synapt Cybersecurity Incident Response Assistant

Python service for cybersecurity incident investigation with Synapt integration,
machine learning, historical retrieval, and evaluation tooling.

See [PROJECT_HANDOFF_CONTEXT.md](PROJECT_HANDOFF_CONTEXT.md) for implementation
status and known limitations, and [docs/OVERALL_ARCHITECTURE.md](docs/OVERALL_ARCHITECTURE.md)
for the architecture. Existing evaluation reports are historical snapshots.

## Local setup

Use Python 3.11 or newer, then run from the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

Configure your own Synapt and optional model provider credentials in `.env`.
Keep credentials and private CA bundles local.

## Dataset and models

Git excludes raw Parquet datasets, SQLite databases, and trained models. Obtain
the CIC-IDS2017 Parquet files separately and place them in `data/archive/`, then run:

```powershell
python scripts/ingest_parquet_to_sqlite.py --data-dir data/archive --db data/cicids2017.sqlite3
python scripts/create_demo_database.py --source data/cicids2017.sqlite3 --output data/cicids2017_demo.sqlite3
python scripts/train_ml_models.py --db data/cicids2017.sqlite3
python scripts/train_anomaly_detector.py
```

The example environment selects the demo database. The small CSV sample in
`data/` is reference data; it is not a replacement for the SQLite database.
The demo creation script refuses to overwrite an existing target.

## Run

```powershell
uvicorn cyber_assistant.main:app --reload
```

For connectivity checks and transfer-specific notes, see
[README_TRANSFER.md](README_TRANSFER.md). Its references to an included database
apply to the original transfer archive; databases are excluded from Git.

## Checks

```powershell
python -m pytest
```

Some evaluation and connectivity checks require configured external services.
