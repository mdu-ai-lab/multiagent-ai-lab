# Builds the evaluation test sets from the pinned datasets in data/public/ into
# data/testsets/<dataset>/dev.jsonl, test.jsonl and regression.jsonl. Their counts and SHA-256
# go into the manifest configs/eval/testsets.json.
# Each line is one question in one shared format. Document text is not copied: source names
# the pinned file and the place inside it. A rebuild gives byte-identical files.
# Official dev and test splits are kept where they share no document. The other datasets are
# split by document with a hash of a fixed key, about 20% dev. The regression set is a fixed
# sample of dev, kept in the mix of its strata. Test is used only for final scores.
# Run: uv run python -m mrag.eval_sets build | verify

import argparse
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from mrag.config import PROJECT_ROOT, get_settings
from mrag.eval_data import CATALOG_FILE, sha256_of

BUILDER_VERSION = "1"
MANIFEST_FILE = PROJECT_ROOT / "configs" / "eval" / "testsets.json"
SPLIT_SALT = "mrag-split-1"
REGRESSION_SALT = "mrag-regression-1"
DEV_PERCENT = 20
REGRESSION_SIZE = 400
# One summary takes much longer than one answer, so the regression sets of the two
# summary datasets are smaller
REGRESSION_SIZE_SUMMARY = 100

Route = Literal["chat", "qa", "summary", "extract", "calc", "graph", "audio"]
Split = Literal["dev", "test"]


class SetError(Exception):
    pass


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # A file inside data/public/ and the place of this question in it
    path: str
    locator: str


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    dataset: str
    split: Split
    language: Literal["en", "sv", "id"]
    route: Route
    task: str
    # The document key that decides the split, so a document is never in both dev and test
    group: str
    question: str | None
    source: Source
    # Every accepted reference answer, as the dataset gives it. An unanswerable item expects a
    # refusal. MuSiQue still keeps the answer of the answerable twin there
    answers: list[JsonValue] = Field(default_factory=list)
    answerable: bool = True
    choices: list[str] | None = None
    correct: int | None = None
    evidence: list[str] = Field(default_factory=list)
    reference: str | None = None
    target: JsonValue = None
    meta: dict[str, JsonValue] = Field(default_factory=dict)


def in_dev(dataset: str, key: str) -> bool:
    digest = hashlib.sha256(f"{SPLIT_SALT}:{dataset}:{key}".encode()).hexdigest()
    return int(digest[:8], 16) % 100 < DEV_PERCENT


def hashed_split(dataset: str, key: str) -> Split:
    return "dev" if in_dev(dataset, key) else "test"


def jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def parquet_rows(path: Path, columns: list[str]) -> list[dict[str, Any]]:
    # pyarrow is needed only here, so the rest of the package works without it
    import pyarrow.parquet as pq

    rows: list[dict[str, Any]] = pq.read_table(path, columns=columns).to_pylist()
    return rows


def relative(root: Path, path: Path) -> str:
    if not path.is_file():
        raise SetError(f"missing source file: {path}")
    return path.relative_to(root).as_posix()


def only(root: Path, pattern: str) -> Path:
    found = sorted(root.glob(pattern))
    if len(found) != 1:
        raise SetError(f"expected one file for {pattern}, found {len(found)}")
    return found[0]


def text_of(sections: Any) -> str:
    # GovReport stores sections with paragraphs and subsections. Paragraph text in order
    if isinstance(sections, dict):
        sections = [sections]
    parts: list[str] = []
    for section in sections or []:
        parts.extend(str(paragraph) for paragraph in section.get("paragraphs", []))
        parts.extend(filter(None, [text_of(section.get("subsections", []))]))
    return "\n\n".join(part for part in parts if part.strip())


def longdocurl(root: Path) -> Iterator[Item]:
    questions = root / "longdocurl" / "LongDocURL_public_with_subtask_category.jsonl"
    pdfs = {path.stem: path for path in (root / "longdocurl" / "pdf_files").rglob("*.pdf")}
    for row in jsonl(questions):
        doc = str(row["doc_no"])
        if doc not in pdfs:
            raise SetError(f"longdocurl: no PDF for document {doc}")
        yield Item(
            id=f"longdocurl:{row['question_id']}",
            dataset="longdocurl",
            split=hashed_split("longdocurl", doc),
            language="en",
            route="qa",
            task="qa",
            group=doc,
            question=row["question"],
            source=Source(path=relative(root, pdfs[doc]), locator=doc),
            answers=[row["answer"]],
            answerable=row["answer"] != "Not answerable",
            evidence=[f"page {page}" for page in row["evidence_pages"]],
            meta={
                "answer_format": row["answer_format"],
                "question_type": row["question_type"],
                "task_tag": row["task_tag"],
                "sub_tasks": "|".join(row["subTask"]),
                "evidence_sources": "|".join(row["evidence_sources"]),
                "total_pages": row["total_pages"],
            },
        )


