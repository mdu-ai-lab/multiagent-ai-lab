# Real calls through llm_client.py to llama-server with the small CI model (profile ci in
# configs/models.yaml). CI starts the server on port 8080 first, then runs:
#   uv run pytest -m ci_model
# There is no skip on purpose: when these tests are asked for, a missing server is a failure.

import pytest

from mrag import tracing
from mrag.llm_client import get_client

pytestmark = pytest.mark.ci_model

QUESTION = [
    {"role": "user", "content": "What is the capital of Sweden? Answer in one short sentence."}
]


@pytest.fixture(scope="module")
def client():
    get_client.cache_clear()
    return get_client("ci")


def test_text_chat(client):
    result = client.chat(QUESTION, max_tokens=100)
    assert "Stockholm" in result.text
    assert result.usage is not None and result.usage.completion_tokens > 0


def test_chat_stream_reports_tokens(client):
    with tracing.request("chat", {"question": "capital"}) as totals:
        text = "".join(client.chat_stream(QUESTION, max_tokens=100))
    assert "Stockholm" in text
    assert totals.model_calls == 1
    assert totals.input_tokens > 0
    assert totals.output_tokens > 0
