# Agent harness

| Field | Value |
|---|---|
| Purpose | Design of the agent harness package: its parts, boundaries, entry point and tests |
| Status | Proposed |
| Last updated | 2026-11-09 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 (D43, R35, steps 1.6 to 13.3) |
| Related documents | [Backend architecture](../04-architecture/backend-architecture.md), [System architecture](../04-architecture/system-architecture.md), [Agents and memory](../03-functional-modules/agents-and-memory.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

## What the harness is

Agent = Model + Harness. The model only reads text and images and writes text. Everything around it that turns it into an agent is the harness: what goes into the prompt, where the evidence comes from, which tools it may use, how long it may run, what is checked before an answer goes out and what is recorded. In this project the model side is llm_client.py. The harness is one package, src/mrag/harness/ (D43), so these parts are designed, configured, versioned and tested as one unit.

## Parts and where they live

| Part | File in src/mrag/harness/ | Built in | Measured by |
|---|---|---|---|
| Public entry, request and stream events | `__init__.py`, `handle.py`, `loop.py` | 1.6 | 1.6 endpoint and streaming tests |
| Settings per profile | `settings.py` with configs/harness.yaml | 1.6 | Every profile loads and is valid |
| Context building: prompt, chat history and sources within the token budget, fixed prompt start | `context.py` | 1.6, 6.1 | No prompt over the budget in any profile. Time to first token |
| Limits and fallbacks: time, tokens, tool calls, rounds | `limits.py` | 1.6, 7.4 | 0 runaway loops in 200 runs. Every fallback tested |
| Memory: chat turns, state of a running request, follow-up rewriting, long-chat summary | `memory.py` | 1.10, 7.5 | Follow-up questions answered correctly |
| Retrieval at question time: hybrid search, RRF, access filter, small-file mode, web, graph and note sources | `retrieval.py` | 5.3, 6.2, 8.2, 9A.4, 9B.1 | 5.5 ablation, filter tests, 6.2 size rule |
| Reranking with the structure score | `rerank.py` | 5.4 | Better than no reranking on dev |
| Answer checks: citations, claims, refusal, JSON output | `verify.py` | 6.3, 6.4 | 100% valid citations, unsupported claims ≤ 10%, refusal F1 ≥ 0.70 |
| Router, with a question to the user when unsure | `router.py` | 7.1 | ≥ 90% correct |
| Agent loop: LangGraph graph, stop conditions, 2 interrupts | `loop.py` | 7.2, 7.1, 10.3 | Each node answers its test questions |
| Planner–Navigator–Reviewer, off unless it helps | `planner.py` | 7.3 | Judge score up, faithfulness drop ≤ 2 points |
| Tools: registry, allowed tools per route, timeouts, result size limits, call format | `tools.py` | 7.6, 8.1, 11.2 | A route cannot call a tool outside its list. BFCL test on the Mac |
| Guards: data wrapping, injection rules, the optional classifier (injection.py) for web pages, personal data masking of traces | `guards.py` | 7.6, 12.1 to 12.3 | Rule test suite. 0 personal data in sampled traces |
| Request trace and its totals (tokens, model calls, tool calls, time, fallback) | recorded by `loop.py` through tracing.py | 1.6 | 1.2 tracing tests |
| The whole harness | all files | 1.6, 7.7 | Import test from 1.6. Each optional part switched off one at a time in 7.7 |

## Outside the package

| Module | Why it stays outside |
|---|---|
| llm_client.py | The model side. The harness calls it |
| prompts.py, tracing.py, config.py, db.py | Shared infrastructure, built in Phases 0 and 1 and also used by the evaluation runs |
| embed.py, index.py, worker.py, figures.py, sections.py | Work at upload is not part of a question: indexing, figure descriptions (figures.py), section summaries (sections.py), graph extraction (kg.py) and the injection scan (injection.py). figures.py, sections.py and kg.py call llm_client.py directly. injection.py runs its own small classifier. The harness reads the index schema from index.py |
| web.py, kg.py (the graph engine chosen in 9A.3), pii.py, injection.py, the code sandbox | Engines. The harness registers or calls them: harness/retrieval.py reads graph facts from kg.py at question time. kg.py, pii.py and injection.py also run in the upload pipeline |
| qa.py, summary.py, extract.py, calc.py, graphrag.py, notebook.py, study.py | Route agents. They use the Harness handle and nothing else on the model or tool side. summary.py only reads the stored section summaries. graphrag.py gets graph facts through harness/retrieval.py |

## Import direction

```
api.py ─► service.py ─┬─► harness (run, Request, events)
                      └─► route agents     service.py builds the route table
route agents ─────────────► harness (Harness handle only)
harness/* ────────────────► llm_client · prompts · tracing · config · db · index schema · engines
```

The harness never imports a route agent, service.py or api.py. loop.py receives the route table as an argument, so no import goes in the other direction. The upload modules (figures.py, sections.py, kg.py), the evaluation runs (the baselines of 2.4 and the judge of 2.5) and the tools in ops/ call llm_client.py directly on purpose. Step 1.6 adds a unit test that reads the imports of every module and fails CI if service.py, api.py or a route agent creates a model client or imports the search or a tool directly. It also fails if a harness module imports a route agent, service.py or api.py. Step 7.7 runs it again with all route agents.

## The run() contract

`harness.run(request, routes)` returns a normal Python generator of events:

| Event | Meaning | From |
|---|---|---|
| Delta | A piece of the answer text | 1.6 |
| Sources | The numbered sources of the answer | 6.1 |
| Status | A short progress note, for example while searching | 7.x |
| Revision | Sentences marked after the claim check | 6.3 |
| Done | The final answer and the request totals | 1.6 |
| Error | The kind of error and a short message | 1.6 |

FastAPI streams a normal generator (Starlette runs it in a thread pool) and the Gradio demo reads generators as well, so the API, the chat page and the demo share one call. From 7.2 the model node writes answer pieces with LangGraph's stream writer and loop.py reads the graph in its custom stream mode, which works with model clients that are not LangChain chat models. When the browser closes the stream, the generator closes, the model call stops and the trace records that it stopped early. Whether answers stream before the claim check or wait for it is decided by test in 6.3.

## Settings

configs/harness.yaml holds one section per profile (mac, gpu, demo, ci, company): token budgets, answer token caps, time and tool-call limits, the tools allowed per route, the context sources per route and an on/off switch for each optional part. The numbers are set by the tests of 1.6, 6.1, 6.2 and 7.4, not guessed. The file is part of the pipeline version, because every configs/*.yaml file is fingerprinted on every run and trace.

## How it grows

| Steps | What the harness gains |
|---|---|
| 1.6, 1.8, 1.10 | The entry point with a plain chat path: system prompt, history within the budget, limits, streaming, request trace and the import test. Chat turns from the chat tables |
| 5.3, 5.4 | Search and reranking at question time |
| 6.1 to 6.4 | Cited prompts within the budget, small-file mode, citation and claim check, refusal |
| 7.1 to 7.6 | Router, LangGraph graph, planner loop, limits and fallbacks, memory, tools and guards |
| 7.7 | The import test again with all route agents and the part-by-part ablation |
| 8.1 to 8.3, 9A.4, 9B.1 | Web search as a tool and web, graph and note sources |
| 10.3, 11.2 | The review interrupt for extraction and the code sandbox as a tool |
| 12.1 to 12.4 | The full rule tests, the optional classifier, masking of trace data and the access filter tests |

## Why every part is measured

Changing only the harness can change results a lot. A heavier harness can also cost more time and tokens without better answers. Step 7.7 switches each optional part off one at a time and records quality, p50 time, tokens and model calls per answer in MLflow. A part that does not help is switched off and the reason is recorded.

## Sources

| Source | Used for |
|---|---|
| LangChain, "The Anatomy of an Agent Harness", 10 March 2026, langchain.com/blog | The definition Agent = Model + Harness and the point that changing only the harness can change results |
| LangGraph documentation, Streaming, section "Use with any LLM" (docs.langchain.com) | Streaming from a model client that is not a LangChain chat model |
