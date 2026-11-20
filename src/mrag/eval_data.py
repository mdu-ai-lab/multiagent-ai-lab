# Downloads the public evaluation datasets listed in configs/eval/datasets.yaml into
# data/public/<name>/ and checks every file against its pinned size and SHA-256.
# A download goes to a .part file first, continues after a cut connection and is renamed only
# when its hash matches. Archives are unpacked so that no file can land outside their folder.
# Run: uv run python -m mrag.eval_data list | download [NAME ...] | verify [NAME ...]

import argparse
import hashlib
import http.client
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mrag.config import PROJECT_ROOT, get_settings

CATALOG_FILE = PROJECT_ROOT / "configs" / "eval" / "datasets.yaml"
USER_AGENT = "multiagent-ai-lab-eval-data"
TIMEOUT_S = 60
TRIES = 3
PAUSE_S = 10.0
CHUNK = 1024 * 1024
ARCHIVE_ENDINGS = (".tar.gz", ".tgz", ".zip")


class DataError(Exception):
    pass


class DataFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    url: str
    size: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hash_from: Literal["source", "measured"]
    unpack: bool = False

    @field_validator("path")
    @classmethod
    def plain_relative_path(cls, value: str) -> str:
        # Only a simple file name inside the dataset folder, so a list entry can never write
        # anywhere else on the disk
        parts = PurePosixPath(value).parts
        if not parts or value.startswith("/") or ".." in parts or "\\" in value:
            raise ValueError(f"path must stay inside the dataset folder: {value!r}")
        return value

    @field_validator("url")
    @classmethod
    def https_only(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError(f"url must use https: {value!r}")
        return value

    @model_validator(mode="after")
    def unpack_needs_archive(self) -> "DataFile":
        if self.unpack and not self.path.endswith(ARCHIVE_ENDINGS):
            raise ValueError(f"unpack needs a .tar.gz, .tgz or .zip file: {self.path}")
        return self


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str
    use: str
    licence: str
    licence_source: str
    files: list[DataFile] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_paths(self) -> "Dataset":
        paths = [item.path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError(f"{self.name}: a file path is listed twice")
        return self

    @property
    def size(self) -> int:
        return sum(item.size for item in self.files)


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    datasets: list[Dataset] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_names(self) -> "Catalog":
        names = [dataset.name for dataset in self.datasets]
        if len(names) != len(set(names)):
            raise ValueError("a dataset name is listed twice")
        return self

    def pick(self, names: list[str]) -> list[Dataset]:
        # All datasets when no name is given, otherwise the named ones in list order
        if not names:
            return list(self.datasets)
        known = {dataset.name: dataset for dataset in self.datasets}
        unknown = [name for name in names if name not in known]
        if unknown:
            raise DataError(f"unknown dataset: {', '.join(unknown)}. Known: {', '.join(known)}")
        return [known[name] for name in names]


def load_catalog(path: Path = CATALOG_FILE) -> Catalog:
    return Catalog.model_validate(yaml.safe_load(path.read_text()))


def public_dir() -> Path:
    return get_settings().data_dir / "public"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(CHUNK):
            digest.update(block)
    return digest.hexdigest()


def is_verified(item: DataFile, target: Path) -> bool:
    if not target.is_file() or target.stat().st_size != item.size:
        return False
    return sha256_of(target) == item.sha256


def fetch_into(item: DataFile, part: Path) -> None:
    # Appends the missing bytes to the .part file. A server that ignores the range request
    # sends the whole file, so the .part file then starts again from zero
    have = part.stat().st_size if part.exists() else 0
    if have > item.size:
        part.unlink()
        have = 0
    if have == item.size:
        return
    headers = {"User-Agent": USER_AGENT}
    if have:
        headers["Range"] = f"bytes={have}-"
    request = urllib.request.Request(item.url, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        mode = "ab" if have and response.status == 206 else "wb"
        with part.open(mode) as handle:
            shutil.copyfileobj(response, handle, CHUNK)
    # A dropped connection can end the read without an error, so a short file counts as a cut
    # connection and the next try continues it
    got = part.stat().st_size
    if got < item.size:
        raise http.client.IncompleteRead(b"", item.size - got)


def download_file(item: DataFile, folder: Path) -> str:
    target = folder / item.path
    if is_verified(item, target):
        return "already verified"
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    for attempt in range(TRIES):
        try:
            fetch_into(item, part)
            break
        except urllib.error.HTTPError as error:
            # A client error such as 404 does not get better with another try
            if error.code < 500 or attempt == TRIES - 1:
                raise DataError(f"{item.path}: HTTP {error.code} from {item.url}") from error
        except (OSError, http.client.HTTPException) as error:
            if attempt == TRIES - 1:
                raise DataError(f"{item.path}: download failed: {error}") from error
        time.sleep(PAUSE_S)
    size = part.stat().st_size
    found = sha256_of(part)
    if size != item.size or found != item.sha256:
        part.unlink()
        raise DataError(
            f"{item.path}: got {size} bytes with SHA-256 {found}, expected {item.size} bytes "
            f"with {item.sha256}. The file was deleted"
        )
    part.rename(target)
    return "downloaded and verified"


def unpacked_folder(item: DataFile, folder: Path) -> Path:
    name = item.path
    for ending in ARCHIVE_ENDINGS:
        name = name.removesuffix(ending)
    return folder / name


def unpack(item: DataFile, folder: Path) -> str:
    # A marker with the archive's hash shows that this exact archive was unpacked completely.
    # Unpacking goes to a temporary folder first, so a stop half way leaves nothing behind
    destination = unpacked_folder(item, folder)
    marker = destination / f".unpacked-{item.sha256[:12]}"
    if marker.exists():
        return "already unpacked"
    archive = folder / item.path
    temporary = destination.with_name(destination.name + ".unpacking")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    if item.path.endswith(".zip"):
        safe_unzip(archive, temporary)
    else:
        with tarfile.open(archive) as tar:
            # The data filter refuses absolute paths, paths with .., links that point outside
            # and special files
            tar.extractall(temporary, filter="data")
    if destination.exists():
        shutil.rmtree(destination)
    temporary.rename(destination)
    marker.touch()
    return "unpacked"


def safe_unzip(archive: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            place = (destination / member.filename).resolve()
            if not place.is_relative_to(root):
                raise DataError(f"{archive.name}: {member.filename!r} lands outside its folder")
        bundle.extractall(destination)


def download(datasets: list[Dataset], root: Path) -> None:
    for dataset in datasets:
        folder = root / dataset.name
        for item in dataset.files:
            print(f"{dataset.name}/{item.path} ({item.size / 1e6:.1f} MB): ", end="", flush=True)
            print(download_file(item, folder), flush=True)
            if item.unpack:
                print(f"{dataset.name}/{item.path}: {unpack(item, folder)}", flush=True)


def verify(datasets: list[Dataset], root: Path) -> bool:
    # Checks every listed file on disk again. Missing or changed files make the result False
    all_ok = True
    for dataset in datasets:
        for item in dataset.files:
            target = root / dataset.name / item.path
            if not target.is_file():
                state, ok = "MISSING", False
            elif is_verified(item, target):
                state, ok = "OK", True
            else:
                state, ok = "WRONG HASH OR SIZE", False
            all_ok = all_ok and ok
            print(f"{state:<18} {dataset.name}/{item.path}")
    return all_ok


def show(datasets: list[Dataset], root: Path) -> None:
    for dataset in datasets:
        on_disk = sum((root / dataset.name / item.path).is_file() for item in dataset.files)
        print(
            f"{dataset.name:<16} {dataset.licence:<11} {dataset.size / 1e6:>9.1f} MB "
            f"{on_disk}/{len(dataset.files)} files on disk  {dataset.use}"
        )
    total = sum(dataset.size for dataset in datasets)
    print(f"Total {total / 1e9:.2f} GB in {root}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Public evaluation datasets")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="show every dataset with its licence and size")
    for name, text in (("download", "download and check"), ("verify", "check the files on disk")):
        command = commands.add_parser(name, help=text)
        command.add_argument("names", nargs="*", help="dataset names (default: all)")
    args = parser.parse_args(argv)
    catalog = load_catalog()
    root = public_dir()
    try:
        if args.command == "list":
            show(catalog.datasets, root)
            return 0
        datasets = catalog.pick(args.names)
        if args.command == "download":
            download(datasets, root)
            return 0
        return 0 if verify(datasets, root) else 1
    except DataError as error:
        print(f"Stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
