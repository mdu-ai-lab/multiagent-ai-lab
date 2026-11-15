# Context building: the messages for the model within the token budget of the profile.
# Tokens are counted exactly with the pinned Qwen3.5 tokenizer, including the chat format
# that the model server adds around every turn. Download the tokenizer once with:
# uv run python -m mrag.harness.context

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from mrag.config import get_settings
from mrag.harness.settings import HarnessError, load
from mrag.llm_client import InputTooLongError, Message

# What the Qwen3.5 chat template (chat_template.jinja at the pinned revision) writes around a
# text turn and, with thinking off, before the answer
TURN = "<|im_start|>{role}\n{content}<|im_end|>\n"
ANSWER_START = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


@dataclass(frozen=True)
class Turn:
    role: Literal["user", "assistant"]
    content: str


def tokenizer_file() -> Path:
    # Downloads the pinned file once into the Hugging Face cache and checks it on every load
    ref = load().tokenizer
    hf_home = get_settings().hf_home
    path = Path(
        hf_hub_download(
            ref.source,
            ref.file,
            revision=ref.revision,
            cache_dir=hf_home / "hub" if hf_home else None,
        )
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != ref.sha256:
        raise HarnessError(f"{path} has SHA-256 {digest}, pinned {ref.sha256}")
    return path


@lru_cache
def tokenizer() -> Tokenizer:
    return Tokenizer.from_file(str(tokenizer_file()))


def count(text: str) -> int:
    return len(tokenizer().encode(text, add_special_tokens=False).ids)


def turn_tokens(message: Message) -> int:
    # The template trims each turn. Its special tokens separate the turns, so the tokens of
    # the whole prompt are the sum of the tokens of its turns
    return count(TURN.format(role=message["role"], content=str(message["content"]).strip()))


def prompt_tokens(messages: list[Message]) -> int:
    return sum(turn_tokens(message) for message in messages) + count(ANSWER_START)


def build_messages(system: str, history: list[Turn], message: str, budget: int) -> list[Message]:
    # The system prompt and the new message always go in. Earlier turns follow from the
    # newest back while the prompt stays within the budget. Older turns are left out
    first: Message = {"role": "system", "content": system}
    last: Message = {"role": "user", "content": message}
    used = prompt_tokens([first, last])
    if used > budget:
        raise InputTooLongError(
            f"The message needs {used} tokens with the system prompt, the budget is {budget}"
        )
    kept: list[Message] = []
    for turn in reversed(history):
        earlier: Message = {"role": turn.role, "content": turn.content}
        tokens = turn_tokens(earlier)
        if used + tokens > budget:
            break
        used += tokens
        kept.append(earlier)
    return [first, *reversed(kept), last]


if __name__ == "__main__":
    print(f"Tokenizer checked: {tokenizer_file()}")
    print("Tokens of a one-question prompt:", prompt_tokens([{"role": "user", "content": "Hi"}]))
