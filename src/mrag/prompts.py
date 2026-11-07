# Prompts live as text files in configs/prompts/<name>.txt, so they are reviewed and backed
# up with the code. In the mac profile every text is also a version in the MLflow prompt
# registry: a changed file becomes a new version the first time it is loaded. Without MLflow
# (other profiles, or the server is off) the version is the file's fingerprint.
# Placeholders are written {{name}}, as in MLflow.

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import mlflow

from mrag import tracing
from mrag.config import PROJECT_ROOT

PROMPTS_DIR = PROJECT_ROOT / "configs" / "prompts"
PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class PromptError(Exception):
    pass


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class Prompt:
    name: str
    template: str
    # MLflow version number, or "file-<fingerprint>" when MLflow is not used
    version: str

    @property
    def variables(self) -> set[str]:
        return set(PLACEHOLDER.findall(self.template))

    def format(self, **values: str) -> str:
        # Every use is recorded, so each trace and run shows the prompt version it used
        missing = self.variables - set(values)
        if missing:
            raise PromptError(f"{self.name}: missing values for {sorted(missing)}")
        tracing.record_prompt(self.name, self.version)
        return PLACEHOLDER.sub(lambda match: str(values[match.group(1)]), self.template)


def registry_version(name: str, template: str) -> str:
    # Reuses the newest MLflow version when its text is the same, otherwise adds a version.
    # link_to_model=False: the project does not use MLflow's app versions
    latest = mlflow.genai.load_prompt(name, allow_missing=True, link_to_model=False)
    if latest is not None and latest.template == template:
        return str(latest.version)
    created = mlflow.genai.register_prompt(
        name,
        template,
        commit_message=f"configs/prompts/{name}.txt",
        tags={"sha256": fingerprint(template)},
    )
    return str(created.version)


@lru_cache
def load(name: str, prompts_dir: Path = PROMPTS_DIR) -> Prompt:
    # Loaded once per process. A changed file is picked up at the next start
    path = prompts_dir / f"{name}.txt"
    if not path.exists():
        raise PromptError(f"No prompt file {path}")
    template = path.read_text()
    version = f"file-{fingerprint(template)[:12]}"
    if tracing.enabled() and tracing.server_reachable():
        version = registry_version(name, template)
    return Prompt(name, template, version)
