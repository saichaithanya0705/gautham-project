"""Render the current project architecture as PNG, SVG, PDF, Mermaid, and offline HTML."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture"
INK = "#172e45"
MUTED = "#53687b"
BLUE = "#3679bf"
TEAL = "#168393"
PURPLE = "#7960af"
AMBER = "#ad7a1f"
ROSE = "#9b5c9e"
CANVAS_W = 28.0
CANVAS_H = 17.8
HTML_W = 2800
HTML_H = 1780
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(CANVAS_W, CANVAS_H))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(0, CANVAS_W)
    ax.set_ylim(CANVAS_H, 0)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def text(x, y, label, size=12, color=INK, weight="normal", **kwargs):
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
        title_size=12.5,
        body_size=10.7,
        dashed=False,
    ):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.025,rounding_size=0.11",
                linewidth=1.25,
                edgecolor=accent,
                facecolor=fill,
                linestyle=(0, (4, 3)) if dashed else "solid",
                zorder=3,
            )
        )
        text(x + 0.15, y + 0.14, title, title_size, accent, "bold")
        if body:
            text(x + 0.15, y + 0.48, body, body_size, MUTED, linespacing=1.48)

    def edge(start, end, color=BLUE, dashed=False, label=None, label_xy=None):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.45,
                color=color,
                linestyle=(0, (4, 3)) if dashed else "solid",
                zorder=2,
                connectionstyle="arc3,rad=0",
            )
        )
        if label and label_xy:
            text(
                *label_xy,
                label,
                size=9.2,
                color=color,
                bbox={"facecolor": "#f8fafc", "edgecolor": "none", "pad": 1.2},
            )

    def section_band(y, h, title, color):
        ax.add_patch(
            FancyBboxPatch(
                (0.35, y),
                27.3,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.14",
                facecolor="#f0f5fa",
                edgecolor="#d5e0ea",
                linewidth=1,
                zorder=0,
            )
        )
        text(0.7, y + 0.18, title, 11, color, "bold")

    text(0.7, 0.28, "CYBERSENTINEL COPILOT", 11.2, BLUE, "bold")
    text(0.7, 0.63, "Full project flow and implemented architecture", 25, INK, "bold")
    text(
        0.7,
        1.16,
        "CIC-IDS2017 · SQLite + FTS5 · local ML · Synapt MCP · FastAPI · LangGraph · human review",
        12.2,
        MUTED,
    )

    section_band(1.62, 3.65, "A · OFFLINE FOUNDATION AND RUNTIME ENTRY", TEAL)
    top = [0.7, 5.15, 10.1, 15.05, 20.0, 24.1]
    widths = [3.85, 4.35, 4.35, 4.35, 3.5, 3.2]
    box(
        top[0],
        2.05,
        widths[0],
        2.65,
        "CIC-IDS2017 preparation",
        "8 Parquet files · 78 source columns\nAudit, normalize, label-map\nPreserve file + row provenance\n2,313,810 flows",
        TEAL,
        "#e8f7f5",
    )
    box(
        top[1],
        2.05,
        widths[1],
        2.65,
        "SQLite evidence layer",
        "flows table · exact filters\n291 incident summaries\nFTS5 BM25 keyword index\nanalyst_feedback table",
        TEAL,
        "#e8f7f5",
    )
    box(
        top[2],
        2.05,
        widths[2],
        2.65,
        "Local prediction models",
        "65 traffic features · 9 families\nHistGradientBoosting classifier\nIsolationForest anomaly detector\nVersioned joblib bundles",
        PURPLE,
        "#f1edfa",
    )
    box(
        top[3],
        2.05,
        widths[3],
        2.65,
        "Synapt knowledge layer",
        "Curated MITRE + NIST context\nHistorical semantic retrieval\nTLS/auth/JSON-RPC adapter\nKnowledge, RAG, judge roles",
        AMBER,
        "#fff5df",
    )
    box(
        top[4],
        2.05,
        widths[4],
        2.65,
        "Analyst dashboard",
        "Investigate · search · chat\nReview evidence and limitations\nSubmit feedback\nHTML / CSS / JavaScript",
        BLUE,
        "#edf5ff",
    )
    box(
        top[5],
        2.05,
        widths[5],
        2.65,
        "FastAPI boundary",
        "Pydantic validation\nNine HTTP routes\nJSON response shaping\nShared service instances",
        BLUE,
        "#edf5ff",
    )
    edge((4.55, 3.37), (5.15, 3.37), TEAL, True)
    edge((9.5, 3.37), (10.1, 3.37), PURPLE, True)
    edge((23.5, 3.37), (24.1, 3.37), BLUE)

    section_band(5.52, 3.65, "B · POST /investigate/flow — SEVEN-STAGE LANGGRAPH CHOREOGRAPHY", BLUE)
    stage_x = [0.7, 4.6, 8.5, 12.4, 16.3, 20.2, 24.1]
    titles = [
        "1 · Guardrail",
        "2 · Flow triage",
        "3 · ML analysis",
        "4 · Knowledge",
        "5 · Priority",
        "6 · Response",
        "7 · Judge",
    ]
    bodies = [
        "Pydantic + query checks\nInjection/action patterns\nDomain relevance",
        "Record lookup / 404\nFTS5 + semantic RAG\nSelf-exclusion",
        "Family + confidence\nRisk + top deviations\nAnomaly score",
        "Sanitized Synapt query\nMITRE/NIST context\nLocal fallback",
        "Deterministic P1–P4\nFamily + risk + anomaly\nMissing context",
        "Investigation steps\nRecommendations\nProvenance + limits",
        "Hard safety gate\nFour rubric dimensions\nProvider/fallback scores",
    ]
    accents = [BLUE, TEAL, PURPLE, AMBER, BLUE, BLUE, AMBER]
    for idx, (x, title, body, accent) in enumerate(zip(stage_x, titles, bodies, accents)):
        box(x, 6.15, 3.2, 2.45, title, body, accent, "white", 11.7, 10.1)
        if idx < len(stage_x) - 1:
            edge((x + 3.2, 7.38), (stage_x[idx + 1], 7.38), BLUE)
    edge((25.7, 4.7), (25.7, 6.15), BLUE)
    edge((7.32, 4.7), (6.2, 6.15), TEAL, True, "flow + BM25", (6.0, 5.18))
    edge((12.27, 4.7), (10.1, 6.15), PURPLE, True, "model inference", (10.5, 5.18))
    edge((17.22, 4.7), (13.8, 6.15), AMBER, True, "semantic + guidance", (15.0, 5.18))

    section_band(9.42, 2.48, "C · RETURNED EVIDENCE AND HUMAN DECISION", BLUE)
    box(
        0.7,
        9.94,
        21.2,
        1.48,
        "Structured response to dashboard",
        "Attack family · confidence · intrusion risk · severity · anomaly · P1–P4 priority · feature deviations · similar incidents\nSynapt analysis · MITRE mappings · investigation steps · response drafts · judge verdict · source provenance · limitations",
        BLUE,
        "#edf5ff",
        12.4,
        10.6,
    )
    box(
        22.35,
        9.94,
        4.95,
        1.48,
        "Human analyst decision",
        "Verify evidence · approve actions\nNo automated containment",
        ROSE,
        "#f8eff9",
        12.2,
        10.5,
    )
    edge((25.7, 8.6), (20.5, 9.94), BLUE)
    edge((21.9, 10.68), (22.35, 10.68), ROSE)

    section_band(12.15, 3.25, "D · SUPPORTING API, FEEDBACK, AND EVALUATION PATHS", PURPLE)
    route_x = [0.7, 5.95, 11.2, 16.45, 21.7]
    route_titles = [
        "Search · /search/incidents",
        "Copilot · /chat",
        "Feedback lifecycle",
        "Evaluation evidence",
        "Health + agent status",
    ]
    route_bodies = [
        "Structured SQLite filters\nFTS5 BM25 + Synapt channel\nRRF-ranked incident summaries",
        "Guardrails + optional record\nClassifier context + MITRE\nSynapt or local response",
        "Submit → pending review\nHuman accept/reject gate\nHoldout + candidate report",
        "40 structured fixtures\nDeepEval adapter + JSON report\nModel/anomaly benchmarks",
        "SQLite live readiness\nModel/RAG indicators\nSynapt configuration status",
    ]
    for x, title, body in zip(route_x, route_titles, route_bodies):
        box(x, 12.75, 4.85, 2.18, title, body, PURPLE, "white", 11.6, 10.1)
    edge((25.7, 4.7), (24.1, 12.75), PURPLE, True)

    text(0.7, 15.74, "IMPLEMENTATION BOUNDARIES FOUND DURING SOURCE REVIEW", 10.7, AMBER, "bold")
    boundary_x = [0.7, 7.55, 14.4, 21.25]
    boundary_titles = ["Dataset metadata", "Retrieval", "Evaluation + judge", "Improvement + health"]
    boundary_bodies = [
        "No IPs, ports, Flow ID, or timestamps\nin this local CIC-IDS2017 export.",
        "Semantic fusion needs provider correlation;\nshort result sets use random padding.",
        "DeepEval case score is fixed locally; judge\nuses fixed defaults when provider fails.",
        "Candidate copies active model; health reports\nSynapt configuration, not a live probe.",
    ]
    for x, title, body in zip(boundary_x, boundary_titles, boundary_bodies):
        box(x, 16.12, 6.15, 1.08, title, body, AMBER, "#fff8e9", 10.9, 9.2)

    edge((0.7, 17.5), (1.35, 17.5), BLUE)
    text(1.48, 17.39, "runtime flow", 9.8, MUTED)
    edge((4.0, 17.5), (4.65, 17.5), TEAL, True)
    text(4.78, 17.39, "offline/shared dependency", 9.8, MUTED)
    text(12.2, 17.39, "Source-checked against the current workspace · generated by scripts/render_architecture.py", 9.5, MUTED)

    for suffix in ["svg", "pdf", "png"]:
        fig.savefig(OUT / f"overall_architecture.{suffix}", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


HTML = rf'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CyberSentinel · Full architecture</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf2f7;color:#172e45;font-family:system-ui,sans-serif}}
header{{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 24px;background:#fff;border-bottom:1px solid #d4deea;flex-wrap:wrap}}
h1{{font-size:19px;margin:0 0 4px}}p{{font-size:13px;color:#53687b;margin:0}}.tools{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
button,a{{font:inherit;font-size:13px;color:#254f7b;border:1px solid #c6d5e5;background:white;padding:9px 12px;border-radius:7px;text-decoration:none;cursor:pointer}}
button:hover,a:hover{{background:#eaf3ff}}button:focus-visible,a:focus-visible,#stage:focus-visible{{outline:3px solid #3679bf;outline-offset:3px}}
#stage{{height:calc(100dvh - 113px);min-height:350px;overflow:hidden;position:relative;touch-action:none;cursor:grab}}#stage.drag{{cursor:grabbing}}
#drawing{{position:absolute;transform-origin:0 0;will-change:transform;user-select:none}}#drawing svg{{display:block;width:{HTML_W}px;height:{HTML_H}px;pointer-events:none}}
footer{{padding:8px 24px;background:white;border-top:1px solid #d4deea;font-size:12px;color:#53687b;display:flex;justify-content:space-between;gap:8px}}
@media(max-width:700px){{header{{padding:12px}}h1{{font-size:16px}}#stage{{height:calc(100dvh - 170px)}}footer{{padding:8px 12px}}.tools{{gap:5px}}button,a{{padding:7px 9px}}}}
</style></head><body>
<header><div><h1>CyberSentinel · Full architecture</h1><p>Implemented data preparation, seven-stage investigation, supporting APIs, evaluation, and analyst review</p></div>
<nav class="tools" aria-label="Diagram controls"><button id="out" aria-label="Zoom out">−</button><span id="zoom" aria-live="polite">100%</span><button id="in" aria-label="Zoom in">+</button><button id="fit">Fit diagram</button><a href="overall_architecture.svg" download>SVG</a><a href="overall_architecture.png" download>PNG</a><a href="overall_architecture.pdf" download>PDF</a></nav></header>
<main id="stage" tabindex="0" aria-label="CyberSentinel full project architecture. Drag to pan; wheel or plus and minus keys to zoom; zero to fit."><div id="drawing">__SVG__</div></main>
<footer><span>Drag to pan · wheel to zoom · keyboard + / − / 0</span><span>Solid: runtime · dashed: preparation/shared dependency</span></footer>
<script>
const stage=document.getElementById('stage'),drawing=document.getElementById('drawing'),zoom=document.getElementById('zoom');
let scale=1,x=0,y=0,last=null;
function paint(){{drawing.style.transform=`translate(${{x}}px,${{y}}px) scale(${{scale}})`;zoom.textContent=Math.round(scale*100)+'%'}}
function fit(){{scale=Math.min((stage.clientWidth-28)/{HTML_W},(stage.clientHeight-28)/{HTML_H});x=(stage.clientWidth-{HTML_W}*scale)/2;y=(stage.clientHeight-{HTML_H}*scale)/2;paint()}}
function magnify(f,cx=stage.clientWidth/2,cy=stage.clientHeight/2){{const next=Math.min(4,Math.max(.08,scale*f));x=cx-(cx-x)*next/scale;y=cy-(cy-y)*next/scale;scale=next;paint()}}
stage.addEventListener('wheel',e=>{{e.preventDefault();const r=stage.getBoundingClientRect();magnify(Math.exp(-e.deltaY*.0015),e.clientX-r.left,e.clientY-r.top)}},{{passive:false}});
stage.addEventListener('pointerdown',e=>{{stage.setPointerCapture(e.pointerId);last={{x:e.clientX,y:e.clientY}};stage.classList.add('drag')}});
stage.addEventListener('pointermove',e=>{{if(!last)return;x+=e.clientX-last.x;y+=e.clientY-last.y;last={{x:e.clientX,y:e.clientY}};paint()}});
function release(){{last=null;stage.classList.remove('drag')}}stage.addEventListener('pointerup',release);stage.addEventListener('pointercancel',release);
document.getElementById('in').onclick=()=>magnify(1.25);document.getElementById('out').onclick=()=>magnify(.8);document.getElementById('fit').onclick=fit;
stage.addEventListener('keydown',e=>{{if(['+','=','-','0'].includes(e.key)){{e.preventDefault();if(e.key==='0')fit();else magnify(e.key==='-'?.8:1.25)}}}});
new ResizeObserver(fit).observe(stage);fit();
</script></body></html>'''


def main() -> None:
    render()
    svg = (OUT / "overall_architecture.svg").read_text(encoding="utf-8")
    svg = svg[svg.index("<svg") :]
    svg = svg.replace(
        "<svg ",
        '<svg role="img" aria-label="CyberSentinel full project architecture" ',
        1,
    )
    (OUT / "overall_architecture.html").write_text(
        HTML.replace("__SVG__", svg), encoding="utf-8"
    )
    source = (ROOT / "docs" / "OVERALL_ARCHITECTURE.md").read_text(encoding="utf-8")
    mermaid = re.search(r"```mermaid\n(.*?)\n```", source, re.S)
    if not mermaid:
        raise ValueError("Overall architecture document has no Mermaid source")
    (OUT / "overall_architecture.mmd").write_text(mermaid.group(1) + "\n", encoding="utf-8")
    for path in sorted(OUT.glob("overall_architecture.*")):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
