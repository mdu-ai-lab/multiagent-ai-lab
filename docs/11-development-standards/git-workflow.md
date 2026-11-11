# Git workflow

| Field | Value |
|---|---|
| Purpose | How work moves through GitHub |
| Status | Proposed |
| Last updated | 2026-11-11 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Code review](../11-development-standards/code-review.md), [CI/CD pipeline](../10-deployment-and-operations/ci-cd-pipeline.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

| Item | Rule | Source |
|---|---|---|
| Owner | Repo in a free GitHub organization | D16, 0.1, Q8 |
| Main branch | Ruleset protect-main for everyone, no bypass: pull request required (0 approvals), CI checks must pass with the branch up to date with main, no deletion, no force push | 1.1, 1.4, D39, D42 |
| Branches | One per phase (phase-1, phase-2 and so on), kept until the phase ends. remote/YYYY-MM-DD for Kaggle or Colab work | 1.1, D39, section 6.4 |
| Commits | After every step, on the phase branch | Rule G, 1.1 |
| Merging | Every change to main goes through a pull request, docs fixes too. Merge commits only. Members always work through pull requests | 1.1, D39 |
| Tags | Version tag at phase end (v0.1.0, v0.2.0 and so on). First tag v0.0.0 (end of Phase 0). First pull request tag v0.0.1 | 1.1 |
| Changelog | CHANGELOG.md updated every step | 1.1 |
| Repo visibility | Public (keeps Actions and Pages free) | Rule Z |
| Tool | gh command-line tool (Homebrew) for the ruleset and pull requests | D39 |

Commit message format: one line that describes the change in plain words, with no plan numbers and no step or phase words (C16) and no name of the coding assistant product (C15).
