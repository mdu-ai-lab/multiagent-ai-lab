# Project overview

| Field | Value |
|---|---|
| Purpose | Short description of what the platform is, who it is for and where it stands |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Project scope](../00-project-overview/project-scope.md), [SRS](../01-requirements/srs.md), [System architecture](../04-architecture/system-architecture.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

## Summary

The Local Multi-Agent RAG Platform (repository: multiagent-ai-lab; GitHub organization: mdu-ai-lab) is a planned chat and document question-answering assistant that runs locally. Specialised agents and retrieval-augmented generation (RAG) work together so one platform can:

- chat, with or without files
- answer questions over supported files with page-level citations
- search the web on request (opt-in)
- summarise long documents and many reviews
- extract structured JSON from documents
- calculate and plot from tables
- answer relationship questions through a knowledge graph built on an ontology (GraphRAG)
- organise sources in notebooks (workspaces on one topic) with study tools (study guide, FAQ, briefing, flashcards, quiz, mind map)
- transcribe and answer questions about audio (late phase)

It is built for the MDU university group. It is designed so a company that avoids cloud AI could pilot it inside its own network after its own review.

## Origin

The design reuses selected ideas from four MDU research works (Billah thesis, Billah et al. journal article, Chakravorty thesis, Wahab thesis). None of them released a usable public pipeline, API or frontend. That gap is the reason for this project. Paper references are listed in WORK_PLAN.md and cited in the module documents.

## Current state

| Item | Value | Evidence |
|---|---|---|
| Code | None written | WORK_PLAN.md section 1 |
| Repository | Not created (planned in a GitHub organization) | WORK_PLAN.md section 1, D16 |
| Live dashboard and demo | Not created | WORK_PLAN.md section 1 |
| Next action | Owner says "start Phase 0" | WORK_PLAN.md section 1 |

## Key constraints

Zero cost, private documents stay on the owner's Mac, real public datasets only, every technology must have a purpose. See [constraints and assumptions](../01-requirements/constraints-and-assumptions.md).
