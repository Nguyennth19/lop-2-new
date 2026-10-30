# Curriculum-format policy — Bài 20 (2026-10-30)

**Learning content does not need verbatim numbers or stories from SGK/SBT.** Acceptance is based on matching the exact lesson's arithmetic structure and skill. Provenance and curriculum conformity are independent QA axes.

## B020 gates (all 51 questions)
- Operator `+` only.
- Exactly **two** addends, never 3+; no subtraction.
- **Both** addends are two-digit integers (10–99), not one-digit.
- Ones column must require carrying: `n1 % 10 + n2 % 10 >= 10`.
- Total within 100 (currently constrained to <=99 by existing two-digit UI).
- Answer matches computed sum.
- `MISSING_DIGIT` hidden cells must reconstruct two two-digit operands satisfying the above.
- Word problems: two addends and the same addition skill; changed context/characters allowed if coherent.
- Student-facing theory, examples and generator must obey the same scope.

## Changes made ONLY in QA Sheets
- Backup: https://docs.google.com/spreadsheets/d/1hMN45drLt13gcU62axtMc5HxGSYP_EyTOl70_fPewuk/edit
- B020_L1_E2A_Q001: 26+4 -> 26+24 = 50.
- B020_L1_E2C_Q001: 23+27+5 -> 23+47 = 70.
- B020_L1_E2C_Q002: 38+12+9 -> 38+24 = 62.
- B020_L1_E2C_Q003: 46+14+7 -> 46+27 = 73.
- Group B020_L1_E2C renamed from three-number drill to two-digit addition.
- 51/51 math and B020 structure pass after readback. Column I/J in QUESTIONS and B020_SOURCE_AUDIT stores independent format QA.
- Original `qa_status` source provenance flags intentionally remain unchanged; a created exercise is allowed when aligned to format. No SOURCE_VERIFIED claim.

## Code
- Development Backend.gs `validateLessonRecords_` now rejects B020 arithmetic outside these constraints. Does not apply B020-specific rule to B021 or other lessons.
- After pulling new code into the QA GAS project, run `testPhase1` with MATH_B020 or `runLessonQA('MATH_B020')`.
- **Important**: edits to question payloads will not automatically rewrite already-saved RUN snapshots in an existing browser. Test B020 in a clean QA browser profile or with separate localStorage data; do not erase children's stored drafts without consent.

## Pending
- Broader pedagogical signoff: check whether B020 specifically includes two-digit results reaching 100; existing UI supports only two result digits.
- Exact source pages remain unverified and are not a requirement for curriculum-format PASS, but sources should be honest (adapted SGK or devised exercises rather than verbatim).
