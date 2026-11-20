# multiagent-ai-lab

Work in Progress

## Status

Version 0.1.0: Phase 1 is done. Working now:

- The chat web page on the Mac: sign-up, login, saved chats, answers streamed from the main
  model (Qwen3.5-9B) and shown as safe Markdown, settings in English and Swedish and an admin
  panel. A FastAPI backend serves it on 127.0.0.1.
- The live dashboard with the progress of the plan: https://mdu-ai-lab.github.io/multiagent-ai-lab/
- The live demo, a plain chat on a free Hugging Face ZeroGPU Space:
  https://huggingface.co/spaces/hossain007bhuiyan/multiagent-ai-lab-demo
- CI on GitHub Actions, MLflow for runs and traces and a weekly health check of the live sites.

Planned and not working yet: questions over documents with sources, web search and the other
agent features. The full plan and the current state are in [docs/WORK_PLAN.md](docs/WORK_PLAN.md).

## Quick start (Mac)

Needs [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 by itself.

```
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run python -m mrag.admin create-admin <email> <name>
make api
```

Then open http://127.0.0.1:8000. Chat answers need the model server (llama-swap on
127.0.0.1:8080 with configs/llama-swap.yaml). How to start it is in
[docs/HANDOVER.md](docs/HANDOVER.md).

## Documentation

- [docs/WORK_PLAN.md](docs/WORK_PLAN.md): plan, decisions, rules and progress (source of truth)
- [docs/HANDOVER.md](docs/HANDOVER.md): report of the last work session
- [docs/README.md](docs/README.md): index of all project documents

## Licence

Apache License 2.0. See [LICENSE](LICENSE).
