# Test plan

| Field | Value |
|---|---|
| Purpose | Tests per phase |
| Status | Proposed |
| Last updated | 2026-11-20 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Acceptance test cases](../09-testing/acceptance-test-cases.md), [Testing status](../09-testing/testing-status.md) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

Each step in WORK_PLAN.md has a done-when test. These are the acceptance tests. Each phase also adds unit tests for its modules and keeps CI green.

| Phase | Main tests | Datasets |
|---|---|---|
| 0 | Model calls, RAM, backup restore | — |
| 1 | CI fail test, API endpoints, streamed chat through the harness and its import test, live site update, health check | — |
| 2 | Rerun identical, judge agreement | LongDocURL, QASPER, TAT-DQA, CORD, GovReport, SPACE, 2WikiMultihopQA, MuSiQue, speech set |
| 3 | Parse each type, resume, OCR error rate, versions | CORD, sample files |
| 4 | Figure descriptions help retrieval | LongDocURL |
| 5 | Ablation, filters, latency | LongDocURL, QASPER |
| 6 | Citations, claim check, refusal | QASPER |
| 7 | Routing, loops, fallbacks, memory, tool access, tool calls, the harness import test and the part-by-part ablation | Mixed test set, BFCL |
| 8 | Toggle, leak test | — |
| 9 | Coverage vs top-k RAG | GovReport, SPACE |
| 9A | Ontology generation, extraction precision, engine comparison, filter, hybrid vs GraphRAG | 2WikiMultihopQA, MuSiQue |
| 9B | Notebook lifecycle, citation and claim check of study outputs, hand-check | 5 public documents |
| 10 | JSON validity, field accuracy | CORD |
| 11 | Sandbox escape, math accuracy | TAT-DQA |
| 12 | Injection, personal data, access, limits | Public injection set |
| 13 | API, UI, MCP, end-to-end | — |
| 14 | Word error rate, time-range citation | Speech set |
| 15 | Images, Postgres, load | — |
| 16 | Fresh install, group test | — |

## Datasets (WORK_PLAN.md section 13, word for word)

| Dataset | Route | Licence (as checked so far) | Why |
|---|---|---|---|
| LongDocURL | Q&A, retrieval, visual | Apache 2.0 (Hugging Face card, checked 20 November 2026) | Long multimodal PDFs with evidence pages. Used by Chakravorty |
| QASPER | Q&A, refusal | CC BY 4.0 (Hugging Face card, checked 20 November 2026) | Evidence paragraphs plus unanswerable questions |
| TAT-DQA | Tables, calculations | CC BY 4.0 (README of the authors' GitHub repo, checked 20 November 2026) | Real financial report pages with arithmetic |
| CORD | Extraction, OCR | CC BY 4.0 (Hugging Face card and the authors' GitHub repo, checked 20 November 2026) | Gold JSON per receipt (Indonesian receipts) |
| GovReport | Long-document summary | CC BY 4.0 (Hugging Face card of the authors' lab, launch/gov_report, checked 20 November 2026) | Long reports with expert summaries |
| SPACE | Review summary | No licence stated for the data. The code in its GitHub repo is MIT (checked 20 November 2026, Q4) | Many reviews per hotel with human summaries |
| MMLongBench-Doc (stretch) | Q&A visual | Apache 2.0 per a 2026 paper (confirm) | Second long-document check |
| 2WikiMultihopQA | GraphRAG | Apache 2.0 (licence file of the authors' GitHub repo, checked 20 November 2026) | Multi-hop questions grounded in entity relations |
| MuSiQue | GraphRAG | CC BY 4.0 (README of the authors' GitHub repo, checked 20 November 2026) | Harder multi-hop questions |
| Public speech set | Audio | Chosen in 2.1 from LibriSpeech, FLEURS and AMI, all CC BY 4.0 (Hugging Face cards, checked 20 November 2026) | Word error rate test |
| Public injection set | Security | Chosen and checked in 12.2 | Attack tests |
| Berkeley Function Calling Leaderboard (BFCL) | Tool calls | Apache 2.0 (Hugging Face card, confirm in 7.6) | Public test of whether the model picks the right tool with valid arguments |
