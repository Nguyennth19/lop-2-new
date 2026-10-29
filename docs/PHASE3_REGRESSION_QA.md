# Phase 3 — Regression QA and Second Lesson Expansion (2026-10-30)

Status: **IN PROGRESS / engineering fixture PASS, production readiness HOLD**.
Production branch `main` and original Sheets records unchanged.

## Implemented
- `Backend.gs` reads a validated `?lesson=MATH_B021` URL parameter into the template and exposes read-only `getLessonCatalog()`.
- `Index.html` installs `ACTIVE_LESSON_ID` from the validated Apps Script template before frontend scripts.
- `Script_Logic.html` was already updated in the preceding Deep QA pass to pass configurable ID to `getLessonData`; non-B020 lessons render through the generic renderer without B020-only adapter.
- `tests/phase3-second-lesson-fixture.js`: synthetic second lesson, 4 sections, four question types, distributed over LV1/LV2/LV3. **Not** SGK, SBT or intended child-facing content.
- Generic renderer visibly warns when question source is not `SOURCE_VERIFIED`.

## Tests executed with isolated JS harness
- Initialized synthetic second lesson `MATH_B021_QA_ONLY` and rendered: LV1 2, LV2 1, LV3 1 questions.
- Tested one newly generated section run, reinitialized same payload, confirmed identical restored markup and attempt snapshot.
- Existing Phase 2 Deep QA: 51/51 B020 cards, new section insertion in memory and arithmetic snapshot checks.

## Known QA gaps
1. There is **no real** second lesson in Google Sheets. Live `getLessonData('MATH_B021')` will return `LESSON_NOT_FOUND` until a real lesson is sourced, verified and added. Fixture intentionally remains separate from production Sheets.
2. Browser integration of `?lesson=...` and actual Apps Script runtime were **not executed** in this isolated harness.
3. DOM-specific grading tests for all 4 types remain a required manual or headless-browser QA gate.
4. There is no multi-lesson launcher/menu. URL parameter is a development routing entry point only.
5. localStorage attempt history cannot resume across devices; per-attempt backend persistence has not been implemented.
6. Textbook source verification and asset registry remain PENDING; generated arithmetic is synthetic practice and not approved textbook content.

## Next release gate
- Supply/approve book-grounded B021 content in a **test copy** of Sheets, run GAS runtime `runLessonQA('MATH_B021')` and browser `?lesson=MATH_B021`.
- Run DOM regression with correct/incorrect/empty/partially-correct answers and reward idempotency; test mobile input and reload history.
- Only after these tests, consider merging to main.
