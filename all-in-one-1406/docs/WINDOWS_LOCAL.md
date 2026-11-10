# LOP2 Windows Local Production — all 1,406 source candidates

**Status:** Executable local runner and persistence verified with tests. **Source content outputs remain unapproved AI drafts.** No paid storage or paid AI account is required if you install an Ollama vision model locally.

## Install once

1. Install **Python 3.11+** (Windows 64-bit), enable PATH/py launcher.
2. Install **Ollama for Windows** from its official website, start it and run `ollama pull qwen2.5vl:7b` in PowerShell. This downloads a sizeable model once and requires enough free SSD and RAM; the actual speed depends on CPU/GPU. If you prefer a different vision-capable model, set `LOP2_LOCAL_MODEL` in Windows environment variables. The model must follow structured JSON output with image input. GPU unknown = speed not guaranteed.
3. Extract both ZIP archives into the same folder such as `D:\LOP2_1406\`:
   - source code ZIP, containing `RUN_ALL.bat`, `CHECK_ONLY.bat`, `BACKUP_NOW.bat`, and `all-in-one-1406/`
   - private input ZIP, containing `PRIVATE_INPUTS/` with `SOURCE_1406.csv`, `SGK_T1.pdf`, `SGK_T2.pdf`, `VBT_T1.pdf`, `VBT_T2.pdf`.
4. Double-click `CHECK_ONLY.bat` to verify source locks without using any model or API.
5. Double-click **`RUN_ALL.bat`**. It checks the source, local Ollama availability, then traverses the complete manifest with checkpoint after every major stage and a backup every 5 records.
6. A crash/power loss: re-run `RUN_ALL.bat` with the *same source files and campaign ID*. Finished items are skipped, page/vision checkpoints are reused.

## Private data boundaries

`PRIVATE_INPUTS/`, `LOCAL_STATE/`, `BACKUPS/` must never be committed to **public GitHub**. Original books/derived content, page crops and passwords stay on your Windows SSD.

## Paths

- `LOCAL_STATE/checkpoint.sqlite3`: SQLite transactional per-question state and audit events, `PRAGMA synchronous=FULL` and WAL.
- `LOCAL_STATE/objects/`: original page/crop evidence, vision extraction snapshots and machine draft JSON, written with fsync and atomic replace.
- `LOCAL_STATE/summary.json`: current progress and counts; no source text.
- `BACKUPS/checkpoint.sqlite3`, `BACKUPS/objects/`, `BACKUPS/events.jsonl`: online SQLite snapshot and incremental file copy. **Same-drive backup is not protection against disk failure or ransomware**. For disaster recovery copy entire BACKUPS folder to a separate SSD/USB drive when the run is stopped, or configure an external backup folder before running. Do not sync source material to an unapproved shared cloud folder.

## Interpretation of progress

- `DRAFT_READY`: a machine-proposed source-associated draft; **not source-certified, not N9, not N10, not releasable**.
- `DRAFT_REVIEW_REQUIRED`: unverified visual or content ambiguity in a draft.
- `EXCEPTION`: machine could not safely convert record; inspect the reason code in SQLite/events. Does not block the next record.
- `SOURCE_PROCESSING_REQUIRED`: an earlier status from historical metadata checks, not production.

The local model may return incorrect slots, crop positions, or answers. This workflow does NOT independently prove source truth or run real browser N9. Those must be added before release. A 1,406/1,406 completed traversal is not 1,406 approved questions.

## Notes

- Default model is `qwen2.5vl:7b`, but availability, hardware speed and structured output compliance must be checked locally. If not installed, `RUN_ALL.bat` fails fast without destroying checkpoints.
- User's 32 GB RAM is generally sufficient for Python/PDF extraction + a moderate quantized local multimodal model, but available GPU and SSD space remain unknown.
- GitHub hosts **code only**. Do not configure a self-hosted runner against this public repo without first hardening/restricting actions.

## Restore backup after disk/problem

1. Close **all** `RUN_ALL.bat` / `BACKUP_NOW.bat` windows.
2. Double-click `RESTORE_BACKUP.bat` and explicitly confirm.
3. Restore performs a SQLite integrity check and copies checkpoint/evidence from the backup. It preserves the existing `LOCAL_STATE` in a timestamped sibling folder first.
4. Run `RUN_ALL.bat` again to resume.

A process-level lock refuses two concurrent runner executions. Evidence files are immutable and checkpoints are transactional. Backup should ideally be on a **different physical SSD**; change the `BACKUP` setting at the top of `RUN_ALL.bat` to a second drive's folder to protect against main-drive failure.

## Real-time trace views

- `LOCAL_STATE/records.csv`: current status for every **attempted** source ID (`DRAFT_READY`, `DRAFT_REVIEW_REQUIRED`, `EXCEPTION`, or in-progress). This is a derived report regenerated after each 5-item chunk, not the transaction journal.
- `LOCAL_STATE/events.jsonl`: chronological append-only event **export** regenerated from the authoritative SQLite event table after each chunk.
- Even if a process is killed between chunk exports, `checkpoint.sqlite3` retains the last completed per-stage transaction and will regenerate the reports at the next checkpoint.