def qasper_references(qa: dict[str, Any]) -> tuple[list[JsonValue], list[str], list[str]]:
    # The same reference answers as the official scorer qasper_evaluator.py builds
    answers: list[JsonValue] = []
    kinds: list[str] = []
    evidence: list[str] = []
    for annotation in qa["answers"]:
        answer = annotation["answer"]
        if answer["unanswerable"]:
            answers.append("Unanswerable")
            kinds.append("none")
            continue
        if answer["extractive_spans"]:
            answers.append(", ".join(answer["extractive_spans"]))
            kinds.append("extractive")
        elif answer["free_form_answer"]:
            answers.append(answer["free_form_answer"])
            kinds.append("abstractive")
        elif answer["yes_no"] is not None:
            answers.append("Yes" if answer["yes_no"] else "No")
            kinds.append("boolean")
        else:
            raise SetError(f"qasper: an annotation of {qa['question_id']} has no answer")
        evidence.extend(text for text in answer["evidence"] if text not in evidence)
    return answers, kinds, evidence


def qasper(root: Path) -> Iterator[Item]:
    files: dict[Split, Path] = {
        "dev": root / "qasper" / "qasper-train-dev-v0.3" / "qasper-dev-v0.3.json",
        "test": root / "qasper" / "qasper-test-and-evaluator-v0.3" / "qasper-test-v0.3.json",
    }
    for split, path in files.items():
        papers = json.loads(path.read_text(encoding="utf-8"))
        for paper_id, paper in papers.items():
            for qa in paper["qas"]:
                answers, kinds, evidence = qasper_references(qa)
                yield Item(
                    id=f"qasper:{qa['question_id']}",
                    dataset="qasper",
                    split=split,
                    language="en",
                    route="qa",
                    task="qa",
                    group=paper_id,
                    question=qa["question"],
                    source=Source(path=relative(root, path), locator=paper_id),
                    answers=answers,
                    # Unanswerable only when every annotator found no answer
                    answerable=any(kind != "none" for kind in kinds),
                    evidence=evidence,
                    meta={"answer_types": "|".join(kinds)},
                )


def tatdqa(root: Path) -> Iterator[Item]:
    files: dict[Split, tuple[str, str]] = {
        "dev": ("tatdqa_dataset_dev.json", "tatdqa_docs_dev/dev"),
        "test": ("tatdqa_dataset_test_gold.json", "tatdqa_docs_test/test"),
    }
    for split, (name, folder) in files.items():
        for doc in json.loads((root / "tatdqa" / name).read_text(encoding="utf-8")):
            uid = doc["doc"]["uid"]
            page = doc["doc"]["page"]
            pdf = root / "tatdqa" / folder / f"{uid}.pdf"
            for question in doc["questions"]:
                yield Item(
                    id=f"tatdqa:{question['uid']}",
                    dataset="tatdqa",
                    split=split,
                    language="en",
                    route="calc",
                    task="table_qa",
                    group=uid,
                    question=question["question"],
                    source=Source(path=relative(root, pdf), locator=f"{uid}#page={page}"),
                    answers=[question["answer"]],
                    meta={
                        "answer_type": question["answer_type"],
                        "scale": question["scale"],
                        "derivation": question["derivation"],
                        "report": doc["doc"]["source"],
                    },
                )


def cord(root: Path) -> Iterator[Item]:
    files: dict[Split, str] = {
        "dev": "validation-00000-of-00001.parquet",
        "test": "test-00000-of-00001.parquet",
    }
    for split, name in files.items():
        path = root / "cord" / name
        for row_number, row in enumerate(parquet_rows(path, ["ground_truth"])):
            truth = json.loads(row["ground_truth"])
            key = f"{split}-{row_number}"
            yield Item(
                id=f"cord:{key}",
                dataset="cord",
                split=split,
                language="id",
                route="extract",
                task="receipt_json",
                group=key,
                question=None,
                source=Source(path=relative(root, path), locator=f"row={row_number}"),
                target=truth["gt_parse"],
            )


