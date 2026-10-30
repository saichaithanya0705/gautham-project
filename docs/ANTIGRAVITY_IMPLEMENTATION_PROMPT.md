# Antigravity implementation prompt — complete cybersecurity assistant requirements

Copy the prompt below into Antigravity with this project folder open. This is an implementation assignment, not a request for another plan or a cosmetic redesign.

---

## Objective and workspace

Act as the lead implementation engineer for the existing AI-Powered Cybersecurity Incident Response Assistant in:

`C:\Users\SAI\Downloads\handoff_zip`

Extend the current working project until every Basic and Advanced requirement below has a real implementation, connected user/API workflow, and saved validation evidence. Work incrementally through the phases; continue beyond planning and scaffold creation. Reuse functioning components and fix root causes. If a genuine external dependency blocks a requirement, finish independent work, identify the exact blocker, and do not declare that requirement complete.

### Read first

1. Applicable `AGENTS.md` instructions and the actual current source.
2. `reports/requirements_audit/PROJECT_REQUIREMENTS_AUDIT.md` and its JSON evidence.
3. `docs/OVERALL_ARCHITECTURE.md` and `docs/synapt_connection_reference.md`.
4. `cybersecurity_synapt_master_project_planner.md` for architectural decisions and the original requirements.
5. `PROJECT_HANDOFF_CONTEXT.md`, `README_TRANSFER.md`, and `docs/implementation_status.md`, treating their conflicting status statements as historical claims to verify.

The audit reflects a reviewed snapshot; some frontend changes happened subsequently. Reinspect and rerun relevant checks before assuming an old finding remains. Preserve current UI improvements and unrelated/concurrent work. No Git repository was present during the audit: check before issuing Git commands, and do not initialize one, reset changes, commit, push, publish, or deploy by assumption.

## Architectural constraints

- Keep FastAPI, LangGraph, SQLite, and Synapt unless a specific change is necessary and explained.
- **SQLite owns exact flow evidence and metadata filtering. Synapt owns semantic/security knowledge retrieval and generative reasoning.** Do not ingest millions of raw flows into Synapt or introduce another vector database.
- Use Synapt's configured LLM as the only generative model, including judge calls where supported. Local scikit-learn models and deterministic code handle classification, anomaly scoring, validation, calculations, and policy.
- `assist_cyber` is the currently configured project provider; read local settings and rediscover tools. Never borrow credentials from example documents, print secrets, disable TLS, or assume schemas from a remembered tool count.
- Preserve the existing source dataset, original SQLite database, and model bundle. Use versioned artifacts/migrations and a rollback path; do not overwrite them to make a test pass.
- Keep flow evidence, dataset ground-truth labels, predictions, retrieved guidance, synthetic fixtures, and analyst conclusions distinct. Do not invent metadata, history, scores, citations, judge verdicts, or benchmarks.
- Model input features and query summaries for inference must not leak ground-truth labels, attack names derived from labels, filename attack labels, or record IDs into predictions. Ground-truth labels can be explicit historical filters and evaluation targets.
- No automatic firewall changes, blocking, host isolation, shell execution, or other containment actions. The product supports human analyst decisions.
- Keep the implementation small and cohesive. Extend the existing UI and services instead of creating disconnected demos or duplicate applications.

## Full requirement checklist

Maintain `docs/REQUIREMENTS_TRACEABILITY.md` with an implementation location, API/UI demonstration, test/evaluation artifact, and status for each ID:

| ID | Required capability |
|---|---|
| B1 | Historical cybersecurity incident RAG similarity search |
| B2 | Fused keyword and semantic hybrid incident search |
| B3 | Incident classification agent |
| B4 | Attack type, protocol, source/destination IP, ports, and timestamp filters |
| B5 | Evidence-backed basic investigation and response recommendations |
| B6 | Enforced input validation guardrails |
| B7 | Incident prioritization from traffic and attack characteristics |
| B8 | APIs exposing all core capabilities |
| A1 | Executable DeepEval analysis/recommendation evaluation |
| A2 | Attack-type and intrusion-risk prediction |
| A3 | Actual LLM-as-Judge validation of analysis/recommendations |
| A4 | Connected multi-agent detection, analysis, risk, and response workflow |
| A5 | Anomaly and suspicious-traffic risk prediction |
| A6 | Explainable traffic-feature relationships and prediction analysis |
| A7 | Reviewed feedback-to-improvement loop |
| A8 | Simple usable frontend |

