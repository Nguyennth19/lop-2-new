# Phase 2 Iteration 3 — Generic Sections and Attempt Identity

## Implemented
- `Script_GenericRenderer.html` creates sections from `SECTIONS` (sorted by sort_order), and renders questions from `QUESTIONS`, for all three levels.
- Four card types: VERTICAL_ADD, MENTAL_ADD, WORD_PROBLEM, MISSING_DIGIT.
- `Script_Logic.html` uses generic renderer after successful structured API response, retaining legacy UI until then.
- Each fixed question's draft key is based on immutable question ID. Additional attempts use `question_id__RUN_N`, tracked by `currentUser.practiceRuns[section_id]` in localStorage.
- Reward owner remains immutable `question_id`, so repeated attempts of the **same question** do not award unlimited stars.
- New section groups of existing four types can be displayed without changing sectionMap.
- Per-section buttons and full-level footer accurately say "Làm lượt mới", because they *restart the same fixed questions*; random new questions are **not implemented** by generic renderer yet.
- Original 10-group display is available in legacy fallback. The main branch was not changed.

## Review constraints
- Source content is still MATH_PASS_SOURCE_PENDING; no textbook claim.
- Visual parity, per-answer grading, state restore, reward and new section behavior need browser QA before merge.
- A repeat attempt is a new answer namespace, **not** a new problem variant.
- No remote persistence of draft/attempt IDs (localStorage only).
- Unknown section type triggers an explicit error (not silent rendering).
- Word problem figures are omitted until QA-approved assets are linked by asset ID.
- The current renderer assumes two-digit vertical arithmetic; expand per template before opening to different grade-2 topics.

## QA checklist
1. Pull latest branch, open test deployment; verify all LV1–LV3 51 cards load.
2. Add a new temporary SECTION with an existing exercise_type and a temporary question in **copied** Sheet, verify new section displays; revert.
3. Change sort_order for two questions, verify order changes while previously saved draft follows question_id.
4. Begin a question, click "Làm lượt mới"; verify empty new draft, reload returns same run number, previous run entries preserved.
5. Correctly grade same question twice in separate runs; ensure only first completion adds 2 stars.
6. Test reset section, reset level, grade section, grade level, keypad and voice.
7. Confirm no console error and SOURCE_PENDING remains unchanged.
8. Confirm no other effects on main/demo before merge.
