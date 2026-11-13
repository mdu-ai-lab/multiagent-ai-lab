# Unit tests for the harness settings and the context building. Token counts use the pinned
# Qwen3.5 tokenizer: uv run python -m mrag.harness.context downloads it once.

import re

import pytest
import yaml

from mrag.config import PROJECT_ROOT
from mrag.harness import context, settings
from mrag.llm_client import InputTooLongError, load_models

PROFILES = settings.load().profiles
# Swedish, an emoji and spaces that the chat template trims
MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant. "},
    {"role": "user", "content": "Hej! Vad är huvudstaden i Sverige? 🇸🇪"},
    {"role": "assistant", "content": "  Stockholm.\n"},
    {"role": "user", "content": "And 17 times 3?\n\n  "},
]


def long_history(turns):
    return [
        context.Turn("user" if number % 2 == 0 else "assistant", f"Turn {number}: " + "word " * 300)
        for number in range(turns)
    ]


def test_every_profile_leaves_room_for_a_prompt():
    for name, profile in PROFILES.items():
        assert 0 < profile.prompt_budget < profile.context_tokens, name


def test_context_sizes_match_the_model_servers():
    # Each context size must be the one its model server really uses
    swap = yaml.safe_load((PROJECT_ROOT / "configs" / "llama-swap.yaml").read_text())
    main = swap["models"][load_models()["mac"].models["main"].name]["cmd"]
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    gpu = (PROJECT_ROOT / "ops" / "gpu_smoke.py").read_text()
    assert re.findall(r"--ctx-size (\d+)", main) == [str(PROFILES["mac"].context_tokens)]
    assert re.findall(r"--ctx-size (\d+)", ci) == [str(PROFILES["ci"].context_tokens)]
    assert re.findall(r"^CONTEXT_SIZE = (\d+)", gpu, re.MULTILINE) == [
        str(PROFILES["gpu"].context_tokens)
    ]


def test_invalid_settings_are_rejected(tmp_path):
    path = tmp_path / "harness.yaml"
    data = yaml.safe_load(settings.HARNESS_FILE.read_text())
    data["profiles"]["mac"]["answer_tokens"] = data["profiles"]["mac"]["context_tokens"]
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(settings.HarnessError, match="not valid"):
        settings.load(path)


def test_unknown_profile_is_reported():
    with pytest.raises(settings.HarnessError, match="no harness settings"):
        settings.for_profile("demo")


def test_counting_turn_by_turn_equals_the_whole_prompt():
    text = "".join(
        context.TURN.format(role=message["role"], content=message["content"].strip())
        for message in MESSAGES
    )
    assert context.prompt_tokens(MESSAGES) == context.count(text + context.ANSWER_START)
    # The chat format is counted too: each turn costs more than its text
    for message in MESSAGES:
        assert context.turn_tokens(message) > context.count(message["content"].strip())


@pytest.mark.parametrize("name", sorted(PROFILES))
def test_the_history_never_goes_over_the_budget(name):
    budget = PROFILES[name].prompt_budget
    history = long_history(60)
    messages = context.build_messages("You are helpful.", history, "Last question?", budget)
    assert context.prompt_tokens(messages) <= budget
    assert messages[0] == {"role": "system", "content": "You are helpful."}
    assert messages[-1] == {"role": "user", "content": "Last question?"}
    # Only the newest turns are kept, in their order
    kept = [message["content"] for message in messages[1:-1]]
    assert 0 < len(kept) < len(history)
    assert kept == [turn.content for turn in history[len(history) - len(kept) :]]
    # The next older turn would not have fit
    older = history[len(history) - len(kept) - 1]
    extra = context.turn_tokens({"role": older.role, "content": older.content})
    assert context.prompt_tokens(messages) + extra > budget


def test_a_short_history_is_kept_whole():
    history = long_history(4)
    messages = context.build_messages("You are helpful.", history, "Next?", 7168)
    assert [message["content"] for message in messages[1:-1]] == [turn.content for turn in history]


def test_a_message_over_the_budget_is_refused():
    with pytest.raises(InputTooLongError, match="budget is 1000"):
        context.build_messages("You are helpful.", [], "word " * 5000, 1000)
