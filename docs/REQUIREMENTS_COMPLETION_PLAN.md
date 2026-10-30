# Requirements completion plan

**Prepared:** 12 October 2026  
**Execution prompt:** [ANTIGRAVITY_IMPLEMENTATION_PROMPT.md](ANTIGRAVITY_IMPLEMENTATION_PROMPT.md)

## Main conclusion

Complete the project by extending its existing FastAPI/SQLite/LangGraph/Synapt architecture. More UI styling or merely adding agent names will not close the retrieval, metadata, judging, anomaly, and feedback gaps. The missing parts need connected evidence contracts and observable demonstrations.

## Dependencies to resolve first

1. **Metadata-preserving data:** The local Parquet files cannot supply missing IPs, ports, or timestamps. Reingest inspected real labeled-flow data into a new versioned database; do not guess metadata or assume a positional join to old records.
2. **Semantic incident identity:** Synapt must return stable historical-summary references resolvable to SQLite. Its currently discovered search schema lacks arbitrary SQL metadata filters, so use bounded candidate retrieval plus SQL enforcement and report candidate truncation honestly.
3. **Actual judge capability:** The existing planner allows only Synapt's generative model. Prove supported model-backed rubric judging and schema-conforming DeepEval calls before promising these requirements; another provider would require an explicit architecture decision.
4. **Feedback semantics:** Live discovery showed `trident_feedback` accepts deflection-style verdicts and an existing feedback identifier, whereas the application sends an unsupported `feedback` field. Analyst attack verdicts must not be force-mapped into unrelated tool meanings; the local reviewed improvement cycle can stand independently of remote feedback sync.

## Gap-to-implementation mapping

| Gap | Implementation direction | Proof required |
|---|---|---|
| Historical incident RAG | Versioned real summaries + stable SQL record mappings + Synapt semantic retrieval | Paraphrase retrieves actual prior records with citations |
| Hybrid search | SQLite FTS5/BM25 + semantic candidates + deduplication/fusion | Ranked shared incident set; keyword/semantic/fused benchmark |
| Required metadata | New real-source ingestion, typed fields, indexes, API/UI filters | Combined attack/protocol/IP/port/time filters on real records |
| Guardrails and correctness | Central boundary policy, typed flows, proper identity/no-evidence/error behavior | Regression probes; no false sanitization or substituted record |
| DeepEval | Schema-aware supported Synapt judge adapter + fixed test corpus + saved metrics | Successful live run, separate from mock/offline tests |
| LLM-as-Judge | Model-backed rubric, typed verdict, bounded revision/abstention | Actual rejected/revised and approved evidence-backed answers |
| Multi-agent workflow | Distinct detection/analysis/risk/response/review responsibilities and contracts | Trace shows meaningful decisions, handoffs, and review routing |
| Anomaly prediction | Training-only benign baseline/detector + validated threshold | Separate anomaly score and evaluated novel/benign anomalies |
| Explainability | Model contributions + class-level feature relationships + descriptive deviations | Reproducible class/flow explanations with correct labels/units |
| Feedback improvement | Review queue → accepted corrections → candidate → protected evaluation → promotion decision | One actual versioned cycle; rejection of a worse candidate is valid |
| UI and delivery | Connect real capabilities, preserve current design, fix errors/status/accessibility | End-to-end browser flows and clean installation |

## Execution order

1. Capture baseline; test metadata, historical identity, and judge feasibility.
2. Fix record identity, invalid input, no-evidence behavior, guardrails, health, and chat context.
3. Build metadata ingestion and historical hybrid retrieval; keep independent analytics work moving if data access is blocked.
4. Establish leakage-aware classification, distinct anomaly prediction, explanations, and priority policy.
5. Connect role-based investigation, actual judging, and DeepEval evaluation.
6. Complete reviewed feedback consumption, UI integration, reproducibility, and truthful deliverables.

## Validation boundaries

The prompt defines observable gates rather than a guaranteed outcome. Real missing metadata, unsupported provider judging, or failed live evaluations cannot be fixed by wording or relabeling. The next agent must report blocked/failed requirements honestly and ask for the smallest necessary external decision while completing independent work.

Original code findings were rechecked during preparation. The UI has changes newer than the original audit and needs fresh browser validation; this plan does not assert that every earlier visual finding is still present. No new ML benchmark, live judge evaluation, or full browser retest was run in this preparation task.

Sources: [official CIC-IDS2017 description](https://www.unb.ca/cic/datasets/ids-2017.html), [DeepEval custom judge documentation](https://github.com/confident-ai/deepeval/blob/main/docs/content/guides/guides-using-custom-llms.mdx), local source/audit, and live read-only MCP tool schemas.
