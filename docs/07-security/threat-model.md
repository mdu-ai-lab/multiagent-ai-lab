# Threat model

| Field | Value |
|---|---|
| Purpose | Assets, entry points, threats and planned mitigations |
| Status | Proposed |
| Last updated | 2026-10-31 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.9 |
| Related documents | [Security requirements](../07-security/security-requirements.md), [Risk register](../12-project-management/risk-register.md) |

> Implementation status: Phase 0 in progress. Only the step 0.1 project setup exists as code (settings, database layer, Alembic). This document describes the planned system. Nothing here is verified behaviour.

Design-level review of the plan. No code was inspected because none exists. Severity is the reviewer's estimate.

## Assets

Private documents, their index and chat history, MLflow traces, tokens (GitHub, Hugging Face, rclone), the GitHub organization, the demo Space.

## Entry points

API, UI, MCP, uploaded files, fetched web pages, the demo, GitHub Actions, notebooks.

## Findings

| ID | Threat | Severity | Evidence in plan | Planned mitigation | Gap |
|---|---|---|---|---|---|
| SF-01 | API has no login before Phase 13. Anyone on the same network could call it | Medium | 1.6, 13.1 | Login in 13.1 | Recommend binding to the Mac only until 13.1. Not yet in plan |
| SF-02 | Hidden instructions inside files or web pages | High | 12.1 | Rules in 12.1, classifier in 12.2 | None until Phase 12 |
| SF-03 | Model-written code escapes the sandbox | High | 11.2 | Docker, no network, limits | Escape tests in 11.2 |
| SF-04 | File text leaks through web search | High | 8.1 | Question only, leak test 8.4 | — |
| SF-05 | Private file uploaded to the demo by mistake | High | 1.8 | Public samples only (BR-PRIV-001) | Manual process. A check in CI: REQUIRES CONFIRMATION |
| SF-06 | Hugging Face or GitHub token exposed in CI logs | Medium | 1.8, 1.4 | GitHub Secrets, secret scan | — |
| SF-07 | Too many organization owners can delete the repo | Medium | Q8 | Role choice | Decide Q8 |
| SF-08 | Malicious or huge uploads | Medium | 12.4 | Limits, type check by content | — |
| SF-09 | Personal data in traces or exports | Medium | 12.3 | Presidio masking | Before Phase 12 traces are unmasked |
| SF-10 | Tampered model or package | Medium | 1.3, 1.4 | Pinned revisions, pip-audit, Dependabot | — |
| SF-11 | rclone or Drive token on the Mac misused | Low | 0.6 | Password manager, no secrets in Drive | — |
| SF-12 | Entity merging links facts from collections a user cannot see | Medium | 9A.2, 9A.4 | Graph built per collection, same filter as retrieve.py | Merge rules across collections REQUIRES CONFIRMATION |
| SF-13 | A poisoned document adds false relations to the graph | Medium | 9A.2 | Source page for every fact, claim check, ontology-constrained output | — |
