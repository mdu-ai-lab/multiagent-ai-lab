# One client for all model calls. The profile in .env picks the backend and the model
# names in configs/models.yaml:
#   openai_server  an OpenAI-style HTTP server: llama-swap on the Mac, vLLM on GPU machines
#   transformers   models loaded inside this process, used by the demo
# Quick check (needs the model server running): uv run python -m mrag.llm_client

import base64
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import openai
import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from mrag.config import PROJECT_ROOT, get_settings

MODELS_FILE = PROJECT_ROOT / "configs" / "models.yaml"

Role = Literal["main", "helper", "embedding", "reranker"]
Message = dict[str, Any]


# Error types, so callers can react to each case (for example fall back to a smaller task)
class LLMError(Exception):
    pass


# The model server cannot be reached or did not answer in time
class ModelUnavailableError(LLMError):
    pass


# The input does not fit into the model's context size
class InputTooLongError(LLMError):
    pass


# The model server failed while working, for example out of memory
class ModelServerError(LLMError):
    pass


# The backend of this profile does not offer this feature
class NotSupportedError(LLMError):
    pass


class ModelRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    revision: str | None = None


class ProfileModels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: Literal["openai_server", "transformers"]
    models: dict[Role, ModelRef]

    @field_validator("models", mode="before")
    @classmethod
    def names_as_refs(cls, value: Any) -> Any:
        # A plain name in the YAML file is short for {name: ...}
        if isinstance(value, dict):
            return {role: {"name": ref} if isinstance(ref, str) else ref
                    for role, ref in value.items()}
        return value


def load_models(path: Path = MODELS_FILE) -> dict[str, ProfileModels]:
    data = yaml.safe_load(path.read_text()) or {}
    try:
        return {profile: ProfileModels.model_validate(entry) for profile, entry in data.items()}
    except ValidationError as error:
        raise LLMError(f"{path.name} is not valid: {error}") from error


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class ChatResult:
    text: str
    reasoning: str
    usage: Usage | None
    finish_reason: str | None


@dataclass(frozen=True)
class RerankResult:
    index: int
    score: float


def image_part(data: bytes, mime_type: str = "image/png") -> dict[str, Any]:
    # Message content part with an image, in the OpenAI chat format
    encoded = base64.b64encode(data).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}}


class LLMClient(Protocol):
    def chat(self, messages: list[Message], role: Role = "main", *, max_tokens: int = 1024,
             temperature: float = 0.0, thinking: bool = False,
             json_schema: dict[str, Any] | None = None,
             timeout: float | None = None) -> ChatResult: ...

    def chat_stream(self, messages: list[Message], role: Role = "main", *,
                    max_tokens: int = 1024, temperature: float = 0.0, thinking: bool = False,
                    timeout: float | None = None) -> Iterator[str]: ...

    def embed(self, texts: list[str], role: Role = "embedding", *,
              timeout: float | None = None) -> list[list[float]]: ...

    def rerank(self, query: str, documents: list[str], role: Role = "reranker", *,
               timeout: float | None = None) -> list[RerankResult]: ...


@contextmanager
def server_errors() -> Iterator[None]:
    # Turns errors of the openai library into the error types above
    try:
        yield
    except openai.APIConnectionError as error:  # also covers timeouts
        raise ModelUnavailableError(f"Model server not reachable: {error}") from error
    except openai.BadRequestError as error:
        if "exceed" in str(error) and "context" in str(error):
            raise InputTooLongError(str(error)) from error
        raise LLMError(str(error)) from error
    except openai.APIStatusError as error:
        if error.status_code >= 500:
            raise ModelServerError(f"Model server error {error.status_code}: {error}") from error
        raise LLMError(str(error)) from error


