# LOP2 ALL-IN-ONE 1406 — Source-first Production Runner V2

**Status: implementation + mocked integration tests complete; live external storage and AI credentials NOT CONNECTED yet. Full campaign NOT ACTIVATED.** This is an isolated workspace and does not edit the Apps Script Question Engine in the repo root.

## What is implemented (real, executable Python)

- `SourceProcessor`: direct mapping from `SOURCE_1406.csv` (`bqa`, `page`, `source_file_id`), verifies all four original SGK/VBT PDF SHA-256 file hashes, 1-based page indices, creates original-page PNG evidence and optional exact bounding-box crops. This does **not** OCR or transcribe by itself.
- `VisionExtractor`: sends original page image to an externally configured, vision-capable OpenAI API model using **Responses API Structured Outputs (Pydantic)**. Explicitly separates worked examples, proposed answers, student slots, source-ID mapping uncertainty. Prompt intentionally returns `found=false` if identification is not defensible.
- `QuestionBuilder`: validates proposed question content, source geometry, distinct student slots, source-observed blanks, simple arithmetic self-checks; creates a **machine draft with immutable source evidence hashes and `release_allowed=false`**.
- `AuditStore`: S3-compatible external object storage, **event-first append-only stage events**, per-record checkpoint, immutable image/crop/model-output/JSON draft objects. Supports AWS S3 and S3-compatible endpoints; full external connectivity requires owner-provided credentials and bucket. Local backend exists for tests.
- `runner.py`: traverses all 1,406 records and 21 BQA under one campaign ID, resumes at the saved stage, avoids re-billing the model for successfully saved extractions, continues after isolated question exceptions, aborts instead of mass-failing data when credentials/quota/network infrastructure is unavailable.
- `download_inputs.py`: fetches the *private* `SOURCE_1406.csv` and four exact locked source PDF files from protected S3 to the ephemeral runner, independently verifies all PDF file hashes before processing.
- Separate protected GitHub Actions `workflow_dispatch` workflow, preflight default, `run-all` **gated** by repository variable + protected environment, max 35 candidates per job, optional automatic continuation up to 50 segments, GitHub concurrency single-writer.

## WHAT IS NOT CLAIMED

There is no independent textual source sign-off, guaranteed correct visual ID mapping, official Question Engine N9 browser pass, reviewer N10, or release N12. Drafts are **not** production questions. The workflow has **not** yet exercised live vision API or live S3 permissions; integration test uses a simulated S3 service and test extractor. The existing 2 visually transcribed B001 pilots are not automatically promoted by this new runner. Additional content QA, asset-aware renderers, N9 integration and reviewer decision remain follow-up work.

## Why the private storage is mandatory

**The repository is public.** Never commit SGK/VBT source PDFs, Working Master exports, page screenshots, student data, answer payloads, private derived data, or API tokens. Use a private S3 bucket (or Cloudflare R2 with compatible S3 endpoint) with encryption, versioning, minimal IAM access and retention policy. Github Actions artifacts are not the durable primary checkpoint.

Upload these five private files to S3 prefix `<LOP2_S3_PREFIX>/inputs/`:

```
SOURCE_1406.csv  # original 1,406-row extract, not a fake/synthetic manifest
SGK_T1.pdf       # original locked PDF 1Zfiw7... sha cb8cb303...
VBT_T1.pdf       # original locked PDF 1YIWc2... sha 7c77820b...
SGK_T2.pdf       # original locked PDF 1T8Ra... sha 044142f3...
VBT_T2.pdf       # original locked PDF 15Xy... sha 9f3b4d9f...
```

Do not publish the bucket or the objects. This repository contains only code and SHA locks.

In GitHub Settings → Environments, create `lop2-private`, restrict it to `main` and configure reviewer approval for costly runs if available. Configure environment secrets:

- `LOP2_S3_BUCKET`
- `LOP2_S3_ACCESS_KEY_ID`
- `LOP2_S3_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`

Configure environment/repository variables:

- `LOP2_S3_REGION` (`auto` for some S3-compatible services, otherwise AWS region)
- `LOP2_S3_ENDPOINT` (blank for native AWS S3, full HTTPS URL for an S3-compatible service)
- `LOP2_S3_PREFIX` (recommend `lop2-private`)
- `LOP2_VISION_MODEL` (model you have enabled with image input and Structured Outputs)
- `LOP2_ENABLE_FULL_RUN` **must remain unset or `NO`** until verified live preflight, cost budget and actual QA are approved.

## Run locally

```bash
python -m pip install -r all-in-one-1406/requirements.txt
python -m unittest discover -s all-in-one-1406/tests -v
python all-in-one-1406/runner.py --manifest /private/SOURCE_1406.csv --pdf-root /private/pdfs \
  --campaign lop2-source-v2-20261109 --store local --state-dir /private/lop2-state --mode preflight
# Production S3 run only after all keys, files and explicit approval are configured:
LOP2_ALLOW_RUN=YES python all-in-one-1406/runner.py --manifest /private/SOURCE_1406.csv \
  --pdf-root /private/pdfs --campaign lop2-source-v2-20261109 --store s3 --mode run --max-items 35
```

`run-all` must not run with a `local` store inside ephemeral GitHub Actions. In CI, external S3 objects use:

- `campaigns/<campaign>/records/<sha256(source_id)>.json` — last durable stage
- `campaigns/<campaign>/events/<sha256(source_id)>/<event_uuid>.json` — immutable per-stage events
- `campaigns/<campaign>/evidence/<sha256(source_id)>/<label>-<sha256>.png` — PDF-derived images
- `campaigns/<campaign>/drafts/<sha256(source_id)>-<sha256>.json` — raw vision and canonical draft candidates

S3 event objects are append-only *by unique key*; enable bucket versioning/object-lock or IAM restrictions if tamper-proof logs are required. Use a single campaign writer; multi-worker distributed leases are not provided in this version.

## Test of interrupted jobs

Unit tests deliberately kill the execution at `PAGE_LOCKED` and `VISION_EXTRACTED`, then recreate new store/runner instances and resume from durable checkpoints. They verify the model is not called again after a saved response; a repeat run produces no extra drafts. S3 interface is verified against a fake service, **not live AWS/R2**. A real S3 readback is performed by `preflight` on GitHub only when secrets are configured.

## Progress reporting

Use `summary.json` stored in the runner temporary environment (numeric only). The durable external status is derived from S3 records, not Actions logs. A status `DRAFT_READY` means **machine draft**, not source-proof and not runtime approval. Real review queue must be resolved independently.

## Activation gates

1. S3 private bucket exists and minimal IAM + protected GitHub environment are configured.
2. Five private input files are uploaded; actual full manifest count 1,406, 21 BQA, and 4 PDF hashes verified.
3. Real S3 preflight write-read passes and the OpenAI image-model account is tested; API usage/cost ceiling agreed.
4. A canary with genuine pages produces inspectable drafts and appropriate exceptions without exposing book content publicly.
5. Runtime adapter and genuine N9 browser QA integrated before any technical release approval; reviewer N10 stays human.
6. Only then set `LOP2_ENABLE_FULL_RUN=YES` and manually dispatch `run-all`. Automatic continuation will then resume same campaign across segmented jobs.