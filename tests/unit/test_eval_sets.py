# Unit tests for src/mrag/eval_sets.py with small made-up files in the formats of the real
# datasets. The real build runs on the downloaded data in data/public/.

import csv
import hashlib
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from mrag import eval_data, eval_sets


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def qasper_answer(**fields):
    answer = {
        "unanswerable": False,
        "extractive_spans": [],
        "yes_no": None,
        "free_form_answer": "",
        "evidence": [],
    }
    return {"answer": answer | fields}


@pytest.fixture
def root(tmp_path):
    # QASPER: one paper in dev and one in test, each with its own question ids
    dev = tmp_path / "qasper/qasper-train-dev-v0.3/qasper-dev-v0.3.json"
    test = tmp_path / "qasper/qasper-test-and-evaluator-v0.3/qasper-test-v0.3.json"
    for path, paper_id in ((dev, "P1"), (test, "P2")):
        first = [
            qasper_answer(extractive_spans=["X", "Y"], evidence=["p1"]),
            qasper_answer(unanswerable=True),
        ]
        none = [qasper_answer(unanswerable=True)]
        qas = [
            {"question_id": f"{paper_id}q1", "question": "Which data?", "answers": first},
            {"question_id": f"{paper_id}q2", "question": "Is it?", "answers": none},
        ]
        paper = {"title": "T", "abstract": "A", "full_text": [], "qas": qas}
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({paper_id: paper}))
    # MuSiQue-Full: every id twice, answerable and unanswerable
    rows = []
    for number in range(40):
        for answerable in (True, False):
            rows.append(
                {
                    "id": f"2hop__{number}_1",
                    "question": f"Q{number}",
                    "answer": "A",
                    "answer_aliases": ["a"],
                    "answerable": answerable,
                    "paragraphs": [{"title": "T", "is_supporting": True}],
                }
            )
    write_jsonl(tmp_path / "musique/musique_data_v1.0/data/musique_full_v1.0_dev.jsonl", rows)
    # ScandiQA: the same article in both official files
    for name, number in (("val.jsonl", 1), ("test.jsonl", 2)):
        write_jsonl(
            tmp_path / "scandiqa-sv" / name,
            [
                {
                    "id": number,
                    "question": "Vem?",
                    "answer": "",
                    "has_answer": False,
                    "title_en": "Same",
                }
            ],
        )
    # SweFAQ inside the SuperLim folder layout
    faq = tmp_path / "swefaq/SuperLim-2.0.5/SuperLim-2.0.5/swefaq"
    for split, category in (("dev", 1), ("test", 2)):
        write_jsonl(
            faq / f"swefaq_{split}.jsonl",
            [
                {
                    "question": "Hur?",
                    "candidate_answers": ["a", "b"],
                    "label": 1,
                    "category_id": category,
                    "meta": {"category": "c", "source": "s"},
                }
            ],
        )
    # FLEURS: tab separated, a quote mark inside the sentence
    for split, sentence in (("dev", "10"), ("test", "20")):
        audio = tmp_path / "fleurs-sv" / split / split
        audio.mkdir(parents=True)
        (audio / f"{sentence}1.wav").write_bytes(b"")
        line = f'{sentence}\t{sentence}1.wav\tHan sa "hej"\than sa hej\th a n\t16000\tMALE\n'
        (tmp_path / "fleurs-sv" / f"{split}.tsv").write_text(line)
    # CORD: Parquet with the ground truth as a JSON text
    (tmp_path / "cord").mkdir()
    for name in ("validation-00000-of-00001.parquet", "test-00000-of-00001.parquet"):
        truth = json.dumps({"gt_parse": {"total": {"total_price": "10"}}})
        pq.write_table(pa.table({"ground_truth": [truth, truth]}), tmp_path / "cord" / name)
    return tmp_path


def test_every_builder_matches_a_dataset_of_the_download_list():
    names = [dataset.name for dataset in eval_data.load_catalog().datasets]
    assert set(eval_sets.BUILDERS) == set(names)


def test_the_hash_split_is_fixed_and_near_twenty_percent():
    keys = [f"doc{number}" for number in range(10000)]
    first = [eval_sets.in_dev("x", key) for key in keys]
    assert first == [eval_sets.in_dev("x", key) for key in keys]
    assert 0.18 < sum(first) / len(keys) < 0.22


