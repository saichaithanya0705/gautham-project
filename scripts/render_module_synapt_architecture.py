"""Render the module-wise CyberSentinel architecture with aligned Synapt roles."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture"
W, H = 34.0, 23.7
HTML_W, HTML_H = 3400, 2370
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

    def band(y, h, title, color):
        ax.add_patch(FancyBboxPatch(
            (0.25, y), 33.5, h, boxstyle="round,pad=0.02,rounding_size=0.13",
            facecolor="#f0f5fa", edgecolor="#d5e0ea", linewidth=1, zorder=0))
        text(0.55, y + 0.15, title, 10.6, color, "bold")

    def box(x, y, w, h, title, body="", accent=BLUE, fill="white", ts=11, bs=9.3):
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

    text(0.55, 0.26, "CYBERSENTINEL COPILOT", 11.2, BLUE, "bold")
    text(0.55, 0.62, "Module-wise architecture with aligned Synapt agent flow", 25, INK, "bold")
    text(0.55, 1.16,
         "Runtime order on top · owning Python modules below · Synapt roles aligned to their consuming stages",
         12, MUTED)

    # Main ordered flow.
    band(1.57, 3.25, "A · PRIMARY INVESTIGATION FLOW — MODULE ORDER", BLUE)
    sx = [0.45 + 3.71 * i for i in range(9)]
    sw = 3.34
    stage_titles = [
        "1 · API entry", "2 · Guardrail", "3 · Flow triage", "4 · ML analysis",
        "5 · Knowledge", "6 · Priority", "7 · Response", "8 · Judge", "9 · UI + analyst",
    ]
    stage_bodies = [
        "Validate contract\nCreate graph state\nDispatch request",
        "Injection/action check\nDomain relevance\nPass or reject",
        "Load exact flow / 404\nHybrid incident RAG\nSelf-exclusion",
        "Classify + risk\nFeature deviations\nAnomaly + MITRE",
        "Sanitize context\nRetrieve procedures\nProvider fallback",
        "Apply P1–P4 policy\nRationale\nMissing context",
        "Build steps/actions\nProvenance\nLimitations",
        "Hard safety gate\nFour-part rubric\nCritique/verdict",
        "Render evidence\nHuman decision\nSubmit feedback",
    ]
    stage_colors = [BLUE, BLUE, TEAL, PURPLE, AMBER, BLUE, BLUE, AMBER, ROSE]
    stage_fills = ["#edf5ff", "#edf5ff", "#e8f7f5", "#f1edfa", "#fff5df",
                   "#edf5ff", "#edf5ff", "#fff5df", "#f8eff9"]
    for i, (x, title, body, color, fill) in enumerate(
        zip(sx, stage_titles, stage_bodies, stage_colors, stage_fills)
    ):
        box(x, 2.05, sw, 2.25, title, body, color, fill, 10.9, 9.1)
        if i < 8:
            arrow((x + sw, 3.18), (sx[i + 1], 3.18), BLUE)

    # Owning module alignment.
    band(5.08, 2.55, "B · OWNING PYTHON MODULES — ONE COLUMN PER RUNTIME STAGE", TEAL)
    module_bodies = [
        "main.py\nschemas.py", "guardrails.py", "sqlite_store.py\nrag/historical_rag.py",
        "ml/predictor.py\nml/anomaly.py", "workflow.py\nsynapt/client.py", "policy.py",
        "workflow.py\nresponse builder", "judge/evaluator.py\nevaluation adapter",
        "ui/index.html\nfeedback/improvement.py",
    ]
    for i, (x, body, color) in enumerate(zip(sx, module_bodies, stage_colors)):
        box(x, 5.62, sw, 1.48, "Module owner", body, color, "white", 10.2, 8.9)
        arrow((x + sw / 2, 4.30), (x + sw / 2, 5.62), color, True)

    # Synapt roles and physical runtime.
    band(7.90, 4.72, "C · SYNAPT AGENT ALIGNMENT AND PHYSICAL PROVIDER FLOW", AMBER)
    role_specs = [
        (sx[2], "Historical Incident RAG Agent", "historical-incident-rag-agent\nSimilarity over 291 summaries\nDeclared: search + query", TEAL),
        (sx[4], "Threat Intel / SOP Agent", "incident-knowledge-agent\nNIST · MITRE · procedures\nDeclared: query + procedures", AMBER),
        (sx[7], "Judge Review Agent", "judge-review-agent\nSafety + grounding rubric\nDeclared: query", AMBER),
    ]
    for x, title, body, color in role_specs:
        box(x, 8.48, sw, 1.62, title, body, color, "#fffaf0", 10.2, 8.7)
    arrow((sx[2] + sw / 2, 7.10), (sx[2] + sw / 2, 8.48), TEAL)
    arrow((sx[4] + sw / 2, 7.10), (sx[4] + sw / 2, 8.48), AMBER)
    arrow((sx[7] + sw / 2, 7.10), (sx[7] + sw / 2, 8.48), AMBER)

    client_x, client_w = sx[2], (sx[7] + sw) - sx[2]
    box(client_x, 10.55, client_w, 0.84, "Shared SynaptClient runtime",
        "TLS/authentication → MCP initialize → tools/list → tools/call · retrieve() prefers trident_query and falls back to trident_search",
        AMBER, "#fff5df", 10.7, 8.8)
    for x, _, _, color in role_specs:
        arrow((x + sw / 2, 10.10), (x + sw / 2, 10.55), color, True)
    box(sx[3], 11.72, (sx[6] + sw) - sx[3], 0.53,
        "Synapt Context Substrate · provider assist_cyber",
        "Shared knowledge, semantic retrieval, and judge response boundary",
        AMBER, "#fff5df", 10.4, 8.4)
    arrow((client_x + client_w / 2, 11.39),
          (client_x + client_w / 2, 11.72), AMBER)
    text(0.55, 12.33,
         "Alignment rule: the three names are logical dashboard roles; current code does not choose a separate credential/client per role.",
         9.4, AMBER, "bold")

    # Data and model modules.
    band(12.90, 2.60, "D · DATA, MODEL, POLICY, AND STATE MODULES", PURPLE)
    data_specs = [
        (0.55, 6.2, "SQLite evidence", "2,313,810 flows\nExact lookup + structured filters\nSource-file/row provenance", TEAL),
        (7.15, 6.2, "Historical retrieval state", "291 incident summaries\nFTS5 BM25 index\nRRF-ranked response", TEAL),
        (13.75, 6.2, "Local ML artifacts", "65-feature classifier · 9 families\nIsolationForest + threshold\nBenign feature baseline", PURPLE),
        (20.35, 6.2, "Policy and mappings", "P1–P4 deterministic rules\nMITRE technique map\nStatic response template", BLUE),
        (26.95, 6.2, "Feedback and reports", "analyst_feedback\nCandidate model bundle\nBenchmark/evaluation JSON", ROSE),
    ]
    for x, w, title, body, color in data_specs:
        box(x, 13.45, w, 1.55, title, body, color, "white", 10.6, 8.9)
    arrow((sx[2] + sw / 2, 13.45), (sx[2] + sw / 2, 7.10), TEAL, True)
    arrow((sx[3] + sw / 2, 13.45), (sx[3] + sw / 2, 7.10), PURPLE, True)
    arrow((sx[5] + sw / 2, 13.45), (sx[5] + sw / 2, 7.10), BLUE, True)
    arrow((sx[8] + sw / 2, 13.45), (sx[8] + sw / 2, 7.10), ROSE, True)

    # Supporting route modules.
    band(15.78, 3.12, "E · SUPPORTING ENDPOINT MODULE FLOWS", PURPLE)
    support_specs = [
        (0.55, "Search module", "POST /search/incidents\nStore filters + HistoricalIncidentRAG\n→ historical role → shared client"),
        (7.15, "Chat module", "POST /chat\nGuardrails + store + predictor\n→ knowledge role → shared client"),
        (13.75, "Feedback module", "POST /feedback and /review\nSQLite human-review lifecycle\nOptional direct trident_feedback"),
        (20.35, "Improvement module", "POST /feedback/improve\nAccepted feedback + 2,000-row holdout\nCandidate bundle + report"),
        (26.95, "Status module", "GET /health + /api/synapt/agents\nSQLite readiness + model indicators\nLogical agent configuration status"),
    ]
    for x, title, body in support_specs:
        box(x, 16.34, 6.2, 2.05, title, body, PURPLE, "#f5f1fb", 10.8, 9.0)

    # Offline lifecycle.
    band(19.18, 2.74, "F · OFFLINE PREPARATION, EVALUATION, AND IMPROVEMENT", TEAL)
    offline_specs = [
        (0.55, "Dataset ingestion", "Parquet audit → normalize labels/features\n→ SQLite flows + indexes", TEAL),
        (7.15, "Model training", "SQLite sample → 65 features\n→ classifier + anomaly bundles", PURPLE),
        (13.75, "Knowledge ingestion", "MITRE/NIST/schema/summaries\n→ trident_ingest → Synapt", AMBER),
        (20.35, "Quality evaluation", "40 fixtures + adapter + safety gate\n→ DeepEval-labelled JSON report", PURPLE),
        (26.95, "Feedback benchmark", "Reviewed corrections + active model\n→ candidate and decision report", ROSE),
    ]
    for x, title, body, color in offline_specs:
        box(x, 19.75, 6.2, 1.68, title, body, color, "white", 10.6, 8.9)

    box(0.55, 22.25, 32.6, 0.90, "Implementation boundary",
        "Synapt roles are aligned by purpose in the UI and architecture. Physically, HistoricalIncidentRAG, knowledge retrieval, judge evaluation, and chat all call the same SynaptClient.retrieve() path; per-agent routing is not implemented in the Python runtime.",
        AMBER, "#fff8e9", 10.6, 9.0)
    text(0.55, 23.47,
         "Solid arrows: runtime order · dashed arrows: module/data dependency · containment remains a human decision",
         9.2, MUTED)

    for suffix in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"module_wise_synapt_architecture.{suffix}", dpi=150, facecolor=BG)
    plt.close(fig)


HTML = rf'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CyberSentinel · Module-wise Synapt architecture</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf2f7;color:#142b43;font-family:system-ui,sans-serif}}header{{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 22px;background:#fff;border-bottom:1px solid #d4deea;flex-wrap:wrap}}h1{{font-size:18px;margin:0 0 3px}}p{{font-size:12.5px;color:#53687b;margin:0}}.tools{{display:flex;gap:7px;align-items:center;flex-wrap:wrap}}button,a{{font:inherit;font-size:12.5px;color:#254f7b;border:1px solid #c6d5e5;background:white;padding:8px 11px;border-radius:7px;text-decoration:none;cursor:pointer}}button:hover,a:hover{{background:#eaf3ff}}button:focus-visible,a:focus-visible,#stage:focus-visible{{outline:3px solid #3478bd;outline-offset:3px}}#stage{{height:calc(100dvh - 106px);min-height:360px;overflow:hidden;position:relative;touch-action:none;cursor:grab}}#stage.drag{{cursor:grabbing}}#drawing{{position:absolute;transform-origin:0 0;will-change:transform;user-select:none}}#drawing svg{{display:block;width:{HTML_W}px;height:{HTML_H}px;pointer-events:none}}footer{{padding:7px 22px;background:white;border-top:1px solid #d4deea;font-size:12px;color:#53687b;display:flex;justify-content:space-between;gap:8px}}@media(max-width:700px){{header{{padding:10px}}h1{{font-size:15px}}#stage{{height:calc(100dvh - 165px)}}footer{{padding:7px 10px}}button,a{{padding:6px 8px}}}}
</style></head><body>
<header><div><h1>CyberSentinel · Module-wise architecture with Synapt agent flow</h1><p>Runtime order, module ownership, logical Synapt roles, shared provider path, data, endpoints, and offline lifecycle</p></div><nav class="tools"><button id="out">−</button><span id="zoom">100%</span><button id="in">+</button><button id="fit">Fit</button><a href="module_wise_synapt_architecture.svg" download>SVG</a><a href="module_wise_synapt_architecture.png" download>PNG</a><a href="module_wise_synapt_architecture.pdf" download>PDF</a></nav></header>
<main id="stage" tabindex="0" aria-label="Module-wise CyberSentinel architecture with aligned Synapt agent roles"><div id="drawing">__SVG__</div></main><footer><span>Drag to pan · wheel to zoom · keyboard + / − / 0</span><span>Logical agent roles and physical shared-client flow are shown separately</span></footer>
<script>const stage=document.getElementById('stage'),drawing=document.getElementById('drawing'),zoom=document.getElementById('zoom');let scale=1,x=0,y=0,last=null;function paint(){{drawing.style.transform=`translate(${{x}}px,${{y}}px) scale(${{scale}})`;zoom.textContent=Math.round(scale*100)+'%'}}function fit(){{scale=Math.min((stage.clientWidth-28)/{HTML_W},(stage.clientHeight-28)/{HTML_H});x=(stage.clientWidth-{HTML_W}*scale)/2;y=(stage.clientHeight-{HTML_H}*scale)/2;paint()}}function mag(f,cx=stage.clientWidth/2,cy=stage.clientHeight/2){{const n=Math.min(5,Math.max(.06,scale*f));x=cx-(cx-x)*n/scale;y=cy-(cy-y)*n/scale;scale=n;paint()}}stage.addEventListener('wheel',e=>{{e.preventDefault();const r=stage.getBoundingClientRect();mag(Math.exp(-e.deltaY*.0015),e.clientX-r.left,e.clientY-r.top)}},{{passive:false}});stage.addEventListener('pointerdown',e=>{{stage.setPointerCapture(e.pointerId);last={{x:e.clientX,y:e.clientY}};stage.classList.add('drag')}});stage.addEventListener('pointermove',e=>{{if(!last)return;x+=e.clientX-last.x;y+=e.clientY-last.y;last={{x:e.clientX,y:e.clientY}};paint()}});function release(){{last=null;stage.classList.remove('drag')}}stage.addEventListener('pointerup',release);stage.addEventListener('pointercancel',release);document.getElementById('in').onclick=()=>mag(1.25);document.getElementById('out').onclick=()=>mag(.8);document.getElementById('fit').onclick=fit;stage.addEventListener('keydown',e=>{{if(['+','=','-','0'].includes(e.key)){{e.preventDefault();e.key==='0'?fit():mag(e.key==='-'?.8:1.25)}}}});new ResizeObserver(fit).observe(stage);fit();</script></body></html>'''


def main() -> None:
    render()
    svg_path = OUT / "module_wise_synapt_architecture.svg"
    svg = svg_path.read_text(encoding="utf-8")
    svg = svg[svg.index("<svg") :]
    svg = svg.replace("<svg ", '<svg role="img" aria-label="Module-wise CyberSentinel architecture with aligned Synapt agents" ', 1)
    (OUT / "module_wise_synapt_architecture.html").write_text(
        HTML.replace("__SVG__", svg), encoding="utf-8")
    source = (ROOT / "docs" / "MODULE_WISE_SYNAPT_ARCHITECTURE.md").read_text(encoding="utf-8")
    diagrams = re.findall(r"```mermaid\n(.*?)\n```", source, re.S)
    for index, diagram in enumerate(diagrams, 1):
        (OUT / f"module_wise_synapt_{index}.mmd").write_text(diagram + "\n", encoding="utf-8")
    for path in sorted(OUT.glob("module_wise_synapt_architecture.*")):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
    print(f"Extracted {len(diagrams)} Mermaid diagrams")


if __name__ == "__main__":
    main()
