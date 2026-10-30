"""Render crystal-clear, uncrossed presentation architecture flow diagram as PNG, SVG, PDF, and interactive HTML."""

from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture"

# Clean high-contrast corporate palette
INK = "#0f172a"
MUTED = "#475569"
BLUE = "#1d4ed8"       # Primary Flow
CYAN = "#0369a1"       # ML & Analytics
EMERALD = "#047857"    # Safety & Triage
TEAL = "#0f766e"       # Results
PURPLE = "#6d28d9"     # Multi-Agent & Synapt
AMBER = "#b45309"      # Policies & Gates
ROSE = "#be123c"       # Guardrails & Judge
DARK_BLUE = "#1e293b"  # System Headers

CANVAS_W = 30.0
CANVAS_H = 20.5
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(CANVAS_W, CANVAS_H))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(0, CANVAS_W)
    ax.set_ylim(CANVAS_H, 0)  # Top-down coordinates
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def text(x, y, label, size=11, color=INK, weight="normal", **kwargs):
        return ax.text(
            x,
            y,
            label,
            fontsize=size,
            color=color,
            weight=weight,
            va="top",
            zorder=5,
            **kwargs,
        )

    def box(
        x,
        y,
        w,
        h,
        title,
        body="",
        accent=BLUE,
        fill="white",
        title_size=10.5,
        body_size=8.8,
        dashed=False,
    ):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.10",
                linewidth=1.25,
                edgecolor=accent,
                facecolor=fill,
                linestyle=(0, (4, 3)) if dashed else "solid",
                zorder=3,
            )
        )
        text(x + 0.12, y + 0.12, title, title_size, accent, "bold")
        if body:
            text(x + 0.12, y + 0.40, body, body_size, MUTED, linespacing=1.35)

    def arrow(start, end, color=BLUE, dashed=False, label=None, label_pos=None):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.4,
                color=color,
                linestyle=(0, (4, 3)) if dashed else "solid",
                zorder=4,
                connectionstyle="arc3,rad=0",
            )
        )
        if label and label_pos:
            text(
                label_pos[0],
                label_pos[1],
                label,
                size=8.0,
                color=color,
                weight="bold",
                bbox={"facecolor": "#ffffff", "edgecolor": "#cbd5e1", "pad": 1.2, "boxstyle": "round,pad=0.2"},
            )

    def section_band(y, h, title, subtitle, color):
        ax.add_patch(
            FancyBboxPatch(
                (0.5, y),
                29.0,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                facecolor="#ffffff",
                edgecolor="#cbd5e1",
                linewidth=1.1,
                zorder=0,
            )
        )
        text(0.8, y + 0.15, title, 11.0, color, "bold")
        if subtitle:
            text(0.8, y + 0.40, subtitle, 8.8, MUTED)

    # -------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------
    text(0.8, 0.25, "CYBERSENTINEL COPILOT - PRESENTATION ARCHITECTURE & DATA FLOW", 11.0, BLUE, "bold")
    text(0.8, 0.56, "End-to-End Investigation Architecture: Clear Multi-Agent & Tool Mapping", 20.0, INK, "bold")
    text(0.8, 1.02, "Frontend UI -> FastAPI Gateway -> 7-Agent LangGraph Pipeline (Aligned to Underlying Engines) -> Verified SOC Output", 10.2, MUTED)

    # =============================================================
    # LAYER 1: USER INPUT & API GATEWAY (TOP BAND)
    # =============================================================
    section_band(1.35, 2.70, "LAYER 1 : ANALYST INPUT & BACKEND API GATEWAY", "How user triggers an investigation and how FastAPI enforces input contracts", DARK_BLUE)

    box(0.8, 1.95, 5.8, 1.85, "1. Security Analyst", "SOC Tier-1/2 Analyst\nInvestigates alerts, scans,\nand abnormal network flows", DARK_BLUE, "#f8fafc")
    box(7.0, 1.95, 6.8, 1.85, "2. Analyst Input Options", "* Record ID (e.g. 2039912)\n* Free-Text Query (e.g. 'SYN flood')\n* Metadata Filters (Protocol/Time)\n* Raw Telemetry JSON (78 feats)", BLUE, "white")
    box(14.2, 1.95, 7.2, 1.85, "3. SOC Copilot Dashboard", "Web UI on http://localhost:8000/\nInteractive form, pipeline status,\nand live audit cards", CYAN, "white")
    box(21.8, 1.95, 7.3, 1.85, "4. FastAPI Microservice", "POST /investigate/flow\nPydantic Contract: FlowInvestigationRequest\nStrict schema & range bounds enforcement", BLUE, "#eff6ff")

    arrow((6.6, 2.87), (7.0, 2.87), DARK_BLUE, label="Enters Query", label_pos=(6.65, 2.65))
    arrow((13.8, 2.87), (14.2, 2.87), BLUE, label="UI Trigger", label_pos=(13.85, 2.65))
    arrow((21.4, 2.87), (21.8, 2.87), CYAN, label="HTTP POST", label_pos=(21.45, 2.65))

    # =============================================================
    # LAYER 2: 7-AGENT LANGGRAPH PIPELINE (MIDDLE BAND)
    # 7 AGENTS IN A PERFECT HORIZONTAL SEQUENCE
    # =============================================================
    section_band(4.40, 4.30, "LAYER 2 : 7-STAGE SEQUENTIAL LANGGRAPH MULTI-AGENT ORCHESTRATION", "Sequential deterministic state flow: Every agent executes in strict order with clean state handoffs", PURPLE)

    # 7 Agents: width=3.7, spacing=0.4
    agent_y = 5.05
    agent_h = 3.35
    w_ag = 3.7
    gap_ag = 0.45
    x_ag = [0.8 + i * (w_ag + gap_ag) for i in range(7)]

    box(x_ag[0], agent_y, w_ag, agent_h, "Agent 1: Guardrail", "* Input Sanitization\n* Prompt Injection Filter\n* XML Context Isolation\n* Relevance Check\n* Blocks Auto-Containment", ROSE, "#fff1f2")
    box(x_ag[1], agent_y, w_ag, agent_h, "Agent 2: Triage & RAG", "* Exact Record Lookup\n* 404 Validation Guard\n* FTS5 BM25 Search\n* Synapt Semantic Search\n* RRF Hybrid Ranking", BLUE, "#eff6ff")
    box(x_ag[2], agent_y, w_ag, agent_h, "Agent 3: ML Analysis", "* HistGradientBoosting\n  (9 Attack Families)\n* Intrusion Risk (1-P_benign)\n* IsolationForest Anomaly\n* Top-5 Feature Deviations", CYAN, "#f0f9ff")
    box(x_ag[3], agent_y, w_ag, agent_h, "Agent 4: Knowledge", "* Read-Only incident-agent\n* Synapt Knowledge Graph\n* trident_query\n* trident_get_procedures\n* MITRE ATT&CK Mapping", PURPLE, "#faf5ff")
    box(x_ag[4], agent_y, w_ag, agent_h, "Agent 5: Prioritization", "* Deterministic Triage\n* Policy Decision Matrix\n* Maps Risk to P1-P4\n* Evaluates Anomaly Severity\n* Discloses Missing Context", AMBER, "#fffbeb")
    box(x_ag[5], agent_y, w_ag, agent_h, "Agent 6: Response", "* NIST SP 800-61 Playbook\n* Step-by-Step Checklist\n* Containment Guidance\n* Human-in-Loop Safeguards\n* Source Provenance", EMERALD, "#ecfdf5")
    box(x_ag[6], agent_y, w_ag, agent_h, "Agent 7: Judge Review", "* Read-Only judge-agent\n* Hard Invariant Safety Check\n* External LLM-as-a-Judge\n* Scores 4 Dimensions:\n  Grounding/Safety/NIST/Rel", ROSE, "#fff1f2")

    # Link from FastAPI Gateway down to Agent 1
    arrow((25.4, 3.80), (25.4, 4.10), PURPLE)
    arrow((25.4, 4.10), (2.65, 4.10), PURPLE)
    arrow((2.65, 4.10), (2.65, 5.05), PURPLE, label="START Orchestration", label_pos=(10.0, 4.18))

    # Sequential horizontal arrows between all 7 agents
    for i in range(6):
        x_start = x_ag[i] + w_ag
        x_end = x_ag[i + 1]
        arrow((x_start, agent_y + 1.6), (x_end, agent_y + 1.6), PURPLE)

    # =============================================================
    # LAYER 3: UNDERPINNING DATA, ML, SYNAPT & JUDGE ENGINES
    # PLACED DIRECTLY BELOW THE EXACT CORRESPONDING AGENT!
    # ZERO CROSSING LINES!
    # =============================================================
    section_band(9.05, 5.30, "LAYER 3 : SUPPORTING DATA STORES, ML MODELS, SYNAPT CONTEXT SUBSTRATE & LLM ENGINES", "Every agent maps straight down to its exact underlying tool or service with zero line-crossing", EMERALD)

    eng_y = 9.80
    eng_h = 4.25

    # 1. Guardrail Engine (Under Agent 1)
    box(x_ag[0], eng_y, w_ag, eng_h, "Guardrail Engine", "src/cyber_assistant/\nguardrails.py\n\n* Parameter Range Bounds\n* Regex Injection Scanners\n* Non-Destructive Invariant\n* Domain Term Verification", ROSE, "white")
    arrow((x_ag[0] + w_ag / 2, agent_y + agent_h), (x_ag[0] + w_ag / 2, eng_y), ROSE, dashed=True, label="Safety Gate", label_pos=(x_ag[0] + 0.1, 8.85))

    # 2. SQLite DB & FTS5 (Under Agent 2)
    box(x_ag[1], eng_y, w_ag, eng_h, "Local SQLite & FTS5", "data/cicids2017.sqlite3\n\n* 2,313,810 Flow Records\n* Read-Only Queries\n* SQLite FTS5 Index\n* 291 Seeded Summaries\n* BM25 Keyword Search", BLUE, "white")
    arrow((x_ag[1] + w_ag / 2, agent_y + agent_h), (x_ag[1] + w_ag / 2, eng_y), BLUE, dashed=True, label="Exact & BM25", label_pos=(x_ag[1] + 0.1, 8.85))

    # 3. Supervised & Anomaly ML Models (Under Agent 3)
    box(x_ag[2], eng_y, w_ag, eng_h, "ML Model Engines", "models/\nattack_classifier.joblib\nanomaly_detector.joblib\n\n* HistGradientBoosting\n  (65 Flow Features)\n* IsolationForest (Benign)\n* Feature Baseline Profiler", CYAN, "white")
    arrow((x_ag[2] + w_ag / 2, agent_y + agent_h), (x_ag[2] + w_ag / 2, eng_y), CYAN, dashed=True, label="ML Inference", label_pos=(x_ag[2] + 0.1, 8.85))

    # 4. Synapt Context Substrate MCP (Under Agent 4)
    box(x_ag[3], eng_y, w_ag, eng_h, "Synapt Context MCP", "Provider: assist_cyber\n(https://beta.synapt.ai)\n\n* trident_query\n* trident_search\n* trident_get_procedures\n* MITRE ATT&CK KG\n* trident_feedback", PURPLE, "#faf5ff")
    arrow((x_ag[3] + w_ag / 2, agent_y + agent_h), (x_ag[3] + w_ag / 2, eng_y), PURPLE, dashed=True, label="MCP Tools", label_pos=(x_ag[3] + 0.1, 8.85))

    # 5. Policy Matrix (Under Agent 5)
    box(x_ag[4], eng_y, w_ag, eng_h, "SOC Triage Matrix", "src/cyber_assistant/\npolicy.py\n\n* P1: Critical Volumetric\n* P2: High Threat Scans\n* P3: Medium Anomalies\n* P4: Low / Benign Flows\n* Missing Context Flags", AMBER, "white")
    arrow((x_ag[4] + w_ag / 2, agent_y + agent_h), (x_ag[4] + w_ag / 2, eng_y), AMBER, dashed=True, label="Triage Rules", label_pos=(x_ag[4] + 0.1, 8.85))

    # 6. NIST SOP Synthesizer (Under Agent 6)
    box(x_ag[5], eng_y, w_ag, eng_h, "NIST SP 800-61 SOP", "SOP Playbook Database\n\n* Phase 1: Detection\n* Phase 2: Containment\n* Phase 3: Eradication\n* Phase 4: Recovery\n* Provenance Tracing", EMERALD, "white")
    arrow((x_ag[5] + w_ag / 2, agent_y + agent_h), (x_ag[5] + w_ag / 2, eng_y), EMERALD, dashed=True, label="Playbooks", label_pos=(x_ag[5] + 0.1, 8.85))

    # 7. LLM-as-a-Judge & DeepEval (Under Agent 7)
    box(x_ag[6], eng_y, w_ag, eng_h, "LLM Judge & DeepEval", "NVIDIA NIM / OpenAI\nEndpoint (nvapi-...)\n\n* meta/llama-3.2-11b\n* ResponseJudge Engine\n* DeepEval v4.2.8 Bench\n* 40/40 Passing Cases\n* 100% Safety Compliance", ROSE, "#fff1f2")
    arrow((x_ag[6] + w_ag / 2, agent_y + agent_h), (x_ag[6] + w_ag / 2, eng_y), ROSE, dashed=True, label="LLM Audit", label_pos=(x_ag[6] + 0.1, 8.85))

    # =============================================================
    # LAYER 4: FINAL OUTPUT & DASHBOARD CARDS (BOTTOM BAND)
    # FLOWS STRAIGHT FROM AGENT 7 / JUDGE INTO VERIFIED OUTPUT
    # =============================================================
    section_band(14.70, 5.40, "LAYER 4 : FINAL VERIFIED OUTPUT & SOC DASHBOARD VISUALIZATION", "Complete JSON response rendered into interactive analyst cards and continuous feedback loop", TEAL)

    # Contract box on the left
    box(0.8, 15.35, 4.8, 4.40, "FlowInvestigationResponse", "* Formatted JSON Schema\n* Deterministic Telemetry\n* Supervised Probabilities\n* Anomaly Deviation Ratios\n* MITRE ATT&CK Badges\n* NIST Action Playbook\n* Verified Judge Verdict\n* Complete Audit Trail", TEAL, "#f0fdfa")

    # Connect Agent 7 output to final contract
    arrow((x_ag[6] + w_ag / 2, eng_y + eng_h), (x_ag[6] + w_ag / 2, 14.9), TEAL)
    arrow((x_ag[6] + w_ag / 2, 14.9), (3.2, 14.9), TEAL)
    arrow((3.2, 14.9), (3.2, 15.35), TEAL, label="Verified Investigation State Output", label_pos=(12.0, 14.98))

    # Dashboard Cards
    card_y = 15.35
    card_w = 3.65
    card_gap = 0.35
    card_x = [6.0 + i * (card_w + card_gap) for i in range(6)]

    box(card_x[0], card_y, card_w, 4.40, "Triage Banner", "* Attack Family Tag\n* Severity Level\n* Operational Tier:\n  P1, P2, P3, or P4\n* Status: Verified\n* Non-Destructive Aid", BLUE, "white")
    box(card_x[1], card_y, card_w, 4.40, "ML Risk Gauge", "* Supervised Class\n* Intrusion Risk Score:\n  1 - P(benign)\n* Multiclass Probabilities\n* Anomaly Indicator:\n  IsolationForest Score", CYAN, "white")
    box(card_x[2], card_y, card_w, 4.40, "Feature Deviations", "* Top-5 Deviations\n* Observed Flow Value\n* Benign Baseline Mean\n* Ratio Multipliers\n* Explainable Telemetry", CYAN, "white")
    box(card_x[3], card_y, card_w, 4.40, "MITRE & Similar", "* MITRE ATT&CK IDs\n  (e.g. T1046, T1498)\n* Tactical Category\n* Top Similar Incidents\n  (RRF Fused BM25 +\n  Synapt Semantic)", PURPLE, "#faf5ff")
    box(card_x[4], card_y, card_w, 4.40, "NIST Action Plan", "* Step-by-Step Actions\n* Safe Containment\n* Target Host Audit\n* Service Isolation Prep\n* Human Approval Gate", EMERALD, "#ecfdf5")
    box(card_x[5], card_y, card_w, 4.40, "Judge Quality Card", "* Pass Verdict: TRUE\n* Safety Score: 100%\n* Grounding: 90%\n* NIST Align: 85%\n* Relevancy: 90%\n* LLM Critique Box", ROSE, "#fff1f2")

    # Connect response box to first card, and chain cleanly
    arrow((5.6, card_y + 2.2), (card_x[0], card_y + 2.2), TEAL)
    for i in range(5):
        arrow((card_x[i] + card_w, card_y + 2.2), (card_x[i + 1], card_y + 2.2), TEAL)

    # Save diagram files
    png_path = OUT / "presentation_flow_diagram.png"
    svg_path = OUT / "presentation_flow_diagram.svg"
    pdf_path = OUT / "presentation_flow_diagram.pdf"

    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {png_path}, {svg_path}, {pdf_path}")

    # Generate interactive HTML viewer
    svg_content = svg_path.read_text(encoding="utf-8")
    clean_svg = svg_content[svg_content.find("<svg"):]

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CyberSentinel - Presentation Architecture Flow Diagram</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; overflow: hidden; }}
    header {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 24px; background: #1e293b; border-bottom: 1px solid #334155; flex-wrap: wrap; }}
    h1 {{ font-size: 18px; margin: 0 0 4px; color: #38bdf8; }}
    p {{ font-size: 12.5px; color: #94a3b8; margin: 0; }}
    .tools {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
    button, a {{ font: inherit; font-size: 13px; color: #f8fafc; border: 1px solid #475569; background: #334155; padding: 8px 14px; border-radius: 6px; text-decoration: none; cursor: pointer; transition: all 0.15s; }}
    button:hover, a:hover {{ background: #0284c7; border-color: #38bdf8; }}
    #stage {{ height: calc(100vh - 70px); width: 100vw; overflow: auto; position: relative; display: flex; justify-content: center; align-items: flex-start; padding: 20px; }}
    #drawing {{ max-width: 100%; transition: transform 0.2s ease; transform-origin: top center; }}
    #drawing svg {{ width: 100%; max-width: 2500px; height: auto; display: block; border-radius: 8px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>CyberSentinel Copilot - Presentation Architecture & Data Flow</h1>
      <p>Clean Columnar Flow: Frontend -> FastAPI -> 7-Agent LangGraph -> Underlying Engines -> Dashboard Cards</p>
    </div>
    <nav class="tools">
      <button onclick="zoomOut()">-</button>
      <span id="zoom-val" style="font-size: 13px; font-weight: bold; min-width: 45px; text-align: center;">100%</span>
      <button onclick="zoomIn()">+</button>
      <button onclick="resetZoom()">Fit</button>
      <a href="presentation_flow_diagram.png" download>Download PNG</a>
      <a href="presentation_flow_diagram.svg" download>Download SVG</a>
      <a href="presentation_flow_diagram.pdf" download>Download PDF</a>
    </nav>
  </header>
  <main id="stage">
    <div id="drawing">
      {clean_svg}
    </div>
  </main>
  <script>
    let scale = 1.0;
    const drawing = document.getElementById('drawing');
    const zoomVal = document.getElementById('zoom-val');
    function update() {{
      drawing.style.transform = `scale(${{scale}})`;
      zoomVal.innerText = `${{Math.round(scale * 100)}}%`;
    }}
    function zoomIn() {{ scale = Math.min(2.5, scale + 0.15); update(); }}
    function zoomOut() {{ scale = Math.max(0.4, scale - 0.15); update(); }}
    function resetZoom() {{ scale = 1.0; update(); }}
  </script>
</body>
</html>"""
    html_path = OUT / "presentation_flow_diagram.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"Generated: {html_path}")


if __name__ == "__main__":
    render()