def test_qasper_references_follow_the_official_scorer(root):
    items = eval_sets.build_dataset("qasper", root)
    first = next(item for item in items["dev"] if item.id == "qasper:P1q1")
    assert first.answers == ["X, Y", "Unanswerable"]
    assert first.answerable is True
    assert first.evidence == ["p1"]
    only_none = next(item for item in items["dev"] if item.id == "qasper:P1q2")
    assert only_none.answerable is False


def test_musique_pairs_stay_in_one_split(root):
    sets = eval_sets.build_dataset("musique", root)
    for split in ("dev", "test"):
        groups = [item.group for item in sets[split]]
        assert all(groups.count(group) == 2 for group in groups)
    assert len(sets["dev"]) + len(sets["test"]) == 80


def test_scandiqa_is_split_again_by_article(root):
    sets = eval_sets.build_dataset("scandiqa-sv", root)
    splits = {item.split for item in sets["dev"] + sets["test"]}
    assert len(splits) == 1
    assert all(item.answers == [] and not item.answerable for item in sets["dev"] + sets["test"])


def test_swefaq_fleurs_and_cord_read_their_formats(root):
    faq = eval_sets.build_dataset("swefaq", root)
    assert faq["test"][0].choices == ["a", "b"] and faq["test"][0].correct == 1
    fleurs = eval_sets.build_dataset("fleurs-sv", root)
    assert fleurs["dev"][0].reference == 'Han sa "hej"'
    assert fleurs["dev"][0].meta["seconds"] == 1.0
    cord = eval_sets.build_dataset("cord", root)
    assert cord["test"][1].target == {"total": {"total_price": "10"}}
    assert cord["test"][1].source.locator == "row=1"


def test_a_document_in_both_splits_stops_the_build():
    item = {
        "dataset": "d",
        "language": "en",
        "route": "qa",
        "task": "qa",
        "group": "same",
        "question": "q",
        "source": eval_sets.Source(path="a", locator="b"),
    }
    items = [
        eval_sets.Item(id="d:1", split="dev", **item),
        eval_sets.Item(id="d:2", split="test", **item),
    ]
    with pytest.raises(eval_sets.SetError, match="in both dev and test"):
        eval_sets.check_groups("d", items)


def test_unknown_fields_are_refused():
    with pytest.raises(ValidationError):
        eval_sets.Source(path="a", locator="b", extra="c")


def make(number, answerable):
    return eval_sets.Item(
        id=f"d:{number}",
        dataset="d",
        split="dev",
        language="en",
        route="qa",
        task="qa",
        group=str(number),
        question="q",
        source=eval_sets.Source(path="a", locator=str(number)),
        answerable=answerable,
    )


def test_the_regression_set_keeps_the_mix_and_is_fixed():
    items = [make(number, number % 4 != 0) for number in range(1000)]
    chosen = eval_sets.regression(items, 400)
    assert len(chosen) == 400
    assert sum(not item.answerable for item in chosen) == 100
    assert [item.id for item in eval_sets.regression(items, 400)] == [item.id for item in chosen]
    assert eval_sets.regression(items[:10], 400) == items[:10]


def test_a_rebuild_is_byte_identical_and_verify_finds_a_change(root, tmp_path, capsys):
    names = ["qasper", "musique", "swefaq"]
    first = eval_sets.build(names, root, tmp_path / "one")
    second = eval_sets.build(names, root, tmp_path / "two")
    assert first == second
    assert (
        first["sets"]["musique"]["dev"]["items"] + first["sets"]["musique"]["test"]["items"] == 80
    )
    assert eval_sets.verify(first, tmp_path / "one") is True
    (tmp_path / "one" / "swefaq" / "test.jsonl").write_text("changed\n")
    assert eval_sets.verify(first, tmp_path / "one") is False
    assert "DIFFERENT  swefaq/test.jsonl" in capsys.readouterr().out


def test_govreport_sections_give_their_text_in_order():
    sections = {
        "paragraphs": ["one"],
        "subsections": [{"paragraphs": ["two"], "subsections": [{"paragraphs": ["three"]}]}],
    }
    assert eval_sets.text_of(sections) == "one\n\ntwo\n\nthree"


def test_a_question_id_used_twice_stops_the_build():
    with pytest.raises(eval_sets.SetError, match="used twice"):
        eval_sets.check_groups("d", [make(1, True), make(1, True)])


