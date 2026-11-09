# LOP2 ALL-IN-ONE 1406 — Production Runner workspace

This is a **separate, non-production workspace** for source-first conversion of 1,406 source candidates across 21 BQA groups. The existing Google Apps Script application in the repository root is not modified.

## Security boundary
This repository was **public** when this workspace was created. **Never commit** the original SGK/VBT PDFs, Working Master exports, student data, image crops, Google credentials, service-account files, OAuth tokens, or proprietary question content here. Use a private storage volume / private repository and protected CI secrets for those materials. Do not publish logs containing source book text.

## Current implementation status
- An executable **manifest traversal and audit/resume core** is included.
- Per-record durable SQLite state, append-only JSONL events, missing-input and image-page preflight exceptions, deterministic source ID de-duplication, retry via `--retry`, and batch-level summary.
- This is **not yet** an OCR or visual understanding engine, canonical question converter, validator, asset cropper or full Chromium runtime runner.
- It never marks `SOURCE_VERIFIED`, `TECH_QA_PASSED`, `N9_PASS`, `N10_PASS` or `RELEASABLE`. A completed manifest traversal is NOT completed content conversion.

## Invocation
Python 3.11+ required, standard library only.

```bash
python all-in-one-1406/runner.py --manifest /private/SOURCE_1406.csv --state-dir /private/lop2-state --run-all
python all-in-one-1406/runner.py --manifest /private/SOURCE_1406.csv --state-dir /private/lop2-state --run-all --retry
python -m unittest discover -s all-in-one-1406/tests -v
```

The manifest must contain `source_id`, `lesson_id`, `owner_batch`, `track`, `volume`, `pdf_page` and `source_sha256`. Optional `source_file_id` is used for traceability. The runner does not download private PDFs. Supply them via a separate secured ingest stage in later implementation.

## Status model
- `INPUT_VALIDATED`: valid source registry entry, not proof of exercise content
- `SOURCE_PROCESSING_REQUIRED`: source page/content/answer slot proof not complete
- `INPUT_EXCEPTION`: malformed source record or page
- `SOURCE_CONFLICT`: duplicate source ID, inconsistent identity metadata
- `TECH_READY`: reserved for future stage after successful source verification + conversion + runtime
- `RELEASABLE`: reserved for independent signed release workflow, never set automatically

## Artifact contract
`state.sqlite3` is the durable local transactional database, `events.jsonl` is an additional append-only audit trail, `summary.json` and `exceptions.csv` are generated views. Do not rely on GitHub Actions artifacts as your only checkpoint: its hosted filesystem is ephemeral. For unattended execution, use a durable external store and upload checkpoint snapshots with versioned backups. Build a single-writer claim/lease mechanism before parallel 21-BQA workers.

## Next implementation gate
Wire a genuinely source-grounded visual extraction adapter; document exact page/crop coordinates, distinguish WORKED_EXAMPLE and STUDENT_SLOT, generate canonical payloads, map original assets, and run the real Question Engine through Chromium. Any unsupported/uncertain item enters a specific exception queue; no self-sign-off for N10.
