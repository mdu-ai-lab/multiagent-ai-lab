# Data cards

| Field | Value |
|---|---|
| Purpose | Source, licence, size, content and use of every public evaluation dataset |
| Status | Proposed |
| Last updated | 2026-11-20 |
| Source of truth | [WORK_PLAN.md](../WORK_PLAN.md) v1.10 |
| Related documents | [Test plan](../09-testing/test-plan.md), [configs/eval/datasets.yaml](../../configs/eval/datasets.yaml) |

> Implementation status: see docs/WORK_PLAN.md, section 1 (current state). Test results are in docs/HANDOVER.md.

## How the datasets are fetched

- configs/eval/datasets.yaml pins every file by its address, size and SHA-256. Hugging Face addresses name a fixed revision.
- `uv run python -m mrag.eval_data download` fetches the files into data/public/ (not in Git) and unpacks the archives. `uv run python -m mrag.eval_data verify` checks every file again.
- A hash marked "source" is published by Hugging Face. A hash marked "measured" was measured once by streaming the file on 20 November 2026, because the source publishes no SHA-256.
- Only the files the evaluation needs are fetched: no training splits (the plan does no training) and no ready-made page images (step 3.4 renders them).
- Downloaded on 20 November 2026: 24 files, 6.56 GB. With the unpacked archives the folder holds 11 GB.
- Licences were read at their sources on 20 November 2026. The counts below were counted in the downloaded files on the same day.
- 2.2 builds the dev and test sets from the pools named below, split by document.

## LongDocURL

| Item | Detail |
|---|---|
| Source | Hugging Face dengchao/LongDocURL at revision 5c96dbe9055f |
| Licence | Apache 2.0 (Hugging Face card). The PDFs are web documents that the authors took from Common Crawl (crawl CC-MAIN-2021-31, through digitalcorpora.org, paper section 3.2.1). The dataset licence covers the questions and labels. Each PDF keeps the copyright of its owner, which was not checked one by one |
| Files | 2 question files (16.4 MB) and pdf_files.tar.gz (2.63 GB) |
| Content | 2,325 questions over 396 English PDFs of 51 to 149 pages (median 78) of 8 types, for example research reports, manuals, books, theses and meeting minutes. Each question has its answer, answer format, evidence pages and evidence types (text, layout, figure, table) |
| Use | Document Q&A, retrieval, figures and tables (steps 4.3, 5.5) |
| Pool for 2.2 | All 2,325 questions (one public set, no official split) |
| Official scorer | Not checked yet (2.3) |
| Limits | English only. The questions and answers were made by a semi-automated pipeline and then checked automatically and by people (paper sections 3.2 and 3.3) |

## QASPER

| Item | Detail |
|---|---|
| Source | AllenAI's download server, version 0.3 (the address in the loader of Hugging Face allenai/qasper) |
| Licence | CC BY 4.0 (Hugging Face card) |
| Files | qasper-train-dev-v0.3.tgz (10.8 MB) and qasper-test-and-evaluator-v0.3.tgz (3.9 MB) |
| Content | Dev: 1,005 questions over 281 research papers. Test: 1,451 questions over 416 papers. Each answer has its evidence paragraphs. 60 dev and 79 test questions are marked unanswerable by every annotator |
| Use | Document Q&A and refusal (steps 5.5, 6.1, 6.4) |
| Pool for 2.2 | Dev and test |
| Official scorer | qasper_evaluator.py in the test archive |
| Limits | Research papers only. The full text comes as parsed paragraphs. The PDFs are not part of the download |

## TAT-DQA

