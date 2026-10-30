# B020 — Source reconciliation audit (2026-10-30)

## Scope and evidence
- Scope: 51 existing questions in QA spreadsheet `10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds`.
- Snapshot backup: `https://docs.google.com/spreadsheets/d/1q9nWQ1Hf4Iz50I79rYZKLhhzZFhPcqTrr2YndI50bc/edit`.
- Source material: SGK Toán 2 KNTT tập 1, Bài 20 tr.76–79; VBT Toán 2 KNTT tập 1 tr.72–76, as represented by public solution sources. Page-by-page primary physical-book verification still pending.
- 51/51 arithmetic solutions pass. Existing question IDs, operands, student rendering and section assignments remain unchanged to preserve prior test snapshots and drafts.

## QA flags applied
- LV1 14: `ADAPTED_NOT_EXACT_SGK`: math-aligned practice, not verified as verbatim SGK.
- LV1 3: `OPERANDS_MATCH_SGK_P78_FORMAT_DIFF`: operands 47+43, 43+47, 65+28 match SGK page 78 exercises but displayed as mental-add instead of source vertical layout; NOT SOURCE_VERIFIED.
- LV2 6: `SBT_EXACT_MATCH_PENDING`: project word problems not evidenced as the exact workbook questions.
- LV3 28: `REFERENCE_ORIGINAL_PENDING`: need reference book edition and page, despite mathematical validity.
- Lesson status: `MATH_PASS_SOURCE_PARTIAL_NO_SGK_CERTIFICATION`.
- CONTENT remains `PEDAGOGICAL_DRAFT_REVIEW_REQUIRED`.
- Per-question evidence: `B020_SOURCE_AUDIT` tab, including page range and audit note.

## Supported public sources
- SGK exercises: https://loigiai.com.vn/bai-20-phep-cong-co-nho-so-co-hai-chu-so-voi-so-co-hai-chu-so
- SGK page 78: https://haylamdo.com/toan-2-ket-noi/bai-20-phep-cong-co-nho-so-co-hai-chu-so-voi-so-co-hai-chu-so.jsp
- VBT page 72–76: https://vietjack.com/vbt-toan-2-kn/bai-20-phep-cong-co-nho-so-co-hai-chu-so-voi-so-co-hai-chu-so.jsp

## Important decision
Do NOT automatically replace all 51 exercises with SGK/VBT items: the original project learning architecture is 17 LV1, 6 LV2, 28 LV3, and source exercises include graphical tasks requiring new renderer templates. Exact textbook fidelity must be certified exercise-by-exercise, with clear distinction between source content and generated supplement. Do not merge to main until pedagogical review is complete.
