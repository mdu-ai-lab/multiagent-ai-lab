# Project scope

| Field | Value |
|---|---|
| Purpose | In-scope and out-of-scope features for version 1 |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Project overview](../00-project-overview/project-overview.md), [Functional requirements](../01-requirements/functional-requirements.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

## In scope for v1

| Area | Included | Phase |
|---|---|---|
| Chat | General chat, streaming, memory, follow-up questions | 6, 7 |
| Files | PDF (digital and scanned), images, Word, PowerPoint, Excel, CSV, HTML, Markdown, text | 3 |
| Visual content | Charts, figures and tables described by a vision model | 4 |
| Search | Hybrid search with reranking and filters | 5 |
| Answers | Citations, claim check, refusal, evidence highlight, small-file mode | 6 |
| Agents | Router, compare, hard-question loop, limits and fallbacks | 7 |
| Web | Opt-in web search with URL citations | 8 |
| Summaries | Long documents and reviews | 9 |
| Knowledge graph | Ontology (LinkML), graph extraction, GraphRAG route | 9A |
| Notebooks | Notebooks (workspaces on one topic), notes, study outputs, mind map | 9B |
| Extraction | Schema-locked JSON with verify and refine | 10 |
| Calculations | Sandboxed pandas code and plots | 11 |
| Security | Injection defences, personal data masking, access per collection, limits | 12 |
| API, UI, MCP | Versioned API from Phase 1, hardened in Phase 13. Gradio UI. MCP tools | 1, 13 |
| Audio | Speech-to-text with time-range citations | 14 |
| Company package | Docker images, GPU server profile, Postgres option, deployment guide | 15 |
| Delivery | CI, live dashboard, live demo, health checks, backup | 0, 1 |

## Out of scope for v1 (non-goals)

| Item | Reason | Source |
|---|---|---|
| Fine-tuning | Needs labelled or synthetic data | D15 |
| Image generation, text-to-speech | No purpose for a document assistant | WORK_PLAN.md section 2 |
| Audio and video overviews (spoken or video summaries of sources) | Need text-to-speech or video generation. Open question Q10 | D19 |
| Multi-machine scaling, SSO | Beyond a prototype | WORK_PLAN.md section 2 |
| Paid hosting or paid tiers | Zero-cost rule | Rule Z |
| Support for every possible file type | Only the listed types | Step 3.2 |

## Project summary (WORK_PLAN.md section 2, word for word)

| Item | Detail |
|---|---|
| Goal | A chat and document question-answering assistant that runs locally. Specialised agents and RAG work together so one platform can chat, answer questions over any supported file with page citations, search the web on request, summarise, extract JSON, calculate and plot from tables, and later transcribe audio |
| Users | The MDU university group first. Designed so companies that avoid cloud AI (for example Volvo) could run it inside their own network later |
| Why | The 4 MDU research works showed useful ideas but none released a usable public pipeline, API or frontend |
| Sources | Billah thesis (DVA504), Billah et al. journal article (Array), Chakravorty thesis (SAF-RAG), Wahab thesis (DVA429). Ideas are reused only where useful and cited as [Paper, Sec, page] |
| v1 scope | Chat, document Q&A, compare documents, web search (opt-in), summaries (long documents and reviews), extraction, calculations and plots, knowledge graph with ontology and GraphRAG, notebooks (workspaces on one topic) and study tools, audio (late phase), API, web UI, MCP, live dashboard, live demo |
| Non-goals in v1 | Fine-tuning, image generation, text-to-speech (including audio overviews (spoken summaries of sources), see Q10), video overviews, multi-machine scaling, SSO, paid hosting |
| Honesty rule | Never claim production-ready, real-time, automated or accurate unless implemented and verified. No system can promise zero hallucination. We reduce and measure it |
