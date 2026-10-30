# Phase 2 — Iteration 2: Sheet-driven items and stable question IDs

Implementation branch: `phase1-data-api-20261030` (production `main` unchanged).

## Implemented
- Adapter reads and sorts `QUESTIONS` per known section; additions/removals/reorders work within the existing 10 section containers.
- `Script_LessonAdapter.html` maps each rendered card `data-prob-id` to the immutable `question_id` before `bindAndRestoreLevelState` runs.
- Migrates position-based draft and rewarded keys on first structured render separately for each level. New input drafts use the stable ID.
- Rejects duplicate IDs, orphan rows and unknown question types.
- Prevents reusing an illustration belonging to a different positional word problem after reorder.
- Existing renderer and scoring flows remain in place; no changes to live deployment, multi-student auth or pedagogical review status.

## Static validation (30 Oct 2026)
Read back 51 structured question rows from Google Sheets: 16 vertical, 9 mental, 8 word, 18 hidden-digit. Duplicate IDs 0, math inconsistencies 0.
This is NOT a browser test. No add/reorder/delete test was executed on the live sheet because that would alter approved demo content.

## Known constraints / next test
- Section containers still fixed for the ten Bài 20 groups. A brand-new section requires a generic registry renderer.
- Existing reset/randomize actions still use legacy section identifiers. Rewards for newly generated questions need their own attempt/run IDs.
- Word-problem inline illustrations are omitted if reordering makes the original positional art association ambiguous; proper asset IDs are pending.
- Manual QA: Pull branch into test Apps Script; test move one question within one section, add then remove a test question, inspect stable drafts after reload and switch levels, run all 51 inputs, revert Sheet changes. Use a **copy** of the sheet for mutations where possible.
- Textbook/source verification remains PENDING.

## Acceptance gate
Do not merge to main until developer QA passes: no JS exception, source flag unchanged, 51/51 cards shown, stable draft on reordering, correct 4-type scoring, regeneration semantics.
