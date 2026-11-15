# The chat logic of the live demo, without the page itself, so it can be tested without
# Gradio. Every message goes to service.chat(), the same agent harness as the API.

from collections.abc import Iterator
from typing import Any

from mrag import harness, service
from mrag.harness.context import Turn

# Shown on the page. The numbers are those of Hugging Face's ZeroGPU documentation
QUOTA_NOTE = (
    "This demo runs on a shared free GPU (Hugging Face ZeroGPU). Every visitor has a small "
    "amount of GPU time per day: 2 minutes without a Hugging Face account and 5 minutes when "
    "signed in with a free account. It starts again 24 hours after the first use."
)
LOCAL_NOTE = "This chat runs on this Mac with the local model server (llama-swap)."


def text_of(content: Any) -> str:
    # Gradio gives the text of a turn as a list of parts: [{"type": "text", "text": "..."}]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def turns_from(history: list[dict[str, Any]]) -> list[Turn]:
    # The earlier turns as the harness takes them. Turns without text (files) are left out
    turns = []
    for item in history:
        role, text = item.get("role"), text_of(item.get("content"))
        if role in ("user", "assistant") and text.strip():
            turns.append(Turn(role, text))
    return turns


def answer(message: str, history: list[dict[str, Any]]) -> Iterator[str]:
    # Gradio shows the whole answer so far at every step, so each step yields all the text
    text = ""
    for event in service.chat(message, turns_from(history)):
        if isinstance(event, harness.Delta):
            text += event.text
            yield text
        elif isinstance(event, harness.Error):
            stop = f"(The answer stopped: {event.message})"
            yield f"{text}\n\n{stop}" if text else stop
