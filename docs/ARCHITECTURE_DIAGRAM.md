# CyberSentinel architecture diagram

The complete, source-checked current architecture is in [OVERALL_ARCHITECTURE.md](OVERALL_ARCHITECTURE.md).

- [Interactive overall flow: zoom and pan](architecture/overall_architecture.html)
- [PNG image](architecture/overall_architecture.png)
- [SVG vector diagram](architecture/overall_architecture.svg)
- [PDF for the panel presentation](architecture/overall_architecture.pdf)
- [Editable Mermaid source](architecture/overall_architecture.mmd)

The overall view includes dataset ingestion, model preparation, curated knowledge ingestion, API routing, the six-stage LangGraph investigation, search/chat/feedback/health flows, returned results, and human analyst review.

This replaces the earlier simplified sketch and corrects its guardrail description; the current investigation guardrail flags matched patterns rather than sanitizing or blocking them.

See [change notes](ARCHITECTURE_CHANGE_NOTES.md) for the approach and validation scope.
