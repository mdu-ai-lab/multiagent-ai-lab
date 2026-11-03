# Security requirements

| Field | Value |
|---|---|
| Purpose | Planned security controls |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Threat model](../07-security/threat-model.md), [Non-functional requirements](../01-requirements/non-functional-requirements.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Control | Requirement IDs | Phase | Status |
|---|---|---|---|
| File and web text are data only | NFR-SEC-001, BR-SEC-001 | 12.1 | Not implemented |
| Optional injection classifier | NFR-SEC-001, BR-KEEP-001 | 12.2 | Not implemented |
| Code sandbox | NFR-SEC-002 | 11.2 | Not implemented |
| Access per collection (including graph route and notebooks) | NFR-SEC-003, BR-ACC-001 | 5.3, 12.4, 9A.4, 9B.1 | Not implemented |
| Input limits and rate limits | NFR-SEC-004 | 12.4, 13.1 | Not implemented |
| Secrets handling | NFR-SEC-005 | 0.1, 1.5 | Not implemented |
| Personal data masking | NFR-SEC-006 | 12.3 | Not implemented |
| Dependency and secret scanning | NFR-SEC-007 | 1.4 | Not implemented |
| Login and tokens | FR-API-002 | 13.1 | Not implemented |
| No outgoing traffic except opt-in web search (company setup) | — | 15.5 | Not implemented |

No security control is in place. No compliance claim (GDPR, EU AI Act, ISO) is made.
