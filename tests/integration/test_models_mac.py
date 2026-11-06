# Checks that every model file the Mac model server loads has the SHA-256 pinned in
# configs/models.yaml. Reads about 11 GB from the SSD. Run with: uv run pytest -m mac

import hashlib

import pytest

from mrag.config import get_settings
from mrag.llm_client import load_models, model_file

SETTINGS = get_settings()

pytestmark = [pytest.mark.mac,
              pytest.mark.skipif(not (SETTINGS.hf_home and SETTINGS.models_dir
                                      and SETTINGS.hf_home.exists() and SETTINGS.models_dir.exists()),
                                 reason="the model folders are not on this machine")]

PINNED = [(role, ref, file_name, digest)
          for role, ref in load_models()["mac"].models.items()
          for file_name, digest in ref.files.items()]


def sha256_of(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@pytest.mark.parametrize(("role", "ref", "file_name", "digest"), PINNED,
                         ids=[file_name for _, _, file_name, _ in PINNED])
def test_model_file_matches_its_pin(role, ref, file_name, digest):
    path = model_file(ref, file_name, SETTINGS.hf_home, SETTINGS.models_dir)
    assert path.exists(), f"{role}: {path} is missing"
    assert sha256_of(path) == digest, f"{role}: {file_name} differs from configs/models.yaml"