class OpenAIServerClient:
    def __init__(self, base_url: str, models: dict[Role, ModelRef],
                 timeout: float = 600.0, max_retries: int = 1) -> None:
        self.models = models
        # Local servers need no key. The library still requires a value
        self.client = openai.OpenAI(base_url=base_url, api_key="not-needed",
                                    timeout=timeout, max_retries=max_retries)

    def model_name(self, role: Role) -> str:
        if role not in self.models:
            raise LLMError(f"No model for role '{role}' in this profile")
        return self.models[role].name

    def chat_args(self, messages: list[Message], role: Role, max_tokens: int,
                  temperature: float, thinking: bool,
                  json_schema: dict[str, Any] | None) -> dict[str, Any]:
        args: dict[str, Any] = {
            "model": self.model_name(role),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            # Qwen chat templates read this switch. llama.cpp and vLLM pass it through
            "extra_body": {"chat_template_kwargs": {"enable_thinking": thinking}},
        }
        if json_schema is not None:
            args["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "answer", "schema": json_schema, "strict": True},
            }
        return args

    def chat(self, messages: list[Message], role: Role = "main", *, max_tokens: int = 1024,
             temperature: float = 0.0, thinking: bool = False,
             json_schema: dict[str, Any] | None = None,
             timeout: float | None = None) -> ChatResult:
        args = self.chat_args(messages, role, max_tokens, temperature, thinking, json_schema)
        with server_errors():
            response = self.client.chat.completions.create(**args, timeout=timeout)
        choice = response.choices[0]
        extra = choice.message.model_extra or {}
        usage = None
        if response.usage is not None:
            usage = Usage(response.usage.prompt_tokens, response.usage.completion_tokens)
        return ChatResult(text=choice.message.content or "",
                          reasoning=extra.get("reasoning_content") or "",
                          usage=usage, finish_reason=choice.finish_reason)

    def chat_stream(self, messages: list[Message], role: Role = "main", *,
                    max_tokens: int = 1024, temperature: float = 0.0, thinking: bool = False,
                    timeout: float | None = None) -> Iterator[str]:
        # Yields the answer text piece by piece. Reasoning text is not included
        args = self.chat_args(messages, role, max_tokens, temperature, thinking, None)
        with server_errors():
            stream = self.client.chat.completions.create(**args, stream=True, timeout=timeout)
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

    def embed(self, texts: list[str], role: Role = "embedding", *,
              timeout: float | None = None) -> list[list[float]]:
        with server_errors():
            response = self.client.embeddings.create(model=self.model_name(role), input=texts,
                                                     encoding_format="float", timeout=timeout)
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]

    def rerank(self, query: str, documents: list[str], role: Role = "reranker", *,
               timeout: float | None = None) -> list[RerankResult]:
        # Reranking is not part of the OpenAI API. llama-server and vLLM both offer /rerank
        body = {"model": self.model_name(role), "query": query, "documents": documents}
        with server_errors():
            data = cast(dict[str, Any], self.client.post(
                "/rerank", cast_to=object, body=body,
                options={"timeout": timeout} if timeout else {}))
        results = [RerankResult(index=item["index"], score=item["relevance_score"])
                   for item in data["results"]]
        return sorted(results, key=lambda result: result.score, reverse=True)