def govreport(root: Path) -> Iterator[Item]:
    files: dict[Split, list[str]] = {
        "dev": ["gao_valid.jsonl", "crs_valid.jsonl"],
        "test": ["gao_test.jsonl", "crs_test.jsonl"],
    }
    for split, names in files.items():
        for name in names:
            part = name.split("_")[0]
            path = root / "govreport" / name
            for row in jsonl(path):
                if part == "gao":
                    reference = text_of(row["highlight"])
                else:
                    reference = text_of_list(row["summary"])
                yield Item(
                    id=f"govreport:{row['id']}",
                    dataset="govreport",
                    split=split,
                    language="en",
                    route="summary",
                    task="long_document_summary",
                    group=row["id"],
                    question=None,
                    source=Source(path=relative(root, path), locator=row["id"]),
                    reference=reference,
                    meta={"part": part, "title": row["title"]},
                )


def text_of_list(paragraphs: Any) -> str:
    return "\n\n".join(str(text) for text in paragraphs if str(text).strip())


def peersum(root: Path) -> Iterator[Item]:
    path = root / "peersum" / "peersum_huggingface.jsonl"
    splits: dict[str, Split] = {"val": "dev", "test": "test"}
    for row in jsonl(path):
        if row["label"] not in splits:
            continue
        ratings = [rating for rating in row["review_ratings"] if rating >= 0]
        yield Item(
            id=f"peersum:{row['paper_id']}",
            dataset="peersum",
            split=splits[row["label"]],
            language="en",
            route="summary",
            task="review_summary",
            group=row["paper_id"],
            question=None,
            source=Source(path=relative(root, path), locator=row["paper_id"]),
            reference=row["meta_review"],
            meta={
                "acceptance": row["paper_acceptance"],
                "comments": len(row["review_ids"]),
                "rated_reviews": len(ratings),
            },
        )


def wikimultihop(root: Path) -> Iterator[Item]:
    path = root / "2wikimultihopqa" / "data" / "data" / "dev.json"
    for row in json.loads(path.read_text(encoding="utf-8")):
        yield Item(
            id=f"2wikimultihopqa:{row['_id']}",
            dataset="2wikimultihopqa",
            split=hashed_split("2wikimultihopqa", row["_id"]),
            language="en",
            route="graph",
            task="multi_hop",
            group=row["_id"],
            question=row["question"],
            source=Source(path=relative(root, path), locator=row["_id"]),
            answers=[row["answer"]],
            evidence=[f"{title}#{sentence}" for title, sentence in row["supporting_facts"]],
            meta={"type": row["type"]},
        )


def musique(root: Path) -> Iterator[Item]:
    path = root / "musique" / "musique_data_v1.0" / "data" / "musique_full_v1.0_dev.jsonl"
    for row in jsonl(path):
        # MuSiQue-Full holds each question twice: answerable and an unanswerable twin with
        # the same id. The split key is the id, so a pair stays together
        state = "answerable" if row["answerable"] else "unanswerable"
        yield Item(
            id=f"musique:{row['id']}:{state}",
            dataset="musique",
            split=hashed_split("musique", row["id"]),
            language="en",
            route="graph",
            task="multi_hop",
            group=row["id"],
            question=row["question"],
            source=Source(path=relative(root, path), locator=f"{row['id']}#{state}"),
            answers=[row["answer"], *row["answer_aliases"]],
            answerable=row["answerable"],
            evidence=[part["title"] for part in row["paragraphs"] if part["is_supporting"]],
            meta={"hops": row["id"].split("hop")[0]},
        )


def scandiqa(root: Path) -> Iterator[Item]:
    # The official val and test sets share Wikipedia articles, so both are split again by
    # article
    for name in ("val.jsonl", "test.jsonl"):
        path = root / "scandiqa-sv" / name
        for row in jsonl(path):
            yield Item(
                id=f"scandiqa-sv:{row['id']}",
                dataset="scandiqa-sv",
                split=hashed_split("scandiqa-sv", row["title_en"]),
                language="sv",
                route="qa",
                task="qa",
                group=row["title_en"],
                question=row["question"],
                source=Source(path=relative(root, path), locator=str(row["id"])),
                answers=[row["answer"]] if row["has_answer"] else [],
                answerable=row["has_answer"],
                meta={"official_split": name.removesuffix(".jsonl")},
            )


def belebele(root: Path) -> Iterator[Item]:
    path = root / "belebele-sv" / "swe_Latn.jsonl"
    for row in jsonl(path):
        key = f"{row['link']}#{row['question_number']}"
        yield Item(
            id=f"belebele-sv:{key}",
            dataset="belebele-sv",
            split=hashed_split("belebele-sv", row["link"]),
            language="sv",
            route="qa",
            task="multiple_choice",
            group=row["link"],
            question=row["question"],
            source=Source(path=relative(root, path), locator=key),
            choices=[row[f"mc_answer{number}"] for number in range(1, 5)],
            # The position in choices, counted from 0
            correct=int(row["correct_answer_num"]) - 1,
        )


