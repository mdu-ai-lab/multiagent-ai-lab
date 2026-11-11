# Non-functional requirements

| Field | Value |
|---|---|
| Purpose | Quality, security, cost and portability requirements with unique IDs |
| Status | Proposed |
| Last updated | 2026-11-09 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [SRS](../01-requirements/srs.md), [Security requirements](../07-security/security-requirements.md), [Performance testing](../09-testing/performance-testing.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

Numbers come from the done-when tests in WORK_PLAN.md v1.10. They are starting targets and may be calibrated against measured baselines in Phase 2, with the change recorded.

| ID | Requirement | Source | Status |
|---|---|---|---|
| NFR-COST-001 | Zero cost for development, hosting, deployment and API use. No new payment methods or paid plans for this project. The owner's existing 2 TB Google Drive is used as it is | Rule Z, section 7 | Not implemented |
| NFR-PRIV-001 | Private documents never leave the Mac | Rule V | Not implemented |
| NFR-PERF-001 | Peak RAM below 13 GB with main, embedding and reranker models loaded on the Mac | 0.4 | Implemented and verified (11,839 MB peak GPU memory increase, step 0.4) |
| NFR-PERF-002 | Search p50 at or below 2 s on the Mac | 5.5 | Not implemented |
| NFR-PERF-003 | Answer latency and load behaviour are measured and reported. Target values: REQUIRES CONFIRMATION | 13.4, 15.4 | Not implemented |
| NFR-QUAL-001 | 100% valid citations. Unsupported claims at or below 10% | 6.3 | Not implemented |
| NFR-QUAL-002 | Refusal F1 at or above 0.70 on QASPER test | 6.4 | Not implemented |
| NFR-QUAL-003 | Routing at or above 90% correct | 7.1 | Not implemented |
| NFR-QUAL-004 | 100% valid JSON on CORD test | 10.2 | Not implemented |
| NFR-QUAL-005 | Summary coverage above top-k RAG with non-overlapping CI. FSCR at or above 0.80 | 9.3 | Not implemented |
| NFR-QUAL-006 | Study outputs: 100% valid citations and unsupported claims at or below 10% | 9B.2, 9B.4 | Not implemented |
| NFR-QUAL-007 | Graph route kept only where it beats hybrid RAG on 2WikiMultihopQA and MuSiQue | 9A.5 | Not implemented |
| NFR-PERF-004 | Graph extraction time and model calls per document are recorded | 9A.2, 9A.5 | Not implemented |
| NFR-REL-001 | Jobs survive crashes and notebook disconnects | 3.1, 1.5 | Not implemented |
| NFR-REL-002 | No runaway agent loops. Every fallback logged | 7.4 | Not implemented |
| NFR-SEC-001 | File and web text never act as instructions or trigger tools | 7.6, 12.1 | Not implemented |
| NFR-SEC-002 | Code runs only in a sandbox without network and with resource limits | 11.2 | Not implemented |
| NFR-SEC-003 | Zero cross-user access leaks | 12.4 | Not implemented |
| NFR-SEC-004 | Input limits: 50 MB per file, 1,000 pages, type checked by content, question length, request rate | 12.4 | Not implemented |
| NFR-SEC-005 | Secrets never in Git or Google Drive | Section 6.4 | Partially implemented (.env ignored by Git, login token files left out of the backup. Notebook secrets in step 1.5) |
| NFR-SEC-006 | Personal data masked in traces, logs, MLflow and exports | 12.3 | Not implemented |
| NFR-SEC-007 | Dependency and secret scanning on every push | 1.4 | Implemented (pip-audit on the three lock files in CI. Three setuptools advisories that cannot affect the vLLM environment are accepted for its lock only, with the reasons in ci.yml. A unit test fails once the lock has the setuptools that fixes one of them, so that exception must then be removed. GitHub's secret scanning with push protection, Dependabot alerts and security updates. Push protection not tested with a real secret) |
| NFR-REPRO-001 | Models, datasets and packages pinned by version or hash | 1.3 | Partially implemented (models, packages and the Qdrant image pinned. Datasets from 2.1) |
| NFR-REPRO-002 | Running the same evaluation twice gives identical numbers | 2.3 | Not implemented |
| NFR-REPRO-003 | Every result traces to its code, prompt, model and data versions | 1.3 | Partially implemented (code, configs, prompts and models traced and checked by ops/check_result.py. Data from 2.1) |
| NFR-PORT-001 | Same code runs in Mac, GPU, demo, CI and company profiles by config | 0.1, 0.5 | Partially implemented (mac and demo profiles only) |
| NFR-PORT-002 | Database switches from SQLite to PostgreSQL by config | 15.3 | Not implemented |
| NFR-OBS-001 | Every agent step and model call is traced with time and tokens. Each request also records its totals: tokens in and out, model calls, tool calls, time and the fallback used | 1.2, 7.2 | Partially implemented (model calls and request totals are traced. LangGraph steps from 7.2) |
| NFR-MAINT-001 | Flat modules (one package for the agent harness, D43), CI checks and an updated plan after every step | Rules C2, G | Not implemented |
| NFR-MAINT-002 | Local output and verification numbers match the expected output for every step | Rules C12, C13 | Not implemented |
| NFR-LEGAL-001 | Licences of models, datasets and tools checked before use | 2.1, 5.2, 5.4 | Not implemented |
| NFR-HON-001 | No claim of production-ready, real-time, automated or accurate without verification | Rule N | Not implemented |
