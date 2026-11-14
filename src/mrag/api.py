# The HTTP API of the platform under /v1, served by FastAPI. Experimental until the API is
# frozen: paths and fields may still change. Start it with: make api
# The functions live in service.py. This file only turns HTTP into calls and back

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from importlib.metadata import version
from typing import Literal

import anyio
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, format_sse_event
from pydantic import BaseModel, Field

from mrag import harness, service
from mrag.harness.context import Turn

# The name of each streamed event
EVENT_NAMES = {harness.Delta: "delta", harness.Done: "done", harness.Error: "error"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    service.start()
    yield


app = FastAPI(
    title="multiagent-ai-lab API",
    version=version("multiagent-ai-lab"),
    description="Experimental: paths and fields under /v1 may still change.",
    lifespan=lifespan,
)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # Earlier turns, oldest first. They come from the saved chats once those exist
    history: list[ChatTurn] = []


@app.get("/v1/health")
def health() -> service.Health:
    return service.health()


@app.get("/v1/version")
def get_version() -> service.VersionInfo:
    return service.version()


@app.get("/v1/models")
def models() -> service.ProfileModels:
    return service.models()


@app.post(
    "/v1/chat",
    responses={200: {"content": {"text/event-stream": {}}, "description": "Server-Sent Events"}},
)
async def chat(body: ChatRequest) -> EventSourceResponse:
    # Streams events: delta (a piece of the answer), then done (the answer and the totals)
    # or error (its kind and a short message). The stream is built here instead of by
    # FastAPI's own event streaming: there a closed connection did not reach this code, so
    # the model kept writing. Here it cancels the stream, which closes the answer at once
    history = [Turn(turn.role, turn.content) for turn in body.history]
    events = service.chat(body.message, history)

    async def stream() -> AsyncIterator[bytes]:
        try:
            # Each event is read in a worker thread, so the server stays free meanwhile
            while (event := await anyio.to_thread.run_sync(next, events, None)) is not None:
                data = json.dumps(asdict(event), ensure_ascii=False)
                yield format_sse_event(event=EVENT_NAMES[type(event)], data_str=data)
        finally:
            # Closing the events stops the model call. The shield lets the close finish
            # although the stream itself was cancelled
            with anyio.CancelScope(shield=True):
                await anyio.to_thread.run_sync(events.close)

    return EventSourceResponse(stream())
