# multiagent-ai-lab

Work in Progress

## Status

Phase 1 is in progress. Working now: the FastAPI backend with login, saved chats and an admin panel, the chat web page, CI and the live dashboard (https://mdu-ai-lab.github.io/multiagent-ai-lab/). Document question answering, web search and the other agent features are planned. The full plan and the current
state are in [docs/WORK_PLAN.md](docs/WORK_PLAN.md).

## Quick start (Mac)

Needs [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 by itself.

```
uv sync
cp .env.example .env
uv run python -m mrag.config
```

The last command prints the active settings.

## Documentation

- [docs/WORK_PLAN.md](docs/WORK_PLAN.md): plan, decisions, rules and progress (source of truth)
- [docs/HANDOVER.md](docs/HANDOVER.md): report of the last work session
- [docs/README.md](docs/README.md): index of all project documents

## Licence

Apache License 2.0. See [LICENSE](LICENSE).