class TransformersClient:
    # Loads each model on first use. Chat only: embedding and reranking for this
    # backend come with the retrieval work of the demo
    def __init__(self, models: dict[Role, ModelRef], cache_dir: Path | None = None) -> None:
        self.models = models
        self.cache_dir = cache_dir
        self.loaded: dict[Role, tuple[Any, Any]] = {}
        self.lock = threading.Lock()

    def load(self, role: Role) -> tuple[Any, Any]:
        if role not in self.models:
            raise LLMError(f"No model for role '{role}' in this profile")
        with self.lock:
            if role not in self.loaded:
                import torch
                from transformers import AutoModelForImageTextToText, AutoProcessor

                ref = self.models[role]
                cache = str(self.cache_dir) if self.cache_dir else None
                processor = AutoProcessor.from_pretrained(ref.name, revision=ref.revision,
                                                          cache_dir=cache)
                model: Any = AutoModelForImageTextToText.from_pretrained(
                    ref.name, revision=ref.revision, cache_dir=cache, dtype="auto")
                if torch.cuda.is_available():
                    device = "cuda"
                elif torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
                self.loaded[role] = (processor, model.to(device).eval())
        return self.loaded[role]

    def inputs(self, processor: Any, model: Any, messages: list[Message],
               thinking: bool) -> Any:
        # Transformers wants {"type": "image", "url": ...} where the OpenAI format
        # has {"type": "image_url", "image_url": {"url": ...}}
        converted = []
        for message in messages:
            content = message["content"]
            if isinstance(content, str):
                parts = [{"type": "text", "text": content}]
            else:
                parts = [{"type": "image", "url": part["image_url"]["url"]}
                         if part["type"] == "image_url" else part for part in content]
            converted.append({"role": message["role"], "content": parts})
        return processor.apply_chat_template(
            converted, add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt", enable_thinking=thinking).to(model.device)

    @staticmethod
    def generate_args(max_tokens: int, temperature: float) -> dict[str, Any]:
        if temperature > 0:
            return {"max_new_tokens": max_tokens, "do_sample": True, "temperature": temperature}
        return {"max_new_tokens": max_tokens, "do_sample": False}

    def chat(self, messages: list[Message], role: Role = "main", *, max_tokens: int = 1024,
             temperature: float = 0.0, thinking: bool = False,
             json_schema: dict[str, Any] | None = None,
             timeout: float | None = None) -> ChatResult:
        if json_schema is not None:
            raise NotSupportedError("JSON schema output is not available in the transformers backend")
        processor, model = self.load(role)
        inputs = self.inputs(processor, model, messages, thinking)
        output = model.generate(**inputs, **self.generate_args(max_tokens, temperature))
        new_tokens = output[0][inputs["input_ids"].shape[1]:]
        text = processor.decode(new_tokens, skip_special_tokens=True)
        reasoning = ""
        if "</think>" in text:
            reasoning, text = text.split("</think>", 1)
            reasoning = reasoning.replace("<think>", "")
        finish = "length" if len(new_tokens) >= max_tokens else "stop"
        usage = Usage(int(inputs["input_ids"].shape[1]), len(new_tokens))
        return ChatResult(text=text.strip(), reasoning=reasoning.strip(), usage=usage,
                          finish_reason=finish)

    def chat_stream(self, messages: list[Message], role: Role = "main", *,
                    max_tokens: int = 1024, temperature: float = 0.0, thinking: bool = False,
                    timeout: float | None = None) -> Iterator[str]:
        from transformers import TextIteratorStreamer

        processor, model = self.load(role)
        inputs = self.inputs(processor, model, messages, thinking)
        streamer = TextIteratorStreamer(processor.tokenizer, skip_prompt=True,
                                        skip_special_tokens=True)
        worker = threading.Thread(target=model.generate, kwargs={
            **inputs, **self.generate_args(max_tokens, temperature), "streamer": streamer})
        worker.start()
        # With thinking on, hold back everything up to the end of the reasoning
        buffer = ""
        answer_started = not thinking
        for piece in streamer:
            if answer_started:
                if piece:
                    yield piece
                continue
            buffer += piece
            if "</think>" in buffer:
                answer_started = True
                rest = buffer.split("</think>", 1)[1].lstrip()
                if rest:
                    yield rest
        worker.join()

    def embed(self, texts: list[str], role: Role = "embedding", *,
              timeout: float | None = None) -> list[list[float]]:
        raise NotSupportedError("Embedding is not available in the transformers backend yet")

    def rerank(self, query: str, documents: list[str], role: Role = "reranker", *,
               timeout: float | None = None) -> list[RerankResult]:
        raise NotSupportedError("Reranking is not available in the transformers backend yet")


@lru_cache
def get_client(profile: str | None = None) -> LLMClient:
    # One client per profile and process. Tests can call get_client.cache_clear()
    settings = get_settings()
    name = profile or settings.profile
    profiles = load_models()
    if name not in profiles:
        raise LLMError(f"Profile '{name}' has no models in configs/models.yaml yet")
    entry = profiles[name]
    if entry.backend == "openai_server":
        return OpenAIServerClient(settings.model_server_url, entry.models)
    cache_dir = settings.hf_home / "hub" if settings.hf_home else None
    return TransformersClient(entry.models, cache_dir=cache_dir)


if __name__ == "__main__":
    reply = get_client().chat([{"role": "user", "content": "Reply with the single word: ready"}],
                              max_tokens=20)
    print(f"{get_settings().profile} profile answered: {reply.text}")