Also deliver updated architecture, as-built design, full executable microservice/setup, and an accurate ten-minute panel presentation.

## Phase 0 — baseline and feasibility checks

Record the current configuration capabilities without secrets, dependencies, routes, data schema/counts, model metadata, relevant test results, and existing running processes. Reuse existing terminals/services where practical; never terminate user-owned processes.

Run a small capability check before committing to the retrieval/judge design:

1. Authenticate and discover current Synapt tools and their full input/output contracts.
2. Demonstrate that a bounded historical summary can retain a stable local incident/document identifier through ingestion and retrieval, so a semantic result can be resolved back to exact SQLite evidence. Use controlled development data/provider scope and avoid contaminating evaluation answers into the production knowledge corpus.
3. Verify whether a supported Synapt model-backed call can assess supplied evidence and a candidate answer with a rubric and return a schema-valid judge decision. A normal domain answer or a deterministic score labeled as an LLM judge is insufficient.
4. Confirm that the installed DeepEval version can call this judge through a custom adapter, including schema-aware synchronous/asynchronous generation. No alternate paid model provider should be silently introduced.
5. Inspect the available official metadata-preserving CIC-IDS2017 files and their actual headers, sizes, license/access, and timestamp semantics before downloading/migrating. The current local `*-no-metadata.parquet` files cannot provide the missing fields.

Read-only discovery on 12 October 2026 showed that `trident_search` supports query/node type/top_k, not arbitrary SQL metadata filters; enforce those filters in SQLite after resolving semantic incident references. The advertised `trident_feedback` contract requires `feedback_id`, `caller_type`, and `verdict` with values `deflected`, `partial`, or `not_deflected`; the existing `{feedback: "..."}` call is invalid. These look like deflection feedback semantics, not attack-verdict semantics: rediscover, understand the identifier lifecycle, and do not force-map analyst verdicts into unrelated enums.

If Synapt cannot support structured judge generation or provenance-preserving historical retrieval within the current constraint, document the reproduced failure and request the minimum necessary platform capability/architecture decision. Keep those requirements visibly blocked while continuing other work; a fallback adapter alone does not satisfy them.

## Phase 1 — correct the existing investigation contracts and guardrails

Fix these source-confirmed problems first and add regression tests:

- An explicitly requested missing `record_id` must return 404; never silently analyze a different historical match. Response target IDs and evidence provenance must agree.
- An empty investigation request must be rejected clearly; an unmatched text-only question must return a handled no-evidence answer or validated error, not HTTP 500. Knowledge-only questions may receive guidance, but numeric prediction/confidence/risk must remain unavailable when no inference ran.
- Remove fabricated 0.50 confidence/risk fallbacks. Use explicit availability/abstention fields and nullable values where appropriate.
- Replace unrestricted `flow_data` with a typed feature contract and field-specific ranges/units/finite-value checks. Reject nonnumeric features and invalid protocols/counts. Preserve legitimate source sentinel values only with a documented transformation; do not blanket-reject valid dataset conventions.
- Distinguish missing measurements from zero. Require sufficient feature coverage or abstain instead of quietly creating a usable-looking zero-filled flow.
- Enforce a central boundary policy across investigation, search, chat, retrieved text, tool arguments, and model output. Separate untrusted evidence from instructions. Reject or safely transform prohibited requests before external/model calls; do not merely label them sanitized. Regex is a supplementary detector, not the whole defense.
- Keep cybersecurity vocabulary available: legitimate discussion of SQL injection, attack strings, and incident-response procedures must remain possible. Constrain actions and instruction authority, not necessary domain analysis.
- Only allow approved read-only investigation tools; validate arguments and results. Tool failures must produce truthful degraded states. Do not construct executable SQL/shell commands from LLM output.
- Explicit record references in new chat messages must take precedence over inherited UI context, or conflicting identifiers must be resolved explicitly. Enforce history/length/role limits; client messages cannot become trusted system instructions.
- Implement truthful health/readiness with distinct configured/checked/available states and check timestamps; a configured provider is not a verified live connection. Avoid excessive health-call costs with bounded caching.

