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
- Only the files the evaluation needs are fetched: no training splits (the plan does no training) and no ready-made page images (step 3.4 renders them). The speech sets come with their official dev splits, so their test sets stay whole.
- Downloaded on 20 November 2026: 40 files of 15 datasets, 9.51 GB. With the unpacked archives the folder holds 15 GB.
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

## LibriSpeech (clean and other, dev and test)

| Item | Detail |
|---|---|
| Source | Hugging Face openslr/librispeech_asr at revision 71cacbfb7e23 |
| Licence | CC BY 4.0 (Hugging Face card) |
| Files | test-clean, test-other, dev-clean and dev-other Parquet files (1.34 GB) |
| Content | test-clean: 2,620 read English sentences by 40 speakers. test-other: 2,939 sentences by 33 speakers, harder to recognise. dev-clean: 2,703 sentences by 40 speakers. dev-other: 2,864 sentences by 33 speakers. Each has its transcript |
| Use | Speech to text, word error rate (step 14.1) |
| Pool for 2.2 | The official dev and test splits |
| Official scorer | None. Word error rate comes from eval_metrics.py |
| Limits | Read audiobooks, clearer than lectures or meetings |

## AMI meetings (headset microphones, dev and test)

| Item | Detail |
|---|---|
| Source | Hugging Face edinburghcstr/ami at revision 46f28f2503e2, the ihm (headset) validation and test splits |
| Licence | CC BY 4.0 (Hugging Face card) |
| Files | 9 Parquet files (2.87 GB) |
| Content | Test: 12,643 spoken segments from 16 meetings, 8.68 hours. Dev (validation): 13,098 segments from 18 meetings, 8.94 hours. Each segment has its transcript, times and speaker ID. Dev and test share no meeting |
| Use | Speech to text on meetings, close to lectures (steps 14.1, 14.2) |
| Pool for 2.2 | The official dev and test splits |
| Official scorer | None. Word error rate comes from eval_metrics.py |
| Limits | English meetings only. Headset audio is cleaner than a room microphone |

## ScandiQA (Swedish part)

| Item | Detail |
|---|---|
| Source | Hugging Face alexandrainst/scandi-qa at revision 0bfc5269714a |
| Licence | CC BY-SA 4.0 (Hugging Face card). Share-alike applies to changed copies that are shared. The test sets are rebuilt on the Mac and never published |
| Files | data/sv/val.jsonl and data/sv/test.jsonl (2.9 MB) |
| Content | Val: 500 and test: 500 Swedish questions, each with a Wikipedia passage and the answer span. 211 val and 210 test passages do not hold the answer (has_answer false). The card states 750 and 749. The files hold 500 each |
| Use | Document Q&A and refusal in Swedish (steps 6.1, 6.4) |
| Pool for 2.2 | Val and test |
| Official scorer | Not checked yet (2.3) |
| Limits | The passages were machine-translated from English Wikipedia (the dataset's code calls DeepL and Google Translate). The questions and answers come from MKQA and were translated by people. It tests translated Swedish, not text first written in Swedish |

## Belebele (Swedish part)

| Item | Detail |
|---|---|
| Source | Hugging Face facebook/belebele at revision 7899cdfa4e1e |
| Licence | CC BY-SA 4.0 (README of the authors' GitHub repo facebookresearch/belebele). The authors' training set has another licence and is not used |
| Files | swe_Latn.jsonl (0.9 MB) |
| Content | 900 questions over 488 Swedish passages, each with 4 choices and the number of the right one. The passages come from FLORES texts of Wikinews (351 questions), Wikibooks (276) and Wikivoyage (273) and were translated by people |
| Use | Reading a Swedish passage and answering (step 6.1) |
| Pool for 2.2 | All 900 (one test set) |
| Official scorer | None needed: accuracy of the chosen number |
| Limits | Multiple choice with short passages. It does not test free answers or citations |

## MKQA (Swedish part)

| Item | Detail |
|---|---|
| Source | GitHub apple/ml-mkqa at commit f964fe1bac4d, dataset/mkqa.jsonl.gz |
| Licence | CC BY-SA 3.0 (README of the authors' GitHub repo). The Hugging Face card says CC BY 3.0. The authors' text is followed |
| Files | mkqa.jsonl.gz (11.9 MB), one file with all 26 languages |
| Content | 10,000 questions, each with its Swedish wording and Swedish answers. 1,427 have the answer type unanswerable. The other types: entity (4,218), long answer (1,815), date (1,174), number (485), number with unit (394), short phrase (349) and yes or no (138) |
| Use | Questions without documents and refusal in Swedish (steps 2.4, 6.4) and later web search (Phase 8) |
| Pool for 2.2 | All 10,000 (one public set) |
| Official scorer | mkqa_eval.py in the authors' GitHub repo (checked in 2.3) |
| Limits | No documents: it tests knowledge and refusal, not reading. The questions come from Natural Questions in English and were translated by people |

## SweFAQ

| Item | Detail |
|---|---|
| Source | Språkbanken, the SuperLim 2.0.5 collection (SuperLim-2.0.5.zip, updated 14 September 2026), folder swefaq |
| Licence | CC BY 4.0 (Språkbanken) |
| Files | SuperLim-2.0.5.zip (67.5 MB). Only its swefaq folder is used. The archive also holds the other SuperLim tasks, which are not used. Its swedn folder holds only a documentation sheet and a table of statistics, no articles. The older swefaq.zip is not used, because it still bundles the SweDN articles that were withdrawn at the request of their copyright holder |
| Content | Dev: 110 and test: 109 Swedish questions in 10 categories each. Each question comes with all answers of its category (a median of 13 to 14) and the index of the right one. The questions and answers come from the FAQs of Swedish authorities such as Försäkringskassan and 1177 (9 sources, documentation sheet) |
| Use | Search and answer matching in Swedish (steps 5.3, 5.5) |
| Pool for 2.2 | Dev and test (the official split keeps the categories apart) |
| Official scorer | The documentation sheet names Krippendorff's pseudoalpha, computed from the accuracy |
| Limits | Small: 109 test questions give wide confidence intervals. Its files are a little smaller than those in the older swefaq.zip. The difference was not checked |

## FLEURS (Swedish part, dev and test)

| Item | Detail |
|---|---|
| Source | Hugging Face google/fleurs at revision 70bb2e84b976, data/sv_se |
| Licence | CC BY 4.0 (Hugging Face card) |
| Files | test.tsv, audio/test.tar.gz, dev.tsv and audio/dev.tar.gz (627.8 MB) |
| Content | Test: 759 recordings (2.33 hours, 16 kHz) of 341 different Swedish sentences, 636 of male voices and 123 of female voices. Dev: 330 recordings (0.98 hours) of 149 sentences. Each recording has its transcript. Dev and test share no sentence |
| Use | Speech to text in Swedish (steps 14.1, 14.2) |
| Pool for 2.2 | The official dev and test splits |
| Official scorer | None. Word error rate comes from eval_metrics.py |
| Limits | Read sentences, not free speech. Most recordings are of male voices |

## Not downloaded

- SPACE: no licence stated for its data (Q4). PeerSum replaces it.
- SweDN (Swedish news summaries): withdrawn by Språkbanken at the request of the copyright holder. No Swedish summary set is used.
- MMLongBench-Doc (stretch in section 13): not part of this download.