def mkqa(root: Path) -> Iterator[Item]:
    path = root / "mkqa" / "mkqa.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    for row in rows:
        key = str(row["example_id"])
        found = row["answers"]["sv"]
        kinds = [answer["type"] for answer in found]
        answers: list[JsonValue] = []
        for answer in found:
            for text in [answer.get("text"), *answer.get("aliases", [])]:
                if text and text not in answers:
                    answers.append(text)
        yield Item(
            id=f"mkqa:{key}",
            dataset="mkqa",
            split=hashed_split("mkqa", key),
            language="sv",
            route="chat",
            task="closed_book",
            group=key,
            question=row["queries"]["sv"],
            source=Source(path=relative(root, path), locator=key),
            answers=answers,
            answerable="unanswerable" not in kinds,
            meta={"answer_types": "|".join(kinds)},
        )


def swefaq(root: Path) -> Iterator[Item]:
    folder = only(root / "swefaq", "**/swefaq/swefaq_dev.jsonl").parent
    for split in ("dev", "test"):
        path = folder / f"swefaq_{split}.jsonl"
        for number, row in enumerate(jsonl(path)):
            yield Item(
                id=f"swefaq:{split}-{number}",
                dataset="swefaq",
                split="dev" if split == "dev" else "test",
                language="sv",
                route="qa",
                task="answer_selection",
                group=str(row["category_id"]),
                question=row["question"],
                source=Source(path=relative(root, path), locator=f"line={number}"),
                choices=list(row["candidate_answers"]),
                correct=int(row["label"]),
                meta={"category": row["meta"]["category"], "source": row["meta"]["source"]},
            )


def librispeech(root: Path) -> Iterator[Item]:
    files: dict[str, Split] = {
        "dev-clean.parquet": "dev",
        "dev-other.parquet": "dev",
        "test-clean.parquet": "test",
        "test-other.parquet": "test",
    }
    for name, split in files.items():
        path = root / "librispeech" / name
        for row in parquet_rows(path, ["id", "text", "speaker_id"]):
            yield Item(
                id=f"librispeech:{row['id']}",
                dataset="librispeech",
                split=split,
                language="en",
                route="audio",
                task="transcription",
                group=str(row["speaker_id"]),
                question=None,
                source=Source(path=relative(root, path), locator=row["id"]),
                reference=row["text"],
                meta={"subset": name.split("-")[1].removesuffix(".parquet")},
            )


def ami(root: Path) -> Iterator[Item]:
    columns = ["meeting_id", "audio_id", "text", "begin_time", "end_time", "speaker_id"]
    for pattern, split in (("ihm-validation-*.parquet", "dev"), ("ihm-test-*.parquet", "test")):
        for path in sorted((root / "ami").glob(pattern)):
            for row in parquet_rows(path, columns):
                yield Item(
                    id=f"ami:{row['audio_id']}",
                    dataset="ami",
                    split="dev" if split == "dev" else "test",
                    language="en",
                    route="audio",
                    task="transcription",
                    group=row["meeting_id"],
                    question=None,
                    source=Source(path=relative(root, path), locator=row["audio_id"]),
                    reference=row["text"],
                    meta={
                        "speaker": row["speaker_id"],
                        "seconds": round(row["end_time"] - row["begin_time"], 2),
                    },
                )


def fleurs(root: Path) -> Iterator[Item]:
    for split in ("dev", "test"):
        path = root / "fleurs-sv" / f"{split}.tsv"
        audio = root / "fleurs-sv" / split / split
        with path.open(encoding="utf-8") as handle:
            # Tab separated without quoting: quote marks belong to the sentences
            rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
        for sentence, file, raw, normalized, _chars, samples, gender in rows:
            yield Item(
                id=f"fleurs-sv:{file.removesuffix('.wav')}",
                dataset="fleurs-sv",
                split="dev" if split == "dev" else "test",
                language="sv",
                route="audio",
                task="transcription",
                group=sentence,
                question=None,
                source=Source(path=relative(root, audio / file), locator=file),
                reference=raw,
                meta={
                    "normalized": normalized,
                    "seconds": round(int(samples) / 16000, 2),
                    "gender": gender,
                },
            )