Acceptance includes missing-record identity, query-only/no-evidence behavior, malformed telemetry, protocol zero handling, stale chat context, malicious instructions in queries/retrieved material, and provider timeout/malformed-output tests. Confirm prohibited instructions do not enter a trusted downstream instruction channel and cannot trigger unauthorized tools. Do not claim perfect injection prevention from a small regex test set.

## Phase 2 — obtain real metadata and implement filtering

Use the official CIC-IDS2017 source or an inspected equivalent that retains **actual** source/destination IPs, ports, protocol, and flow timestamps. Prefer inspecting the official labeled-flow distribution; not every machine-learning CSV variant preserves all metadata. If downloading requires user interaction or access approval, report the precise file/action and continue other phases.

- Add an idempotent ingestion path for the selected CSV/Parquet schema with versioned database output, raw labels, canonical attack label/family, stable identity, row/file/hash provenance, field availability, and source checksums.
- Parse timestamps with a documented source timezone, explicit normalization, and errors for ambiguous formats. Never silently treat a timezone-less value as known UTC.
- Do not enrich the old no-metadata database by guessed row positions or ambiguous feature-fingerprint joins. Prefer reingestion from verified source rows; any join needs provable identity and ambiguity handling.
- Extend typed API/UI filters for label/family, protocol, source/destination IP, source/destination port, inclusive start and exclusive end time, and existing useful duration/provenance fields. CIDR/ranges are optional; exact IP/port/time support is required.
- Add appropriate indexes, parameterized SQL, missing-metadata semantics, valid port/IP/time checks, and combined-filter tests.
- A metadata-reduced demo may remain available with an honest capability indicator; B4 stays incomplete until real metadata-filtered records are demonstrated.

## Phase 3 — historical RAG and true hybrid ranking

Build a bounded, versioned corpus of **real historical flow/incident summaries**. Derive summaries deterministically from observed features and explicitly describe whether they represent individual flows or groups; do not imply analyst-confirmed incidents. Keep raw records in SQLite.

Each summary needs a stable incident/document ID, source dataset version, record references, actual metadata, traffic characteristics, and clear label provenance. Groups require deterministic membership and a retrievable member manifest. Do not group unrelated events just because labels or feature fingerprints match.

- Store summaries, record mappings, and an FTS5/BM25 keyword index in SQLite or a separate local SQLite application-state database; local SQLite FTS5 was verified available.
- Ingest a representative, configurable corpus into Synapt using supported contracts, retaining durable source identifiers. Include all supported families and benign examples without sending all 2.3M flows.
- Separate semantic search for historical summaries from retrieval of response playbooks/domain knowledge. Inspect actual search output, resolve entity/chunk/document references, and join back to SQL records; never use a generated prose answer as if it were a ranked incident result list.
- Retrieve keyword and semantic candidates over the **same historical corpus**, deduplicate by stable incident ID, and fuse rankings, such as reciprocal rank fusion. Expose component ranks, fused rank/score, matched records, and a concise similarity reason.
- Apply all metadata filters to the final evidence set in SQLite. Overfetch/refill semantic candidates within bounded budgets where supported, and disclose truncation/degraded coverage. Do not imply exact global filtered semantic top-k if only a truncated subset was examined.
- Keep free-text questions out of literal `LIKE full_question` predicates. Retrieval must handle paraphrases such as “repeated failed SSH login attempts” without requiring the exact label string.
- Build retrieval queries for unknown input flows from observed features and available metadata, not their ground-truth attack labels. Do not return the target flow itself as proof of a prior similar incident; exclude self/duplicate-summary membership or identify it separately.
- Generate analysis from resolved historical evidence, measured features, model results, and separately sourced domain guidance. Return stable record/chunk citations and verify every cited reference actually belongs to the provided evidence.
- When semantic retrieval fails, expose explicit keyword-only degradation; do not label it hybrid success.

Acceptance: paraphrase retrieval resolves real prior records; structured filters are respected; history is ranked rather than sorted by record ID; fusion/dedup/self-exclusion work; empty results are handled; and a saved benchmark compares keyword-only, semantic-only, and fused retrieval on held-out query wording.

## Phase 4 — defensible classification, anomaly prediction, explainability, and priority

Reuse the classifier where appropriate, but fix the evaluation boundary:

- Seed and record sampling, data versions, feature schemas, transforms, split manifests, model parameters, and artifact versions. Keep labels/filenames/IDs out of input features.
- Group repeated feature fingerprints where appropriate to avoid train/test copies. Use feature-only fingerprints for ML leakage checks; an existing fingerprint that includes labels is not sufficient to detect mislabeled feature duplicates. Report any unresolved ambiguity.
- Fit imputation/scaling/calibration, benign baselines, and explanation backgrounds on training data only. Freeze validation thresholds before final testing.
- Publish per-class precision/recall/F1/support, macro/weighted results, confusion matrix, false-positive rates, and uncertainty for rare classes. Investigate current infiltration recall 0.57 and the two-row rare-attack holdout honestly; do not demand or fabricate perfect scores.
- Add day/session-based transfer tests when metadata permits, accounting for attacks that occur on only one day. Do not describe an unseen-class temporal test as ordinary fully supported multiclass evaluation.
- Predict family and retain original attack-subtype labels for historical display/evaluation. Subtype prediction is optional if explicitly described; family grouping must remain clear.
- Implement an anomaly detector or defensible statistical anomaly model, for example an IsolationForest trained on benign training data. Save its fitted pipeline and validation-chosen threshold; evaluate abnormal benign traffic as well as malicious traffic.
- Return attack probability, classification confidence, anomaly score/flag, and operational priority as separate named quantities. An anomaly score is not automatically a calibrated probability of intrusion.
- Add genuine model-specific explanations where feasible, or another validated contribution method; pair them with class-level permutation importance/feature distributions. Keep benign deviations as descriptive comparisons, not renamed SHAP values. Verify IAT/idle/duration units and derived-feature formulas.
- Define a documented deterministic P1–P4 policy using measured attack/traffic signals and available anomaly/impact/asset context. If asset criticality is unknown, say so. Include reasons and missing-context flags; do not make every confident scan automatically P1.

Acceptance: real versioned classifier/anomaly artifacts, leakage-aware split evidence, distinct scoring fields, reproducible feature explanations, and policy tests covering benign high-volume traffic, scanning, brute force, service flooding, unknown/rare attacks, and missing context. Explainability describes model behavior/associations, not proven causation.

## Phase 5 — connected investigation agents and answer validation

Evolve the existing LangGraph into a typed, auditable workflow:

`validate → detection/triage → historical retrieval + classification → evidence analysis → risk assessment → response draft → judge/output validation → bounded revision or reviewed result`

- Give detection, analysis, risk, response, and review roles distinct objectives, evidence inputs, structured outputs, and bounded tool permissions. Deterministic ML/policy components can be tools; not every role needs an LLM call.
- Implement substantive role-specific decisions and validated handoffs, rather than merely renaming sequential functions “agents.” Evidence analysis should reconcile predictions, history, anomalies, and gaps; response should consume those conclusions; review must be able to reject unsupported claims and route to bounded revision/abstention.
- Preserve exact target/provenance across state transitions. Capture request/investigation IDs, role summaries, tool provenance, prompt/output versions, validation decisions, durations, and errors. Do not expose private chain-of-thought; log concise decision summaries, with secrets redacted and retention controls.
- Reuse the same trusted backend in chat and investigation so policy/model/evidence results do not drift between routes. A conversation can choose a different path, but must obey the same contracts.
- Validate generated output schemas and finite/range constraints; references must exist; recommendations must be supported and specific to the provided evidence. Failed validation must not be presented as a successful analysis.
- Keep external calls/revisions bounded by timeouts, concurrency/cost budgets, maximum attempts, and circuit/degraded behavior. Idempotency is required for writes; do not blindly retry non-idempotent ingestion/feedback.

### Actual LLM-as-Judge

Use a separate model-backed evaluation call/task through supported Synapt capability with the candidate answer, bounded evidence, and explicit rubric. Assess factual support, relevance, evidence/metadata consistency, calibrated uncertainty, action safety, and response appropriateness.

Return a typed verdict, dimension scores, unsupported claim/evidence references, reasons, and pass/fail. Reject critical safety violations and fabricated evidence regardless of average score. Handle malformed JSON, out-of-range scores, unsupported references, provider failures, and revision exhaustion explicitly. Same-model generation/judgment is allowed under the existing provider constraint, but disclose correlated bias and complement it with deterministic checks and analyst review. Do not claim the judge makes the system deterministic or correct.

