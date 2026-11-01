# Real calls through the Mac model server (llama-swap). Skipped when it is not running.
# Start it first as described in docs/HANDOVER.md, then: uv run pytest -m mac

import json
import math
import urllib.request

import pytest

from mrag.config import get_settings
from mrag.llm_client import get_client, image_part


def server_running():
    try:
        with urllib.request.urlopen(f"{get_settings().model_server_url}/models", timeout=2):
            return True
    except OSError:
        return False


pytestmark = [pytest.mark.mac,
              pytest.mark.skipif(not server_running(), reason="llama-swap is not running")]

QUESTION = [{"role": "user", "content": "What is the capital of Sweden? Answer in one short sentence."}]


@pytest.fixture(scope="module")
def client():
    get_client.cache_clear()
    return get_client("mac")


def test_text_chat(client):
    result = client.chat(QUESTION, max_tokens=100)
    assert "Stockholm" in result.text
    assert result.usage is not None and result.usage.completion_tokens > 0


def test_chat_stream(client):
    pieces = list(client.chat_stream(QUESTION, max_tokens=100))
    assert len(pieces) > 1
    assert "Stockholm" in "".join(pieces)


def test_thinking_switch(client):
    result = client.chat(QUESTION, max_tokens=1500, thinking=True)
    assert result.reasoning
    assert "Stockholm" in result.text


def test_image_chat(client, red_blue_png):
    messages = [{"role": "user", "content": [
        {"type": "text", "text": "Which two colours are in this picture? One short sentence."},
        image_part(red_blue_png)]}]
    text = client.chat(messages, max_tokens=60).text.lower()
    assert "red" in text and "blue" in text


def test_json_schema(client):
    schema = {"type": "object", "properties": {"city": {"type": "string"},
                                               "country": {"type": "string"}},
              "required": ["city", "country"], "additionalProperties": False}
    messages = [{"role": "user", "content": "Extract the city and country from: "
                 "Stockholm is the capital of Sweden."}]
    data = json.loads(client.chat(messages, max_tokens=200, json_schema=schema).text)
    assert data == {"city": "Stockholm", "country": "Sweden"}


def test_embedding(client):
    vectors = client.embed(["What is the capital of Sweden?",
                            "Stockholm is the capital city of Sweden.",
                            "A python is a large snake."])

    def cosine(a, b):
        return sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))

    assert len(vectors) == 3 and len(vectors[0]) == 2048
    assert cosine(vectors[0], vectors[1]) > cosine(vectors[0], vectors[2]) + 0.3


def test_rerank(client):
    results = client.rerank("What is the capital of Sweden?",
                            ["A python is a large snake.",
                             "Stockholm is the capital city of Sweden.",
                             "Oslo is the capital of Norway."])
    assert results[0].index == 1
    assert results[0].score > results[1].score > 0