BUILDERS: dict[str, Callable[[Path], Iterator[Item]]] = {
    "longdocurl": longdocurl,
    "qasper": qasper,
    "tatdqa": tatdqa,
    "cord": cord,
    "govreport": govreport,
    "peersum": peersum,
    "2wikimultihopqa": wikimultihop,
    "musique": musique,
    "scandiqa-sv": scandiqa,
    "belebele-sv": belebele,
    "mkqa": mkqa,
    "swefaq": swefaq,
    "librispeech": librispeech,
    "ami": ami,
    "fleurs-sv": fleurs,
}


def stratum(item: Item) -> str:
    # The regression set keeps the mix of these keys from dev
    kind = item.meta.get("answer_format") or item.meta.get("answer_type") or item.meta.get("type")
    return f"{item.answerable}|{kind or ''}"


def order(item: Item) -> str:
    return hashlib.sha256(f"{REGRESSION_SALT}:{item.id}".encode()).hexdigest()


def regression(items: list[Item], size: int) -> list[Item]:
    # A fixed sample of dev in the proportions of its strata (largest remainder), each
    # stratum taken in the order of a hash of the question id
    if len(items) <= size:
        return list(items)
    groups: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        groups[stratum(item)].append(item)
    quotas = {key: size * len(members) / len(items) for key, members in groups.items()}
    taken = {key: int(quota) for key, quota in quotas.items()}
    rest = size - sum(taken.values())
    for key in sorted(quotas, key=lambda key: (-(quotas[key] - taken[key]), key))[:rest]:
        taken[key] += 1
    chosen: list[Item] = []
    for key, members in groups.items():
        chosen.extend(sorted(members, key=order)[: taken[key]])
    return chosen


def line(item: Item) -> str:
    data = item.model_dump(mode="json")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def check_groups(name: str, items: list[Item]) -> None:
    ids = [item.id for item in items]
    if len(ids) != len(set(ids)):
        raise SetError(f"{name}: a question id is used twice")
    splits: dict[str, set[str]] = defaultdict(set)
    for item in items:
        splits[item.group].add(item.split)
    mixed = sorted(group for group, found in splits.items() if len(found) > 1)
    if mixed:
        raise SetError(f"{name}: {len(mixed)} documents are in both dev and test, first {mixed[0]}")


def build_dataset(name: str, root: Path) -> dict[str, list[Item]]:
    items = sorted(BUILDERS[name](root), key=lambda item: item.id)
    check_groups(name, items)
    sets = {split: [item for item in items if item.split == split] for split in ("dev", "test")}
    size = REGRESSION_SIZE_SUMMARY if items and items[0].route == "summary" else REGRESSION_SIZE
    sets["regression"] = sorted(regression(sets["dev"], size), key=lambda item: item.id)
    return sets


def write(sets: dict[str, list[Item]], folder: Path) -> dict[str, dict[str, Any]]:
    folder.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict[str, Any]] = {}
    for name, items in sets.items():
        path = folder / f"{name}.jsonl"
        path.write_text("".join(line(item) + "\n" for item in items), encoding="utf-8")
        entries[name] = {
            "items": len(items),
            "unanswerable": sum(not item.answerable for item in items),
            "sha256": sha256_of(path),
        }
    return entries


def testsets_dir() -> Path:
    return get_settings().data_dir / "testsets"


def build(names: list[str], root: Path, out: Path) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "builder_version": BUILDER_VERSION,
        "datasets_yaml_sha256": sha256_of(CATALOG_FILE),
        "sets": {},
    }
    for name in names:
        entries = write(build_dataset(name, root), out / name)
        manifest["sets"][name] = entries
        counts = ", ".join(f"{split} {entry['items']}" for split, entry in entries.items())
        print(f"{name}: {counts}", flush=True)
    return manifest


def verify(manifest: dict[str, Any], out: Path) -> bool:
    all_ok = True
    for name, entries in manifest["sets"].items():
        for split, entry in entries.items():
            path = out / name / f"{split}.jsonl"
            ok = path.is_file() and sha256_of(path) == entry["sha256"]
            all_ok = all_ok and ok
            print(
                f"{'OK' if ok else 'DIFFERENT':<10} {name}/{split}.jsonl ({entry['items']} items)"
            )
    return all_ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluation test sets")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="build every test set and write the manifest")
    commands.add_parser("verify", help="check the built files against the manifest")
    args = parser.parse_args(argv)
    root = get_settings().data_dir / "public"
    try:
        if args.command == "build":
            manifest = build(list(BUILDERS), root, testsets_dir())
            text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            MANIFEST_FILE.write_text(text, encoding="utf-8")
            print(f"Manifest written: {MANIFEST_FILE}")
            return 0
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        return 0 if verify(manifest, testsets_dir()) else 1
    except SetError as error:
        print(f"Stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