## Phase 6 — executable DeepEval and real quality reports

- Add compatible evaluation dependencies separately from minimal runtime dependencies and a documented command for deterministic tests versus live model-backed evaluations.
- Implement a Synapt-backed custom `DeepEvalBaseLLM` adapter only after the capability check succeeds. Support the installed DeepEval contracts, including supplied Pydantic schemas, validated return values, async generation, bounded retries, and errors. A deterministic fake judge is only a labeled test double.
- Build at least 40 versioned, inspectable cases spanning supported families/benign traffic, paraphrase historical retrieval, combined filters, absent evidence, conflicting labels/predictions, rare attacks, prompt injection, unsafe requests, and provider failures. Tag cases requiring real metadata/live services. Clearly label synthetic edge-case fixtures; never mix them into claims about real benchmark accuracy.
- Use real `LLMTestCase` outputs and the exact retrieved context seen by the system. Run suitable faithfulness, answer relevancy, contextual retrieval metrics, and a cybersecurity recommendation G-Eval rubric. Add deterministic citation/filter/identity/safety checks and held-out retrieval Recall@k/MRR or nDCG where relevance judgments support them.
- Define and justify quality thresholds before evaluating; save per-case scores/reasons, failures, metric/judge versions, data/prompt/model versions, latency, and aggregate summaries. Record skipped/blocked live cases separately from passed cases; do not loosen thresholds afterward to get a green report.
- A recommended starting project gate is zero critical safety/identity/citation failures, with explicit, predeclared aggregate quality targets and disclosure of all subthreshold cases. These are project criteria, not guarantees or official DeepEval defaults.
- Keep gold answers and held-out test labels out of production retrieval and prompts. Generation context must not contain the expected answer just to improve evaluation scores.

Acceptance requires an actual successful live DeepEval run and actual judge verdicts, not just importable evaluation code or passing endpoint smoke tests. If the model capability is unavailable, leave A1/A3 blocked with an executable adapter boundary and reproduced error rather than declaring completion.

## Phase 7 — complete a reviewed continuous-improvement cycle

Store feedback against immutable investigation/record IDs, dataset/model/prompt/retrieval versions, original prediction/answer, reviewer verdict/rating/notes, and optional corrected family/label. Distinguish unreviewed suggestions from accepted corrections.

Implement the following end-to-end workflow with migrations/API or administrative commands and UI support where useful:

`submit review → review/accept or reject → create versioned improvement dataset/change → train or reindex/revise → evaluate on locked regression/holdout sets → human promotion decision → rollback-capable activation`

- At least one improvement path must actually consume accepted feedback and produce a candidate plus before/after evaluation. Merely saving ratings is incomplete; changing a dashboard counter is not an improvement.
- Feedback cases used for revision/training must remain separate from untouched final evaluation data. Repeatedly tuning against the same holdout must be disclosed and avoided with a protected test set.
- Do not auto-retrain from untrusted feedback, alter gold labels, or promote a candidate because one review was positive. A cycle that correctly rejects a worse candidate is still a functioning reviewed improvement process; do not manufacture an improvement.
- Correct remote feedback integration only if the live tool semantics support the intended event. Retain local analyst review if Synapt exposes only deflection feedback; return a truthful unsupported/not-synced state. Use a supported alternative only after schema/semantic validation.
- Persist audit linkage, status transitions, promotion/rollback decisions, and idempotency keys. Redact secrets from all logs/artifacts.

## Phase 8 — integrate the frontend, reproducibility, and deliverables

Preserve the current visual direction while connecting the completed behavior:

- Historical search with actual metadata controls, ranked similar incidents, match explanations, and evidence links.
- Investigation with distinct classifier/anomaly/priority fields, prediction availability, class-specific explanations, source citations, agent progress/trace summaries, judge verdict/revisions, limitations, and honest model/provider status.
- Chat that switches record context correctly and shares evidence/guardrail policy.
- Feedback submission and reviewed correction/status flow with clear local-save versus remote-sync indicators.
- Proper empty/loading/partial/error states; check HTTP status before rendering; never display missing predictions as zero or missing guardrails as passed. Render untrusted content safely.
- Programmatic labels, keyboard/focus support, accessible dialogs/tabs, and no page-level horizontal overflow at widths 390 and 768; also verify desktop around 1440. Recheck the current UI rather than replacing it based on the older screenshot.
- Declare direct runtime dependencies such as `scikit-learn` and `joblib`, development/evaluation dependencies, and compatible model serialization versions. Package HTML/assets explicitly. Verify fresh-environment setup using documented commands and test imported installed-package behavior, not only source-tree imports.
- Provide safe data/model/index setup commands, environment examples without secrets, optional containerization if helpful, migration/rollback procedures, and a reproducible demo. Do not silently install giant datasets/models or provision paid resources when the configuration requires a user decision.
- Update `docs/implementation_status.md`, handoff/README, the as-built design, architecture source/exports, and presentation so they match the finished code and actual measured results. Keep the earlier audit as a dated baseline and add a new verification report instead of rewriting history.
- Produce a ten-minute presentation/slides outline plus demo script answering all three professional questions: similar historical incidents, attack-associated traffic features, and investigation priority. Include actual result screenshots, evidence traceability, evaluation results, and remaining limitations.

## Final acceptance demonstration and completion report

Run and record, rather than merely describe:

1. Fresh install/start; UI and `/health` in healthy and disconnected states.
2. Ranked semantic + keyword historical incident search for held-out paraphrases, with real record citations and combined IP/port/protocol/time filters.
3. Known flow investigation; missing record; invalid telemetry; query-only/empty-evidence handling; target/provenance consistency.
4. Attack prediction and separately evaluated anomaly prediction with real explanations and reasoned P1–P4 priority.
5. Detection, analysis, risk, response, and review handoffs, including an output rejected/revised by a real judge and a safe result when review cannot complete.
6. A live DeepEval report and deterministic safety/identity/filter/citation regression results; distinguish offline doubles, live results, skipped tests, and failures.
7. Feedback submission → reviewed correction → candidate revision → before/after evaluation → recorded promotion/rejection/rollback decision.
8. Browser interactions for search, investigation, chat record switching, evidence, and feedback on desktop/mobile, including provider failure and HTTP error states.

Maintain an evidence checklist throughout. Finish with a B1–B8/A1–A8 matrix linking implementation files, commands, artifacts, and actual statuses; summarize changes, root causes, decisions, validation, and limitations. Every “met” must have an observable connected demonstration. A test that only checks field existence, a mock response, a renamed node, or a new status document is insufficient proof.

Proceed with implementation now; do not stop after producing a plan or skeleton. Continue useful independent work if blocked. Ask only for missing data/access or an architecture decision that cannot be resolved within the existing authorization, and state exactly why it is needed. Do not declare all requirements met if any data, live judge, evaluation, or integration gate remains unresolved.

---

## Reference notes for this prompt

- [Official CIC-IDS2017 source](https://www.unb.ca/cic/datasets/ids-2017.html): labeled-flow and machine-learning distributions differ; inspect the chosen files for metadata preservation.
- [DeepEval custom LLM documentation](https://github.com/confident-ai/deepeval/blob/main/docs/content/guides/guides-using-custom-llms.mdx): custom judges need schema-aware generation contracts; use the version actually installed.
- Preparation on 12 October 2026 included source reinspection, read-only live Synapt schema discovery, a local FTS5 capability check, and current documentation checks. No feature fixes, data migration, training, knowledge ingestion, remote feedback submission, or deployment were performed while preparing this prompt.

## Change transparency

### What I did

Created this implementation prompt and an accompanying completion plan; application code, credentials, datasets, model artifacts, and external provider content were unchanged.

### Why this approach

An ordered implementation assignment with traceability, capability checks, and concrete demonstrations makes the intended completion testable by the next agent.

### Why not the alternative

A generic “finish everything” prompt invites cosmetic status changes, disconnected features, fabricated metadata, and mock-only verification.

### What was the issue / root cause

Several requirements lack distinct evidence/data/model contracts, while earlier completion claims treated a running demo and smoke tests as proof of full coverage.

### Why this works best

The phases fix correctness first, resolve real data/provider dependencies early, then connect retrieval, prediction, review, feedback, UI, and measured delivery.

### Other valid patterns

Synapt-supported retrieval/judging implementations can vary, and anomaly/explanation methods may differ; the same provenance, validation, scoring separation, and live acceptance evidence remain necessary.