def test_the_regression_set_fills_its_size_when_quotas_have_remainders():
    # Three strata of 333 questions: each quota is 133.33, so one more must be added
    items = [make(number, True) for number in range(333)]
    items += [make(number, False) for number in range(333, 666)]
    items += [
        make(number, True).model_copy(update={"meta": {"answer_type": "x"}})
        for number in range(666, 999)
    ]
    assert len(eval_sets.regression(items, 400)) == 400


def fresh_row(number, verdict, question_type="fact", pages="2"):
    return [
        f"en-x-{number:02d}",
        "en",
        "arXiv x",
        pages,
        f"Question {number}?",
        "",
        "Not in the document" if question_type == "unanswerable" else "42",
        "Why",
        "number",
        question_type,
        "body",
        "quote",
        verdict,
        "",
    ]


def write_fresh(folder, rows, header=None):
    pdf = folder / "docs" / "en" / "x.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.4 made-up document")
    document = {
        "document": "arXiv x",
        "file": "docs/en/x.pdf",
        "pages": 3,
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
    }
    (folder / "documents.json").write_text(json.dumps([document]))
    with (folder / "questions.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows([header or eval_sets.FRESH_COLUMNS, *rows])
    return folder


def test_fresh_keeps_only_rows_marked_correct(tmp_path):
    rows = [
        fresh_row(1, "correct"),
        fresh_row(2, "wrong"),
        fresh_row(3, "fix"),
        fresh_row(4, "Correct ", "unanswerable", ""),
    ]
    entries = eval_sets.build_fresh(write_fresh(tmp_path / "f", rows), tmp_path / "out")
    assert entries["test"]["items"] == 2 and entries["test"]["unanswerable"] == 1
    items = list(eval_sets.jsonl(tmp_path / "out/fresh/test.jsonl"))
    assert [item["id"] for item in items] == ["fresh:en-x-01", "fresh:en-x-04"]
    assert items[0]["answers"] == ["42"] and items[0]["evidence"] == ["page 2"]
    assert items[1]["answers"] == [] and items[1]["answerable"] is False
    assert {item["split"] for item in items} == {"test"}


def test_fresh_sends_calculations_to_the_calc_route(tmp_path):
    rows = [fresh_row(1, "correct", "calculation"), fresh_row(2, "correct", "comparison")]
    items = list(eval_sets.fresh(write_fresh(tmp_path, rows)))
    assert [item.route for item in items] == ["calc", "qa"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("no verdict", "no verdict yet"),
        ("changed pdf", "missing or changed"),
        ("page outside", "page outside the document"),
        ("wrong header", "columns of questions.csv"),
        ("same id", "used twice"),
    ],
)
def test_bad_fresh_input_stops_the_build(tmp_path, change, message):
    rows = [fresh_row(1, "correct"), fresh_row(2, "" if change == "no verdict" else "correct")]
    if change == "page outside":
        rows[1] = fresh_row(2, "correct", pages="2, 4")
    if change == "same id":
        rows[1] = fresh_row(1, "wrong")
    header = [*eval_sets.FRESH_COLUMNS[:-1], "notes"] if change == "wrong header" else None
    folder = write_fresh(tmp_path, rows, header)
    if change == "changed pdf":
        (folder / "docs/en/x.pdf").write_bytes(b"%PDF-1.4 another document")
    with pytest.raises(eval_sets.SetError, match=message):
        list(eval_sets.fresh(folder))


def test_a_public_rebuild_keeps_the_fresh_entry():
    fresh_entry = {"test": {"items": 2, "unanswerable": 1, "sha256": "a"}}
    old = {"sets": {"fresh": fresh_entry, "qasper": {}}}
    manifest = eval_sets.with_local_sets({"sets": {"qasper": {"dev": {}}}}, old)
    assert manifest["sets"] == {"qasper": {"dev": {}}, "fresh": fresh_entry}
    assert eval_sets.with_local_sets({"sets": {}}, None) == {"sets": {}}


def test_verify_passes_a_local_set_that_is_not_on_this_computer(tmp_path, capsys):
    manifest = {"sets": {"fresh": {"test": {"items": 2, "unanswerable": 1, "sha256": "a"}}}}
    assert eval_sets.verify(manifest, tmp_path) is True
    assert "LOCAL" in capsys.readouterr().out
    (tmp_path / "fresh").mkdir()
    (tmp_path / "fresh" / "test.jsonl").write_text("changed\n")
    assert eval_sets.verify(manifest, tmp_path) is False
