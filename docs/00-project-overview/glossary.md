# Glossary

| Field | Value |
|---|---|
| Purpose | Plain definitions of terms used across the documentation |
| Status | Proposed |
| Last updated | 2026-11-09 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Project overview](../00-project-overview/project-overview.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Term | Meaning |
|---|---|
| RAG | Retrieval-augmented generation: the model answers using text found in your files |
| Agent | A model-driven step that decides what to do next, such as which search to run |
| Route | One task path in the agent graph (chat, document Q&A, web, summary, extraction, calculation, compare) |
| Agent harness | Everything around the model that makes it an agent, in one package (src/mrag/harness/, D43): context building, retrieval at question time, memory, tools, the agent loop, limits, guards and answer checks. The model itself stays outside (llm_client.py) |
| Chunk | A small piece of a document stored for search |
| Element | One parsed part of a document (heading, paragraph, table, figure) with page and position |
| Hybrid search | Combining meaning search (vectors) with word search (BM25) |
| RRF | Reciprocal rank fusion: a way to merge ranked result lists |
| Reranker | A model that re-scores search results for relevance |
| Claim check | Checking each answer sentence against its cited source |
| Refusal | Answering "not found in your files" instead of guessing |
| Profile | A configuration for one environment: Mac, GPU, demo, CI or company server |
| ZeroGPU | Hugging Face feature that gives a Space a shared GPU on demand |
| MCP | Model Context Protocol: lets other AI tools call the platform's tools |
| FSCR | Fully supported claims ratio (from the Wahab thesis) |
| Golden set | A frozen test set with correct answers |
| Phase gate | Check results and get owner permission before the next phase |
| Knowledge graph | Entities (people, places, concepts) and the relations between them, extracted from documents |
| GraphRAG | RAG that also uses the knowledge graph, for relationship and whole-corpus questions |
| Ontology | The fixed list of entity and relation types the graph may contain |
| LinkML | A YAML modelling language that can generate Pydantic models and OWL from one ontology file |
| OWL | Web Ontology Language, a standard format for ontologies |
| Community summary | A summary of a cluster of related entities, used for whole-corpus questions |
| Notebook (platform) | A workspace on one topic with chosen sources, chats and notes. Not a Jupyter notebook |
| Knowledge base | Collections, knowledge graph and saved notes together (interpretation, Q11) |
