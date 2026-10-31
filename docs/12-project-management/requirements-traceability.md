# Requirements traceability

| Field | Value |
|---|---|
| Purpose | Links from each requirement to module, test and status |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Functional requirements](../01-requirements/functional-requirements.md), [Acceptance test cases](../09-testing/acceptance-test-cases.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Components, entities and APIs per requirement are listed in each module document. Status uses: Implemented and verified, Implemented verification incomplete, Partially implemented, Not implemented, Not verified, Blocked, Not applicable.

| Requirement | Module | Test | Status |
|---|---|---|---|
| FR-CHAT-001 | [agents-and-memory](../03-functional-modules/agents-and-memory.md) | AT-7.2 | Not implemented |
| FR-CHAT-002 | [agents-and-memory](../03-functional-modules/agents-and-memory.md) | AT-6.1 | Not implemented |
| FR-CHAT-003 | [agents-and-memory](../03-functional-modules/agents-and-memory.md) | AT-7.5 | Not implemented |
| FR-ING-001 | [ingestion](../03-functional-modules/ingestion.md) | AT-3.2 | Not implemented |
| FR-ING-002 | [ingestion](../03-functional-modules/ingestion.md) | AT-3.1 | Not implemented |
| FR-ING-003 | [ingestion](../03-functional-modules/ingestion.md) | AT-3.3 | Not implemented |
| FR-ING-004 | [ingestion](../03-functional-modules/ingestion.md) | AT-3.4 | Not implemented |
| FR-ING-005 | [ingestion](../03-functional-modules/ingestion.md) | AT-3.5 | Not implemented |
| FR-ING-006 | [ingestion](../03-functional-modules/ingestion.md) | AT-3.2 | Not implemented |
| FR-VIS-001 | [visual-content](../03-functional-modules/visual-content.md) | AT-4.1 | Not implemented |
| FR-RET-001 | [retrieval](../03-functional-modules/retrieval.md) | AT-5.1 | Not implemented |
| FR-RET-002 | [retrieval](../03-functional-modules/retrieval.md) | AT-5.2, AT-5.3 | Not implemented |
| FR-RET-003 | [retrieval](../03-functional-modules/retrieval.md) | AT-5.3 | Not implemented |
| FR-RET-004 | [retrieval](../03-functional-modules/retrieval.md) | AT-5.4 | Not implemented |
| FR-QA-001 | [grounded-answers](../03-functional-modules/grounded-answers.md) | AT-6.1 | Not implemented |
| FR-QA-002 | [grounded-answers](../03-functional-modules/grounded-answers.md) | AT-6.2 | Not implemented |
| FR-QA-003 | [grounded-answers](../03-functional-modules/grounded-answers.md) | AT-6.3 | Not implemented |
| FR-QA-004 | [grounded-answers](../03-functional-modules/grounded-answers.md) | AT-6.4 | Not implemented |
| FR-QA-005 | [grounded-answers](../03-functional-modules/grounded-answers.md) | AT-6.5 | Not implemented |
| FR-QA-006 | [grounded-answers](../03-functional-modules/grounded-answers.md) | AT-7.2 | Not implemented |
| FR-AGT-001 | [agents-and-memory](../03-functional-modules/agents-and-memory.md) | AT-7.1 | Not implemented |
| FR-AGT-002 | [agents-and-memory](../03-functional-modules/agents-and-memory.md) | AT-7.3 | Not implemented |
| FR-AGT-003 | [agents-and-memory](../03-functional-modules/agents-and-memory.md) | AT-7.4 | Not implemented |
| FR-WEB-001 | [web-search](../03-functional-modules/web-search.md) | AT-8.1 | Not implemented |
| FR-WEB-002 | [web-search](../03-functional-modules/web-search.md) | AT-8.2 | Not implemented |
| FR-WEB-003 | [web-search](../03-functional-modules/web-search.md) | AT-8.3 | Not implemented |
| FR-SUM-001 | [summaries](../03-functional-modules/summaries.md) | AT-9.1 | Not implemented |
| FR-SUM-002 | [summaries](../03-functional-modules/summaries.md) | AT-9.2 | Not implemented |
| FR-KG-001 | [knowledge-graph](../03-functional-modules/knowledge-graph.md) | AT-9A.1 | Not implemented |
| FR-KG-002 | [knowledge-graph](../03-functional-modules/knowledge-graph.md) | AT-9A.2 | Not implemented |
| FR-KG-003 | [knowledge-graph](../03-functional-modules/knowledge-graph.md) | AT-9A.3 | Not implemented |
| FR-KG-004 | [knowledge-graph](../03-functional-modules/knowledge-graph.md) | AT-9A.4 | Not implemented |
| FR-NB-001 | [notebooks](../03-functional-modules/notebooks.md) | AT-9B.1 | Not implemented |
| FR-NB-002 | [notebooks](../03-functional-modules/notebooks.md) | AT-9B.2 | Not implemented |
| FR-NB-003 | [notebooks](../03-functional-modules/notebooks.md) | AT-9B.3 | Not implemented |
| FR-EXT-001 | [extraction](../03-functional-modules/extraction.md) | AT-10.1 | Not implemented |
| FR-EXT-002 | [extraction](../03-functional-modules/extraction.md) | AT-10.2 | Not implemented |
| FR-EXT-003 | [extraction](../03-functional-modules/extraction.md) | AT-10.3 | Not implemented |
| FR-EXT-004 | [extraction](../03-functional-modules/extraction.md) | AT-10.4 | Not implemented |
| FR-CALC-001 | [calculations](../03-functional-modules/calculations.md) | AT-11.1 | Not implemented |
| FR-CALC-002 | [calculations](../03-functional-modules/calculations.md) | AT-11.2 | Not implemented |
| FR-CALC-003 | [calculations](../03-functional-modules/calculations.md) | AT-11.3 | Not implemented |
| FR-AUD-001 | [audio](../03-functional-modules/audio.md) | AT-14.2 | Not implemented |
| FR-API-001 | [api-ui-mcp](../03-functional-modules/api-ui-mcp.md) | AT-1.6 | Not implemented |
| FR-API-002 | [api-ui-mcp](../03-functional-modules/api-ui-mcp.md) | AT-13.1 | Not implemented |
| FR-UI-001 | [api-ui-mcp](../03-functional-modules/api-ui-mcp.md) | AT-13.2 | Not implemented |
| FR-MCP-001 | [api-ui-mcp](../03-functional-modules/api-ui-mcp.md) | AT-13.3 | Not implemented |
| FR-FBK-001 | [api-ui-mcp](../03-functional-modules/api-ui-mcp.md) | AT-13.4 | Not implemented |
| FR-OPS-001 | [delivery-and-operations](../03-functional-modules/delivery-and-operations.md) | AT-1.7 | Not implemented |
| FR-OPS-002 | [delivery-and-operations](../03-functional-modules/delivery-and-operations.md) | AT-1.8 | Not implemented |
| FR-OPS-003 | [delivery-and-operations](../03-functional-modules/delivery-and-operations.md) | AT-1.9 | Not implemented |
| FR-OPS-004 | [delivery-and-operations](../03-functional-modules/delivery-and-operations.md) | AT-0.6 | Not implemented |
| FR-OPS-005 | [delivery-and-operations](../03-functional-modules/delivery-and-operations.md) | AT-13.4 | Not implemented |
| FR-EVAL-001 | [evaluation](../03-functional-modules/evaluation.md) | AT-2.3 | Not implemented |
| FR-EVAL-002 | [evaluation](../03-functional-modules/evaluation.md) | AT-2.4 | Not implemented |
| FR-EVAL-003 | [evaluation](../03-functional-modules/evaluation.md) | AT-2.5 | Not implemented |
| FR-ADM-001 | [api-ui-mcp](../03-functional-modules/api-ui-mcp.md) | AT-12.4 | Not implemented |

## Owner requirements R1 to R33 (WORK_PLAN.md section 3, word for word)

| # | Requirement | Where it is covered | Status |
|---|---|---|---|
| R1 | Advanced, professional chat prototype (not basic): multi-turn chat with memory, streaming answers, file upload and a chat list | Whole plan, phases 3 to 14 | Planned |
| R2 | Agents, RAG, LLMs and every needed model and tool | Sections 8 and 9, phases 3 to 14 | Planned |
| R3 | Any supported file type: PDF (digital and scanned), images, Word, PowerPoint, Excel, CSV, HTML, Markdown, text. Audio later | 3.2, 14.x | Planned |
| R4 | Questions over files with page citations and as little hallucination as possible | Phase 6 | Planned |
| R5 | Online information (web search) | Phase 8 | Planned |
| R6 | Summaries, reviews, extraction, calculations and plots, compare documents | Phases 7, 9, 10, 11 | Planned |
| R7 | Zero cost for development, hosting, deployment and API. No paid tiers. No trials treated as free | Sections 5 and 7, rule Z | Planned |
| R8 | Free open-weight Hugging Face models | Section 9 | Planned |
| R9 | Private documents never leave the Mac | Sections 5 and 6, steps 8.4, 12.x | Planned |
| R10 | Real public datasets. No synthetic data unless you agree | 2.1, 9.3 | Planned |
| R11 | Every technology has a real purpose | Section 9 (why column) | Planned |
| R12 | Project on the external 2 TB SSD | Section 6.3 | Planned |
| R13 | Backup in Google Drive, continue from Drive or Colab when the SSD is missing, sync back without conflicts | Section 6.4, step 0.6 | Planned |
| R14 | Use both MacBook Air M2 (16 GB) and Google Colab, chosen per task | Section 6.2 | Planned |
| R15 | Do not limit the design because of the MacBook. Use free cloud GPU when needed | Sections 6.1 and 6.2 | Planned |
| R16 | Push to GitHub after every step | Rule G | Planned |
| R17 | Live website that updates automatically after every push, before and after the API exists | Section 11, steps 1.7, 1.8 | Planned |
| R18 | API at the best stage, without rework | Step 1.6 (API-first), Phase 13 hardening | Planned |
| R19 | CI/CD and MLOps where they have a purpose | Phase 1 | Planned |
| R20 | MLflow for experiments, traces and versioning | 1.2, 1.3 | Planned |
| R21 | Testing, monitoring, documentation, version control, data management, security | 1.4, 1.9, 13.4, 16.2, section 6, Phase 12 | Planned |
| R22 | Future company use (on-prem, audit trail, versioned releases) | Phase 15 | Planned |
| R23 | A self-contained handover | Sections 1 and 15 | Planned |
| R24 | Easy English, step by step, why for each step | Rule C1 | Planned |
| R25 | Coding rules (flat modules, file creation by the coding assistant after approval, hashes, full commands, Git one per line, expected output, human style, no comma before and/or/but) | Section 5.2 | Planned |
| R26 | One phase at a time with checks and permission. Done/not-done table after each phase. What to do next after each step | Rule P | Planned |
| R27 | Copy-pasteable plan and a .docx copy | This file and WORK_PLAN.docx | Done (this file) |
| R28 | Repo owned by a GitHub organization from the start | Step 0.1, step 1.1 | Planned |
| R29 | GraphRAG: answers that follow relationships between entities across documents | Phase 9A | Planned |
| R30 | Ontology: a defined, versioned set of entity and relation types | Step 9A.1 | Planned |
| R31 | Knowledge base: collections, knowledge graph and saved notes together (interpretation, see Q11) | Phases 9A, 9B | Planned |
| R32 | Notebooks (workspaces on one topic): sources, chat, notes, study guide, FAQ, briefing, flashcards, quiz, mind map | Phase 9B | Planned |
| R33 | Verification loop: code, commands and expected output with a 12-character verification number per Python code file, checked locally with uv | Rules C12, C13, step 0.1 | Planned |
