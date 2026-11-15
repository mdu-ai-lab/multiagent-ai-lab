# Harness settings per profile from configs/harness.yaml: the context size of the profile's
# model server, the cap on answer tokens and the time limit of a request. Also the pinned
# tokenizer that counts tokens for the budget

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from mrag.config import PROJECT_ROOT, Profile

HARNESS_FILE = PROJECT_ROOT / "configs" / "harness.yaml"


class HarnessError(Exception):
    pass


class TokenizerRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    file: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ProfileSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_tokens: int = Field(gt=0)
    answer_tokens: int = Field(gt=0)
    time_limit_s: float = Field(gt=0)

    @model_validator(mode="after")
    def room_for_a_prompt(self) -> "ProfileSettings":
        if self.answer_tokens >= self.context_tokens:
            raise ValueError("answer_tokens must be smaller than context_tokens")
        return self

    @property
    def prompt_budget(self) -> int:
        # The prompt gets what the answer leaves free in the context
        return self.context_tokens - self.answer_tokens


class HarnessSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tokenizer: TokenizerRef
    profiles: dict[Profile, ProfileSettings]


@lru_cache
def load(path: Path = HARNESS_FILE) -> HarnessSettings:
    try:
        return HarnessSettings.model_validate(yaml.safe_load(path.read_text()))
    except ValidationError as error:
        raise HarnessError(f"{path.name} is not valid: {error}") from error


def for_profile(profile: str, path: Path = HARNESS_FILE) -> ProfileSettings:
    for name, settings in load(path).profiles.items():
        if name == profile:
            return settings
    raise HarnessError(f"Profile '{profile}' has no harness settings in {path.name} yet")
