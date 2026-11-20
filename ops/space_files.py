# Builds the folder that is uploaded to the demo Space: the app and its Space card, the
# platform code, the configs the code reads and requirements.txt with the exact versions of
# uv.lock. Only these files, so nothing else from the repo can reach the Space.
# Run: uv run python ops/space_files.py <folder>

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Repo path -> path in the Space
FILES = {
    "demo/app.py": "app.py",
    "demo/chat.py": "chat.py",
    "demo/README.md": "README.md",
    "configs/models.yaml": "configs/models.yaml",
    "configs/harness.yaml": "configs/harness.yaml",
}
FOLDERS = {"src/mrag": "src/mrag", "configs/prompts": "configs/prompts"}
# The platform and the demo group, without the dev tools and without hashes. spaces is left
# out because a ZeroGPU Space installs its own version of it next to Gradio
EXPORT = [
    "uv", "export", "--frozen", "--no-dev", "--group", "demo", "--no-emit-project",
    "--no-hashes", "--format", "requirements-txt", "--quiet", "--no-emit-package", "spaces",
]  # fmt: skip


def build(folder: Path) -> list[Path]:
    # Returns the files written. An existing folder is replaced
    if folder.exists():
        shutil.rmtree(folder)
    for source, target in FILES.items():
        (folder / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, folder / target)
    for source, target in FOLDERS.items():
        shutil.copytree(
            ROOT / source, folder / target, ignore=shutil.ignore_patterns("__pycache__")
        )
    requirements = subprocess.run(EXPORT, cwd=ROOT, check=True, capture_output=True, text=True)
    (folder / "requirements.txt").write_text(requirements.stdout)
    return sorted(path for path in folder.rglob("*") if path.is_file())


if __name__ == "__main__":
    files = build(Path(sys.argv[1]))
    print(f"{len(files)} files for the Space")
