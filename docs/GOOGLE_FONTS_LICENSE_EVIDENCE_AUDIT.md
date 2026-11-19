# Pinned Google Fonts license evidence audit

The workflow now fetches each unique license file from the exact immutable Google Fonts revision recorded in the font collection manifest. It stores the complete text snapshot, SHA-256, pinned source URL, copyright lines, possible Reserved Font Name strings, and presence/absence of selected OFL 1.1 clauses.

The current source corpus reports 52 font files across 20 families. The audit deduplicates the 20 family-level license files, while retaining the per-font exact SHA-256 and pinned font-source evidence in the candidate queue.

## What a PASS means

A PASS means the pinned license text was retrieved from `raw.githubusercontent.com/google/fonts`, decoded, hashed, and checked for the SIL Open Font License 1.1 marker and selected expected clauses. It does not decide whether machine-learning training is legally permitted, whether third-party upstream rights apply, or whether every intended use complies with all license terms.

The output deliberately keeps:
- `approved_font_count: 0`
- `ml_training_allowed: false`
- `status: REVIEW_REQUIRED`

The license text itself is preserved in the workflow artifact `pinned-font-license-evidence`. Do not copy the candidate queue into the approved manifest or change its pending flags automatically.


## Relationship to the separate conditional OFL policy

This document describes the **source-text evidence audit only**. Its output intentionally remains a neutral candidate report with REVIEW_REQUIRED / zero approvals because that script verifies retrieved license text, hashes, copyright lines, and selected clauses; it does not itself interpret the legal effect of the license for AI training.

The project-level conditional policy is documented separately in [OFL_AI_TRAINING_POLICY.md](OFL_AI_TRAINING_POLICY.md). It applies the official SIL OFL FAQ version 1.1-update8 (November 2026), especially Q1.25 and Q3.9, and is implemented by the separate builder scripts/build_ofl_training_rights_manifest.py. That process creates the active per-file manifest only after checking the exact source-font SHA-256 values against the pinned corpus and the license evidence.

For the current verified corpus, the separate manifest contains **52 exact font files across 20 families**, all conditionally approved for this project's training pipeline. This is not an unrestricted or non-commercial-only approval:

- Any font software produced and released based on these OFL sources must remain under SIL OFL 1.1.
- Preserve applicable copyright notices and acknowledgements.
- Do not use a recorded Reserved Font Name without written permission.
- OFL is **not** a NonCommercial license; downstream commercial use is not prohibited by its terms, subject to the OFL conditions.
- Model-weight distribution licensing is separate and is not settled by this font manifest.

The source-text audit's REVIEW_REQUIRED result and the separate project's conditional policy manifest are therefore different artifacts with different scopes; do not interpret the former as meaning the current per-file manifest has zero approved fonts. This is a conservative project policy mapping, not legal advice.
