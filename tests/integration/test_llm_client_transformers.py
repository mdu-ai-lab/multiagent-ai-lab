# Real chat through the transformers backend with a small model (Qwen3.5-0.8B, about 1.8 GB,
# downloaded once into HF_HOME). Needs the demo dependency group:
#   uv run --group demo pytest -m transformers

import pytest

from mrag.config import get_settings
from mrag.llm_client import ModelRef, TransformersClient, image_part

pytest.importorskip("transformers", minversion="5.22.1")
pytestmark = pytest.mark.transformers

SMALL_MODEL = ModelRef(name="Qwen/Qwen3.5-0.8B", revision="2fc06364715b967f1860aea9cf38778875588b17")
QUESTION = [{"role": "user", "content": "What is the capital of Sweden? Answer in one short sentence."}]


@pytest.fixture(scope="module")
def client():
    hf_home = get_settings().hf_home
    return TransformersClient({"main": SMALL_MODEL}, cache_dir=hf_home / "hub" if hf_home else None)


def test_text_chat(client):
    result = client.chat(QUESTION, max_tokens=60)
    assert "Stockholm" in result.text
    assert result.reasoning == ""


def test_chat_stream(client):
    assert "Stockholm" in "".join(client.chat_stream(QUESTION, max_tokens=60))


def test_image_chat(client, red_blue_png):
    messages = [{"role": "user", "content": [
        {"type": "text", "text": "Which two colours are in this picture? One short sentence."},
        image_part(red_blue_png)]}]
    text = client.chat(messages, max_tokens=60).text.lower()
    assert "red" in text and "blue" in text
