# The HTTP API of the platform under /v1, served by FastAPI. Experimental until the API is
# frozen: paths and fields may still change. Start it with: make api
# The functions live in service.py. This file only turns HTTP into calls and back

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from importlib.metadata import version
from typing import Literal

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
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


@app.post("/v1/chat", response_class=EventSourceResponse)
def chat(body: ChatRequest) -> Iterator[ServerSentEvent]:
    # Streams events: delta (a piece of the answer), then done (the answer and the totals)
    # or error (its kind and a short message)
    history = [Turn(turn.role, turn.content) for turn in body.history]
    for event in service.chat(body.message, history):
        yield ServerSentEvent(event=EVENT_NAMES[type(event)], data=asdict(event))
