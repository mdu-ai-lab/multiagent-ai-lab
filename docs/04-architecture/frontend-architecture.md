# Frontend architecture

| Field | Value |
|---|---|
| Purpose | Planned user interfaces |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Screen specifications](../08-ui-ux/screen-specifications.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

| Client | Technology | Talks to | Phase |
|---|---|---|---|
| Local web UI | Gradio 6 (ui.py), including notebook view and mind map and graph view | API only | 13.2 |
| Demo mind map view | Simple view in the demo | service.py in-process | 9B.3 |
| Live demo | Gradio on ZeroGPU Space | service.py in-process | 1.8, grows each phase |
| Live dashboard | Static site from site_build.py | results/ files at build time | 1.7 |
| MCP | Gradio MCP mode | API with login token | 13.3 |

The local UI calls only the API so it can be replaced later without backend changes.
