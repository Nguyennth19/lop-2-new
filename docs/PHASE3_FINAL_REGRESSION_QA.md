# PHASE 3 — FINAL REGRESSION QA (one-pass)

Date: 2026-10-30. Branch: phase1-data-api-20261030. Production main untouched.

## Automated in-browser suite
Run **phase3FinalRegressionQA()** once in Console inside the Google Apps Script QA Web App after opening MATH_B021_QA_ONLY LV1 and allowing Sheets to load. This directly calls the production evaluateScope().
Cases:
- partial vertical, wrong carry
- partially completed word problem, wrong operator
- partly completed hidden-digit card
- star idempotency across RUN 1 and RUN 2
- independent draft-key serialization for two runs
- generic renderer creation for LV1, LV2, LV3
- switching rendered level previews does not mutate run counts
- reject a malformed API payload with orphan question
The runner saves/restores the currentUser object and prints PHASE3_FINAL_REGRESSION_RESULT. Do not claim PASS until the user supplies the runtime console result.

## Additional real-browser checks required (cannot be simulated)
1. Enter partial answer in LV1; reload Web App; check that specific draft restored.
2. Start RUN 1, enter answer, start RUN 2; reload; check RUN 2 values persist and RUN 1 snapshot remains in localStorage (QA profile only).
3. Switch LV1 -> LV2 -> LV3 -> LV1; check drafts and current attempt remain stable.
4. Temporarily disconnect from network / force Apps Script getLessonData failure in test environment; verify visible error and no misleading B020 fallback when opening B021. Record result and restore connectivity.
5. Verify no source-status promotion: TEST_ONLY_UNVERIFIED remains non-approved.

## Known blocker
Current loader initially renders legacy B020 cards while an alternate lesson API is loading, and on error warns in Console but does not show a robust on-page error. This must be fixed before an unambiguous PASS for error handling / Phase 3 release. Not safe to merge to main.
Historical run navigation and cross-device persistence are still incomplete.
