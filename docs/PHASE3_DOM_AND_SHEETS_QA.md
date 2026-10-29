# PHASE 3 — Isolated Sheets and browser DOM QA

## Achieved 2026-10-30
1. Created a separate Google Sheets copy: https://docs.google.com/spreadsheets/d/10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds/edit
2. Inserted MATH_B021_QA_ONLY with 4 sections and 4 questions representing VERTICAL_ADD, MENTAL_ADD, WORD_PROBLEM and MISSING_DIGIT; source_id SRC_QA_SYNTH, QA=TEST_ONLY_UNVERIFIED. Readback confirmed all rows.
3. Preserved original production Google Sheet and main branch unchanged.
4. Backend.gs accepts `PHASE3_QA_SPREADSHEET_ID` as a server-only Script Property for **test deployment** and uses it before the production ID. Do not set this property on the main production Apps Script project.
5. Added `Script_Phase3QA.html` to the development branch. From browser Console after loading test Apps Script deployment run `phase3GradeDOMQA()`; it uses the actual `evaluateScope` and detached DOM nodes, and restores user stars/rewards/drafts. Covers correct, wrong, empty cases across 4 types. Requires real browser execution for result, not yet independently executed.
6. Checked JavaScript syntax of new QA harness and current Logic/GenericRenderer.

## Setup for real end-to-end test
- Clone Apps Script project for QA (separate project rather than same deployment) and pull this development branch.
- In QA project's Script Properties configure `PHASE3_QA_SPREADSHEET_ID=10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds`. Do not use the property in production.
- Run `runLessonQA('MATH_B021_QA_ONLY')` inside Apps Script; inspect returned status, 4 sections, 4 questions, 0 errors.
- Deploy QA-only webapp URL and append `?lesson=MATH_B021_QA_ONLY` (or `&lesson=...` if URL has a query).
- Open DevTools Console and execute `phase3GradeDOMQA()`. Record full PASS/FAIL JSON output, then manually verify second-lesson rendering and practice attempts.
- Do not promote source status: these are synthetic QA questions, not verified SGK/SBT content.

## Remaining blockers
- Real B021 textbook edition, page/exercise mapping and exact content have not been supplied, so the request to test a **source-verified** second lesson is not complete.
- No access from this tool session to execute the Apps Script deployment or browser DOM. Browser QA script committed but actual result remains PENDING.
- The 51 original B020 questions also remain MATH_PASS_SOURCE_PENDING.
- Run history remains browser-local, not synchronized among devices.
- No promotion/merge to main.

## Release gate
HOLD until (a) DOM QA pass in Apps Script browser, (b) source-verified second lesson with citations to edition/pages, (c) end-to-end QA on copied Sheet and separate Apps Script deployment.
