# Phase 1 — Structured Lesson Data (2026-10-30)

## Source preservation
- Production/demo `main` untouched, frozen at `7856afe2d18317c4e0a6ef4f9f08005f81ceb088`.
- Development branch: `phase1-data-api-20261030`.
- Original Google Sheets two tabs `BaiTap_PhepTinh`, `BaiTap_LoiVan` preserved.
- Google Sheets backup made separately before structural changes.

## Data
- `LESSONS` 1 record, `SECTIONS` 10, `QUESTIONS` 51.
- `CONTENT` 1 reconstructed teaching note pending review.
- `SOURCES` 3 provisional references; textbook editions/pages unverified.
- `ASSETS` header only; chibi asset mappings deferred.
- `MIGRATION_QA` contains migration counts and static check status.

Question inventory:
- LV1: 6 vertical additions, 9 mental expressions, 2 word problems.
- LV2: 6 word problems.
- LV3: 10 vertical additions, 18 hidden-digit puzzles.
- Total: 51.

## API
- New `getLessonData('MATH_B020')` returns structured JSON, sections, questions, content, source and asset registries.
- `getLessonData()` without an ID delegates to legacy endpoint for old UI compatibility.
- `runLessonQA('MATH_B020')` can be run in the Apps Script editor *after syncing this branch to an Apps Script deployment*.
- The API is **not deployed** merely because the branch was committed; no runtime smoke test is claimed.

## Automated verification
- In migration: 51 question IDs created deterministically, numeric 2-operand and 3-term answers checked, hidden-digit puzzles reconstructed and validated.
- On API read: validation checks duplicate/missing IDs, required fields, section linkage, JSON parse, arithmetic and puzzle correctness.
- Educational source fidelity has **not** been checked against actual SGK/SBT/reference books.
- Rendering/client migration belongs to Phase 2.

## Caution
- Static theory from the original render component is not a fully migrated pedagogical content package; CONTENT is a draft summary requiring review.
- The source Google Sheets now has additional tabs. No old tabs were deleted.
