# Phase 2 V4 — Generated practice and persistent attempts

- Generic renderer now generates fresh arithmetic variants for VERTICAL_ADD, MENTAL_ADD and MISSING_DIGIT using two-digit carrying additions under 100.
- WORD_PROBLEM remains fixed in repeat runs: changing story numbers without approved source text is unsafe.
- Each section run owns a snapshot in localStorage: practiceSnapshots[sectionId::run] keyed by immutable question ID.
- Re-opening and reloading an existing attempt restores exactly the same operands/answers; no new draw on reload.
- Old V3 runs missing snapshots are initialized from their original question payloads, rather than silently generating different answers.
- Card/draft key includes __RUN_N suffix, so attempts are isolated.
- Rewards are limited to one +2-star award per immutable question ID across attempts. Repeating a question, even with new operands, does not award additional stars.
- Source review remains MATH_PASS_SOURCE_PENDING; generated questions are synthetic practice, not SGK or SBT originals.
- This implementation is a developer-branch build. Do not claim Apps Script browser QA until explicitly tested.
- Recommended QA: 51 fixed cards, generate each LV, reload and confirm same run, 2 runs with independent drafts, no doubled rewards, math consistency, V3 saved run migration, word problem content unchanged.

Known limitations: practice snapshots are stored in browser localStorage (not multi-device); a three-term question is generated arithmetically but is not the same pedagogical template as the source; no visual/UI runtime test from this environment.
