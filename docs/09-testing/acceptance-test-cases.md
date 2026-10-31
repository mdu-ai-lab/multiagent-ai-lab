# Acceptance test cases

| Field | Value |
|---|---|
| Purpose | One test case per plan step |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Test plan](../09-testing/test-plan.md), [Traceability](../12-project-management/requirements-traceability.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Copied from the done-when column of WORK_PLAN.md section 12. The plan stays the source of truth.

| ID | Step | Pass condition | Result |
|---|---|---|---|
| AT-0.1 | Project setup | uv run python -m mrag.config prints the settings. The repo is on GitHub with no data files. The coding assistant has loaded its local rules file. The uv check command (rule C13) prints the same numbers as the coding assistant for every Python file of this step. | Passed |
| AT-0.2 | Search database | Health check returns OK. Data is still there after a restart. | Passed |
| AT-0.3 | Mac model server | 5 test calls succeed: text chat, chat with an image, embedding, reranking and JSON output. | Passed |
| AT-0.4 | Measure the Mac | Peak RAM < 13 GB with main + embedding + reranker loaded. Settings saved in config. | Not run |
| AT-0.5 | Model client | The same test call works through the wrapper with the Mac profile. | Not run |
| AT-0.6 | Backup and sync | Backup runs. A file restored into a temp folder matches the original. Drive usage recorded. | Not run |
| AT-0.7 | Plan in the repo | docs/WORK_PLAN.md is on GitHub and shows Phase 0 progress. | Not run |
| AT-1.1 | GitHub workflow | First pull request merged with tag v0.0.1. | Not run |
| AT-1.2 | MLflow | A test run shows all fields. A trace shows each model call with time and tokens. The export creates JSON files. | Not run |
| AT-1.3 | Versioning rules | Pick one old result and trace it to its exact versions. | Not run |
| AT-1.4 | CI pipeline | CI is green. A deliberately broken commit fails CI. | Not run |
| AT-1.5 | Free GPU profile | The smoke test runs on Colab and on Kaggle. The chosen GPU models are recorded. The runs appear in the Mac's MLflow. | Not run |
| AT-1.6 | API-first skeleton | The API runs locally. All endpoint tests pass in CI. | Not run |
| AT-1.7 | Live dashboard (CD) | The site URL works. A pushed change appears on it within minutes. Site size stays far below 1 GB. | Not run |
| AT-1.8 | Live demo (CD) | The Space URL works. A pushed change appears after the Space rebuilds. | Not run |
| AT-1.9 | Health checks | A deliberately wrong URL creates an issue. | Not run |
| AT-2.1 | Datasets | All datasets on the SSD. Every data card complete. | Not run |
| AT-2.2 | Test sets | A manifest lists counts and file hashes. | Not run |
| AT-2.3 | Evaluation script | Running the same test twice gives identical numbers. | Not run |
| AT-2.4 | Baselines | Baseline tables saved in MLflow and shown on the dashboard. | Not run |
| AT-2.5 | Judge | Agreement number reported. Scoring guide frozen and versioned. | Not run |
| AT-3.1 | Upload and background jobs | Kill the worker mid-job. After restart the job finishes. | Not run |
| AT-3.2 | Parse every file type | A sample file of each type parses correctly. | Not run |
| AT-3.3 | OCR test | Best engine chosen by numbers and set in config. | Not run |
| AT-3.4 | Rich records | Heading path on ≥ 95% of text parts. Every part has a page and a box. | Not run |
| AT-3.5 | Versions and duplicates | Tests for duplicate, new version and delete pass. | Not run |
| AT-4.1 | Describe visuals | Every figure has a description linked to its page. | Not run |
| AT-4.2 | Parser comparison | Results table done. Winner set in config. | Not run |
| AT-4.3 | Prove it helps | Evidence found ≥ 5 points more often. Otherwise we rethink. | Not run |
| AT-5.1 | Chunking | No table is split. Every chunk has a heading path and a page. | Not run |
| AT-5.2 | Indexing | All test files indexed. Re-indexing unchanged files creates 0 new vectors. | Not run |
| AT-5.3 | Hybrid search | The filter test returns only allowed chunks. | Not run |
| AT-5.4 | Reranking | Better than no reranking on dev. | Not run |
| AT-5.5 | Ablation tests | Best setup beats dense-only on nDCG@10 with CI above 0. Search p50 ≤ 2 s on the Mac. | Not run |
| AT-6.1 | Cited answers | Every test answer carries citations. | Not run |
| AT-6.2 | Small-file mode | Size rule per profile chosen by test numbers. | Not run |
| AT-6.3 | Citation and claim check | 100% valid citations. Unsupported claims ≤ 10%. | Not run |
| AT-6.4 | Refusal | Refusal F1 ≥ 0.70 on test. | Not run |
| AT-6.5 | Highlight data | Every citation maps to a box. | Not run |
| AT-7.1 | Router | ≥ 90% correct. Helper kept only if within 2 points of the main model. | Not run |
| AT-7.2 | Agent graph | Each node answers its test questions. | Not run |
| AT-7.3 | Hard-question loop | Judge score up. Faithfulness drop ≤ 2 points. Otherwise it stays off. | Not run |
| AT-7.4 | Limits and fallbacks | 0 runaway loops in 200 runs. Every fallback tested. | Not run |
| AT-7.5 | Chat memory | Follow-up questions in test chats answered correctly. | Not run |
| AT-8.1 | Opt-in search | Toggle off → 0 web calls. No key or payment needed. | Not run |
| AT-8.2 | Read pages | Clean text with source for the test pages. | Not run |
| AT-8.3 | Web citations | Every web citation points to a fetched URL. | Not run |
| AT-8.4 | Leak test | 0 matches. | Not run |
| AT-9.1 | Long documents | Every main section appears in the summary. | Not run |
| AT-9.2 | Reviews | 100% of numbers match pandas. | Not run |
| AT-9.3 | Test | Higher coverage (non-overlapping CI). FSCR ≥ 0.80. | Not run |
| AT-9A.1 | Ontology | Pydantic models and OWL file generate without errors. Changing the YAML and regenerating updates both. | Not run |
| AT-9A.2 | Graph extraction | Every graph fact has a source page. Extraction precision measured on a hand-checked sample of 50 facts. Time and model calls recorded. | Not run |
| AT-9A.3 | Engine choice | Comparison table on 2WikiMultihopQA dev. Winner set in config. | Not run |
| AT-9A.4 | Graph route | Router sends graph questions to this route. Every answer cites pages. Filter test passes. | Not run |
| AT-9A.5 | Test | Results table logged in MLflow. Graph route kept only where it beats hybrid RAG. | Not run |
| AT-9B.1 | Notebooks | Create a notebook, add sources, chat, save a note, reopen it with everything kept. | Not run |
| AT-9B.2 | Study outputs | All 6 output types generate. 100% valid citations. Quiz answers checked against their sources. | Not run |
| AT-9B.3 | Mind map | Mind map generates for a test notebook. Every node links to a source page. | Not run |
| AT-9B.4 | Test | Unsupported claims ≤ 10%. Hand-check result recorded. | Not run |
| AT-10.1 | Schemas | The CORD schema accepts CORD's correct answers. | Not run |
| AT-10.2 | Extractor | 100% valid JSON. | Not run |
| AT-10.3 | Verifier and Refiner | Field accuracy ≥ few-shot baseline, with Wilson CI. | Not run |
| AT-10.4 | Export and batch | Files open correctly. A batch of 100 completes. | Not run |
| AT-11.1 | Find tables | Test tables load with correct types. | Not run |
| AT-11.2 | Sandbox code | Escape tests blocked: network, file writing, endless loop and huge memory. | Not run |
| AT-11.3 | Plots | Plot appears for plot questions. | Not run |
| AT-11.4 | Math test | ≥ 10 points better. | Not run |
| AT-12.1 | Rule defences | Rule test suite passes. | Not run |
| AT-12.2 | Injection classifier | Kept only if attack success drops and false alarms ≤ 2%. | Not run |
| AT-12.3 | Personal data | 0 personal data in sampled traces. | Not run |
| AT-12.4 | Access and limits | 0 leaks in a cross-user test. All limits tested. | Not run |
| AT-13.1 | API hardening | All API tests pass, including login and limit tests. | Not run |
| AT-13.2 | Full web UI | A full chat works in the browser locally and in the demo. | Not run |
| AT-13.3 | MCP | An MCP client calls the tools successfully. | Not run |
| AT-13.4 | User feedback and monitoring | Feedback appears on the right trace. The monitoring view shows the last 7 days. | Not run |
| AT-13.5 | End-to-end test | Upload → ask → streamed cited answer with highlight. | Not run |
| AT-14.1 | Model comparison | Best model per profile chosen. | Not run |
| AT-14.2 | Audio pipeline | A question about a recording cites the right time range. | Not run |
| AT-15.1 | Docker images | Images build in CI and start correctly. | Not run |
| AT-15.2 | GPU server profile | Compose file validated in CI. vLLM path works on Kaggle. | Not run |
| AT-15.3 | Database switch | All tests pass on both databases. | Not run |
| AT-15.4 | Load test | Speed and error numbers reported. | Not run |
| AT-15.5 | Deployment and security guide | Guide covers every service and setting. | Not run |
| AT-16.1 | One-command setup | A fresh install works on the M2. | Not run |
| AT-16.2 | Guides and cards | Every feature and every model covered. | Not run |
| AT-16.3 | Final report | Real numbers for every route. | Not run |
| AT-16.4 | Group test | They succeed without your help. | Not run |
