# Bài 21 — Technical QA sign-off (2026-10-30)

## User-confirmed results
- Step A: GitHub Pull / QA configuration PASS.
- Step B: `testPhase3CurriculumQA()` PASS for B020+B021.
- Step C: `testPhase3NegativeCases()` PASS 4/4. Minus, 3 terms and no-carry were rejected; 67+3=70 accepted.
- Step D: `phase3B021VisualQA()` PASS 10/10.
- Step E: `phase3GradeDOMQA()` and `phase3FinalRegressionQA()` marked PASS by tester (individual counts were not supplied for this step).

## Decision
Technical sign-off PASS for the **currently integrated B021 subset** (5 sections, 11 questions). Does not approve full B021 curriculum or public release.

## Outstanding
- Picture-driven, comparison and selection exercises still missing.
- No LV3 book-grounded reference content.
- Public-source comparison not primary-edition signed off.
- LocalStorage cross-device history and release smoke tests remain outside this signoff.
- No change to production main or production Sheets.
