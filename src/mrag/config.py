# Settings for every profile (mac, gpu, demo, ci, company).
# Values come from environment variables first, then the .env file, then the defaults below.
# Print the active settings with: uv run python -m mrag.config

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/mrag/config.py -> the repo root is two folders up from src/mrag
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MRAG_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

    # Which machine we run on. Model backend and storage are chosen from this later
    profile: Literal["mac", "gpu", "demo", "ci", "company"] = "mac"

    # Holds private/, public/, annotations/ and the SQLite file. A relative path is
    # read from the repo root, so commands work from any folder
    data_dir: Path = Path("data")

    # Hugging Face model cache. Read from HF_HOME (no MRAG_ prefix) so the Hugging Face
    # tools and this config use the same variable. None means the Hugging Face default
    hf_home: Path | None = Field(default=None, validation_alias="HF_HOME")

    # Empty means SQLite at <data_dir>/app.db. A PostgreSQL URL here switches the database
    database_url: str = ""

    # Service addresses. Only the Mac itself, nothing listens on the network
    model_server_url: str = "http://127.0.0.1:8080/v1"
    qdrant_url: str = "http://127.0.0.1:6333"
    # Port 5000 is taken by the macOS AirPlay Receiver, so MLflow uses 5001
    mlflow_tracking_uri: str = "http://127.0.0.1:5001"

    # Mac model server: the llama-server program and the folder with the GGUF files
    # converted locally. Both live outside the repo. None means not set on this machine
    llama_server: Path | None = None
    models_dir: Path | None = None

    @model_validator(mode="after")
    def fill_paths(self) -> "Settings":
        if not self.data_dir.is_absolute():
            self.data_dir = PROJECT_ROOT / self.data_dir
        if not self.database_url:
            self.database_url = f"sqlite:///{self.data_dir / 'app.db'}"
        return self


@lru_cache
def get_settings() -> Settings:
    # Read once per process. Tests can call get_settings.cache_clear()
    return Settings()


if __name__ == "__main__":
    for name, value in get_settings().model_dump().items():
        print(f"{name}: {value}")
