# Functional requirements

| Field | Value |
|---|---|
| Purpose | Every planned functional requirement with a unique ID |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [SRS](../01-requirements/srs.md), [Traceability](../12-project-management/requirements-traceability.md), [Modules](../03-functional-modules/README.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

All requirements come from WORK_PLAN.md v1.7. They are proposed until the group supervisor confirms them. "Plan step" points to the step that builds and tests the requirement.

| ID | Requirement | Plan step | Status |
|---|---|---|---|
| FR-CHAT-001 | Chat without files. Answers are labelled "no sources" | 7.2 | Not implemented |
| FR-CHAT-002 | Answers stream word by word | 6.1 | Not implemented |
| FR-CHAT-003 | Chat memory per thread. Follow-up questions are rewritten into full questions. Long chats get a running summary | 7.5 | Not implemented |
| FR-ING-001 | Upload PDF, Word, PowerPoint, Excel, CSV, HTML, Markdown, text and image files | 3.2 | Not implemented |
| FR-ING-002 | Background jobs with status queued, parsing, indexing, done or failed with reason. A crashed job restarts | 3.1 | Not implemented |
| FR-ING-003 | OCR for scanned pages with an engine chosen by character error rate | 3.3 | Not implemented |
| FR-ING-004 | Store each element with file ID, version, page, heading path, position box, type and text. Render page images | 3.4 | Not implemented |
| FR-ING-005 | Detect duplicates and new versions by sha256. Delete removes everything from a file | 3.5 | Not implemented |
| FR-ING-006 | Reject unsupported file types with a clear message | 3.2 | Not implemented |
| FR-VIS-001 | Describe charts, figures and tables with a vision model. Link each description to its page and box. Mark it model-generated | 4.1 | Not implemented |
| FR-RET-001 | Split documents by section into chunks that keep heading path, parent and neighbours. Tables stay whole | 5.1 | Not implemented |
| FR-RET-002 | Hybrid search: meaning, BM25, keyword and page-image search merged with RRF | 5.2, 5.3 | Not implemented |
| FR-RET-003 | Always filter search by allowed collections, latest version and chosen files | 5.3 | Not implemented |
| FR-RET-004 | Rerank results and add a structure score. Keep the best 6 to 8 | 5.4 | Not implemented |
| FR-QA-001 | Answer only from numbered sources and cite every claim with file and page | 6.1 | Not implemented |
| FR-QA-002 | Small-file mode: give the whole file to the model when it fits | 6.2 | Not implemented |
| FR-QA-003 | Validate citations and check each sentence against its source | 6.3 | Not implemented |
| FR-QA-004 | Refuse with "I could not find this in your files" when evidence is missing | 6.4 | Not implemented |
| FR-QA-005 | Return page and box coordinates for each citation | 6.5 | Not implemented |
| FR-QA-006 | Compare two or more documents side by side | 7.2 | Not implemented |
| FR-AGT-001 | Route each request through rules, then the helper model, then the main model or a question to the user | 7.1 | Not implemented |
| FR-AGT-002 | Run the Planner, Navigator and Reviewer loop only for hard questions, max 3 rounds | 7.3 | Not implemented |
| FR-AGT-003 | Enforce request limits and fallback paths | 7.4 | Not implemented |
| FR-WEB-001 | Web search only when the user turns it on. Send only the rewritten question | 8.1 | Not implemented |
| FR-WEB-002 | Read and clean fetched pages. Do not store them in collections | 8.2 | Not implemented |
| FR-WEB-003 | Cite web sources as [W#] with URL and apply the claim check | 8.3 | Not implemented |
| FR-SUM-001 | Summarise long documents section by section with citations. Short, medium or detailed length | 9.1 | Not implemented |
| FR-SUM-002 | Summarise reviews with a pandas statistics block and review-ID citations | 9.2 | Not implemented |
| FR-KG-001 | Define entity and relation types in a versioned LinkML ontology that generates Pydantic models and OWL | 9A.1 | Not implemented |
| FR-KG-002 | Extract entities and relations per collection into the ontology schema. Every fact keeps its source chunk, file and page | 9A.2 | Not implemented |
| FR-KG-003 | Graph engine (LightRAG or own ontology-guided graph) chosen by test and set in config | 9A.3 | Not implemented |
| FR-KG-004 | Graph route for local and whole-corpus questions with page citations, claim check, refusal and the collection filter | 9A.4 | Not implemented |
| FR-NB-001 | Notebooks with chosen sources, chats and saved notes with citations | 9B.1 | Not implemented |
| FR-NB-002 | Study outputs with citations: briefing, study guide with glossary, FAQ, timeline, flashcards, quiz | 9B.2 | Not implemented |
| FR-NB-003 | Mind map from section structure and the knowledge graph. Every node links to a source page | 9B.3 | Not implemented |
| FR-EXT-001 | Keep extraction schemas as versioned Pydantic models | 10.1 | Not implemented |
| FR-EXT-002 | Extract schema-locked JSON with few-shot examples | 10.2 | Not implemented |
| FR-EXT-003 | Verify and refine extraction (max 2 retries), then ask the user to review | 10.3 | Not implemented |
| FR-EXT-004 | Export to JSON, CSV or Excel. Batch extraction | 10.4 | Not implemented |
| FR-CALC-001 | Find relevant tables and load them into pandas with cleaned values | 11.1 | Not implemented |
| FR-CALC-002 | Run model-written pandas code in a locked sandbox | 11.2 | Not implemented |
| FR-CALC-003 | Show plots in the chat with code and source table cited | 11.3 | Not implemented |
| FR-AUD-001 | Transcribe audio with timestamps. Citations point to time ranges | 14.2 | Not implemented |
| FR-API-001 | Versioned API under /v1, experimental until Phase 13 | 1.6 | Not implemented |
| FR-API-002 | Login, rate limits, clear errors and a frozen /v1 contract | 13.1 | Not implemented |
| FR-UI-001 | Web UI with chat list, streaming chat, file upload, web toggle, source panel with highlight, extraction view, export, notebook view and mind map and graph view | 13.2 | Not implemented |
| FR-MCP-001 | Offer search, ask and extract as MCP tools behind a login token | 13.3 | Not implemented |
| FR-FBK-001 | Thumbs up or down with optional comment on every answer, saved to its trace | 13.4 | Not implemented |
| FR-OPS-001 | Live dashboard on GitHub Pages rebuilt after CI passes on main | 1.7 | Not implemented |
| FR-OPS-002 | Live demo on a ZeroGPU Space redeployed after CI passes on main | 1.8 | Not implemented |
| FR-OPS-003 | Weekly health check that opens a GitHub issue on failure | 1.9 | Not implemented |
| FR-OPS-004 | One-way backup to Google Drive, inbox import and restore test | 0.6 | Not implemented |
| FR-OPS-005 | Local monitoring view of latency, errors, fallbacks and low-rated answers | 13.4 | Not implemented |
| FR-EVAL-001 | Evaluation harness with metrics per route, logged to MLflow | 2.3 | Not implemented |
| FR-EVAL-002 | Closed-book baselines per profile | 2.4 | Not implemented |
| FR-EVAL-003 | Judge model with a frozen scoring guide and a human check | 2.5 | Not implemented |
| FR-ADM-001 | Users and collections stored in the database. Each user sees only their collections. How collections are created and shared: REQUIRES CONFIRMATION | 12.4 | Not implemented |
