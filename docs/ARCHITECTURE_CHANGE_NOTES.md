# Architecture documentation change notes

## What I did

Rebuilt the architecture documentation around the current seven-stage LangGraph workflow and added detailed end-to-end and module-wise references. The package includes a layered component view, ten numbered runtime stages, focused Mermaid diagrams, an endpoint routing map, trust boundaries, failure behavior, and a dedicated Synapt alignment diagram that maps each logical agent role to its consuming workflow module and the shared physical client/provider path.

Added a final panel-oriented architecture that begins with analyst input, frontend, backend validation, and LangGraph entry; follows all seven agents; attaches every Synapt role and declared tool to its caller; shows local databases and models; and ends with response mapping, frontend evidence, analyst decision, feedback review, and improvement evidence.

## Why this approach

The architecture is derived from executable modules and verified runtime endpoints, so the panel can trace each box to code and distinguish runtime behavior from offline preparation.

## Why not the alternative

A requirements-only target diagram would overstate incomplete behavior, while a single request sequence would omit training, evaluation, feedback, and shared storage dependencies.

## What was the issue / root cause

The previous exported image still showed six workflow stages and described anomaly detection, the judge, DeepEval, and improvement as pending even though those modules had been added. Some newly added features also contain fallback or placeholder behavior that the prior high-level Mermaid diagram did not disclose.

## Why this works best

The new diagrams present the implemented topology and step order while labeling provider degradation, dataset metadata limits, fixed-score evaluation, random RAG padding, and candidate-copy improvement behavior. The module-wise view prevents the three displayed Synapt roles from being confused with three independent Python clients: it shows their logical alignment and the actual shared `SynaptClient.retrieve()` transport.

## Other valid patterns

A deployment diagram can be added once a production host, reverse proxy, secrets store, observability stack, and scaling model exist. A separate target-state diagram is also useful for a roadmap, provided it is clearly labeled as proposed rather than implemented.
