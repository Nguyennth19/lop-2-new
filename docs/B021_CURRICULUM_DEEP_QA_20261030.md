# Bài 21 Curriculum QA + Deep Test — 2026-10-30

## Rule (specific to Bài 21)
Bài 21 is **Luyện tập chung**, not a repeat of the narrow Bài 20 constraint. Public SGK shows both 45+6, 81+9 and 26+66, plus mental sums 41+19, 67+3, 76+14; VBT also includes addition/word problems. Source pointers: https://sachgiaokhoa.aistudybuddy.net/sach-online/lop-2/toan-2-tap-1/bai-21-luyen-tap-chung/ and https://vietjack.com/vbt-toan-2-kn/bai-21-luyen-tap-chung.jsp

The currently supported *arithmetic-card and word-problem* subsets must meet:
- addition only, exactly 2 addends, integers in 1..99, at least one two-digit;
- ones digits sum >= 10 (carrying), result <= 100;
- answer exact, story coherent; no subtraction or 3+ addends in current addition sections;
- 2-digit + 1-digit is explicitly valid, unlike B020.
- visual compare, number from image or choice tasks must be implemented as separate question types and passed against their own rubrics, not rewritten as fake arithmetic cards.
- Existing V4 random generator covers 2-digit + 2-digit carry and is a **partial subset** of B021 variants; don't call B021 fully supported until the other visual templates are implemented.

## Updated isolated QA Sheet
Original: https://docs.google.com/spreadsheets/d/10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds/edit
Backup before update: https://docs.google.com/spreadsheets/d/16EGasOkFuU5sku9RhdmM4aQ0mJy_uaKeMBeMyvb-O0I/edit
- 11 B021 questions kept stable with source descriptions, IDs and existing arithmetic.
- Each of 11 is marked `curriculum_format_QA=PASS_B021_CARRY_REVIEW` and has scope note.
- Lesson marked `CURRICULUM_FORMAT_PASS_PARTIAL_CONTENT`.
- `qa_status=SECONDARY_CROSSCHECK_PENDING_PRIMARY`: no claim of original-book editorial verification.
- LV1: 3 sections, 6 questions; LV2: 2 sections, 5 questions; LV3: none, awaiting legitimate reference sources.
- Neither production Sheet nor main branch changed.

## Run in isolated Apps Script QA project (after GitHub Pull)
1. Confirm Script Properties `PHASE3_QA_SPREADSHEET_ID` still points to the isolated QA spreadsheet.
2. In `Backend.gs` select function `testPhase3CurriculumQA` and press Run. Inspect log `PHASE3_CURRICULUM_QA`: expect B020 51/10, B021 11/5, both success with errors [].
3. Select `testPhase3NegativeCases`, press Run; inspect `PHASE3_NEGATIVE_CASES`: expect 4/4 marked passed, including one-digit valid and minus/3-terms/no-carry rejected.
4. Deploy > Manage deployments > edit QA webapp > New version > Deploy. Open QA Web App `?lesson=MATH_B021`.
5. Enter LV1 and wait for API. F12 Console in `userHtmlFrame`, run `phase3B021VisualQA()`; expect 9 checks all PASS (lesson ID, renderer, 11 count, LV1 6, LV2 5, LV3 0, vertical, mental, word, warning — actually 10 checks).
6. In the same QA browser run `phase3GradeDOMQA()` (expect 9/9) and `phase3FinalRegressionQA()` (expect 10/10) after lesson loading.
7. Manually verify LV1/2 switch, draft and RUN snapshot reload. Do not test from main production deployment.

## Release blockers
- B021 incomplete vs book: many image/diagram questions and LV3 content remain absent.
- Current UI has no custom support for all book visual/question formats; new templates and their test suites required.
- Exact physical SGK/VBT 2026 page-by-page provenance remains pending; adapted exercises are allowed by curriculum policy.
- Existing Web App home is B020-themed hardcoding. B021 learning page routes but home not multi-lesson-ready.
- LocalStorage attempt history cross-device still missing.
