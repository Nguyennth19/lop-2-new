# POST-QA BASELINE CONTRACT — 2026-10-30

## Immutable references
- Code branch: `baseline-qa-b020-b021-20261030` (created from `phase1-data-api-20261030`).
- Working refactor branch: `refactor-safe-post-qa-20261030`.
- Frozen QA Sheet COPY: https://docs.google.com/spreadsheets/d/1AfMsXGBt7Aqc52aulJ9EZBZP_wJrlp7HSCl3N6VeDUY/edit?usp=drivesdk
- Active QA Sheet (DO NOT accidentally overwrite from refactor): `10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds`.
- Production main and production Sheet remain out of scope.

## Test evidence at freeze point
- B020: 51 questions, 10 sections; source and math format validations PASS.
- B021: 15 questions, 8 sections; curriculum rules PASS (5 rules).
- Rule boundary tests: 7/7 PASS.
- Interaction schema tests: 4/4 PASS.
- Curriculum audit: both lessons PASS.
- User confirmed browser functional smoke PASS, but latest full detailed UI DOM counts were not pasted. UI/UX is explicitly not approved.
- This baseline represents the *tested subset*, not 99% quantified coverage, full textbook coverage, or a production release.

## Non-regression invariants
1. Stable lesson/section/question IDs; `?lesson=` routing and response shape.
2. Arithmetic answers, curriculum allow/deny decisions, source statuses.
3. `evaluateScope` correct/wrong/empty counts, feedback and empty-answers.
4. At-most-once +2 stars/reward-owner across attempts.
5. Draft keys, RUN snapshots, reload persistence.
6. Interactive CHOICE/MATCH_PAIRS/DRAG_TAP behavior, including tap alternatives.
7. B020 and B021 supported level and question counts; missing LV3 must not invent content.
8. No writes to production Sheets from QA tooling.

## Proposed safe refactor order
P0: automated differential test harness comparing baseline and candidate on fixed fixtures; make snapshot of API responses and user state.
P1: extract pure curriculum rules and schema validation; keep Backend.gs as thin Apps Script adapter, preserve public functions and error codes.
P2: isolate grading pure functions and reward accounting behind testable boundaries, with identical UI feedback/output.
P3: isolate renderer by question type, remove duplicated escaping and input state code; retain same DOM selectors for draft/restoration.
P4: improve diagnostics and structured logs with IDs only; avoid child personally identifying information.
P5: performance (batch Sheets access, memoize within a request only), feature flags, migration tests, bundle size and accessibility checks.

## Release gates
- All prior named QA commands PASS on refactor branch, plus new differential comparisons.
- QA Web App full manual reload/RUN/levels, isolated from production.
- Source and art audit separate from code acceptance.
- Merge only on explicit owner approval. No branch is technically protected by this document; configure GitHub rulesets.
