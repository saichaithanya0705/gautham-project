# Transfer Bundle Setup

See [PROJECT_HANDOFF_CONTEXT.md](PROJECT_HANDOFF_CONTEXT.md) for project scope,
dataset limitations, Synapt status, and next implementation steps.

## Quick start

1. Install Python 3.11 or newer.
2. Create an environment and install dependencies:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. Add your own Synapt credentials and provider
   settings locally. Never share or package `.env` or a CA certificate bundle.
4. Start the API from the project root:

   ```powershell
   uvicorn cyber_assistant.main:app --app-dir src --reload
   ```

The transfer archive includes `data/cicids2017_demo.sqlite3`, a small labeled
sample database. Set `DATABASE_PATH=data/cicids2017_demo.sqlite3` for the demo.
It is not the full CIC-IDS2017 benchmark.

## Use the full dataset

The original eight Parquet files are intentionally excluded to keep the ZIP
under 50 MB. Copy the dataset folder onto the target PC, install `pyarrow`,
`pandas`, and `numpy` from `requirements.txt`, then run:

```powershell
python scripts/ingest_parquet_to_sqlite.py --data-dir "archive (1)" --db data/cicids2017.sqlite3
```

Then set `DATABASE_PATH=data/cicids2017.sqlite3` in `.env` and regenerate the
Synapt schema reference if needed:

```powershell
python scripts/export_sqlite_schema.py --db data/cicids2017.sqlite3 --output docs/sqlite_schema_for_synapt.md
```

## Synapt connectivity

Run `python scripts/check_synapt_mcp.py` after configuring `.env`. The project
uses the credentials and provider ID in that file; no credentials are included
in the transfer bundle. If the target machine uses TLS inspection, configure an
IT-approved CA bundle via `SYNAPT_CA_BUNDLE` and keep certificate verification
enabled.
