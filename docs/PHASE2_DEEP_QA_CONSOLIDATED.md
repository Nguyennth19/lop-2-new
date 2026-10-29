# PHASE 2 DEEP QA — consolidated gate (2026-10-30)

## Inputs
- User-confirmed V1 6/6, V2 7/7, V3 8/8, V4 8/8, all from manual Apps Script testing.
- Current Google Sheets data: 51 rows, 10 sections; LV1 17, LV2 6, LV3 28.

## Executed in this QA pass
- Inspected Backend.gs, Script_LessonAdapter.html, Script_GenericRenderer.html, Script_Logic.html and Script_Render.html.
- Tested Generic Renderer in isolated JS with 51 real Sheets question payloads: output counts LV1 17, LV2 6, LV3 28.
- Generated practice snapshots for all ten sections; checked hidden-digit sums, 3-term mental addition and fixed word-problem payload preservation; found no arithmetic inconsistencies in tested runs.
- Reinitialized data to simulate reload and compared rendered output: stable.
- Injected a synthetic eleventh section into test data in memory; renderer included it successfully; production Sheet unchanged.
- Fixed Backend.gs validation so numeric zero answers are valid.
- Made frontend API lesson ID configurable through `window.ACTIVE_LESSON_ID || 'MATH_B020'`, bypassing the Bài 20-only adapter when a different lesson is requested.

## Remaining blockers — NOT certified
1. Actual second-lesson end-to-end Apps Script deployment and lesson selection/navigation are **not implemented**. Setting ACTIVE_LESSON_ID is a development configuration, not a UI for selecting lessons.
2. Full DOM grading is not unit-tested using a browser DOM for 51 cases, even though arithmetic payload checks passed and user-tested V4.
3. Current per-question reward key gives at most +2 stars lifetime per original question, even after regenerated practice. This is intended anti-farming policy and needs product signoff.
4. Attempts and snapshots live in localStorage only. Historical attempt navigation and backend analytics per run are not implemented; existing saveStudentProgress payload does not identify run or question IDs.
5. Genuine randomization of WORD_PROBLEM remains disabled for pedagogical safety; no source-supported generator configured.
6. 51 source questions still have MATH_PASS_SOURCE_PENDING: source book edition/page and instructional accuracy are NOT certified.
7. Art mapping awaits approved asset IDs and QA.
8. Legacy UI relies on fixed chapter layout and lesson-specific theory; generic renderer is isolated from the old theory blocks.

## Recommended go/no-go
- **Engineering component QA: CONDITIONAL PASS** for current Bài 20 renderer and generated arithmetic across isolated tests.
- **Phase 2 full closure: HOLD** until second-lesson deployment test, grade DOM regression, historical attempt policy and source review gating are addressed.
- `main` must not be merged or deployed from this branch yet.

## Suggested final acceptance suite
A. In a separate test copy of Sheets, add MATH_B021 with 2 sections and four question types; verify return of getLessonData('MATH_B021') and frontend route.
B. Submit correct, wrong, empty and partially correct answers for all 4 formats and check per-input and per-card scores.
C. After two generated runs, hard-refresh and close/reopen browser; verify answers and reward ledger do not drift.
D. Test when API is unavailable, an unknown question type is inserted, or question_id is changed.
E. Confirm loaded sources remain visibly PENDING and there is no claim of book alignment.
