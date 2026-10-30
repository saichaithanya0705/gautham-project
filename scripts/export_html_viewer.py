"""Generate a standalone interactive HTML viewer for the SQLite demo database."""

import sqlite3
import pandas as pd
from pathlib import Path

def generate_viewer():
    db_path = Path("data/cicids2017_demo.sqlite3")
    if not db_path.exists():
        print("Database not found:", db_path)
        return

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        """
        SELECT record_id, attack_family, attack_label, protocol, flow_duration, 
               round(flow_bytes_s, 1) as flow_bytes_s, round(flow_packets_s, 1) as flow_packets_s,
               syn_flag_count, rst_flag_count, source_file, source_row_number
        FROM flows 
        LIMIT 1000
        """,
        conn
    )
    conn.close()

    th_html = "".join(f"<th>{col}</th>" for col in df.columns)
    rows_html = []
    for _, row in df.iterrows():
        tds = "".join(f"<td>{val}</td>" for val in row)
        rows_html.append(f"<tr>{tds}</tr>")
    tb_html = "\n".join(rows_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CIC-IDS2017 SQLite Database Viewer</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; }}
    .card {{ background: #1e293b; border: 1px solid #334155; color: #f8fafc; }}
    table.table {{ color: #e2e8f0; }}
    .dataTables_wrapper {{ color: #cbd5e1; }}
    .page-link {{ background-color: #334155; border-color: #475569; color: #38bdf8; }}
    .page-item.active .page-link {{ background-color: #0284c7; border-color: #0284c7; }}
    .form-control, .form-select {{ background-color: #0f172a; border-color: #334155; color: #f8fafc; }}
  </style>
</head>
<body class="p-4">
  <div class="container-fluid">
    <div class="card p-4 shadow-lg rounded">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 class="fw-bold text-info">🛡️ CIC-IDS2017 SQLite Interactive Table Viewer</h2>
          <p class="text-secondary mb-0">Showing 1,000 sample flows from <code>data/cicids2017_demo.sqlite3</code></p>
        </div>
        <span class="badge bg-primary fs-6">3,818 Total Records</span>
      </div>
      <div class="table-responsive">
        <table id="flowsTable" class="table table-dark table-striped table-hover table-bordered w-100">
          <thead>
            <tr>{th_html}</tr>
          </thead>
          <tbody>
            {tb_html}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
  <script>
    $(document).ready(function() {{
      $('#flowsTable').DataTable({{
        pageLength: 20,
        lengthMenu: [10, 20, 50, 100],
        order: [[0, 'asc']]
      }});
    }});
  </script>
</body>
</html>
"""
    out_file = Path("data/view_data.html")
    out_file.write_text(html_content, encoding="utf-8")
    print(f"Successfully generated {out_file.resolve()}")

if __name__ == "__main__":
    generate_viewer()
