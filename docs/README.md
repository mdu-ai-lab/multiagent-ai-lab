# Documentation index

| Field | Value |
|---|---|
| Purpose | Central entry point for all project documentation |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](WORK_PLAN.md) v1.9 |
| Related documents | [WORK_PLAN.md](WORK_PLAN.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

## 1. Project summary

A planned local, zero-cost platform where agents and RAG answer questions over files with page citations, search the web on request, summarise, extract JSON, calculate and transcribe audio. Built for the MDU university group. See [project overview](00-project-overview/project-overview.md).

**Important:** only the step 0.1 project setup exists as code (settings, database layer, Alembic). Every document describes the plan. All requirements are "Not implemented".

## 2. Directory map

| Folder | Content |
|---|---|
| 00-project-overview | Overview, scope, business requirements, stakeholders, glossary |
| 01-requirements | SRS, functional and non-functional requirements, business rules, constraints, acceptance |
| 02-users-and-permissions | Roles, permission matrix, use cases, access policy |
| 03-functional-modules | One document per module |
| 04-architecture | Architecture, ADRs, diagram index |
| 05-database | Data stores, ER diagram, data dictionary, constraints |
| 06-api | Standards, endpoint catalog, errors, integrations |
| 07-security | Requirements, auth, threat model, privacy, secrets |
| 08-ui-ux | Flows and screens |
| 09-testing | Strategy, plan, acceptance cases, performance, status |
| 10-deployment-and-operations | Environment, deployment, CI/CD, monitoring, backup, incidents |
| 11-development-standards | Coding, structure, Git, review, done, AI agent workflow |
| 12-project-management | Roadmap, milestones, risks, traceability |

## 3. Recommended reading order

1. [WORK_PLAN.md](WORK_PLAN.md) (source of truth)
2. [Project overview](00-project-overview/project-overview.md) and [scope](00-project-overview/project-scope.md)
3. [SRS](01-requirements/srs.md)
4. [System architecture](04-architecture/system-architecture.md) and [ADRs](04-architecture/architecture-decision-records/README.md)
5. [Modules](03-functional-modules/README.md)
6. [Threat model](07-security/threat-model.md)
7. [AI agent workflow](11-development-standards/ai-agent-workflow.md)

## 4. All documents

| Folder | Documents |
|---|---|
| 00-project-overview | [business-requirements](00-project-overview/business-requirements.md), [glossary](00-project-overview/glossary.md), [project-overview](00-project-overview/project-overview.md), [project-scope](00-project-overview/project-scope.md), [stakeholders](00-project-overview/stakeholders.md) |
| 01-requirements | [acceptance-criteria](01-requirements/acceptance-criteria.md), [business-rules](01-requirements/business-rules.md), [constraints-and-assumptions](01-requirements/constraints-and-assumptions.md), [functional-requirements](01-requirements/functional-requirements.md), [non-functional-requirements](01-requirements/non-functional-requirements.md), [srs](01-requirements/srs.md) |
| 02-users-and-permissions | [access-control-policy](02-users-and-permissions/access-control-policy.md), [role-permission-matrix](02-users-and-permissions/role-permission-matrix.md), [use-cases](02-users-and-permissions/use-cases.md), [user-types](02-users-and-permissions/user-types.md) |
| 03-functional-modules | [README](03-functional-modules/README.md), [agents-and-memory](03-functional-modules/agents-and-memory.md), [api-ui-mcp](03-functional-modules/api-ui-mcp.md), [audio](03-functional-modules/audio.md), [calculations](03-functional-modules/calculations.md), [delivery-and-operations](03-functional-modules/delivery-and-operations.md), [evaluation](03-functional-modules/evaluation.md), [extraction](03-functional-modules/extraction.md), [grounded-answers](03-functional-modules/grounded-answers.md), [ingestion](03-functional-modules/ingestion.md), [knowledge-graph](03-functional-modules/knowledge-graph.md), [notebooks](03-functional-modules/notebooks.md), [retrieval](03-functional-modules/retrieval.md), [summaries](03-functional-modules/summaries.md), [visual-content](03-functional-modules/visual-content.md), [web-search](03-functional-modules/web-search.md) |
| 04-architecture | [ADR-001](04-architecture/architecture-decision-records/ADR-001.md), [ADR-002](04-architecture/architecture-decision-records/ADR-002.md), [ADR-003](04-architecture/architecture-decision-records/ADR-003.md), [ADR-004](04-architecture/architecture-decision-records/ADR-004.md), [ADR-005](04-architecture/architecture-decision-records/ADR-005.md), [ADR-006](04-architecture/architecture-decision-records/ADR-006.md), [ADR-007](04-architecture/architecture-decision-records/ADR-007.md), [ADR-008](04-architecture/architecture-decision-records/ADR-008.md), [ADR-009](04-architecture/architecture-decision-records/ADR-009.md), [ADR-010](04-architecture/architecture-decision-records/ADR-010.md), [ADR-011](04-architecture/architecture-decision-records/ADR-011.md), [ADR-012](04-architecture/architecture-decision-records/ADR-012.md), [ADR-013](04-architecture/architecture-decision-records/ADR-013.md), [ADR-014](04-architecture/architecture-decision-records/ADR-014.md), [ADR-015](04-architecture/architecture-decision-records/ADR-015.md), [ADR-016](04-architecture/architecture-decision-records/ADR-016.md), [ADR-017](04-architecture/architecture-decision-records/ADR-017.md), [ADR-018](04-architecture/architecture-decision-records/ADR-018.md), [ADR-019](04-architecture/architecture-decision-records/ADR-019.md), [ADR-020](04-architecture/architecture-decision-records/ADR-020.md), [ADR-021](04-architecture/architecture-decision-records/ADR-021.md), [ADR-022](04-architecture/architecture-decision-records/ADR-022.md), [README](04-architecture/architecture-decision-records/README.md), [architecture-overview](04-architecture/architecture-overview.md), [backend-architecture](04-architecture/backend-architecture.md), [deployment-architecture](04-architecture/deployment-architecture.md), [README](04-architecture/diagrams/README.md), [frontend-architecture](04-architecture/frontend-architecture.md), [integration-architecture](04-architecture/integration-architecture.md), [system-architecture](04-architecture/system-architecture.md) |
| 05-database | [data-dictionary](05-database/data-dictionary.md), [database-design](05-database/database-design.md), [er-diagram](05-database/er-diagram.md), [relationships-and-constraints](05-database/relationships-and-constraints.md) |
| 06-api | [api-standards](06-api/api-standards.md), [authentication](06-api/authentication.md), [endpoint-catalog](06-api/endpoint-catalog.md), [error-handling](06-api/error-handling.md), [external-integrations](06-api/external-integrations.md) |
| 07-security | [authentication-and-authorization](07-security/authentication-and-authorization.md), [data-privacy](07-security/data-privacy.md), [secrets-management](07-security/secrets-management.md), [security-requirements](07-security/security-requirements.md), [threat-model](07-security/threat-model.md) |
| 08-ui-ux | [screen-specifications](08-ui-ux/screen-specifications.md), [user-flows](08-ui-ux/user-flows.md) |
| 09-testing | [acceptance-test-cases](09-testing/acceptance-test-cases.md), [performance-testing](09-testing/performance-testing.md), [test-plan](09-testing/test-plan.md), [testing-status](09-testing/testing-status.md), [testing-strategy](09-testing/testing-strategy.md) |
| 10-deployment-and-operations | [backup-and-recovery](10-deployment-and-operations/backup-and-recovery.md), [ci-cd-pipeline](10-deployment-and-operations/ci-cd-pipeline.md), [deployment-guide](10-deployment-and-operations/deployment-guide.md), [environment-configuration](10-deployment-and-operations/environment-configuration.md), [incident-response](10-deployment-and-operations/incident-response.md), [monitoring-and-logging](10-deployment-and-operations/monitoring-and-logging.md) |
| 11-development-standards | [ai-agent-workflow](11-development-standards/ai-agent-workflow.md), [code-review](11-development-standards/code-review.md), [coding-standards](11-development-standards/coding-standards.md), [definition-of-done](11-development-standards/definition-of-done.md), [git-workflow](11-development-standards/git-workflow.md), [project-structure](11-development-standards/project-structure.md) |
| 12-project-management | [milestones](12-project-management/milestones.md), [requirements-traceability](12-project-management/requirements-traceability.md), [risk-register](12-project-management/risk-register.md), [roadmap](12-project-management/roadmap.md) |
| (root) | [WORK_PLAN](WORK_PLAN.md) |

## 5. Key architectural decisions

Local llama.cpp runtime (ADR-002), LangGraph plus smolagents (ADR-003), Qdrant (ADR-004), SQLite then Postgres (ADR-005), MLflow (ADR-006), CI/CD on GitHub Actions (ADR-007), API-first (ADR-008), GitHub Pages plus ZeroGPU (ADR-009), Colab main and Kaggle backup (ADR-010), GitHub organization (ADR-016), knowledge graph and GraphRAG chosen by test (ADR-017), LinkML ontology (ADR-018), notebooks without audio overviews (ADR-019), verification loop and verification number (ADR-020), coding assistant with a local rules file and HANDOVER.md (ADR-021), names multiagent-ai-lab and mdu-ai-lab (ADR-022).

## 6. Main modules

Ingestion, visual content, retrieval, grounded answers, agents and memory, web search, summaries, knowledge graph and GraphRAG, notebooks and study tools, extraction, calculations, audio, API/UI/MCP, evaluation, delivery and operations.

## 7. Requirements status

| Type | Count | Implemented |
|---|---|---|
| Functional | 57 | 0 |
| Non-functional | 32 | 0 |
| Business rules | 16 | 0 |

## 8. Known implementation gaps

Everything except the step 0.1 project setup. Phase 0 is in progress.

## 9. Security concerns requiring attention

| ID | Concern |
|---|---|
| SF-01 | API without login before Phase 13. Recommendation: listen only on the Mac itself |
| SF-02 | Hidden instructions in files and web pages until Phase 12 |
| SF-05 | Private file uploaded to the public demo by mistake |
| SF-09 | Traces not masked before Phase 12 |
| SF-12 | Entity merging could link facts across collections |

Full list: [threat model](07-security/threat-model.md).

## 10. Items requiring human confirmation

| Item | Where |
|---|---|
| Open questions from WORK_PLAN.md section 4.2 (listed below) | WORK_PLAN.md section 4.2 |
| Storage and backup of the knowledge graph and notebooks | [Database design](05-database/database-design.md) |
| Supervisor approval of requirements | [SRS](01-requirements/srs.md) |
| Admin role and collection sharing | [User types](02-users-and-permissions/user-types.md) |
| API paths, error format, pagination | [Endpoint catalog](06-api/endpoint-catalog.md), [API standards](06-api/api-standards.md) |
| Password hash and token details | [Authentication and authorization](07-security/authentication-and-authorization.md) |
| Answer latency target | [Performance testing](09-testing/performance-testing.md) |
| Data retention | [Data privacy](07-security/data-privacy.md) |
| Commit message format, reviewer count | [Git workflow](11-development-standards/git-workflow.md), [Code review](11-development-standards/code-review.md) |

## 11. Documents not created and why

| Document | Reason |
|---|---|
| Payment processing, mobile apps, multi-tenant isolation beyond collection access | Not part of this project |
| CSRF and CORS documentation | REQUIRES CONFIRMATION until the web UI exists (Phase 13) |
| 05-database/indexes-and-performance.md | No tables or queries exist |
| 05-database/migration-strategy.md | Alembic is chosen (D25) but no tables exist yet. Covered in database design |
| 06-api/pagination-filtering-sorting.md | No list endpoints exist. Covered in API standards |
| 08-ui-ux/design-system.md | No visual design decisions exist |

## Open questions (WORK_PLAN.md section 4.2, word for word)

| ID | Question | Needed by |
|---|---|---|
| Q1 | Code licence for the repo. Proposal: Apache-2.0. Confirm with the group | Answered 31 October 2026: Apache-2.0 (D23) |
| Q2 | Should private documents ever be backed up to Drive? Default: no. Option: encrypted with rclone crypt, only if you decide | Step 0.6 |
| Q3 | Is your Hugging Face account older than 30 days with a verified email? (needed for the free ZeroGPU Space) | Step 1.8 |
| Q4 | SPACE dataset licence (not yet verified). Replace if it blocks use | Step 2.1 |
| Q5 | SPACE key points: written by hand (default) or LLM-assisted (counts as synthetic, needs your approval) | Step 9.3 |
| Q6 | Swedish documents in v1 or later | Step 2.2 |
| Q8 | Which role "full access" means: Owner (controls the whole organization, including deleting it) or Admin (full control of the repo only) | Answered 31 October 2026: Admin on the repo (D24) |
| Q9 | Which domain ontology to build first (for example research papers or industrial documents) | Step 9A.1 |
| Q10 | Add audio overviews (spoken summaries of sources)? This needs a text-to-speech model and changes a non-goal | Before Phase 9B |
| Q11 | Does "Knowledge" mean the knowledge base described in R31 or something else? | Before Phase 9A |

## 12. Maintenance

Update WORK_PLAN.md first, then the affected documents, in the same commit. Change a document's status only when the change is real. Never mark a document Approved unless the group supervisor approved it.