| Item | Detail |
|---|---|
| Source | Google Drive folder of the authors (linked from GitHub NExTplusplus/TAT-DQA) |
| Licence | CC BY 4.0 (README of the authors' GitHub repo) |
| Files | tatdqa_dataset_dev.json, tatdqa_dataset_test_gold.json and the PDF pages of both (332 MB) |
| Content | Dev: 1,644 questions over 274 financial report documents. Test (with the answers released in January 2024): 1,663 questions over 277 documents. Answer types: arithmetic, span, multi-span and count |
| Use | Tables and calculations (steps 11.1, 11.4) |
| Pool for 2.2 | Dev and test |
| Official scorer | Not checked yet (2.3) |
| Limits | Financial reports only. Google Drive addresses can change. The pinned SHA-256 shows any change |

## CORD

| Item | Detail |
|---|---|
| Source | Hugging Face naver-clova-ix/cord-v2 at revision 7f0115a4b758 |
| Licence | CC BY 4.0 (Hugging Face card and the authors' GitHub repo) |
| Files | validation and test Parquet files (476 MB) |
| Content | 100 validation and 100 test receipt images, each with its ground truth JSON (items, prices, totals) |
| Use | Extraction and OCR (steps 3.3, 10.2, 10.3) |
| Pool for 2.2 | Validation (dev and the few-shot examples) and test |
| Official scorer | Not checked yet (2.3) |
| Limits | Indonesian receipts. 100 test receipts give wide confidence intervals |

## GovReport

| Item | Detail |
|---|---|
| Source | Hugging Face launch/gov_report at revision 32feeaede49f (the authors' lab) |
| Licence | CC BY 4.0 (Hugging Face card of the authors' lab) |
| Files | valid and test files of the GAO and CRS parts (124 MB) |
| Content | GAO: 612 valid and 611 test reports with their highlights pages. CRS: 362 valid and 362 test reports with expert summaries. Each report has its title and dates |
| Use | Long-document summary (steps 9.1, 9.3) |
| Pool for 2.2 | Valid and test |
| Official scorer | None. Coverage and FSCR come from eval_metrics.py (2.3) |
| Limits | US government reports only |

## PeerSum

| Item | Detail |
|---|---|
| Source | Hugging Face oaimli/PeerSum at revision 08f657c7b181 (the authors) |
| Licence | Apache 2.0 (Hugging Face card of the authors). The reviews, meta-reviews and ratings come from OpenReview, whose terms release every comment, review and rating under CC BY 4.0 (openreview.net/legal/terms) |
| Files | peersum_huggingface.jsonl (476 MB) |
| Content | 14,993 papers from ICLR 2018 to 2022 and NeurIPS 2021 and 2022: 11,992 train, 1,496 val and 1,505 test. Each paper has its meta-review (the summary), its title and abstract, the acceptance result and a median of 11 comments: official reviews with a rating from 1 to 10 and a confidence, author answers and public comments (rating -1) |
| Use | Review summary (steps 9.2, 9.3). Replaces SPACE (Q4) |
| Pool for 2.2 | Val and test |
| Official scorer | None |
| Limits | Reviews of scientific papers, not of products or hotels. A meta-review is written for an accept or reject decision. The comments carry no dates, so the "trend over time" statistic of 9.2 cannot be tested on PeerSum |

## 2WikiMultihopQA

| Item | Detail |
|---|---|
| Source | Dropbox link in the README of GitHub Alab-NII/2wikimultihop (data.zip) |
| Licence | Apache 2.0 (licence file of the authors' GitHub repo). Built from Wikipedia and Wikidata |
| Files | data.zip (246 MB) with train, dev and test |
| Content | Dev: 12,576 questions with answers, supporting facts and evidence triples, of 4 types (compositional, comparison, bridge comparison, inference). The test file has no answers (0 of 12,576) |
| Use | GraphRAG (steps 9A.3, 9A.5) |
| Pool for 2.2 | Dev only |
| Official scorer | In the authors' GitHub repo (checked in 2.3) |
| Limits | Dropbox addresses can change. The pinned SHA-256 shows any change |

## MuSiQue

| Item | Detail |
|---|---|
| Source | Google Drive file of the authors (linked from GitHub StonyBrookNLP/musique), version 1.0 |
| Licence | CC BY 4.0 (README of the authors' GitHub repo) |
| Files | musique_data_v1.0.zip (272 MB) |
| Content | MuSiQue-Ans dev: 2,417 answerable questions. MuSiQue-Full dev: 4,834 questions, half of them unanswerable. The test files have no answers |
| Use | GraphRAG and refusal on multi-hop questions (steps 9A.5, 6.4) |
| Pool for 2.2 | Dev only |
| Official scorer | evaluate_v1.0.py in the authors' GitHub repo (checked in 2.3) |
| Limits | The authors warn that some single-hop questions also appear in the training sets of the datasets MuSiQue was built from |

## LibriSpeech (test-clean and test-other)

| Item | Detail |
|---|---|
| Source | Hugging Face openslr/librispeech_asr at revision 71cacbfb7e23 |
| Licence | CC BY 4.0 (Hugging Face card) |
| Files | test-clean and test-other Parquet files (683 MB) |
| Content | test-clean: 2,620 read English sentences by 40 speakers. test-other: 2,939 sentences by 33 speakers, harder to recognise. Each has its transcript |
| Use | Speech to text, word error rate (step 14.1) |
| Pool for 2.2 | Both files as test sets. They are already the standard test split |
| Official scorer | None. Word error rate comes from eval_metrics.py |
| Limits | Read audiobooks, clearer than lectures or meetings |

## AMI meetings (headset microphones, test)

| Item | Detail |
|---|---|
| Source | Hugging Face edinburghcstr/ami at revision 46f28f2503e2, the ihm (headset) test split |
| Licence | CC BY 4.0 (Hugging Face card) |
| Files | 4 Parquet files (1.29 GB) |
| Content | 12,643 spoken segments from 16 meetings, 8.68 hours, with transcripts, times and speaker IDs |
| Use | Speech to text on meetings, close to lectures (steps 14.1, 14.2) |
| Pool for 2.2 | The test split |
| Official scorer | None. Word error rate comes from eval_metrics.py |
| Limits | English meetings only. Headset audio is cleaner than a room microphone |

## Not downloaded

- SPACE: no licence stated for its data (Q4). PeerSum replaces it.
- MMLongBench-Doc (stretch in section 13): not part of this download.
- FLEURS Swedish: only if Q6 brings Swedish into v1.
