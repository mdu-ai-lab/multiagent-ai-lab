# Git workflow

| Field | Value |
|---|---|
| Purpose | How work moves through GitHub |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Code review](../11-development-standards/code-review.md), [CI/CD pipeline](../10-deployment-and-operations/ci-cd-pipeline.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Item | Rule | Source |
|---|---|---|
| Owner | Repo in a free GitHub organization | D16, 0.1, Q8 |
| Main branch | Protected for everyone | 1.1 |
| Branches | One per phase. remote/YYYY-MM-DD for Colab work | 1.1, section 6.4 |
| Commits | After every step | Rule G |
| Merging | Pull request at phase end. Members always work through pull requests | 1.1 |
| Tags | Version tag at phase end (v0.1.0, v0.2.0 and so on). First tag v0.0.0 (end of Phase 0). First pull request tag v0.0.1 | 1.1 |
| Changelog | CHANGELOG.md updated every step | 1.1 |
| Repo visibility | Public (keeps Actions and Pages free) | Rule Z |

Commit message format: REQUIRES CONFIRMATION.
