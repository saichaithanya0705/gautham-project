"""Render the panel-ready user-input-to-final-output architecture."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture"
W, H = 32.0, 20.2
HTML_W, HTML_H = 3200, 2020
INK = "#142b43"
MUTED = "#53687b"
BLUE = "#3478bd"
TEAL = "#168393"
PURPLE = "#795fac"
AMBER = "#ad791e"
ROSE = "#9a579b"
BG = "#f8fafc"
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(W, H))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)

    def text(x, y, value, size=11, color=INK, weight="normal", **kwargs):
        return ax.text(x, y, value, fontsize=size, color=color, weight=weight,
                       va="top", zorder=5, **kwargs)

    def band(y, h, title, color, subtitle=""):
        ax.add_patch(FancyBboxPatch(
            (0.24, y), 31.52, h, boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor="#f0f5fa", edgecolor="#d5e0ea", linewidth=1, zorder=0))
        text(0.52, y + 0.13, title, 10.4, color, "bold")
        if subtitle:
            text(31.48, y + 0.13, subtitle, 8.9, MUTED, "normal", ha="right")

    def box(x, y, w, h, title, body="", accent=BLUE, fill="white", ts=10.8, bs=8.8):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.022,rounding_size=0.09",
            facecolor=fill, edgecolor=accent, linewidth=1.15, zorder=3))
        text(x + 0.13, y + 0.12, title, ts, accent, "bold")
        if body:
            text(x + 0.13, y + 0.43, body, bs, MUTED, linespacing=1.35)

    def arrow(start, end, color=BLUE, dashed=False, curve=0):
        ax.add_patch(FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=11, linewidth=1.35,
            color=color, linestyle=(0, (4, 3)) if dashed else "solid", zorder=2,
            connectionstyle=f"arc3,rad={curve}"))

    def routed_arrow(points, color=BLUE, dashed=False):
        xs, ys = zip(*points)
        ax.plot(xs[:-1], ys[:-1], color=color, linewidth=1.35,
                linestyle=(0, (4, 3)) if dashed else "solid", zorder=2)
        arrow(points[-2], points[-1], color, dashed)

    text(0.55, 0.24, "CYBERSENTINEL COPILOT", 11.1, BLUE, "bold")
    text(0.55, 0.60, "Presentation architecture · user input to final analyst output", 25, INK, "bold")
    text(0.55, 1.12,
         "Frontend → backend → seven investigation agents → aligned Synapt roles and tools → result → human-reviewed feedback",
         11.8, MUTED)

    # Phase 1: entry.
    band(1.48, 2.42, "PHASE 1 · USER INPUT → FRONTEND → BACKEND ENTRY", BLUE)
    entry_x = [0.52, 6.80, 13.08, 19.36, 25.64]
    entry_titles = [
        "1 · SOC analyst input", "2 · Frontend dashboard", "3 · FastAPI backend",
        "4 · Pydantic contract", "5 · LangGraph entry",
    ]
    entry_bodies = [
        "Record ID · question\nAttack family · protocol\nOptional raw flow",
        "Investigation tab\nSearch · chat · feedback\nHTML/CSS/JavaScript",
        "POST /investigate/flow\nRoute dispatch\nShared services",
        "Types · ranges · lengths\nAt least one input\nHTTP 422 on failure",
        "Create InvestigationState\nStart compiled StateGraph\nCarry evidence forward",
    ]
    for i, (x, title, body) in enumerate(zip(entry_x, entry_titles, entry_bodies)):
        box(x, 1.93, 5.82, 1.55, title, body, BLUE, "#edf5ff", 10.7, 8.7)
        if i < 4:
            arrow((x + 5.82, 2.70), (entry_x[i + 1], 2.70), BLUE)

    # Phase 2: seven agents.
    band(4.18, 3.02, "PHASE 2 · LANGGRAPH INCIDENT INVESTIGATION — SEVEN AGENTS IN EXECUTION ORDER", BLUE)
    ax_stage = [0.48 + 4.50 * i for i in range(7)]
    aw = 4.10
    titles = [
        "Agent 1 · Guardrail", "Agent 2 · Flow Triage", "Agent 3 · ML Analysis",
        "Agent 4 · Knowledge", "Agent 5 · Priority", "Agent 6 · Response", "Agent 7 · Judge",
    ]
    bodies = [
        "guardrails.py\nInjection · relevance\nAction/telemetry safety",
        "sqlite_store.py + RAG\nExact record / 404\nHistorical similarity",
        "predictor.py + anomaly.py\nFamily · risk · deviations\nIsolationForest + MITRE",
        "synapt_knowledge_agent\nSanitized provider question\nProcedures + indicators",
        "policy.py\nDeterministic P1–P4\nRationale + missing context",
        "workflow.py builder\nSteps · response drafts\nProvenance + limitations",
        "evaluator.py\nHard safety gate\nGrounding/NIST/relevance",
    ]
    colors = [BLUE, TEAL, PURPLE, AMBER, BLUE, BLUE, AMBER]
    fills = ["#edf5ff", "#e8f7f5", "#f1edfa", "#fff5df", "#edf5ff", "#edf5ff", "#fff5df"]
    for i, (x, title, body, color, fill) in enumerate(zip(ax_stage, titles, bodies, colors, fills)):
        box(x, 4.72, aw, 1.95, title, body, color, fill, 10.5, 8.6)
        if i < 6:
            arrow((x + aw, 5.70), (ax_stage[i + 1], 5.70), BLUE)
    arrow((entry_x[-1] + 2.91, 3.48), (ax_stage[0] + 2.05, 4.72), BLUE)

    # Phase 3: Synapt roles and tools.
    band(7.48, 3.55, "PHASE 3 · SYNAPT AGENT ROLES + MCP TOOLS — ATTACHED TO THE CALLING AGENT", AMBER,
         "Logical roles share one physical client/provider path")
    syn_specs = [
        (ax_stage[1], "Historical Incident RAG Agent", "historical-incident-rag-agent\nDeclared tools:\ntrident_search · trident_query", TEAL),
        (ax_stage[3], "Threat Intel & SOP Agent", "incident-knowledge-agent\nDeclared tools:\ntrident_query · trident_get_procedures", AMBER),
        (ax_stage[6], "Judge Review Agent", "judge-review-agent\nDeclared tool:\ntrident_query", AMBER),
    ]
    for x, title, body, color in syn_specs:
        box(x, 8.02, aw, 1.42, title, body, color, "#fffaf0", 9.9, 8.2)
    arrow((ax_stage[1] + aw / 2, 6.67), (ax_stage[1] + aw / 2, 8.02), TEAL)
    arrow((ax_stage[3] + aw / 2, 6.67), (ax_stage[3] + aw / 2, 8.02), AMBER)
    arrow((ax_stage[6] + aw / 2, 6.67), (ax_stage[6] + aw / 2, 8.02), AMBER)
    client_x = ax_stage[1]
    client_w = ax_stage[6] + aw - client_x
    box(client_x, 9.77, client_w, 0.52, "Shared SynaptClient → MCP initialize → tools/list → tools/call",
        "Runtime retrieve(): trident_query preferred; trident_search fallback · provider ID injected when tool schema supports it",
        AMBER, "#fff5df", 9.9, 8.2)
    for x, _, _, color in syn_specs:
        arrow((x + aw / 2, 9.44), (x + aw / 2, 9.77), color, True)
    box(ax_stage[2], 10.53, ax_stage[5] + aw - ax_stage[2], 0.34,
        "Synapt Context Substrate · assist_cyber", "", AMBER, "#fff5df", 9.4, 8)
    arrow((client_x + client_w / 2, 10.29), (client_x + client_w / 2, 10.53), AMBER)

    # Phase 4: local dependencies.
    band(11.30, 2.12, "PHASE 4 · LOCAL DATA, MODELS, POLICY, AND STATE USED BY THE AGENTS", PURPLE)
    dep_specs = [
        (0.52, 7.35, "SQLite + FTS5", "2,313,810 flows · exact lookup\n291 summaries · BM25 keyword retrieval", TEAL),
        (8.20, 7.35, "Local ML models", "HistGradientBoosting · 65 features · 9 families\nIsolationForest · anomaly threshold · benign baseline", PURPLE),
        (15.88, 7.35, "Deterministic intelligence", "MITRE tactic map · P1–P4 policy\nInvestigation/response templates · provenance rules", BLUE),
        (23.56, 7.90, "Feedback + evidence reports", "analyst_feedback · candidate model bundle\nAnomaly, evaluation, and improvement JSON reports", ROSE),
    ]
    for x, w, title, body, color in dep_specs:
        box(x, 11.82, w, 1.15, title, body, color, "white", 10.2, 8.5)
    arrow((ax_stage[1] + aw / 2, 11.82), (ax_stage[1] + aw / 2, 6.67), TEAL, True)
    arrow((ax_stage[2] + aw / 2, 11.82), (ax_stage[2] + aw / 2, 6.67), PURPLE, True)
    arrow((ax_stage[4] + aw / 2, 11.82), (ax_stage[4] + aw / 2, 6.67), BLUE, True)

    # Phase 5: return/output continues left to right using an A-to-A row connector.
    band(13.69, 2.55, "PHASE 5 · FINAL OUTPUT FLOW — CONTINUE LEFT TO RIGHT", ROSE,
         "Connector A: Judge → backend response → frontend → analyst → feedback")
    out_x = [0.47, 6.74, 13.01, 19.28, 25.55]
    out_titles = [
        "10 · Backend mapper", "11 · Frontend results", "12 · Analyst decision",
        "13 · Feedback review", "14 · Improvement evidence",
    ]
    out_bodies = [
        "FlowInvestigationResponse\nNormalize optional fields\nReturn JSON",
        "Family · confidence · risk\nAnomaly · priority · RAG\nMITRE · guidance · verdict",
        "Verify evidence\nMonitor · escalate · dismiss\nManually approve actions",
        "Submit rating/verdict\nHuman accept/reject gate\nStore analyst correction",
        "Holdout benchmark\nCandidate artifact/report\nReviewed learning input",
    ]
    out_colors = [BLUE, BLUE, ROSE, ROSE, PURPLE]
    for i, (x, title, body, color) in enumerate(zip(out_x, out_titles, out_bodies, out_colors)):
        box(x, 14.20, 5.90, 1.50, title, body, color, "white", 10.3, 8.5)
        if i < 4:
            arrow((x + 5.90, 14.95), (out_x[i + 1], 14.95), color)
    routed_arrow([
        (ax_stage[6] + aw / 2, 6.67),
        (31.64, 7.12),
        (31.64, 13.92),
    ], AMBER)
    text(31.62, 13.64, "A", 9.6, AMBER, "bold", ha="center",
         bbox={"boxstyle": "circle,pad=0.22", "facecolor": "#fff8e9", "edgecolor": AMBER})
    text(0.29, 13.64, "A", 9.6, AMBER, "bold", ha="center",
         bbox={"boxstyle": "circle,pad=0.22", "facecolor": "#fff8e9", "edgecolor": AMBER})
    arrow((0.29, 13.99), (out_x[0] + 0.18, 14.20), AMBER)

    # Supporting frontend flows and tool chain.
    band(16.52, 2.48, "SUPPORTING FRONTEND FLOWS AND PROJECT TOOL CHAIN", TEAL)
    support = [
        (0.52, "Incident Search", "/search/incidents\nSQLite filters + FTS5\n+ Historical RAG role"),
        (6.78, "SOC Copilot Chat", "/chat\nGuardrails + flow/classifier context\n+ Knowledge role"),
        (13.04, "Status Panels", "/health + /api/synapt/agents\nSQLite/model indicators\nThree logical role statuses"),
        (19.30, "Offline Preparation", "Parquet → SQLite\nTrain classifier/anomaly\ntrident_ingest knowledge"),
        (25.56, "Core Tools", "FastAPI · Pydantic · LangGraph\nSQLite/FTS5 · scikit-learn\nSynapt MCP · DeepEval adapter"),
    ]
    for x, title, body in support:
        box(x, 17.06, 5.92, 1.42, title, body, TEAL, "#eef9f7", 10.2, 8.4)

    box(0.52, 19.28, 30.96, 0.57, "Presentation accuracy note",
        "The three Synapt names are logical UI roles. Current HistoricalIncidentRAG, knowledge, judge, and chat calls share SynaptClient.retrieve(); trident_get_procedures is displayed as a granted tool but is not directly called by the investigation workflow.",
        AMBER, "#fff8e9", 9.7, 8.4)
    text(0.52, 20.03,
         "Solid arrows: execution order · dashed arrows: dependency/tool attachment · no automated containment is executed",
         9.1, MUTED)

    for suffix in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"presentation_end_to_end_architecture.{suffix}", dpi=150, facecolor=BG)
    plt.close(fig)


HTML = rf'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CyberSentinel · Presentation architecture</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#edf2f7;color:#142b43;font-family:system-ui,sans-serif}}header{{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 22px;background:#fff;border-bottom:1px solid #d4deea;flex-wrap:wrap}}h1{{font-size:18px;margin:0 0 3px}}p{{font-size:12.5px;color:#53687b;margin:0}}.tools{{display:flex;gap:7px;align-items:center;flex-wrap:wrap}}button,a{{font:inherit;font-size:12.5px;color:#254f7b;border:1px solid #c6d5e5;background:white;padding:8px 11px;border-radius:7px;text-decoration:none;cursor:pointer}}button:hover,a:hover{{background:#eaf3ff}}button:focus-visible,a:focus-visible,#stage:focus-visible{{outline:3px solid #3478bd;outline-offset:3px}}#stage{{height:calc(100dvh - 106px);min-height:360px;overflow:hidden;position:relative;touch-action:none;cursor:grab}}#stage.drag{{cursor:grabbing}}#drawing{{position:absolute;transform-origin:0 0;will-change:transform;user-select:none}}#drawing svg{{display:block;width:{HTML_W}px;height:{HTML_H}px;pointer-events:none}}footer{{padding:7px 22px;background:white;border-top:1px solid #d4deea;font-size:12px;color:#53687b;display:flex;justify-content:space-between;gap:8px}}@media(max-width:700px){{header{{padding:10px}}h1{{font-size:15px}}#stage{{height:calc(100dvh - 165px)}}footer{{padding:7px 10px}}button,a{{padding:6px 8px}}}}</style></head><body>
<header><div><h1>CyberSentinel · User input to final output</h1><p>Frontend, backend, seven agents, aligned Synapt roles and tools, local dependencies, result, and feedback</p></div><nav class="tools"><button id="out">−</button><span id="zoom">100%</span><button id="in">+</button><button id="fit">Fit</button><a href="presentation_end_to_end_architecture.svg" download>SVG</a><a href="presentation_end_to_end_architecture.png" download>PNG</a><a href="presentation_end_to_end_architecture.pdf" download>PDF</a></nav></header>
<main id="stage" tabindex="0" aria-label="CyberSentinel presentation architecture from user input to final output"><div id="drawing">__SVG__</div></main><footer><span>Drag to pan · wheel to zoom · keyboard + / − / 0</span><span>Presentation-ready source-checked flow</span></footer>
<script>const stage=document.getElementById('stage'),drawing=document.getElementById('drawing'),zoom=document.getElementById('zoom');let scale=1,x=0,y=0,last=null;function paint(){{drawing.style.transform=`translate(${{x}}px,${{y}}px) scale(${{scale}})`;zoom.textContent=Math.round(scale*100)+'%'}}function fit(){{scale=Math.min((stage.clientWidth-28)/{HTML_W},(stage.clientHeight-28)/{HTML_H});x=(stage.clientWidth-{HTML_W}*scale)/2;y=(stage.clientHeight-{HTML_H}*scale)/2;paint()}}function mag(f,cx=stage.clientWidth/2,cy=stage.clientHeight/2){{const n=Math.min(5,Math.max(.06,scale*f));x=cx-(cx-x)*n/scale;y=cy-(cy-y)*n/scale;scale=n;paint()}}stage.addEventListener('wheel',e=>{{e.preventDefault();const r=stage.getBoundingClientRect();mag(Math.exp(-e.deltaY*.0015),e.clientX-r.left,e.clientY-r.top)}},{{passive:false}});stage.addEventListener('pointerdown',e=>{{stage.setPointerCapture(e.pointerId);last={{x:e.clientX,y:e.clientY}};stage.classList.add('drag')}});stage.addEventListener('pointermove',e=>{{if(!last)return;x+=e.clientX-last.x;y+=e.clientY-last.y;last={{x:e.clientX,y:e.clientY}};paint()}});function release(){{last=null;stage.classList.remove('drag')}}stage.addEventListener('pointerup',release);stage.addEventListener('pointercancel',release);document.getElementById('in').onclick=()=>mag(1.25);document.getElementById('out').onclick=()=>mag(.8);document.getElementById('fit').onclick=fit;stage.addEventListener('keydown',e=>{{if(['+','=','-','0'].includes(e.key)){{e.preventDefault();e.key==='0'?fit():mag(e.key==='-'?.8:1.25)}}}});new ResizeObserver(fit).observe(stage);fit();</script></body></html>'''


def main() -> None:
    render()
    svg_path = OUT / "presentation_end_to_end_architecture.svg"
    svg = svg_path.read_text(encoding="utf-8")
    svg = svg[svg.index("<svg") :]
    svg = svg.replace("<svg ", '<svg role="img" aria-label="CyberSentinel presentation architecture from user input to final output" ', 1)
    (OUT / "presentation_end_to_end_architecture.html").write_text(HTML.replace("__SVG__", svg), encoding="utf-8")
    source = (ROOT / "docs" / "PRESENTATION_END_TO_END_ARCHITECTURE.md").read_text(encoding="utf-8")
    diagrams = re.findall(r"```mermaid\n(.*?)\n```", source, re.S)
    for index, diagram in enumerate(diagrams, 1):
        (OUT / f"presentation_end_to_end_{index}.mmd").write_text(diagram + "\n", encoding="utf-8")
    for path in sorted(OUT.glob("presentation_end_to_end_architecture.*")):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
    print(f"Extracted {len(diagrams)} Mermaid diagrams")


if __name__ == "__main__":
    main()
