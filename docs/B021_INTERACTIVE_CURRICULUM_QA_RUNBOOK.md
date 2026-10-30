# Bài 21 — Interactive exercises + sheet-driven curriculum QA (2026-10-30)

## Added (development / isolated QA only)
- 4 B021 cards and 3 groups, bringing B021 from 11 questions/5 groups to **15 questions/8 groups**.
- LV1 **8 questions / 4 groups**; LV2 **7 questions / 4 groups**; LV3 **0** (reference materials unavailable).
- `CHOICE`: tap large answer; example longest flight path (bee 61 cm, dragonfly 63 cm, grasshopper 51 cm), and illustrative fish tanks.
- `MATCH_PAIRS`: connect equations to outputs via three accessible select menus (45+6=51, 81+9=90, 26+66=92).
- `DRAG_TAP`: drag a result token onto the zone, or tap the token on mobile; e.g. dragonfly route 39+24=63 cm.
- Emojis are **new schematic illustrative placeholders**, **not original textbook pictures**. The tank numbers are adapted, not sourced verbatim.
- Existing scoring `evaluateScope`, reward ledger and input drafts support the new types; user browser verification is required.
- New data `qa_status=ADAPTED_FROM_LESSON_FORMAT` and `curriculum_format_QA=PENDING_INTERACTIVE_QA` pending actual QA.

## CURRICULUM_RULES (new Sheet)
Columns: `lesson_id, rule_id, question_type, operation, min_addends, max_addends, min_digits, max_digits, carry_required, max_result, allowed_skills, status`.
- MATH_B020 requires 2-digit, 2-addend, carrying addition <= 99.
- MATH_B021 arithmetic allows 1-/2-digit operands (at least one 2-digit), 2-addend, carrying, <=100.
- B021 interactive types restricted by allowed `skill`: `COMPARE_ADDITION_LENGTH`, `VISUAL_COMPARE_MEASURE`, `PAIR_ADDITION`, `DRAG_ADDITION_LENGTH`.
- `getLessonData` reads this table on every request and blocks API responses when a rule rejects a question.
- Existing B020/B021 validators remain defense-in-depth.
- `CURRICULUM_AUDIT` is a new Sheet showing latest pass/fail and errors.

## Real test instructions (QA Apps Script project only)
1. Pull branch `phase1-data-api-20261030` latest. Confirm `Backend.gs`, `Index.html`, `Script_GenericRenderer.html`, `Script_Interactions.html`, `Script_Logic.html`, `Script_Phase3QA.html` are present.
2. Confirm Script Property `PHASE3_QA_SPREADSHEET_ID=10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds`.
3. Run `testCurriculumRulesTable()`. Expect PASS, B020 51/10, B021 15/8. If FAIL, inspect `CURRICULUM_AUDIT` or detailed errors.
4. Run `testInteractivePayloadNegativeQA()`. Expect PASS, 4/4.
5. Run `runCurriculumAuditQA()`. Expect PASS; inspect `CURRICULUM_AUDIT` on QA Google Sheet.
6. For automatic on-edit audit, **optionally** run `installCurriculumAuditTriggerQA()` **once** in the QA project and authorize. Only allowed for the hardcoded isolated QA spreadsheet ID. Inspect Apps Script > Triggers to confirm. Edit an isolated B021 question; confirm new report timestamps in `CURRICULUM_AUDIT`. Remember that malicious/broken rows will block the API; undo bad QA edits.
7. **Deploy a new QA Web App version**. Open `?lesson=MATH_B021`, enter LV1; run DevTools Console inside `userHtmlFrame`:
   - `phase3B021VisualQA()`: expect **13/13** after adding choice, match, drag checks.
   - `phase3InteractiveDOMQA()`: expect **7/7** (correct/wrong/empty across 3 types).
   - `phase3GradeDOMQA()`: expect **9/9** (legacy grading).
   - `phase3FinalRegressionQA()`: expect **10/10** (legacy final regression).
8. Test touch or mouse: tap MCQ options; connect match selects; drag a token or tap it; check star award once per question across re-grade and RUN; reload to verify state.
9. On LV3, expect no current content (no false placeholder questions).

## Source / user-experience references
- SGK B021 types: https://loigiaihay.com/giai-bai-21-luyen-tap-chung-sgk-toan-2-ket-noi-tri-thuc-voi-cuoc-song-a86672.html
- Interactive matching and accessibility considerations: https://www.monash.edu/learning-teaching/teachhq/Assessment/assessment-tasks/ensure-clairty-and-quality
- Khan Academy Kids accessibility, multimodal interaction and focus: https://khankids.zendesk.com/hc/en-us/articles/48491600117787-Our-Accessibility-Statement

## Important boundaries
- This is a **first working prototype for the missing interaction families**, NOT all actual SGK figures and subtasks. Original pictures, water-tank heights, kangaroo jumps, multi-part reasoning and LV3 must be reviewed and separately authored.
- Do not copy copyrighted textbook illustrations; create original diagrams/assets.
- Rules table edits are **not unrestricted**: the hardcoded validators enforce baseline B020/B021 constraints, sheet-driven rules add allowlisted skills.
- No production Sheets edits or main-branch merge.
- QA browser results must be supplied before marking any new features PASS.
