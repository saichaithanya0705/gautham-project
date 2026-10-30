"""Render the detailed, numbered CyberSentinel architecture and flow."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture"
INK = "#142b43"
MUTED = "#53687b"
BLUE = "#3478bd"
TEAL = "#168393"
PURPLE = "#795fac"
AMBER = "#ad791e"
ROSE = "#9a579b"
BG = "#f8fafc"
WIDTH = 30.0
HEIGHT = 26.2
HTML_W = 3000
HTML_H = 2620
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})


def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(WIDTH, HEIGHT))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(HEIGHT, 0)
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)

    def label(x, y, value, size=11, color=INK, weight="normal", **kwargs):
        return ax.text(
            x,
            y,
            value,
            fontsize=size,
            color=color,
            weight=weight,
            va="top",
            zorder=5,
            **kwargs,
        )

    def card(x, y, w, h, title, body="", accent=BLUE, fill="white", ts=11.4, bs=9.5):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.025,rounding_size=0.10",
                linewidth=1.2,
                edgecolor=accent,
                facecolor=fill,
                zorder=3,
            )
        )
        label(x + 0.14, y + 0.12, title, ts, accent, "bold")
        if body:
            label(x + 0.14, y + 0.43, body, bs, MUTED, linespacing=1.35)

    def arrow(start, end, color=BLUE, dashed=False):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.4,
                color=color,
                linestyle=(0, (4, 3)) if dashed else "solid",
                zorder=2,
            )
        )

    label(0.7, 0.30, "CYBERSENTINEL COPILOT", 11.3, BLUE, "bold")
    label(0.7, 0.67, "Detailed architecture and numbered end-to-end flow", 25, INK, "bold")
    label(
        0.7,
        1.22,
        "Each stage shows ownership, processing, dependencies, output, and the next transition",
        12,
        MUTED,
    )

    # Column headings.
    headings = [
        (0.7, "STEP / OWNER", BLUE),
        (5.0, "PROCESSING AND DECISIONS", BLUE),
        (15.5, "DATA / MODEL / EXTERNAL DEPENDENCIES", PURPLE),
        (23.0, "OUTPUT AND NEXT STATE", TEAL),
    ]
    for x, title, color in headings:
        label(x, 1.82, title, 10.3, color, "bold")

    rows = [
        {
            "step": "0 · Offline foundation",
            "owner": "Preparation scripts",
            "process": "Audit and normalize CIC-IDS2017\nMap labels to nine attack families\nSeed 291 incident summaries and FTS5\nTrain classifier and benign-only anomaly model",
            "deps": "8 Parquet files · 78 columns\nSQLite · scikit-learn · joblib\nCurated MITRE/NIST documents",
            "output": "2,313,810 SQLite flows\n65-feature classifier bundle\nIsolationForest bundle\nSynapt knowledge corpus",
            "color": TEAL,
            "fill": "#e8f7f5",
        },
        {
            "step": "1 · Analyst + API entry",
            "owner": "Dashboard / FastAPI",
            "process": "Collect record ID, query, family, protocol, or raw flow\nValidate types, bounds, length, and non-empty request\nDispatch POST /investigate/flow",
            "deps": "index.html\nFlowInvestigationRequest\nFastAPI route wiring",
            "output": "Validated request\nHTTP 422 on contract failure\nLangGraph initial state",
            "color": BLUE,
            "fill": "#edf5ff",
        },
        {
            "step": "2 · Guardrail",
            "owner": "guardrail_agent",
            "process": "Detect prompt injection and destructive instructions\nBlock unauthorized automated containment\nCheck cybersecurity relevance for query-only requests",
            "deps": "Guardrail regex policy\nDomain relevance patterns\nNo external side effects",
            "output": "guardrail_status: passed/rejected\nViolation reason when blocked\nSanitized path to triage",
            "color": BLUE,
            "fill": "#edf5ff",
        },
        {
            "step": "3 · Flow triage + RAG",
            "owner": "flow_triage_agent",
            "process": "Load exact record or validate raw telemetry\nEnforce real 404 for missing explicit record\nRun BM25 and semantic channels; RRF, filter, self-exclude",
            "deps": "SQLite flows · FTS5 summaries\nHistoricalIncidentRAG\nSynapt semantic retrieval",
            "output": "target_flow or unassessed state\nsimilar_flows\ntarget_not_found flag",
            "color": TEAL,
            "fill": "#e8f7f5",
        },
        {
            "step": "4 · ML analysis",
            "owner": "ml_analysis_agent",
            "process": "Extract 65 traffic features\nPredict family, confidence, risk = 1 − P(benign), severity\nCalculate top five deviations and anomaly score",
            "deps": "HistGradientBoostingClassifier\nBenign feature baseline\nIsolationForest + threshold",
            "output": "ml_prediction\nanomaly_prediction\nMITRE tactic mapping",
            "color": PURPLE,
            "fill": "#f1edfa",
        },
        {
            "step": "5 · Knowledge retrieval",
            "owner": "synapt_knowledge_agent",
            "process": "Keep rejected text outside provider boundary\nSanitize analyst context and ask a family-specific question\nRetrieve procedures, ATT&CK indicators, verification steps",
            "deps": "SynaptClient · TLS/auth/JSON-RPC\nMITRE/NIST corpus\nDeterministic local fallback",
            "output": "synapt_evidence\nsynapt_analysis\nGraceful disconnected status",
            "color": AMBER,
            "fill": "#fff5df",
        },
        {
            "step": "6 · Risk prioritization",
            "owner": "prioritization_agent",
            "process": "Combine family, risk, anomaly, and known context\nApply explicit P1–P4 attack-family policy\nRecord unknown asset and host identity context",
            "deps": "determine_incident_priority\nClassification + anomaly outputs\nOptional asset criticality",
            "output": "priority_level and code\nPolicy rationale\nmissing_context list",
            "color": BLUE,
            "fill": "#edf5ff",
        },
        {
            "step": "7 · Response synthesis",
            "owner": "response_recommendation_agent",
            "process": "Assemble investigation sequence and response drafts\nAttach record/model/provider provenance\nDisclose dataset, metadata, and automation limits",
            "deps": "Prediction · priority · similar incidents\nSynapt analysis · MITRE mappings\nNIST-aligned static response template",
            "output": "investigation_steps\nrecommended_response\nsource_provenance + limitations",
            "color": BLUE,
            "fill": "#edf5ff",
        },
        {
            "step": "8 · Output validation",
            "owner": "judge_review_agent",
            "process": "Reject prohibited automatic-action language first\nScore grounding, action safety, NIST alignment, relevance\nParse model JSON when provider-backed judge is available",
            "deps": "ResponseJudge\nSynaptDeepEvalLLM adapter\nFixed rubric fallback",
            "output": "pass_verdict\ncomposite + dimension scores\ncritique + unsupported claims",
            "color": AMBER,
            "fill": "#fff5df",
        },
        {
            "step": "9 · Present + improve",
            "owner": "Dashboard / analyst",
            "process": "Render the complete evidence package\nHuman verifies findings and approves any response\nSubmit rating, verdict, notes, optional corrected family",
            "deps": "FlowInvestigationResponse\nanalyst_feedback table\nHuman review gate",
            "output": "Analyst decision\nPending feedback record\nAccepted/rejected improvement input",
            "color": ROSE,
            "fill": "#f8eff9",
        },
    ]

    y0 = 2.18
    row_h = 1.82
    gap = 0.16
    xs = [0.7, 5.0, 15.5, 23.0]
    ws = [3.9, 10.05, 7.05, 6.3]
    for idx, row in enumerate(rows):
        y = y0 + idx * (row_h + gap)
        card(xs[0], y, ws[0], row_h, row["step"], row["owner"], row["color"], row["fill"], 11.1, 9.5)
        card(xs[1], y, ws[1], row_h, "Processing", row["process"], row["color"], "white", 10.6, 9.25)
        card(xs[2], y, ws[2], row_h, "Dependencies", row["deps"], row["color"], "white", 10.6, 9.25)
        card(xs[3], y, ws[3], row_h, "Output", row["output"], row["color"], "white", 10.6, 9.25)
        arrow((4.6, y + row_h / 2), (5.0, y + row_h / 2), row["color"])
        arrow((15.05, y + row_h / 2), (15.5, y + row_h / 2), row["color"], True)
        arrow((22.55, y + row_h / 2), (23.0, y + row_h / 2), row["color"])
        if idx < len(rows) - 1:
            next_y = y0 + (idx + 1) * (row_h + gap)
            arrow((26.15, y + row_h), (26.15, next_y), BLUE)

    support_y = y0 + len(rows) * (row_h + gap) + 0.18
    label(0.7, support_y, "SUPPORTING PATHS THAT SHARE THE SAME DATA, MODELS, AND PROVIDER", 10.5, PURPLE, "bold")
    cards = [
        (0.7, "Incident search", "Structured SQL + FTS5 BM25\n+ Synapt semantic channel + RRF"),
        (7.95, "Conversational copilot", "Guardrails + optional flow context\n+ classifier + MITRE + Synapt/local reply"),
        (15.2, "Feedback and improvement", "Submit → human review → holdout\n+ candidate artifact + benchmark report"),
        (22.45, "Evaluation evidence", "40 fixtures + provider adapter\n+ local safety gate + JSON reports"),
    ]
    for x, title, body in cards:
        card(x, support_y + 0.42, 6.85, 1.45, title, body, PURPLE, "#f5f1fb", 11, 9.4)

    bottom_y = support_y + 2.13
    label(0.7, bottom_y, "SOURCE-REVIEWED BOUNDARIES", 10.5, AMBER, "bold")
    boundaries = [
        (0.7, "Metadata", "Local export lacks IP, port, Flow ID, timestamp fields."),
        (7.95, "Retrieval", "Sparse fused sets are padded with random corpus records."),
        (15.2, "Evaluation / judge", "Benchmark score and offline judge fallback use fixed defaults."),
        (22.45, "Improvement / health", "Candidate copies active model; Synapt health is config-based."),
    ]
    for x, title, body in boundaries:
        card(x, bottom_y + 0.40, 6.85, 1.05, title, body, AMBER, "#fff8e9", 10.6, 8.9)

    label(0.7, HEIGHT - 0.32, "Solid arrows: runtime transition · dashed arrows: dependency input · all response actions require human approval", 9.3, MUTED)

    for suffix in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"detailed_architecture_flow.{suffix}", dpi=150, facecolor=BG)
    plt.close(fig)


HTML = rf'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CyberSentinel · Detailed architecture and flow</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf2f7;color:#142b43;font-family:system-ui,sans-serif}}
header{{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 22px;background:#fff;border-bottom:1px solid #d4deea;flex-wrap:wrap}}
h1{{font-size:18px;margin:0 0 3px}}p{{font-size:12.5px;color:#53687b;margin:0}}.tools{{display:flex;gap:7px;align-items:center;flex-wrap:wrap}}
button,a{{font:inherit;font-size:12.5px;color:#254f7b;border:1px solid #c6d5e5;background:white;padding:8px 11px;border-radius:7px;text-decoration:none;cursor:pointer}}
button:hover,a:hover{{background:#eaf3ff}}button:focus-visible,a:focus-visible,#stage:focus-visible{{outline:3px solid #3478bd;outline-offset:3px}}
#stage{{height:calc(100dvh - 106px);min-height:360px;overflow:hidden;position:relative;touch-action:none;cursor:grab}}#stage.drag{{cursor:grabbing}}
#drawing{{position:absolute;transform-origin:0 0;will-change:transform;user-select:none}}#drawing svg{{display:block;width:{HTML_W}px;height:{HTML_H}px;pointer-events:none}}
footer{{padding:7px 22px;background:white;border-top:1px solid #d4deea;font-size:12px;color:#53687b;display:flex;justify-content:space-between;gap:8px}}
@media(max-width:700px){{header{{padding:10px}}h1{{font-size:15px}}#stage{{height:calc(100dvh - 165px)}}footer{{padding:7px 10px}}button,a{{padding:6px 8px}}}}
</style></head><body>
<header><div><h1>CyberSentinel · Detailed architecture and numbered flow</h1><p>Inputs, processing, dependencies, outputs, branches, and supporting paths</p></div>
<nav class="tools" aria-label="Diagram controls"><button id="out" aria-label="Zoom out">−</button><span id="zoom" aria-live="polite">100%</span><button id="in" aria-label="Zoom in">+</button><button id="fit">Fit</button><a href="detailed_architecture_flow.svg" download>SVG</a><a href="detailed_architecture_flow.png" download>PNG</a><a href="detailed_architecture_flow.pdf" download>PDF</a></nav></header>
<main id="stage" tabindex="0" aria-label="Detailed CyberSentinel architecture. Drag to pan, use wheel or plus and minus to zoom, and zero to fit."><div id="drawing">__SVG__</div></main>
<footer><span>Drag to pan · wheel to zoom · keyboard + / − / 0</span><span>Source checked against the current implementation</span></footer>
<script>
const stage=document.getElementById('stage'),drawing=document.getElementById('drawing'),zoom=document.getElementById('zoom');let scale=1,x=0,y=0,last=null;
function paint(){{drawing.style.transform=`translate(${{x}}px,${{y}}px) scale(${{scale}})`;zoom.textContent=Math.round(scale*100)+'%'}}
function fit(){{scale=Math.min((stage.clientWidth-28)/{HTML_W},(stage.clientHeight-28)/{HTML_H});x=(stage.clientWidth-{HTML_W}*scale)/2;y=(stage.clientHeight-{HTML_H}*scale)/2;paint()}}
function mag(f,cx=stage.clientWidth/2,cy=stage.clientHeight/2){{const n=Math.min(5,Math.max(.06,scale*f));x=cx-(cx-x)*n/scale;y=cy-(cy-y)*n/scale;scale=n;paint()}}
stage.addEventListener('wheel',e=>{{e.preventDefault();const r=stage.getBoundingClientRect();mag(Math.exp(-e.deltaY*.0015),e.clientX-r.left,e.clientY-r.top)}},{{passive:false}});
stage.addEventListener('pointerdown',e=>{{stage.setPointerCapture(e.pointerId);last={{x:e.clientX,y:e.clientY}};stage.classList.add('drag')}});stage.addEventListener('pointermove',e=>{{if(!last)return;x+=e.clientX-last.x;y+=e.clientY-last.y;last={{x:e.clientX,y:e.clientY}};paint()}});function release(){{last=null;stage.classList.remove('drag')}}stage.addEventListener('pointerup',release);stage.addEventListener('pointercancel',release);
document.getElementById('in').onclick=()=>mag(1.25);document.getElementById('out').onclick=()=>mag(.8);document.getElementById('fit').onclick=fit;stage.addEventListener('keydown',e=>{{if(['+','=','-','0'].includes(e.key)){{e.preventDefault();e.key==='0'?fit():mag(e.key==='-'?.8:1.25)}}}});new ResizeObserver(fit).observe(stage);fit();
</script></body></html>'''


def main() -> None:
    render()
    svg_path = OUT / "detailed_architecture_flow.svg"
    svg = svg_path.read_text(encoding="utf-8")
    svg = svg[svg.index("<svg") :]
    svg = svg.replace("<svg ", '<svg role="img" aria-label="Detailed CyberSentinel architecture and numbered flow" ', 1)
    (OUT / "detailed_architecture_flow.html").write_text(HTML.replace("__SVG__", svg), encoding="utf-8")

    source = (ROOT / "docs" / "DETAILED_ARCHITECTURE_AND_FLOW.md").read_text(encoding="utf-8")
    diagrams = re.findall(r"```mermaid\n(.*?)\n```", source, re.S)
    for index, diagram in enumerate(diagrams, 1):
        (OUT / f"detailed_flow_{index}.mmd").write_text(diagram + "\n", encoding="utf-8")

    for path in sorted(OUT.glob("detailed_architecture_flow.*")):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
    print(f"Extracted {len(diagrams)} Mermaid diagrams")


if __name__ == "__main__":
    main()
