# PHASE 2 READINESS — Bài 20

## Verified checkpoint (2026-10-30)
- Google Sheets: 1 lesson, 10 sections, 51 questions.
- 16 VERTICAL_ADD; 9 MENTAL_ADD; 8 WORD_PROBLEM; 18 MISSING_DIGIT.
- Duplicate IDs: 0. Required question fields: 51/51. Arithmetic and hidden-digit answers: 51/51.
- `qa_status=MATH_PASS_SOURCE_PENDING` is *not* editorial / textbook approval.
- Source book edition/page verification: 0/51. ASSETS: no mappings. CONTENT pedagogical prose awaiting review.

## Ground rules
- Never modify `main` until Phase 2 QA passes. Use `phase1-data-api-20261030` or new development branch.
- Preserve current `Index.html`, `Script_UI.html` input behavior and 3 level screens until parity tests pass.
- Keep `getLessonData()` (no args) compatible with the legacy UI while introducing `getLessonData('MATH_B020')`.
- Render no untrusted inline HTML or JS from Sheets (escape question text, allowlisted bold formatting only).
- No source claim of SGK/SBT without edition + page + direct comparison.

## Data-to-render contract
`LESSONS` -> lesson metadata. `SECTIONS` -> ordered level/exercise groups. `QUESTIONS` -> ordered question objects with parsed `payload`.
`question_type` renderer registry:
- `VERTICAL_ADD`: n1, n2, op, answer -> existing column-arithmetic card
- `MENTAL_ADD`: n1,n2,op,answer OR terms[] -> existing expression card
- `WORD_PROBLEM`: desc, summary, solution, n1,n2,answer,unit -> existing word-problem card
- `MISSING_DIGIT`: rows[3][2], sum, answer -> existing hidden-digit puzzle card
Unknown type => show a clear content error; never silently skip.
All input IDs and progress keys should incorporate lesson_id + section_id + question_id.
`CONTENT` should render theory with review_status gating. `ASSETS` lookup by approved asset_id; missing asset => safe placeholder.

## Phase 2 implementation sequence
1. Add isolated browser-side `LessonAdapter` mapping structured API data to current card interfaces; validate schema/version and section/question ID join.
2. Implement renderer registry keyed by question_type, taking questions in sort_order and sections in sort_order.
3. Implement loading state; never rerender active student inputs upon asynchronous sync. Cache per lesson and explicit refresh behavior.
4. Keep legacy rendering behind a temporary feature flag. Switch Bài 20 to API data in dev branch only.
5. QA fixed-vs-new display and 51 responses, regeneration, scoring, resume, mobile keypad, sound, accessibility.
6. Only after parity and author approval, merge/deploy.

## Gate / acceptance tests
- API success response: exactly 10 sections, 51 questions, zero structural errors.
- Sheet edit to one question updates correct rendered card after explicit reload.
- Add/remove/order question in Sheet reflected in UI without changing JavaScript (supported question_type).
- Invalid/missing data shows specific error without misrepresenting a fallback as current lesson.
- Same saved draft survives reload, switching levels, and normal data refresh where question IDs persist.
- Math + UI parity for LV1/LV2/LV3; no duplicated question IDs after regeneration.
- No production changes to user account management or access policy (deferred).

## Editorial review queue
1. Identify exact SGK/SBT/reference edition, lesson title, page, exercise and question for each of 51 items.
2. Compare exact instruction, numeric operands, story prompt, expected solution and units with actual photographed/scanned book material.
3. Confirm 1 theory entry reflects approved curriculum; identify extra lesson content that currently lives in rendering code.
4. Asset mapping: use approved 288-PNG asset registry and image IDs only after asset QA; inline SVGs in old code are not covered by current ASSETS.
5. Reconcile 9 puzzle-like entries present in old numeric Sheet vs 18 puzzle instances embedded in JavaScript and document provenance.

## Phase 1 vs Phase 2 boundary
This is preparation, not a claim that the new UI is integrated or the GAS runtime QA was executed. The authoring/educational checks remain PENDING until actual source textbooks are supplied or located in connected project files.
