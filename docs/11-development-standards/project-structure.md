# Project structure

| Field | Value |
|---|---|
| Purpose | Planned repository layout |
| Status | Proposed |
| Last updated | 2026-11-05 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Backend architecture](../04-architecture/backend-architecture.md) |

> Implementation status: Phase 0 done (project setup, search database, Mac model server, model client and backup). Later features are planned and not built yet. Test results are in docs/HANDOVER.md.

Copied from WORK_PLAN.md section 8.2.

```
multiagent-ai-lab/
├── src/mrag/        config.py db.py llm_client.py service.py api.py auth.py ui.py
│                    jobs.py worker.py parse.py figures.py chunking.py pii.py versioning.py
│                    embed.py index.py retrieve.py rerank.py router.py graph.py qa.py planner.py
│                    ontology.py kg.py graphrag.py notebook.py study.py
│                    grounding.py memory.py web.py summary.py extract.py calc.py security.py harness.py
│                    audio.py tracing.py eval_data.py eval_metrics.py eval_run.py judge.py
│                    export_results.py site_build.py
│                    admin.py translations.py templates/ static/ (pages of ui.py)
├── demo/            app.py and requirements for the ZeroGPU Space
├── notebooks/       colab_gpu.ipynb kaggle_gpu.ipynb (every cell labelled)
├── configs/         settings, models.yaml, harness.yaml, schemas/, ontology/, eval/
├── migrations/      Alembic database migrations (D25)
├── data/            private/ public/ annotations/ (only annotations in Git)
├── results/         exported result summaries (in Git)
├── tests/           unit/ integration/ e2e/ fixtures/
├── benchmarks/      measuring tools, for example measure_mac.py
├── ops/             operations tools, for example backup.py (make backup) and mlflow-server/ (local MLflow server)
├── docs/            WORK_PLAN.md, HANDOVER.md, guides, data cards, system card
├── .github/workflows/  ci.yml pages.yml demo.yml health.yml release.yml
├── compose.yaml  Makefile  pyproject.toml  uv.lock  .env.example  LICENSE  README.md  CHANGELOG.md
```
